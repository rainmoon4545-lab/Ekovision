# Advanced Trigger Zones Guide

## Overview

Advanced Trigger Zones allow you to define multiple classification zones instead of a single zone. This is useful for:

- Multi-lane conveyor belts
- Different product categories in different areas
- Selective classification regions
- Complex production line layouts

## Features

- **Multiple Zones**: Up to 3 trigger zones simultaneously
- **Zone Management**: Add, remove, enable/disable zones
- **Overlap Prevention**: Automatic validation prevents overlapping zones
- **Visual Distinction**: Color-coded zones (Green, Blue, Red)
- **Configuration**: Save/load zones from config.yaml
- **Mouse Editor**: Interactive zone editing (future feature)

## Configuration

### Enable Multiple Zones

Edit `config.yaml`:

```yaml
# Single zone mode (default - legacy)
trigger_zone:
  x_offset_pct: 30.0
  y_offset_pct: 20.0
  width_pct: 40.0
  height_pct: 60.0

# Multiple zones mode (new)
multi_zone:
  enabled: true # Enable multiple zones
  max_zones: 3 # Maximum number of zones
  zones:
    - x_offset_pct: 10.0
      y_offset_pct: 20.0
      width_pct: 25.0
      height_pct: 60.0
      enabled: true
      name: "Lane 1"

    - x_offset_pct: 40.0
      y_offset_pct: 20.0
      width_pct: 25.0
      height_pct: 60.0
      enabled: true
      name: "Lane 2"

    - x_offset_pct: 70.0
      y_offset_pct: 20.0
      width_pct: 25.0
      height_pct: 60.0
      enabled: true
      name: "Lane 3"
```

### Zone Parameters

| Parameter      | Type   | Range      | Description            |
| -------------- | ------ | ---------- | ---------------------- |
| `x_offset_pct` | float  | 0-100      | X offset from left (%) |
| `y_offset_pct` | float  | 0-100      | Y offset from top (%)  |
| `width_pct`    | float  | 1-100      | Zone width (%)         |
| `height_pct`   | float  | 1-100      | Zone height (%)        |
| `enabled`      | bool   | true/false | Zone active state      |
| `name`         | string | -          | Zone display name      |

## Usage Examples

### Example 1: Three-Lane Conveyor

For a conveyor belt with three parallel lanes:

```yaml
multi_zone:
  enabled: true
  max_zones: 3
  zones:
    # Left lane
    - x_offset_pct: 5.0
      y_offset_pct: 25.0
      width_pct: 28.0
      height_pct: 50.0
      enabled: true
      name: "Left Lane"

    # Center lane
    - x_offset_pct: 36.0
      y_offset_pct: 25.0
      width_pct: 28.0
      height_pct: 50.0
      enabled: true
      name: "Center Lane"

    # Right lane
    - x_offset_pct: 67.0
      y_offset_pct: 25.0
      width_pct: 28.0
      height_pct: 50.0
      enabled: true
      name: "Right Lane"
```

**Visual Layout**:

```
┌────────────────────────────────────────┐
│                                        │
│  ┌──────┐   ┌──────┐   ┌──────┐      │
│  │ Left │   │Center│   │Right │      │
│  │ Lane │   │ Lane │   │ Lane │      │
│  │      │   │      │   │      │      │
│  └──────┘   └──────┘   └──────┘      │
│                                        │
└────────────────────────────────────────┘
```

### Example 2: Vertical Zones

For products moving at different heights:

```yaml
multi_zone:
  enabled: true
  max_zones: 2
  zones:
    # Upper zone
    - x_offset_pct: 30.0
      y_offset_pct: 10.0
      width_pct: 40.0
      height_pct: 35.0
      enabled: true
      name: "Upper Zone"

    # Lower zone
    - x_offset_pct: 30.0
      y_offset_pct: 55.0
      width_pct: 40.0
      height_pct: 35.0
      enabled: true
      name: "Lower Zone"
```

### Example 3: Selective Classification

Enable only specific zones:

```yaml
multi_zone:
  enabled: true
  max_zones: 3
  zones:
    # Active zone
    - x_offset_pct: 20.0
      y_offset_pct: 20.0
      width_pct: 30.0
      height_pct: 60.0
      enabled: true
      name: "Active Zone"

    # Disabled zone (for testing)
    - x_offset_pct: 55.0
      y_offset_pct: 20.0
      width_pct: 30.0
      height_pct: 60.0
      enabled: false # Disabled
      name: "Test Zone"
```

## Python API

### Using ZoneManager

```python
from src.tracking.zone_manager import ZoneManager, ZoneManagerConfig
from src.tracking.trigger_zone import TriggerZoneConfig

# Create zone manager
config = ZoneManagerConfig(
    max_zones=3,
    zones=[
        {
            'x_offset_pct': 10.0,
            'y_offset_pct': 20.0,
            'width_pct': 25.0,
            'height_pct': 60.0,
            'enabled': True,
            'name': 'Zone 1'
        }
    ]
)

zone_manager = ZoneManager(
    frame_width=640,
    frame_height=480,
    config=config
)

# Add zone
new_zone_config = TriggerZoneConfig(
    x_offset_pct=40.0,
    y_offset_pct=20.0,
    width_pct=25.0,
    height_pct=60.0
)
zone_manager.add_zone(new_zone_config, name="Zone 2")

# Check if point is in any zone
is_in_zone, zone_idx = zone_manager.contains_point(100, 200)
if is_in_zone:
    print(f"Point is in zone {zone_idx}")

# Draw zones on frame
annotated_frame = zone_manager.draw_overlay(frame)

# Toggle zone
zone_manager.toggle_zone(0)  # Disable zone 0

# Save configuration
config = zone_manager.save_to_config()
```

### Adding Zones Programmatically

```python
# Add multiple zones
zones_to_add = [
    {
        'config': TriggerZoneConfig(10.0, 20.0, 25.0, 60.0),
        'name': 'Lane 1'
    },
    {
        'config': TriggerZoneConfig(40.0, 20.0, 25.0, 60.0),
        'name': 'Lane 2'
    },
    {
        'config': TriggerZoneConfig(70.0, 20.0, 25.0, 60.0),
        'name': 'Lane 3'
    }
]

for zone_data in zones_to_add:
    success = zone_manager.add_zone(
        zone_data['config'],
        name=zone_data['name']
    )
    if not success:
        print(f"Failed to add {zone_data['name']}")
```

## Zone Validation

### Overlap Detection

The system automatically prevents overlapping zones:

```python
# This will fail if zones overlap
success = zone_manager.add_zone(overlapping_config)
if not success:
    print("Zone overlaps with existing zone")
```

**Overlap Rules**:

- Zones cannot share any pixels
- Even 1-pixel overlap is rejected
- Validation happens automatically on add

### Boundary Validation

Zones must stay within frame boundaries:

```python
# Invalid: exceeds frame width
config = TriggerZoneConfig(
    x_offset_pct=80.0,
    width_pct=30.0  # 80 + 30 = 110% (invalid)
)

# System automatically clamps to valid range
zone = TriggerZone(640, 480, config)
# Zone will be adjusted to fit within frame
```

## Visual Indicators

### Zone Colors

- **Zone 1**: Green (0, 255, 0)
- **Zone 2**: Blue (255, 0, 0)
- **Zone 3**: Red (0, 0, 255)

### Zone States

- **Enabled**: Solid border, 30% transparency
- **Disabled**: Dashed border, 10% transparency, "(DISABLED)" label

### Zone Labels

Each zone displays:

- Zone name
- Enabled/disabled state
- Position (top-left corner)

## Performance Considerations

### Computational Impact

Multiple zones have minimal performance impact:

| Zones   | FPS Impact | Classification Load |
| ------- | ---------- | ------------------- |
| 1 zone  | Baseline   | 100%                |
| 2 zones | < 1%       | ~200%               |
| 3 zones | < 2%       | ~300%               |

**Note**: Classification load increases proportionally with active zones, but overall FPS impact is minimal due to efficient zone checking.

### Memory Usage

- Each zone: ~1 KB
- 3 zones: ~3 KB total
- Negligible impact on system memory

### Optimization Tips

1. **Disable Unused Zones**: Set `enabled: false` for zones not in use
2. **Minimize Overlap Checks**: Keep zones well-separated
3. **Appropriate Zone Sizes**: Larger zones = more classifications

## Troubleshooting

### Zone Not Appearing

**Problem**: Zone configured but not visible

**Solutions**:

- Check `multi_zone.enabled: true` in config
- Verify zone coordinates are within frame (0-100%)
- Ensure zone is enabled: `enabled: true`
- Check zone size (width/height > 0)

### Cannot Add Zone

**Problem**: `add_zone()` returns False

**Possible Causes**:

1. **Max zones reached**: Already have 3 zones
2. **Overlap detected**: New zone overlaps existing zone
3. **Invalid coordinates**: Zone exceeds frame boundaries

**Solutions**:

- Remove unused zones first
- Adjust zone position to avoid overlap
- Validate coordinates before adding

### Zones Overlapping

**Problem**: Zones appear to overlap visually

**Explanation**: This should not happen due to validation. If it does:

- Check if zones were added programmatically without validation
- Verify configuration file syntax
- Restart application to reload config

### Performance Degradation

**Problem**: FPS drops with multiple zones

**Possible Causes**:

- Too many bottles in multiple zones simultaneously
- All zones active with high traffic

**Solutions**:

- Reduce number of active zones
- Adjust zone sizes to reduce simultaneous classifications
- Increase cache size in config

## Best Practices

1. **Start Simple**: Begin with 1-2 zones, add more as needed
2. **Test Thoroughly**: Verify zones don't overlap before production
3. **Name Zones Clearly**: Use descriptive names (e.g., "Left Lane", not "Zone 1")
4. **Document Layout**: Keep a diagram of zone positions
5. **Monitor Performance**: Check FPS with all zones active
6. **Use Disable Feature**: Temporarily disable zones for testing
7. **Save Configurations**: Keep backup copies of working configs

## Migration from Single Zone

### Step 1: Backup Current Config

```bash
cp config.yaml config.yaml.backup
```

### Step 2: Enable Multi-Zone

```yaml
multi_zone:
  enabled: true
  max_zones: 3
  zones:
    # Copy your existing trigger_zone settings here
    - x_offset_pct: 30.0 # From trigger_zone.x_offset_pct
      y_offset_pct: 20.0 # From trigger_zone.y_offset_pct
      width_pct: 40.0 # From trigger_zone.width_pct
      height_pct: 60.0 # From trigger_zone.height_pct
      enabled: true
      name: "Main Zone"
```

### Step 3: Test

```bash
python run_detection_tracking.py
# Verify zone appears correctly
```

### Step 4: Add Additional Zones

Once first zone works, add more zones as needed.

## Future Features

- **Mouse-Based Editor**: Interactive zone creation and editing
- **Zone Templates**: Pre-defined layouts for common scenarios
- **Zone Analytics**: Per-zone statistics and reports
- **Dynamic Zones**: Zones that adapt to conveyor speed
- **Zone Priorities**: Different classification priorities per zone

## FAQ

**Q: Can I have more than 3 zones?**  
A: Currently limited to 3 zones. This can be increased in code by changing `max_zones` in `ZoneManagerConfig`.

**Q: Can zones have different shapes?**  
A: Currently only rectangular zones are supported.

**Q: Do all zones classify simultaneously?**  
A: Yes, if a bottle enters multiple zones, it will be classified in each zone.

**Q: Can I change zones during runtime?**  
A: Not currently. Zones are loaded from config at startup. Restart required for changes.

**Q: How do I know which zone triggered classification?**  
A: Check logs or use the Python API to track zone indices.

---

**Last Updated**: February 12, 2026  
**Version**: 1.0.0  
**Author**: EkoVision Development Team
