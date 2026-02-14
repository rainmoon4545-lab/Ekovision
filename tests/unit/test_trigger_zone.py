"""
Unit tests for TriggerZone class.
"""
import numpy as np
import pytest
import cv2
from src.tracking.trigger_zone import TriggerZone, TriggerZoneConfig


class TestTriggerZoneConfig:
    """Tests for TriggerZoneConfig."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = TriggerZoneConfig()
        assert config.x_offset_pct == 30.0
        assert config.y_offset_pct == 20.0
        assert config.width_pct == 40.0
        assert config.height_pct == 60.0
    
    def test_valid_config(self):
        """Test validation of valid configuration."""
        config = TriggerZoneConfig(
            x_offset_pct=25.0,
            y_offset_pct=15.0,
            width_pct=50.0,
            height_pct=70.0
        )
        assert config.validate()
    
    def test_invalid_negative_offset(self):
        """Test validation rejects negative offsets."""
        config = TriggerZoneConfig(x_offset_pct=-10.0)
        assert not config.validate()
    
    def test_invalid_large_offset(self):
        """Test validation rejects offsets > 50%."""
        config = TriggerZoneConfig(x_offset_pct=60.0)
        assert not config.validate()
    
    def test_invalid_small_width(self):
        """Test validation rejects width < 20%."""
        config = TriggerZoneConfig(width_pct=10.0)
        assert not config.validate()
    
    def test_invalid_large_width(self):
        """Test validation rejects width > 80%."""
        config = TriggerZoneConfig(width_pct=90.0)
        assert not config.validate()
    
    def test_invalid_exceeds_frame(self):
        """Test validation rejects config that exceeds frame boundaries."""
        config = TriggerZoneConfig(x_offset_pct=40.0, width_pct=70.0)
        assert not config.validate()
    
    def test_clamp_negative_values(self):
        """Test clamping negative values."""
        config = TriggerZoneConfig(x_offset_pct=-10.0, y_offset_pct=-5.0)
        clamped = config.clamp()
        assert clamped.x_offset_pct == 0.0
        assert clamped.y_offset_pct == 0.0
    
    def test_clamp_large_values(self):
        """Test clamping values that exceed limits."""
        config = TriggerZoneConfig(width_pct=90.0, height_pct=95.0)
        clamped = config.clamp()
        # Width is clamped to 80, but then adjusted to fit within frame
        # Default x_offset is 30%, so max width is 70% (100 - 30)
        assert clamped.width_pct == 70.0
        # Height is clamped to 80, but then adjusted to fit within frame
        # Default y_offset is 20%, so max height is 80% (100 - 20)
        assert clamped.height_pct == 80.0
    
    def test_clamp_exceeds_frame(self):
        """Test clamping when zone exceeds frame boundaries."""
        config = TriggerZoneConfig(x_offset_pct=40.0, width_pct=70.0)
        clamped = config.clamp()
        assert clamped.x_offset_pct + clamped.width_pct <= 100


class TestTriggerZone:
    """Tests for TriggerZone class."""
    
    def test_initialization_default_config(self):
        """Test initialization with default configuration."""
        zone = TriggerZone(frame_width=640, frame_height=480)
        assert zone.frame_width == 640
        assert zone.frame_height == 480
        assert zone.config is not None
    
    def test_initialization_custom_config(self):
        """Test initialization with custom configuration."""
        config = TriggerZoneConfig(
            x_offset_pct=25.0,
            y_offset_pct=15.0,
            width_pct=50.0,
            height_pct=70.0
        )
        zone = TriggerZone(frame_width=640, frame_height=480, config=config)
        assert zone.config.x_offset_pct == 25.0
        assert zone.config.y_offset_pct == 15.0
    
    def test_get_boundaries(self):
        """Test getting pixel boundaries from percentage config."""
        config = TriggerZoneConfig(
            x_offset_pct=25.0,  # 25% of 640 = 160
            y_offset_pct=20.0,  # 20% of 480 = 96
            width_pct=50.0,     # 50% of 640 = 320
            height_pct=60.0     # 60% of 480 = 288
        )
        zone = TriggerZone(frame_width=640, frame_height=480, config=config)
        x1, y1, x2, y2 = zone.get_boundaries()
        
        assert x1 == 160
        assert y1 == 96
        assert x2 == 160 + 320  # 480
        assert y2 == 96 + 288   # 384
    
    def test_contains_point_inside(self):
        """Test point inside trigger zone."""
        zone = TriggerZone(frame_width=640, frame_height=480)
        x1, y1, x2, y2 = zone.get_boundaries()
        
        # Test center point
        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2
        assert zone.contains_point(center_x, center_y)
    
    def test_contains_point_outside(self):
        """Test point outside trigger zone."""
        zone = TriggerZone(frame_width=640, frame_height=480)
        
        # Test point at origin (should be outside default zone)
        assert not zone.contains_point(0, 0)
        
        # Test point at bottom-right corner
        assert not zone.contains_point(639, 479)
    
    def test_contains_point_on_boundary(self):
        """Test point on trigger zone boundary."""
        zone = TriggerZone(frame_width=640, frame_height=480)
        x1, y1, x2, y2 = zone.get_boundaries()
        
        # Points on boundary should be inside
        assert zone.contains_point(x1, y1)
        assert zone.contains_point(x2, y2)
    
    def test_update_config(self):
        """Test updating trigger zone configuration."""
        zone = TriggerZone(frame_width=640, frame_height=480)
        old_boundaries = zone.get_boundaries()
        
        new_config = TriggerZoneConfig(
            x_offset_pct=10.0,
            y_offset_pct=10.0,
            width_pct=30.0,
            height_pct=40.0
        )
        zone.update_config(new_config)
        new_boundaries = zone.get_boundaries()
        
        assert old_boundaries != new_boundaries
        assert zone.config.x_offset_pct == 10.0
    
    def test_update_config_invalid_clamped(self):
        """Test updating with invalid config gets clamped."""
        zone = TriggerZone(frame_width=640, frame_height=480)
        
        invalid_config = TriggerZoneConfig(
            x_offset_pct=-10.0,  # Invalid
            y_offset_pct=20.0,
            width_pct=40.0,
            height_pct=60.0
        )
        zone.update_config(invalid_config)
        
        # Should be clamped to 0
        assert zone.config.x_offset_pct == 0.0
    
    def test_draw_overlay(self):
        """Test drawing trigger zone overlay on frame."""
        zone = TriggerZone(frame_width=640, frame_height=480)
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        annotated = zone.draw_overlay(frame)
        
        assert annotated.shape == frame.shape
        assert not np.array_equal(annotated, frame)  # Frame should be modified
    
    def test_draw_overlay_custom_color(self):
        """Test drawing overlay with custom color."""
        zone = TriggerZone(frame_width=640, frame_height=480)
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        annotated = zone.draw_overlay(frame, color=(255, 0, 0), thickness=3)
        
        assert annotated.shape == frame.shape
    
    def test_get_center(self):
        """Test getting center point of trigger zone."""
        config = TriggerZoneConfig(
            x_offset_pct=20.0,  # 20% of 640 = 128
            y_offset_pct=20.0,  # 20% of 480 = 96
            width_pct=60.0,     # 60% of 640 = 384
            height_pct=60.0     # 60% of 480 = 288
        )
        zone = TriggerZone(frame_width=640, frame_height=480, config=config)
        center_x, center_y = zone.get_center()
        
        # Center should be at (128 + 384/2, 96 + 288/2) = (320, 240)
        assert center_x == 320
        assert center_y == 240
    
    def test_get_area(self):
        """Test getting area of trigger zone."""
        config = TriggerZoneConfig(
            x_offset_pct=25.0,  # 25% of 640 = 160
            y_offset_pct=20.0,  # 20% of 480 = 96
            width_pct=50.0,     # 50% of 640 = 320
            height_pct=60.0     # 60% of 480 = 288
        )
        zone = TriggerZone(frame_width=640, frame_height=480, config=config)
        area = zone.get_area()
        
        # Area should be 320 * 288 = 92160
        assert area == 320 * 288
    
    def test_boundaries_within_frame(self):
        """Test that boundaries never exceed frame dimensions."""
        config = TriggerZoneConfig(
            x_offset_pct=45.0,
            y_offset_pct=45.0,
            width_pct=60.0,
            height_pct=60.0
        )
        zone = TriggerZone(frame_width=640, frame_height=480, config=config)
        x1, y1, x2, y2 = zone.get_boundaries()
        
        assert 0 <= x1 <= 640
        assert 0 <= y1 <= 480
        assert 0 <= x2 <= 640
        assert 0 <= y2 <= 480
    
    def test_repr(self):
        """Test string representation."""
        zone = TriggerZone(frame_width=640, frame_height=480)
        repr_str = repr(zone)
        
        assert "TriggerZone" in repr_str
        assert "640x480" in repr_str
