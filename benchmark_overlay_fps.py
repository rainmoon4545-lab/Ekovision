"""
Benchmark script to measure FPS impact of ClassificationOverlay.
Tests overlay rendering performance with and without the overlay enabled.
"""

import time
import numpy as np
from src.tracking.classification_overlay import ClassificationOverlay
from src.tracking.bottle_tracker import BottleTrack, TrackingState

def create_test_frame(width=1920, height=1080):
    """Create a test frame."""
    return np.random.randint(0, 255, (height, width, 3), dtype=np.uint8)

def create_test_tracks(num_tracks=3):
    """Create test tracks with classification results."""
    tracks = []
    for i in range(num_tracks):
        track = BottleTrack(
            track_id=i + 1,
            bbox=np.array([100 + i * 200, 100, 200 + i * 200, 400]),
            confidence=0.95,
            state=TrackingState.CLASSIFIED
        )
        track.classification_results = {
            'product': 'Aqua',
            'grade': 'A',
            'cap': 'Blue',
            'label': 'Complete',
            'brand': 'Danone',
            'type': 'PET',
            'subtype': '600ml',
            'volume': '600ml'
        }
        tracks.append(track)
    return tracks

def create_cache(tracks):
    """Create classification cache from tracks."""
    cache = {}
    for track in tracks:
        cache[track.track_id] = track.classification_results
    return cache

def benchmark_without_overlay(num_frames=100):
    """Benchmark frame processing without overlay."""
    import cv2
    frame = create_test_frame()
    tracks = create_test_tracks(3)
    
    start_time = time.time()
    for _ in range(num_frames):
        # Simulate realistic frame processing (similar to pipeline rendering)
        annotated = frame.copy()
        
        # Draw bounding boxes (simulating existing rendering)
        for track in tracks:
            x1, y1, x2, y2 = track.bbox.astype(int)
            cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Draw track ID
            cv2.putText(annotated, f"ID: {track.track_id}", (x1, y1 - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            # Draw classification labels (simulating per-bottle labels)
            y_offset = y1 + 20
            for attr, value in track.classification_results.items():
                text = f"{attr}: {value}"
                cv2.putText(annotated, text, (x1, y_offset),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                y_offset += 20
    end_time = time.time()
    
    elapsed = end_time - start_time
    fps = num_frames / elapsed
    return fps, elapsed

def benchmark_with_overlay(num_frames=100):
    """Benchmark frame processing with overlay."""
    import cv2
    frame = create_test_frame()
    tracks = create_test_tracks(3)
    cache = create_cache(tracks)
    overlay = ClassificationOverlay()
    
    start_time = time.time()
    for _ in range(num_frames):
        # Simulate realistic frame processing (similar to pipeline rendering)
        annotated = frame.copy()
        
        # Draw bounding boxes (simulating existing rendering)
        for track in tracks:
            x1, y1, x2, y2 = track.bbox.astype(int)
            cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Draw track ID
            cv2.putText(annotated, f"ID: {track.track_id}", (x1, y1 - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            # Draw classification labels (simulating per-bottle labels)
            y_offset = y1 + 20
            for attr, value in track.classification_results.items():
                text = f"{attr}: {value}"
                cv2.putText(annotated, text, (x1, y_offset),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                y_offset += 20
        
        # Add overlay rendering
        annotated = overlay.render(annotated, tracks, cache)
    end_time = time.time()
    
    elapsed = end_time - start_time
    fps = num_frames / elapsed
    return fps, elapsed

def main():
    print("=" * 60)
    print("Classification Overlay FPS Benchmark")
    print("=" * 60)
    
    num_frames = 100
    print(f"\nBenchmarking with {num_frames} frames...")
    print(f"Frame size: 1920x1080")
    print(f"Number of tracks: 3")
    
    # Warm-up
    print("\nWarming up...")
    benchmark_without_overlay(10)
    benchmark_with_overlay(10)
    
    # Benchmark without overlay
    print("\nBenchmarking WITHOUT overlay...")
    fps_without, time_without = benchmark_without_overlay(num_frames)
    print(f"  FPS: {fps_without:.2f}")
    print(f"  Time: {time_without:.3f}s")
    print(f"  Avg frame time: {(time_without / num_frames) * 1000:.2f}ms")
    
    # Benchmark with overlay
    print("\nBenchmarking WITH overlay...")
    fps_with, time_with = benchmark_with_overlay(num_frames)
    print(f"  FPS: {fps_with:.2f}")
    print(f"  Time: {time_with:.3f}s")
    print(f"  Avg frame time: {(time_with / num_frames) * 1000:.2f}ms")
    
    # Calculate impact
    fps_drop = fps_without - fps_with
    fps_drop_percent = (fps_drop / fps_without) * 100
    time_overhead = time_with - time_without
    time_overhead_percent = (time_overhead / time_without) * 100
    
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"FPS without overlay: {fps_without:.2f}")
    print(f"FPS with overlay:    {fps_with:.2f}")
    print(f"FPS drop:            {fps_drop:.2f} ({fps_drop_percent:.2f}%)")
    print(f"\nTime overhead:       {time_overhead:.3f}s ({time_overhead_percent:.2f}%)")
    print(f"Per-frame overhead:  {(time_overhead / num_frames) * 1000:.2f}ms")
    
    # Check if within acceptable range
    print("\n" + "=" * 60)
    if fps_drop_percent <= 5.0:
        print("✓ PASS: FPS impact is within acceptable range (<= 5%)")
    else:
        print(f"✗ FAIL: FPS impact ({fps_drop_percent:.2f}%) exceeds 5% threshold")
    print("=" * 60)
    
    return fps_drop_percent <= 5.0

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
