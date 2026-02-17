# Design Document: Classification Results Overlay

## Overview

Fitur ini menambahkan overlay permanen di bagian atas layar yang menampilkan hasil klasifikasi botol secara real-time. Overlay akan menampilkan ringkasan hasil klasifikasi dari semua botol yang sedang dilacak dan diklasifikasi, melengkapi label klasifikasi yang sudah ada (yang mengikuti setiap botol).

### Design Goals

1. **Non-intrusive**: Overlay tidak menghalangi area deteksi utama
2. **Performance**: Minimal impact pada FPS (< 5% overhead)
3. **Readability**: Informasi mudah dibaca dengan kontras yang baik
4. **Scalability**: Dapat menampilkan multiple tracks secara efisien
5. **Integration**: Seamless integration dengan rendering pipeline yang ada

### Key Design Decisions

1. **Rendering Order**: Overlay digambar terakhir (setelah semua elemen lain) untuk memastikan selalu terlihat
2. **Data Source**: Menggunakan cache klasifikasi yang sama dengan label per-botol untuk konsistensi
3. **Layout Strategy**: Multi-column layout untuk mengoptimalkan ruang layar
4. **Update Strategy**: Incremental updates hanya ketika ada perubahan klasifikasi

## Architecture

### Component Overview

```
DetectionTrackingPipeline
├── _render_frame (existing)
│   ├── Draw trigger zone
│   ├── Draw bounding boxes
│   ├── Draw per-bottle labels
│   └── Draw overlay (NEW)
│       └── ClassificationOverlay (NEW)
│           ├── _calculate_layout
│           ├── _draw_background
│           ├── _draw_track_results
│           └── _draw_empty_state
```

### New Component: ClassificationOverlay

Komponen baru yang bertanggung jawab untuk rendering overlay hasil klasifikasi.

**Responsibilities:**

- Calculate overlay dimensions and position
- Render semi-transparent background
- Display classification results for active tracks
- Handle empty state (no classifications)
- Manage multi-column layout

**Integration Point:**

- Called from `DetectionTrackingPipeline._render_frame()` setelah semua rendering lain selesai
- Receives: frame, list of tracks, classification cache
- Returns: frame with overlay drawn

## Components and Interfaces

### ClassificationOverlay Class

```python
class ClassificationOverlay:
    """
    Renders classification results overlay at the top of the frame.
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

    def _calculate_layout(
        self,
        frame_width: int,
        frame_height: int,
        num_tracks: int
    ) -> Dict[str, Any]:
        """
        Calculate overlay layout dimensions and positions.

        Args:
            frame_width: Frame width in pixels
            frame_height: Frame height in pixels
            num_tracks: Number of tracks to display

        Returns:
            Dictionary with layout information:
            {
                'overlay_x': int,
                'overlay_y': int,
                'overlay_width': int,
                'overlay_height': int,
                'num_columns': int,
                'column_width': int
            }
        """

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
```

### Integration with DetectionTrackingPipeline

Modifikasi pada `DetectionTrackingPipeline`:

```python
class DetectionTrackingPipeline:
    def __init__(self, ...):
        # ... existing initialization ...

        # NEW: Initialize overlay renderer
        self.overlay = ClassificationOverlay(
            position="top-center",
            background_alpha=0.7,
            font_scale=0.6,
            max_tracks_display=3
        )

    def _render_frame(self, frame, tracks, show_trigger_zone=True):
        # ... existing rendering code ...

        # NEW: Draw classification overlay (last step)
        annotated = self.overlay.render(
            annotated,
            tracks,
            self.cache
        )

        return annotated
```

## Data Models

### Layout Configuration

```python
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
```

### Overlay Configuration

```python
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
```

### Color Scheme (Reused from existing)

```python
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
```

## Correctness Properties

_A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees._

### Property 1: Overlay Position Consistency

_For any_ sequence of frames with varying bottle positions, the overlay coordinates (x, y) should remain constant across all frames.

**Validates: Requirements 1.2**

### Property 2: Classified Tracks Visibility

_For any_ track with status CLASSIFIED, that track's classification results should appear in the overlay rendering.

**Validates: Requirements 2.1**

### Property 3: Complete Attribute Rendering

_For any_ classified track, all 8 classification attributes (product, grade, cap, label, brand, type, subtype, volume) should be rendered in the overlay in the format "attribute_name: value".

**Validates: Requirements 2.2, 3.3**

### Property 4: Multiple Track Separation

_For any_ set of multiple classified tracks, each track's results should be rendered in a separate section within the overlay.

**Validates: Requirements 2.3**

### Property 5: Track ID Header Display

_For any_ classified track displayed in the overlay, the track ID should appear as a header at the top of that track's result section.

**Validates: Requirements 2.4, 4.3**

### Property 6: Color Scheme Consistency

_For any_ classification attribute rendered in the overlay, the color used should match the corresponding color in the CATEGORY_COLORS mapping.

**Validates: Requirements 3.1**

### Property 7: Text Background Rendering

_For any_ text element rendered in the overlay, a background rectangle should be drawn behind the text for contrast.

**Validates: Requirements 3.5**

### Property 8: Vertical Column Layout

_For any_ track's classification results, the attributes should be arranged vertically (increasing y-coordinate) within that track's column.

**Validates: Requirements 4.1**

### Property 9: Multi-Column Layout Activation

_For any_ frame with more than 2 classified tracks, the layout calculation should produce num_columns > 1.

**Validates: Requirements 4.2**

### Property 10: Track ID Sorting

_For any_ list of classified tracks to be displayed, the tracks should be sorted by track_id in ascending order before rendering.

**Validates: Requirements 4.4**

### Property 11: Track Display Limit

_For any_ list of classified tracks with count > max_tracks_display, only the first max_tracks_display tracks should be rendered, and a "+N more" indicator should be displayed.

**Validates: Requirements 4.5**

### Property 12: Minimum Overlay Height

_For any_ frame, the calculated overlay height should be >= min_overlay_height configuration value.

**Validates: Requirements 1.4**

### Property 13: Data Immutability

_For any_ input data (tracks list, classification cache), the data should remain unchanged after the overlay render operation completes.

**Validates: Requirements 6.5**

### Property 14: Incomplete Classification Handling

_For any_ classification result with fewer than 8 attributes, the missing attributes should be rendered with value "N/A".

**Validates: Requirements 7.2**

### Property 15: Coordinate Bounds Validation

_For any_ frame with dimensions (width, height), the calculated overlay coordinates should satisfy: 0 <= overlay_x < width and 0 <= overlay_y < height, and overlay_x + overlay_width <= width and overlay_y + overlay_height <= height.

**Validates: Requirements 7.4**

### Property 16: Dynamic Resolution Adaptation

_For any_ two frames with different resolutions, the overlay dimensions and position should be recalculated to fit each frame's dimensions appropriately.

**Validates: Requirements 7.5**

## Error Handling

### Exception Handling Strategy

1. **Graceful Degradation**: If overlay rendering fails, the frame should be returned without overlay rather than crashing
2. **Input Validation**: Validate frame dimensions, track data, and cache data before processing
3. **Bounds Checking**: Ensure all coordinates are within frame boundaries
4. **Logging**: Log errors for debugging without interrupting video processing

### Error Scenarios

#### Invalid Frame Dimensions

```python
def render(self, frame, tracks, cache):
    try:
        if frame is None or frame.size == 0:
            logger.warning("Invalid frame provided to overlay")
            return frame

        height, width = frame.shape[:2]
        if width <= 0 or height <= 0:
            logger.warning(f"Invalid frame dimensions: {width}x{height}")
            return frame

        # Continue with rendering...
    except Exception as e:
        logger.error(f"Error rendering overlay: {e}")
        return frame  # Return original frame
```

#### Missing Classification Data

```python
def _draw_track_results(self, frame, track, results, x, y, column_width):
    # Handle incomplete classification results
    expected_attributes = ['product', 'grade', 'cap', 'label',
                          'brand', 'type', 'subtype', 'volume']

    for attr in expected_attributes:
        value = results.get(attr, "N/A")
        # Render attribute with value or "N/A"
```

#### Coordinate Overflow

```python
def _calculate_layout(self, frame_width, frame_height, num_tracks):
    # Ensure overlay fits within frame
    overlay_width = min(calculated_width, frame_width - 2 * self.padding)
    overlay_height = min(calculated_height, frame_height // 2)

    # Ensure coordinates are within bounds
    overlay_x = max(0, min(overlay_x, frame_width - overlay_width))
    overlay_y = max(0, min(overlay_y, frame_height - overlay_height))

    return layout
```

### Error Recovery

- **Partial Rendering**: If one track fails to render, continue with remaining tracks
- **Fallback Layout**: If multi-column layout fails, fall back to single column
- **Cache Fallback**: If cache is unavailable, use track.classification_results directly

## Testing Strategy

### Dual Testing Approach

This feature requires both unit tests and property-based tests for comprehensive coverage:

- **Unit tests**: Verify specific examples, edge cases, and error conditions
- **Property tests**: Verify universal properties across all inputs

Together, these approaches provide comprehensive coverage where unit tests catch concrete bugs and property tests verify general correctness.

### Property-Based Testing

We will use **Hypothesis** (Python property-based testing library) to implement property tests.

**Configuration:**

- Minimum 100 iterations per property test
- Each test tagged with: `# Feature: classification-results-overlay, Property N: [property text]`
- Each correctness property implemented by a SINGLE property-based test

**Test Structure:**

```python
from hypothesis import given, strategies as st
import hypothesis.strategies as st

@given(
    frame=st_frame(),
    tracks=st.lists(st_classified_track(), min_size=1, max_size=10)
)
def test_property_1_overlay_position_consistency(frame, tracks):
    """
    Feature: classification-results-overlay
    Property 1: Overlay Position Consistency

    For any sequence of frames with varying bottle positions,
    the overlay coordinates should remain constant.
    """
    overlay = ClassificationOverlay()

    # Render with different track positions
    layout1 = overlay._calculate_layout(frame.shape[1], frame.shape[0], len(tracks))

    # Move tracks to different positions
    moved_tracks = [move_track(t) for t in tracks]
    layout2 = overlay._calculate_layout(frame.shape[1], frame.shape[0], len(moved_tracks))

    # Overlay position should be the same
    assert layout1['overlay_x'] == layout2['overlay_x']
    assert layout1['overlay_y'] == layout2['overlay_y']
```

### Unit Testing

**Focus Areas:**

1. Configuration validation
2. Empty state rendering
3. Integration with pipeline
4. Specific edge cases (e.g., exactly 3 tracks, exactly max_tracks_display + 1 tracks)
5. Error handling scenarios

**Example Unit Tests:**

```python
def test_empty_state_no_tracks():
    """Test overlay shows empty state when no tracks provided."""
    overlay = ClassificationOverlay()
    frame = np.zeros((480, 640, 3), dtype=np.uint8)

    result = overlay.render(frame, [], {})

    # Verify empty state message is rendered
    # (Check for specific text or verify _draw_empty_state was called)

def test_configuration_values():
    """Test overlay uses correct configuration values."""
    overlay = ClassificationOverlay(
        background_alpha=0.7,
        font_scale=0.6,
        margin_top=10
    )

    assert overlay.background_alpha == 0.7
    assert overlay.font_scale >= 0.6
    assert overlay.margin_top == 10

def test_integration_with_pipeline():
    """Test overlay integrates correctly with rendering pipeline."""
    pipeline = DetectionTrackingPipeline(...)
    frame = create_test_frame()

    # Verify overlay is initialized
    assert hasattr(pipeline, 'overlay')
    assert isinstance(pipeline.overlay, ClassificationOverlay)

    # Verify overlay.render is called in _render_frame
    # (Use mock or verify output contains overlay)
```

### Test Data Generators (Hypothesis Strategies)

```python
import hypothesis.strategies as st
from hypothesis import assume

@st.composite
def st_frame(draw, min_width=320, min_height=240, max_width=1920, max_height=1080):
    """Generate random frame with valid dimensions."""
    width = draw(st.integers(min_value=min_width, max_value=max_width))
    height = draw(st.integers(min_value=min_height, max_value=max_height))
    return np.zeros((height, width, 3), dtype=np.uint8)

@st.composite
def st_classification_results(draw, complete=True):
    """Generate random classification results."""
    attributes = ['product', 'grade', 'cap', 'label', 'brand', 'type', 'subtype', 'volume']

    if complete:
        return {attr: draw(st.text(min_size=1, max_size=20)) for attr in attributes}
    else:
        # Generate incomplete results (missing some attributes)
        num_attrs = draw(st.integers(min_value=1, max_value=7))
        selected_attrs = draw(st.lists(st.sampled_from(attributes),
                                      min_size=num_attrs, max_size=num_attrs, unique=True))
        return {attr: draw(st.text(min_size=1, max_size=20)) for attr in selected_attrs}

@st.composite
def st_classified_track(draw):
    """Generate random BottleTrack with CLASSIFIED status."""
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
```

### Integration Testing

1. **End-to-End Pipeline Test**: Verify overlay appears in final rendered frame
2. **Performance Test**: Measure FPS impact (should be < 5%)
3. **Visual Regression Test**: Compare rendered frames with expected outputs

### Test Coverage Goals

- **Line Coverage**: > 90% for ClassificationOverlay class
- **Branch Coverage**: > 85% for all conditional logic
- **Property Coverage**: 100% of correctness properties implemented as tests
