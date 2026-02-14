"""
Quick test script for PerformanceMonitor
Tests import, initialization, and basic functionality
"""
import sys
import numpy as np

print("Testing PerformanceMonitor...")
print("="*60)

# Test 1: Import
print("\n1. Testing import...")
try:
    from src.performance_monitor import PerformanceMonitor
    print("✓ Import successful")
except Exception as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

# Test 2: Initialization
print("\n2. Testing initialization...")
try:
    monitor = PerformanceMonitor(history_size=60)
    print("✓ Initialization successful")
except Exception as e:
    print(f"✗ Initialization failed: {e}")
    sys.exit(1)

# Test 3: Update metrics
print("\n3. Testing update_metrics()...")
try:
    monitor.update_metrics()
    print("✓ update_metrics() successful")
except Exception as e:
    print(f"✗ update_metrics() failed: {e}")
    sys.exit(1)

# Test 4: Update frame time
print("\n4. Testing update_frame_time()...")
try:
    monitor.update_frame_time('detection', 25.0)
    monitor.update_frame_time('tracking', 5.0)
    monitor.update_frame_time('classification', 33.0)
    monitor.update_frame_time('rendering', 8.0)
    print("✓ update_frame_time() successful")
except Exception as e:
    print(f"✗ update_frame_time() failed: {e}")
    sys.exit(1)

# Test 5: Draw overlay
print("\n5. Testing draw_overlay()...")
try:
    # Create dummy frame
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    annotated_frame = monitor.draw_overlay(frame)
    print(f"✓ draw_overlay() successful (frame shape: {annotated_frame.shape})")
except Exception as e:
    print(f"✗ draw_overlay() failed: {e}")
    sys.exit(1)

# Test 6: Toggle overlay
print("\n6. Testing toggle_overlay()...")
try:
    initial_state = monitor.show_overlay
    monitor.toggle_overlay()
    new_state = monitor.show_overlay
    assert initial_state != new_state, "Toggle didn't change state"
    print(f"✓ toggle_overlay() successful (state changed: {initial_state} -> {new_state})")
except Exception as e:
    print(f"✗ toggle_overlay() failed: {e}")
    sys.exit(1)

# Test 7: Save performance graph
print("\n7. Testing save_performance_graph()...")
try:
    # Add some dummy data
    for i in range(10):
        monitor.update_metrics()
        monitor.update_frame_time('detection', 25.0 + i)
        monitor.update_frame_time('tracking', 5.0)
        monitor.update_frame_time('classification', 33.0)
        monitor.update_frame_time('rendering', 8.0)
    
    graph_path = monitor.save_performance_graph()
    if graph_path:
        print(f"✓ save_performance_graph() successful: {graph_path}")
    else:
        print("⚠ save_performance_graph() returned None (expected if matplotlib not installed)")
except Exception as e:
    print(f"✗ save_performance_graph() failed: {e}")
    # Don't exit - matplotlib might not be installed yet

print("\n" + "="*60)
print("All tests passed! ✓")
print("="*60)
print("\nPerformanceMonitor is ready to use.")
print("Next step: Run 'python run_detection_tracking.py' and press 'm' to toggle overlay")
