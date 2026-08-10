"""Transparent first-order GPU inference memory/capacity calculations."""
from __future__ import annotations
from dataclasses import dataclass
from math import ceil

GIB = 1024 ** 3

@dataclass(frozen=True)
class Transformer:
    parameters: int
    layers: int
    kv_heads: int
    head_dim: int
    weight_bits: int = 16
    kv_bits: int = 16

    def __post_init__(self):
        for value in (self.parameters,self.layers,self.kv_heads,self.head_dim,self.weight_bits,self.kv_bits):
            if value <= 0: raise ValueError("model dimensions and bits must be positive")

def weight_bytes(model: Transformer) -> int:
    return ceil(model.parameters * model.weight_bits / 8)

def kv_bytes_per_token(model: Transformer) -> int:
    # key + value, for every layer and KV head
    return ceil(2 * model.layers * model.kv_heads * model.head_dim * model.kv_bits / 8)

def max_sequences(model: Transformer, gpu_gib: float, utilization: float, tokens_per_sequence: int,
                  fixed_overhead_gib: float = 0) -> int:
    if not 0 < utilization <= 1 or gpu_gib <= 0 or tokens_per_sequence <= 0 or fixed_overhead_gib < 0:
        raise ValueError("invalid capacity inputs")
    usable = gpu_gib * GIB * utilization - weight_bytes(model) - fixed_overhead_gib * GIB
    return max(0, int(usable // (kv_bytes_per_token(model) * tokens_per_sequence)))

def required_replicas(arrival_rps: float, measured_rps_per_replica: float, target_utilization: float,
                      failure_headroom: int = 0) -> int:
    if arrival_rps < 0 or measured_rps_per_replica <= 0 or not 0 < target_utilization <= 1 or failure_headroom < 0:
        raise ValueError("invalid replica inputs")
    return ceil(arrival_rps / (measured_rps_per_replica * target_utilization)) + failure_headroom
