"""
Unit tests for ByteTrack implementation.
"""
import numpy as np
import pytest
from src.tracking.bytetrack import BYTETracker, STrack, iou_batch, linear_assignment


class TestIoUBatch:
    """Tests for IoU calculation."""
    
    def test_iou_identical_boxes(self):
        """Test IoU of identical boxes should be 1.0."""
        boxes1 = np.array([[0, 0, 10, 10]])
        boxes2 = np.array([[0, 0, 10, 10]])
        iou = iou_batch(boxes1, boxes2)
        assert iou[0, 0] == pytest.approx(1.0)
    
    def test_iou_no_overlap(self):
        """Test IoU of non-overlapping boxes should be 0.0."""
        boxes1 = np.array([[0, 0, 10, 10]])
        boxes2 = np.array([[20, 20, 30, 30]])
        iou = iou_batch(boxes1, boxes2)
        assert iou[0, 0] == pytest.approx(0.0)
    
    def test_iou_partial_overlap(self):
        """Test IoU of partially overlapping boxes."""
        boxes1 = np.array([[0, 0, 10, 10]])
        boxes2 = np.array([[5, 5, 15, 15]])
        iou = iou_batch(boxes1, boxes2)
        # Intersection: 5x5 = 25, Union: 100 + 100 - 25 = 175
        expected_iou = 25 / 175
        assert iou[0, 0] == pytest.approx(expected_iou, rel=1e-5)
    
    def test_iou_empty_input(self):
        """Test IoU with empty input."""
        boxes1 = np.array([]).reshape(0, 4)
        boxes2 = np.array([[0, 0, 10, 10]])
        iou = iou_batch(boxes1, boxes2)
        assert iou.shape == (0, 1)


class TestLinearAssignment:
    """Tests for linear assignment."""
    
    def test_perfect_match(self):
        """Test perfect matching with low cost."""
        cost_matrix = np.array([[0.1, 0.9], [0.9, 0.1]])
        matches, u_a, u_b = linear_assignment(cost_matrix, thresh=0.5)
        assert len(matches) == 2
        assert len(u_a) == 0
        assert len(u_b) == 0
    
    def test_no_match_high_threshold(self):
        """Test no matching when all costs exceed threshold."""
        cost_matrix = np.array([[0.9, 0.9], [0.9, 0.9]])
        matches, u_a, u_b = linear_assignment(cost_matrix, thresh=0.5)
        assert len(matches) == 0
        assert len(u_a) == 2
        assert len(u_b) == 2
    
    def test_partial_match(self):
        """Test partial matching."""
        cost_matrix = np.array([[0.1, 0.9, 0.9], [0.9, 0.2, 0.9]])
        matches, u_a, u_b = linear_assignment(cost_matrix, thresh=0.5)
        assert len(matches) == 2
        assert len(u_b) == 1


class TestSTrack:
    """Tests for STrack class."""
    
    def test_track_initialization(self):
        """Test track initialization."""
        bbox = np.array([10, 20, 30, 40])
        score = 0.9
        track = STrack(bbox, score)
        assert np.array_equal(track.tlbr, bbox)
        assert track.score == score
        assert track.track_id is None
        assert not track.is_activated
    
    def test_track_activation(self):
        """Test track activation assigns ID."""
        track = STrack(np.array([10, 20, 30, 40]), 0.9)
        track.activate(frame_id=1)
        assert track.track_id is not None
        assert track.is_activated
        assert track.frame_id == 1
    
    def test_track_update(self):
        """Test track update."""
        track1 = STrack(np.array([10, 20, 30, 40]), 0.9)
        track1.activate(frame_id=1)
        
        track2 = STrack(np.array([12, 22, 32, 42]), 0.85)
        track1.update(track2, frame_id=2)
        
        assert np.array_equal(track1.tlbr, track2.tlbr)
        assert track1.score == track2.score
        assert track1.frame_id == 2
        assert track1.tracklet_len == 1


class TestBYTETracker:
    """Tests for BYTETracker class."""
    
    def test_tracker_initialization(self):
        """Test tracker initialization."""
        tracker = BYTETracker()
        assert tracker.frame_id == 0
        assert len(tracker.tracked_stracks) == 0
    
    def test_first_detection_assigns_id(self):
        """Test first detection assigns track ID."""
        tracker = BYTETracker(track_thresh=0.5)
        detections = np.array([[10, 20, 30, 40, 0.9]])
        
        tracks = tracker.update(detections)
        
        assert len(tracks) == 1
        assert tracks[0].track_id is not None
        assert tracks[0].is_activated
    
    def test_empty_detections(self):
        """Test tracker with empty detections."""
        tracker = BYTETracker()
        detections = np.array([]).reshape(0, 5)
        
        tracks = tracker.update(detections)
        
        assert len(tracks) == 0
    
    def test_track_persistence(self):
        """Test track persists across frames."""
        tracker = BYTETracker(track_thresh=0.5, match_thresh=0.8)
        
        # Frame 1: Initial detection
        detections1 = np.array([[10, 20, 30, 40, 0.9]])
        tracks1 = tracker.update(detections1)
        track_id = tracks1[0].track_id
        
        # Frame 2: Similar detection (should match)
        detections2 = np.array([[11, 21, 31, 41, 0.9]])
        tracks2 = tracker.update(detections2)
        
        assert len(tracks2) == 1
        assert tracks2[0].track_id == track_id
    
    def test_low_confidence_filtered(self):
        """Test low confidence detections are filtered."""
        tracker = BYTETracker(track_thresh=0.5)
        detections = np.array([[10, 20, 30, 40, 0.3]])  # Below threshold
        
        tracks = tracker.update(detections)
        
        assert len(tracks) == 0
    
    def test_tracker_reset(self):
        """Test tracker reset clears state."""
        tracker = BYTETracker(track_thresh=0.5)
        detections = np.array([[10, 20, 30, 40, 0.9]])
        tracker.update(detections)
        
        tracker.reset()
        
        assert tracker.frame_id == 0
        assert len(tracker.tracked_stracks) == 0
        assert len(tracker.lost_stracks) == 0
    
    def test_multiple_detections(self):
        """Test tracker with multiple detections."""
        tracker = BYTETracker(track_thresh=0.5)
        detections = np.array([
            [10, 20, 30, 40, 0.9],
            [50, 60, 70, 80, 0.85],
            [100, 110, 120, 130, 0.95]
        ])
        
        tracks = tracker.update(detections)
        
        assert len(tracks) == 3
        track_ids = [t.track_id for t in tracks]
        assert len(set(track_ids)) == 3  # All unique IDs
