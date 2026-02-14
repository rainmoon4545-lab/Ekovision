"""
Quick test to verify pipeline can be imported and initialized.
Run this before running the full system.
"""
import sys
print("Testing pipeline import...")

try:
    from src.tracking import (
        DetectionTrackingPipeline,
        TriggerZoneConfig,
        BottleTracker,
        TriggerZone,
        ClassificationCache
    )
    print("✓ All tracking components imported successfully")
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)

try:
    import cv2
    print(f"✓ OpenCV version: {cv2.__version__}")
except ImportError:
    print("✗ OpenCV not installed")
    sys.exit(1)

try:
    import torch
    print(f"✓ PyTorch version: {torch.__version__}")
    print(f"✓ CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"✓ CUDA device: {torch.cuda.get_device_name(0)}")
except ImportError:
    print("✗ PyTorch not installed")
    sys.exit(1)

try:
    from ultralytics import YOLO
    print("✓ Ultralytics YOLO imported")
except ImportError:
    print("✗ Ultralytics not installed")
    sys.exit(1)

try:
    from transformers import AutoImageProcessor, AutoModel
    print("✓ Transformers imported")
except ImportError:
    print("✗ Transformers not installed")
    sys.exit(1)

try:
    import joblib
    import numpy as np
    from PIL import Image
    print("✓ All dependencies available")
except ImportError as e:
    print(f"✗ Missing dependency: {e}")
    sys.exit(1)

print("\n" + "="*60)
print("ALL CHECKS PASSED")
print("="*60)
print("\nYou can now run:")
print("  python run_detection_tracking.py")
print("\nOr run tests:")
print("  pytest tests/unit/ -v")
