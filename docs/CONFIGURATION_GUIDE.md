# Configuration Guide

## Overview

The EkoVision Detection-Tracking-Trigger system uses a YAML configuration file (`config.yaml`) for easy parameter tuning without editing code.

## Configuration File

The system looks for `config.yaml` in the root directory. If not found, it uses default values.

### Quick Start

1. Copy the sample configuration:

```bash
cp config.sample.yaml config.yaml
```

2. Edit `config.yaml` with your preferred settings

3. Run the system:

```bash
python run_detection_tracking.py
```

## Configuration Sections

### Camera Configuration

```yaml
camera:
  index: 0 # Camera device index (0 = default, 1 = second camera)
  width: 640 # Frame width in pixels (320-1920)
  height: 480 # Frame height in pixels (240-1080)
```

**Parameters**:

- `index`: Camera device index. Use 0 for default camera, 1 for second camera, etc.
- `width`: Frame width in pixels. Valid range: 320-1920
- `height`: Frame height in pixels. Valid range: 240-1080

**Tips**:

- Higher resolution = better quality but lower FPS
- Recommended: 640x480 for real-time performance
- For high-speed conveyor: Use 320x240 for maximum FPS

### Detection Configuration

```yaml
detection:
  confidence_threshold: 0.5 # YOLO confidence threshold (0.0-1.0)
```

**Parameters**:

- `confidence_threshold`: Minimum confidence score for detections. Valid range: 0.0-1.0

**Tips**:

- Lower threshold = more detections (including false positives)
- Higher threshold = fewer detections (may miss some bottles)
- Recommended: 0.5 for balanced performance

### Trigger Zone Configuration

```yaml
trigger_zone:
  x_offset_pct: 30.0 # X offset from left edge (0-50%)
  y_offset_pct: 20.0 # Y offset from top edge (0-50%)
  width_pct: 40.0 # Zone width as percentage of frame (20-80%)
  height_pct: 60.0 # Zone height as percentage of frame (20-80%)
```

**Parameters**:

- `x_offset_pct`: Horizontal offset from left edge. Valid range: 0-50%
- `y_offset_pct`: Vertical offset from top edge. Valid range: 0-50%
- `width_pct`: Zone width as percentage of frame. Valid range: 20-80%
- `height_pct`: Zone height as percentage of frame. Valid range: 20-80%

**Tips**:

- Default (40% x 60%, centered) works for most cases
- For fast conveyor: Use smaller zone (20% x 40%) for precise timing
- For slow conveyor: Use larger zone (60% x 80%) for more flexibility

**Example Configurations**:

Fast Conveyor (narrow zone):

```yaml
trigger_zone:
  x_offset_pct: 40.0
  y_offset_pct: 30.0
  width_pct: 20.0
  height_pct: 40.0
```

Slow Conveyor (wide zone):

```yaml
trigger_zone:
  x_offset_pct: 20.0
  y_offset_pct: 10.0
  width_pct: 60.0
  height_pct: 80.0
```

### Tracking Configuration

```yaml
tracking:
  max_age: 30 # Maximum frames to keep track without detection (10-60)
  min_hits: 1 # Minimum detections before confirming track (1-5)
  iou_threshold: 0.3 # IoU threshold for matching detections (0.1-0.9)
  max_tracks: 20 # Maximum number of simultaneous tracks (5-50)
  max_classification_attempts: 2 # Maximum retry attempts before FAILED state (1-5)
```

**Parameters**:

- `max_age`: Maximum frames to keep track without detection. Valid range: 10-60
- `min_hits`: Minimum detections before confirming track. Valid range: 1-5
- `iou_threshold`: IoU threshold for matching detections. Valid range: 0.1-0.9
- `max_tracks`: Maximum simultaneous tracks. Valid range: 5-50
- `max_classification_attempts`: Maximum retry attempts. Valid range: 1-5

**Tips**:

- `max_age=30`: Good for 30 FPS video (1 second persistence)
- `min_hits=1`: Immediate tracking (recommended for real-time)
- `iou_threshold=0.3`: Lower = more lenient matching
- `max_tracks=20`: Sufficient for most conveyor scenarios
- `max_classification_attempts=2`: Prevents infinite retry loops

### Cache Configuration

```yaml
cache:
  max_size: 100 # Maximum number of cached classification results (10-500)
```

**Parameters**:

- `max_size`: Maximum cached results. Valid range: 10-500

**Tips**:

- Default (100) is sufficient for most cases
- Increase if you have many bottles on screen simultaneously
- LRU eviction automatically removes oldest entries

### Model Paths

```yaml
models:
  yolo_path: "best.pt"
  dinov3_model: "facebook/dinov3-convnext-small-pretrain-lvd1689m"
  encoder_path: "dinov3_multilabel_encoder.pkl"
  mapping_path: "label_mapping_dict.joblib"
  classifiers_dir: "OVR_Checkpoints-20251018T053026Z-1-001/OVR_Checkpoints"
```

**Parameters**:

- `yolo_path`: Path to YOLO model file
- `dinov3_model`: HuggingFace model identifier for DINOv3
- `encoder_path`: Path to MultiLabelBinarizer encoder
- `mapping_path`: Path to label mapping dictionary
- `classifiers_dir`: Directory containing 314 classifier models

**Tips**:

- Use relative paths from project root
- Ensure all files exist before running
- System will fail with clear error if files are missing

### Label Configuration

```yaml
labels:
  columns:
    - product
    - grade
    - cap
    - label
    - brand
    - type
    - subtype
    - volume
```

**Parameters**:

- `columns`: List of 8 classification attributes

**Tips**:

- Must have exactly 8 attributes
- Order must match your training data
- Do not modify unless you retrained the models

### Display Configuration

```yaml
display:
  show_trigger_zone: true # Show trigger zone overlay on startup
  show_fps: true # Show FPS counter
  show_statistics: true # Show statistics overlay
```

**Parameters**:

- `show_trigger_zone`: Show trigger zone overlay on startup
- `show_fps`: Show FPS counter (currently always shown)
- `show_statistics`: Show statistics overlay (currently always shown)

**Tips**:

- Toggle trigger zone at runtime with 't' key
- FPS and statistics are always visible for monitoring

### Performance Configuration

```yaml
performance:
  device: "auto" # Device for inference: "auto", "cuda", or "cpu"
  warmup_classifiers: true # Warmup classifiers on startup to prevent lag
```

**Parameters**:

- `device`: Inference device. Options: "auto", "cuda", "cpu"
- `warmup_classifiers`: Warmup classifiers on startup

**Tips**:

- `device="auto"`: Automatically use CUDA if available, otherwise CPU
- `device="cuda"`: Force CUDA (will fallback to CPU if unavailable)
- `device="cpu"`: Force CPU (useful for debugging)
- `warmup_classifiers=true`: Prevents 10-50x first-inference lag spike

### Logging Configuration

```yaml
logging:
  level: "INFO" # Logging level: DEBUG, INFO, WARNING, ERROR
  log_to_file: false # Save logs to file
  log_file: "ekovision.log" # Log file path (if log_to_file is true)
```

**Parameters**:

- `level`: Logging level. Options: "DEBUG", "INFO", "WARNING", "ERROR"
- `log_to_file`: Save logs to file
- `log_file`: Log file path

**Tips**:

- `level="INFO"`: Standard logging (recommended)
- `level="DEBUG"`: Verbose logging for troubleshooting
- `log_to_file=true`: Useful for long-running sessions

## Validation and Fallback

The configuration loader validates all values and provides fallback to defaults:

- **Out of range values**: Clamped to valid range with warning
- **Invalid types**: Replaced with default value with warning
- **Missing file**: Uses all default values with warning
- **Invalid YAML**: Uses all default values with error message

## Example Configurations

### High-Speed Conveyor

```yaml
camera:
  width: 320
  height: 240

trigger_zone:
  x_offset_pct: 40.0
  y_offset_pct: 30.0
  width_pct: 20.0
  height_pct: 40.0

tracking:
  max_age: 20
  max_classification_attempts: 1
```

### Low-Speed Conveyor

```yaml
camera:
  width: 640
  height: 480

trigger_zone:
  x_offset_pct: 20.0
  y_offset_pct: 10.0
  width_pct: 60.0
  height_pct: 80.0

tracking:
  max_age: 45
  max_classification_attempts: 3
```

### High-Quality Mode

```yaml
camera:
  width: 1280
  height: 720

detection:
  confidence_threshold: 0.7

tracking:
  max_tracks: 30

cache:
  max_size: 200
```

## Troubleshooting

### Configuration Not Loading

**Problem**: System uses default values instead of config.yaml

**Solutions**:

1. Check file exists: `ls config.yaml`
2. Check YAML syntax: `python -c "import yaml; yaml.safe_load(open('config.yaml'))"`
3. Check file permissions
4. Check for typos in filename

### Invalid Values

**Problem**: Warning messages about invalid values

**Solutions**:

1. Check value ranges in this guide
2. Check data types (int vs float vs string)
3. Use sample config as reference: `config.sample.yaml`

### Performance Issues

**Problem**: Low FPS or high latency

**Solutions**:

1. Reduce camera resolution (width/height)
2. Reduce trigger zone size
3. Reduce max_tracks
4. Ensure device="cuda" if GPU available

## Advanced Usage

### Multiple Configurations

Create different config files for different scenarios:

```bash
# Development config
cp config.yaml config.dev.yaml

# Production config
cp config.yaml config.prod.yaml

# Use specific config
cp config.prod.yaml config.yaml
python run_detection_tracking.py
```

### Environment-Specific Configs

Use environment variables to select config:

```bash
# Linux/Mac
export EKOVISION_CONFIG="config.prod.yaml"

# Windows
set EKOVISION_CONFIG=config.prod.yaml
```

(Note: This requires code modification to support environment variables)

## Support

For issues or questions:

1. Check this guide
2. Check `RUNNING_GUIDE.md` for general usage
3. Check `PROJECT_REVIEW.md` for system overview
4. Open an issue in the repository
