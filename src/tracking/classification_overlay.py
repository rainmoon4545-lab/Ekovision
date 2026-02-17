"""
ClassificationOverlay - Renders classification results overlay at the top of the frame.

This module provides a component for displaying classification results in a permanent
overlay area at the top of the video frame, complementing the per-bottle labels.
"""
from dataclasses import dataclass
from typing import Tuple, List, Dict, Any, Optional
import numpy as np
import cv2
import logging

from .bottle_tracker import BottleTrack, TrackingState


# Configure logging
logger = logging.getLogger(__name__)


# Category colors (BGR format) - consistent with pipeline rendering
CATEGORY_COLORS = {
    'product': (255, 0, 0),      # Blue
    'grade': (0, 255, 0),        # Green
    'cap': (0, 0, 255),          # Red
    'label': (255, 255, 0),      # Cyan
    'brand': (255, 0, 255),      # Magenta
    'type': (0, 255, 255),       # Yellow
    'subtype': (128, 128, 255),  # Light Red
    'volume': (255, 128, 0)      # Orange
}


@dataclass
class OverlayConfig:
    """Configuration for classification overlay."""
    position: str = "top-center"  # "top-left", "top-center", "top-right"
    background_color: Tuple[int, int, int] = (0, 0, 0)  # BGR
    background_alpha: float = 0.7  # 0.0-1.0
    font_scale: float = 0.6
    font_thickness: int = 2
    padding: int = 10
    margin_top: int = 10
    max_tracks_display: int = 3
    min_overlay_height: int = 150
    attribute_spacing: int = 25


@dataclass
class OverlayLayout:
    """Layout configuration for overlay rendering."""
    overlay_x: int
    overlay_y: int
    overlay_width: int
    overlay_height: int
    num_columns: int
    column_width: int
    row_height: int


class ClassificationOverlay:
    """
    Renders classification results overlay at the top of the frame.
    
    This class provides a permanent overlay display area that shows classification
    results for all active tracked bottles. The overlay appears at the top of the
    frame and displays results in a multi-column layout when needed.
    """
    
    def __init__(
        self,
        position: str = "top-center",
        background_color: Tuple[int, int, int] = (0, 0, 0),
        background_alpha: float = 0.7,
        font_scale: float = 0.6,
        font_thickness: int = 2,
        padding: int = 10,
        max_tracks_display: int = 3
    ):
        """
        Initialize overlay renderer.
        
        Args:
            position: Overlay position ("top-left", "top-center", "top-right")
            background_color: Background color in BGR format
            background_alpha: Background transparency (0.0-1.0)
            font_scale: Font size scale
            font_thickness: Font thickness
            padding: Padding around content in pixels
            max_tracks_display: Maximum number of tracks to display
        """
        self.config = OverlayConfig(
            position=position,
            background_color=background_color,
            background_alpha=background_alpha,
            font_scale=font_scale,
            font_thickness=font_thickness,
            padding=padding,
            max_tracks_display=max_tracks_display
        )
        
        # Store configuration values as instance attributes for easy access
        self.position = position
        self.background_color = background_color
        self.background_alpha = background_alpha
        self.font_scale = font_scale
        self.font_thickness = font_thickness
        self.padding = padding
        self.margin_top = self.config.margin_top
        self.max_tracks_display = max_tracks_display
        self.min_overlay_height = self.config.min_overlay_height
        self.attribute_spacing = self.config.attribute_spacing
        
        logger.info(
            f"ClassificationOverlay initialized: position={position}, "
            f"alpha={background_alpha}, max_tracks={max_tracks_display}"
        )
    
    def render(
        self,
        frame: np.ndarray,
        tracks: List[BottleTrack],
        cache: Dict[int, Dict[str, str]]
    ) -> np.ndarray:
        """
        Render overlay on frame.
        
        Args:
            frame: Input frame in BGR format
            tracks: List of active BottleTrack objects
            cache: Classification results cache {track_id: results}
        
        Returns:
            Frame with overlay rendered
        """
        try:
            # Validate frame
            if frame is None or frame.size == 0:
                logger.warning("Invalid frame provided to render")
                return frame
            
            frame_height, frame_width = frame.shape[:2]
            if frame_width <= 0 or frame_height <= 0:
                logger.warning(f"Invalid frame dimensions: {frame_width}x{frame_height}")
                return frame
            
            # Filter tracks for only CLASSIFIED tracks
            classified_tracks = [
                track for track in tracks 
                if track.state == TrackingState.CLASSIFIED
            ]
            
            # Sort tracks by track_id (ascending)
            classified_tracks.sort(key=lambda t: t.track_id)
            
            # Limit tracks to max_tracks_display
            has_more_tracks = len(classified_tracks) > self.max_tracks_display
            num_additional_tracks = len(classified_tracks) - self.max_tracks_display
            display_tracks = classified_tracks[:self.max_tracks_display]
            
            # Calculate layout based on number of tracks to display
            num_tracks = len(display_tracks)
            
            # Handle empty state (no classified tracks)
            if num_tracks == 0:
                # Calculate layout for empty state
                layout = self._calculate_layout(frame_width, frame_height, 1)
                
                # Draw background
                frame = self._draw_background(
                    frame,
                    layout.overlay_x,
                    layout.overlay_y,
                    layout.overlay_width,
                    layout.overlay_height
                )
                
                # Draw empty state message
                frame = self._draw_empty_state(
                    frame,
                    layout.overlay_x,
                    layout.overlay_y,
                    layout.overlay_width,
                    layout.overlay_height
                )
                
                return frame
            
            # Calculate layout for displaying tracks
            layout = self._calculate_layout(frame_width, frame_height, num_tracks)
            
            # Draw background
            frame = self._draw_background(
                frame,
                layout.overlay_x,
                layout.overlay_y,
                layout.overlay_width,
                layout.overlay_height
            )
            
            # Draw track results in columns
            for i, track in enumerate(display_tracks):
                # Calculate column position
                column_index = i % layout.num_columns
                column_x = layout.overlay_x + self.padding + (column_index * (layout.column_width + self.padding))
                column_y = layout.overlay_y + self.padding
                
                # Get classification results from cache
                results = cache.get(track.track_id, {})
                
                # Draw track results
                self._draw_track_results(
                    frame,
                    track,
                    results,
                    column_x,
                    column_y,
                    layout.column_width
                )
            
            # Add "+N more" indicator if there are additional tracks
            if has_more_tracks:
                indicator_text = f"+{num_additional_tracks} more"
                font = cv2.FONT_HERSHEY_SIMPLEX
                indicator_color = (200, 200, 200)  # Light gray
                
                # Position at bottom-right of overlay
                (text_w, text_h), _ = cv2.getTextSize(
                    indicator_text, font, self.font_scale * 0.8, self.font_thickness
                )
                
                indicator_x = layout.overlay_x + layout.overlay_width - text_w - self.padding
                indicator_y = layout.overlay_y + layout.overlay_height - self.padding
                
                # Draw text background
                bg_x1 = indicator_x - 5
                bg_y1 = indicator_y - text_h - 5
                bg_x2 = indicator_x + text_w + 5
                bg_y2 = indicator_y + 5
                cv2.rectangle(frame, (bg_x1, bg_y1), (bg_x2, bg_y2), (60, 60, 60), -1)
                
                # Draw indicator text
                cv2.putText(
                    frame, indicator_text, (indicator_x, indicator_y),
                    font, self.font_scale * 0.8, indicator_color, self.font_thickness
                )
            
            return frame
            
        except Exception as e:
            # Return original frame if error occurs
            logger.error(f"Error rendering overlay: {e}")
            return frame
    
    def _calculate_layout(
        self,
        frame_width: int,
        frame_height: int,
        num_tracks: int
    ) -> OverlayLayout:
        """
        Calculate overlay layout dimensions and positions.
        
        Args:
            frame_width: Frame width in pixels
            frame_height: Frame height in pixels
            num_tracks: Number of tracks to display
        
        Returns:
            OverlayLayout object with layout information
        """
        # Determine number of columns based on number of tracks
        # Multi-column layout activates when more than 2 tracks
        if num_tracks > 2:
            num_columns = min(num_tracks, 3)  # Max 3 columns
        else:
            num_columns = num_tracks if num_tracks > 0 else 1
        
        # Calculate row height based on number of attributes (8) plus header
        # Each attribute needs attribute_spacing pixels
        num_attributes = 8
        row_height = (num_attributes + 1) * self.attribute_spacing + self.padding * 2
        
        # Calculate overlay height (ensure minimum height)
        overlay_height = max(row_height, self.min_overlay_height)
        
        # Calculate column width based on number of columns
        # Each column needs space for text (estimate ~250 pixels per column)
        column_width = 250
        overlay_width = (column_width * num_columns) + (self.padding * (num_columns + 1))
        
        # Ensure overlay width doesn't exceed frame width
        max_width = frame_width - (2 * self.padding)
        if overlay_width > max_width:
            overlay_width = max_width
            column_width = (overlay_width - (self.padding * (num_columns + 1))) // num_columns
        
        # Ensure overlay height doesn't exceed half of frame height
        max_height = frame_height // 2
        if overlay_height > max_height:
            overlay_height = max_height
        
        # Calculate overlay position based on position parameter
        if self.position == "top-left":
            overlay_x = self.padding
        elif self.position == "top-right":
            overlay_x = frame_width - overlay_width - self.padding
        else:  # "top-center" (default)
            overlay_x = (frame_width - overlay_width) // 2
        
        overlay_y = self.margin_top
        
        # Validate coordinates don't exceed frame dimensions
        overlay_x = max(0, min(overlay_x, frame_width - overlay_width))
        overlay_y = max(0, min(overlay_y, frame_height - overlay_height))
        
        # Ensure overlay fits within frame bounds
        if overlay_x + overlay_width > frame_width:
            overlay_width = frame_width - overlay_x
        if overlay_y + overlay_height > frame_height:
            overlay_height = frame_height - overlay_y
        
        return OverlayLayout(
            overlay_x=overlay_x,
            overlay_y=overlay_y,
            overlay_width=overlay_width,
            overlay_height=overlay_height,
            num_columns=num_columns,
            column_width=column_width,
            row_height=row_height
        )
    
    def _draw_background(
        self,
        frame: np.ndarray,
        x: int,
        y: int,
        width: int,
        height: int
    ) -> np.ndarray:
        """
        Draw semi-transparent background.

        Args:
            frame: Input frame
            x: Top-left x coordinate
            y: Top-left y coordinate
            width: Background width
            height: Background height

        Returns:
            Frame with background drawn
        """
        try:
            # Validate frame
            if frame is None or frame.size == 0:
                logger.warning("Invalid frame provided to _draw_background")
                return frame

            frame_height, frame_width = frame.shape[:2]

            # Handle edge case: overlay area exceeds frame boundaries
            # Clamp coordinates to frame boundaries
            x = max(0, min(x, frame_width - 1))
            y = max(0, min(y, frame_height - 1))

            # Adjust width and height to fit within frame
            if x + width > frame_width:
                width = frame_width - x
            if y + height > frame_height:
                height = frame_height - y

            # Ensure width and height are positive
            if width <= 0 or height <= 0:
                logger.warning(
                    f"Invalid overlay dimensions after bounds checking: "
                    f"width={width}, height={height}"
                )
                return frame

            # Create a copy of the overlay region
            overlay_region = frame[y:y+height, x:x+width].copy()

            # Create a solid background with the configured color
            background = np.full_like(overlay_region, self.background_color, dtype=np.uint8)

            # Blend the background with the original frame using alpha blending
            # cv2.addWeighted: dst = src1 * alpha + src2 * beta + gamma
            # We want: result = background * alpha + original * (1 - alpha)
            blended = cv2.addWeighted(
                background,
                self.background_alpha,
                overlay_region,
                1.0 - self.background_alpha,
                0
            )

            # Place the blended region back onto the frame
            frame[y:y+height, x:x+width] = blended

            return frame

        except Exception as e:
            logger.error(f"Error drawing background: {e}")
            return frame


    
    def _draw_track_results(
        self,
        frame: np.ndarray,
        track: BottleTrack,
        results: Dict[str, str],
        x: int,
        y: int,
        column_width: int
    ) -> int:
        """
        Draw classification results for a single track.
        
        Args:
            frame: Input frame
            track: BottleTrack object
            results: Classification results dictionary
            x: Starting x coordinate
            y: Starting y coordinate
            column_width: Width of the column
        
        Returns:
            Height used by this track's results
        """
        current_y = y
        font = cv2.FONT_HERSHEY_SIMPLEX
        
        # Render track ID as header
        header_text = f"Track #{track.track_id}"
        header_color = (255, 255, 255)  # White for header
        
        # Get text size for header
        (header_w, header_h), _ = cv2.getTextSize(
            header_text, font, self.font_scale, self.font_thickness
        )
        
        # Draw text background for header
        bg_x1 = x
        bg_y1 = current_y - header_h - 5
        bg_x2 = x + header_w + 10
        bg_y2 = current_y + 5
        cv2.rectangle(frame, (bg_x1, bg_y1), (bg_x2, bg_y2), (50, 50, 50), -1)
        
        # Draw header text
        cv2.putText(
            frame, header_text, (x + 5, current_y),
            font, self.font_scale, header_color, self.font_thickness
        )
        
        current_y += self.attribute_spacing
        
        # Define all 8 expected attributes in order
        expected_attributes = ['product', 'grade', 'cap', 'label', 'brand', 'type', 'subtype', 'volume']
        
        # Render all 8 attributes with format "name: value"
        for attr in expected_attributes:
            # Handle incomplete classification results (missing attributes → "N/A")
            value = results.get(attr, "N/A")
            
            # Format text as "name: value"
            attr_text = f"{attr}: {value}"
            
            # Get color for this attribute from CATEGORY_COLORS
            attr_color = CATEGORY_COLORS.get(attr, (255, 255, 255))
            
            # Get text size for this attribute
            (text_w, text_h), _ = cv2.getTextSize(
                attr_text, font, self.font_scale, self.font_thickness
            )
            
            # Draw text background for this attribute
            bg_x1 = x
            bg_y1 = current_y - text_h - 5
            bg_x2 = x + text_w + 10
            bg_y2 = current_y + 5
            cv2.rectangle(frame, (bg_x1, bg_y1), (bg_x2, bg_y2), (40, 40, 40), -1)
            
            # Draw attribute text
            cv2.putText(
                frame, attr_text, (x + 5, current_y),
                font, self.font_scale, attr_color, self.font_thickness
            )
            
            # Move to next line with proper vertical spacing
            current_y += self.attribute_spacing
        
        # Return height used by this track's results
        height_used = current_y - y
        return height_used
    
    def _draw_empty_state(
        self,
        frame: np.ndarray,
        x: int,
        y: int,
        width: int,
        height: int
    ) -> np.ndarray:
        """
        Draw empty state message when no classifications available.

        Args:
            frame: Input frame
            x: Top-left x coordinate
            y: Top-left y coordinate
            width: Overlay width
            height: Overlay height

        Returns:
            Frame with empty state message
        """
        # Message to display
        message = "Menunggu klasifikasi..."

        # Use consistent font with track results
        font = cv2.FONT_HERSHEY_SIMPLEX

        # Get text size to center it
        (text_w, text_h), _ = cv2.getTextSize(
            message, font, self.font_scale, self.font_thickness
        )

        # Calculate center position within overlay
        text_x = x + (width - text_w) // 2
        text_y = y + (height + text_h) // 2

        # Draw text background for contrast
        bg_x1 = text_x - 5
        bg_y1 = text_y - text_h - 5
        bg_x2 = text_x + text_w + 5
        bg_y2 = text_y + 5
        cv2.rectangle(frame, (bg_x1, bg_y1), (bg_x2, bg_y2), (50, 50, 50), -1)

        # Draw message text in white
        text_color = (255, 255, 255)
        cv2.putText(
            frame, message, (text_x, text_y),
            font, self.font_scale, text_color, self.font_thickness
        )

        return frame


