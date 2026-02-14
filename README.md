# EkoVision PET Detection System

A real-time computer vision system for detecting and classifying PET bottles on conveyor belts using YOLO and DINOv3 models with intelligent Detection-Tracking-Trigger architecture.

## Overview

EkoVision is a proof-of-concept system designed for industrial bottle sorting applications. It uses a smart architecture that reduces computational load by 80-90% while maintaining high accuracy through strategic classification triggering.

## Key Features

### Core System

- **Detection-Tracking-Trigger Architecture**: Classify only when bottles enter trigger zone
- **80-90% Computational Reduction**: Smart caching eliminates redundant classifications
- **Real-time Performance**: 17+ FPS with GPU acceleration
- **Multi-label Classification**: 8 attributes per bottle (product, grade, cap, label, brand, type, subtype, volume)
- **State Management**: NEW → TRACKED → CLASSIFIED → FAILED workflow
- **Smart Caching**: LRU cache with configurable size

### Enhanced Features (Phase 1-4)

- **YAML Configuration**: Centralized config file for all system parameters
- **Data Logging & Export**: CSV/JSON export with session summaries
- **Video Recording**: Annotated MP4 recordings with bounding boxes
- **Runtime Camera Controls**: Adjust exposure, brightness, and presets on-the-fly
- **Performance Monitoring**: Real-time FPS, GPU/CPU usage, VRAM tracking, and performance graphs

## Quick Start

### Platform Support

EkoVision runs on:

- ✓ Windows (NVIDIA CUDA / CPU)
- ✓ macOS (Apple MPS / CPU)
- ✓ Linux (NVIDIA CUDA / CPU)

**For macOS users:** See [macOS Setup Guide](docs/MACOS_SETUP_GUIDE.md) for platform-specific instructions.

### Installation

**Windows / Linux:**

```bash
# Install dependencies
pip install -r requirements.txt

# Verify model files exist
# - best.pt (YOLO model)
# - dinov3_multilabel_encoder.pkl
# - label_mapping_dict.joblib
# - OVR_Checkpoints/ (314 classifiers)
```

**macOS:**

```bash
# Install dependencies
pip3 install -r requirements.txt

# Grant camera permission in System Preferences
# See docs/MACOS_SETUP_GUIDE.md for details
```

### Configuration

Edit `config.yaml` to customize system parameters:

```yaml
camera:
  index: 0
  width: 640
  height: 480

detection:
  confidence_threshold: 0.5

trigger_zone:
  x_offset_pct: 30.0
  y_offset_pct: 20.0
  width_pct: 40.0
  height_pct: 60.0
```

See [Configuration Guide](docs/CONFIGURATION_GUIDE.md) for details.

### Running

```bash
python run_detection_tracking.py
```

## Keyboard Controls

| Key             | Action                                    |
| --------------- | ----------------------------------------- |
| `q`             | Quit application                          |
| `r`             | Reset pipeline (clear cache & tracking)   |
| `s`             | Show statistics                           |
| `t`             | Toggle trigger zone overlay               |
| `e`             | Export data to CSV                        |
| `j`             | Export data to JSON                       |
| `v`             | Toggle video recording                    |
| `c`             | Toggle camera control mode                |
| `m`             | Toggle performance overlay                |
| `g`             | Save performance graph (PNG)              |
| `[` / `]`       | Adjust exposure (in camera mode)          |
| `-` / `+`       | Adjust brightness (in camera mode)        |
| `a`             | Toggle auto-exposure (in camera mode)     |
| `1` / `2` / `3` | Camera presets: Indoor/Outdoor/High Speed |

## Documentation

### User Guides

- [Running Guide](RUNNING_GUIDE.md) - Complete usage instructions
- [Configuration Guide](docs/CONFIGURATION_GUIDE.md) - YAML configuration reference
- [macOS Setup Guide](docs/MACOS_SETUP_GUIDE.md) - Setup lengkap untuk MacBook
- [macOS vs Windows Comparison](MACOS_VS_WINDOWS_COMPARISON.md) - Platform comparison
- [External Camera Guide](docs/EXTERNAL_CAMERA_GUIDE.md) - Setup kamera eksternal USB/IP camera
- [Camera Quick Setup](docs/CAMERA_QUICK_SETUP.md) - Panduan cepat 5 menit
- [Classification Troubleshooting](docs/CLASSIFICATION_TROUBLESHOOTING.md) - Debug klasifikasi
- [Data Logging Guide](docs/DATA_LOGGING_GUIDE.md) - Export and logging features
- [Camera Controls Guide](docs/CAMERA_CONTROLS_GUIDE.md) - Runtime camera adjustments
- [Performance Monitoring Guide](docs/PERFORMANCE_MONITORING_GUIDE.md) - Performance tracking and optimization
- [Batch Processing Guide](docs/BATCH_PROCESSING_GUIDE.md) - Process multiple videos
- [Advanced Trigger Zones Guide](docs/ADVANCED_TRIGGER_ZONES_GUIDE.md) - Multiple trigger zones
- [Web Dashboard Guide](docs/WEB_DASHBOARD_GUIDE.md) - Remote monitoring via web browser

### Technical Documentation

- [Project Structure](PROJECT_STRUCTURE.md) - Codebase organization
- [Project Review](PROJECT_REVIEW.md) - Technical analysis

## System Requirements

### Hardware

- **GPU**: NVIDIA RTX Series (6GB+ VRAM recommended)
- **CPU**: Intel Core i7 / AMD Ryzen 7 or better
- **RAM**: 16GB minimum (32GB recommended)
- **Camera**: USB webcam or industrial camera with manual exposure control

### Software

- **OS**: Windows 10/11, Linux, or macOS
- **Python**: 3.8 - 3.11
- **CUDA**: 11.x or 12.x (for GPU acceleration)

## Architecture

```
┌─────────────┐
│   Camera    │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────┐
│  Detection-Tracking-Trigger Pipeline   │
├─────────────────────────────────────────┤
│  1. YOLO Detection (YOLOv10m)          │
│  2. ByteTrack Tracking                  │
│  3. Trigger Zone Check                  │
│  4. DINOv3 Feature Extraction           │
│  5. 314 LogisticRegression Classifiers  │
│  6. LRU Cache (100 entries)             │
│  7. State Management                    │
└──────┬──────────────────────────────────┘
       │
       ▼
┌─────────────┐
│   Display   │  ← Real-time visualization
│   Logger    │  ← CSV/JSON/Video export
└─────────────┘
```

## Models Used

- **YOLOv10m**: Object detection (bottles)
- **DINOv3**: Feature extraction (embeddings)
- **314 LogisticRegression Classifiers**: Multi-label classification (One-vs-Rest)

## Performance

- **Classification Time**: ~33ms per bottle (67% below 100ms target)
- **FPS**: 17.5 FPS average with GPU
- **Computational Reduction**: 80-90% vs per-frame classification
- **Cache Hit Rate**: 75%+ in typical scenarios

## Testing

```bash
# Run unit tests
pytest tests/unit/ -v

# Expected: 99 passed
```

## Project Status

- ✅ Core detection-tracking-trigger system (complete)
- ✅ Phase 1: YAML configuration support (complete)
- ✅ Phase 2: Data logging and export (complete)
- ✅ Phase 3: Runtime camera controls (complete)
- ✅ Phase 4: Documentation updates (complete)
- ✅ Phase 5: Performance monitoring (complete)
- 🔜 Phase 6: Batch processing (planned)
- 🔜 Phase 7: Advanced trigger zones (planned)
- 🔜 Phase 8: Web dashboard (optional)

## License

[Your License Here]

## Support

For questions or issues, please open an issue in the repository.
