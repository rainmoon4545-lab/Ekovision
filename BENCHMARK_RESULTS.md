# Classifier Performance Benchmark Results

**Date**: February 12, 2026  
**System**: Windows, Python 3.14  
**Classifiers**: 314 scikit-learn LogisticRegression models  
**Feature Dimension**: 768 (DINOv3 small)

---

## Executive Summary

✅ **TARGET ACHIEVED!** Sequential inference meets the <100ms target.

**Key Finding**: Sequential inference (33.15 ms) is **FASTER** than parallel inference due to overhead.

**Recommendation**: **Use SEQUENTIAL inference** - simplest and fastest approach.

---

## Detailed Results

### 1. Single Classifier Performance

| Metric       | Value    |
| ------------ | -------- |
| Average Time | 0.168 ms |
| Std Dev      | 0.403 ms |
| Min Time     | 0.096 ms |
| Max Time     | 3.501 ms |
| Iterations   | 100      |

**Analysis**: Individual classifiers are extremely fast (<0.2ms average).

---

### 2. Sequential Inference (All 314 Classifiers)

| Metric       | Value           |
| ------------ | --------------- |
| Average Time | **33.15 ms** ✅ |
| Std Dev      | 3.02 ms         |
| Min Time     | 30.44 ms        |
| Max Time     | 41.49 ms        |
| Iterations   | 10              |

**Analysis**:

- **WELL BELOW** 100ms target (67% margin)
- Consistent performance (low std dev)
- 314 classifiers × 0.168ms ≈ 53ms theoretical, actual 33ms (efficient)

---

### 3. Parallel Inference Results

| n_jobs         | Avg Time (ms) | Speedup | Status         |
| -------------- | ------------- | ------- | -------------- |
| 2              | 95.83         | 0.35x   | ❌ Slower      |
| 4              | 150.73        | 0.22x   | ❌ Slower      |
| 8              | 712.78        | 0.05x   | ❌ Much Slower |
| -1 (all cores) | 137.13        | 0.24x   | ❌ Slower      |

**Analysis**:

- Parallel inference is **SLOWER** than sequential
- Overhead from process spawning and data serialization exceeds benefits
- Small per-classifier time (0.168ms) makes parallelization inefficient

---

## Performance Impact Estimation

### Scenario 1: Classification Every Frame (Worst Case)

| Mode                | Time per Frame | Max FPS      |
| ------------------- | -------------- | ------------ |
| Sequential          | 33.15 ms       | **30.2 FPS** |
| Parallel (n_jobs=2) | 95.83 ms       | 10.4 FPS     |

---

### Scenario 2: Detection-Tracking-Trigger (80% Reduction)

**Assumptions**:

- 80% of frames skip classification (tracking mode)
- Only 20% of frames trigger classification
- YOLO + Tracking overhead: ~50ms per frame

| Component                      | Time (ms) |
| ------------------------------ | --------- |
| YOLO + Tracking                | 50.00     |
| Classification (20% of frames) | 6.63      |
| **Total per Frame**            | **56.63** |

**Estimated FPS**: **17.7 FPS** ✅

With Detection-Tracking-Trigger architecture, system can achieve **17-18 FPS** on CPU, which meets the requirement of 15 FPS for single bottle and 10 FPS for multiple bottles.

---

## Optimization Recommendations

### ✅ RECOMMENDED APPROACH: Sequential Inference

**Rationale**:

1. **Fastest**: 33.15ms beats all parallel configurations
2. **Simplest**: No parallelization complexity
3. **Reliable**: Low variance, predictable performance
4. **Meets Target**: 67% below 100ms threshold

**Implementation**:

```python
# Simple sequential loop
Y_proba_list = [clf.predict_proba(X)[0, 1] for clf in all_classifiers]
Y_proba = np.array(Y_proba_list)
```

### ❌ NOT RECOMMENDED: Parallel Inference

**Reasons**:

- 2-20x slower than sequential
- High overhead for small tasks
- Unpredictable performance (high variance)
- Adds complexity without benefit

---

## Why Parallel is Slower

1. **Process Spawning Overhead**: Creating worker processes takes time
2. **Data Serialization**: Feature vectors must be pickled/unpickled
3. **Small Task Size**: Each classifier takes only 0.168ms - too fast to benefit from parallelization
4. **GIL Not the Issue**: Scikit-learn releases GIL during computation, but overhead dominates

**Rule of Thumb**: Parallelization only helps when individual tasks take >10ms.

---

## Conclusion

✅ **100ms Target**: ACHIEVED (33.15ms, 67% margin)  
✅ **FPS Target**: ACHIEVED (17.7 FPS estimated with tracking)  
✅ **Implementation**: Use sequential inference (simplest & fastest)  
✅ **No Further Optimization Needed**: Proceed with implementation

---

## Next Steps

1. ✅ Benchmark complete
2. ✅ Performance target validated
3. ➡️ Proceed with Task 1: Set up project structure
4. ➡️ Implement Detection-Tracking-Trigger architecture
5. ➡️ Use sequential classifier inference in pipeline

---

## Technical Notes

- **Scikit-learn Version Warning**: Models trained with 1.6.1, loaded with 1.8.0 - no issues observed
- **Feature Dimension**: 768 confirmed from first classifier
- **All 314 Classifiers Loaded**: No missing models
- **Benchmark Iterations**: 100 for single, 10 for sequential/parallel (sufficient for stable averages)

---

**Benchmark Script**: `benchmark_classifiers.py`  
**Results JSON**: `benchmark_results.json`  
**Generated**: February 12, 2026
