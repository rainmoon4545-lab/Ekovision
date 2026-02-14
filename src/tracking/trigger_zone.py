"""
TriggerZone class for defining classification trigger regions.
"""
import cv2
import numpy as np
from typing import Tuple, Optional
from dataclasses import dataclass


@dataclass
class TriggerZoneConfig:
    """Configuration for trigger zone."""
    x_offset_pct: float = 30.0  # X offset from left edge (percentage)
    y_offset_pct: float = 20.0  # Y offset from top edge (percentage)
    width_pct: float = 40.0     # Zone width (percentage)
    height_pct: float = 60.0    # Zone height (percentage)
    
    def validate(self) -> bool:
        """
        Validate configuration values.
        
        Returns:
            True if valid, False otherwise
        """
        if not (0 <= self.x_offset_pct <= 50):
            return False
        if not (0 <= self.y_offset_pct <= 50):
            return False
        if not (20 <= self.width_pct <= 80):
            return False
        if not (20 <= self.height_pct <= 80):
            return False
        if self.x_offset_pct + self.width_pct > 100:
            return False
        if self.y_offset_pct + self.height_pct > 100:
            return False
        return True
    
    def clamp(self) -> 'TriggerZoneConfig':
        """
        Clamp configuration values to valid ranges.
        
        Returns:
            New config with clamped values
        """
        x_offset = np.clip(self.x_offset_pct, 0, 50)
        y_offset = np.clip(self.y_offset_pct, 0, 50)
        width = np.clip(self.width_pct, 20, 80)
        height = np.clip(self.height_pct, 20, 80)
        
        # Ensure zone doesn't exceed frame boundaries
        if x_offset + width > 100:
            width = 100 - x_offset
        if y_offset + height > 100:
            height = 100 - y_offset
        
        return TriggerZoneConfig(
            x_offset_pct=x_offset,
            y_offset_pct=y_offset,
            width_pct=width,
            height_pct=height
        )


class TriggerZone:
    """
    Defines a rectangular trigger zone for classification.
    
    The trigger zone is specified using percentage-based coordinates
    relative to frame dimensions, making it resolution-independent.
    """
    
    def __init__(
        self,
        frame_width: int,
        frame_height: int,
        config: Optional[TriggerZoneConfig] = None
    ):
        """
        Initialize trigger zone.
        
        Args:
            frame_width: Width of video frame in pixels
            frame_height: Height of video frame in pixels
            config: Zone configuration (uses default if None)
        """
        self.frame_width = frame_width
        self.frame_height = frame_height
        
        if config is None:
            config = TriggerZoneConfig()
        
        # Validate and clamp config
        if not config.validate():
            print(f"Warning: Invalid trigger zone config, clamping to valid range")
            config = config.clamp()
        
        self.config = config
        self._update_boundaries()
    
    def _update_boundaries(self):
        """Calculate pixel coordinates from percentage-based config."""
        self.x1 = int(self.frame_width * self.config.x_offset_pct / 100)
        self.y1 = int(self.frame_height * self.config.y_offset_pct / 100)
        self.x2 = int(self.frame_width * (self.config.x_offset_pct + self.config.width_pct) / 100)
        self.y2 = int(self.frame_height * (self.config.y_offset_pct + self.config.height_pct) / 100)
        
        # Ensure boundaries are within frame
        self.x1 = max(0, min(self.x1, self.frame_width))
        self.y1 = max(0, min(self.y1, self.frame_height))
        self.x2 = max(0, min(self.x2, self.frame_width))
        self.y2 = max(0, min(self.y2, self.frame_height))
    
    def get_boundaries(self) -> Tuple[int, int, int, int]:
        """
        Get pixel coordinates of trigger zone boundaries.
        
        Returns:
            Tuple of (x1, y1, x2, y2) in pixels
        """
        return (self.x1, self.y1, self.x2, self.y2)
    
    def contains_point(self, x: float, y: float) -> bool:
        """
        Check if a point is inside the trigger zone.
        
        Args:
            x: X coordinate in pixels
            y: Y coordinate in pixels
        
        Returns:
            True if point is inside zone, False otherwise
        """
        return self.x1 <= x <= self.x2 and self.y1 <= y <= self.y2
    
    def update_config(self, config: TriggerZoneConfig):
        """
        Update trigger zone configuration.
        
        Args:
            config: New configuration
        """
        # Validate and clamp config
        if not config.validate():
            print(f"Warning: Invalid trigger zone config, clamping to valid range")
            config = config.clamp()
        
        self.config = config
        self._update_boundaries()
    
    def draw_overlay(
        self,
        frame: np.ndarray,
        color: Tuple[int, int, int] = (0, 255, 0),
        thickness: int = 2,
        alpha: float = 0.3
    ) -> np.ndarray:
        """
        Draw trigger zone overlay on frame.
        
        Args:
            frame: Input frame (BGR format)
            color: Zone border color in BGR
            thickness: Border line thickness
            alpha: Transparency for filled zone (0=transparent, 1=opaque)
        
        Returns:
            Frame with trigger zone overlay
        """
        overlay = frame.copy()
        
        # Draw filled rectangle with transparency
        cv2.rectangle(overlay, (self.x1, self.y1), (self.x2, self.y2), color, -1)
        frame = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)
        
        # Draw border
        cv2.rectangle(frame, (self.x1, self.y1), (self.x2, self.y2), color, thickness)
        
        # Draw label
        label = "TRIGGER ZONE"
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.6
        font_thickness = 2
        
        # Get text size for background
        (text_width, text_height), baseline = cv2.getTextSize(
            label, font, font_scale, font_thickness
        )
        
        # Draw text background
        text_x = self.x1 + 5
        text_y = self.y1 - 10
        if text_y < text_height + 10:
            text_y = self.y1 + text_height + 10
        
        cv2.rectangle(
            frame,
            (text_x - 2, text_y - text_height - 2),
            (text_x + text_width + 2, text_y + baseline + 2),
            (0, 0, 0),
            -1
        )
        
        # Draw text
        cv2.putText(
            frame,
            label,
            (text_x, text_y),
            font,
            font_scale,
            color,
            font_thickness
        )
        
        return frame
    
    def get_center(self) -> Tuple[int, int]:
        """
        Get center point of trigger zone.
        
        Returns:
            Tuple of (center_x, center_y) in pixels
        """
        center_x = (self.x1 + self.x2) // 2
        center_y = (self.y1 + self.y2) // 2
        return (center_x, center_y)
    
    def get_area(self) -> int:
        """
        Get area of trigger zone in pixels.
        
        Returns:
            Area in square pixels
        """
        width = self.x2 - self.x1
        height = self.y2 - self.y1
        return width * height
    
    def __repr__(self) -> str:
        """String representation of trigger zone."""
        return (
            f"TriggerZone(frame={self.frame_width}x{self.frame_height}, "
            f"zone=[{self.x1},{self.y1},{self.x2},{self.y2}], "
            f"config={self.config})"
        )
