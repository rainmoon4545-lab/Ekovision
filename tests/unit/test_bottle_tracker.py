"""
Unit tests for BottleTracker class.
"""
import numpy as np
import pytest
from src.tracking.bottle_tracker import (
    BottleTracker, BottleTrack, TrackingState
)


class TestTrackingState:
    """Tests for TrackingState enum."""
    
    def test_state_values(self):
        """Test state enum values."""
        assert TrackingState.NEW.value == "NEW"
        assert TrackingState.TRACKED.value == "TRACKED"
        assert TrackingState.CLASSIFIED.value == "CLASSIFIED"
        assert TrackingState.FAILED.value == "FAILED"


class TestBottleTrack:
    """Tests for BottleTrack dataclass."""
    
    def test_initialization(self):
        """Test bottle track initialization."""
        bbox = np.array([10, 20, 30, 40])
        track = BottleTrack(
            track_id=1,
            bbox=bbox,
            confidence=0.9
        )
        
        assert track.track_id == 1
        assert np.array_equal(track.bbox, bbox)
        assert track.confidence == 0.9
        assert track.state == TrackingState.NEW
        assert track.frames_since_update == 0
        assert track.classification_results is None
        assert track.classification_attempts == 0
    
    def test_get_center(self):
        """Test getting center point."""
        bbox = np.array([10, 20, 30, 40])
        track = BottleTrack(track_id=1, bbox=bbox, confidence=0.9)
        
        center_x, center_y = track.get_center()
        
        assert center_x == 20.0  # (10 + 30) / 2
        assert center_y == 30.0  # (20 + 40) / 2
    
    def test_get_area(self):
        """Test getting bounding box area."""
        bbox = np.array([10, 20, 30, 50])
        track = BottleTrack(track_id=1, bbox=bbox, confidence=0.9)
        
        area = track.get_area()
        
        assert area == 600.0  # (30-10) * (50-20) = 20 * 30
    
    def test_repr(self):
        """Test string representation."""
        bbox = np.array([10, 20, 30, 40])
        track = BottleTrack(track_id=1, bbox=bbox, confidence=0.9)
        
        repr_str = repr(track)
        
        assert "BottleTrack" in repr_str
        assert "id=1" in repr_str
        assert "NEW" in repr_str


class TestBottleTracker:
    """Tests for BottleTracker class."""
    
    def test_initialization(self):
        """Test tracker initialization."""
        tracker = BottleTracker()
        
        assert tracker.max_age == 30
        assert tracker.max_classification_attempts == 2
        assert tracker.max_tracks == 20
        assert len(tracker.tracks) == 0
        assert tracker.frame_count == 0
    
    def test_first_detection_assigns_id(self):
        """Test first detection assigns track ID."""
        tracker = BottleTracker(track_thresh=0.5)
        detections = np.array([[10, 20, 30, 40, 0.9]])
        
        tracks = tracker.update(detections)
        
        assert len(tracks) == 1
        assert tracks[0].track_id is not None
        assert tracks[0].state == TrackingState.NEW
    
    def test_empty_detections(self):
        """Test tracker with empty detections."""
        tracker = BottleTracker()
        detections = np.array([]).reshape(0, 5)
        
        tracks = tracker.update(detections)
        
        assert len(tracks) == 0
    
    def test_state_transition_new_to_tracked(self):
        """Test state transitions from NEW to TRACKED."""
        tracker = BottleTracker(track_thresh=0.5)
        
        # Frame 1: Initial detection (NEW)
        detections1 = np.array([[10, 20, 30, 40, 0.9]])
        tracks1 = tracker.update(detections1)
        assert tracks1[0].state == TrackingState.NEW
        track_id = tracks1[0].track_id
        
        # Frame 2: Same detection (should be TRACKED)
        detections2 = np.array([[11, 21, 31, 41, 0.9]])
        tracks2 = tracker.update(detections2)
        assert len(tracks2) == 1
        assert tracks2[0].track_id == track_id
        assert tracks2[0].state == TrackingState.TRACKED
    
    def test_track_removal_after_max_age(self):
        """Test track removal after exceeding max_age."""
        tracker = BottleTracker(max_age=2, track_thresh=0.5)
        
        # Frame 1: Initial detection
        detections1 = np.array([[10, 20, 30, 40, 0.9]])
        tracker.update(detections1)
        assert len(tracker.tracks) == 1
        
        # Frames 2-4: No detections (track should be removed after frame 4)
        for _ in range(3):
            tracker.update(np.array([]).reshape(0, 5))
        
        assert len(tracker.tracks) == 0
    
    def test_get_track_by_id(self):
        """Test getting track by ID."""
        tracker = BottleTracker(track_thresh=0.5)
        detections = np.array([[10, 20, 30, 40, 0.9]])
        tracks = tracker.update(detections)
        track_id = tracks[0].track_id
        
        retrieved_track = tracker.get_track_by_id(track_id)
        
        assert retrieved_track is not None
        assert retrieved_track.track_id == track_id
    
    def test_get_track_by_id_not_found(self):
        """Test getting non-existent track returns None."""
        tracker = BottleTracker()
        
        retrieved_track = tracker.get_track_by_id(999)
        
        assert retrieved_track is None
    
    def test_remove_track(self):
        """Test removing track by ID."""
        tracker = BottleTracker(track_thresh=0.5)
        detections = np.array([[10, 20, 30, 40, 0.9]])
        tracks = tracker.update(detections)
        track_id = tracks[0].track_id
        
        result = tracker.remove_track(track_id)
        
        assert result is True
        assert len(tracker.tracks) == 0
    
    def test_remove_track_not_found(self):
        """Test removing non-existent track returns False."""
        tracker = BottleTracker()
        
        result = tracker.remove_track(999)
        
        assert result is False
    
    def test_get_active_count(self):
        """Test getting active track count."""
        tracker = BottleTracker(track_thresh=0.5)
        detections = np.array([
            [10, 20, 30, 40, 0.9],
            [50, 60, 70, 80, 0.85]
        ])
        tracker.update(detections)
        
        active_count = tracker.get_active_count()
        
        assert active_count == 2
    
    def test_mark_classified(self):
        """Test marking track as classified."""
        tracker = BottleTracker(track_thresh=0.5)
        detections = np.array([[10, 20, 30, 40, 0.9]])
        tracks = tracker.update(detections)
        track_id = tracks[0].track_id
        
        results = {'product': 'Aqua', 'volume': '600ml'}
        success = tracker.mark_classified(track_id, results)
        
        assert success is True
        track = tracker.get_track_by_id(track_id)
        assert track.state == TrackingState.CLASSIFIED
        assert track.classification_results == results
    
    def test_mark_failed(self):
        """Test marking track as failed."""
        tracker = BottleTracker(track_thresh=0.5)
        detections = np.array([[10, 20, 30, 40, 0.9]])
        tracks = tracker.update(detections)
        track_id = tracks[0].track_id
        
        success = tracker.mark_failed(track_id)
        
        assert success is True
        track = tracker.get_track_by_id(track_id)
        assert track.state == TrackingState.FAILED
    
    def test_increment_classification_attempts(self):
        """Test incrementing classification attempts."""
        tracker = BottleTracker(track_thresh=0.5, max_classification_attempts=2)
        detections = np.array([[10, 20, 30, 40, 0.9]])
        tracks = tracker.update(detections)
        track_id = tracks[0].track_id
        
        # First attempt
        tracker.increment_classification_attempts(track_id)
        track = tracker.get_track_by_id(track_id)
        assert track.classification_attempts == 1
        assert track.state != TrackingState.FAILED
        
        # Second attempt (should auto-mark as FAILED)
        tracker.increment_classification_attempts(track_id)
        track = tracker.get_track_by_id(track_id)
        assert track.classification_attempts == 2
        assert track.state == TrackingState.FAILED
    
    def test_should_classify_new_track(self):
        """Test should_classify returns True for NEW track."""
        tracker = BottleTracker(track_thresh=0.5)
        detections = np.array([[10, 20, 30, 40, 0.9]])
        tracks = tracker.update(detections)
        track_id = tracks[0].track_id
        
        should_classify = tracker.should_classify(track_id)
        
        assert should_classify is True
    
    def test_should_classify_classified_track(self):
        """Test should_classify returns False for CLASSIFIED track."""
        tracker = BottleTracker(track_thresh=0.5)
        detections = np.array([[10, 20, 30, 40, 0.9]])
        tracks = tracker.update(detections)
        track_id = tracks[0].track_id
        
        tracker.mark_classified(track_id, {'product': 'Aqua'})
        should_classify = tracker.should_classify(track_id)
        
        assert should_classify is False
    
    def test_should_classify_failed_track(self):
        """Test should_classify returns False for FAILED track."""
        tracker = BottleTracker(track_thresh=0.5)
        detections = np.array([[10, 20, 30, 40, 0.9]])
        tracks = tracker.update(detections)
        track_id = tracks[0].track_id
        
        tracker.mark_failed(track_id)
        should_classify = tracker.should_classify(track_id)
        
        assert should_classify is False
    
    def test_should_classify_max_attempts_reached(self):
        """Test should_classify returns False after max attempts."""
        tracker = BottleTracker(track_thresh=0.5, max_classification_attempts=2)
        detections = np.array([[10, 20, 30, 40, 0.9]])
        tracks = tracker.update(detections)
        track_id = tracks[0].track_id
        
        # Reach max attempts
        tracker.increment_classification_attempts(track_id)
        tracker.increment_classification_attempts(track_id)
        
        should_classify = tracker.should_classify(track_id)
        
        assert should_classify is False
    
    def test_maximum_tracks_limit(self):
        """Test maximum tracks limit enforcement."""
        tracker = BottleTracker(max_tracks=3, track_thresh=0.5)
        
        # Add 5 detections with varying confidence
        detections = np.array([
            [10, 20, 30, 40, 0.95],   # Highest
            [50, 60, 70, 80, 0.90],
            [100, 110, 120, 130, 0.85],
            [150, 160, 170, 180, 0.80],
            [200, 210, 220, 230, 0.75]  # Lowest
        ])
        tracker.update(detections)
        
        # Should keep only 3 highest confidence tracks
        assert len(tracker.tracks) == 3
        
        # Verify highest confidence tracks are kept
        confidences = [track.confidence for track in tracker.tracks.values()]
        assert min(confidences) >= 0.85
    
    def test_reset(self):
        """Test tracker reset."""
        tracker = BottleTracker(track_thresh=0.5)
        detections = np.array([[10, 20, 30, 40, 0.9]])
        tracker.update(detections)
        
        tracker.reset()
        
        assert len(tracker.tracks) == 0
        assert tracker.frame_count == 0
    
    def test_get_statistics(self):
        """Test getting tracker statistics."""
        tracker = BottleTracker(track_thresh=0.5)
        detections = np.array([
            [10, 20, 30, 40, 0.9],
            [50, 60, 70, 80, 0.85]
        ])
        tracks = tracker.update(detections)
        
        # Mark one as classified
        tracker.mark_classified(tracks[0].track_id, {'product': 'Aqua'})
        
        stats = tracker.get_statistics()
        
        assert stats['total_tracks'] == 2
        assert stats['active_tracks'] == 2
        assert stats['classified'] == 1
        assert stats['new_tracks'] == 1
        assert stats['frame_count'] == 1
    
    def test_multiple_detections(self):
        """Test tracker with multiple detections."""
        tracker = BottleTracker(track_thresh=0.5)
        detections = np.array([
            [10, 20, 30, 40, 0.9],
            [50, 60, 70, 80, 0.85],
            [100, 110, 120, 130, 0.95]
        ])
        
        tracks = tracker.update(detections)
        
        assert len(tracks) == 3
        track_ids = [t.track_id for t in tracks]
        assert len(set(track_ids)) == 3  # All unique IDs
    
    def test_repr(self):
        """Test string representation."""
        tracker = BottleTracker(track_thresh=0.5)
        detections = np.array([[10, 20, 30, 40, 0.9]])
        tracker.update(detections)
        
        repr_str = repr(tracker)
        
        assert "BottleTracker" in repr_str
        assert "tracks=1" in repr_str
