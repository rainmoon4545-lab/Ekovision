"""
EkoVision Web Dashboard

Run the detection system with web-based interface.

Usage:
    python run_web_dashboard.py [--port 5000] [--host 0.0.0.0]
"""

import os
import sys
import cv2
import torch
import joblib
import argparse
import threading
from ultralytics import YOLO
from transformers import AutoImageProcessor, AutoModel
from src.tracking import DetectionTrackingPipeline
from src.tracking.trigger_zone import TriggerZoneConfig
from src.config_loader import ConfigLoader
from src.data_logger import DataLogger
from src.performance_monitor import PerformanceMonitor
from src.web_dashboard.app import WebDashboard


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='EkoVision Web Dashboard',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default='config.yaml',
        help='Path to configuration file (default: config.yaml)'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=5000,
        help='Web server port (default: 5000)'
    )
    
    parser.add_argument(
        '--host',
        type=str,
        default='0.0.0.0',
        help='Web server host (default: 0.0.0.0)'
    )
    
    parser.add_argument(
        '--camera',
        type=int,
        help='Camera index (overrides config)'
    )
    
    return parser.parse_args()


def load_models(config, device):
    """Load all required models."""
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
    
    return yolo_model, dinov3_processor, dinov3_model, mlb, mapping_dict, all_classifiers


def camera_loop(cap, pipeline, logger, perf_monitor, dashboard):
    """Camera processing loop."""
    print("\nStarting camera loop...")
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("✗ Failed to read frame")
                break
            
            # Process frame
            annotated_frame, stats = pipeline.process_frame(frame)
            
            # Update performance monitor
            if perf_monitor:
                perf_monitor.update_metrics()
                annotated_frame = perf_monitor.draw_overlay(annotated_frame)
            
            # Log frame
            logger.log_frame(fps=stats.get('fps', 0))
            
            # Log detections
            tracks = pipeline.tracker.get_active_tracks()
            for track in tracks:
                logger.log_detection(
                    timestamp="",
                    track_id=track.track_id,
                    bbox=track.bbox,
                    confidence=track.confidence,
                    state=track.state.value,
                    classification=track.classification_results
                )
            
            # Update dashboard frame
            dashboard.update_frame(annotated_frame)
    
    except Exception as e:
        print(f"✗ Camera loop error: {e}")
    
    finally:
        cap.release()
        print("✓ Camera loop stopped")


def main():
    """Main application."""
    args = parse_arguments()
    
    print("="*60)
    print("EKOVISION WEB DASHBOARD")
    print("="*60)
    print()
    
    # Load configuration
    config = ConfigLoader.load(args.config)
    
    # Override camera if specified
    if args.camera is not None:
        config.camera.index = args.camera
    
    # Device configuration
    if config.performance.device == "auto":
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
    else:
        device = config.performance.device
    
    print(f"Device: {device}")
    print()
    
    # Load models
    try:
        yolo_model, dinov3_processor, dinov3_model, mlb, mapping_dict, all_classifiers = load_models(config, device)
    except Exception as e:
        print(f"✗ Failed to load models: {e}")
        return 1
    
    # Initialize camera
    print(f"\nOpening camera {config.camera.index}...")
    cap = cv2.VideoCapture(config.camera.index)
    
    if not cap.isOpened():
        print(f"✗ Failed to open camera {config.camera.index}")
        return 1
    
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.camera.width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.camera.height)
    
    actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"✓ Camera opened: {actual_width}x{actual_height}")
    
    # Initialize pipeline
    print("\nInitializing pipeline...")
    trigger_config = TriggerZoneConfig(
        x_offset_pct=config.trigger_zone.x_offset_pct,
        y_offset_pct=config.trigger_zone.y_offset_pct,
        width_pct=config.trigger_zone.width_pct,
        height_pct=config.trigger_zone.height_pct
    )
    
    pipeline = DetectionTrackingPipeline(
        yolo_model=yolo_model,
        dinov3_processor=dinov3_processor,
        dinov3_model=dinov3_model,
        classifiers=all_classifiers,
        mlb=mlb,
        mapping_dict=mapping_dict,
        label_columns=config.labels.columns,
        frame_width=actual_width,
        frame_height=actual_height,
        confidence_threshold=config.detection.confidence_threshold,
        trigger_zone_config=trigger_config,
        max_classification_attempts=config.tracking.max_classification_attempts,
        device=device
    )
    print("✓ Pipeline initialized")
    
    # Initialize logger
    print("\nInitializing logger...")
    logger = DataLogger(output_dir="exports")
    print("✓ Logger initialized")
    
    # Initialize performance monitor
    print("\nInitializing performance monitor...")
    perf_monitor = PerformanceMonitor(history_size=60)
    print("✓ Performance monitor initialized")
    
    # Initialize web dashboard
    print("\nInitializing web dashboard...")
    dashboard = WebDashboard(pipeline, config, logger, perf_monitor)
    print("✓ Dashboard initialized")
    
    # Start camera loop in separate thread
    camera_thread = threading.Thread(
        target=camera_loop,
        args=(cap, pipeline, logger, perf_monitor, dashboard),
        daemon=True
    )
    camera_thread.start()
    
    # Run web server (blocking)
    try:
        dashboard.run(host=args.host, port=args.port, debug=False)
    except KeyboardInterrupt:
        print("\n\nShutting down...")
    finally:
        cap.release()
        print("✓ Shutdown complete")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
