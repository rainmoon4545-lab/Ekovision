"""
Run EkoVision with optimized configuration for low-end laptops.

This script uses config.optimized.yaml which is tuned for:
- Intel i3 CPU
- 4GB RAM
- No dedicated GPU

Expected FPS: 15-25 FPS (vs 1-2 FPS with default config)
"""

import sys
import yaml
import cv2
import torch
import numpy as np
from pathlib import Path

# Import components
from src.tracking.pipeline import DetectionTrackingPipeline
from src.tracking.trigger_zone import TriggerZoneConfig
from src.config_loader import load_config
from src.camera_controller import CameraController
from src.data_logger import DataLogger

def main():
    print("=" * 60)
    print("EkoVision - OPTIMIZED MODE")
    print("=" * 60)
    print("\nLoading optimized configuration...")
    
    # Load optimized config
    config_path = "config.optimized.yaml"
    if not Path(config_path).exists():
        print(f"ERROR: {config_path} not found!")
        print("Please ensure config.optimized.yaml exists in the project root.")
        sys.exit(1)
    
    config = load_config(config_path)
    
    print("\n📊 OPTIMIZED SETTINGS:")
    print(f"  - Resolution: {config['camera']['width']}x{config['camera']['height']}")
    print(f"  - Skip Frames: {config['classification'].get('skip_frames', 0)}")
    print(f"  - Max Tracks: {config['tracking']['max_tracks']}")
    print(f"  - Preprocessing: {config['classification']['enable_preprocessing']}")
    print(f"  - Temporal Smoothing: {config['classification']['enable_temporal_smoothing']}")
    print(f"  - Overlay: {config['classification'].get('show_overlay', True)}")
    print(f"  - Device: {config['performance']['device']}")
    
    print("\n🎯 EXPECTED PERFORMANCE:")
    print("  - Target FPS: 15-25 FPS")
    print("  - Trade-off: Slightly reduced accuracy for better speed")
    
    print("\n⌨️  KEYBOARD CONTROLS:")
    print("  - Q: Quit")
    print("  - T: Toggle trigger zone")
    print("  - S: Save current frame")
    print("  - R: Reset tracker")
    print("  - SPACE: Pause/Resume")
    
    print("\n" + "=" * 60)
    print("Loading models...")
    
    # Load models (same as run_detection_tracking.py)
    from ultralytics import YOLO
    from transformers import AutoImageProcessor, AutoModel
    import joblib
    
    # YOLO
    yolo_model = YOLO(config['models']['yolo_path'])
    print(f"✓ YOLO model loaded: {config['models']['yolo_path']}")
    
    # DINOv3
    dinov3_processor = AutoImageProcessor.from_pretrained(config['models']['dinov3_model'])
    dinov3_model = AutoModel.from_pretrained(config['models']['dinov3_model'])
    device = 'cpu'  # Force CPU for low-end laptop
    dinov3_model = dinov3_model.to(device)
    dinov3_model.eval()
    print(f"✓ DINOv3 model loaded on {device}")
    
    # Classifiers
    classifiers_dir = Path(config['models']['classifiers_dir'])
    classifiers = []
    for clf_file in sorted(classifiers_dir.glob("*.pkl")):
        clf = joblib.load(clf_file)
        classifiers.append(clf)
    print(f"✓ Loaded {len(classifiers)} classifiers")
    
    # Label encoder and mapping
    mlb = joblib.load(config['models']['encoder_path'])
    mapping_dict = joblib.load(config['models']['mapping_path'])
    print("✓ Label encoder and mapping loaded")
    
    # Initialize camera
    camera = CameraController(
        camera_index=config['camera']['index'],
        width=config['camera']['width'],
        height=config['camera']['height']
    )
    
    if not camera.is_opened():
        print("ERROR: Could not open camera!")
        sys.exit(1)
    
    print(f"✓ Camera opened: {config['camera']['width']}x{config['camera']['height']}")
    
    # Initialize trigger zone
    trigger_zone_config = TriggerZoneConfig(
        x_offset_pct=config['trigger_zone']['x_offset_pct'],
        y_offset_pct=config['trigger_zone']['y_offset_pct'],
        width_pct=config['trigger_zone']['width_pct'],
        height_pct=config['trigger_zone']['height_pct']
    )
    
    # Initialize pipeline
    pipeline = DetectionTrackingPipeline(
        yolo_model=yolo_model,
        dinov3_processor=dinov3_processor,
        dinov3_model=dinov3_model,
        classifiers=classifiers,
        mlb=mlb,
        mapping_dict=mapping_dict,
        label_columns=config['labels']['columns'],
        frame_width=config['camera']['width'],
        frame_height=config['camera']['height'],
        confidence_threshold=config['detection']['confidence_threshold'],
        trigger_zone_config=trigger_zone_config,
        max_classification_attempts=config['tracking']['max_classification_attempts'],
        device=device,
        classification_config=config['classification']
    )
    
    print("✓ Pipeline initialized")
    print("\n" + "=" * 60)
    print("🚀 STARTING OPTIMIZED MODE...")
    print("=" * 60 + "\n")
    
    # Initialize data logger
    logger = DataLogger(
        log_dir="exports",
        enable_logging=True
    )
    
    # Main loop
    paused = False
    frame_count = 0
    
    try:
        while True:
            if not paused:
                # Read frame
                ret, frame = camera.read()
                if not ret:
                    print("ERROR: Failed to read frame")
                    break
                
                # Process frame
                annotated_frame, stats = pipeline.process_frame(frame)
                
                # Display
                cv2.imshow('EkoVision - OPTIMIZED', annotated_frame)
                
                # Log statistics every 30 frames
                if frame_count % 30 == 0:
                    print(f"Frame {frame_count}: FPS={stats['avg_fps']:.1f}, "
                          f"Tracks={stats['active_tracks']}, "
                          f"Classifications={stats['classifications']}")
                
                frame_count += 1
            else:
                # Paused - just wait for key
                cv2.waitKey(100)
            
            # Handle keyboard input
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q'):
                print("\nQuitting...")
                break
            elif key == ord('t'):
                pipeline.show_trigger_zone = not pipeline.show_trigger_zone
                print(f"Trigger zone: {'ON' if pipeline.show_trigger_zone else 'OFF'}")
            elif key == ord('s'):
                filename = f"frame_{frame_count}.jpg"
                cv2.imwrite(filename, annotated_frame)
                print(f"Saved: {filename}")
            elif key == ord('r'):
                pipeline.reset()
                print("Tracker reset")
            elif key == ord(' '):
                paused = not paused
                print(f"{'PAUSED' if paused else 'RESUMED'}")
    
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    
    finally:
        # Cleanup
        print("\n" + "=" * 60)
        print("FINAL STATISTICS")
        print("=" * 60)
        
        final_stats = pipeline.get_statistics()
        print(f"Total frames: {final_stats['frame_count']}")
        print(f"Total classifications: {final_stats['classification_count']}")
        print(f"Average FPS: {final_stats['avg_fps']:.2f}")
        print(f"Cache hit rate: {final_stats['cache']['hit_rate']:.1f}%")
        
        # Export summary
        logger.export_summary(final_stats)
        
        camera.release()
        cv2.destroyAllWindows()
        print("\n✓ Cleanup complete")

if __name__ == "__main__":
    main()
