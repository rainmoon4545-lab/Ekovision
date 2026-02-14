# Performance Monitoring Guide

## Overview

The Performance Monitoring system provides real-time insights into system performance, including FPS, GPU/CPU usage, memory consumption, and frame processing time breakdown. This helps identify bottlenecks and optimize system performance.

## Features

### Real-time Metrics

- **FPS (Frames Per Second)**: Current and average FPS over the last 60 seconds
- **GPU Usage**: GPU utilization percentage (CUDA only)
- **CPU Usage**: CPU utilization percentage
- **VRAM Usage**: Video memory consumption in GB (CUDA only)
- **Frame Time Breakdown**: Time spent in each processing stage (detection, tracking, classification, rendering)

### Visual Overlay

The performance overlay displays metrics directly on the video feed with color-coded warnings:

- **Green**: Normal operation
- **Yellow**: Warning threshold exceeded
- **Red**: Critical threshold exceeded

### Performance Graphs

Generate detailed performance graphs showing:

- FPS history over time
- GPU/CPU usage trends
- VRAM consumption
- Frame time breakdown by stage

## Keyboard Controls

| Key | Action                             |
| --- | ---------------------------------- |
| `m` | Toggle performance overlay on/off  |
| `g` | Save performance graph to PNG file |

## Usage

### Enabling Performance Overlay

1. Run the application normally
2. Press `m` to toggle the performance overlay
3. The overlay appears in the top-left corner of the video feed

### Saving Performance Graphs

1. Press `g` to save a performance graph
2. The graph is saved to `performance_graphs/performance_YYYY-MM-DD_HH-MM-SS.png`
3. A confirmation message shows the file path

## Understanding the Metrics

### FPS (Frames Per Second)

- **Current FPS**: Instantaneous frame rate
- **Average FPS**: Rolling average over 60 seconds
- **Target**: 15-20 FPS for real-time processing
- **Warning**: < 10 FPS (yellow), < 5 FPS (red)

### GPU Usage

- **Normal**: 50-80% (efficient utilization)
- **Warning**: > 90% (yellow, potential bottleneck)
- **Critical**: > 95% (red, GPU saturated)

### CPU Usage

- **Normal**: 30-60% (balanced load)
- **Warning**: > 80% (yellow, high load)
- **Critical**: > 90% (red, CPU bottleneck)

### VRAM Usage

- **Normal**: < 4 GB (typical for YOLOv10m + DINOv3)
- **Warning**: > 6 GB (yellow, high memory usage)
- **Critical**: > 8 GB (red, risk of OOM)

### Frame Time Breakdown

Shows time spent in each processing stage:

- **Detection**: YOLO object detection
- **Tracking**: ByteTrack tracking algorithm
- **Classification**: DINOv3 feature extraction + classifier inference
- **Rendering**: Drawing annotations and overlays

## Performance Optimization Tips

### If FPS is Low (< 10 FPS)

1. **Check GPU Usage**: If < 50%, CPU might be bottleneck
2. **Reduce Resolution**: Lower camera resolution in `config.yaml`
3. **Increase Confidence Threshold**: Fewer detections = faster processing
4. **Optimize Trigger Zone**: Smaller zone = fewer classifications

### If GPU Usage is High (> 90%)

1. **Use Smaller YOLO Model**: Switch from YOLOv10m to YOLOv10s
2. **Batch Processing**: Process multiple frames together (advanced)
3. **Reduce Input Size**: Lower detection resolution

### If CPU Usage is High (> 80%)

1. **Check Tracking Overhead**: Too many tracks can slow CPU
2. **Optimize Cache Size**: Adjust LRU cache size in config
3. **Reduce Annotation Complexity**: Disable unnecessary overlays

### If VRAM Usage is High (> 6 GB)

1. **Use Smaller Models**: Switch to lighter YOLO/DINOv3 variants
2. **Reduce Batch Size**: Process fewer images at once
3. **Clear Cache**: Reset pipeline periodically with `r` key

## Performance Graph Interpretation

### FPS Graph (Top Left)

- **Stable Line**: Good performance, consistent frame rate
- **Fluctuating**: Variable load, check for bottlenecks
- **Declining**: Performance degradation over time

### GPU/CPU Usage (Top Right)

- **Balanced**: Both GPU and CPU utilized efficiently
- **GPU High, CPU Low**: GPU-bound (expected for deep learning)
- **CPU High, GPU Low**: CPU bottleneck (tracking/preprocessing)

### VRAM Usage (Bottom Left)

- **Stable**: Normal operation
- **Increasing**: Potential memory leak (report bug)
- **Spiky**: Variable batch sizes or cache behavior

### Frame Time Breakdown (Bottom Right)

- **Detection Dominant**: YOLO is the bottleneck
- **Classification Dominant**: DINOv3 or classifiers are slow
- **Tracking Dominant**: Too many tracks or complex tracking
- **Rendering Dominant**: Too many annotations (unlikely)

## Troubleshooting

### Overlay Not Showing

- Press `m` to toggle overlay on
- Check if frame is too small (overlay requires minimum 640x480)

### Graph Not Saving

- Check write permissions for `performance_graphs/` directory
- Ensure matplotlib is installed: `pip install matplotlib`
- Check console for error messages

### Metrics Show Zero

- **GPU Metrics**: Only available with CUDA (GPU mode)
- **CPU Metrics**: Requires `psutil` library (auto-installed)
- Wait a few seconds for metrics to stabilize

### Performance Overhead

The performance monitor is designed to be lightweight:

- Metrics updated every 1 second (not every frame)
- Minimal CPU/GPU overhead (< 1% FPS impact)
- Overlay rendering is optimized with OpenCV

## Configuration

Performance monitoring is always enabled but can be controlled via keyboard:

```yaml
# No configuration needed - always available
# Toggle with 'm' key during runtime
```

## Examples

### Normal Operation

```
FPS: 17.5 (avg: 17.2)  [GREEN]
GPU: 75%  [GREEN]
CPU: 45%  [GREEN]
VRAM: 3.2 GB  [GREEN]

Detection: 25ms
Tracking: 5ms
Classification: 33ms
Rendering: 8ms
```

### Warning State

```
FPS: 8.5 (avg: 9.2)  [YELLOW]
GPU: 92%  [YELLOW]
CPU: 55%  [GREEN]
VRAM: 6.5 GB  [YELLOW]

Detection: 45ms
Tracking: 8ms
Classification: 65ms
Rendering: 12ms
```

### Critical State

```
FPS: 4.2 (avg: 5.1)  [RED]
GPU: 98%  [RED]
CPU: 85%  [YELLOW]
VRAM: 8.2 GB  [RED]

Detection: 85ms
Tracking: 15ms
Classification: 120ms
Rendering: 18ms
```

## Best Practices

1. **Monitor During Development**: Keep overlay on to catch performance issues early
2. **Save Graphs Regularly**: Document performance before/after optimizations
3. **Baseline Testing**: Record performance with known workloads
4. **Compare Configurations**: Test different settings and compare graphs
5. **Production Monitoring**: Disable overlay in production, save graphs periodically

## Integration with Other Features

### Data Logging

Performance metrics are NOT logged to CSV/JSON exports (to avoid overhead). Use graph saving for performance documentation.

### Camera Controls

Changing camera settings (exposure, brightness) may affect performance:

- Higher exposure = brighter image but slower capture
- Auto exposure = variable performance

### Video Recording

Recording adds minimal overhead (< 5% FPS impact) but increases disk I/O.

## Technical Details

### Metrics Collection

- **FPS**: Calculated from frame timestamps (rolling average)
- **GPU Usage**: NVIDIA SMI query (CUDA only)
- **CPU Usage**: `psutil.cpu_percent()` (system-wide)
- **VRAM**: `torch.cuda.memory_allocated()` (process-specific)

### Update Frequency

- Metrics updated every 1 second (configurable in code)
- Overlay redrawn every frame (minimal overhead)
- History stored for 60 seconds (configurable)

### Thread Safety

Performance monitoring is single-threaded and runs in the main loop. No threading issues.

## Support

For issues or questions:

1. Check console output for error messages
2. Verify matplotlib installation: `pip install matplotlib`
3. Test with minimal configuration (default `config.yaml`)
4. Report bugs with saved performance graphs

---

**Last Updated**: February 12, 2026  
**Version**: 1.0.0  
**Author**: EkoVision Development Team
