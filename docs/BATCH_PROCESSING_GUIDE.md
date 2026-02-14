# Batch Processing Guide

## Overview

Batch processing allows you to process pre-recorded videos offline without a camera. This is useful for:

- Processing archived footage
- Testing and benchmarking
- Bulk video analysis
- Automated workflows

## Features

- **Offline Processing**: Process videos without real-time constraints
- **Progress Tracking**: Visual progress bars with ETA
- **Batch Reports**: Comprehensive JSON reports with statistics
- **Flexible Output**: Choose CSV, JSON, and/or video output
- **Directory Processing**: Process multiple videos at once
- **Error Recovery**: Continue processing even if individual videos fail

## Quick Start

### Process Single Video

```bash
python run_detection_tracking.py --batch --input video.mp4
```

### Process Directory

```bash
python run_detection_tracking.py --batch --input-dir videos/
```

### Custom Output Directory

```bash
python run_detection_tracking.py --batch --input video.mp4 --output-dir results/
```

## Command Line Options

### Mode Selection

| Option    | Description                             |
| --------- | --------------------------------------- |
| `--batch` | Enable batch processing mode (required) |

### Input Options

| Option              | Description                     | Example               |
| ------------------- | ------------------------------- | --------------------- |
| `--input FILE`      | Process single video file       | `--input video.mp4`   |
| `--input-dir DIR`   | Process all videos in directory | `--input-dir videos/` |
| `--pattern PATTERN` | File pattern for directory mode | `--pattern "*.avi"`   |

### Output Options

| Option             | Description                   | Default        |
| ------------------ | ----------------------------- | -------------- |
| `--output-dir DIR` | Output directory              | `batch_output` |
| `--no-video`       | Don't save annotated video    | Save video     |
| `--no-json`        | Don't save JSON data          | Save JSON      |
| `--csv-only`       | Save only CSV (no JSON/video) | Save all       |

### Other Options

| Option          | Description           | Default       |
| --------------- | --------------------- | ------------- |
| `--config FILE` | Configuration file    | `config.yaml` |
| `--no-progress` | Disable progress bars | Show progress |

## Usage Examples

### Example 1: Basic Batch Processing

Process a single video with default settings:

```bash
python run_detection_tracking.py --batch --input sample.mp4
```

**Output**:

- `batch_output/sample_processed.mp4` - Annotated video
- `batch_output/sample_processed.csv` - Detection data
- `batch_output/sample_processed.json` - Classification data
- `batch_output/sample_processed.summary.json` - Session summary
- `batch_output/batch_report.json` - Batch processing report

### Example 2: Process Multiple Videos

Process all MP4 files in a directory:

```bash
python run_detection_tracking.py --batch --input-dir videos/ --output-dir results/
```

**Progress Output**:

```
Found 3 video(s) to process
Output directory: results/

Processing video1.mp4: 100%|████████| 1500/1500 [01:23<00:00, 18.0frame/s]
✓ video1.mp4: 1500 frames, 45 classifications, 18.0 FPS

Processing video2.mp4: 100%|████████| 2000/2000 [01:52<00:00, 17.8frame/s]
✓ video2.mp4: 2000 frames, 60 classifications, 17.8 FPS

Processing video3.mp4: 100%|████████| 1200/1200 [01:07<00:00, 17.9frame/s]
✓ video3.mp4: 1200 frames, 38 classifications, 17.9 FPS

============================================================
BATCH PROCESSING SUMMARY
============================================================
Videos processed: 3
  Succeeded: 3
  Failed: 0

Total frames: 4700
Total classifications: 143
Average FPS: 17.9
Total duration: 262.5s
============================================================

✓ Report saved: results/batch_report.json
✓ Batch processing complete!
```

### Example 3: CSV Only (No Video)

Save only CSV data to minimize disk usage:

```bash
python run_detection_tracking.py --batch --input-dir videos/ --csv-only --no-video
```

This saves only CSV files, skipping video and JSON output.

### Example 4: Process AVI Files

Process AVI files instead of MP4:

```bash
python run_detection_tracking.py --batch --input-dir videos/ --pattern "*.avi"
```

### Example 5: Custom Configuration

Use a custom configuration file:

```bash
python run_detection_tracking.py --batch --input video.mp4 --config custom_config.yaml
```

### Example 6: Silent Mode

Disable progress bars for automated scripts:

```bash
python run_detection_tracking.py --batch --input-dir videos/ --no-progress
```

## Output Files

### Per-Video Outputs

For each processed video, the following files are generated:

#### 1. Annotated Video (`.mp4`)

Processed video with bounding boxes and classifications.

**Location**: `{output_dir}/{video_name}_processed.mp4`

**Features**:

- Color-coded bounding boxes (yellow/cyan/green/red)
- Track IDs and classification results
- Trigger zone overlay
- FPS counter

#### 2. CSV Detection Data (`.csv`)

All detection events with timestamps.

**Location**: `{output_dir}/{video_name}_processed.csv`

**Columns**:

- timestamp
- track_id
- bbox (x, y, w, h)
- confidence
- state (NEW, TRACKED, CLASSIFIED, FAILED)
- classification results (8 attributes)

#### 3. JSON Classification Data (`.json`)

Classification history per bottle.

**Location**: `{output_dir}/{video_name}_processed.json`

**Structure**:

```json
{
  "track_1": {
    "classifications": [
      {
        "timestamp": "2026-02-12T10:30:45",
        "product": "Aqua",
        "grade": "Premium",
        ...
      }
    ]
  }
}
```

#### 4. Session Summary (`.summary.json`)

Processing statistics for the video.

**Location**: `{output_dir}/{video_name}_processed.summary.json`

**Contents**:

- Total frames processed
- Total classifications
- Computational reduction percentage
- Average FPS
- Cache statistics

### Batch Report

#### `batch_report.json`

Comprehensive report for all processed videos.

**Location**: `{output_dir}/batch_report.json`

**Structure**:

```json
{
  "start_time": "2026-02-12T10:30:00",
  "end_time": "2026-02-12T10:35:30",
  "total_duration_seconds": 330.5,
  "videos_processed": 3,
  "videos_succeeded": 3,
  "videos_failed": 0,
  "total_frames": 4700,
  "total_classifications": 143,
  "avg_fps": 17.9,
  "results": [
    {
      "video_path": "videos/video1.mp4",
      "output_path": "results/video1_processed",
      "success": true,
      "frames_processed": 1500,
      "classifications": 45,
      "duration_seconds": 83.5,
      "avg_fps": 18.0,
      "error_message": null
    },
    ...
  ]
}
```

## Performance Considerations

### Processing Speed

Batch processing is typically faster than real-time because:

- No camera I/O overhead
- No display rendering (unless saving video)
- Can process at maximum hardware speed

**Expected Performance**:

- With GPU: 15-20 FPS
- With CPU: 5-10 FPS

### Disk Space

Estimate disk space requirements:

| Output Type     | Size per Minute | Example (10 min video) |
| --------------- | --------------- | ---------------------- |
| Annotated Video | ~50-100 MB      | 500-1000 MB            |
| CSV Data        | ~1-5 MB         | 10-50 MB               |
| JSON Data       | ~0.5-2 MB       | 5-20 MB                |
| Summary         | ~10 KB          | 10 KB                  |

**Total for 10-minute video**: ~515-1070 MB (all outputs)

**CSV-only mode**: ~15-60 MB (95% reduction)

### Memory Usage

- **RAM**: 4-8 GB (same as real-time mode)
- **VRAM**: 3-6 GB (GPU mode)

## Troubleshooting

### Video Not Found

```
✗ Video file not found: video.mp4
```

**Solution**: Check file path and ensure video exists.

### Failed to Open Video

```
✗ Failed to open video: video.mp4
```

**Solution**:

- Check video codec (MP4/H.264 recommended)
- Verify file is not corrupted
- Try converting with ffmpeg: `ffmpeg -i input.avi -c:v libx264 output.mp4`

### Out of Memory

```
✗ CUDA out of memory
```

**Solution**:

- Process videos one at a time (don't use directory mode)
- Reduce video resolution
- Use CPU mode: Set `device: "cpu"` in config.yaml

### Slow Processing

**Possible causes**:

- CPU mode (no GPU)
- High resolution videos
- Too many bottles per frame

**Solutions**:

- Enable GPU acceleration
- Reduce video resolution: `ffmpeg -i input.mp4 -vf scale=640:480 output.mp4`
- Adjust trigger zone to reduce classifications

### Progress Bar Not Showing

```
⚠ tqdm not installed. Progress bar disabled.
```

**Solution**: Install tqdm: `pip install tqdm`

## Integration with Other Tools

### FFmpeg Integration

Convert videos before processing:

```bash
# Convert AVI to MP4
ffmpeg -i input.avi -c:v libx264 -crs 23 output.mp4

# Reduce resolution
ffmpeg -i input.mp4 -vf scale=640:480 output.mp4

# Extract frames
ffmpeg -i input.mp4 -vf fps=1 frame_%04d.png
```

### Python API

Use batch processor in your own scripts:

```python
from src.batch_processor import BatchProcessor
from src.tracking import DetectionTrackingPipeline

# Initialize pipeline (see run_detection_tracking.py for full setup)
pipeline = DetectionTrackingPipeline(...)

# Create batch processor
processor = BatchProcessor(
    pipeline=pipeline,
    output_dir="results",
    save_video=True,
    save_json=True,
    save_csv=True
)

# Process single video
result = processor.process_video("video.mp4")

# Process directory
results = processor.process_directory("videos/", pattern="*.mp4")

# Generate report
processor.print_summary()
processor.save_report()
```

## Best Practices

1. **Test First**: Process a short video first to verify settings
2. **Monitor Disk Space**: Check available space before batch processing
3. **Use CSV-Only**: For large batches, use `--csv-only` to save space
4. **Backup Originals**: Keep original videos separate from output
5. **Organize Output**: Use descriptive output directory names
6. **Check Reports**: Review batch_report.json for errors
7. **Incremental Processing**: Process videos in small batches

## Automation

### Bash Script Example

```bash
#!/bin/bash
# Process all videos in a directory tree

find /path/to/videos -name "*.mp4" -type f | while read video; do
    echo "Processing: $video"
    python run_detection_tracking.py --batch --input "$video" --output-dir "results/"
done
```

### Windows Batch Script

```batch
@echo off
REM Process all MP4 files in current directory

for %%f in (*.mp4) do (
    echo Processing: %%f
    python run_detection_tracking.py --batch --input "%%f" --output-dir "results/"
)
```

### Python Script

```python
import os
from pathlib import Path

videos_dir = Path("videos")
output_dir = Path("results")

for video in videos_dir.glob("*.mp4"):
    print(f"Processing: {video}")
    os.system(f'python run_detection_tracking.py --batch --input "{video}" --output-dir "{output_dir}"')
```

## FAQ

**Q: Can I process videos in parallel?**  
A: Not currently. Process videos sequentially to avoid GPU memory issues.

**Q: What video formats are supported?**  
A: MP4, AVI, MOV, and other OpenCV-supported formats.

**Q: Can I resume interrupted batch processing?**  
A: No. Re-run the batch command. Already processed videos will be overwritten.

**Q: How do I process only specific frames?**  
A: Use FFmpeg to extract frames first, then process the extracted video.

**Q: Can I change configuration per video?**  
A: Yes, use `--config` with different config files for each run.

---

**Last Updated**: February 12, 2026  
**Version**: 1.0.0  
**Author**: EkoVision Development Team
