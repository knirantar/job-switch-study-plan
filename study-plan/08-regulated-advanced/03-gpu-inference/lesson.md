# GPU Inference: Execution, Memory, Batching and Capacity

**Parent:** 08 — Regulated and Advanced Systems  
**Target:** Senior AI Platform / MLOps Engineer  
**Study time:** 3–4 hours plus lab  
**Lab:** [`lab/`](lab/) — first-order transformer memory and replica calculations with seven tests

## 1. FOUNDATIONS

### Why GPUs help—and why they sometimes do not

Inference applies a trained function to inputs. Neural networks spend much of their time in dense/sparse tensor operations with vast independent arithmetic. A CPU has relatively few sophisticated cores optimized for low-latency general-purpose execution; a GPU has many execution lanes optimized for high-throughput parallel work. Feeding enough compatible work lets GPUs amortize instruction and memory-transfer overhead.

A GPU is not “a faster CPU.” It is a device with its own memory hierarchy, execution model, runtime queues and transfer costs. A small decision tree at 10 requests/s may be faster/cheaper on CPU because serialization and host-device transfer dominate. A transformer with billions of parameters often needs GPU memory bandwidth and tensor-matrix hardware to meet latency/throughput.

CUDA's model launches a **kernel**—device function—over a **grid** of thread blocks. Threads in a block cooperate through fast shared memory and synchronization. Hardware schedules groups called **warps** (commonly 32 threads on NVIDIA architectures). If threads in a warp take different branches, **warp divergence** serializes paths. An **SM** (streaming multiprocessor) schedules resident warps/blocks. **Occupancy** measures resident warps relative to capacity; maximum occupancy does not guarantee maximum performance because registers, shared memory, instruction mix and memory stalls matter.

### Latency, throughput and goodput

**Kernel latency** is device execution; **end-to-end latency** includes queueing, preprocessing, host/device transfer, kernel launch, postprocessing and network. **Throughput** may be examples/s or tokens/s. **Goodput** counts requests meeting their SLO. For generative inference, **prefill** processes the input prompt in parallel; **decode** generates tokens autoregressively and repeatedly reads weights/KV cache. Time to first token (TTFT) emphasizes prefill/queueing; time per output token (TPOT) emphasizes decode.

Compute-bound work is limited by arithmetic throughput; memory-bound work is limited by bandwidth/data movement. **Arithmetic intensity** is operations per byte moved. The roofline model says attainable performance is bounded by min(peak compute, bandwidth × arithmetic intensity). Batching reuses weights across requests and can increase intensity, but adds queue time and memory.

### Memory vocabulary

Host RAM is CPU memory; device global memory is high-capacity GPU memory (often called VRAM/HBM). Registers are per-thread fast storage; shared memory is per-block on-chip storage; caches reduce global-memory traffic. **Pinned** host memory enables efficient asynchronous transfer but cannot be overused without harming the host. A CUDA **stream** is an ordered queue of operations; independent streams may overlap transfer and compute when hardware/dependencies permit.

Inference memory includes weights, activations/workspace, allocator/graph/runtime overhead and—for autoregressive transformers—KV cache. Fragmentation means free bytes exist but not in usable layout. Out-of-memory can therefore occur below nominal capacity. Capacity calculations are hypotheses that must be verified on the exact runtime, model and input distribution.

## 2. CORE MECHANICS

### 2.1 Follow one request through the device

The server validates/deserializes input, tokenizes/preprocesses on CPU or GPU, admits it to a queue, forms a batch, copies/addresses tensors, launches kernels, synchronizes dependencies, copies/serializes output and responds. Instrument each phase. If end-to-end p95 is 120 ms but GPU compute is 35 ms, kernel optimization alone cannot remove the remaining 85 ms.

Asynchronous APIs do not make dependencies disappear. Copy into a buffer, launch a kernel on another stream without an event/dependency, and the kernel may read incomplete data. Synchronizing the whole device fixes correctness but destroys overlap. Use stream ordering/events and buffer lifetime ownership.

### 2.2 Coalescing, divergence and launch overhead

Adjacent warp threads should access contiguous/aligned memory so transactions coalesce. Strided/random accesses waste bandwidth. For a row-major matrix, map neighboring threads across columns, not far-apart rows, when the kernel semantics allow. Branch divergence matters only within a warp: half taking `if`, half `else` can execute both paths masked.

Thousands of tiny kernels incur launch/synchronization overhead. Kernel fusion combines compatible operations, reducing intermediate global-memory writes and launches, though it can increase registers and reduce occupancy. CUDA graphs can capture a stable launch sequence to reduce CPU launch overhead; dynamic shapes/control flow limit reuse.

### 2.3 Calculate weight memory correctly

Weight-only bytes are approximately `parameters × bits/8`. The lab's 7B model at FP16 is exactly 14,000,000,000 decimal bytes = about 13.04 GiB. At 8 bits it is 7 GB; at 4 bits 3.5 GB, plus quantization scales/zeros/alignment. Framework “7B” is approximate; inspect the artifact.

Training needs optimizer states and gradients, but inference normally does not. It still needs runtime workspace, temporary activations and sometimes multiple profiles/engines. Reserving 90% of a 24 GiB GPU does not mean weights may consume all 21.6 GiB; leave explicit overhead and fragmentation margin.

### 2.4 Understand KV-cache arithmetic

Self-attention caches keys and values for prior tokens so decode does not recompute them. A first-order per-token formula is:

```text
KV bytes/token = 2 × layers × KV_heads × head_dim × bytes/element
```

The factor 2 is key plus value. For 32 layers, 8 KV heads, head dimension 128 and FP16: `2×32×8×128×2 = 131,072 bytes/token` = 128 KiB/token. One 4,096-token sequence uses 536,870,912 bytes = 512 MiB. Full multi-head attention with 32 KV heads uses four times as much; grouped-query attention (GQA) shares K/V across query heads.

The lab budgets a 24 GiB device at 90%, subtracts 14 GB weights and 2 GiB fixed overhead, leaving enough first-order KV space for 13 full 4,096-token sequences. The initial expected value was 10; the executable arithmetic corrected it. Real engines allocate blocks, metadata and temporary buffers, so benchmarked concurrency can be lower.

### 2.5 Static, dynamic and continuous batching

Static batching asks clients to supply a batch. Dynamic batching waits briefly and groups compatible queued requests. Larger batches can improve utilization but add wait and padding. Deadline-aware scheduling dispatches before the oldest request exhausts its queue budget.

Traditional static LLM batches wait for all sequences to finish, wasting slots when output lengths differ. Continuous batching admits waiting sequences between decoding iterations as completed sequences leave. Paged/block KV allocation reduces fragmentation and enables non-contiguous logical sequences. It does not eliminate finite memory: enforce max prompt/output, global/tenant tokens and bounded queues.

Separate interactive from bulk queues. A batch of 2,000-token prompts should not block a 10-token clinical lookup. Bucket by length, model, adapter and sampling compatibility. Fair scheduling prevents a tenant with huge prompts consuming every KV block.

### 2.6 Quantize with a quality contract

FP32 uses 32 bits, FP16/BF16 16, INT8 8 and common weight-only schemes ~4. Quantization maps real values to discrete representations using scale/zero point. **Post-training quantization (PTQ)** calibrates after training; **quantization-aware training (QAT)** simulates quantization during training. Per-channel scales often retain accuracy better than one tensor scale at more metadata/compute complexity.

Lower bits reduce weight bandwidth/memory only if supported kernels are efficient. An INT8 engine can be slower if it inserts conversions or lacks optimized shapes. Evaluate task/slice/calibration/safety plus TTFT/TPOT/goodput and memory on the target accelerator. Never infer clinical/financial acceptability from perplexity alone.

### 2.7 Use compilation and optimized runtimes carefully

ONNX Runtime, TensorRT and framework compilers perform graph optimization, operator fusion, precision selection and kernel selection. Dynamic shapes expand engine/profile complexity; constrain realistic min/opt/max shapes. Unsupported operators may fall back to CPU or a slow plugin, creating transfers and tail spikes.

An engine built for one GPU architecture/runtime may not be portable. Record model digest, precision/calibration data, compiler/runtime/driver/CUDA versions, target compute capability and build flags. Verify numeric tolerance against a reference and scan custom plugins like native code.

### 2.8 Partition and parallelize models

**Data parallelism/replication** puts a full copy on each GPU and routes independent requests. It maximizes simple throughput when one copy fits. **Tensor parallelism** shards matrix operations within layers across GPUs and uses collectives such as all-reduce; it needs fast interconnect. **Pipeline parallelism** places layer groups on devices; microbatches reduce pipeline bubbles but add latency/complexity. **Expert parallelism** distributes mixture-of-experts experts and adds all-to-all routing.

If a 70B FP16 model is ~140 GB weight-only, it cannot fit one 80 GB device. Two devices may hold weights but leave insufficient KV/workspace; four may be operationally appropriate. PCIe versus high-bandwidth NVLink/NVSwitch materially changes tensor-parallel latency. Benchmark the exact topology; “4 GPUs” is incomplete.

### 2.9 Share GPUs without unsafe interference

NVIDIA MIG can partition supported GPUs into hardware-isolated instances with fixed compute/memory slices. Time-slicing shares a device temporally but provides weaker performance isolation and no memory partition equivalence. Multi-process service (MPS) can improve concurrent CUDA process utilization but changes isolation/accounting considerations.

For regulated multi-tenancy, prefer dedicated/MIG boundaries for high-risk tenants/models when justified, encrypt and authorize model/data paths, clear lifecycle buffers, and ensure telemetry does not expose payloads. Do not use tenant IDs as unbounded metric labels. A noisy tenant can exhaust queue/KV memory even if GPU compute quotas seem fair; quota on tokens and residency.

### 2.10 Benchmark scientifically

Pin hardware SKU/count/topology, clocks/power mode, driver/CUDA/runtime/container/model/artifact/precision, server configuration, input/output distribution, concurrency and warmup. Separate cold load from steady state. Use representative prompt lengths—not one 8-token prompt for a workload whose p95 is 2,000.

Report TTFT p50/p95/p99, TPOT/inter-token, end-to-end percentiles, request/token throughput, goodput, queue time, failures, GPU utilization/memory/power and CPU/network. Sweep concurrency, batch delay/size, instances, quantization and parallelism one controlled dimension or declared matrix at a time. Repeat and show variability.

NVIDIA's Triton Inception example reports dynamic batching at concurrency 8 around 267.8 inference/s and 35,590 μs client p95; combining two instances reached 289.6/s but p95 59,817 μs. That illustrates why more instances can harm tail latency once the GPU is saturated; it is not a forecast for transformers.

### 2.11 Capacity and autoscaling

Use measured safe throughput at SLO, not vendor peak FLOPS. If a replica sustains 25 rps at SLO, target utilization 60%, arrival 120 rps: `ceil(120/(25×.6))=8`; add one failure-headroom replica = 9. The lab verifies this.

Scale on queue age/depth, in-flight/token load, SLO goodput, KV occupancy and GPU metrics, not CPU alone. Cold start includes scheduling, image pull, model download, engine load and warmup. A 40 GB artifact over effective 2 GB/s has a 20-second transfer floor. Hold warm capacity for sudden traffic and cap scaling to protect cost/registry/downstreams.

### 2.12 Reliability and failure handling

ECC faults, Xid/driver resets, OOM, thermal/power throttling, stuck kernels and interconnect failures require health detection and instance drain/replacement. Readiness waits for verified model load and warmup. Bound allocations; reject before OOM. A process surviving CUDA error may still have corrupt context—follow runtime/vendor guidance and replace where required.

Canary runtime/model/driver upgrades. Keep compatible previous images and artifacts. GPU nodes are scarce: use disruption budgets, topology-aware scheduling, image/model prefetch, quota and priority. Degrade explicitly to an approved smaller/CPU model only if accuracy/latency/compliance are validated and responses identify the fallback.

### 2.13 Run the capacity lab

```bash
cd lab
python3 -m unittest -v test_capacity.py
```

Seven tests cover FP16 weights, GQA/MHA KV ratio, sequence capacity, insufficient memory, replica headroom and invalid parameters. It deliberately does not pretend to model activations, allocator blocks, CUDA contexts, graph workspace, fragmentation, adapters or model-specific architecture; add measured margins.

## 3. WORKED PROBLEMS

### Problem 1 — Weight memory (easy)

Estimate 13B parameters at BF16. **Solution.** `13e9×2=26 GB` decimal ≈24.21 GiB, weight-only. **Mistake:** treating this as total device requirement.

### Problem 2 — KV/token with GQA (easy)

32 layers, 8 KV heads, head dim 128, FP16. **Solution.** `2×32×8×128×2=131,072 bytes` =128 KiB/token. **Mistake:** using query-head count or forgetting K+V.

### Problem 3 — Sequence KV (medium)

Using 128 KiB/token, 8,192 tokens. **Solution.** `131,072×8,192=1,073,741,824` bytes =1 GiB/sequence. **Mistake:** confusing decimal GB/GiB.

### Problem 4 — MHA versus GQA (medium)

Change KV heads 8→32. **Solution.** KV is four times: 512 KiB/token and 4 GiB for 8,192 tokens. Weights unchanged. **Mistake:** assuming context memory depends only on parameter count.

### Problem 5 — Replica capacity (medium)

120 rps, 25 rps/replica measured, 60% target, one spare. **Solution.** `ceil(120/15)+1=9`. **Mistake:** sizing at saturation or forgetting integer/spare.

### Problem 6 — Diagnose low utilization (medium)

GPU 25%, p95 high, server queue low, CPU tokenization 95%. **Solution.** CPU preprocessing is bottleneck. Profile, parallelize/vectorize/tokenizer batching or move supported work; more GPU replicas alone waste cost. **Mistake:** assuming latency means GPU saturation.

### Problem 7 — Batch trade-off (hard)

Batch 1 gives p95 30 ms/80 rps; batch 8 gives 70 ms/300 rps; SLO 50 ms. **Solution.** Batch 8 fails despite throughput. Sweep intermediate batch/delay and select max goodput ≤50 ms; separate bulk queue. **Mistake:** choosing maximum throughput.

### Problem 8 — Quantization release (hard)

INT8 halves weights and improves throughput 35%, but high-value-claim recall drops .94→.89; gate ≥.92. **Solution.** Reject for this release/slice. Try calibration/QAT/mixed precision or different kernel; efficiency cannot waive quality. **Mistake:** validating aggregate accuracy only.

### Problem 9 — Parallelism choice (hard)

Model weight-only 140 GB; four 80 GB GPUs with NVLink; workload interactive. **Solution.** Replication cannot fit. Start with tensor parallel across enough GPUs leaving KV/workspace (likely 4, verified), minimize cross-node communication, benchmark TTFT/TPOT. Pipeline may add bubbles; two GPUs may lack operational memory. **Mistake:** dividing weights by total memory without overhead/topology.

## 4. REAL-WORLD / APPLIED CONTEXT

CUDA's official programming guide defines grids, blocks, threads, memory hierarchy and asynchronous execution. It is the source of truth for device/runtime version behavior; framework abstractions do not remove those constraints.

Triton exposes dynamic batching, instance groups, Performance Analyzer and Model Analyzer. Official Model Analyzer metrics split queue, input copy, inference and output copy and collect GPU memory/utilization/power. This supports bottleneck evidence rather than tuning from aggregate latency.

vLLM applies PagedAttention and continuous batching to LLM serving. The paper reports system-specific throughput comparisons; reproduce on your model/hardware instead of copying headline multipliers. The local lab's corrected 13-sequence result is a transparent arithmetic fixture, not a vLLM capacity promise.

## 5. COMPARISON TABLE

| Option | Concrete effect | Use | Boundary |
|---|---|---|---|
| CPU | Low startup, general cores | Small/low-volume model | Neural throughput |
| GPU | Parallel/bandwidth, device overhead | Batched tensor work | Cost/transfer/cold start |
| FP16/BF16 | 2 bytes/weight | Quality baseline | 7B ≈14 GB weights |
| INT8 | ~1 byte/weight + metadata | Validated kernels/quality | Calibration/operator support |
| 4-bit weight-only | ~0.5 byte/weight + metadata | Memory-bound LLM | Quality/dequant overhead |
| Replication | Full weights/device | Model fits, throughput | Duplicated memory |
| Tensor parallel | Sharded layers + collectives | Model too large | Interconnect latency |
| Pipeline parallel | Layer stages | Very large model | Bubbles/latency |
| Dynamic batch | Higher utilization + wait | Stateless inference | Tail deadlines |
| Continuous batch | Refill decode slots | Variable LLM outputs | Scheduler/KV complexity |
| MIG | Fixed hardware slices | Stronger isolation | Fixed partition flexibility |
| Time-slicing | Flexible sharing | Dev/low-risk burst | Weak performance isolation |

## 6. COMMON MISTAKES & MISCONCEPTIONS

1. Peak FLOPS predicts application throughput—memory, shapes and software dominate.
2. Weight bytes equal required VRAM—KV/workspace/runtime remain.
3. All attention uses query-head KV—GQA/MQA reduce cache.
4. GPU utilization alone finds bottleneck—CPU/queue/network and memory stalls matter.
5. Maximum occupancy is maximum speed—resource/instruction balance matters.
6. More batch always helps—it consumes memory and queue budget.
7. Lower precision always accelerates—unsupported kernels/conversions can slow it.
8. Same GPU name means same result—power, topology, driver/runtime and partition differ.
9. Async means correct overlap—dependencies and buffer lifetime still matter.
10. OOM only at 100%—fragmentation/workspace spikes cause earlier failure.
11. More instances always increase throughput—saturated GPU adds contention/tail latency.
12. GPU sharing equals tenant isolation—memory, queue and side-channel boundaries need design.

## 7. CHEAT SHEET — REVIEW ONLY

> Review only; not a substitute for the full lesson.

- Weight bytes ≈ params × bits/8.
- KV/token = 2 × layers × KV heads × head dim × KV bytes.
- Total VRAM = weights + KV + activations/workspace + runtime + fragmentation margin.
- Prefill drives TTFT/compute; decode repeatedly reads weights/KV and drives TPOT.
- Batch improves reuse; queue delay/padding/memory set boundary.
- Quantize only with task/slice quality and target-hardware benchmarks.
- Replicate if model fits; tensor-shard if not; topology matters.
- Benchmark exact artifact/runtime/hardware/input distribution; report goodput and percentiles.
- Scale on queue/token/KV/SLO signals; include cold-start and failure headroom.
- Readiness follows digest verification, load and warmup.

## 8. PRACTICE SET FOR SELF-TEST

1. Calculate weight-only decimal GB for 30B at INT8.
2. Calculate KV bytes/token for 40 layers, 8 KV heads, head dim 128, BF16.
3. Using answer 2, calculate GiB for one 4,096-token sequence.
4. Why can a 24 GiB GPU not safely load exactly 24 GiB of weights?
5. At 180 rps, 30 measured rps/replica and 50% target, how many replicas before spare?
6. Which metric distinguishes queueing from kernel execution in Triton analysis?
7. Name four benchmark dimensions that must be pinned.
8. Why might tensor parallel across slow cross-node links hurt interactive latency?
9. What quality evidence is required before INT8 healthcare deployment?
10. Give two reasons an OOM occurs below displayed nominal capacity.

## 9. CURATED RESOURCES

1. [CUDA C Programming Guide 12.5](https://docs.nvidia.com/cuda/archive/12.5.0/cuda-c-programming-guide/) — authoritative execution, memory, streams and synchronization model.
2. [NVIDIA Triton Optimization](https://docs.nvidia.com/deeplearning/triton-inference-server/user-guide/docs/user_guide/optimization.html) — measured batching/instance sweep methodology and concrete numbers.
3. [Triton Model Analyzer](https://docs.nvidia.com/deeplearning/triton-inference-server/user-guide/docs/user_guide/model_analyzer.html) — configuration search plus GPU memory/compute measurement.
4. [NVIDIA TensorRT Developer Guide](https://docs.nvidia.com/deeplearning/tensorrt/latest/) — engines, dynamic shapes, precision, calibration and deployment constraints.
5. [vLLM documentation](https://docs.vllm.ai/en/latest/) — continuous batching, distributed serving, quantization and metrics.
6. **Kwon et al., “Efficient Memory Management for Large Language Model Serving with PagedAttention,” SOSP 2023** — block-based KV memory design and evaluated trade-offs.
7. **Williams, Waterman, Patterson, “Roofline: An Insightful Visual Performance Model,” CACM 2009** — compute-versus-bandwidth reasoning.
8. **Hennessy & Patterson, _Computer Architecture: A Quantitative Approach_, 6th ed., Chapters 4 and 6** — memory hierarchy and data-level parallel architecture.
9. [NVIDIA Nsight Systems User Guide](https://docs.nvidia.com/nsight-systems/UserGuide/) — timeline-based CPU/GPU/transfer bottleneck investigation.
10. [NVIDIA MIG User Guide](https://docs.nvidia.com/datacenter/tesla/mig-user-guide/) — exact supported isolation/partition mechanics and lifecycle.

## 10. RELATED TOPICS BRIDGE

### Before

1. **Model Serving and LLMOps** — provides contracts, queues, batching and SLOs.
2. **ML Fundamentals/Lifecycle** — supplies quality gates and immutable artifacts.
3. **Concurrency** — supplies asynchronous scheduling and race/dependency reasoning.
4. **Capacity and DR** — supplies headroom, failure modes and recovery.

### After

1. **Multitenancy and FinOps** — allocates scarce GPU memory/compute/cost fairly.
2. **Kubernetes** — schedules devices, topology, warm capacity and rollouts.
3. **Observability** — correlates queue/copy/kernel/memory/power with SLOs.
4. **Security and Audit** — protects shared accelerators, native plugins and artifacts.

---ANSWER KEY BELOW---

1. `30e9×1=30 GB` decimal, plus metadata/workspace.
2. `2×40×8×128×2=163,840 bytes/token`.
3. `163,840×4,096=671,088,640 bytes = 0.625 GiB`.
4. Runtime/context, activations/workspace, input/output, allocator fragmentation and safety margin need memory.
5. `ceil(180/(30×.5))=12` replicas.
6. `perf_server_queue` versus `perf_server_compute_infer` (also input/output copy metrics).
7. Hardware/topology, driver/CUDA/runtime/container, model/precision, server config, input/output distribution, concurrency/warmup—any four.
8. Each layer's collectives add communication latency; slow/high-latency links can dominate compute and TTFT/TPOT.
9. Task, slice, calibration/safety metrics versus approved baseline on representative data, plus target-hardware numeric and serving tests.
10. Fragmentation and temporary workspace/activation spikes; also other processes/context or conservative allocator reservation.
