"""
Testing Mode - Klasifikasi SEMUA botol yang terdeteksi
Tanpa perlu trigger zone atau gerakan

Gunakan untuk testing dengan botol statis
"""
import os
import sys
import cv2
import torch
import joblib
import numpy as np
import time
from datetime import datetime
from ultralytics import YOLO
from transformers import AutoImageProcessor, AutoModel
from src.tracking import DetectionTrackingPipeline
from src.tracking.trigger_zone import TriggerZoneConfig
from src.config_loader import ConfigLoader

print("="*60)
print("EKOVISION - TESTING MODE")
print("Mode: Klasifikasi SEMUA botol (no trigger zone)")
print("="*60)
print()

# Load configuration
config = ConfigLoader.load("config.yaml")

# Device configuration
if config.performance.device == "auto":
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
else:
    device = config.performance.device

print(f"Device: {device}")
print()

# Load models
print("Loading models...")

# YOLO
yolo_model = YOLO(config.models.yolo_path).to(device)
print(f"✓ YOLO model loaded")

# DINOv3
dinov3_processor = AutoImageProcessor.from_pretrained(config.models.dinov3_model)
dinov3_model = AutoModel.from_pretrained(config.models.dinov3_model).to(device).eval()
print(f"✓ DINOv3 model loaded")

# Encoder and mapping
mlb = joblib.load(config.models.encoder_path)
mapping_dict = joblib.load(config.models.mapping_path)
print(f"✓ Encoder and mapping loaded")

# Classifiers
all_classifiers = []
num_classes = len(mlb.classes_)

for i in range(num_classes):
    class_name = mlb.classes_[i]
    safe_name = str(class_name).replace(" ", "_").replace("/", "_").replace(":", "_").replace(".", "_")
    clf_path = os.path.join(config.models.classifiers_dir, f"clf_{i}_{safe_name}.pkl")
    
    if os.path.exists(clf_path):
        all_classifiers.append(joblib.load(clf_path))

print(f"✓ Loaded {len(all_classifiers)} classifiers")
print()

# Initialize pipeline
print("Initializing pipeline...")
trigger_config = TriggerZoneConfig(
    x_offset_pct=5.0,   # Full frame
    y_offset_pct=5.0,
    width_pct=90.0,
    height_pct=90.0
)

pipeline = DetectionTrackingPipeline(
    yolo_model=yolo_model,
    dinov3_processor=dinov3_processor,
    dinov3_model=dinov3_model,
    classifiers=all_classifiers,
    mlb=mlb,
    mapping_dict=mapping_dict,
    label_columns=config.labels.columns,
    frame_width=config.camera.width,
    frame_height=config.camera.height,
    confidence_threshold=config.classification.confidence_threshold,
    trigger_zone_config=trigger_config,
    max_classification_attempts=5,  # Lebih banyak retry
    device=device,
    classification_config={
        'expand_bbox_ratio': config.classification.expand_bbox_ratio,
        'min_crop_size': config.classification.min_crop_size,
        'enable_temporal_smoothing': config.classification.enable_temporal_smoothing,
        'temporal_window_size': config.classification.temporal_window_size,
        'enable_preprocessing': config.classification.enable_preprocessing,
        'enable_ensemble': config.classification.enable_ensemble
    }
)
print("✓ Pipeline initialized")

# PATCH: Disable trigger zone check untuk testing
print("\n⚠ TESTING MODE: Trigger zone check DISABLED")
print("   Semua botol akan diklasifikasi tanpa perlu masuk zone\n")

# Monkey patch the trigger zone check
original_should_trigger = pipeline._should_trigger_classification

def testing_should_trigger(track):
    """Testing mode: klasifikasi semua botol"""
    from src.tracking.bottle_tracker import TrackingState
    
    # Only classify NEW or TRACKED bottles
    if track.state not in [TrackingState.NEW, TrackingState.TRACKED]:
        return False
    
    # SKIP trigger zone check - langsung return True
    # Check if should classify (not exceeded max attempts)
    return pipeline.tracker.should_classify(track.track_id)

pipeline._should_trigger_classification = testing_should_trigger

# Initialize camera
print(f"Opening camera {config.camera.index}...")
cap = cv2.VideoCapture(config.camera.index)

if not cap.isOpened():
    print(f"✗ Failed to open camera {config.camera.index}")
    sys.exit(1)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.camera.width)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.camera.height)

actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
print(f"✓ Camera opened: {actual_width}x{actual_height}")

print("\n" + "="*60)
print("TESTING MODE ACTIVE")
print("="*60)
print("Cara Testing:")
print("  1. Tunjukkan botol ke kamera")
print("  2. Tunggu 1-2 detik")
print("  3. Klasifikasi akan muncul otomatis!")
print()
print("Controls:")
print("  - Press 'q' to quit")
print("  - Press 'r' to reset")
print("  - Press 's' to show statistics")
print("="*60 + "\n")

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            print("✗ Failed to read frame")
            break
        
        # Process frame
        annotated_frame, stats = pipeline.process_frame(frame)
        
        # Draw testing mode indicator
        cv2.putText(
            annotated_frame,
            "TESTING MODE",
            (10, actual_height - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 255),
            2
        )
        
        # Display
        cv2.imshow('EkoVision - Testing Mode', annotated_frame)
        
        # Handle keyboard
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('q'):
            print("\nQuitting...")
            break
        
        elif key == ord('r'):
            print("\nResetting pipeline...")
            pipeline.reset()
            print("✓ Pipeline reset")
        
        elif key == ord('s'):
            print("\n" + "="*60)
            print("STATISTICS")
            print("="*60)
            full_stats = pipeline.get_statistics()
            print(f"Frames processed: {full_stats['frame_count']}")
            print(f"Classifications: {full_stats['classification_count']}")
            print(f"Average FPS: {full_stats['avg_fps']:.1f}")
            print(f"\nTracker:")
            print(f"  Total tracks: {full_stats['tracker']['total_tracks']}")
            print(f"  Active tracks: {full_stats['tracker']['active_tracks']}")
            print(f"  Classified: {full_stats['tracker']['classified']}")
            print(f"  Failed: {full_stats['tracker']['failed']}")
            print("="*60 + "\n")

except KeyboardInterrupt:
    print("\n\nInterrupted by user")

finally:
    cap.release()
    cv2.destroyAllWindows()
    
    # Final statistics
    print("\n" + "="*60)
    print("FINAL STATISTICS")
    print("="*60)
    final_stats = pipeline.get_statistics()
    print(f"Total frames: {final_stats['frame_count']}")
    print(f"Total classifications: {final_stats['classification_count']}")
    print(f"Average FPS: {final_stats['avg_fps']:.1f}")
    print("="*60)
    
    print("\n✓ Testing complete")
