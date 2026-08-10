"""Small, dependency-free inference gateway policy core for study and tests."""
from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import dataclass, field
from typing import Callable

EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
CARD = re.compile(r"\b(?:\d[ -]*?){13,19}\b")


class RequestRejected(ValueError): pass
class QuotaExceeded(RuntimeError): pass


def redact(text: str) -> str:
    return CARD.sub("[PAYMENT_CARD]", EMAIL.sub("[EMAIL]", text))


def cache_key(model_digest: str, prompt: str, temperature: float, max_tokens: int) -> str:
    payload = json.dumps({"model": model_digest, "prompt": prompt, "temperature": temperature,
                          "max_tokens": max_tokens}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


@dataclass
class TokenBucket:
    capacity: int
    refill_per_second: float
    tokens: float = field(init=False)
    updated_at: float = field(default_factory=time.monotonic)

    def __post_init__(self) -> None: self.tokens = float(self.capacity)

    def consume(self, amount: int, now: float | None = None) -> bool:
        current = time.monotonic() if now is None else now
        elapsed = max(0.0, current - self.updated_at)
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_per_second)
        self.updated_at = current
        if amount > self.tokens: return False
        self.tokens -= amount
        return True


class Gateway:
    def __init__(self, model_digest: str, generate: Callable[[str, int], str], bucket: TokenBucket):
        self.model_digest, self.generate, self.bucket = model_digest, generate, bucket
        self.cache: dict[str, str] = {}

    def infer(self, prompt: str, max_tokens: int = 128, temperature: float = 0.0,
              now: float | None = None) -> dict[str, object]:
        if not 1 <= max_tokens <= 512: raise RequestRejected("max_tokens must be 1..512")
        if not 0.0 <= temperature <= 2.0: raise RequestRejected("temperature must be 0..2")
        safe_prompt = redact(prompt)
        estimated = len(safe_prompt.split()) + max_tokens
        if not self.bucket.consume(estimated, now): raise QuotaExceeded("tenant token budget exhausted")
        key = cache_key(self.model_digest, safe_prompt, temperature, max_tokens)
        hit = temperature == 0.0 and key in self.cache
        if hit: output = self.cache[key]
        else:
            output = redact(self.generate(safe_prompt, max_tokens))
            if temperature == 0.0: self.cache[key] = output
        return {"output": output, "cache_hit": hit, "model_digest": self.model_digest,
                "input_words": len(safe_prompt.split())}
