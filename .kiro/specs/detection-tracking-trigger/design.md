# Design Document: Detection-Tracking-Trigger Architecture

## Overview

This design document specifies the implementation of a Detection-Tracking-Trigger Architecture for the EkoVision PET Detection system. The architecture introduces three key optimizations:

1. **Continuous Detection**: YOLOv10m runs on every frame for fast bottle detection
2. **Object Tracking**: ByteTrack (pure Python) assigns persistent IDs to bottles across frames
3. **Trigger-Based Classification**: DINOv3 classification occurs only once per bottle when it enters a center trigger zone

The design reduces computational load by 80-90% while maintaining classification accuracy by processing each bottle exactly once at optimal position.

### Performance Benchmarking (CRITICAL - Pre-Implementation)

Before implementing the classification layer, performance benchmarking MUST be conducted to establish baselines and identify optimization needs:

**Benchmark Requirements**:

- Measure single classifier inference time on representative DINOv3 feature vectors
- Measure total time for all 314 classifiers running sequentially
- Test parallel inference using joblib.Parallel with various n_jobs values
- Document baseline metrics: single time, sequential time, parallel time, speedup factor
- Target: Total classification time <100ms for real-time performance

**Optimization Strategy** (if sequential exceeds 100ms):

- Implement parallel inference with joblib.Parallel
- Consider model pruning or feature selection
- Evaluate GPU batch processing for classifier inference
- Document chosen optimization approach and measured improvements

This benchmarking establishes whether the 314-classifier approach is viable for real-time operation and guides implementation decisions.

### Key Design Decisions

- **Pure Python ByteTrack**: Use pure Python implementation (boxmot/supervision) instead of pip package to avoid C++ compilation dependencies (cython-bbox, lap) that fail on Windows and non-standard environments
- **Center Trigger Zone**: Classification at frame center minimizes lens distortion and ensures consistent image quality
- **LRU Cache**: Least-recently-used eviction prevents memory growth during long sessions
- **Thread-Safe Design**: Maintains compatibility with Streamlit's async video processing
- **Classifier Warmup**: Run dummy prediction through all 314 classifiers during initialization to prevent 10-50x first-inference lag spike
- **Batch Processing**: When multiple bottles enter trigger zone simultaneously, batch process them in single GPU call to minimize transfer overhead
- **FAILED State**: Prevent infinite retry loops by limiting classification attempts (max 2) and marking failed bottles as FAILED
- **Camera Validation**: Validate camera settings by reading back values and provide fallback guidance for non-responsive cameras
- **torch.cuda VRAM Monitoring**: Use torch.cuda API (<1ms) instead of nvidia-smi subprocess (50-100ms) for real-time monitoring
- **100ms Classification Target**: Tighter performance target (down from 200ms) to ensure real-time operation with potential parallel inference

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                     Video Frame Input                        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Detection Layer (YOLOv10m)                      │
│  • Runs on every frame                                       │
│  • Returns bounding boxes + confidence scores                │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│           Tracking System (ByteTrack - Pure Python)          │
│  • Assigns unique Bottle_ID to each detection                │
│  • Maintains ID across frames                                │
│  • Handles occlusions (30 frame persistence)                 │
│  • Tracks classification attempts and FAILED state           │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Trigger Zone Evaluator                          │
│  • Checks if bottle center is in trigger zone                │
│  • Evaluates tracking state (NEW/TRACKED/CLASSIFIED/FAILED)  │
│  • Collects all bottles needing classification               │
└────────────────────────┬────────────────────────────────────┘
                         │
                    ┌────┴────┐
                    │         │
         Trigger?   │    No   │   Yes (Single or Multiple)
                    │         │
                    ▼         ▼
            ┌───────────┐  ┌──────────────────────┐
            │  Render   │  │ Classification Layer │
            │  Cached   │  │   (DINOv3 + MLs)     │
            │  Results  │  │  • Batch processing  │
            └─────┬─────┘  │  • Warmed classifiers│
                  │        └──────────┬───────────┘
                  │                   │
                  │                   ▼
                  │         ┌──────────────────┐
                  │         │  Result Cache    │
                  │         │  Store: ID→Dict  │
                  │         └──────────┬───────┘
                  │                    │
                  └────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              Visualization & Output                          │
│  • Draw bounding boxes with IDs                              │
│  • Display classification results                            │
│  • Show trigger zone overlay                                 │
│  • Display FAILED state with red color                       │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Frame Acquisition**: Video frame received from webcam or file
2. **Detection**: YOLO processes frame, returns all bottle detections
3. **Tracking**: ByteTrack matches detections to existing tracks, assigns IDs
4. **Trigger Evaluation**: For each tracked bottle:
   - Check if center point is in trigger zone
   - Check if tracking state is NEW (not CLASSIFIED or FAILED)
   - If both true, add to classification batch
5. **Classification** (conditional):
   - If multiple bottles need classification: batch process all in single GPU call
   - If single bottle needs classification: process individually (or batch of 1)
   - Extract crops, run DINOv3 (batched), run classifiers
   - Increment classification_attempts counter
   - If classification fails and max attempts reached: set state to FAILED
6. **Caching**: Store results with Bottle_ID
7. **Rendering**: Draw boxes, IDs, and results on frame (FAILED state shown in red)

## Components and Interfaces

### 1. TriggerZone Class

Manages the configurable region of interest where classification is triggered.

```python
class TriggerZone:
    """
    Defines and manages the trigger zone for classification.

    Attributes:
        frame_width: Width of the video frame in pixels
        frame_height: Height of the video frame in pixels
        x_offset_pct: Horizontal offset from center as percentage (0-50)
        y_offset_pct: Vertical offset from center as percentage (0-50)
        width_pct: Zone width as percentage of frame width (20-80)
        height_pct: Zone height as percentage of frame height (20-80)
    """

    def __init__(self, frame_width: int, frame_height: int,
                 x_offset_pct: float = 0.0, y_offset_pct: float = 0.0,
                 width_pct: float = 40.0, height_pct: float = 60.0):
        """Initialize trigger zone with frame dimensions and configuration."""
        pass

    def update_config(self, x_offset_pct: float, y_offset_pct: float,
                     width_pct: float, height_pct: float) -> None:
        """Update zone configuration and recalculate boundaries."""
        pass

    def get_boundaries(self) -> tuple[int, int, int, int]:
        """
        Calculate absolute pixel coordinates of trigger zone.

        Returns:
            (x_min, y_min, x_max, y_max) in pixel coordinates
        """
        pass

    def contains_point(self, x: float, y: float) -> bool:
        """
        Check if a point is within the trigger zone.

        Args:
            x: X coordinate in pixels
            y: Y coordinate in pixels

        Returns:
            True if point is inside zone, False otherwise
        """
        pass

    def draw_overlay(self, frame: np.ndarray, color: tuple = (0, 255, 255),
                    thickness: int = 2, alpha: float = 0.3) -> np.ndarray:
        """
        Draw trigger zone visualization on frame.

        Args:
            frame: Input frame (BGR format)
            color: Border color in BGR
            thickness: Border line thickness
            alpha: Transparency for filled overlay (0=transparent, 1=opaque)

        Returns:
            Frame with trigger zone overlay
        """
        pass
```

### 2. BottleTracker Class

Wraps ByteTrack algorithm and manages bottle tracking state.

```python
from dataclasses import dataclass
from enum import Enum

class TrackingState(Enum):
    """Enumeration of possible tracking states for a bottle."""
    NEW = "NEW"              # First detection, not yet classified
    TRACKED = "TRACKED"      # Being tracked, not in trigger zone yet
    CLASSIFIED = "CLASSIFIED"  # Classification completed
    FAILED = "FAILED"        # Classification failed after max retry attempts

@dataclass
class BottleTrack:
    """
    Represents a tracked bottle with its state and metadata.

    Attributes:
        track_id: Unique identifier for this bottle
        bbox: Bounding box as (x_min, y_min, x_max, y_max)
        confidence: Detection confidence score
        state: Current tracking state
        frames_since_update: Number of frames since last detection
        classification_results: Cached classification dict or None
        classification_attempts: Number of classification attempts made
    """
    track_id: int
    bbox: tuple[int, int, int, int]
    confidence: float
    state: TrackingState
    frames_since_update: int = 0
    classification_results: dict = None
    classification_attempts: int = 0

    def get_center(self) -> tuple[float, float]:
        """Calculate center point of bounding box."""
        x_min, y_min, x_max, y_max = self.bbox
        return ((x_min + x_max) / 2, (y_min + y_max) / 2)

class BottleTracker:
    """
    Manages bottle tracking using ByteTrack algorithm (pure Python implementation).

    Attributes:
        max_age: Maximum frames to keep track without detection (default 30)
        min_hits: Minimum detections before confirming track (default 1)
        iou_threshold: IoU threshold for matching detections (default 0.3)
        max_classification_attempts: Maximum classification retry attempts (default 2)

    Note: Uses pure Python ByteTrack implementation (from boxmot or supervision library)
    to avoid C++ compilation dependencies for better portability across platforms.
    """

    def __init__(self, max_age: int = 30, min_hits: int = 1,
                 iou_threshold: float = 0.3, max_classification_attempts: int = 2):
        """Initialize ByteTrack tracker with configuration."""
        pass

    def update(self, detections: list[tuple]) -> list[BottleTrack]:
        """
        Update tracker with new detections from current frame.

        Args:
            detections: List of (bbox, confidence) tuples from YOLO
                       bbox format: (x_min, y_min, x_max, y_max)

        Returns:
            List of BottleTrack objects for all active tracks
        """
        pass

    def get_track_by_id(self, track_id: int) -> BottleTrack | None:
        """Retrieve a specific track by its ID."""
        pass

    def remove_track(self, track_id: int) -> None:
        """Manually remove a track from active tracking."""
        pass

    def get_active_count(self) -> int:
        """Return number of currently active tracks."""
        pass

    def reset(self) -> None:
        """Clear all tracks and reset tracker state."""
        pass
```

### 3. ClassificationCache Class

Thread-safe LRU cache for storing classification results.

```python
from collections import OrderedDict
from threading import Lock

class ClassificationCache:
    """
    Thread-safe LRU cache for bottle classification results.

    Attributes:
        max_size: Maximum number of cached results (default 100)
        cache: OrderedDict mapping track_id to classification dict
        lock: Threading lock for concurrent access
        hit_count: Number of cache hits (for statistics)
        miss_count: Number of cache misses (for statistics)
    """

    def __init__(self, max_size: int = 100):
        """Initialize cache with maximum size."""
        self.max_size = max_size
        self.cache = OrderedDict()
        self.lock = Lock()
        self.hit_count = 0
        self.miss_count = 0

    def get(self, track_id: int) -> dict | None:
        """
        Retrieve cached classification results for a track.

        Args:
            track_id: Unique bottle identifier

        Returns:
            Classification dict if cached, None otherwise
        """
        pass

    def put(self, track_id: int, results: dict) -> None:
        """
        Store classification results for a track.

        Args:
            track_id: Unique bottle identifier
            results: Classification dict with 8 attributes
        """
        pass

    def remove(self, track_id: int) -> None:
        """Remove a specific track from cache."""
        pass

    def clear(self) -> None:
        """Clear all cached results."""
        pass

    def get_stats(self) -> dict:
        """
        Get cache statistics.

        Returns:
            Dict with keys: size, hit_count, miss_count, hit_rate
        """
        pass
```

### 4. DetectionTrackingPipeline Class

Main orchestrator that integrates all components.

```python
class DetectionTrackingPipeline:
    """
    Main pipeline orchestrating detection, tracking, and classification.

    Attributes:
        yolo_model: YOLOv10m detection model
        dinov3_processor: DINOv3 image processor
        dinov3_model: DINOv3 feature extraction model
        classifiers: List of 314 scikit-learn classifiers
        mlb: MultiLabelBinarizer for label encoding
        mapping_dict: Label mapping dictionary
        tracker: BottleTracker instance
        trigger_zone: TriggerZone instance
        cache: ClassificationCache instance
        confidence_threshold: Minimum confidence for detections
        device: torch.device for GPU/CPU
    """

    def __init__(self, yolo_model, dinov3_processor, dinov3_model,
                 classifiers, mlb, mapping_dict, device,
                 confidence_threshold: float = 0.25):
        """
        Initialize pipeline with all required models and components.

        Performs classifier warmup during initialization to prevent first-inference lag.
        """
        pass

    def process_frame(self, frame_bgr: np.ndarray) -> tuple[np.ndarray, dict]:
        """
        Process a single frame through the complete pipeline.

        Args:
            frame_bgr: Input frame in BGR format

        Returns:
            Tuple of (annotated_frame, statistics_dict)
            statistics_dict contains: active_tracks, classifications_triggered,
                                     cache_hits, fps
        """
        pass

    def _detect_bottles(self, frame_rgb: np.ndarray) -> list[tuple]:
        """
        Run YOLO detection on frame.

        Returns:
            List of (bbox, confidence) tuples
        """
        pass

    def _should_trigger_classification(self, track: BottleTrack) -> bool:
        """
        Determine if classification should be triggered for a track.

        Args:
            track: BottleTrack object

        Returns:
            True if classification should run, False otherwise
        """
        pass

    def _classify_bottle(self, frame_pil: Image, bbox: tuple) -> dict:
        """
        Run DINOv3 feature extraction and classification for a single bottle.

        Args:
            frame_pil: Frame as PIL Image (RGB)
            bbox: Bounding box (x_min, y_min, x_max, y_max)

        Returns:
            Classification dict with 8 attributes
        """
        pass

    def _classify_bottles_batch(self, frame_pil: Image, bboxes_list: list[tuple]) -> list[dict]:
        """
        Run DINOv3 feature extraction and classification for multiple bottles in batch.

        Batches all crops into a single tensor and sends to DINO in one GPU call
        to minimize GPU transfer overhead when multiple bottles enter trigger zone.

        Args:
            frame_pil: Frame as PIL Image (RGB)
            bboxes_list: List of bounding boxes [(x_min, y_min, x_max, y_max), ...]

        Returns:
            List of classification dicts with 8 attributes each
        """
        pass

    def _render_frame(self, frame: np.ndarray, tracks: list[BottleTrack],
                     show_trigger_zone: bool = True) -> np.ndarray:
        """
        Draw all visualizations on frame.

        Args:
            frame: Input frame (BGR)
            tracks: List of active BottleTrack objects
            show_trigger_zone: Whether to draw trigger zone overlay

        Returns:
            Annotated frame
        """
        pass

    def update_trigger_zone(self, x_offset_pct: float, y_offset_pct: float,
                           width_pct: float, height_pct: float) -> None:
        """Update trigger zone configuration."""
        pass

    def reset(self) -> None:
        """Reset all tracking state and cached results."""
        pass
```

### 5. StreamProcessor Integration

Modified Streamlit video processor that uses the new pipeline.

```python
class TrackingStreamProcessor(VideoProcessorBase):
    """
    Streamlit video processor using Detection-Tracking-Trigger pipeline.

    Attributes:
        pipeline: DetectionTrackingPipeline instance
        last_time: Timestamp of last processed frame
        min_interval: Minimum time between frames (for FPS limiting)
        frame_count: Total frames processed
        classification_count: Total classifications triggered
    """

    def __init__(self, pipeline: DetectionTrackingPipeline, fps_limit: int = 6):
        """Initialize processor with pipeline and FPS limit."""
        self.pipeline = pipeline
        self._last_time = 0.0
        self._min_interval = 1.0 / max(1, fps_limit)
        self.frame_count = 0
        self.classification_count = 0

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        """
        Process incoming video frame.

        Args:
            frame: Input video frame from streamlit-webrtc

        Returns:
            Annotated video frame
        """
        now = time.time()
        if now - self._last_time < self._min_interval:
            return frame
        self._last_time = now

        img_bgr = frame.to_ndarray(format="bgr24")
        out_bgr, stats = self.pipeline.process_frame(img_bgr)

        self.frame_count += 1
        self.classification_count += stats.get('classifications_triggered', 0)

        # Update predictions_store for UI display
        with predictions_lock:
            if stats.get('latest_classification'):
                predictions_store.appendleft({
                    "timestamp": datetime.now().isoformat(timespec="seconds"),
                    "pred": stats['latest_classification'],
                    "track_id": stats.get('track_id')
                })

        return av.VideoFrame.from_ndarray(out_bgr, format="bgr24")
```

### 6. CameraController Class

Manages camera configuration and applies settings to OpenCV VideoCapture.

```python
from dataclasses import dataclass
import cv2

@dataclass
class CameraPreset:
    """Predefined camera configuration preset."""
    name: str
    exposure: float      # Shutter speed in seconds (1/250 to 1/2000)
    brightness: int      # -50 to +50
    contrast: float      # 0.5 to 2.0
    auto_exposure: bool

class CameraController:
    """
    Manages camera configuration for optimal bottle detection.

    Attributes:
        cap: OpenCV VideoCapture instance
        exposure: Current shutter speed (1/250 to 1/2000 sec)
        brightness: Current brightness (-50 to +50)
        contrast: Current contrast (0.5 to 2.0)
        auto_exposure: Auto-exposure enabled flag
        presets: Dictionary of predefined camera presets
        supports_manual_control: Flag indicating if camera responds to programmatic control
    """

    PRESETS = {
        "Indoor": CameraPreset("Indoor", 1/500, 10, 1.2, False),
        "Outdoor": CameraPreset("Outdoor", 1/1000, -10, 1.0, False),
        "High Speed": CameraPreset("High Speed", 1/2000, 0, 1.5, False)
    }

    def __init__(self, video_capture: cv2.VideoCapture):
        """Initialize camera controller with VideoCapture instance."""
        pass

    def set_exposure(self, shutter_speed: float) -> bool:
        """
        Set manual exposure (shutter speed).

        Args:
            shutter_speed: Shutter speed in seconds (1/250 to 1/2000)

        Returns:
            True if successful, False otherwise
        """
        pass

    def set_brightness(self, brightness: int) -> bool:
        """
        Set brightness adjustment.

        Args:
            brightness: Brightness value (-50 to +50)

        Returns:
            True if successful, False otherwise
        """
        pass

    def set_contrast(self, contrast: float) -> bool:
        """
        Set contrast adjustment.

        Args:
            contrast: Contrast multiplier (0.5 to 2.0)

        Returns:
            True if successful, False otherwise
        """
        pass

    def set_auto_exposure(self, enabled: bool) -> bool:
        """
        Enable or disable auto-exposure.

        Args:
            enabled: True to enable auto-exposure, False for manual

        Returns:
            True if successful, False otherwise
        """
        pass

    def load_preset(self, preset_name: str) -> bool:
        """
        Load and apply a predefined camera preset.

        Args:
            preset_name: Name of preset ("Indoor", "Outdoor", "High Speed")

        Returns:
            True if successful, False otherwise
        """
        pass

    def get_current_settings(self) -> dict:
        """
        Get current camera settings.

        Returns:
            Dict with keys: exposure, brightness, contrast, auto_exposure
        """
        pass

    def validate_setting(self, property: int, expected_value: float) -> bool:
        """
        Validate that a camera setting was applied correctly.

        Args:
            property: OpenCV property constant (e.g., cv2.CAP_PROP_EXPOSURE)
            expected_value: Expected value after setting

        Returns:
            True if setting was applied correctly, False otherwise
        """
        pass

    def check_brightness_histogram(self, frame: np.ndarray) -> str:
        """
        Validate frame brightness using histogram analysis.

        Args:
            frame: Input frame (BGR format)

        Returns:
            "too_dark", "ok", or "too_bright"
        """
        pass
```

### 7. DataLogger Class

Handles background logging and export of detection/classification data.

```python
from threading import Thread, Lock
from queue import Queue
import csv
import json
from datetime import datetime

class DataLogger:
    """
    Background thread for logging detection and classification data.

    Attributes:
        log_queue: Thread-safe queue for log entries
        csv_data: List of detection records for CSV export
        json_data: Dictionary of classification history for JSON export
        performance_log: List of performance metrics over time
        is_recording: Video recording active flag
        video_writer: OpenCV VideoWriter for MP4 recording
        lock: Threading lock for data access
    """

    def __init__(self):
        """Initialize data logger with empty buffers."""
        self.log_queue = Queue()
        self.csv_data = []
        self.json_data = {}
        self.performance_log = []
        self.is_recording = False
        self.video_writer = None
        self.lock = Lock()
        self._thread = None
        self._running = False

    def start(self) -> None:
        """Start background logging thread."""
        pass

    def stop(self) -> None:
        """Stop background logging thread."""
        pass

    def log_detection(self, timestamp: str, track_id: int, bbox: tuple,
                     confidence: float, classification: dict, state: str) -> None:
        """
        Log a detection event.

        Args:
            timestamp: ISO format timestamp
            track_id: Bottle ID
            bbox: Bounding box (x_min, y_min, x_max, y_max)
            confidence: Detection confidence
            classification: Classification results dict (8 attributes)
            state: Tracking state (NEW, TRACKED, CLASSIFIED)
        """
        pass

    def log_performance(self, fps: float, classification_rate: float,
                       cache_hit_rate: float, active_tracks: int) -> None:
        """
        Log performance metrics.

        Args:
            fps: Current frames per second
            classification_rate: Classifications per second
            cache_hit_rate: Cache hit rate percentage
            active_tracks: Number of active tracked bottles
        """
        pass

    def start_recording(self, frame_width: int, frame_height: int,
                       fps: int = 30) -> bool:
        """
        Start video recording.

        Args:
            frame_width: Video frame width
            frame_height: Video frame height
            fps: Recording frame rate

        Returns:
            True if recording started, False otherwise
        """
        pass

    def stop_recording(self) -> str:
        """
        Stop video recording.

        Returns:
            Path to saved video file
        """
        pass

    def write_frame(self, frame: np.ndarray) -> None:
        """Write frame to video file if recording is active."""
        pass

    def export_csv(self) -> str:
        """
        Export detection data to CSV file.

        Returns:
            Path to generated CSV file
        """
        pass

    def export_json(self) -> str:
        """
        Export classification history to JSON file.

        Returns:
            Path to generated JSON file
        """
        pass

    def generate_session_summary(self) -> dict:
        """
        Generate session summary report.

        Returns:
            Dict with keys: total_bottles, total_classifications,
                          average_fps, cache_stats
        """
        pass

    def _generate_filename(self, extension: str) -> str:
        """
        Generate timestamped filename.

        Args:
            extension: File extension (e.g., "csv", "json", "mp4")

        Returns:
            Filename in format: ekovision_YYYY-MM-DD_HH-MM-SS.ext
        """
        pass
```

### 8. PerformanceMonitor Class

Tracks and displays real-time system performance metrics.

```python
import psutil
import torch
from collections import deque

class PerformanceMonitor:
    """
    Monitors system performance metrics in real-time.

    Attributes:
        fps_history: Deque of FPS values over last 60 seconds
        gpu_available: Flag indicating GPU availability
        device: torch.device for GPU/CPU
        frame_times: Dict tracking processing time breakdown
        warning_thresholds: Dict of warning threshold values
    """

    def __init__(self, device: torch.device):
        """Initialize performance monitor."""
        self.device = device
        self.gpu_available = torch.cuda.is_available()
        self.fps_history = deque(maxlen=60)
        self.frame_times = {
            'detection': 0.0,
            'tracking': 0.0,
            'classification': 0.0,
            'rendering': 0.0
        }
        self.warning_thresholds = {
            'fps_min': 10,
            'gpu_usage_max': 95,
            'vram_usage_max': 90
        }

    def update_fps(self, fps: float) -> None:
        """Add FPS measurement to history."""
        pass

    def get_cpu_usage(self) -> float:
        """
        Get current CPU usage percentage.

        Returns:
            CPU usage as percentage (0-100)
        """
        pass

    def get_gpu_usage(self) -> float:
        """
        Get current GPU usage percentage.

        Returns:
            GPU usage as percentage (0-100), or 0 if no GPU
        """
        pass

    def get_vram_usage(self) -> tuple[float, float]:
        """
        Get current VRAM usage using torch.cuda API for instant monitoring.

        Uses torch.cuda.memory_allocated() and torch.cuda.get_device_properties()
        for <1ms overhead instead of 50-100ms nvidia-smi subprocess overhead.

        Returns:
            Tuple of (used_gb, total_gb), or (0.0, 0.0) if CUDA not available
        """
        pass

    def update_frame_times(self, detection_time: float, tracking_time: float,
                          classification_time: float, rendering_time: float) -> None:
        """Update frame processing time breakdown."""
        pass

    def get_frame_times(self) -> dict:
        """
        Get frame processing time breakdown.

        Returns:
            Dict with keys: detection_time, tracking_time,
                          classification_time, rendering_time (in ms)
        """
        pass

    def calculate_reduction_percentage(self, legacy_fps: float,
                                      tracking_fps: float) -> float:
        """
        Calculate computational reduction percentage.

        Args:
            legacy_fps: FPS in legacy mode
            tracking_fps: FPS in tracking mode

        Returns:
            Reduction percentage (0-100)
        """
        pass

    def get_warnings(self) -> list[str]:
        """
        Get list of active performance warnings.

        Returns:
            List of warning messages
        """
        pass

    def get_fps_graph_data(self) -> list[float]:
        """
        Get FPS history for graphing.

        Returns:
            List of FPS values over last 60 seconds
        """
        pass
```

### 9. TestingModeManager Class

Manages specialized testing modes for field validation.

```python
from enum import Enum

class TestingMode(Enum):
    """Enumeration of testing modes."""
    NORMAL = "Normal"
    STATIC_TEST = "Static Test"
    LOW_SPEED_TEST = "Low-Speed Test"
    STRESS_TEST = "Stress Test"

class TestingModeManager:
    """
    Manages testing modes and mode-specific metrics.

    Attributes:
        current_mode: Active testing mode
        static_test_metrics: Position stability tracking
        low_speed_metrics: Tracking continuity tracking
        stress_test_metrics: Maximum concurrent bottles tracking
    """

    def __init__(self):
        """Initialize testing mode manager."""
        self.current_mode = TestingMode.NORMAL
        self.static_test_metrics = {
            'position_variance': 0.0,
            'movement_detected': False
        }
        self.low_speed_metrics = {
            'id_swaps': 0,
            'tracking_breaks': 0
        }
        self.stress_test_metrics = {
            'max_concurrent_bottles': 0,
            'capacity_exceeded': False
        }

    def set_mode(self, mode: TestingMode) -> None:
        """Set active testing mode and reset metrics."""
        pass

    def get_mode(self) -> TestingMode:
        """Get current testing mode."""
        pass

    def update_static_test(self, tracks: list) -> None:
        """
        Update static test metrics.

        Args:
            tracks: List of BottleTrack objects
        """
        pass

    def update_low_speed_test(self, tracks: list, prev_tracks: list) -> None:
        """
        Update low-speed test metrics.

        Args:
            tracks: Current frame tracks
            prev_tracks: Previous frame tracks
        """
        pass

    def update_stress_test(self, active_count: int) -> None:
        """
        Update stress test metrics.

        Args:
            active_count: Number of active tracked bottles
        """
        pass

    def get_metrics(self) -> dict:
        """
        Get metrics for current testing mode.

        Returns:
            Dict of mode-specific metrics
        """
        pass

    def get_warnings(self) -> list[str]:
        """
        Get warnings for current testing mode.

        Returns:
            List of warning messages
        """
        pass
```

## Data Models

### Detection Data

```python
# YOLO detection output format
Detection = tuple[
    tuple[int, int, int, int],  # bbox: (x_min, y_min, x_max, y_max)
    float                        # confidence: 0.0 to 1.0
]
```

### Track Data

```python
# Complete track information
@dataclass
class BottleTrack:
    track_id: int                      # Unique identifier (e.g., 101, 102)
    bbox: tuple[int, int, int, int]    # Current bounding box
    confidence: float                   # Detection confidence
    state: TrackingState                # NEW, TRACKED, or CLASSIFIED
    frames_since_update: int            # Frames without detection
    classification_results: dict | None # Cached results or None
```

### Classification Results

```python
# Classification output format (unchanged from current system)
ClassificationResults = dict[str, str]
# Example:
# {
#     "product": "Bottle",
#     "grade": "Grade A",
#     "cap": "Blue Cap",
#     "label": "Full Label",
#     "brand": "Brand X",
#     "type": "PET",
#     "subtype": "Clear",
#     "volume": "500ml (85.2%)"  # May include fallback percentage
# }
```

### Pipeline Statistics

```python
# Statistics returned by process_frame
PipelineStats = dict[str, Any]
# Example:
# {
#     "active_tracks": 3,
#     "classifications_triggered": 1,
#     "cache_hits": 2,
#     "fps": 12.5,
#     "latest_classification": {...},  # If classification occurred
#     "track_id": 101                  # ID of classified bottle
# }
```

### Camera Settings

```python
# Camera configuration data
CameraSettings = dict[str, Any]
# Example:
# {
#     "exposure": 1/1000,      # Shutter speed in seconds
#     "brightness": 10,        # -50 to +50
#     "contrast": 1.2,         # 0.5 to 2.0
#     "auto_exposure": False   # Auto-exposure enabled
# }
```

### Detection Log Entry

```python
# Single detection log entry for CSV export
DetectionLogEntry = dict[str, Any]
# Example:
# {
#     "timestamp": "2026-02-12T14:30:00",
#     "track_id": 101,
#     "bbox": "(100, 200, 300, 400)",
#     "confidence": 0.95,
#     "product": "Bottle",
#     "grade": "Grade A",
#     "cap": "Blue Cap",
#     "label": "Full Label",
#     "brand": "Brand X",
#     "type": "PET",
#     "subtype": "Clear",
#     "volume": "500ml",
#     "tracking_state": "CLASSIFIED"
# }
```

### Performance Metrics

```python
# Real-time performance metrics
PerformanceMetrics = dict[str, Any]
# Example:
# {
#     "cpu_usage": 45.2,           # Percentage
#     "gpu_usage": 78.5,           # Percentage
#     "vram_used": 4.2,            # GB
#     "vram_total": 8.0,           # GB
#     "detection_time": 15.3,      # ms
#     "tracking_time": 2.1,        # ms
#     "classification_time": 45.7, # ms
#     "rendering_time": 8.2,       # ms
#     "reduction_percentage": 87.3 # Percentage
# }
```

### Testing Mode Metrics

```python
# Testing mode specific metrics
TestingModeMetrics = dict[str, Any]
# Static Test Example:
# {
#     "position_variance": 2.3,    # Pixels
#     "movement_detected": False
# }
# Low-Speed Test Example:
# {
#     "id_swaps": 0,
#     "tracking_breaks": 1
# }
# Stress Test Example:
# {
#     "max_concurrent_bottles": 18,
#     "capacity_exceeded": False
# }
```

## Correctness Properties

_A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees._

### Property 1: Detection respects confidence threshold

_For any_ frame containing multiple bottle detections with varying confidence scores, all returned detections should have confidence scores greater than or equal to the configured threshold, and no detections below the threshold should be returned.

**Validates: Requirements 1.3, 1.4**

### Property 2: Unique ID assignment for new detections

_For any_ frame with new bottle detections, each detection should receive a unique Bottle_ID that is distinct from all other currently active track IDs.

**Validates: Requirements 2.1, 2.6**

### Property 3: ID persistence across frames

_For any_ bottle that appears in consecutive frames with overlapping bounding boxes, the Bottle_ID should remain constant across those frames (invariant property).

**Validates: Requirements 2.2**

### Property 4: ID lifecycle with occlusion handling

_For any_ tracked bottle, if it disappears from detections for N frames then reappears, the Bottle_ID should be preserved if N ≤ 30 frames, and should be removed if N > 30 frames.

**Validates: Requirements 2.3, 2.4**

### Property 5: Trigger zone configuration updates boundaries

_For any_ valid trigger zone configuration (x_offset, y_offset, width, height as percentages), updating the configuration should result in new boundary coordinates that correctly reflect the percentage-based positioning within the frame dimensions.

**Validates: Requirements 3.2**

### Property 6: Point-in-zone detection

_For any_ bounding box and trigger zone, the zone membership check should return true if and only if the center point of the bounding box falls within the zone boundaries.

**Validates: Requirements 4.3**

### Property 7: Classification triggers only for NEW bottles in zone

_For any_ tracked bottle, classification should be triggered if and only if the bottle's tracking state is NEW and its center point is within the trigger zone boundaries.

**Validates: Requirements 4.1, 4.2, 8.3**

### Property 8: State transition after classification

_For any_ bottle that undergoes classification, its tracking state should transition from NEW to CLASSIFIED after the classification completes.

**Validates: Requirements 4.5**

### Property 9: Classification output format

_For any_ bottle that is classified, the classification results should be a dictionary containing exactly 8 keys: product, grade, cap, label, brand, type, subtype, and volume, with string values for each key.

**Validates: Requirements 5.2, 5.4**

### Property 10: Classification format consistency with legacy system

_For any_ bottle classification, the output format and fallback/conflict resolution logic should produce results identical to the legacy per-frame processing system when given the same input crop.

**Validates: Requirements 5.3**

### Property 11: Cache stores classification results

_For any_ bottle that is classified, immediately after classification the Result_Cache should contain an entry mapping the Bottle_ID to the classification results dictionary.

**Validates: Requirements 6.1**

### Property 12: Cache retrieval for tracked bottles

_For any_ Bottle_ID that has cached classification results, retrieving from the cache should return the same classification dictionary that was originally stored.

**Validates: Requirements 6.2**

### Property 13: Cache cleanup on track removal

_For any_ Bottle_ID that is removed from active tracking, the corresponding entry should also be removed from the Result_Cache.

**Validates: Requirements 6.3**

### Property 14: LRU cache eviction

_For any_ sequence of cache insertions that exceeds the maximum cache size (100 entries), the least recently used entry should be evicted to maintain the size limit.

**Validates: Requirements 6.5, 11.1**

### Property 15: Maximum tracked bottles limit

_For any_ frame with more than 20 detected bottles, the tracking system should maintain at most 20 active tracks.

**Validates: Requirements 11.3**

### Property 16: Confidence-based prioritization at capacity

_For any_ frame with more than 20 detected bottles, the 20 bottles with the highest confidence scores should be tracked, and lower confidence detections should be dropped.

**Validates: Requirements 11.4**

### Property 17: Error recovery during classification

_For any_ classification operation that encounters an error during feature extraction, the system should mark the bottle's classification results as containing "UNKNOWN" values and continue tracking without crashing.

**Validates: Requirements 12.2**

### Property 18: Invalid configuration handling

_For any_ trigger zone configuration where dimensions would exceed frame boundaries (e.g., width > 100% or negative offsets), the system should reject the configuration and reset to default values.

**Validates: Requirements 12.5**

### Property 19: Pipeline statistics completeness

_For any_ processed frame, the returned statistics dictionary should contain keys for: active_tracks, classifications_triggered, cache_hits, and fps.

**Validates: Requirements 13.3**

### Property 20: Predictions store update

_For any_ frame where classification is triggered, the predictions_store deque should be updated with a new entry containing the classification results and timestamp.

**Validates: Requirements 9.3**

### Property 21: Configuration changes apply immediately

_For any_ trigger zone configuration update, the next processed frame should use the new configuration values without requiring system restart.

**Validates: Requirements 10.5**

### Property 22: Legacy mode processes every frame

_For any_ sequence of frames processed in Legacy Mode, classification should be triggered for every frame that contains a detected bottle, regardless of tracking state or trigger zone position.

**Validates: Requirements 14.2**

### Property 23: Mode switching clears state

_For any_ mode switch between Tracking Mode and Legacy Mode, all tracking state and cached classification results should be cleared before processing the next frame.

**Validates: Requirements 14.3**

### Property 24: Camera settings apply in real-time

_For any_ valid camera setting change (exposure, brightness, contrast, auto-exposure), the new settings should be applied to the next processed frame without requiring system restart.

**Validates: Requirements 15.6**

### Property 25: CSV export contains required columns

_For any_ set of logged detections, the exported CSV file should contain columns for: timestamp, track_id, bbox, confidence, all 8 classification attributes (product, grade, cap, label, brand, type, subtype, volume), and tracking_state.

**Validates: Requirements 16.1**

### Property 26: JSON export contains classification history

_For any_ classification history with tracked bottles, the exported JSON file should contain entries for all tracked bottles with their complete classification results.

**Validates: Requirements 16.3**

### Property 27: Performance metrics logging completeness

_For any_ processed frame, the performance log entry should contain: FPS, classification_rate, cache_hit_rate, and active_tracks.

**Validates: Requirements 16.4**

### Property 28: Session summary completeness

_For any_ completed session, the generated summary report should contain: total_bottles_detected, total_classifications, average_fps, and cache_statistics.

**Validates: Requirements 16.5**

### Property 29: Export filename format

_For any_ file export operation (CSV, JSON, MP4), the generated filename should match the format "ekovision_YYYY-MM-DD_HH-MM-SS.{extension}" where the timestamp reflects the export time.

**Validates: Requirements 16.7**

### Property 30: Static test movement detection

_For any_ bottle in Static Test Mode, if the bottle's position changes by more than a threshold distance between consecutive frames, a movement warning should be generated.

**Validates: Requirements 18.3**

### Property 31: Low-speed test ID swap detection

_For any_ sequence of frames in Low-Speed Test Mode, if a bottle's bounding box is matched to a different track_id than in the previous frame (ID swap), a warning should be generated.

**Validates: Requirements 18.5**

### Property 32: Stress test capacity warning

_For any_ frame in Stress Test Mode where the number of active tracks exceeds 20, a capacity exceeded warning should be generated.

**Validates: Requirements 18.7**

### Property 33: Classifier warmup prevents first-inference lag

_For any_ system initialization, after warmup completes, the first real classification should have similar inference time to subsequent classifications (no 10-50x slowdown).

**Validates: Requirements 5.7**

### Property 34: Batch processing correctness

_For any_ set of bottles classified in batch, each bottle's classification results should be identical to what would be obtained by classifying that bottle individually.

**Validates: Requirements 5.6**

### Property 35: FAILED state prevents infinite retries

_For any_ bottle that fails classification and reaches maximum retry attempts, the bottle's state should transition to FAILED and no further classification attempts should be made for that bottle.

**Validates: Requirements 4.3, 4.7**

### Property 36: Camera validation detects non-responsive cameras

_For any_ camera setting change, if the camera does not respond correctly (verified by reading back the value), a warning should be generated indicating manual configuration is needed.

**Validates: Requirements 15.10, 15.11**

### Property 37: VRAM monitoring uses torch.cuda API

_For any_ VRAM usage query, the monitoring system should use torch.cuda API and complete in <1ms, not nvidia-smi subprocess (50-100ms overhead).

**Validates: Requirements 17.3**

## Error Handling

### Detection Layer Errors

**YOLO Model Failure**:

- If YOLO model fails to load: Log error, display message in UI, prevent video processing
- If YOLO inference fails on a frame: Log warning, return empty detection list, continue with next frame
- If confidence threshold is invalid: Clamp to valid range [0.0, 1.0], log warning

**Detection Format Errors**:

- If bounding box coordinates are invalid (negative, out of bounds): Skip detection, log warning
- If confidence score is NaN or infinite: Skip detection, log warning

### Tracking System Errors

**ByteTrack Initialization Failure**:

- If ByteTrack fails to initialize: Fall back to simple IoU matching, log error
- If max_age or iou_threshold are invalid: Use default values, log warning

**Track Update Errors**:

- If track update fails: Log error, continue with existing tracks
- If track ID assignment fails: Skip that detection, continue with others
- If track count exceeds maximum (20): Drop lowest confidence tracks, log warning

**State Management Errors**:

- If track state becomes corrupted: Reset track to NEW state, log error
- If track bbox becomes invalid: Remove track, log warning

### Classification Layer Errors

**DINOv3 Errors**:

- If feature extraction fails: Return UNKNOWN for all attributes, log error, continue tracking
- If image crop is invalid (zero size, negative dimensions): Skip classification, log error
- If GPU memory exhausted during inference: Fall back to CPU, log warning

**Classifier Errors**:

- If individual classifier fails: Use "UNKNOWN" for that attribute, continue with others
- If all classifiers fail: Return dict with all "UNKNOWN" values, log error
- If probability computation fails: Use fallback logic with 0.0 probabilities

**Label Mapping Errors**:

- If mapping_dict is missing a category: Use "UNKNOWN" for that category, log error
- If label is not in mapping: Use raw label value, log warning

### Cache Errors

**Memory Errors**:

- If cache insertion fails due to memory: Clear cache, log error, continue
- If cache exceeds size limit: Evict LRU entries until under limit
- If cache retrieval fails: Treat as cache miss, log warning

**Concurrency Errors**:

- If lock acquisition times out: Skip cache operation, log warning
- If cache becomes corrupted: Clear cache, reinitialize, log error

### Trigger Zone Errors

**Configuration Errors**:

- If zone dimensions exceed frame size: Reset to default (40% x 60%), log warning
- If zone offsets are negative: Clamp to 0%, log warning
- If zone offsets push zone out of frame: Adjust to keep zone in bounds, log warning

**Boundary Calculation Errors**:

- If frame dimensions are zero or negative: Use default 640x480, log error
- If boundary calculation produces invalid coordinates: Use full frame as zone, log error

### Frame Processing Errors

**Input Errors**:

- If frame is None or empty: Skip frame, log warning
- If frame format is unsupported: Attempt conversion, log warning if fails
- If frame dimensions change mid-stream: Reinitialize trigger zone, log info

**Pipeline Errors**:

- If entire pipeline fails: Log error, return original frame unmodified
- If rendering fails: Return frame with detections but no annotations, log error

**Thread Safety Errors**:

- If predictions_store lock times out: Skip store update, log warning
- If concurrent access causes corruption: Clear store, reinitialize, log error

### Camera Controller Errors

**Configuration Errors**:

- If exposure value is out of range (not 1/250 to 1/2000): Clamp to valid range, log warning
- If brightness value is out of range (not -50 to +50): Clamp to valid range, log warning
- If contrast value is out of range (not 0.5 to 2.0): Clamp to valid range, log warning
- If camera doesn't support manual exposure: Disable manual control, log warning

**Hardware Errors**:

- If camera connection is lost: Display error in UI, stop processing
- If camera settings fail to apply: Retry once, log error if still fails
- If preset loading fails: Keep current settings, log error

### Data Logger Errors

**File I/O Errors**:

- If CSV export fails: Log error, display message in UI
- If JSON export fails: Log error, display message in UI
- If video recording fails to start: Display error, disable recording
- If disk space is insufficient: Stop recording, log error, display warning

**Threading Errors**:

- If log queue becomes full: Drop oldest entries, log warning
- If background thread crashes: Restart thread, log error
- If data corruption detected: Clear corrupted data, log error

**Export Errors**:

- If filename generation fails: Use fallback name with UUID, log warning
- If file already exists: Append counter to filename (e.g., "\_1", "\_2")

### Performance Monitor Errors

**Metric Collection Errors**:

- If GPU metrics unavailable: Display "N/A", continue with CPU metrics
- If psutil fails to get CPU usage: Display last known value, log warning
- If VRAM query fails: Display "Unknown", log warning

**Graph Rendering Errors**:

- If FPS history is empty: Display empty graph with message
- If graph rendering fails: Skip graph, log error

### Testing Mode Errors

**Mode Switching Errors**:

- If mode switch fails: Keep current mode, log error
- If metrics reset fails: Clear metrics manually, log warning

**Metric Calculation Errors**:

- If position variance calculation fails: Use 0.0, log warning
- If ID swap detection fails: Skip detection for that frame, log warning
- If concurrent bottle count is invalid: Use last known value, log warning

### Recovery Strategies

**Graceful Degradation**:

1. Classification error → Continue tracking with UNKNOWN labels
2. Tracking error → Fall back to per-frame detection without IDs
3. GPU error → Fall back to CPU processing
4. Cache error → Clear cache and continue without caching
5. Camera error → Use default settings and continue
6. Logging error → Continue processing without logging
7. Performance monitoring error → Continue without metrics display

**State Reset**:

- Provide "Reset System" button in UI to clear all state
- Automatically reset on mode switch
- Reset on configuration validation failure
- Reset data logger on export errors

**Error Reporting**:

- Log all errors with timestamp and context
- Display critical errors in Streamlit UI
- Maintain error counter in statistics
- Include error summary in session report

## Testing Strategy

### Dual Testing Approach

The testing strategy employs both unit tests and property-based tests to ensure comprehensive coverage:

**Unit Tests**: Focus on specific examples, edge cases, and integration points

- Specific configuration values (default trigger zone dimensions)
- Edge cases (empty frames, single bottle, maximum bottles)
- Error conditions (invalid configurations, classification failures)
- Integration with Streamlit components

**Property-Based Tests**: Verify universal properties across all inputs

- Run minimum 100 iterations per property test
- Use randomized inputs (frame dimensions, bottle positions, confidence scores)
- Test invariants (ID persistence, cache consistency)
- Test state transitions (NEW → CLASSIFIED)

### Property-Based Testing Configuration

**Framework**: Use `hypothesis` library for Python property-based testing

**Test Configuration**:

```python
from hypothesis import given, settings, strategies as st

@settings(max_examples=100, deadline=None)
@given(
    frame_width=st.integers(min_value=320, max_value=1920),
    frame_height=st.integers(min_value=240, max_value=1080),
    num_bottles=st.integers(min_value=0, max_value=25),
    confidence_threshold=st.floats(min_value=0.0, max_value=1.0)
)
def test_property_X(...):
    # Feature: detection-tracking-trigger, Property X: <property text>
    pass
```

**Tag Format**: Each property test must include a comment:

```python
# Feature: detection-tracking-trigger, Property 1: Detection respects confidence threshold
```

### Test Categories

#### 0. Performance Benchmarking Tests (Pre-Implementation)

**Unit Tests**:

- Test benchmark script with mock classifiers
- Test parallel inference configuration
- Test performance metric calculation

**Benchmark Execution**:

- Run with real 314 classifiers on representative features
- Measure and document baseline performance
- Identify optimization needs before implementation

#### 1. Detection Layer Tests

**Unit Tests**:

- Test with empty frame (no detections)
- Test with single bottle at various confidence levels
- Test with multiple bottles above and below threshold
- Test GPU vs CPU detection consistency

**Property Tests**:

- Property 1: Confidence threshold filtering (100+ random frames)

#### 2. Tracking System Tests

**Unit Tests**:

- Test first detection assigns ID
- Test ID persistence with slight movement
- Test ID removal after 31 frames
- Test maximum 20 tracks limit

**Property Tests**:

- Property 2: Unique ID assignment (100+ random detection sets)
- Property 3: ID persistence across frames (100+ movement sequences)
- Property 4: ID lifecycle with occlusion (100+ occlusion scenarios)
- Property 15: Maximum tracked bottles limit (100+ crowded frames)
- Property 16: Confidence-based prioritization (100+ capacity scenarios)

#### 3. Trigger Zone Tests

**Unit Tests**:

- Test default configuration (40% x 60%, centered)
- Test zone at frame corners
- Test zone with maximum dimensions (80% x 80%)
- Test invalid configurations (negative, >100%)

**Property Tests**:

- Property 5: Configuration updates boundaries (100+ random configs)
- Property 6: Point-in-zone detection (100+ random points and zones)
- Property 18: Invalid configuration handling (100+ invalid configs)
- Property 21: Configuration changes apply immediately (100+ config sequences)

#### 4. Classification Trigger Tests

**Unit Tests**:

- Test NEW bottle in zone triggers classification
- Test CLASSIFIED bottle in zone does not trigger
- Test NEW bottle outside zone does not trigger
- Test state transition after classification

**Property Tests**:

- Property 7: Classification triggers only for NEW bottles in zone (100+ scenarios)
- Property 8: State transition after classification (100+ classifications)

#### 5. Classification Layer Tests

**Unit Tests**:

- Test classification returns 8 attributes
- Test fallback logic with low confidence
- Test conflict resolution with multiple predictions
- Test error handling (invalid crop, model failure)
- Test classifier warmup during initialization
- Test batch processing with multiple bottles
- Test FAILED state after max retry attempts

**Property Tests**:

- Property 9: Classification output format (100+ random crops)
- Property 10: Format consistency with legacy system (100+ comparisons)
- Property 17: Error recovery during classification (100+ error scenarios)
- Property 33: Classifier warmup prevents first-inference lag (100+ warmup tests)
- Property 34: Batch processing correctness (100+ batch scenarios)
- Property 35: FAILED state prevents infinite retries (100+ failure scenarios)

#### 6. Cache Tests

**Unit Tests**:

- Test cache stores and retrieves results
- Test cache miss returns None
- Test cache eviction at 101 entries
- Test cache cleanup on track removal

**Property Tests**:

- Property 11: Cache stores classification results (100+ store operations)
- Property 12: Cache retrieval for tracked bottles (100+ retrieve operations)
- Property 13: Cache cleanup on track removal (100+ removal scenarios)
- Property 14: LRU cache eviction (100+ eviction scenarios)

#### 7. Integration Tests

**Unit Tests**:

- Test complete pipeline with single bottle
- Test pipeline with multiple bottles
- Test mode switching (Tracking ↔ Legacy)
- Test predictions_store updates
- Test statistics computation

**Property Tests**:

- Property 19: Pipeline statistics completeness (100+ frames)
- Property 20: Predictions store update (100+ classification events)
- Property 22: Legacy mode processes every frame (100+ frame sequences)
- Property 23: Mode switching clears state (100+ mode switches)

#### 8. Camera Controller Tests

**Unit Tests**:

- Test exposure setting within valid range
- Test brightness setting within valid range
- Test contrast setting within valid range
- Test auto-exposure toggle
- Test preset loading (Indoor, Outdoor, High Speed)
- Test invalid settings are clamped
- Test validation detects when camera doesn't respond
- Test histogram-based brightness validation

**Property Tests**:

- Property 24: Camera settings apply in real-time (100+ setting changes)
- Property 36: Camera validation detects non-responsive cameras (100+ validation scenarios)

#### 9. Data Logger Tests

**Unit Tests**:

- Test CSV export with sample detections
- Test JSON export with sample classifications
- Test video recording start/stop
- Test filename generation with timestamp
- Test session summary generation

**Property Tests**:

- Property 25: CSV export contains required columns (100+ export operations)
- Property 26: JSON export contains classification history (100+ export operations)
- Property 27: Performance metrics logging completeness (100+ log entries)
- Property 28: Session summary completeness (100+ sessions)
- Property 29: Export filename format (100+ exports)

#### 10. Performance Monitor Tests

**Unit Tests**:

- Test CPU usage retrieval
- Test GPU usage retrieval (if available)
- Test VRAM usage retrieval (if available)
- Test VRAM usage returns (0.0, 0.0) if CUDA unavailable
- Test FPS history tracking
- Test frame time breakdown
- Test warning generation (low FPS, high GPU, high VRAM)
- Test torch.cuda API is used (not nvidia-smi)

**Property Tests**:

- Property 37: VRAM monitoring uses torch.cuda API (100+ timing measurements)

#### 11. Testing Mode Tests

**Unit Tests**:

- Test mode switching (Normal, Static, Low-Speed, Stress)
- Test static test metrics calculation
- Test low-speed test metrics calculation
- Test stress test metrics calculation

**Property Tests**:

- Property 30: Static test movement detection (100+ movement scenarios)
- Property 31: Low-speed test ID swap detection (100+ tracking sequences)
- Property 32: Stress test capacity warning (100+ high-load scenarios)

### Test Data Generation

**Synthetic Frames**:

- Generate frames with known bottle positions
- Use simple colored rectangles as "bottles"
- Control confidence scores explicitly
- Simulate occlusions by removing detections

**Mock Models**:

- Mock YOLO to return controlled detections
- Mock DINOv3 to return deterministic features
- Mock classifiers to return predictable results
- Enable fast testing without GPU

**Real Data**:

- Use pre-recorded video clips for integration tests
- Test with actual YOLO and DINOv3 models
- Validate against known ground truth
- Measure actual FPS and performance

### Performance Testing

**Benchmarks**:

- Measure FPS with 1, 3, 5, 10 bottles
- Compare Tracking Mode vs Legacy Mode
- Measure classification reduction percentage
- Profile GPU memory usage

**Stress Tests**:

- Process 1000 frame video with multiple bottles
- Test with 20+ simultaneous detections
- Test cache with 200+ entries (verify eviction)
- Test long-running session (memory leaks)

### Continuous Testing

**Pre-commit Hooks**:

- Run unit tests on all modified files
- Run property tests with reduced iterations (10 examples)
- Check code formatting and linting

**CI/CD Pipeline**:

- Run full unit test suite
- Run property tests with full iterations (100 examples)
- Run integration tests with real models
- Generate coverage report (target: 80%+)

### Test Execution

**Local Development**:

```bash
# Run all unit tests
pytest tests/unit/ -v

# Run property tests
pytest tests/property/ -v --hypothesis-show-statistics

# Run specific property test
pytest tests/property/test_tracking.py::test_property_3_id_persistence -v

# Run with coverage
pytest --cov=src --cov-report=html
```

**Mock vs Real Models**:

- Unit tests: Use mocks for speed
- Property tests: Use mocks for speed, real models for validation
- Integration tests: Use real models
- Performance tests: Use real models on GPU

This dual testing approach ensures both concrete correctness (unit tests) and general correctness (property tests), providing comprehensive validation of the Detection-Tracking-Trigger Architecture.
