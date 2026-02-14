"""
Script untuk debug masalah klasifikasi tidak muncul.
Menampilkan informasi detail tentang proses klasifikasi.
"""
import cv2
import numpy as np
from src.tracking.pipeline import DetectionTrackingPipeline
from src.config_loader import load_config

print("="*70)
print("DEBUG KLASIFIKASI EKOVISION")
print("="*70)

# Load config
print("\n1. Loading configuration...")
config = load_config("config.yaml")
print(f"✓ Config loaded")
print(f"  - Camera ID: {config.camera.camera_id}")
print(f"  - Confidence threshold: {config.detection.confidence_threshold}")
print(f"  - Trigger zone: {config.trigger_zone.x_offset_pct}%, {config.trigger_zone.y_offset_pct}%")

# Initialize pipeline
print("\n2. Initializing pipeline...")
pipeline = DetectionTrackingPipeline(config)
print(f"✓ Pipeline initialized")
print(f"  - Device: {pipeline.device}")
print(f"  - Classifiers loaded: {len(pipeline.classifiers)}")

# Open camera
print("\n3. Opening camera...")
cap = cv2.VideoCapture(config.camera.camera_id)
if not cap.isOpened():
    print("✗ Failed to open camera")
    exit(1)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.camera.width)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.camera.height)
print(f"✓ Camera opened")

print("\n" + "="*70)
print("MONITORING KLASIFIKASI")
print("="*70)
print("\nInstruksi:")
print("  - Masukkan botol ke dalam trigger zone (kotak hijau)")
print("  - Perhatikan console untuk log detail")
print("  - Tekan 'q' untuk quit")
print("  - Tekan 't' untuk toggle trigger zone")
print("  - Tekan 's' untuk show statistics")
print("\n" + "="*70)

frame_count = 0
show_trigger_zone = True

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            print("✗ Failed to read frame")
            break
        
        frame_count += 1
        
        # Process frame
        annotated, stats = pipeline.process_frame(frame, show_trigger_zone=show_trigger_zone)
        
        # Log setiap 30 frame (1 detik pada 30 FPS)
        if frame_count % 30 == 0:
            print(f"\n[Frame {frame_count}]")
            print(f"  Active tracks: {stats['active_tracks']}")
            print(f"  Total classifications: {stats['classifications']}")
            print(f"  Cache size: {stats['cache_size']}")
            print(f"  FPS: {stats['avg_fps']:.1f}")
        
        # Log detail untuk setiap track
        tracks = pipeline.tracker.tracks
        for track_id, track in tracks.items():
            if track.state.value == "CLASSIFIED":
                # Track sudah diklasifikasi
                if frame_count % 30 == 0:  # Log setiap 1 detik
                    results = pipeline.cache.get(track_id)
                    if results:
                        print(f"\n  Track ID {track_id}: CLASSIFIED")
                        for key, value in results.items():
                            print(f"    - {key}: {value}")
            elif track.state.value == "TRACKED":
                # Track sedang di-track, cek apakah di trigger zone
                center_x, center_y = track.get_center()
                in_zone = pipeline.trigger_zone.contains_point(center_x, center_y)
                if in_zone and frame_count % 30 == 0:
                    print(f"\n  Track ID {track_id}: IN TRIGGER ZONE (waiting classification)")
                    print(f"    - Center: ({center_x:.0f}, {center_y:.0f})")
                    print(f"    - Classification attempts: {track.classification_attempts}")
            elif track.state.value == "FAILED":
                if frame_count % 30 == 0:
                    print(f"\n  Track ID {track_id}: CLASSIFICATION FAILED")
                    print(f"    - Attempts: {track.classification_attempts}")
        
        # Display frame
        cv2.imshow("Debug Classification", annotated)
        
        # Keyboard controls
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            print("\n✓ Quit requested")
            break
        elif key == ord('t'):
            show_trigger_zone = not show_trigger_zone
            print(f"\n✓ Trigger zone: {'ON' if show_trigger_zone else 'OFF'}")
        elif key == ord('s'):
            print("\n" + "="*70)
            print("STATISTICS")
            print("="*70)
            stats = pipeline.get_statistics()
            for key, value in stats.items():
                print(f"  {key}: {value}")
            print("="*70)

except KeyboardInterrupt:
    print("\n✓ Interrupted by user")

finally:
    cap.release()
    cv2.destroyAllWindows()
    print("\n" + "="*70)
    print("FINAL STATISTICS")
    print("="*70)
    stats = pipeline.get_statistics()
    print(f"  Total frames: {frame_count}")
    print(f"  Total classifications: {stats['total_classifications']}")
    print(f"  Success rate: {stats['classification_success_rate']:.1f}%")
    print(f"  Cache hits: {stats['cache_stats']['hits']}")
    print(f"  Cache misses: {stats['cache_stats']['misses']}")
    print("="*70)
