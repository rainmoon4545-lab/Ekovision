# Data Logging and Export Guide

## Overview

The EkoVision system includes comprehensive data logging and export capabilities for analysis and validation.

## Features

- **CSV Export**: All detection data with timestamps and classifications
- **JSON Export**: Classification history for all tracked bottles
- **Video Recording**: Annotated video with bounding boxes and labels
- **Session Summary**: Aggregate statistics and performance metrics

## Keyboard Controls

| Key | Action           | Description                              |
| --- | ---------------- | ---------------------------------------- |
| `e` | Export CSV       | Save all detection records to CSV file   |
| `j` | Export JSON      | Save classification history to JSON file |
| `v` | Toggle Recording | Start/stop video recording               |

## Export Directory

All exports are saved to the `exports/` directory in the project root.

The directory is created automatically on first export.

## File Naming Convention

All exported files use timestamped filenames:

```
ekovision_YYYY-MM-DD_HH-MM-SS.{extension}
```

**Examples**:

- `ekovision_2026-02-12_14-30-45.csv`
- `ekovision_2026-02-12_14-30-45.json`
- `ekovision_2026-02-12_14-30-45.mp4`
- `ekovision_2026-02-12_14-30-45.summary.json`

## CSV Export

### Format

CSV files contain one row per detection with the following columns:

| Column         | Type     | Description                                    |
| -------------- | -------- | ---------------------------------------------- |
| timestamp      | ISO 8601 | Detection timestamp                            |
| track_id       | int      | Unique bottle ID                               |
| x1, y1, x2, y2 | int      | Bounding box coordinates                       |
| confidence     | float    | Detection confidence (0.0-1.0)                 |
| state          | string   | Tracking state (NEW/TRACKED/CLASSIFIED/FAILED) |
| product        | string   | Product classification                         |
| grade          | string   | Grade classification                           |
| cap            | string   | Cap classification                             |
| label          | string   | Label classification                           |
| brand          | string   | Brand classification                           |
| type           | string   | Type classification                            |
| subtype        | string   | Subtype classification                         |
| volume         | string   | Volume classification                          |

### Example

```csv
timestamp,track_id,x1,y1,x2,y2,confidence,state,product,grade,cap,label,brand,type,subtype,volume
2026-02-12T14:30:45,101,120,80,220,280,0.950,CLASSIFIED,Aqua,Premium,Blue,Clear,Danone,Water,Still,600ml
2026-02-12T14:30:46,101,125,82,225,282,0.948,CLASSIFIED,Aqua,Premium,Blue,Clear,Danone,Water,Still,600ml
2026-02-12T14:30:47,102,300,100,400,300,0.920,NEW,UNKNOWN,UNKNOWN,UNKNOWN,UNKNOWN,UNKNOWN,UNKNOWN,UNKNOWN,UNKNOWN
```

### Usage

**Export during session**:

1. Press `e` key
2. Check console for export path
3. File saved to `exports/ekovision_YYYY-MM-DD_HH-MM-SS.csv`

**Automatic export on exit**:

- Session summary is automatically saved when you quit (press `q`)

### Analysis Examples

**Python (pandas)**:

```python
import pandas as pd

# Load CSV
df = pd.read_csv('exports/ekovision_2026-02-12_14-30-45.csv')

# Count bottles by state
print(df['state'].value_counts())

# Count bottles by brand
print(df[df['state'] == 'CLASSIFIED']['brand'].value_counts())

# Average confidence by state
print(df.groupby('state')['confidence'].mean())

# Bottles per minute
df['timestamp'] = pd.to_datetime(df['timestamp'])
df['minute'] = df['timestamp'].dt.floor('T')
print(df.groupby('minute')['track_id'].nunique())
```

**Excel**:

1. Open CSV in Excel
2. Use PivotTable for analysis
3. Create charts for visualization

## JSON Export

### Format

JSON files contain complete classification history:

```json
{
  "session_start": "2026-02-12T14:30:00",
  "session_end": "2026-02-12T14:45:00",
  "total_bottles": 45,
  "total_frames": 1500,
  "total_classifications": 42,
  "bottles": [
    {
      "track_id": 101,
      "first_seen": "2026-02-12T14:30:45",
      "last_seen": "2026-02-12T14:30:48",
      "state": "CLASSIFIED",
      "frames_tracked": 90,
      "classification_attempts": 1,
      "classification": {
        "product": "Aqua",
        "grade": "Premium",
        "cap": "Blue",
        "label": "Clear",
        "brand": "Danone",
        "type": "Water",
        "subtype": "Still",
        "volume": "600ml"
      }
    }
  ]
}
```

### Fields

**Session Level**:

- `session_start`: Session start timestamp (ISO 8601)
- `session_end`: Session end timestamp (ISO 8601)
- `total_bottles`: Total unique bottles tracked
- `total_frames`: Total frames processed
- `total_classifications`: Total classification operations

**Bottle Level**:

- `track_id`: Unique bottle ID
- `first_seen`: First detection timestamp
- `last_seen`: Last detection timestamp
- `state`: Final tracking state
- `frames_tracked`: Number of frames bottle was visible
- `classification_attempts`: Number of classification attempts
- `classification`: Classification results (null if not classified)

### Usage

**Export during session**:

1. Press `j` key
2. Check console for export path
3. File saved to `exports/ekovision_YYYY-MM-DD_HH-MM-SS.json`

### Analysis Examples

**Python**:

```python
import json

# Load JSON
with open('exports/ekovision_2026-02-12_14-30-45.json') as f:
    data = json.load(f)

# Session statistics
print(f"Duration: {data['session_end']} - {data['session_start']}")
print(f"Total bottles: {data['total_bottles']}")
print(f"Classification rate: {data['total_classifications'] / data['total_bottles']:.1%}")

# Bottle statistics
bottles = data['bottles']
classified = [b for b in bottles if b['state'] == 'CLASSIFIED']
failed = [b for b in bottles if b['state'] == 'FAILED']

print(f"Classified: {len(classified)}")
print(f"Failed: {len(failed)}")

# Brand distribution
from collections import Counter
brands = [b['classification']['brand'] for b in classified if b['classification']]
print(Counter(brands))
```

## Video Recording

### Format

- **Codec**: MP4V (H.264 compatible)
- **Extension**: .mp4
- **Frame Rate**: 30 FPS
- **Resolution**: Same as camera input

### Features

Recorded video includes:

- Bounding boxes with track IDs
- Color-coded states (Yellow/Cyan/Green/Red)
- Classification results (8 attributes)
- Trigger zone overlay
- FPS counter
- Statistics overlay
- Recording indicator (red dot)

### Usage

**Start recording**:

1. Press `v` key
2. Console shows: "✓ Recording started: exports/ekovision_YYYY-MM-DD_HH-MM-SS.mp4"
3. Red dot appears in top-left corner

**Stop recording**:

1. Press `v` key again
2. Console shows: "✓ Recording stopped: exports/ekovision_YYYY-MM-DD_HH-MM-SS.mp4"
3. Red dot disappears

**Automatic stop on exit**:

- Recording automatically stops when you quit (press `q`)

### Tips

- Recording adds minimal overhead (~1-2 FPS impact)
- File size: ~10-20 MB per minute (depends on resolution and activity)
- Use for documentation, debugging, or presentations
- Can record while exporting CSV/JSON

## Session Summary

### Format

Session summary is automatically saved on exit:

```json
{
  "session_start": "2026-02-12T14:30:00",
  "session_end": "2026-02-12T14:45:00",
  "duration_seconds": 900.0,
  "total_frames": 1500,
  "total_bottles": 45,
  "total_classifications": 42,
  "computational_reduction_pct": 97.2,
  "average_fps": 16.7,
  "state_distribution": {
    "NEW": 2,
    "TRACKED": 1,
    "CLASSIFIED": 40,
    "FAILED": 2
  },
  "detection_records": 4500
}
```

### Fields

- `session_start`: Session start timestamp
- `session_end`: Session end timestamp
- `duration_seconds`: Session duration in seconds
- `total_frames`: Total frames processed
- `total_bottles`: Total unique bottles tracked
- `total_classifications`: Total classification operations
- `computational_reduction_pct`: Percentage reduction vs per-frame classification
- `average_fps`: Average frames per second
- `state_distribution`: Count of bottles by final state
- `detection_records`: Total detection records logged

### Usage

**Automatic save on exit**:

- Summary is automatically saved when you quit (press `q`)
- File: `exports/ekovision_YYYY-MM-DD_HH-MM-SS.summary.json`
- Also printed to console

**Console output**:

```
============================================================
SESSION SUMMARY
============================================================
Duration: 900.0 seconds
Total frames: 1500
Total bottles: 45
Total classifications: 42
Computational reduction: 97.2%
Average FPS: 16.7

State Distribution:
  NEW: 2
  TRACKED: 1
  CLASSIFIED: 40
  FAILED: 2
============================================================
```

## Workflow Examples

### Basic Workflow

1. Start system: `python run_detection_tracking.py`
2. Let system run and process bottles
3. Press `q` to quit
4. Check `exports/` directory for summary

### Analysis Workflow

1. Start system
2. Run for desired duration
3. Press `e` to export CSV
4. Press `j` to export JSON
5. Continue running or quit
6. Analyze data with Python/Excel

### Documentation Workflow

1. Start system
2. Press `v` to start recording
3. Demonstrate system functionality
4. Press `v` to stop recording
5. Press `q` to quit
6. Use video for presentations/documentation

### Debugging Workflow

1. Start system
2. Press `v` to start recording
3. Reproduce issue
4. Press `e` to export CSV (for detailed analysis)
5. Press `v` to stop recording
6. Press `q` to quit
7. Review video and CSV to identify issue

## File Management

### Directory Structure

```
project/
├── exports/
│   ├── ekovision_2026-02-12_14-30-45.csv
│   ├── ekovision_2026-02-12_14-30-45.json
│   ├── ekovision_2026-02-12_14-30-45.mp4
│   ├── ekovision_2026-02-12_14-30-45.summary.json
│   ├── ekovision_2026-02-12_15-00-00.csv
│   └── ...
```

### Cleanup

**Manual cleanup**:

```bash
# Delete all exports
rm -rf exports/*

# Delete old exports (Linux/Mac)
find exports/ -name "*.csv" -mtime +7 -delete

# Delete old exports (Windows PowerShell)
Get-ChildItem exports/ -Filter *.csv | Where-Object {$_.LastWriteTime -lt (Get-Date).AddDays(-7)} | Remove-Item
```

**Selective cleanup**:

```bash
# Keep only summaries
rm exports/*.csv exports/*.json exports/*.mp4

# Keep only videos
rm exports/*.csv exports/*.json exports/*.summary.json
```

### Backup

**Backup exports**:

```bash
# Create backup directory
mkdir backups

# Copy exports
cp -r exports/ backups/exports_2026-02-12/

# Or create archive
tar -czf backups/exports_2026-02-12.tar.gz exports/
```

## Performance Impact

| Feature         | FPS Impact | Disk Usage           |
| --------------- | ---------- | -------------------- |
| CSV Logging     | <0.1 FPS   | ~1 KB per bottle     |
| JSON Logging    | <0.1 FPS   | ~2 KB per bottle     |
| Video Recording | ~1-2 FPS   | ~10-20 MB per minute |
| Session Summary | <0.1 FPS   | ~1 KB                |

**Tips**:

- Logging has minimal performance impact
- Video recording has small FPS impact (acceptable for documentation)
- Export operations (pressing `e` or `j`) are fast (<1 second)

## Troubleshooting

### Export Directory Not Created

**Problem**: `exports/` directory doesn't exist

**Solution**: Directory is created automatically on first export. If it fails, create manually:

```bash
mkdir exports
```

### Permission Denied

**Problem**: Cannot write to `exports/` directory

**Solution**: Check directory permissions:

```bash
# Linux/Mac
chmod 755 exports/

# Windows: Right-click → Properties → Security → Edit permissions
```

### Video File Corrupted

**Problem**: Video file won't play

**Solution**:

- Always stop recording properly (press `v` or `q`)
- Don't force-quit the application during recording
- If corrupted, try VLC player (more forgiving)

### Large File Sizes

**Problem**: Export files are too large

**Solution**:

- CSV/JSON: Normal, contains all data
- Video: Reduce camera resolution in `config.yaml`
- Compress old files: `gzip exports/*.csv`

## Integration with Analysis Tools

### Python (pandas)

```python
import pandas as pd
import json

# Load CSV
df = pd.read_csv('exports/ekovision_2026-02-12_14-30-45.csv')

# Load JSON
with open('exports/ekovision_2026-02-12_14-30-45.json') as f:
    data = json.load(f)

# Analysis
print(df.describe())
print(df['brand'].value_counts())
```

### Excel

1. Open CSV in Excel
2. Data → From Text/CSV
3. Use PivotTable for analysis
4. Create charts

### Power BI / Tableau

1. Import CSV as data source
2. Create visualizations
3. Build dashboards

### Custom Scripts

```python
# Example: Count bottles per hour
import pandas as pd

df = pd.read_csv('exports/ekovision_2026-02-12_14-30-45.csv')
df['timestamp'] = pd.to_datetime(df['timestamp'])
df['hour'] = df['timestamp'].dt.hour

bottles_per_hour = df.groupby('hour')['track_id'].nunique()
print(bottles_per_hour)
```

## Support

For issues or questions:

1. Check this guide
2. Check `RUNNING_GUIDE.md` for general usage
3. Check `CONFIGURATION_GUIDE.md` for settings
4. Open an issue in the repository
