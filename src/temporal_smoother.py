"""
Temporal Smoothing Module for EkoVision

Smooths classification results across frames to reduce flickering and improve stability.
"""
from typing import Dict, List, Optional
from collections import Counter, defaultdict


class TemporalSmoother:
    """
    Smooth classification results over time using majority voting.
    
    Maintains a history of predictions for each track and returns
    the most common prediction across the temporal window.
    """
    
    def __init__(self, window_size: int = 5):
        """
        Initialize temporal smoother.
        
        Args:
            window_size: Number of frames to consider for smoothing
        """
        self.window_size = window_size
        self.history: Dict[int, List[Dict[str, str]]] = defaultdict(list)
    
    def smooth(self, track_id: int, current_pred: Dict[str, str]) -> Dict[str, str]:
        """
        Smooth prediction using temporal history.
        
        Args:
            track_id: Track ID
            current_pred: Current classification prediction
        
        Returns:
            Smoothed prediction using majority voting
        """
        # Add current prediction to history
        self.history[track_id].append(current_pred)
        
        # Keep only last N predictions
        if len(self.history[track_id]) > self.window_size:
            self.history[track_id].pop(0)
        
        # If we don't have enough history, return current prediction
        if len(self.history[track_id]) < 2:
            return current_pred
        
        # Perform majority voting for each attribute
        return self._vote(self.history[track_id])
    
    def _vote(self, predictions: List[Dict[str, str]]) -> Dict[str, str]:
        """
        Perform majority voting across predictions.
        
        Args:
            predictions: List of prediction dictionaries
        
        Returns:
            Voted prediction dictionary
        """
        result = {}
        
        # Get all keys from first prediction
        keys = predictions[0].keys()
        
        # Vote for each attribute
        for key in keys:
            # Collect all values for this attribute
            values = [pred[key] for pred in predictions]
            
            # Find most common value
            most_common = Counter(values).most_common(1)[0][0]
            result[key] = most_common
        
        return result
    
    def clear_track(self, track_id: int):
        """
        Clear history for a specific track.
        
        Args:
            track_id: Track ID to clear
        """
        if track_id in self.history:
            del self.history[track_id]
    
    def clear_all(self):
        """Clear all history."""
        self.history.clear()
    
    def get_history_size(self, track_id: int) -> int:
        """
        Get number of predictions in history for a track.
        
        Args:
            track_id: Track ID
        
        Returns:
            Number of predictions in history
        """
        return len(self.history.get(track_id, []))
    
    def __repr__(self) -> str:
        """String representation."""
        return f"TemporalSmoother(window_size={self.window_size}, active_tracks={len(self.history)})"
