# Camera Controls Guide

## Overview

The EkoVision system includes runtime camera controls for optimizing image quality in different lighting conditions and conveyor speeds.

## Features

- **Manual Exposure Control**: Adjust shutter speed for motion blur reduction
- **Brightness Adjustment**: Compensate for lighting conditions
- **Contrast Adjustment**: Enhance bottle visibility
- **Auto-Exposure Toggle**: Switch between manual and automatic exposure
- **Camera Presets**: Quick settings for common scenarios
- **Settings Validation**: Verify camera responds to programmatic control

## Activating Camera Controls

Press `c` to enter camera control mode.

When active, you'll see:

```
============================================================
CAMERA CONTROL MODE ACTIVE
============================================================
  [ / ]  - Decrease/Increase exposure
  - / +  - Decrease/Increase brightness
  a      - Toggle auto-exposure
  1      - Load 'Indoor' preset
  2      - Load 'Outdoor' preset
  3      - Load 'High Speed' preset
  c      - Close camera controls
============================================================
```

Press `c` again to exit camera control mode.

## Keyboard Controls

### Exposure Control

| Key | Action            | Description                             |
| --- | ----------------- | --------------------------------------- |
| `[` | Decrease exposure | Faster shutter speed (less motion blur) |
| `]` | Increase exposure | Slower shutter speed (brighter image)   |

**When to use**:

- **Fast conveyor**: Press `[` multiple times for faster shutter (1/1000 to 1/2000 sec)
- **Slow conveyor**: Press `]` for slower shutter (1/250 to 1/500 sec)
- **Dark environment**: Press `]` to brighten image

**Tips**:

- Each press adjusts by approximately 1 EV (double/half exposure time)
- Faster shutter = less motion blur but darker image
- Slower shutter = brighter image but more motion blur
- Requires good lighting for fast shutter speeds

### Brightness Control

| Key | Action              | Description    |
| --- | ------------------- | -------------- |
| `-` | Decrease brightness | Darker image   |
| `+` | Increase brightness | Brighter image |

**When to use**:

- **Too dark**: Press `+` multiple times
- **Too bright**: Press `-` multiple times
- **Overexposed**: Press `-` to reduce brightness

**Tips**:

- Each press adjusts by 5 units
- Range: -50 to +50
- Works independently of exposure
- Useful for fine-tuning after exposure adjustment

### Auto-Exposure Toggle

| Key | Action               | Description                         |
| --- | -------------------- | ----------------------------------- |
| `a` | Toggle auto-exposure | Switch between manual and automatic |

**When to use**:

- **Consistent lighting**: Use manual exposure for stable image
- **Variable lighting**: Use auto-exposure for adaptation
- **Testing**: Toggle to compare manual vs auto

**Tips**:

- Auto-exposure adapts to lighting changes automatically
- Manual exposure provides consistent image quality
- Recommended: Manual exposure for production use

### Camera Presets

| Key | Preset     | Description                           |
| --- | ---------- | ------------------------------------- |
| `1` | Indoor     | Optimized for indoor lighting         |
| `2` | Outdoor    | Optimized for outdoor/bright lighting |
| `3` | High Speed | Optimized for fast-moving bottles     |

**Preset Details**:

**Indoor Preset**:

- Exposure: 1/500 sec
- Brightness: +10
- Contrast: 1.2
- Auto-exposure: OFF
- **Use for**: Indoor factory with LED lighting

**Outdoor Preset**:

- Exposure: 1/1000 sec
- Brightness: -10
- Contrast: 1.0
- Auto-exposure: OFF
- **Use for**: Outdoor or very bright environments

**High Speed Preset**:

- Exposure: 1/2000 sec
- Brightness: 0
- Contrast: 1.5
- Auto-exposure: OFF
- **Use for**: Fast-moving conveyor (requires bright lighting)

## Camera Settings Display

Current settings are displayed when you adjust them:

```
==================================================
CAMERA SETTINGS
==================================================
Auto-exposure: OFF
Exposure: 1/500 sec
Brightness: 10
Contrast: 1.2
Manual control: Supported
==================================================
```

**Fields**:

- **Auto-exposure**: ON (automatic) or OFF (manual)
- **Exposure**: Shutter speed in seconds (only shown if manual)
- **Brightness**: Current brightness value (-50 to +50)
- **Contrast**: Current contrast multiplier (0.5 to 2.0)
- **Manual control**: Whether camera responds to programmatic control

## Camera Control Workflow

### Initial Setup

1. Start system: `python run_detection_tracking.py`
2. Press `c` to enter camera control mode
3. Test current settings with a few bottles
4. Adjust as needed

### Optimization Workflow

**For Motion Blur**:

1. Press `c` to enter camera control mode
2. Press `[` multiple times to increase shutter speed
3. If image too dark, press `+` to increase brightness
4. Test with moving bottles
5. Repeat until motion blur eliminated

**For Dark Image**:

1. Press `c` to enter camera control mode
2. Press `]` to decrease shutter speed (slower = brighter)
3. Or press `+` to increase brightness
4. Or press `1` to load Indoor preset
5. Test and adjust

**For Bright Image**:

1. Press `c` to enter camera control mode
2. Press `[` to increase shutter speed (faster = darker)
3. Or press `-` to decrease brightness
4. Or press `2` to load Outdoor preset
5. Test and adjust

### Quick Preset Selection

**Indoor Factory**:

1. Press `c`
2. Press `1` (Indoor preset)
3. Press `c` to close

**Outdoor/Bright**:

1. Press `c`
2. Press `2` (Outdoor preset)
3. Press `c` to close

**Fast Conveyor**:

1. Press `c`
2. Press `3` (High Speed preset)
3. Press `c` to close

## Camera Compatibility

### Supported Cameras

Most USB webcams and industrial cameras support basic controls:

- ✅ Brightness adjustment
- ✅ Auto-exposure toggle
- ⚠️ Manual exposure (varies by camera)
- ⚠️ Contrast adjustment (varies by camera)

### Camera Validation

The system validates camera settings by reading back values after applying them.

**Status Indicators**:

- **"Manual control: Supported"**: Camera responds to programmatic control
- **"Manual control: Not supported"**: Camera doesn't respond (use manual configuration)

### Non-Responsive Cameras

If your camera doesn't respond to programmatic control:

**Option 1: Use Camera Software**

- Most cameras have configuration software
- Set exposure, brightness, contrast manually
- Settings persist across sessions

**Option 2: Use OS Camera Settings**

- **Windows**: Camera app → Settings
- **Linux**: v4l2-ctl or guvcview
- **Mac**: System Preferences → Camera

**Option 3: Use Physical Controls**

- Some industrial cameras have physical dials
- Adjust exposure and brightness manually

### Recommended Cameras

For best results, use cameras with manual exposure control:

- **Industrial cameras**: Basler, FLIR, Allied Vision
- **Webcams**: Logitech C920/C930, Microsoft LifeCam
- **Action cameras**: GoPro (with USB output)

**Key features**:

- Manual exposure control
- Global shutter (preferred for fast motion)
- High frame rate (30+ FPS)
- Good low-light performance

## Troubleshooting

### Settings Don't Apply

**Problem**: Pressing keys doesn't change camera settings

**Solutions**:

1. Check if camera control mode is active (press `c`)
2. Check console for error messages
3. Try different camera (some don't support manual control)
4. Use camera software for manual configuration

### Image Too Dark

**Problem**: Image is too dark to see bottles

**Solutions**:

1. Press `]` to slow down shutter (brighter)
2. Press `+` to increase brightness
3. Add external lighting (LED floodlights)
4. Use Indoor preset (press `1`)

### Motion Blur

**Problem**: Bottles are blurry when moving

**Solutions**:

1. Press `[` to speed up shutter (less blur)
2. Add brighter lighting to compensate
3. Use High Speed preset (press `3`)
4. Reduce conveyor speed (if possible)

### Overexposed Image

**Problem**: Image is too bright, bottles washed out

**Solutions**:

1. Press `[` to speed up shutter (darker)
2. Press `-` to decrease brightness
3. Use Outdoor preset (press `2`)
4. Reduce external lighting

### Inconsistent Image Quality

**Problem**: Image quality varies over time

**Solutions**:

1. Disable auto-exposure (press `a` until OFF)
2. Set manual exposure and brightness
3. Ensure consistent lighting
4. Use preset for stable settings

## Best Practices

### Lighting Setup

**Recommended**:

- Bright LED floodlights (daylight white, 5000-6500K)
- Positioned to eliminate shadows
- Consistent intensity (no flickering)
- Sufficient for fast shutter speeds (1/1000 sec or faster)

**Avoid**:

- Fluorescent lights (can flicker at 50/60 Hz)
- Incandescent lights (too warm, inconsistent)
- Natural sunlight (varies throughout day)
- Backlighting (creates silhouettes)

### Camera Positioning

**Recommended**:

- Perpendicular to conveyor belt
- Height: 50-100 cm above bottles
- Angle: Straight down or slight angle
- Stable mounting (no vibration)

**Avoid**:

- Extreme angles (distortion)
- Too close (limited field of view)
- Too far (low resolution)
- Unstable mounting (motion blur)

### Settings for Different Scenarios

**Indoor Factory (LED lighting)**:

```
Preset: Indoor (press '1')
Or manual:
  Exposure: 1/500 sec (press '[' or ']')
  Brightness: +10 (press '+')
  Auto-exposure: OFF (press 'a')
```

**Outdoor/Bright Environment**:

```
Preset: Outdoor (press '2')
Or manual:
  Exposure: 1/1000 sec
  Brightness: -10 (press '-')
  Auto-exposure: OFF
```

**Fast Conveyor (>1 m/s)**:

```
Preset: High Speed (press '3')
Or manual:
  Exposure: 1/2000 sec (press '[' multiple times)
  Brightness: 0
  Contrast: 1.5
  Auto-exposure: OFF
Requires: Very bright lighting
```

**Slow Conveyor (<0.5 m/s)**:

```
Manual settings:
  Exposure: 1/250 sec (press ']' multiple times)
  Brightness: +5
  Auto-exposure: OFF
```

## Advanced Configuration

### Saving Settings

Camera settings are not automatically saved to config file.

**To save current settings**:

1. Note current settings (press `c` to view)
2. Edit `config.yaml` manually (future feature: auto-save)
3. Or use camera software to save to camera firmware

### Custom Presets

To create custom presets, edit `src/camera_controller.py`:

```python
PRESETS = {
    "Indoor": CameraPreset("Indoor", 1/500, 10, 1.2, False),
    "Outdoor": CameraPreset("Outdoor", 1/1000, -10, 1.0, False),
    "High Speed": CameraPreset("High Speed", 1/2000, 0, 1.5, False),
    "Custom": CameraPreset("Custom", 1/750, 5, 1.1, False),  # Add your preset
}
```

Then assign to keyboard shortcut in `run_detection_tracking.py`.

### Histogram-Based Validation

The system can validate brightness using histogram analysis:

```python
# In camera_controller.py
brightness_status = camera_ctrl.check_brightness_histogram(frame)
# Returns: "too_dark", "ok", or "too_bright"
```

This feature can be used for automatic brightness adjustment (future enhancement).

## Integration with Other Features

### With Data Logging

Camera settings are not logged by default.

**To log settings** (future enhancement):

- Add camera settings to session summary
- Include in CSV export metadata
- Record settings changes in log file

### With Configuration File

Camera settings can be loaded from `config.yaml` (future enhancement):

```yaml
camera:
  exposure: 0.002 # 1/500 sec
  brightness: 10
  contrast: 1.2
  auto_exposure: false
```

### With Batch Processing

Camera controls are not available in batch processing mode (video files don't have adjustable camera settings).

## Support

For issues or questions:

1. Check this guide
2. Check camera manufacturer documentation
3. Test with camera software first
4. Check `RUNNING_GUIDE.md` for general usage
5. Open an issue in the repository

## Appendix: Exposure Values

| Shutter Speed | Exposure Value | Use Case                    |
| ------------- | -------------- | --------------------------- |
| 1/250 sec     | -8             | Slow conveyor, low light    |
| 1/500 sec     | -9             | Standard indoor             |
| 1/1000 sec    | -10            | Fast conveyor, bright light |
| 1/2000 sec    | -11            | Very fast, very bright      |

**Note**: Exposure values are approximate and may vary by camera.
