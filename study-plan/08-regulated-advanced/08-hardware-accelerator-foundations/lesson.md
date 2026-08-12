# Computer Hardware and Accelerator Foundations from Scratch

Parent subject: `08-regulated-advanced`
Study time: 3–4 hours
Target: senior AI platform / MLOps / backend interviews

## 1. FOUNDATIONS

### Software performance runs on physical machinery

Programs execute instructions on processors, move bytes through memory hierarchies, communicate across buses/networks, and persist data on storage. Abstract runtimes are essential, but capacity and latency are constrained by hardware. An engineer who only counts operations may miss that moving model weights dominates computation; one who only buys more GPU may leave it idle behind CPU preprocessing or network transfer.

### Bits, bytes, and representation

A bit is 0/1; eight bits form byte. Binary prefixes: KiB=2¹⁰, MiB=2²⁰, GiB=2³⁰. Decimal hardware/network units often use KB/GB=10³/10⁹. A 80 GB GPU marketed decimal is about 74.5 GiB. State units.

Integers use fixed widths on hardware; signed commonly two's complement. Floating point approximates real numbers with sign, exponent, significand. IEEE-754 float32 has 1 sign, 8 exponent, 23 stored fraction bits (~7 decimal significant digits); float64 11/52 (~16 digits). Operations round and are not associative: `(a+b)+c` may differ from `a+(b+c)`.

ML formats include float16 (5 exponent/10 fraction), bfloat16 (8/7, wider range but less precision), TensorFloat-32 internal modes, int8/int4 quantization. Lower precision reduces storage/bandwidth and can use faster units, but risks overflow, underflow, rounding, accuracy loss. Accumulation often uses higher precision.

### CPU architecture

A CPU core fetches, decodes, executes instructions. Modern cores use pipelines, superscalar issue, out-of-order execution, branch prediction, speculative execution, vector/SIMD instructions, and multiple hardware threads. Clock GHz is cycles/s, not instructions/s; IPC varies with dependencies, branches, cache misses, and instruction mix.

CPUs excel at low-latency serial/control-heavy work, diverse branches, OS/application logic, and modest parallelism. SIMD applies one instruction to multiple data lanes (AVX etc.), useful for numerical kernels. Compiler/runtime/library must vectorize; Python loops do not automatically exploit full SIMD like optimized NumPy kernels.

### Memory hierarchy

Registers are tiny/fast; L1/L2/L3 caches progressively larger/slower; DRAM much larger/slower; SSD/storage slower; network remote memory/services slower. Approximate latency orders vary by hardware: register/cycle, L1 ~nanoseconds, DRAM tens to ~100 ns, NVMe tens–hundreds microseconds, network milliseconds. Verify platform; ratios matter.

Cache works because programs exhibit temporal and spatial locality. A cache line often 64 bytes on CPUs; accessing one byte fetches a line. Sequential arrays use bandwidth; pointer-chasing random objects causes misses. False sharing occurs when threads modify independent variables on one cache line, causing coherence traffic.

**Bandwidth** is bytes/s; **latency** is delay. A 100 GB/s memory can still have high single-access latency; concurrency/prefetch hides it. Memory capacity, bandwidth and access pattern are distinct.

### Storage and I/O

Storage workload described by IOPS, request size, throughput, latency, queue depth, read/write ratio, sequential/random and durability. 10,000 IOPS×4 KiB≈39.1 MiB/s; at 256 KiB≈2.44 GiB/s, likely hitting another cap. Filesystem/page cache/direct I/O and write barriers affect behavior.

Training pipelines can starve GPU if reading many small files/decompressing/augmenting. Sharded sequential formats, prefetch, workers, pinned memory and caching help, but preserve data shuffle and integrity.

### Parallelism and concurrency

Concurrency means tasks overlap in time; parallelism executes simultaneously. **Data parallelism** applies same operation to different data. **Task parallelism** different tasks. Amdahl's Law: if fraction p is parallel and speedup s, total speedup `1/((1-p)+p/s)`. If 90% parallel with infinite processors, maximum10× because 10% serial.

Parallel overhead includes scheduling, synchronization, communication, imbalance, memory contention and reductions. Adding threads can slow a memory-bound workload. Measure scaling efficiency.

### GPU architecture

GPUs have many throughput-oriented execution units organized into streaming multiprocessors (SMs on NVIDIA terminology; analogous compute units elsewhere). Threads execute in groups called warps (commonly 32 NVIDIA threads) under SIMT: one instruction stream across lanes. Blocks/thread groups schedule on SMs and share fast on-chip memory/synchronization.

GPU hides latency by keeping many warps ready; when one waits on memory, another executes. **Occupancy** is active warps relative to hardware maximum, constrained by registers, shared memory, block size and limits. Higher occupancy is not always faster if bandwidth/instruction bottleneck already saturated.

Branch divergence within a warp serializes different paths. Coalesced memory access lets neighboring threads access neighboring addresses efficiently. Random/scattered access wastes transactions.

### GPU memory hierarchy

Registers per thread fastest; shared memory/L1 on SM; L2 shared; device global memory large/high bandwidth; host memory across PCIe/NVLink; storage/network farther. GPU HBM bandwidth may be terabytes/s, but model inference can still be memory-bound because every generated token reads large weights/KV with limited arithmetic.

Host-device transfer over PCIe is far below HBM and has latency. Moving tiny tensors repeatedly is inefficient. Batch transfers, keep model/data on device, use pinned host memory/asynchronous copies, and overlap compute where safe.

Unified/managed memory simplifies address space but page migration/oversubscription can cause unpredictable stalls; it does not make CPU/GPU memory bandwidth identical.

### Kernels and launches

A **kernel** is function executed across many GPU threads. Launch has fixed overhead; many tiny kernels underutilize device. Kernel fusion combines operations, reducing launches and intermediate memory traffic. Frameworks use CUDA/ROCm and optimized libraries (cuBLAS, cuDNN, Triton, oneDNN etc.).

Asynchronous execution means CPU launch returns before GPU completion. Benchmark requires synchronization around timed region; otherwise you measure enqueue time. Warm up compilation/caches and report distributions.

### Matrix multiplication

Dense GEMM C=A×B is central. A m×k, B k×n performs roughly 2mkn floating operations (multiply+add convention). It reuses tiles from fast memory; optimized kernels maximize data reuse. Tensor cores accelerate matrix operations in supported precision/layout.

Example 1024³ multiply≈2.147 billion FLOPs. At ideal100 TFLOP/s compute floor≈21.5 microseconds, but memory, launch, shapes, precision and utilization increase actual. Peak spec is not application performance.

### Compute-bound versus memory-bound

**Arithmetic intensity**=operations/bytes moved from a memory level. Hardware has peak compute P FLOP/s and memory bandwidth B byte/s. Roofline bound `performance≤min(P,B×intensity)`. Ridge point P/B.

If GPU P=100 TFLOP/s and B=2 TB/s, ridge=50 FLOP/byte. Kernel intensity10 is bandwidth-bound with roof20 TFLOP/s. Intensity100 can be compute-bound up to100 TFLOP/s. Quantization halves/quarters bytes and may raise effective intensity plus specialized compute.

### Model memory

Parameter memory≈count×bytes. A 7-billion-parameter model: fp32 28 GB decimal, fp16/bf16 14 GB, int8 7 GB, int4 3.5 GB before scales/metadata/runtime. Training adds gradients, optimizer states (often multiple fp32 tensors), activations and fragmentation; can require many times weights.

Inference also uses KV cache proportional to layers×batch×sequence×key/value dimensions×bytes, activations, workspaces and framework allocator. “Weights fit” does not mean workload fits.

### Distributed accelerator communication

Data parallel training replicates model and all-reduces gradients. Tensor parallel splits matrix dimensions and communicates activations; pipeline parallel splits layers and sends microbatches; expert parallel routes tokens. Interconnect bandwidth/latency and topology (PCIe, NVLink/NVSwitch, InfiniBand/RoCE) determine scaling.

Eight GPUs do not give 8×. Efficiency=actual speedup/8. At 6×, 75%. Slowest worker/straggler and network collectives stall synchronized training.

### Performance measurement

Define workload shapes, precision, batch, sequence, model, hardware/power, software/drivers, warmup, duration, concurrency, input distribution and correctness. Measure end-to-end latency (p50/p95/p99), throughput, time-to-first-token, inter-token latency, utilization, HBM/SM/tensor activity, memory, power, transfer, queue, CPU, and quality.

Microbenchmarks isolate; end-to-end validates user result. Profile before optimize. Peak utilization alone can reflect wasted work.

Energy and thermal limits are also part of sustained performance. A short benchmark can reach a boost clock that a thirty-minute workload cannot maintain; shared cloud hosts can expose topology or power differences. Record power limits, temperature, clock behavior and run duration when comparisons influence expensive capacity purchases. Normalize cost and energy per useful, quality-accepted output rather than celebrating maximum tokens per second from a degraded model.

## 2. CORE MECHANICS

### 2.1 Calculate representation memory

100 million values: float32=400,000,000 bytes≈381.47 MiB; float16=200MB≈190.73MiB; int8=100MB≈95.37MiB. Add array metadata/alignment; Python list of float objects is far larger.

For batch tensor `(64,3,224,224)` float32: elements9,633,792; bytes38,535,168≈36.75MiB. Gradients/activations multiply.

### 2.2 Bandwidth transfer floor

Copy 12 GiB over ideal PCIe effective24 GB/s decimal: bytes12×2³⁰≈12.885GB; floor≈0.537s. Actual includes protocol/contention/mapping. Over 300 GB/s NVLink-like link floor≈42.9ms. Keep weights resident.

### 2.3 Amdahl

80% parallel sped up 8×: speedup `1/(.2+.8/8)=1/.3=3.333×`, not8. With infinite parallelism max5×. Optimize serial input/control path or change algorithm.

### 2.4 Roofline

P=120TFLOP/s,B=1.5TB/s; ridge80FLOP/B. Kernel I=20→bandwidth roof30TFLOP/s. Observed15→50% of roof, not 12.5% of peak alone. Investigate access, occupancy, divergence, launch.

### 2.5 Warp divergence

Warp32 threads, 16 take branch A and16 B. SIMT executes A with half lanes active then B half, roughly losing branch-region utilization (not exactly 2× due instructions/cache). Reorganize data/kernels or use predication if beneficial; don't contort without profiling.

### 2.6 Coalescing

Thread i reading `array[i]` accesses contiguous values and memory transactions combine. Reading `array[i*large_stride]` scatters cache lines. Matrix layout (row/column major), transpose and alignment determine. Tiled shared memory reorganizes reuse while avoiding bank conflicts.

### 2.7 Training memory estimate

7B parameters mixed precision, illustrative: fp16 weights14GB; fp16 gradients14GB; fp32 master weights28GB; Adam first+second moments56GB →112GB before activations/temp/fragmentation. Implementations/sharding/8-bit optimizer differ. ZeRO/FSDP shards states across devices, trading communication.

### 2.8 KV cache

Approx decoder KV bytes=`2 × layers × batch × sequence × kv_heads × head_dim × bytes`. For 32 layers,batch8,seq4096,32 heads,128 dim,fp16: `2×32×8×4096×32×128×2=17,179,869,184` bytes=16GiB. Grouped-query attention with8 KV heads reduces to4GiB. Verify model architecture/framework layout.

### 2.9 Benchmark correctly

Warm up 50 requests; synchronize GPU; measure 1,000 representative inputs with fixed arrival/concurrency and tokenizer; record p50/p95/p99, throughput, TTFT/tokens/s, memory/energy, errors, output quality. Repeat runs; show confidence/variance. Include queue and preprocessing. Compare same precision/quality.

### 2.10 Diagnose underutilized GPU

Check queue/work exists; CPU/tokenizer/data loader; batch/shapes; H2D copies; kernel timeline/gaps; launch count; SM/tensor utilization; HBM bandwidth; occupancy/registers; synchronization; power/thermal; multi-GPU communication. GPU utilization percentage is coarse and can hide memory-bound work.

## 3. WORKED PROBLEMS

### Problem 1 — Tensor bytes (easy)

1,000×768 float32 embedding matrix.

**Solution.** 768,000×4=3,072,000 bytes≈2.93MiB.

**Trap:** 3.072MiB (mix decimal/binary).

### Problem 2 — Weight memory (easy)

13B parameters bf16.

**Solution.** ~26GB decimal≈24.21GiB before overhead.

**Trap:** assuming fits 24GiB exactly.

### Problem 3 — IOPS throughput (easy)

20,000 IOPS at 8KiB.

**Solution.** 160,000KiB/s=156.25MiB/s if IOPS is bottleneck.

**Trap:** calling 20,000MB/s.

### Problem 4 — Amdahl (medium)

95% parallel on20 workers.

**Solution.** `1/(.05+.95/20)=10.256×`; efficiency51.3%.

**Trap:** 19×/20×.

### Problem 5 — Roofline (medium)

Peak80TFLOP/s, bandwidth2TB/s, intensity15.

**Solution.** bandwidth roof30TFLOP/s, so memory-bound; max30.

**Trap:** promise80.

### Problem 6 — PCIe transfer (medium)

8GB batch at16GB/s ideal.

**Solution.** .5s floor, too high for low-latency; actual worse.

**Trap:** ignoring transfer in GPU compute benchmark.

### Problem 7 — KV scaling (hard)

Double batch and sequence. KV memory factor?

**Solution.** 4× because linear in each.

**Trap:** 2×.

### Problem 8 — Async timing (hard)

CPU timer around kernel launch reports 0.1ms while kernel 10ms.

**Solution.** Launch asynchronous; synchronize/events correctly. Warmup and end-to-end timing.

**Trap:** publishing enqueue latency.

### Problem 9 — Quantization (hard)

Int8 halves fp16 weights. Does latency halve?

**Solution.** Not necessarily: dequant overhead, unsupported kernels, compute/launch/KV/CPU bottlenecks, batch and accuracy. Benchmark end-to-end quality-equivalent workload.

**Trap:** bytes ratio equals performance ratio.

## 4. REAL-WORLD / APPLIED CONTEXT

### NVIDIA tensor cores

Tensor cores accelerate matrix multiply-accumulate in supported precisions/layouts. Framework autocast/mixed precision can use them, with loss scaling for fp16 training. Actual throughput requires compatible shapes, sufficient work, and optimized kernels.

### FlashAttention

FlashAttention computes exact attention with IO-aware tiling to reduce HBM reads/writes and avoid materializing full score matrix, improving speed/memory while mathematical attention remains. It illustrates memory traffic, not FLOP count alone, controlling performance.

### vLLM PagedAttention

Paged KV cache organizes blocks to reduce fragmentation/waste and enable continuous batching. Serving throughput improves under variable sequences, but admission still accounts for per-token KV and fragmentation.

## 5. COMPARISON TABLE

| Hardware | Strength | Memory | Best workloads | Limitation |
|---|---|---|---|---|
| CPU | low-latency control, branches, broad | cache+DRAM | APIs, preprocessing, small models | lower dense parallel throughput |
| GPU | massive data parallel/tensor ops | HBM | training/inference/numerics | transfer, batching, cost, kernels |
| TPU/AI ASIC | specialized matrix efficiency | HBM/on-chip | supported ML graphs | ecosystem/shape/provider constraints |
| fp32 | precision/range | 4B/value | stable baseline | bandwidth/memory |
| bf16 | fp32-like exponent | 2B | training/inference | less significand precision |
| fp16 | more precision bits than bf16, narrow range | 2B | mixed precision | overflow/underflow |
| int8/int4 | compact/fast supported | 1/.5B | quantized inference | calibration/accuracy/kernel metadata |
| PCIe | standard host/device/inter-GPU | tens GB/s | attachment | below HBM/NVLink |
| NVLink-like | high GPU interconnect | higher | multi-GPU | topology/cost/platform |

## 6. COMMON MISTAKES & MISCONCEPTIONS

1. GB and GiB interchangeable—~7.4% difference.
2. GHz equals performance—IPC/memory/workload matter.
3. More cores gives linear speedup—serial/overhead/bandwidth.
4. Cache capacity equals application memory—hierarchy and working set.
5. GPU is faster for every task—launch/transfer/branch/small work can lose.
6. High occupancy guarantees speed—bottleneck may elsewhere.
7. GPU utilization shows useful compute—it is coarse.
8. Peak FLOPS predicts latency—intensity/utilization/shape matter.
9. Weights fit means model serves—KV/workspaces/fragmentation remain.
10. Lower precision preserves quality—validate calibration/tasks/slices.
11. Async timer measures execution—must synchronize/use events.
12. Eight GPUs gives8×—communication/serial/imbalance reduce.

## 7. CHEAT SHEET — REVIEW ONLY

Review only, not a substitute for the lesson.

- bytes=elements×dtype bytes; state GB vs GiB.
- CPU control/latency; GPU throughput/data parallel.
- hierarchy: registers→cache/shared→DRAM/HBM→interconnect→storage/network.
- bandwidth bytes/s; latency delay; locality/coalescing matter.
- Amdahl speedup=`1/((1-p)+p/s)`.
- GPU warp/SIMT; divergence serializes branch paths.
- kernel launch async; synchronize benchmarks.
- GEMM ~2mkn FLOPs.
- intensity=FLOPs/bytes; roof=min(peak,bandwidth×intensity).
- parameter bytes is only start; training states/activation, inference KV.
- KV linear in batch×sequence×layers×KV heads×head dim.
- benchmark workload+quality end-to-end, then profile.

## 8. PRACTICE SET FOR SELF-TEST

1. Convert80GB decimal to GiB.
2. Compute bytes for `(32,512,4096)` bf16.
3. Calculate IOPS throughput50k×16KiB.
4. Amdahl p=.7,s=16.
5. Roofline P=200TF,B=4TB,I=30.
6. Explain warp divergence.
7. List training memory beyond weights.
8. Calculate KV when batch doubles only.
9. Design GPU inference benchmark fields.
10. Diagnose low GPU use/high CPU.

## 9. CURATED RESOURCES

- David Patterson and John Hennessy, *Computer Organization and Design RISC-V Edition*, 2nd ed., Chapters 1, 2, 4, 5, 6 — instructions, processor, memory hierarchy, parallelism.
- John Hennessy and David Patterson, *Computer Architecture: A Quantitative Approach*, 6th ed., Chapters 1, 2, 4, 5 — performance, memory, DLP/GPU, TLP.
- NVIDIA, *CUDA C++ Programming Guide*, sections Programming Model, Hardware Implementation, Memory Hierarchy, Performance Guidelines — authoritative CUDA/SIMT/occupancy/coalescing.
- Samuel Williams, Andrew Waterman, David Patterson, “Roofline: An Insightful Visual Performance Model for Multicore Architectures,” 2009 — primary arithmetic intensity model.
- Paulius Micikevicius et al., “Mixed Precision Training,” 2017 — fp16 accumulation/loss scaling methodology.
- Tri Dao et al., “FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness,” 2022 — IO-aware GPU attention.
- Woosuk Kwon et al., “Efficient Memory Management for Large Language Model Serving with PagedAttention,” 2023 — KV serving memory.
- PyTorch official “Performance Tuning Guide,” profiler, AMP, and distributed docs — practical framework measurement/optimization.

## 10. RELATED TOPICS BRIDGE

### Before

1. **Linux/JVM/Python Runtime:** processes, memory, threads, native libraries.
2. **Math/Transformers:** matrix shapes, precision, attention and KV.
3. **Cloud Compute:** VM/GPU SKU, storage/network capacity.

### After

1. **GPU Inference advanced:** capacity, batching, quantization, parallelism and benchmarks.
2. **Model Serving/LLMOps:** queue/admission/autoscaling and cost.
3. **SaaS Cost Foundations:** GPU allocation/unit economics.
4. **SRE Capacity:** saturation, overload, failure headroom.

---ANSWER KEY BELOW---

1. `80e9/2^30≈74.51GiB`.
2. 32×512×4096×2=134,217,728 bytes=128MiB.
3. 800,000KiB/s=781.25MiB/s.
4. `1/(.3+.7/16)=2.909×`.
5. B×I=120TF, below200, bandwidth-bound roof120TF.
6. Threads in warp taking different branches execute paths with inactive lanes, reducing efficiency.
7. Gradients, master weights, optimizer moments, activations, temp/workspace, communication buffers, allocator fragmentation.
8. 2×.
9. Model/tokenizer, hardware/topology/software, precision/quantization, batch/concurrency/arrival, input/output length distribution, warmup/sync, latency/TTFT/tokens/s/throughput/memory/power/errors/quality.
10. Profile tokenization/data loader/preprocessing, H2D copies, batch, kernel gaps, thread limits; optimize/parallelize CPU, cache/pretokenize, batch/overlap transfers while preserving semantics.
