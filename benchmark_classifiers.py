import os
import time
import numpy as np
import joblib
import json

# Configuration
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_PATH, "OVR_Checkpoints-20251018T053026Z-1-001", "OVR_Checkpoints")
ENCODER_PATH = os.path.join(BASE_PATH, "dinov3_multilabel_encoder.pkl")

NUM_ITERATIONS = 100
FEATURE_DIM = None

def load_classifiers():
    print("=" * 80)
    print("LOADING CLASSIFIERS")
    print("=" * 80)
    
    if not os.path.exists(ENCODER_PATH):
        raise FileNotFoundError(f"Encoder not found at {ENCODER_PATH}")
    
    mlb = joblib.load(ENCODER_PATH)
    num_classes = len(mlb.classes_)
    
    print(f"Number of classes: {num_classes}")
    print(f"Loading classifiers from: {MODEL_DIR}")
    
    all_classifiers = []
    missing_count = 0
    
    for i in range(num_classes):
        class_name = mlb.classes_[i]
        safe_name = str(class_name).replace(" ", "_").replace("/", "_").replace(":", "_").replace(".", "_")
        clf_path = os.path.join(MODEL_DIR, f"clf_{i}_{safe_name}.pkl")
        
        if not os.path.exists(clf_path):
            alt_path = os.path.join(MODEL_DIR, f"clf_{i}_{class_name}.pkl")
            if os.path.exists(alt_path):
                clf_path = alt_path
            else:
                print(f"Missing classifier: {clf_path}")
                missing_count += 1
                continue
        
        try:
            all_classifiers.append(joblib.load(clf_path))
        except Exception as e:
            print(f"Error loading {clf_path}: {e}")
            continue
    
    print(f"Loaded {len(all_classifiers)} classifiers ({missing_count} missing)")
    print()
    
    return all_classifiers, mlb

def infer_feature_dimension(classifiers):
    if not classifiers:
        raise ValueError("No classifiers loaded")
    
    try:
        feature_dim = int(classifiers[0].coef_.shape[1])
        print(f"Inferred feature dimension: {feature_dim}")
        return feature_dim
    except Exception as e:
        print(f"Could not infer feature dimension: {e}")
        print("Using default: 768 (DINOv3 small)")
        return 768

def benchmark_single_classifier(classifiers, feature_dim, num_iterations=100):
    print("=" * 80)
    print("BENCHMARK 1: Single Classifier Inference")
    print("=" * 80)
    
    X = np.random.randn(1, feature_dim).astype(np.float32)
    
    _ = classifiers[0].predict_proba(X)
    
    times = []
    for _ in range(num_iterations):
        start = time.perf_counter()
        _ = classifiers[0].predict_proba(X)
        end = time.perf_counter()
        times.append((end - start) * 1000)
    
    avg_time = np.mean(times)
    std_time = np.std(times)
    min_time = np.min(times)
    max_time = np.max(times)
    
    print(f"Iterations: {num_iterations}")
    print(f"Average time: {avg_time:.3f} ms")
    print(f"Std dev: {std_time:.3f} ms")
    print(f"Min time: {min_time:.3f} ms")
    print(f"Max time: {max_time:.3f} ms")
    print()
    
    return avg_time

def benchmark_sequential(classifiers, feature_dim, num_iterations=10):
    print("=" * 80)
    print("BENCHMARK 2: Sequential Inference (All Classifiers)")
    print("=" * 80)
    
    X = np.random.randn(1, feature_dim).astype(np.float32)
    
    for clf in classifiers:
        _ = clf.predict_proba(X)
    
    times = []
    for _ in range(num_iterations):
        start = time.perf_counter()
        for clf in classifiers:
            _ = clf.predict_proba(X)
        end = time.perf_counter()
        times.append((end - start) * 1000)
    
    avg_time = np.mean(times)
    std_time = np.std(times)
    min_time = np.min(times)
    max_time = np.max(times)
    
    print(f"Iterations: {num_iterations}")
    print(f"Average time: {avg_time:.2f} ms")
    print(f"Std dev: {std_time:.2f} ms")
    print(f"Min time: {min_time:.2f} ms")
    print(f"Max time: {max_time:.2f} ms")
    print()
    
    return avg_time

def benchmark_parallel(classifiers, feature_dim, n_jobs_list, num_iterations=10):
    print("=" * 80)
    print("BENCHMARK 3: Parallel Inference (joblib.Parallel)")
    print("=" * 80)
    
    from joblib import Parallel, delayed
    
    X = np.random.randn(1, feature_dim).astype(np.float32)
    
    def predict_single(clf, X):
        return clf.predict_proba(X)[0, 1]
    
    results = {}
    
    for n_jobs in n_jobs_list:
        print(f"Testing with n_jobs={n_jobs}")
        
        _ = Parallel(n_jobs=n_jobs)(delayed(predict_single)(clf, X) for clf in classifiers)
        
        times = []
        for _ in range(num_iterations):
            start = time.perf_counter()
            _ = Parallel(n_jobs=n_jobs)(delayed(predict_single)(clf, X) for clf in classifiers)
            end = time.perf_counter()
            times.append((end - start) * 1000)
        
        avg_time = np.mean(times)
        std_time = np.std(times)
        
        print(f"  Average time: {avg_time:.2f} ms")
        print(f"  Std dev: {std_time:.2f} ms")
        
        results[n_jobs] = avg_time
    
    print()
    return results

def calculate_speedup(sequential_time, parallel_times):
    print("=" * 80)
    print("SPEEDUP ANALYSIS")
    print("=" * 80)
    
    print(f"Sequential time: {sequential_time:.2f} ms")
    print()
    
    for n_jobs, parallel_time in parallel_times.items():
        speedup = sequential_time / parallel_time
        print(f"n_jobs={n_jobs:2d}: {parallel_time:6.2f} ms | Speedup: {speedup:.2f}x")
    
    print()

def generate_recommendations(single_time, sequential_time, parallel_times):
    print("=" * 80)
    print("OPTIMIZATION RECOMMENDATIONS")
    print("=" * 80)
    
    TARGET_TIME = 100
    
    print(f"Target: < {TARGET_TIME} ms")
    print(f"Current sequential: {sequential_time:.2f} ms")
    print()
    
    best_n_jobs = min(parallel_times, key=parallel_times.get)
    best_time = parallel_times[best_n_jobs]
    
    if best_time < TARGET_TIME:
        print(f"TARGET ACHIEVED with parallel inference!")
        print(f"   Recommended: n_jobs={best_n_jobs} ({best_time:.2f} ms)")
        print()
        print("IMPLEMENTATION STRATEGY:")
        print(f"  1. Use joblib.Parallel with n_jobs={best_n_jobs}")
        print("  2. No additional optimization needed")
        print("  3. Proceed with implementation")
    elif sequential_time < TARGET_TIME:
        print(f"TARGET ACHIEVED with sequential inference!")
        print(f"   Sequential time: {sequential_time:.2f} ms")
        print()
        print("IMPLEMENTATION STRATEGY:")
        print("  1. Use sequential inference (simplest)")
        print("  2. No parallelization needed")
        print("  3. Proceed with implementation")
    else:
        print(f"TARGET NOT ACHIEVED")
        print(f"   Best parallel time: {best_time:.2f} ms (n_jobs={best_n_jobs})")
        print(f"   Gap: {best_time - TARGET_TIME:.2f} ms")
        print()
        print("OPTIMIZATION STRATEGIES:")
        print(f"  1. Use parallel inference with n_jobs={best_n_jobs}")
        print("  2. Consider model pruning")
        print("  3. Consider feature selection")
        print("  4. Consider GPU batch processing")
    
    print()
    
    print("FPS IMPACT ESTIMATION:")
    print(f"  If classification every frame:")
    print(f"    Sequential: {1000/sequential_time:.1f} FPS")
    print(f"    Parallel (n_jobs={best_n_jobs}): {1000/best_time:.1f} FPS")
    print()
    print(f"  With Detection-Tracking-Trigger (80%% reduction):")
    print(f"    Effective overhead: {best_time * 0.2:.2f} ms per frame")
    print(f"    Estimated FPS: {1000/(best_time * 0.2 + 50):.1f} FPS")
    print()

def main():
    print()
    print("=" * 80)
    print("CLASSIFIER PERFORMANCE BENCHMARK")
    print("=" * 80)
    print()
    
    try:
        classifiers, mlb = load_classifiers()
        
        if len(classifiers) == 0:
            print("No classifiers loaded. Cannot proceed.")
            return
        
        feature_dim = infer_feature_dimension(classifiers)
        
        single_time = benchmark_single_classifier(classifiers, feature_dim, num_iterations=100)
        sequential_time = benchmark_sequential(classifiers, feature_dim, num_iterations=10)
        parallel_times = benchmark_parallel(classifiers, feature_dim, n_jobs_list=[2, 4, 8, -1], num_iterations=10)
        
        calculate_speedup(sequential_time, parallel_times)
        generate_recommendations(single_time, sequential_time, parallel_times)
        
        results = {
            "single_classifier_time_ms": float(single_time),
            "sequential_time_ms": float(sequential_time),
            "parallel_times_ms": {str(k): float(v) for k, v in parallel_times.items()},
            "num_classifiers": len(classifiers),
            "feature_dimension": feature_dim,
            "target_time_ms": 100
        }
        
        results_path = os.path.join(BASE_PATH, "benchmark_results.json")
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"Results saved to: {results_path}")
        print()
        
        print("=" * 80)
        print("BENCHMARK COMPLETE")
        print("=" * 80)
        
    except Exception as e:
        print(f"Benchmark failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
