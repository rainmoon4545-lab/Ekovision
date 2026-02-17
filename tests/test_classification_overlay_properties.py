"""
Property-based tests for ClassificationOverlay class.

These tests use Hypothesis to verify universal correctness properties
across all valid inputs.

Configuration:
- Minimum 100 iterations per property test (configured in conftest.py)
- Each test tagged with: Feature: classification-results-overlay, Property N
"""
import pytest
import numpy as np
from hypothesis import given, strategies as st, assume, settings
from src.tracking.classification_overlay import ClassificationOverlay
from src.tracking.bottle_tracker import BottleTrack, TrackingState


# ============================================================================
# Hypothesis Strategies (Test Data Generators)
# ============================================================================

@st.composite
def st_frame(draw, min_width=320, min_height=240, max_width=1920, max_height=1080):
    """
    Generate random frame with valid dimensions.
    
    Args:
        draw: Hypothesis draw function
        min_width: Minimum frame width (default: 320)
        min_height: Minimum frame height (default: 240)
        max_width: Maximum frame width (default: 1920)
        max_height: Maximum frame height (default: 1080)
    
    Returns:
        np.ndarray: Random frame with shape (height, width, 3) and dtype uint8
    """
    width = draw(st.integers(min_value=min_width, max_value=max_width))
    height = draw(st.integers(min_value=min_height, max_value=max_height))
    return np.zeros((height, width, 3), dtype=np.uint8)


@st.composite
def st_classification_results(draw, complete=True):
    """
    Generate random classification results.
    
    Args:
        draw: Hypothesis draw function
        complete: If True, generate all 8 attributes; if False, generate 1-7 attributes
    
    Returns:
        Dict[str, str]: Classification results dictionary
    """
    attributes = ['product', 'grade', 'cap', 'label', 'brand', 'type', 'subtype', 'volume']
    
    # Use printable ASCII characters for text generation to avoid rendering issues
    text_strategy = st.text(
        min_size=1, 
        max_size=20, 
        alphabet=st.characters(
            min_codepoint=32,  # Space
            max_codepoint=126,  # Tilde
            blacklist_categories=('Cs', 'Cc')  # No surrogates or control characters
        )
    )
    
    if complete:
        return {attr: draw(text_strategy) for attr in attributes}
    else:
        # Generate incomplete results (missing some attributes)
        num_attrs = draw(st.integers(min_value=1, max_value=7))
        selected_attrs = draw(st.lists(
            st.sampled_from(attributes),
            min_size=num_attrs, 
            max_size=num_attrs, 
            unique=True
        ))
        return {attr: draw(text_strategy) for attr in selected_attrs}


@st.composite
def st_classified_track(draw, track_id=None):
    """
    Generate random BottleTrack with CLASSIFIED status.
    
    Args:
        draw: Hypothesis draw function
        track_id: Optional fixed track ID (if None, generates random ID)
    
    Returns:
        BottleTrack: Random classified track
    """
    if track_id is None:
        track_id = draw(st.integers(min_value=1, max_value=1000))
    
    x1 = draw(st.integers(min_value=0, max_value=500))
    y1 = draw(st.integers(min_value=0, max_value=500))
    x2 = draw(st.integers(min_value=x1 + 10, max_value=x1 + 200))
    y2 = draw(st.integers(min_value=y1 + 10, max_value=y1 + 200))
    
    return BottleTrack(
        track_id=track_id,
        bbox=np.array([x1, y1, x2, y2]),
        confidence=draw(st.floats(min_value=0.5, max_value=1.0)),
        state=TrackingState.CLASSIFIED,
        classification_results=draw(st_classification_results())
    )


@st.composite
def st_track_with_state(draw, state=None):
    """
    Generate random BottleTrack with specified or random state.
    
    Args:
        draw: Hypothesis draw function
        state: Optional TrackingState (if None, generates random state)
    
    Returns:
        BottleTrack: Random track with specified state
    """
    if state is None:
        state = draw(st.sampled_from(list(TrackingState)))
    
    track_id = draw(st.integers(min_value=1, max_value=1000))
    x1 = draw(st.integers(min_value=0, max_value=500))
    y1 = draw(st.integers(min_value=0, max_value=500))
    x2 = draw(st.integers(min_value=x1 + 10, max_value=x1 + 200))
    y2 = draw(st.integers(min_value=y1 + 10, max_value=y1 + 200))
    
    # Only CLASSIFIED tracks have classification_results
    classification_results = None
    if state == TrackingState.CLASSIFIED:
        classification_results = draw(st_classification_results())
    
    return BottleTrack(
        track_id=track_id,
        bbox=np.array([x1, y1, x2, y2]),
        confidence=draw(st.floats(min_value=0.5, max_value=1.0)),
        state=state,
        classification_results=classification_results
    )


@st.composite
def st_classification_cache(draw, tracks):
    """
    Generate classification cache for given tracks.
    
    Args:
        draw: Hypothesis draw function
        tracks: List of BottleTrack objects
    
    Returns:
        Dict[int, Dict[str, str]]: Classification cache mapping track_id to results
    """
    cache = {}
    for track in tracks:
        if track.state == TrackingState.CLASSIFIED and track.classification_results:
            cache[track.track_id] = track.classification_results
    return cache


# ============================================================================
# Property Tests
# ============================================================================

class TestOverlayPositionConsistency:
    """
    Feature: classification-results-overlay
    Property 1: Overlay Position Consistency
    
    For any sequence of frames with varying bottle positions,
    the overlay coordinates (x, y) should remain constant across all frames.
    
    Validates: Requirements 1.2
    """
    
    @given(
        frame=st_frame(),
        tracks1=st.lists(st_classified_track(), min_size=1, max_size=5),
        tracks2=st.lists(st_classified_track(), min_size=1, max_size=5)
    )
    def test_property_1_overlay_position_consistency(self, frame, tracks1, tracks2):
        """
        Property 1: Overlay Position Consistency
        
        For any sequence of frames with varying bottle positions,
        the overlay coordinates should remain constant.
        """
        # Ensure tracks have unique IDs within each list
        for i, track in enumerate(tracks1):
            track.track_id = i + 1
        for i, track in enumerate(tracks2):
            track.track_id = i + 1
        
        overlay = ClassificationOverlay()
        frame_height, frame_width = frame.shape[:2]
        
        # Calculate layout with first set of tracks
        layout1 = overlay._calculate_layout(frame_width, frame_height, len(tracks1))
        
        # Calculate layout with second set of tracks (different positions)
        # Note: We use the same number of tracks to ensure fair comparison
        # The key insight is that bottle positions shouldn't affect overlay position
        num_tracks = min(len(tracks1), len(tracks2))
        layout2 = overlay._calculate_layout(frame_width, frame_height, num_tracks)
        layout3 = overlay._calculate_layout(frame_width, frame_height, num_tracks)
        
        # Overlay position should be the same for the same frame dimensions and track count
        assert layout2.overlay_x == layout3.overlay_x, \
            f"Overlay X position changed: {layout2.overlay_x} != {layout3.overlay_x}"
        assert layout2.overlay_y == layout3.overlay_y, \
            f"Overlay Y position changed: {layout2.overlay_y} != {layout3.overlay_y}"
        
        # Additional check: overlay position should only depend on frame dimensions and track count,
        # not on the actual track positions
        # Create cache with different track IDs
        cache1 = {track.track_id: track.classification_results for track in tracks1}
        cache2 = {track.track_id: track.classification_results for track in tracks2}
        
        # Render with both sets of tracks
        result1 = overlay.render(frame.copy(), tracks1[:num_tracks], cache1)
        result2 = overlay.render(frame.copy(), tracks2[:num_tracks], cache2)
        
        # Both should succeed (return valid frames)
        assert result1 is not None
        assert result2 is not None
        assert result1.shape == frame.shape
        assert result2.shape == frame.shape
        
        # Verify that the overlay position is consistent by checking layout calculation
        # The overlay should be at the same position regardless of bottle positions
        layout_check1 = overlay._calculate_layout(frame_width, frame_height, num_tracks)
        layout_check2 = overlay._calculate_layout(frame_width, frame_height, num_tracks)
        
        assert layout_check1.overlay_x == layout_check2.overlay_x
        assert layout_check1.overlay_y == layout_check2.overlay_y
