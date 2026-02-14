"""
BottleTracker class for managing bottle tracking with state management.
"""
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Any
import numpy as np
from .bytetrack import BYTETracker, STrack


class TrackingState(Enum):
    """State of a tracked bottle."""
    NEW = "NEW"                    # Just detected, not yet classified
    TRACKED = "TRACKED"            # Being tracked, waiting for trigger
    CLASSIFIED = "CLASSIFIED"      # Successfully classified
    FAILED = "FAILED"              # Classification failed after max attempts


@dataclass
class BottleTrack:
    """
    Represents a tracked bottle with state and classification results.
    """
    track_id: int
    bbox: np.ndarray  # [x1, y1, x2, y2]
    confidence: float
    state: TrackingState = TrackingState.NEW
    frames_since_update: int = 0
    classification_results: Optional[Dict[str, str]] = None
    classification_attempts: int = 0
    
    def get_center(self) -> Tuple[float, float]:
        """
        Get center point of bounding box.
        
        Returns:
            Tuple of (center_x, center_y)
        """
        x1, y1, x2, y2 = self.bbox
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2
        return (center_x, center_y)
    
    def get_area(self) -> float:
        """
        Get area of bounding box.
        
        Returns:
            Area in square pixels
        """
        x1, y1, x2, y2 = self.bbox
        width = x2 - x1
        height = y2 - y1
        return width * height
    
    def __repr__(self) -> str:
        """String representation."""
        center_x, center_y = self.get_center()
        return (
            f"BottleTrack(id={self.track_id}, "
            f"state={self.state.value}, "
            f"center=({center_x:.1f},{center_y:.1f}), "
            f"conf={self.confidence:.2f}, "
            f"attempts={self.classification_attempts})"
        )


class BottleTracker:
    """
    High-level tracker for bottles with state management.
    
    Wraps ByteTrack and adds:
    - State management (NEW, TRACKED, CLASSIFIED, FAILED)
    - Classification attempt tracking
    - Maximum retry logic
    - Track capacity limits
    """
    
    def __init__(
        self,
        max_age: int = 30,
        min_hits: int = 1,
        iou_threshold: float = 0.3,
        max_classification_attempts: int = 2,
        max_tracks: int = 20,
        track_thresh: float = 0.5
    ):
        """
        Initialize bottle tracker.
        
        Args:
            max_age: Maximum frames to keep lost tracks
            min_hits: Minimum hits to confirm track
            iou_threshold: IoU threshold for matching
            max_classification_attempts: Maximum classification retries
            max_tracks: Maximum number of simultaneous tracks
            track_thresh: Confidence threshold for tracking
        """
        self.max_age = max_age
        self.min_hits = min_hits
        self.iou_threshold = iou_threshold
        self.max_classification_attempts = max_classification_attempts
        self.max_tracks = max_tracks
        self.track_thresh = track_thresh
        
        # Initialize ByteTrack
        self.byte_tracker = BYTETracker(
            track_thresh=track_thresh,
            track_buffer=max_age,
            match_thresh=iou_threshold,
            frame_rate=30
        )
        
        # Track management
        self.tracks: Dict[int, BottleTrack] = {}
        self.frame_count = 0
    
    def update(self, detections: np.ndarray) -> List[BottleTrack]:
        """
        Update tracker with new detections.
        
        Args:
            detections: Array of shape (N, 5) with format [x1, y1, x2, y2, score]
        
        Returns:
            List of active BottleTrack objects
        """
        self.frame_count += 1
        
        # Update ByteTrack
        stracks = self.byte_tracker.update(detections)
        
        # Track IDs from current frame
        current_track_ids = set()
        
        # Update or create BottleTrack objects
        for strack in stracks:
            track_id = strack.track_id
            current_track_ids.add(track_id)
            
            if track_id in self.tracks:
                # Update existing track
                bottle_track = self.tracks[track_id]
                bottle_track.bbox = strack.tlbr
                bottle_track.confidence = strack.score
                bottle_track.frames_since_update = 0
                
                # Update state: NEW -> TRACKED if not yet classified
                if bottle_track.state == TrackingState.NEW:
                    bottle_track.state = TrackingState.TRACKED
            else:
                # Create new track
                bottle_track = BottleTrack(
                    track_id=track_id,
                    bbox=strack.tlbr,
                    confidence=strack.score,
                    state=TrackingState.NEW,
                    frames_since_update=0
                )
                self.tracks[track_id] = bottle_track
        
        # Update frames_since_update for tracks not in current frame
        tracks_to_remove = []
        for track_id, bottle_track in self.tracks.items():
            if track_id not in current_track_ids:
                bottle_track.frames_since_update += 1
                
                # Remove tracks that exceed max_age
                if bottle_track.frames_since_update > self.max_age:
                    tracks_to_remove.append(track_id)
        
        # Remove old tracks
        for track_id in tracks_to_remove:
            del self.tracks[track_id]
        
        # Enforce max_tracks limit
        if len(self.tracks) > self.max_tracks:
            self._enforce_track_limit()
        
        # Return active tracks (frames_since_update == 0)
        active_tracks = [
            track for track in self.tracks.values()
            if track.frames_since_update == 0
        ]
        
        return active_tracks
    
    def _enforce_track_limit(self):
        """
        Enforce maximum track limit by removing lowest confidence tracks.
        """
        # Sort tracks by confidence (descending)
        sorted_tracks = sorted(
            self.tracks.items(),
            key=lambda x: x[1].confidence,
            reverse=True
        )
        
        # Keep only top max_tracks
        tracks_to_keep = dict(sorted_tracks[:self.max_tracks])
        self.tracks = tracks_to_keep
    
    def get_track_by_id(self, track_id: int) -> Optional[BottleTrack]:
        """
        Get track by ID.
        
        Args:
            track_id: Track ID
        
        Returns:
            BottleTrack or None if not found
        """
        return self.tracks.get(track_id)
    
    def remove_track(self, track_id: int) -> bool:
        """
        Remove track by ID.
        
        Args:
            track_id: Track ID to remove
        
        Returns:
            True if removed, False if not found
        """
        if track_id in self.tracks:
            del self.tracks[track_id]
            return True
        return False
    
    def get_active_count(self) -> int:
        """
        Get count of active tracks (frames_since_update == 0).
        
        Returns:
            Number of active tracks
        """
        return sum(1 for track in self.tracks.values() if track.frames_since_update == 0)
    
    def get_all_tracks(self) -> List[BottleTrack]:
        """
        Get all tracks (including lost ones).
        
        Returns:
            List of all BottleTrack objects
        """
        return list(self.tracks.values())
    
    def get_active_tracks(self) -> List[BottleTrack]:
        """
        Get only active tracks (frames_since_update == 0).
        
        Returns:
            List of active BottleTrack objects
        """
        return [track for track in self.tracks.values() if track.frames_since_update == 0]
    
    def mark_classified(
        self,
        track_id: int,
        classification_results: Dict[str, str]
    ) -> bool:
        """
        Mark track as classified with results.
        
        Args:
            track_id: Track ID
            classification_results: Classification results dict
        
        Returns:
            True if successful, False if track not found
        """
        track = self.get_track_by_id(track_id)
        if track is None:
            return False
        
        track.state = TrackingState.CLASSIFIED
        track.classification_results = classification_results
        return True
    
    def mark_failed(self, track_id: int) -> bool:
        """
        Mark track as failed (classification failed after max attempts).
        
        Args:
            track_id: Track ID
        
        Returns:
            True if successful, False if track not found
        """
        track = self.get_track_by_id(track_id)
        if track is None:
            return False
        
        track.state = TrackingState.FAILED
        return True
    
    def increment_classification_attempts(self, track_id: int) -> bool:
        """
        Increment classification attempts counter.
        
        Args:
            track_id: Track ID
        
        Returns:
            True if successful, False if track not found
        """
        track = self.get_track_by_id(track_id)
        if track is None:
            return False
        
        track.classification_attempts += 1
        
        # Auto-mark as FAILED if max attempts reached
        if track.classification_attempts >= self.max_classification_attempts:
            track.state = TrackingState.FAILED
        
        return True
    
    def should_classify(self, track_id: int) -> bool:
        """
        Check if track should be classified.
        
        Args:
            track_id: Track ID
        
        Returns:
            True if should classify, False otherwise
        """
        track = self.get_track_by_id(track_id)
        if track is None:
            return False
        
        # Only classify NEW or TRACKED bottles that haven't reached max attempts
        if track.state in [TrackingState.NEW, TrackingState.TRACKED]:
            if track.classification_attempts < self.max_classification_attempts:
                return True
        
        return False
    
    def reset(self):
        """Reset tracker state."""
        self.tracks.clear()
        self.byte_tracker.reset()
        self.frame_count = 0
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get tracker statistics.
        
        Returns:
            Dictionary with statistics
        """
        state_counts = {
            TrackingState.NEW: 0,
            TrackingState.TRACKED: 0,
            TrackingState.CLASSIFIED: 0,
            TrackingState.FAILED: 0
        }
        
        for track in self.tracks.values():
            state_counts[track.state] += 1
        
        return {
            'total_tracks': len(self.tracks),
            'active_tracks': self.get_active_count(),
            'new_tracks': state_counts[TrackingState.NEW],
            'tracked': state_counts[TrackingState.TRACKED],
            'classified': state_counts[TrackingState.CLASSIFIED],
            'failed': state_counts[TrackingState.FAILED],
            'frame_count': self.frame_count
        }
    
    def __repr__(self) -> str:
        """String representation."""
        stats = self.get_statistics()
        return (
            f"BottleTracker(tracks={stats['total_tracks']}, "
            f"active={stats['active_tracks']}, "
            f"classified={stats['classified']}, "
            f"failed={stats['failed']})"
        )
