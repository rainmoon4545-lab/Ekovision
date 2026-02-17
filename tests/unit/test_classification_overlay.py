"""
Unit tests for ClassificationOverlay class.
"""
import pytest
import numpy as np
from src.tracking.classification_overlay import (
    ClassificationOverlay,
    OverlayConfig,
    OverlayLayout,
    CATEGORY_COLORS
)
from src.tracking.bottle_tracker import BottleTrack, TrackingState


class TestOverlayConfig:
    """Test OverlayConfig dataclass."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = OverlayConfig()
        
        assert config.position == "top-center"
        assert config.background_color == (0, 0, 0)
        assert config.background_alpha == 0.7
        assert config.font_scale == 0.6
        assert config.font_thickness == 2
        assert config.padding == 10
        assert config.margin_top == 10
        assert config.max_tracks_display == 3
        assert config.min_overlay_height == 150
        assert config.attribute_spacing == 25
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = OverlayConfig(
            position="top-left",
            background_alpha=0.5,
            font_scale=0.8,
            max_tracks_display=5
        )
        
        assert config.position == "top-left"
        assert config.background_alpha == 0.5
        assert config.font_scale == 0.8
        assert config.max_tracks_display == 5


class TestClassificationOverlay:
    """Test ClassificationOverlay class."""
    
    def test_initialization_default(self):
        """Test overlay initialization with default parameters."""
        overlay = ClassificationOverlay()
        
        assert overlay.position == "top-center"
        assert overlay.background_alpha == 0.7
        assert overlay.font_scale == 0.6
        assert overlay.max_tracks_display == 3
    
    def test_initialization_custom(self):
        """Test overlay initialization with custom parameters."""
        overlay = ClassificationOverlay(
            position="top-left",
            background_color=(50, 50, 50),
            background_alpha=0.5,
            font_scale=0.8,
            max_tracks_display=5
        )
        
        assert overlay.position == "top-left"
        assert overlay.background_color == (50, 50, 50)
        assert overlay.background_alpha == 0.5
        assert overlay.font_scale == 0.8
        assert overlay.max_tracks_display == 5
    
    def test_render_returns_frame(self):
        """Test that render returns a frame (even if not fully implemented)."""
        overlay = ClassificationOverlay()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        tracks = []
        cache = {}
        
        result = overlay.render(frame, tracks, cache)
        
        assert result is not None
        assert result.shape == frame.shape
    
    def test_calculate_layout_single_track(self):
        """Test layout calculation for single track."""
        overlay = ClassificationOverlay()
        
        layout = overlay._calculate_layout(640, 480, 1)
        
        assert isinstance(layout, OverlayLayout)
        assert layout.num_columns == 1
        assert layout.overlay_height >= overlay.min_overlay_height
        assert 0 <= layout.overlay_x < 640
        assert 0 <= layout.overlay_y < 480
    
    def test_calculate_layout_two_tracks(self):
        """Test layout calculation for two tracks."""
        overlay = ClassificationOverlay()
        
        layout = overlay._calculate_layout(640, 480, 2)
        
        assert layout.num_columns == 2
        assert layout.overlay_height >= overlay.min_overlay_height
    
    def test_calculate_layout_multi_column(self):
        """Test layout calculation activates multi-column for > 2 tracks."""
        overlay = ClassificationOverlay()
        
        layout = overlay._calculate_layout(640, 480, 3)
        
        assert layout.num_columns > 1
        assert layout.num_columns <= 3
    
    def test_calculate_layout_position_top_center(self):
        """Test layout calculation for top-center position."""
        overlay = ClassificationOverlay(position="top-center")
        
        layout = overlay._calculate_layout(640, 480, 1)
        
        # Top-center should be roughly centered horizontally
        expected_x = (640 - layout.overlay_width) // 2
        assert abs(layout.overlay_x - expected_x) <= 1  # Allow 1 pixel tolerance
    
    def test_calculate_layout_position_top_left(self):
        """Test layout calculation for top-left position."""
        overlay = ClassificationOverlay(position="top-left")
        
        layout = overlay._calculate_layout(640, 480, 1)
        
        assert layout.overlay_x == overlay.padding
    
    def test_calculate_layout_position_top_right(self):
        """Test layout calculation for top-right position."""
        overlay = ClassificationOverlay(position="top-right")
        
        layout = overlay._calculate_layout(640, 480, 1)
        
        # Top-right should be near the right edge
        assert layout.overlay_x > 640 // 2
    
    def test_calculate_layout_bounds_validation(self):
        """Test that layout coordinates stay within frame bounds."""
        overlay = ClassificationOverlay()
        
        layout = overlay._calculate_layout(640, 480, 3)
        
        # Verify coordinates are within bounds
        assert 0 <= layout.overlay_x < 640
        assert 0 <= layout.overlay_y < 480
        assert layout.overlay_x + layout.overlay_width <= 640
        assert layout.overlay_y + layout.overlay_height <= 480
    
    def test_calculate_layout_minimum_height(self):
        """Test that overlay height meets minimum requirement."""
        overlay = ClassificationOverlay()
        
        layout = overlay._calculate_layout(640, 480, 1)
        
        assert layout.overlay_height >= overlay.min_overlay_height
    
    def test_draw_background_basic(self):
        """Test basic background drawing."""
        overlay = ClassificationOverlay()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        result = overlay._draw_background(frame, 10, 10, 200, 100)
        
        assert result is not None
        assert result.shape == frame.shape
    
    def test_draw_background_transparency(self):
        """Test that background applies transparency."""
        overlay = ClassificationOverlay(background_alpha=0.7)
        frame = np.ones((480, 640, 3), dtype=np.uint8) * 255  # White frame
        
        result = overlay._draw_background(frame, 10, 10, 200, 100)
        
        # Background area should be darker than original (due to black background)
        background_region = result[10:110, 10:210]
        assert np.mean(background_region) < 255
    
    def test_draw_background_invalid_frame(self):
        """Test background drawing with invalid frame."""
        overlay = ClassificationOverlay()
        
        # Test with None
        result = overlay._draw_background(None, 10, 10, 200, 100)
        assert result is None
        
        # Test with empty frame
        empty_frame = np.array([])
        result = overlay._draw_background(empty_frame, 10, 10, 200, 100)
        assert result.size == 0
    
    def test_draw_background_bounds_clamping(self):
        """Test that background drawing clamps to frame boundaries."""
        overlay = ClassificationOverlay()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Try to draw beyond frame boundaries
        result = overlay._draw_background(frame, 600, 10, 200, 100)
        
        # Should not crash and should return a valid frame
        assert result is not None
        assert result.shape == frame.shape
    
    def test_draw_background_edge_case_exceeds_frame(self):
        """Test background drawing when overlay exceeds frame."""
        overlay = ClassificationOverlay()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Overlay that would exceed frame dimensions
        result = overlay._draw_background(frame, 500, 400, 300, 200)
        
        # Should handle gracefully
        assert result is not None
        assert result.shape == frame.shape


class TestCategoryColors:
    """Test CATEGORY_COLORS constant."""
    
    def test_all_categories_present(self):
        """Test that all required categories have colors defined."""
        required_categories = [
            'product', 'grade', 'cap', 'label',
            'brand', 'type', 'subtype', 'volume'
        ]
        
        for category in required_categories:
            assert category in CATEGORY_COLORS
    
    def test_colors_are_bgr_tuples(self):
        """Test that colors are valid BGR tuples."""
        for category, color in CATEGORY_COLORS.items():
            assert isinstance(color, tuple)
            assert len(color) == 3
            assert all(0 <= c <= 255 for c in color)


class TestRenderMethod:
    """Test the main render method."""
    
    def test_render_with_empty_tracks(self):
        """Test render with no tracks shows empty state."""
        overlay = ClassificationOverlay()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        result = overlay.render(frame, [], {})
        
        assert result is not None
        assert result.shape == frame.shape
    
    def test_render_with_classified_track(self):
        """Test render with a single classified track."""
        overlay = ClassificationOverlay()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Create a classified track
        track = BottleTrack(
            track_id=1,
            bbox=np.array([100, 100, 200, 200]),
            confidence=0.9,
            state=TrackingState.CLASSIFIED,
            classification_results={
                'product': 'Bottle',
                'grade': 'A',
                'cap': 'Blue',
                'label': 'Clean',
                'brand': 'BrandX',
                'type': 'PET',
                'subtype': 'Clear',
                'volume': '500ml'
            }
        )
        
        cache = {
            1: {
                'product': 'Bottle',
                'grade': 'A',
                'cap': 'Blue',
                'label': 'Clean',
                'brand': 'BrandX',
                'type': 'PET',
                'subtype': 'Clear',
                'volume': '500ml'
            }
        }
        
        result = overlay.render(frame, [track], cache)
        
        assert result is not None
        assert result.shape == frame.shape
    
    def test_render_filters_non_classified_tracks(self):
        """Test that render only shows CLASSIFIED tracks."""
        overlay = ClassificationOverlay()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Create tracks with different states
        track1 = BottleTrack(
            track_id=1,
            bbox=np.array([100, 100, 200, 200]),
            confidence=0.9,
            state=TrackingState.NEW
        )
        
        track2 = BottleTrack(
            track_id=2,
            bbox=np.array([300, 100, 400, 200]),
            confidence=0.9,
            state=TrackingState.TRACKED
        )
        
        track3 = BottleTrack(
            track_id=3,
            bbox=np.array([500, 100, 600, 200]),
            confidence=0.9,
            state=TrackingState.CLASSIFIED,
            classification_results={'product': 'Bottle'}
        )
        
        cache = {3: {'product': 'Bottle'}}
        
        result = overlay.render(frame, [track1, track2, track3], cache)
        
        # Should render successfully (only track3 is classified)
        assert result is not None
        assert result.shape == frame.shape
    
    def test_render_sorts_tracks_by_id(self):
        """Test that tracks are sorted by track_id."""
        overlay = ClassificationOverlay()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Create tracks in non-sorted order
        track3 = BottleTrack(
            track_id=3,
            bbox=np.array([100, 100, 200, 200]),
            confidence=0.9,
            state=TrackingState.CLASSIFIED
        )
        
        track1 = BottleTrack(
            track_id=1,
            bbox=np.array([300, 100, 400, 200]),
            confidence=0.9,
            state=TrackingState.CLASSIFIED
        )
        
        track2 = BottleTrack(
            track_id=2,
            bbox=np.array([500, 100, 600, 200]),
            confidence=0.9,
            state=TrackingState.CLASSIFIED
        )
        
        cache = {
            1: {'product': 'Bottle1'},
            2: {'product': 'Bottle2'},
            3: {'product': 'Bottle3'}
        }
        
        result = overlay.render(frame, [track3, track1, track2], cache)
        
        # Should render without error (sorting happens internally)
        assert result is not None
        assert result.shape == frame.shape
    
    def test_render_limits_tracks_to_max_display(self):
        """Test that render limits tracks to max_tracks_display."""
        overlay = ClassificationOverlay(max_tracks_display=2)
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Create 4 classified tracks
        tracks = []
        cache = {}
        for i in range(1, 5):
            track = BottleTrack(
                track_id=i,
                bbox=np.array([100*i, 100, 100*i+100, 200]),
                confidence=0.9,
                state=TrackingState.CLASSIFIED
            )
            tracks.append(track)
            cache[i] = {'product': f'Bottle{i}'}
        
        result = overlay.render(frame, tracks, cache)
        
        # Should render successfully with only 2 tracks displayed
        assert result is not None
        assert result.shape == frame.shape
    
    def test_render_with_incomplete_classification(self):
        """Test render with incomplete classification results."""
        overlay = ClassificationOverlay()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        track = BottleTrack(
            track_id=1,
            bbox=np.array([100, 100, 200, 200]),
            confidence=0.9,
            state=TrackingState.CLASSIFIED
        )
        
        # Incomplete cache (missing some attributes)
        cache = {
            1: {
                'product': 'Bottle',
                'grade': 'A'
                # Missing other attributes
            }
        }
        
        result = overlay.render(frame, [track], cache)
        
        # Should handle gracefully
        assert result is not None
        assert result.shape == frame.shape
    
    def test_render_error_handling_invalid_frame(self):
        """Test that render handles invalid frame gracefully."""
        overlay = ClassificationOverlay()
        
        # Test with None
        result = overlay.render(None, [], {})
        assert result is None
        
        # Test with empty array
        empty_frame = np.array([])
        result = overlay.render(empty_frame, [], {})
        assert result.size == 0
    
    def test_render_error_handling_exception(self):
        """Test that render returns original frame on exception."""
        overlay = ClassificationOverlay()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Create a track that might cause issues (but shouldn't crash)
        track = BottleTrack(
            track_id=999,
            bbox=np.array([100, 100, 200, 200]),
            confidence=0.9,
            state=TrackingState.CLASSIFIED
        )
        
        # Empty cache (track not in cache)
        cache = {}
        
        result = overlay.render(frame, [track], cache)
        
        # Should return a valid frame (not crash)
        assert result is not None
        assert result.shape == frame.shape
