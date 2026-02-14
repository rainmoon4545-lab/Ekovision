# Requirements Document: Detection-Tracking-Trigger Architecture

## Introduction

The EkoVision PET Detection system currently processes every frame with both YOLOv10m (object detection) and DINOv3 (feature extraction and classification), causing significant computational bottleneck and low FPS on edge devices. This document specifies requirements for implementing a Detection-Tracking-Trigger Architecture that reduces computational load by up to 90% while maintaining classification accuracy.

The new architecture introduces object tracking to assign unique IDs to detected bottles, a trigger zone mechanism to classify bottles only once at optimal position, and a result caching system to display classifications without re-processing.

## Glossary

- **Detection_Layer**: The YOLOv10m model that runs continuously on every frame to detect bottle bounding boxes
- **Tracking_System**: The ByteTrack or SORT algorithm that assigns and maintains unique IDs for detected bottles across frames
- **Trigger_Zone**: A configurable region of interest (ROI) in the center of the frame where classification is triggered
- **Classification_Layer**: The DINOv3 feature extraction combined with 314 scikit-learn classifiers for multi-label classification
- **Result_Cache**: An in-memory storage system that maps bottle IDs to their classification results
- **Bottle_ID**: A unique integer identifier assigned to each tracked bottle (e.g., 101, 102, 103)
- **Tracking_State**: The status of a bottle, which can be NEW (first detection), TRACKED (being followed), CLASSIFIED (classification completed), or FAILED (classification failed after maximum retry attempts)
- **Multi_Label_Classification**: Classification across 8 attributes: product, grade, cap, label, brand, type, subtype, volume
- **Frame_Processing_Pipeline**: The complete sequence of detection, tracking, trigger evaluation, and classification operations
- **Camera_Configuration**: Settings that control camera behavior including exposure, brightness, contrast, and auto-exposure
- **Data_Logger**: Background thread that records detection and classification data for export and analysis
- **Performance_Monitor**: Component that tracks and displays real-time system metrics including GPU/CPU usage, VRAM, and processing times
- **Testing_Mode**: Specialized operational mode for field validation including Static Test, Low-Speed Test, and Stress Test
- **Session_Summary**: Report generated at session end containing aggregate statistics and performance metrics

## Requirements

### Requirement 0: Performance Benchmarking

**User Story:** As a developer, I want to benchmark classifier performance before implementation, so that I can identify optimization needs and ensure real-time performance targets are achievable.

#### Acceptance Criteria

1. WHEN the system initializes, THE Performance_Benchmark SHALL measure single classifier inference time on representative feature vectors
2. WHEN benchmarking, THE Performance_Benchmark SHALL measure total time for all 314 classifiers running sequentially
3. WHEN benchmarking, THE Performance_Benchmark SHALL test parallel inference using joblib.Parallel to measure potential speedup
4. THE Performance_Benchmark SHALL document baseline performance metrics including: single classifier time, total sequential time, total parallel time, and speedup factor
5. WHEN total classification time exceeds 100ms, THE Performance_Benchmark SHALL identify optimization strategies and document them for implementation
6. THE Performance_Benchmark SHALL run before any implementation tasks to establish performance baselines

### Requirement 1: Fast Detection Layer

**User Story:** As a system operator, I want continuous object detection on every frame, so that bottles are detected immediately when they enter the camera view.

#### Acceptance Criteria

1. THE Detection_Layer SHALL run YOLOv10m on every incoming frame
2. WHEN a frame is processed, THE Detection_Layer SHALL return bounding box coordinates for all detected bottles within 50ms
3. THE Detection_Layer SHALL use the existing confidence threshold configuration from the Streamlit sidebar
4. WHEN multiple bottles are detected in a frame, THE Detection_Layer SHALL return all bounding boxes with confidence scores above the threshold
5. THE Detection_Layer SHALL maintain the existing GPU acceleration when available

### Requirement 2: Object Tracking System

**User Story:** As a system operator, I want each detected bottle to have a unique ID that persists across frames, so that I can track individual bottles as they move through the scene.

#### Acceptance Criteria

1. WHEN a bottle is first detected, THE Tracking_System SHALL assign it a unique Bottle_ID
2. WHEN a bottle moves between frames, THE Tracking_System SHALL maintain the same Bottle_ID across consecutive frames
3. WHEN a bottle temporarily disappears due to occlusion, THE Tracking_System SHALL preserve its Bottle_ID for up to 30 frames
4. WHEN a bottle leaves the frame for more than 30 frames, THE Tracking_System SHALL remove its Bottle_ID from active tracking
5. THE Tracking_System SHALL use either ByteTrack or SORT algorithm for tracking implementation
6. WHEN tracking multiple bottles simultaneously, THE Tracking_System SHALL maintain distinct IDs for each bottle without ID swapping

### Requirement 3: Trigger Zone Definition

**User Story:** As a system operator, I want to define a center region where classification occurs, so that bottles are classified at optimal position with minimal distortion.

#### Acceptance Criteria

1. THE Trigger_Zone SHALL be defined as a rectangular region in the center of the frame
2. THE Trigger_Zone SHALL be configurable via Streamlit sidebar with parameters for x_offset, y_offset, width, and height as percentages of frame dimensions
3. THE Trigger_Zone SHALL have default dimensions of 40% width and 60% height, centered in the frame
4. WHEN rendering the video stream, THE Trigger_Zone SHALL be visualized with a semi-transparent overlay or border
5. THE Trigger_Zone SHALL support real-time adjustment without restarting the application

### Requirement 4: Trigger Logic for Classification

**User Story:** As a system operator, I want bottles to be classified only once when they enter the trigger zone, so that computational resources are used efficiently.

#### Acceptance Criteria

1. WHEN a bottle with Tracking_State NEW enters the Trigger_Zone, THE Classification_Layer SHALL be triggered
2. WHEN a bottle with Tracking_State CLASSIFIED enters the Trigger_Zone, THE Classification_Layer SHALL NOT be triggered
3. WHEN a bottle with Tracking_State FAILED enters the Trigger_Zone, THE Classification_Layer SHALL NOT be triggered
4. WHEN determining if a bottle is in the Trigger_Zone, THE Frame_Processing_Pipeline SHALL check if the bottle's bounding box center point is within the Trigger_Zone boundaries
5. WHEN a bottle is triggered for classification, THE Frame_Processing_Pipeline SHALL extract the bottle crop using its bounding box coordinates
6. WHEN classification is triggered, THE Frame_Processing_Pipeline SHALL update the bottle's Tracking_State from NEW to CLASSIFIED
7. WHEN classification fails and the bottle has reached maximum retry attempts, THE Frame_Processing_Pipeline SHALL update the bottle's Tracking_State to FAILED to prevent infinite retries

### Requirement 5: Classification Execution

**User Story:** As a system operator, I want the existing DINOv3 and classifier models to process bottles only when triggered, so that classification accuracy is maintained while reducing computational load.

#### Acceptance Criteria

1. WHEN a bottle is triggered for classification, THE Classification_Layer SHALL extract DINOv3 features from the bottle crop
2. WHEN features are extracted, THE Classification_Layer SHALL run all 314 scikit-learn classifiers to predict the 8 Multi_Label_Classification attributes
3. THE Classification_Layer SHALL apply the existing fallback and conflict resolution logic for label mapping
4. WHEN classification completes, THE Classification_Layer SHALL return results in the same format as the current system (dictionary with 8 keys)
5. THE Classification_Layer SHALL complete classification within 100ms on GPU-enabled systems for optimal real-time performance
6. WHEN multiple bottles enter the Trigger_Zone simultaneously, THE Classification_Layer SHALL batch process all bottles in a single GPU call to minimize transfer overhead
7. WHEN the system initializes, THE Classification_Layer SHALL warm up all classifiers with a dummy prediction to prevent first-inference lag spikes

### Requirement 6: Result Caching System

**User Story:** As a system operator, I want classification results to be stored and reused, so that each bottle is only classified once regardless of how long it remains visible.

#### Acceptance Criteria

1. WHEN a bottle is classified, THE Result_Cache SHALL store the classification results mapped to the Bottle_ID
2. WHEN a tracked bottle is detected in subsequent frames, THE Result_Cache SHALL retrieve cached results using the Bottle_ID
3. WHEN a bottle leaves the frame and its Bottle_ID is removed from tracking, THE Result_Cache SHALL delete the corresponding cached results
4. THE Result_Cache SHALL support concurrent access from the video processing thread
5. WHEN the Result_Cache exceeds 100 entries, THE Result_Cache SHALL remove the oldest entries using a least-recently-used (LRU) eviction policy

### Requirement 7: Visualization and Display

**User Story:** As a system operator, I want to see bounding boxes with bottle IDs and classification results on the video stream, so that I can monitor the system's performance in real-time.

#### Acceptance Criteria

1. WHEN rendering a frame, THE Frame_Processing_Pipeline SHALL draw bounding boxes around all tracked bottles
2. WHEN drawing a bounding box, THE Frame_Processing_Pipeline SHALL display the Bottle_ID above the box
3. WHEN a bottle has Tracking_State CLASSIFIED, THE Frame_Processing_Pipeline SHALL display all 8 classification attributes with color-coded text using the existing CATEGORY_COLORS_BGR mapping
4. WHEN a bottle has Tracking_State NEW or TRACKED, THE Frame_Processing_Pipeline SHALL display the tracking state text instead of classification results
5. WHEN rendering the Trigger_Zone, THE Frame_Processing_Pipeline SHALL draw a semi-transparent rectangle or border to indicate the zone boundaries
6. THE Frame_Processing_Pipeline SHALL display FPS counter in the top-left corner of the frame

### Requirement 8: Performance Optimization

**User Story:** As a system operator, I want the system to achieve real-time FPS on edge devices, so that the application is practical for production deployment.

#### Acceptance Criteria

1. WHEN processing a video stream with a single bottle, THE Frame_Processing_Pipeline SHALL achieve at least 15 FPS on NVIDIA RTX GPU systems
2. WHEN processing a video stream with up to 5 bottles simultaneously, THE Frame_Processing_Pipeline SHALL maintain at least 10 FPS on NVIDIA RTX GPU systems
3. WHEN a bottle is not in the Trigger_Zone, THE Frame_Processing_Pipeline SHALL skip DINOv3 feature extraction and classification
4. THE Frame_Processing_Pipeline SHALL reduce DINOv3 invocations by at least 80% compared to the current per-frame processing approach
5. WHEN GPU memory usage exceeds 90% of available VRAM, THE Frame_Processing_Pipeline SHALL log a warning and continue operation

### Requirement 9: Integration with Existing System

**User Story:** As a developer, I want the new architecture to integrate seamlessly with the existing Streamlit application, so that minimal changes are required to the UI and configuration.

#### Acceptance Criteria

1. THE Frame_Processing_Pipeline SHALL maintain compatibility with the existing StreamProcessor class in the Streamlit application
2. THE Frame_Processing_Pipeline SHALL use the existing confidence_threshold slider from the Streamlit sidebar
3. THE Frame_Processing_Pipeline SHALL continue to populate the predictions_store deque with classification results
4. THE Frame_Processing_Pipeline SHALL support both webcam input (via streamlit-webrtc) and video file input
5. WHEN the system is initialized, THE Frame_Processing_Pipeline SHALL load the existing YOLO, DINOv3, and classifier models without modification

### Requirement 10: Configuration and Tuning

**User Story:** As a system operator, I want to configure tracking and trigger parameters via the UI, so that I can optimize performance for different deployment scenarios.

#### Acceptance Criteria

1. THE Streamlit sidebar SHALL provide sliders for Trigger_Zone position (x_offset, y_offset) as percentages from 0% to 50%
2. THE Streamlit sidebar SHALL provide sliders for Trigger_Zone dimensions (width, height) as percentages from 20% to 80%
3. THE Streamlit sidebar SHALL provide a slider for tracking persistence duration from 10 to 60 frames
4. THE Streamlit sidebar SHALL provide a toggle to enable/disable Trigger_Zone visualization overlay
5. WHEN configuration parameters are changed, THE Frame_Processing_Pipeline SHALL apply changes to the next processed frame without requiring application restart

### Requirement 11: Memory Management

**User Story:** As a system operator, I want the system to manage memory efficiently during long-running sessions, so that the application remains stable without memory leaks.

#### Acceptance Criteria

1. WHEN the Result_Cache exceeds its maximum size, THE Result_Cache SHALL automatically evict the least recently used entries
2. WHEN a bottle is no longer tracked, THE Tracking_System SHALL release all associated memory resources within 5 seconds
3. THE Frame_Processing_Pipeline SHALL limit the maximum number of simultaneously tracked bottles to 20
4. WHEN the maximum tracked bottle limit is reached, THE Tracking_System SHALL prioritize bottles with higher confidence scores
5. THE Frame_Processing_Pipeline SHALL provide a "Clear Cache" button in the Streamlit sidebar to manually reset the Result_Cache and Tracking_System

### Requirement 12: Error Handling and Robustness

**User Story:** As a system operator, I want the system to handle errors gracefully, so that temporary issues do not crash the application.

#### Acceptance Criteria

1. WHEN the Tracking_System fails to assign an ID, THE Frame_Processing_Pipeline SHALL log the error and continue processing the next frame
2. WHEN the Classification_Layer encounters an error during feature extraction, THE Frame_Processing_Pipeline SHALL mark the bottle as UNKNOWN and continue tracking
3. WHEN the Result_Cache encounters a memory error, THE Frame_Processing_Pipeline SHALL clear the cache and log a warning
4. WHEN GPU memory is exhausted, THE Frame_Processing_Pipeline SHALL fall back to CPU processing and display a warning message
5. IF the Trigger_Zone configuration is invalid (e.g., dimensions exceed frame boundaries), THEN THE Frame_Processing_Pipeline SHALL reset to default values and log a warning

### Requirement 13: Testing and Validation Support

**User Story:** As a developer, I want to test the system with different input sources and scenarios, so that I can validate performance improvements and accuracy.

#### Acceptance Criteria

1. THE Frame_Processing_Pipeline SHALL support processing pre-recorded video files in addition to live webcam streams
2. THE Frame_Processing_Pipeline SHALL provide a debug mode that logs tracking events (new ID, ID lost, classification triggered) to the console
3. THE Frame_Processing_Pipeline SHALL display real-time statistics including: active tracked bottles, classifications per second, and cache hit rate
4. WHEN debug mode is enabled, THE Frame_Processing_Pipeline SHALL save annotated frames to disk at configurable intervals
5. THE Frame_Processing_Pipeline SHALL support a "stress test" mode that processes video files with multiple bottles at maximum speed

### Requirement 14: Backwards Compatibility

**User Story:** As a developer, I want to maintain the option to use the original per-frame processing approach, so that I can compare performance and validate the new architecture.

#### Acceptance Criteria

1. THE Streamlit sidebar SHALL provide a toggle to switch between "Tracking Mode" (new architecture) and "Legacy Mode" (per-frame processing)
2. WHEN Legacy Mode is enabled, THE Frame_Processing_Pipeline SHALL process every frame with both YOLO and DINOv3 as in the original implementation
3. WHEN switching between modes, THE Frame_Processing_Pipeline SHALL clear all tracking state and cached results
4. THE Frame_Processing_Pipeline SHALL display the current mode prominently in the UI
5. WHEN in Tracking Mode, THE Frame_Processing_Pipeline SHALL display performance metrics comparing current FPS to Legacy Mode baseline

### Requirement 15: Camera Configuration UI

**User Story:** As a system operator, I want to adjust camera settings directly from the UI, so that I can optimize bottle detection for different lighting conditions and conveyor speeds.

#### Acceptance Criteria

1. THE Streamlit sidebar SHALL provide a section for camera configuration controls
2. THE Streamlit sidebar SHALL provide a slider for manual exposure control with shutter speed range from 1/250 to 1/2000 seconds
3. THE Streamlit sidebar SHALL provide a slider for brightness adjustment with range from -50 to +50
4. THE Streamlit sidebar SHALL provide a slider for contrast adjustment with range from 0.5 to 2.0
5. THE Streamlit sidebar SHALL provide a toggle to enable or disable auto-exposure
6. WHEN camera settings are adjusted, THE Frame_Processing_Pipeline SHALL apply changes to the video stream in real-time
7. THE Streamlit sidebar SHALL display the current camera settings values
8. THE Streamlit sidebar SHALL provide preset buttons for common configurations: "Indoor", "Outdoor", and "High Speed"
9. WHEN a preset button is clicked, THE Frame_Processing_Pipeline SHALL load and apply the corresponding camera configuration
10. WHEN camera settings are applied, THE Camera_Configuration SHALL validate that the camera responds correctly and display warnings if programmatic control is not supported
11. WHEN camera validation detects that programmatic control is not working, THE Camera_Configuration SHALL provide guidance for manual configuration fallback

### Requirement 16: Data Logging and Export

**User Story:** As a system operator, I want to export detection and classification data, so that I can analyze system performance and validate proof-of-concept results.

#### Acceptance Criteria

1. WHEN the export CSV button is clicked, THE Frame_Processing_Pipeline SHALL generate a CSV file with columns: timestamp, track_id, bbox, confidence, classification_results (8 attributes), tracking_state
2. WHEN video recording is enabled, THE Frame_Processing_Pipeline SHALL save the annotated video stream to disk in MP4 format
3. WHEN the export JSON button is clicked, THE Frame_Processing_Pipeline SHALL generate a JSON file containing classification history for all tracked bottles
4. THE Frame_Processing_Pipeline SHALL log performance metrics over time including: FPS, classification_rate, cache_hit_rate, active_tracks
5. WHEN a session ends, THE Frame_Processing_Pipeline SHALL generate a summary report with: total bottles detected, total classifications, average FPS, cache statistics
6. THE Streamlit sidebar SHALL provide controls for: Start/Stop Recording, Export CSV, Export JSON
7. WHEN exporting files, THE Frame_Processing_Pipeline SHALL generate filenames with timestamp format: "ekovision_YYYY-MM-DD_HH-MM-SS.csv"
8. THE Frame_Processing_Pipeline SHALL run data logging in a background thread to avoid blocking video processing

### Requirement 17: Real-time Performance Monitoring

**User Story:** As a system operator, I want to monitor system performance in real-time, so that I can ensure the system meets the 80-90% computational reduction target and identify bottlenecks.

#### Acceptance Criteria

1. THE Streamlit sidebar SHALL display real-time GPU usage percentage
2. THE Streamlit sidebar SHALL display real-time CPU usage percentage
3. THE Streamlit sidebar SHALL display VRAM usage in format: current/total (e.g., "4.2GB / 8.0GB")
4. THE Streamlit sidebar SHALL display frame processing time breakdown with: detection_time, tracking_time, classification_time, rendering_time
5. THE Streamlit sidebar SHALL display classification reduction percentage compared to legacy mode
6. THE Streamlit sidebar SHALL display cache statistics including: size, hit_rate, miss_rate
7. WHEN FPS drops below 10, THE Streamlit sidebar SHALL display a warning indicator
8. WHEN GPU usage exceeds 95%, THE Streamlit sidebar SHALL display a warning indicator
9. WHEN VRAM usage exceeds 90%, THE Streamlit sidebar SHALL display a warning indicator
10. THE Streamlit sidebar SHALL display a performance graph showing FPS over the last 60 seconds

### Requirement 18: Testing Modes for Field Validation

**User Story:** As a system operator, I want to use specialized testing modes, so that I can validate system performance during the 3-phase field testing process.

**Status**: ⚠️ OPTIONAL - Not implemented in POC, can be added as enhancement

#### Acceptance Criteria

1. THE Streamlit sidebar SHALL provide a "Testing Mode" selector with options: "Normal", "Static Test", "Low-Speed Test", "Stress Test"
2. WHEN Static Test Mode is selected, THE Frame_Processing_Pipeline SHALL display bottle position stability metrics
3. WHEN Static Test Mode is selected and a bottle moves, THE Frame_Processing_Pipeline SHALL display a warning
4. WHEN Low-Speed Test Mode is selected, THE Frame_Processing_Pipeline SHALL display tracking continuity metrics
5. WHEN Low-Speed Test Mode is selected and an ID swap occurs, THE Frame_Processing_Pipeline SHALL display a warning
6. WHEN Stress Test Mode is selected, THE Frame_Processing_Pipeline SHALL display the maximum number of concurrent bottles handled
7. WHEN Stress Test Mode is selected and active tracks exceed 20, THE Frame_Processing_Pipeline SHALL display a warning
8. THE Streamlit UI header SHALL clearly indicate the currently selected testing mode
9. WHEN a testing mode is active, THE Streamlit sidebar SHALL display metrics specific to that testing phase

---

## OPTIONAL ENHANCEMENTS (Post-POC Features)

The following requirements are enhancements that can be added after the proof-of-concept is validated. These features improve usability and production readiness but are not critical for core functionality.

### Requirement 19: Configuration File Support

**User Story:** As a system operator, I want to configure the system via a configuration file, so that I can easily adjust settings without editing code.

#### Acceptance Criteria

1. THE System SHALL support loading configuration from a YAML or JSON file (e.g., `config.yaml`)
2. THE Configuration file SHALL include sections for: camera settings, trigger zone, tracking parameters, classification settings
3. WHEN the configuration file is present, THE System SHALL load settings from the file on startup
4. WHEN the configuration file is missing, THE System SHALL use default hardcoded values
5. THE Configuration file SHALL support comments for documentation
6. WHEN configuration values are invalid, THE System SHALL log warnings and use default values
7. THE System SHALL provide a sample configuration file (`config.sample.yaml`) with all available options documented

**Example Configuration**:

```yaml
# EkoVision Detection-Tracking-Trigger Configuration

camera:
  index: 0 # Camera device index (0 = default)
  width: 640 # Frame width in pixels
  height: 480 # Frame height in pixels

detection:
  confidence_threshold: 0.5 # YOLO confidence threshold (0.0-1.0)

trigger_zone:
  x_offset_pct: 30.0 # X offset from left (0-50%)
  y_offset_pct: 20.0 # Y offset from top (0-50%)
  width_pct: 40.0 # Zone width (20-80%)
  height_pct: 60.0 # Zone height (20-80%)

tracking:
  max_age: 30 # Max frames to keep track without detection
  max_tracks: 20 # Maximum simultaneous tracks
  max_classification_attempts: 2 # Max retry before FAILED state

cache:
  max_size: 100 # Maximum cached results

models:
  yolo_path: "best.pt"
  dinov3_model: "facebook/dinov3-convnext-small-pretrain-lvd1689m"
  encoder_path: "dinov3_multilabel_encoder.pkl"
  mapping_path: "label_mapping_dict.joblib"
  classifiers_dir: "OVR_Checkpoints-20251018T053026Z-1-001/OVR_Checkpoints"
```

### Requirement 20: Data Logging and Export (Standalone)

**User Story:** As a system operator, I want to export detection and classification data, so that I can analyze system performance and validate results.

#### Acceptance Criteria

1. THE System SHALL support keyboard shortcut 'e' to export current session data to CSV
2. WHEN CSV export is triggered, THE System SHALL generate a file with columns: timestamp, track_id, bbox, confidence, state, and 8 classification attributes
3. THE System SHALL support keyboard shortcut 'j' to export classification history to JSON
4. WHEN JSON export is triggered, THE System SHALL generate a file containing all tracked bottles with their classification results
5. THE System SHALL support keyboard shortcut 'v' to start/stop video recording
6. WHEN video recording is active, THE System SHALL save annotated frames to MP4 file
7. THE System SHALL display recording status indicator on screen (red dot when recording)
8. WHEN exporting files, THE System SHALL generate filenames with timestamp format: "ekovision_YYYY-MM-DD_HH-MM-SS.{csv|json|mp4}"
9. WHEN a session ends, THE System SHALL optionally generate a summary report with: total bottles detected, total classifications, average FPS, cache statistics
10. THE System SHALL log all exports to console with file paths

**CSV Format**:

```csv
timestamp,track_id,x1,y1,x2,y2,confidence,state,product,grade,cap,label,brand,type,subtype,volume
2026-02-12T10:30:45,101,120,80,220,280,0.95,CLASSIFIED,Aqua,Premium,Blue,Clear,Danone,Water,Still,600ml
```

**JSON Format**:

```json
{
  "session_start": "2026-02-12T10:30:00",
  "session_end": "2026-02-12T10:45:00",
  "total_bottles": 45,
  "total_classifications": 42,
  "bottles": [
    {
      "track_id": 101,
      "first_seen": "2026-02-12T10:30:45",
      "last_seen": "2026-02-12T10:30:48",
      "state": "CLASSIFIED",
      "classification": {
        "product": "Aqua",
        "grade": "Premium",
        ...
      }
    }
  ]
}
```

### Requirement 21: Runtime Camera Controls

**User Story:** As a system operator, I want to adjust camera settings at runtime via keyboard, so that I can optimize image quality for different lighting conditions.

#### Acceptance Criteria

1. THE System SHALL support keyboard shortcut 'c' to open camera control mode
2. WHEN camera control mode is active, THE System SHALL display on-screen menu with available controls
3. THE System SHALL support keyboard shortcuts for exposure adjustment: '[' to decrease, ']' to increase (steps of 1/250 sec)
4. THE System SHALL support keyboard shortcuts for brightness adjustment: '-' to decrease, '+' to increase (steps of 5)
5. THE System SHALL support keyboard shortcut 'a' to toggle auto-exposure on/off
6. THE System SHALL support keyboard shortcuts '1', '2', '3' to load presets: Indoor, Outdoor, High Speed
7. WHEN camera settings are adjusted, THE System SHALL display current values on screen for 3 seconds
8. WHEN camera does not respond to programmatic control, THE System SHALL display warning message
9. THE System SHALL validate camera settings by reading back values after applying
10. THE System SHALL save current camera settings to config file when 'Ctrl+S' is pressed

**On-Screen Display** (when 'c' is pressed):

```
Camera Controls:
  [ / ]  - Exposure (1/500 sec)
  - / +  - Brightness (10)
  a      - Auto-exposure (OFF)
  1/2/3  - Presets (Indoor/Outdoor/High Speed)
  c      - Close menu
```

### Requirement 22: Performance Monitoring Display

**User Story:** As a system operator, I want to see real-time performance metrics on screen, so that I can monitor system health and identify bottlenecks.

#### Acceptance Criteria

1. THE System SHALL support keyboard shortcut 'm' to toggle performance metrics overlay
2. WHEN metrics overlay is enabled, THE System SHALL display in top-right corner: GPU usage, CPU usage, VRAM usage, frame time breakdown
3. THE System SHALL update metrics every 1 second to avoid performance impact
4. THE System SHALL display GPU usage as percentage (0-100%)
5. THE System SHALL display CPU usage as percentage (0-100%)
6. THE System SHALL display VRAM usage in format: "current/total GB"
7. THE System SHALL display frame time breakdown: detection_ms, tracking_ms, classification_ms, rendering_ms
8. WHEN FPS drops below 10, THE System SHALL display warning indicator (red text)
9. WHEN GPU usage exceeds 95%, THE System SHALL display warning indicator (yellow background)
10. WHEN VRAM usage exceeds 90%, THE System SHALL display warning indicator (orange background)
11. THE System SHALL support keyboard shortcut 'g' to save performance graph (FPS over last 60 seconds) as PNG

**On-Screen Display** (when 'm' is pressed):

```
Performance Metrics:
  FPS: 17.5 (avg: 17.2)
  GPU: 78% | CPU: 45%
  VRAM: 4.2/8.0 GB

Frame Time:
  Detection: 12ms
  Tracking: 3ms
  Classification: 33ms
  Rendering: 8ms
  Total: 56ms
```

### Requirement 23: Advanced Trigger Zone Configuration

**User Story:** As a system operator, I want to configure multiple trigger zones or custom shapes, so that I can optimize for different conveyor layouts.

#### Acceptance Criteria

1. THE System SHALL support keyboard shortcut 'z' to enter trigger zone edit mode
2. WHEN in edit mode, THE System SHALL allow mouse-based zone adjustment: click and drag corners to resize
3. THE System SHALL support multiple trigger zones (up to 3) for complex conveyor layouts
4. THE System SHALL support keyboard shortcut 'n' to add new trigger zone
5. THE System SHALL support keyboard shortcut 'Delete' to remove selected trigger zone
6. WHEN multiple zones are active, THE System SHALL classify bottles when they enter ANY zone
7. THE System SHALL display zone numbers on screen (Zone 1, Zone 2, Zone 3)
8. THE System SHALL save trigger zone configurations to config file
9. THE System SHALL support keyboard shortcut 'Ctrl+Z' to undo last zone adjustment
10. THE System SHALL validate that zones do not overlap by more than 20%

**Advanced Configuration** (config.yaml):

```yaml
trigger_zones:
  - name: "Primary Zone"
    x_offset_pct: 30.0
    y_offset_pct: 20.0
    width_pct: 40.0
    height_pct: 60.0
    enabled: true

  - name: "Secondary Zone"
    x_offset_pct: 10.0
    y_offset_pct: 40.0
    width_pct: 30.0
    height_pct: 40.0
    enabled: false
```

### Requirement 24: Batch Processing Mode

**User Story:** As a system operator, I want to process pre-recorded videos in batch mode, so that I can analyze historical footage efficiently.

#### Acceptance Criteria

1. THE System SHALL support command-line argument `--batch` to enable batch processing mode
2. WHEN batch mode is enabled, THE System SHALL process video files from a specified directory
3. THE System SHALL support command-line argument `--input-dir` to specify input directory
4. THE System SHALL support command-line argument `--output-dir` to specify output directory
5. WHEN processing videos in batch, THE System SHALL save annotated videos to output directory
6. WHEN processing videos in batch, THE System SHALL generate CSV and JSON exports for each video
7. THE System SHALL display progress bar showing: current video, frame progress, estimated time remaining
8. THE System SHALL generate batch summary report with: total videos processed, total bottles detected, average FPS per video
9. THE System SHALL support command-line argument `--skip-visualization` to disable rendering for faster processing
10. THE System SHALL support command-line argument `--max-workers` to enable parallel video processing

**Command-Line Usage**:

```bash
# Process single video
python run_detection_tracking.py --batch --input video.mp4 --output results/

# Process directory of videos
python run_detection_tracking.py --batch --input-dir videos/ --output-dir results/

# Fast processing (no visualization)
python run_detection_tracking.py --batch --input-dir videos/ --output-dir results/ --skip-visualization

# Parallel processing
python run_detection_tracking.py --batch --input-dir videos/ --output-dir results/ --max-workers 4
```

### Requirement 25: Web Dashboard (Optional)

**User Story:** As a system operator, I want to monitor the system remotely via web browser, so that I can supervise operations without physical access to the workstation.

#### Acceptance Criteria

1. THE System SHALL support command-line argument `--web-dashboard` to enable web interface
2. WHEN web dashboard is enabled, THE System SHALL start HTTP server on configurable port (default: 8080)
3. THE Web Dashboard SHALL display live video stream with annotations
4. THE Web Dashboard SHALL display real-time statistics: FPS, active tracks, classifications, cache hit rate
5. THE Web Dashboard SHALL display performance metrics: GPU/CPU usage, VRAM, frame time breakdown
6. THE Web Dashboard SHALL provide controls for: start/stop, reset, toggle trigger zone, export data
7. THE Web Dashboard SHALL support multiple concurrent viewers without performance degradation
8. THE Web Dashboard SHALL use WebSocket for real-time updates
9. THE Web Dashboard SHALL be accessible at `http://localhost:8080` by default
10. THE System SHALL continue to support standalone mode (OpenCV window) when web dashboard is disabled

**Command-Line Usage**:

```bash
# Start with web dashboard
python run_detection_tracking.py --web-dashboard --port 8080

# Web dashboard only (no OpenCV window)
python run_detection_tracking.py --web-dashboard --headless
```

**Web Dashboard Features**:

- Live video stream with WebRTC
- Real-time statistics panel
- Performance graphs (FPS, GPU usage over time)
- Control buttons (Start/Stop, Reset, Export)
- Configuration panel (trigger zone, tracking parameters)
- Log viewer (recent events and warnings)

---

## Enhancement Priority

Based on user value and implementation complexity:

**High Priority** (Quick wins):

1. ✅ Requirement 19: Configuration File Support (Easy, high value)
2. ✅ Requirement 20: Data Logging and Export (Medium, high value)
3. ✅ Requirement 21: Runtime Camera Controls (Medium, high value)

**Medium Priority** (Useful features): 4. ✅ Requirement 22: Performance Monitoring Display (Easy, medium value) 5. ✅ Requirement 24: Batch Processing Mode (Medium, medium value)

**Low Priority** (Advanced features): 6. ⚠️ Requirement 23: Advanced Trigger Zone Configuration (Complex, low value) 7. ⚠️ Requirement 25: Web Dashboard (Complex, situational value)

**Implementation Order Recommendation**:

1. Config file support (Req 19) - Foundation for other features
2. Data logging (Req 20) - Critical for analysis
3. Camera controls (Req 21) - Improves usability
4. Performance monitoring (Req 22) - Helps optimization
5. Batch processing (Req 24) - Useful for testing
6. Advanced zones (Req 23) - Only if needed
7. Web dashboard (Req 25) - Only for remote monitoring needs
