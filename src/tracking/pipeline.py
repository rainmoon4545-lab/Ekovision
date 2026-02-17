"""
DetectionTrackingPipeline - Main pipeline integrating all components.
"""
import time
import numpy as np
import cv2
import torch
from PIL import Image
from typing import Dict, List, Tuple, Any, Optional
from collections import deque

from .bottle_tracker import BottleTracker, TrackingState
from .trigger_zone import TriggerZone, TriggerZoneConfig
from .classification_cache import ClassificationCache
from .classification_overlay import ClassificationOverlay
from ..image_enhancement import (
    expand_bbox,
    preprocess_crop,
    ensure_minimum_crop_size
)
from ..temporal_smoother import TemporalSmoother


class DetectionTrackingPipeline:
    """
    Main pipeline for Detection-Tracking-Trigger architecture.
    
    Integrates YOLO detection, ByteTrack tracking, trigger zone logic,
    and DINOv3 classification with caching.
    """
    
    def __init__(
        self,
        yolo_model,
        dinov3_processor,
        dinov3_model,
        classifiers: List,
        mlb,
        mapping_dict: Dict,
        label_columns: List[str],
        frame_width: int,
        frame_height: int,
        confidence_threshold: float = 0.5,
        trigger_zone_config: Optional[TriggerZoneConfig] = None,
        max_classification_attempts: int = 2,
        device: str = 'cuda',
        classification_config: Optional[Dict] = None
    ):
        """
        Initialize detection-tracking pipeline.
        
        Args:
            yolo_model: YOLO detection model
            dinov3_processor: DINOv3 image processor
            dinov3_model: DINOv3 feature extraction model
            classifiers: List of scikit-learn classifiers (314 models)
            mlb: MultiLabelBinarizer for label encoding
            mapping_dict: Mapping dictionary for label categories
            label_columns: List of label column names (8 attributes)
            frame_width: Video frame width
            frame_height: Video frame height
            confidence_threshold: Confidence threshold for classification
            trigger_zone_config: Trigger zone configuration
            max_classification_attempts: Maximum classification retry attempts
            device: Device for model inference ('cuda' or 'cpu')
            classification_config: Classification configuration dict
        """
        # Models
        self.yolo_model = yolo_model
        self.dinov3_processor = dinov3_processor
        self.dinov3_model = dinov3_model
        self.classifiers = classifiers
        self.mlb = mlb
        self.mapping_dict = mapping_dict
        self.label_columns = label_columns
        self.confidence_threshold = confidence_threshold
        self.device = device
        
        # Frame dimensions
        self.frame_width = frame_width
        self.frame_height = frame_height
        
        # Classification config
        if classification_config is None:
            classification_config = {}
        self.expand_bbox_ratio = classification_config.get('expand_bbox_ratio', 0.1)
        self.min_crop_size = classification_config.get('min_crop_size', 224)
        self.enable_temporal_smoothing = classification_config.get('enable_temporal_smoothing', True)
        self.temporal_window_size = classification_config.get('temporal_window_size', 5)
        self.enable_preprocessing = classification_config.get('enable_preprocessing', True)
        self.enable_ensemble = classification_config.get('enable_ensemble', False)
        
        # Initialize components
        self.tracker = BottleTracker(
            max_age=30,
            min_hits=1,
            iou_threshold=0.3,
            max_classification_attempts=max_classification_attempts,
            max_tracks=20,
            track_thresh=confidence_threshold
        )
        
        self.trigger_zone = TriggerZone(
            frame_width=frame_width,
            frame_height=frame_height,
            config=trigger_zone_config
        )
        
        self.cache = ClassificationCache(max_size=100)
        
        # Initialize classification overlay
        self.overlay = ClassificationOverlay(
            position="top-center",
            background_alpha=0.7,
            font_scale=0.6,
            max_tracks_display=3
        )
        
        # Temporal smoother
        if self.enable_temporal_smoothing:
            self.temporal_smoother = TemporalSmoother(window_size=self.temporal_window_size)
        else:
            self.temporal_smoother = None
        
        # Statistics
        self.frame_count = 0
        self.classification_count = 0
        self.fps_history = deque(maxlen=30)
        self.last_frame_time = time.time()
        self.show_trigger_zone = True  # Default: show trigger zone
        
        # Skip frame detection for performance optimization
        self.skip_frames = classification_config.get('skip_frames', 0)  # 0 = detect every frame
        self.detection_frame_counter = 0
        self.last_detections = []  # Store last detection results
        
        # Overlay display toggle
        self.show_overlay = classification_config.get('show_overlay', True)
        
        # Warmup classifiers
        self._warmup_classifiers()
    
    def _warmup_classifiers(self):
        """
        Warmup classifiers to prevent first-inference lag.
        
        Runs a dummy prediction through all 314 classifiers to ensure
        they are loaded and ready for fast inference.
        """
        print("Warming up classifiers...")
        dummy_features = np.random.randn(1, 768).astype(np.float32)
        
        for clf in self.classifiers:
            try:
                _ = clf.predict_proba(dummy_features)
            except Exception as e:
                print(f"Warning: Classifier warmup failed: {e}")
        
        print(f"Classifier warmup complete ({len(self.classifiers)} classifiers)")
    
    def _detect_bottles(self, frame_rgb: np.ndarray) -> np.ndarray:
        """
        Run YOLO detection on frame.
        
        Args:
            frame_rgb: Frame in RGB format
        
        Returns:
            Detections array of shape (N, 5) with format [x1, y1, x2, y2, score]
        """
        img_pil = Image.fromarray(frame_rgb)
        
        # Run YOLO inference
        results = self.yolo_model(img_pil, verbose=False, conf=self.confidence_threshold)
        
        if not results or not results[0].boxes:
            return np.array([]).reshape(0, 5)
        
        # Extract boxes
        boxes = results[0].boxes.cpu().numpy()
        detections = []
        
        for box in boxes:
            x1, y1, x2, y2 = box.xyxy[0]
            conf = box.conf[0]
            
            # Filter by confidence
            if conf >= self.confidence_threshold:
                detections.append([x1, y1, x2, y2, conf])
        
        return np.array(detections) if detections else np.array([]).reshape(0, 5)
    
    def _extract_dinov3_features(self, image_crop: Image.Image) -> np.ndarray:
        """
        Extract DINOv3 features from image crop.
        
        Args:
            image_crop: PIL Image crop
        
        Returns:
            Feature vector of shape (768,)
        """
        inputs = self.dinov3_processor(images=image_crop, return_tensors="pt").to(self.device)
        
        with torch.no_grad():
            outputs = self.dinov3_model(**inputs)
            features = outputs.last_hidden_state[:, 0, :]
            return features.cpu().numpy().flatten()
    
    def _classify_bottle(
        self,
        frame_pil: Image.Image,
        bbox: np.ndarray
    ) -> Optional[Dict[str, str]]:
        """
        Classify a single bottle using DINOv3 + classifiers.
        
        Args:
            frame_pil: Full frame as PIL Image
            bbox: Bounding box [x1, y1, x2, y2]
        
        Returns:
            Classification results dict or None if failed
        """
        try:
            # Expand bounding box for more context
            if self.expand_bbox_ratio > 0:
                expanded_bbox = expand_bbox(
                    bbox,
                    (frame_pil.height, frame_pil.width),
                    self.expand_bbox_ratio
                )
            else:
                expanded_bbox = tuple(map(int, bbox))
            
            # Extract crop
            x1, y1, x2, y2 = expanded_bbox
            image_crop = frame_pil.crop((x1, y1, x2, y2))
            
            # Ensure minimum crop size
            if self.min_crop_size > 0:
                image_crop = ensure_minimum_crop_size(image_crop, self.min_crop_size)
            
            # Preprocess crop if enabled
            if self.enable_preprocessing:
                image_crop = preprocess_crop(image_crop)
            
            # Extract features
            features = self._extract_dinov3_features(image_crop)
            
            # Run classifiers (sequential inference - fastest based on benchmark)
            X_pred = features.reshape(1, -1)
            Y_proba_list = [clf.predict_proba(X_pred)[0, 1] for clf in self.classifiers]
            Y_proba = np.array(Y_proba_list)
            
            # Map probabilities to class names
            class_proba_map = dict(zip(self.mlb.classes_, Y_proba))
            
            # Binary prediction (threshold 0.5)
            Y_pred_biner = (Y_proba > 0.5).astype(int).reshape(1, -1)
            predicted_labels_set = set(self.mlb.inverse_transform(Y_pred_biner)[0])
            
            # Apply mapping logic with fallback and conflict resolution
            final_output = {}
            
            for col in self.label_columns:
                intersection = predicted_labels_set.intersection(self.mapping_dict[col])
                
                # Find highest probability label in this category
                best_proba = -1
                best_label = "UNKNOWN"
                for label in self.mapping_dict[col]:
                    proba = class_proba_map.get(label, 0.0)
                    if proba > best_proba:
                        best_proba = proba
                        best_label = label
                
                if len(intersection) == 1:
                    # No conflict, strong prediction
                    final_output[col] = intersection.pop()
                elif len(intersection) == 0:
                    # Fallback if no binary prediction
                    if best_proba >= self.confidence_threshold:
                        final_output[col] = f"{best_label} ({best_proba*100:.1f}%)"
                    else:
                        final_output[col] = "UNKNOWN"
                else:
                    # Conflict: multiple binary predictions (rare)
                    final_output[col] = f"CONFLICT -> {best_label} ({best_proba*100:.1f}%)"
            
            return final_output
            
        except Exception as e:
            print(f"Classification error: {e}")
            return None
    
    def _should_trigger_classification(self, track) -> bool:
        """
        Check if track should trigger classification.
        
        Args:
            track: BottleTrack object
        
        Returns:
            True if should classify, False otherwise
        """
        # Only classify NEW or TRACKED bottles
        if track.state not in [TrackingState.NEW, TrackingState.TRACKED]:
            return False
        
        # Check if in trigger zone
        center_x, center_y = track.get_center()
        if not self.trigger_zone.contains_point(center_x, center_y):
            return False
        
        # Check if should classify (not exceeded max attempts)
        return self.tracker.should_classify(track.track_id)
    
    def process_frame(self, frame_bgr: np.ndarray, show_trigger_zone: Optional[bool] = None) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Process a single frame through the pipeline.
        
        Args:
            frame_bgr: Input frame in BGR format
            show_trigger_zone: Whether to show trigger zone overlay (None = use default)
        
        Returns:
            Tuple of (annotated_frame, statistics_dict)
        """
        self.frame_count += 1
        frame_start_time = time.time()
        
        # Convert to RGB
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        frame_pil = Image.fromarray(frame_rgb)
        
        # 1. Detection (with skip frame optimization)
        should_detect = (self.detection_frame_counter % (self.skip_frames + 1)) == 0
        
        if should_detect:
            # Run detection on this frame
            detections = self._detect_bottles(frame_rgb)
            self.last_detections = detections  # Store for skipped frames
        else:
            # Reuse last detection results (tracking will handle movement)
            detections = self.last_detections
        
        self.detection_frame_counter += 1
        
        # 2. Tracking
        tracks = self.tracker.update(detections)
        
        # 3. Classification trigger logic
        for track in tracks:
            if self._should_trigger_classification(track):
                # Classify bottle
                results = self._classify_bottle(frame_pil, track.bbox)
                
                if results is not None:
                    # Apply temporal smoothing if enabled
                    if self.temporal_smoother is not None:
                        results = self.temporal_smoother.smooth(track.track_id, results)
                    
                    # Classification successful
                    self.tracker.mark_classified(track.track_id, results)
                    self.cache.put(track.track_id, results)
                    self.classification_count += 1
                else:
                    # Classification failed
                    self.tracker.increment_classification_attempts(track.track_id)
        
        # 4. Render frame
        show_zone = show_trigger_zone if show_trigger_zone is not None else self.show_trigger_zone
        annotated_frame = self._render_frame(frame_bgr, tracks, show_trigger_zone=show_zone)
        
        # 5. Calculate statistics
        frame_time = time.time() - frame_start_time
        fps = 1.0 / frame_time if frame_time > 0 else 0
        self.fps_history.append(fps)
        avg_fps = sum(self.fps_history) / len(self.fps_history) if self.fps_history else 0
        
        stats = {
            'frame_count': self.frame_count,
            'active_tracks': len(tracks),
            'total_tracks': len(self.tracker.tracks),
            'classifications': self.classification_count,
            'cache_size': self.cache.get_size(),
            'cache_stats': self.cache.get_stats(),
            'fps': fps,
            'avg_fps': avg_fps,
            'frame_time_ms': frame_time * 1000
        }
        
        return annotated_frame, stats

    
    def _render_frame(
        self,
        frame: np.ndarray,
        tracks: List,
        show_trigger_zone: bool = True
    ) -> np.ndarray:
        """
        Render frame with tracking annotations.
        
        Args:
            frame: Input frame in BGR format
            tracks: List of BottleTrack objects
            show_trigger_zone: Whether to show trigger zone overlay
        
        Returns:
            Annotated frame
        """
        annotated = frame.copy()
        
        # Draw trigger zone
        if show_trigger_zone:
            annotated = self.trigger_zone.draw_overlay(
                annotated,
                color=(0, 255, 0),
                thickness=2,
                alpha=0.2
            )
        
        # Color mapping for states
        state_colors = {
            TrackingState.NEW: (255, 255, 0),      # Yellow
            TrackingState.TRACKED: (0, 255, 255),  # Cyan
            TrackingState.CLASSIFIED: (0, 255, 0), # Green
            TrackingState.FAILED: (0, 0, 255)      # Red
        }
        
        # Category colors (BGR format)
        category_colors = {
            'product': (255, 0, 0),      # Blue
            'grade': (0, 255, 0),        # Green
            'cap': (0, 0, 255),          # Red
            'label': (255, 255, 0),      # Cyan
            'brand': (255, 0, 255),      # Magenta
            'type': (0, 255, 255),       # Yellow
            'subtype': (128, 128, 255),  # Light Red
            'volume': (255, 128, 0)      # Orange
        }
        
        # Draw each track
        for track in tracks:
            x1, y1, x2, y2 = map(int, track.bbox)
            
            # Get color based on state
            color = state_colors.get(track.state, (255, 255, 255))
            
            # Draw bounding box
            thickness = 3 if track.state == TrackingState.CLASSIFIED else 2
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, thickness)
            
            # Draw track ID with background (BIGGER)
            track_text = f"ID: {track.track_id}"
            text_size = cv2.getTextSize(track_text, cv2.FONT_HERSHEY_SIMPLEX, 0.9, 2)[0]
            
            # Black background for track ID
            cv2.rectangle(
                annotated,
                (x1 - 2, y1 - text_size[1] - 12),
                (x1 + text_size[0] + 2, y1 - 2),
                (0, 0, 0),
                -1
            )
            
            cv2.putText(
                annotated,
                track_text,
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,  # Dari 0.6 → 0.9 (50% lebih besar)
                color,
                2
            )
            
            # Draw classification results or state
            if track.state == TrackingState.CLASSIFIED and track.classification_results:
                # Get cached results
                results = self.cache.get(track.track_id)
                if results is None:
                    results = track.classification_results
                
                # Draw all 8 attributes with LARGER text
                y_offset = y1 - 30
                if y_offset < 250:
                    y_offset = y2 + 30
                
                for i, (key, value) in enumerate(results.items()):
                    text = f"{key}: {value}"
                    text_color = category_colors.get(key, (255, 255, 255))
                    
                    # Draw text with black background for better visibility
                    text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)[0]
                    
                    # Draw black background rectangle
                    cv2.rectangle(
                        annotated,
                        (x1 - 2, y_offset + i * 30 - text_size[1] - 2),
                        (x1 + text_size[0] + 2, y_offset + i * 30 + 2),
                        (0, 0, 0),
                        -1
                    )
                    
                    # Draw text (BIGGER: 0.5 → 0.8, thickness: 2 → 2)
                    cv2.putText(
                        annotated,
                        text,
                        (x1, y_offset + i * 30),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8,  # Dari 0.5 → 0.8 (60% lebih besar)
                        text_color,
                        2
                    )
            
            elif track.state == TrackingState.FAILED:
                # Draw FAILED text
                cv2.putText(
                    annotated,
                    "FAILED",
                    (x1, y1 - 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 0, 255),
                    2
                )
            
            else:
                # Draw state
                state_text = track.state.value
                cv2.putText(
                    annotated,
                    state_text,
                    (x1, y1 - 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    color,
                    2
                )
        
        # Draw FPS counter (BIGGER with background)
        if self.fps_history:
            avg_fps = sum(self.fps_history) / len(self.fps_history)
            fps_text = f"FPS: {avg_fps:.1f}"
            text_size = cv2.getTextSize(fps_text, cv2.FONT_HERSHEY_SIMPLEX, 1.2, 3)[0]
            
            # Black background
            cv2.rectangle(
                annotated,
                (5, 5),
                (15 + text_size[0], 40),
                (0, 0, 0),
                -1
            )
            
            cv2.putText(
                annotated,
                fps_text,
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.2,  # Dari 1.0 → 1.2 (20% lebih besar)
                (0, 255, 0),
                3  # Dari 2 → 3 (lebih tebal)
            )
        
        # Draw statistics (BIGGER with background)
        stats_text = f"Tracks: {len(tracks)} | Classifications: {self.classification_count}"
        text_size = cv2.getTextSize(stats_text, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)[0]
        
        # Black background
        cv2.rectangle(
            annotated,
            (5, 50),
            (15 + text_size[0], 80),
            (0, 0, 0),
            -1
        )
        
        cv2.putText(
            annotated,
            stats_text,
            (10, 70),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,  # Dari 0.6 → 0.8 (33% lebih besar)
            (255, 255, 255),
            2
        )
        
        # Draw classification overlay (last step) - only if enabled
        if self.show_overlay:
            annotated = self.overlay.render(
                annotated,
                tracks,
                self.cache
            )
        
        return annotated
    
    def update_trigger_zone(self, config: TriggerZoneConfig):
        """
        Update trigger zone configuration.
        
        Args:
            config: New trigger zone configuration
        """
        self.trigger_zone.update_config(config)
    
    def toggle_trigger_zone_visibility(self):
        """Toggle trigger zone visibility."""
        self.show_trigger_zone = not self.show_trigger_zone
        return self.show_trigger_zone
    
    def set_trigger_zone_visibility(self, visible: bool):
        """
        Set trigger zone visibility.
        
        Args:
            visible: True to show, False to hide
        """
        self.show_trigger_zone = visible
    
    def reset(self):
        """Reset pipeline state."""
        self.tracker.reset()
        self.cache.clear()
        if self.temporal_smoother is not None:
            self.temporal_smoother.clear_all()
        self.frame_count = 0
        self.classification_count = 0
        self.fps_history.clear()
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get pipeline statistics.
        
        Returns:
            Dictionary with comprehensive statistics
        """
        tracker_stats = self.tracker.get_statistics()
        cache_stats = self.cache.get_stats()
        
        avg_fps = sum(self.fps_history) / len(self.fps_history) if self.fps_history else 0
        
        # Calculate reduction percentage
        if self.frame_count > 0:
            reduction_pct = (1 - self.classification_count / self.frame_count) * 100
        else:
            reduction_pct = 0
        
        return {
            'frame_count': self.frame_count,
            'classification_count': self.classification_count,
            'reduction_percentage': reduction_pct,
            'avg_fps': avg_fps,
            'tracker': tracker_stats,
            'cache': {
                'size': cache_stats.size,
                'max_size': cache_stats.max_size,
                'hits': cache_stats.hits,
                'misses': cache_stats.misses,
                'hit_rate': cache_stats.hit_rate
            }
        }
    
    def __repr__(self) -> str:
        """String representation."""
        stats = self.get_statistics()
        return (
            f"DetectionTrackingPipeline("
            f"frames={stats['frame_count']}, "
            f"classifications={stats['classification_count']}, "
            f"reduction={stats['reduction_percentage']:.1f}%, "
            f"fps={stats['avg_fps']:.1f})"
        )
