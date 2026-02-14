"""
Pure Python implementation of ByteTrack algorithm.
Simplified version without C++ dependencies (cython-bbox, lap).

Based on ByteTrack paper: https://arxiv.org/abs/2110.06864
"""
import numpy as np
from collections import OrderedDict
from typing import List, Tuple, Optional


def iou_batch(bboxes1: np.ndarray, bboxes2: np.ndarray) -> np.ndarray:
    """
    Calculate IoU between two sets of bounding boxes.
    
    Args:
        bboxes1: Array of shape (N, 4) in format [x1, y1, x2, y2]
        bboxes2: Array of shape (M, 4) in format [x1, y1, x2, y2]
    
    Returns:
        IoU matrix of shape (N, M)
    """
    if len(bboxes1) == 0 or len(bboxes2) == 0:
        return np.zeros((len(bboxes1), len(bboxes2)))
    
    # Calculate intersection
    x1 = np.maximum(bboxes1[:, None, 0], bboxes2[None, :, 0])
    y1 = np.maximum(bboxes1[:, None, 1], bboxes2[None, :, 1])
    x2 = np.minimum(bboxes1[:, None, 2], bboxes2[None, :, 2])
    y2 = np.minimum(bboxes1[:, None, 3], bboxes2[None, :, 3])
    
    intersection = np.maximum(0, x2 - x1) * np.maximum(0, y2 - y1)
    
    # Calculate areas
    area1 = (bboxes1[:, 2] - bboxes1[:, 0]) * (bboxes1[:, 3] - bboxes1[:, 1])
    area2 = (bboxes2[:, 2] - bboxes2[:, 0]) * (bboxes2[:, 3] - bboxes2[:, 1])
    
    # Calculate union
    union = area1[:, None] + area2[None, :] - intersection
    
    # Calculate IoU
    iou = intersection / np.maximum(union, 1e-6)
    
    return iou


def linear_assignment(cost_matrix: np.ndarray, thresh: float) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Simple greedy matching algorithm (replacement for scipy.optimize.linear_sum_assignment).
    
    Args:
        cost_matrix: Cost matrix of shape (N, M)
        thresh: Threshold for valid matches
    
    Returns:
        Tuple of (matches, unmatched_a, unmatched_b)
        - matches: Array of shape (K, 2) with matched indices
        - unmatched_a: Array of unmatched indices from first set
        - unmatched_b: Array of unmatched indices from second set
    """
    if cost_matrix.size == 0:
        return np.empty((0, 2), dtype=int), np.arange(cost_matrix.shape[0]), np.arange(cost_matrix.shape[1])
    
    matches = []
    unmatched_a = list(range(cost_matrix.shape[0]))
    unmatched_b = list(range(cost_matrix.shape[1]))
    
    # Greedy matching: find best match iteratively
    cost_copy = cost_matrix.copy()
    while True:
        # Find minimum cost
        if cost_copy.size == 0:
            break
        
        min_val = cost_copy.min()
        if min_val > thresh:
            break
        
        # Find indices of minimum
        min_idx = np.unravel_index(cost_copy.argmin(), cost_copy.shape)
        i, j = min_idx
        
        # Get original indices
        orig_i = unmatched_a[i]
        orig_j = unmatched_b[j]
        
        matches.append([orig_i, orig_j])
        
        # Remove matched row and column
        cost_copy = np.delete(cost_copy, i, axis=0)
        cost_copy = np.delete(cost_copy, j, axis=1)
        unmatched_a.pop(i)
        unmatched_b.pop(j)
    
    matches = np.array(matches) if matches else np.empty((0, 2), dtype=int)
    unmatched_a = np.array(unmatched_a)
    unmatched_b = np.array(unmatched_b)
    
    return matches, unmatched_a, unmatched_b


class STrack:
    """Single object track."""
    
    _count = 0
    
    def __init__(self, tlbr: np.ndarray, score: float):
        """
        Initialize track.
        
        Args:
            tlbr: Bounding box in format [x1, y1, x2, y2]
            score: Detection confidence score
        """
        self.tlbr = np.asarray(tlbr, dtype=np.float32)
        self.score = score
        self.track_id = None
        self.is_activated = False
        self.tracklet_len = 0
        self.frame_id = 0
        self.start_frame = 0
    
    def activate(self, frame_id: int):
        """Activate a new track."""
        self.track_id = self.next_id()
        self.tracklet_len = 0
        self.frame_id = frame_id
        self.start_frame = frame_id
        self.is_activated = True
    
    def re_activate(self, new_track: 'STrack', frame_id: int):
        """Reactivate a lost track."""
        self.tlbr = new_track.tlbr
        self.score = new_track.score
        self.tracklet_len = 0
        self.frame_id = frame_id
        self.is_activated = True
    
    def update(self, new_track: 'STrack', frame_id: int):
        """Update track with new detection."""
        self.tlbr = new_track.tlbr
        self.score = new_track.score
        self.tracklet_len += 1
        self.frame_id = frame_id
        self.is_activated = True
    
    def mark_lost(self):
        """Mark track as lost."""
        self.is_activated = False
    
    def mark_removed(self):
        """Mark track as removed."""
        self.is_activated = False
    
    @staticmethod
    def next_id():
        """Get next track ID."""
        STrack._count += 1
        return STrack._count
    
    @staticmethod
    def reset_id():
        """Reset track ID counter."""
        STrack._count = 0


class BYTETracker:
    """
    ByteTrack multi-object tracker.
    Pure Python implementation without C++ dependencies.
    """
    
    def __init__(
        self,
        track_thresh: float = 0.5,
        track_buffer: int = 30,
        match_thresh: float = 0.8,
        frame_rate: int = 30
    ):
        """
        Initialize ByteTrack tracker.
        
        Args:
            track_thresh: Detection confidence threshold for high-confidence detections
            track_buffer: Number of frames to keep lost tracks
            match_thresh: IoU threshold for matching
            frame_rate: Frame rate of video (not used in this simplified version)
        """
        self.track_thresh = track_thresh
        self.track_buffer = track_buffer
        self.match_thresh = match_thresh
        self.frame_rate = frame_rate
        
        self.tracked_stracks: List[STrack] = []
        self.lost_stracks: List[STrack] = []
        self.removed_stracks: List[STrack] = []
        
        self.frame_id = 0
    
    def update(self, detections: np.ndarray) -> List[STrack]:
        """
        Update tracker with new detections.
        
        Args:
            detections: Array of shape (N, 5) with format [x1, y1, x2, y2, score]
        
        Returns:
            List of active tracks
        """
        self.frame_id += 1
        activated_stracks = []
        refind_stracks = []
        lost_stracks = []
        removed_stracks = []
        
        if len(detections) == 0:
            # No detections, mark all tracks as lost
            for track in self.tracked_stracks:
                track.mark_lost()
                lost_stracks.append(track)
            
            self.tracked_stracks = []
            self.lost_stracks = lost_stracks
            return []
        
        # Separate high and low confidence detections
        scores = detections[:, 4]
        remain_inds = scores > self.track_thresh
        inds_low = scores > 0.1
        inds_high = scores > self.track_thresh
        
        dets = detections[inds_high]
        dets_low = detections[inds_low & ~inds_high]
        
        # Create new tracks from detections
        detections_high = [STrack(det[:4], det[4]) for det in dets]
        detections_low = [STrack(det[:4], det[4]) for det in dets_low]
        
        # Match with tracked tracks
        unconfirmed = []
        tracked_stracks = []
        for track in self.tracked_stracks:
            if not track.is_activated:
                unconfirmed.append(track)
            else:
                tracked_stracks.append(track)
        
        # First association with high score detections
        strack_pool = tracked_stracks
        matches, u_track, u_detection = self._match(strack_pool, detections_high)
        
        for itracked, idet in matches:
            track = strack_pool[itracked]
            det = detections_high[idet]
            track.update(det, self.frame_id)
            activated_stracks.append(track)
        
        # Second association with low score detections
        detections_left = [detections_high[i] for i in u_detection]
        r_tracked_stracks = [strack_pool[i] for i in u_track]
        
        matches, u_track, u_detection_second = self._match(r_tracked_stracks, detections_low)
        
        for itracked, idet in matches:
            track = r_tracked_stracks[itracked]
            det = detections_low[idet]
            track.update(det, self.frame_id)
            activated_stracks.append(track)
        
        # Mark unmatched tracks as lost
        for it in u_track:
            track = r_tracked_stracks[it]
            track.mark_lost()
            lost_stracks.append(track)
        
        # Deal with unconfirmed tracks
        detections_left = [detections_high[i] for i in u_detection]
        matches, u_unconfirmed, u_detection = self._match(unconfirmed, detections_left)
        
        for itracked, idet in matches:
            track = unconfirmed[itracked]
            det = detections_left[idet]
            track.update(det, self.frame_id)
            activated_stracks.append(track)
        
        for it in u_unconfirmed:
            track = unconfirmed[it]
            track.mark_removed()
            removed_stracks.append(track)
        
        # Initialize new tracks
        for inew in u_detection:
            track = detections_left[inew]
            if track.score < self.track_thresh:
                continue
            track.activate(self.frame_id)
            activated_stracks.append(track)
        
        # Update lost tracks
        for track in self.lost_stracks:
            if self.frame_id - track.frame_id > self.track_buffer:
                track.mark_removed()
                removed_stracks.append(track)
        
        # Merge lists
        self.tracked_stracks = [t for t in activated_stracks if t.is_activated]
        self.lost_stracks = [t for t in lost_stracks if t not in removed_stracks]
        self.removed_stracks.extend(removed_stracks)
        
        return self.tracked_stracks
    
    def _match(self, tracks: List[STrack], detections: List[STrack]) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Match tracks with detections using IoU.
        
        Args:
            tracks: List of tracks
            detections: List of detections
        
        Returns:
            Tuple of (matches, unmatched_tracks, unmatched_detections)
        """
        if len(tracks) == 0 or len(detections) == 0:
            return np.empty((0, 2), dtype=int), np.arange(len(tracks)), np.arange(len(detections))
        
        # Calculate IoU matrix
        track_boxes = np.array([t.tlbr for t in tracks])
        det_boxes = np.array([d.tlbr for d in detections])
        
        iou_matrix = iou_batch(track_boxes, det_boxes)
        
        # Convert IoU to cost (1 - IoU)
        cost_matrix = 1 - iou_matrix
        
        # Perform matching
        matches, u_track, u_detection = linear_assignment(cost_matrix, 1 - self.match_thresh)
        
        return matches, u_track, u_detection
    
    def reset(self):
        """Reset tracker state."""
        self.tracked_stracks = []
        self.lost_stracks = []
        self.removed_stracks = []
        self.frame_id = 0
        STrack.reset_id()
