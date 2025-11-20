---
**⚠️ CRITICAL: NO FAKE DATA ⚠️**
This project uses ONLY real, verified data sources. NO placeholders, NO synthetic data, NO fake values.
All data must come from authenticated APIs, official sources, or validated historical records.
---

# Hardware Core Comparison: Mac Mini M4 vs Mac Studio M2
**Date**: November 17, 2025  
**Purpose**: Compare core counts and their impact on training performance

---

## Core Count Comparison

### Mac Mini M4 (Current/Base Model)
- **CPU Cores**: 4 performance + 6 efficiency = 10 cores total
- **GPU Cores**: 10-core GPU
- **Neural Engine**: 16-core Neural Engine
- **Memory Bandwidth**: 120 GB/s

### Mac Mini M4 (Pro Variant - if available)
- **CPU Cores**: 6 performance + 6 efficiency = 12 cores total
- **GPU Cores**: 16-core GPU
- **Neural Engine**: 16-core Neural Engine
- **Memory Bandwidth**: 120 GB/s

### Mac Studio M2 Max
- **CPU Cores**: 8 performance + 4 efficiency = 12 cores total
- **GPU Cores**: 30-core or 38-core GPU
- **Neural Engine**: 16-core Neural Engine
- **Memory Bandwidth**: 400 GB/s (with 64GB+ configs)

### Mac Studio M2 Ultra
- **CPU Cores**: 16 performance + 8 efficiency = 24 cores total
- **GPU Cores**: 60-core or 76-core GPU
- **Neural Engine**: 32-core Neural Engine (2x)
- **Memory Bandwidth**: 800 GB/s

---

## Impact on Your Training Workload

### 1. CPU Cores (Tree Models: LightGBM/XGBoost)

**Current Usage**:
- Your plan mentions: "Tree-Based Baselines (CPU, 8-10 threads)"
- LightGBM/XGBoost can use multiple CPU cores for parallel tree building

**Mac Mini M4 (10 cores)**:
- Can use 8-10 threads effectively
- Good for tree models
- Limited by memory (16GB), not cores

**Mac Studio M2 Max (12 cores)**:
- Can use 10-12 threads
- ~20% more CPU performance
- Still memory-limited

**Mac Studio M2 Ultra (24 cores)**:
- Can use 20+ threads
- ~2x CPU performance
- Overkill unless training many tree models in parallel

**Impact**: CPU cores help with tree models, but you're currently memory-limited, not CPU-limited.

---

### 2. GPU Cores (Neural Networks: TensorFlow Metal)

**Current Usage**:
- TensorFlow Metal GPU for LSTM/GRU/CNN training
- Your plan: "Simple Neural Baselines (GPU, sequential)"
- One GPU job at a time (memory constraint)

**Mac Mini M4 (10 GPU cores)**:
- Good for single model training
- Memory-limited (can't train multiple models in parallel)
- Sequential training required

**Mac Studio M2 Max (30-38 GPU cores)**:
- 3-4x more GPU cores
- Can train larger models or faster
- Still memory-limited (unless you get 64GB+)

**Mac Studio M2 Ultra (60-76 GPU cores)**:
- 6-7x more GPU cores
- Can train multiple models in parallel (if memory allows)
- Massive GPU performance

**Impact**: More GPU cores = faster neural training, but memory is still the bottleneck.

---

### 3. Neural Engine Cores (ML Acceleration)

**Current Usage**:
- Not explicitly used in your training scripts
- Could accelerate some ML operations
- Underutilized in current setup

**Mac Mini M4 (16 Neural Engine cores)**:
- Good for inference acceleration
- Can help with some preprocessing

**Mac Studio M2 Max (16 Neural Engine cores)**:
- Same as M4
- No advantage here

**Mac Studio M2 Ultra (32 Neural Engine cores)**:
- 2x Neural Engine cores
- Better for batch inference
- Still underutilized in most ML workflows

**Impact**: Neural Engine helps with inference, but training uses GPU/CPU more.

---

## Real-World Performance Impact

### Scenario 1: Tree Models (LightGBM/XGBoost)

**Mac Mini M4 (10 CPU cores, 16GB)**:
- Can use 8-10 threads
- Memory-limited (can't load large datasets)
- Training time: Baseline

**Mac Studio M2 Max (12 CPU cores, 64GB)**:
- Can use 10-12 threads (~20% faster)
- 4x more memory (can load larger datasets)
- Training time: ~1.2x faster (cores) + much faster (memory allows larger batches)

**Winner**: M2 Max wins due to memory, not cores (cores help ~20%)

---

### Scenario 2: Neural Networks (LSTM/GRU)

**Mac Mini M4 (10 GPU cores, 16GB)**:
- Sequential training (one model at a time)
- Batch size limited to 32 (LSTM) or 16 (attention)
- Training time: Baseline

**Mac Studio M2 Max (38 GPU cores, 64GB)**:
- 3.8x more GPU cores (~3x faster per model)
- 4x more memory (batch size 128+)
- Can train 2-3 models in parallel (if memory allows)
- Training time: ~3-5x faster overall

**Winner**: M2 Max wins due to both GPU cores AND memory

---

### Scenario 3: Parallel Training (Multiple Models)

**Mac Mini M4 (10 GPU cores, 16GB)**:
- Can't parallelize (memory constraint)
- Must train sequentially
- Training time: 60-70 models × sequential time

**Mac Studio M2 Ultra (76 GPU cores, 128GB)**:
- Can train 4-6 models in parallel
- Massive GPU power
- Training time: ~10-15x faster for large batches

**Winner**: M2 Ultra for parallel training, but overkill for your scale

---

## Core Count vs Memory: Which Matters More?

### For Your Workload:

**Memory is the primary bottleneck**:
- Current: 16GB limits batch sizes
- Current: Forces sequential training
- Current: Requires FP16 mixed precision

**Cores are secondary**:
- CPU cores: Help tree models (~20% improvement with more cores)
- GPU cores: Help neural models (~3x improvement with more cores)
- But: Can't utilize more cores without more memory

**The Math**:
- More cores + same memory = Limited improvement (can't use cores fully)
- Same cores + more memory = Significant improvement (larger batches)
- More cores + more memory = Best improvement (parallel training)

---

## Recommendation Matrix

| Option | CPU Cores | GPU Cores | Memory | Best For |
|--------|-----------|-----------|--------|----------|
| **M4 Mini 16GB** (Current) | 10 | 10 | 16GB | Budget, single model training |
| **M4 Mini 48GB** | 10 | 10 | 48GB | Best value, 3x memory, same cores |
| **M2 Max Studio 64GB** | 12 | 38 | 64GB | More cores + more memory |
| **M2 Ultra Studio 128GB** | 24 | 76 | 128GB | Maximum performance, overkill |

---

## Core Utilization in Your Current Setup

### What You're Using:

1. **CPU Cores (Tree Models)**:
   - LightGBM/XGBoost: 8-10 threads
   - Utilization: ~80-100% of available cores
   - Constraint: Memory, not cores

2. **GPU Cores (Neural Models)**:
   - TensorFlow Metal: Uses all 10 GPU cores
   - Utilization: ~100% during training
   - Constraint: Memory limits batch size

3. **Neural Engine**:
   - Not actively used in training
   - Could be utilized for preprocessing/inference
   - Opportunity: Underutilized

---

## Bottom Line

### Core Count Impact:

**CPU Cores**:
- Current (10 cores): Good for tree models
- M2 Max (12 cores): ~20% improvement
- M2 Ultra (24 cores): ~2x improvement, but overkill

**GPU Cores**:
- Current (10 cores): Good for single model
- M2 Max (38 cores): ~3-4x improvement per model
- M2 Ultra (76 cores): ~7x improvement, can parallelize

**Memory vs Cores**:
- More memory (16GB → 48GB): 3-4x improvement (enables larger batches)
- More GPU cores (10 → 38): 3-4x improvement (faster per model)
- Both together: 5-10x improvement (parallel training)

### Recommendation:

**Priority 1: More Memory** (M4 Mini 48GB)
- Solves the primary bottleneck
- Enables larger batches
- Allows some parallelization
- Best value

**Priority 2: More Cores + Memory** (M2 Max Studio 64GB)
- If budget allows
- More GPU cores + more memory
- Can train 2-3 models in parallel
- Better sustained performance

**Priority 3: Maximum** (M2 Ultra Studio 128GB)
- Overkill for 60-70 models
- Only if you scale to 200+ models
- Massive parallel training capability

---

## Conclusion

**Cores matter, but memory matters more for your workload.**

- Current: Memory-limited, not core-limited
- More cores help, but can't be fully utilized without more memory
- Best upgrade: M4 Mini 48GB (more memory, same cores) = 3-4x improvement
- Alternative: M2 Max Studio 64GB (more cores + more memory) = 5-6x improvement

**The external drive doesn't help with cores either** - cores are hardware, not storage.



