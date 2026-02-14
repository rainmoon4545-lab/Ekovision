"""
Real-time Detection-Tracking-Trigger System
Supports both real-time camera and batch video processing
"""
import os
import sys
import cv2
import torch
import joblib
import numpy as np
import time
import argparse
from datetime import datetime
from pathlib import Path
from ultralytics import YOLO
from transformers import AutoImageProcessor, AutoModel
from src.tracking import DetectionTrackingPipeline
from src.tracking.trigger_zone import TriggerZoneConfig
from src.config_loader import ConfigLoader
from src.data_logger import DataLogger
from src.camera_controller import CameraController
from src.performance_monitor import PerformanceMonitor
from src.batch_processor import BatchProcessor

# ========== LOAD CONFIGURATION ==========

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='EkoVision Detection-Tracking-Trigger System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Real-time camera mode (default)
  python run_detection_tracking.py
  
  # Batch process single video
  python run_detection_tracking.py --batch --input video.mp4
  
  # Batch process directory
  python run_detection_tracking.py --batch --input-dir videos/ --output-dir results/
  
  # Batch with custom settings
  python run_detection_tracking.py --batch --input-dir videos/ --no-video --csv-only
        """
    )
    
    # Mode selection
    parser.add_argument(
        '--batch',
        action='store_true',
        help='Enable batch processing mode (offline video processing)'
    )
    
    parser.add_argument(
        '--web',
        action='store_true',
        help='Enable web dashboard mode (browser-based interface)'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=5000,
        help='Port for web dashboard (default: 5000)'
    )
    
    # Input options
    parser.add_argument(
        '--input',
        type=str,
        help='Input video file for batch processing'
    )
    
    parser.add_argument(
        '--input-dir',
        type=str,
        help='Input directory containing videos for batch processing'
    )
    
    parser.add_argument(
        '--pattern',
        type=str,
        default='*.mp4',
        help='File pattern for batch directory processing (default: *.mp4)'
    )
    
    # Output options
    parser.add_argument(
        '--output-dir',
        type=str,
        default='batch_output',
        help='Output directory for batch processing (default: batch_output)'
    )
    
    parser.add_argument(
        '--no-video',
        action='store_true',
        help='Do not save annotated video in batch mode'
    )
    
    parser.add_argument(
        '--no-json',
        action='store_true',
        help='Do not save JSON data in batch mode'
    )
    
    parser.add_argument(
        '--csv-only',
        action='store_true',
        help='Save only CSV data in batch mode'
    )
    
    # Configuration
    parser.add_argument(
        '--config',
        type=str,
        default='config.yaml',
        help='Path to configuration file (default: config.yaml)'
    )
    
    parser.add_argument(
        '--no-progress',
        action='store_true',
        help='Disable progress bars in batch mode'
    )
    
    return parser.parse_args()


print("="*60)
print("EKOVISION DETECTION-TRACKING-TRIGGER SYSTEM")
print("="*60)
print()

# Load configuration from config.yaml
config = ConfigLoader.load("config.yaml")

# Extract configuration values
CAMERA_INDEX = config.camera.index
FRAME_WIDTH = config.camera.width
FRAME_HEIGHT = config.camera.height

CONFIDENCE_THRESHOLD = config.detection.confidence_threshold

YOLO_MODEL_PATH = config.models.yolo_path
DINOV3_MODEL_NAME = config.models.dinov3_model
ENCODER_PATH = config.models.encoder_path
MAPPING_SAVE_PATH = config.models.mapping_path
MODEL_DIR = config.models.classifiers_dir

LABEL_COLUMNS = config.labels.columns

# Device configuration
if config.performance.device == "auto":
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
elif config.performance.device == "cuda":
    if torch.cuda.is_available():
        device = 'cuda'
    else:
        print("⚠ CUDA requested but not available, falling back to CPU")
        device = 'cpu'
else:
    device = 'cpu'

print(f"Device: {device}")
print()

# ========== LOAD MODELS ==========

def load_models():
    """Load all required models."""
    print("Loading models...")
    
    # YOLO
    if not os.path.exists(YOLO_MODEL_PATH):
        raise FileNotFoundError(f"YOLO model not found: {YOLO_MODEL_PATH}")
    yolo_model = YOLO(YOLO_MODEL_PATH).to(device)
    print(f"✓ YOLO model loaded")
    
    # DINOv3
    dinov3_processor = AutoImageProcessor.from_pretrained(DINOV3_MODEL_NAME)
    dinov3_model = AutoModel.from_pretrained(DINOV3_MODEL_NAME).to(device).eval()
    print(f"✓ DINOv3 model loaded")
    
    # Encoder and mapping
    if not os.path.exists(ENCODER_PATH):
        raise FileNotFoundError(f"Encoder not found: {ENCODER_PATH}")
    if not os.path.exists(MAPPING_SAVE_PATH):
        raise FileNotFoundError(f"Mapping not found: {MAPPING_SAVE_PATH}")
    
    mlb = joblib.load(ENCODER_PATH)
    mapping_dict = joblib.load(MAPPING_SAVE_PATH)
    print(f"✓ Encoder and mapping loaded")
    
    # Classifiers
    all_classifiers = []
    missing_count = 0
    num_classes = len(mlb.classes_)
    
    for i in range(num_classes):
        class_name = mlb.classes_[i]
        safe_name = str(class_name).replace(" ", "_").replace("/", "_").replace(":", "_").replace(".", "_")
        clf_path = os.path.join(MODEL_DIR, f"clf_{i}_{safe_name}.pkl")
        
        if not os.path.exists(clf_path):
            alt_path = os.path.join(MODEL_DIR, f"clf_{i}_{class_name}.pkl")
            if os.path.exists(alt_path):
                clf_path = alt_path
            else:
                print(f"⚠ Missing classifier: {clf_path}")
                missing_count += 1
                continue
        
        try:
            all_classifiers.append(joblib.load(clf_path))
        except Exception as e:
            print(f"✗ Error loading {clf_path}: {e}")
            continue
    
    print(f"✓ Loaded {len(all_classifiers)} classifiers ({missing_count} missing)")
    
    return yolo_model, dinov3_processor, dinov3_model, mlb, mapping_dict, all_classifiers


# ========== BATCH PROCESSING ==========

def batch_process(args, pipeline):
    """
    Batch process videos offline.
    
    Args:
        args: Command line arguments
        pipeline: DetectionTrackingPipeline instance
    """
    print("\n" + "="*60)
    print("BATCH PROCESSING MODE")
    print("="*60)
    
    # Initialize batch processor
    processor = BatchProcessor(
        pipeline=pipeline,
        output_dir=args.output_dir,
        save_video=not args.no_video,
        save_json=not args.no_json and not args.csv_only,
        save_csv=True
    )
    
    print(f"Output directory: {args.output_dir}")
    print(f"Save video: {not args.no_video}")
    print(f"Save JSON: {not args.no_json and not args.csv_only}")
    print(f"Save CSV: True")
    print()
    
    # Process single video or directory
    if args.input:
        # Single video
        print(f"Processing video: {args.input}")
        result = processor.process_video(
            args.input,
            show_progress=not args.no_progress
        )
        
        if result.success:
            print(f"\n✓ Processing complete!")
            print(f"  Frames: {result.frames_processed}")
            print(f"  Classifications: {result.classifications}")
            print(f"  Average FPS: {result.avg_fps:.1f}")
            print(f"  Duration: {result.duration_seconds:.1f}s")
        else:
            print(f"\n✗ Processing failed: {result.error_message}")
            return 1
    
    elif args.input_dir:
        # Directory of videos
        print(f"Processing directory: {args.input_dir}")
        print(f"Pattern: {args.pattern}")
        print()
        
        results = processor.process_directory(
            args.input_dir,
            pattern=args.pattern,
            show_progress=not args.no_progress
        )
        
        if not results:
            print("\n✗ No videos processed")
            return 1
    
    else:
        print("✗ Error: --input or --input-dir required for batch mode")
        print("Use --help for usage information")
        return 1
    
    # Generate and save report
    processor.print_summary()
    processor.save_report()
    
    print("\n✓ Batch processing complete!")
    return 0


# ========== MAIN APPLICATION ==========

def main():
    """Main application entry point."""
    
    # Parse command line arguments
    args = parse_arguments()
    
    # Load configuration
    config = ConfigLoader.load(args.config)
    
    # Load models
    try:
        yolo_model, dinov3_processor, dinov3_model, mlb, mapping_dict, all_classifiers = load_models()
    except Exception as e:
        print(f"✗ Failed to load models: {e}")
        return 1
    
    # Initialize pipeline (common for both modes)
    print("\nInitializing Detection-Tracking-Trigger pipeline...")
    trigger_config = TriggerZoneConfig(
        x_offset_pct=config.trigger_zone.x_offset_pct,
        y_offset_pct=config.trigger_zone.y_offset_pct,
        width_pct=config.trigger_zone.width_pct,
        height_pct=config.trigger_zone.height_pct
    )
    
    # Determine frame size for pipeline
    if args.batch and args.input:
        # Get size from input video
        cap_temp = cv2.VideoCapture(args.input)
        frame_width = int(cap_temp.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap_temp.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap_temp.release()
    else:
        # Use config defaults
        frame_width = config.camera.width
        frame_height = config.camera.height
    
    pipeline = DetectionTrackingPipeline(
        yolo_model=yolo_model,
        dinov3_processor=dinov3_processor,
        dinov3_model=dinov3_model,
        classifiers=all_classifiers,
        mlb=mlb,
        mapping_dict=mapping_dict,
        label_columns=config.labels.columns,
        frame_width=frame_width,
        frame_height=frame_height,
        confidence_threshold=config.classification.confidence_threshold,
        trigger_zone_config=trigger_config,
        max_classification_attempts=config.tracking.max_classification_attempts,
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
    
    # Choose mode
    if args.batch:
        # Batch processing mode
        return batch_process(args, pipeline)
    else:
        # Real-time camera mode
        return realtime_camera_mode(config, pipeline)


def realtime_camera_mode(config, pipeline):
    """Real-time camera processing mode."""
def realtime_camera_mode(config, pipeline):
    """Real-time camera processing mode."""
    
    # Initialize camera
    print(f"\nOpening camera {config.camera.index}...")
    cap = cv2.VideoCapture(config.camera.index)
    
    if not cap.isOpened():
        print(f"✗ Failed to open camera {config.camera.index}")
        return 1
    
    # Set camera resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.camera.width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.camera.height)
    
    # Get actual resolution
    actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"✓ Camera opened: {actual_width}x{actual_height}")
    
    # Initialize data logger
    print("\nInitializing data logger...")
    logger = DataLogger(output_dir="exports")
    print("✓ Data logger initialized")
    
    # Initialize camera controller
    print("\nInitializing camera controller...")
    camera_ctrl = CameraController(cap)
    print("✓ Camera controller initialized")
    camera_ctrl.print_settings()
    
    # Initialize performance monitor
    print("\nInitializing performance monitor...")
    perf_monitor = PerformanceMonitor(history_size=60)
    print("✓ Performance monitor initialized")
    
    print("\n" + "="*60)
    print("DETECTION-TRACKING-TRIGGER SYSTEM RUNNING")
    print("="*60)
    print("Controls:")
    print("  - Press 'q' to quit")
    print("  - Press 'r' to reset pipeline")
    print("  - Press 's' to show statistics")
    print("  - Press 't' to toggle trigger zone visibility")
    print("  - Press 'e' to export CSV")
    print("  - Press 'j' to export JSON")
    print("  - Press 'v' to start/stop video recording")
    print("  - Press 'c' to open camera controls")
    print("  - Press 'm' to toggle performance overlay")
    print("  - Press 'g' to save performance graph")
    print("="*60 + "\n")
    
    show_trigger_zone = config.display.show_trigger_zone
    camera_control_mode = False
    frame_count = 0
    
    try:
        while True:
            # Read frame
            ret, frame = cap.read()
            if not ret:
                print("✗ Failed to read frame")
                break
            
            frame_count += 1
            
            # Start frame timing
            frame_start = time.time()
            
            # Process frame through pipeline (with stage timing)
            detection_start = time.time()
            annotated_frame, stats = pipeline.process_frame(frame)
            detection_time = (time.time() - detection_start) * 1000
            
            # Update performance metrics
            perf_monitor.update_frame_time('detection', detection_time)
            perf_monitor.update_metrics()
            
            # Log frame processing
            logger.log_frame(fps=stats.get('fps', 0))
            
            # Log detections
            tracks = pipeline.tracker.get_active_tracks()
            for track in tracks:
                logger.log_detection(
                    timestamp=datetime.now().isoformat(),
                    track_id=track.track_id,
                    bbox=track.bbox,
                    confidence=track.confidence,
                    state=track.state.value,
                    classification=track.classification_results
                )
            
            # Log classifications
            if stats.get('classifications', 0) > 0:
                logger.log_classification()
            
            # Write frame to video if recording
            if logger.is_recording:
                logger.write_frame(annotated_frame)
                # Draw recording indicator
                cv2.circle(annotated_frame, (30, 90), 10, (0, 0, 255), -1)
                cv2.putText(
                    annotated_frame,
                    "REC",
                    (50, 95),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 0, 255),
                    2
                )
            
            # Draw performance overlay
            annotated_frame = perf_monitor.draw_overlay(annotated_frame)
            
            # Display frame
            cv2.imshow('EkoVision - Detection-Tracking-Trigger', annotated_frame)
            
            # Handle keyboard input
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
                print(f"Reduction: {full_stats['reduction_percentage']:.1f}%")
                print(f"Average FPS: {full_stats['avg_fps']:.1f}")
                print(f"\nTracker:")
                print(f"  Total tracks: {full_stats['tracker']['total_tracks']}")
                print(f"  Active tracks: {full_stats['tracker']['active_tracks']}")
                print(f"  Classified: {full_stats['tracker']['classified']}")
                print(f"  Failed: {full_stats['tracker']['failed']}")
                print(f"\nCache:")
                print(f"  Size: {full_stats['cache']['size']}/{full_stats['cache']['max_size']}")
                print(f"  Hit rate: {full_stats['cache']['hit_rate']:.1%}")
                print(f"  Hits: {full_stats['cache']['hits']}")
                print(f"  Misses: {full_stats['cache']['misses']}")
                print("="*60 + "\n")
            
            elif key == ord('t'):
                pipeline.toggle_trigger_zone_visibility()
                show_trigger_zone = pipeline.show_trigger_zone
                print(f"Trigger zone visibility: {'ON' if show_trigger_zone else 'OFF'}")
            
            elif key == ord('e'):
                print("\nExporting CSV...")
                logger.export_csv()
            
            elif key == ord('j'):
                print("\nExporting JSON...")
                logger.export_json()
            
            elif key == ord('v'):
                if logger.is_recording:
                    print("\nStopping video recording...")
                    logger.stop_recording()
                else:
                    print("\nStarting video recording...")
                    logger.start_recording(actual_width, actual_height, fps=30)
            
            elif key == ord('c'):
                camera_control_mode = not camera_control_mode
                if camera_control_mode:
                    print("\n" + "="*60)
                    print("CAMERA CONTROL MODE ACTIVE")
                    camera_ctrl.show_controls_help()
                else:
                    print("\nCamera control mode closed")
            
            elif key == ord('m'):
                perf_monitor.toggle_overlay()
                print(f"Performance overlay: {'ON' if perf_monitor.show_overlay else 'OFF'}")
            
            elif key == ord('g'):
                print("\nSaving performance graph...")
                graph_path = perf_monitor.save_performance_graph()
                if graph_path:
                    print(f"✓ Graph saved: {graph_path}")
                else:
                    print("✗ Failed to save graph")
            
            # Camera controls (only active when in camera control mode)
            if camera_control_mode:
                if key == ord('['):
                    camera_ctrl.adjust_exposure(-1)
                    camera_ctrl.print_settings()
                
                elif key == ord(']'):
                    camera_ctrl.adjust_exposure(1)
                    camera_ctrl.print_settings()
                
                elif key == ord('-') or key == ord('_'):
                    camera_ctrl.adjust_brightness(-5)
                    camera_ctrl.print_settings()
                
                elif key == ord('+') or key == ord('='):
                    camera_ctrl.adjust_brightness(5)
                    camera_ctrl.print_settings()
                
                elif key == ord('a'):
                    camera_ctrl.set_auto_exposure(not camera_ctrl.auto_exposure)
                    camera_ctrl.print_settings()
                
                elif key == ord('1'):
                    camera_ctrl.load_preset("Indoor")
                    camera_ctrl.print_settings()
                
                elif key == ord('2'):
                    camera_ctrl.load_preset("Outdoor")
                    camera_ctrl.print_settings()
                
                elif key == ord('3'):
                    camera_ctrl.load_preset("High Speed")
                    camera_ctrl.print_settings()
    
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    
    finally:
        # Cleanup
        print("\nCleaning up...")
        
        # Stop recording if active
        if logger.is_recording:
            logger.stop_recording()
        
        cap.release()
        cv2.destroyAllWindows()
        
        # Final statistics
        print("\n" + "="*60)
        print("FINAL STATISTICS")
        print("="*60)
        final_stats = pipeline.get_statistics()
        print(f"Total frames: {final_stats['frame_count']}")
        print(f"Total classifications: {final_stats['classification_count']}")
        print(f"Computational reduction: {final_stats['reduction_percentage']:.1f}%")
        print(f"Average FPS: {final_stats['avg_fps']:.1f}")
        print("="*60)
        
        # Save session summary
        print("\nSaving session summary...")
        logger.save_summary()
        logger.print_summary()
        
        print("\n✓ System shutdown complete")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
