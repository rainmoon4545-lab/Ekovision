"""
Unit tests for temporal smoother module.
"""
import pytest
from src.temporal_smoother import TemporalSmoother


class TestTemporalSmoother:
    """Tests for TemporalSmoother class."""
    
    def test_initialization(self):
        """Test smoother initialization."""
        smoother = TemporalSmoother(window_size=5)
        
        assert smoother.window_size == 5
        assert len(smoother.history) == 0
    
    def test_smooth_single_prediction(self):
        """Test smoothing with single prediction."""
        smoother = TemporalSmoother(window_size=5)
        
        pred = {'product': 'Aqua', 'grade': 'A', 'cap': 'Blue'}
        result = smoother.smooth(track_id=1, current_pred=pred)
        
        # Should return same prediction
        assert result == pred
    
    def test_smooth_consistent_predictions(self):
        """Test smoothing with consistent predictions."""
        smoother = TemporalSmoother(window_size=3)
        
        pred = {'product': 'Aqua', 'grade': 'A', 'cap': 'Blue'}
        
        # Add same prediction 3 times
        for _ in range(3):
            result = smoother.smooth(track_id=1, current_pred=pred)
        
        # Should return same prediction
        assert result == pred
    
    def test_smooth_majority_voting(self):
        """Test smoothing with majority voting."""
        smoother = TemporalSmoother(window_size=5)
        
        # Add predictions with one attribute changing
        preds = [
            {'product': 'Aqua', 'grade': 'A'},
            {'product': 'Aqua', 'grade': 'A'},
            {'product': 'Aqua', 'grade': 'B'},  # Different grade
            {'product': 'Aqua', 'grade': 'A'},
            {'product': 'Aqua', 'grade': 'A'}
        ]
        
        for pred in preds:
            result = smoother.smooth(track_id=1, current_pred=pred)
        
        # Should vote for 'A' (appears 4 times vs 1 time)
        assert result['product'] == 'Aqua'
        assert result['grade'] == 'A'
    
    def test_smooth_window_size_limit(self):
        """Test that history is limited to window size."""
        smoother = TemporalSmoother(window_size=3)
        
        # Add 5 predictions
        for i in range(5):
            pred = {'product': f'Product{i}', 'grade': 'A'}
            smoother.smooth(track_id=1, current_pred=pred)
        
        # History should only contain last 3
        assert smoother.get_history_size(track_id=1) == 3
    
    def test_smooth_multiple_tracks(self):
        """Test smoothing with multiple tracks."""
        smoother = TemporalSmoother(window_size=3)
        
        pred1 = {'product': 'Aqua', 'grade': 'A'}
        pred2 = {'product': 'Coca-Cola', 'grade': 'B'}
        
        # Add predictions for different tracks
        result1 = smoother.smooth(track_id=1, current_pred=pred1)
        result2 = smoother.smooth(track_id=2, current_pred=pred2)
        
        # Should maintain separate histories
        assert result1 == pred1
        assert result2 == pred2
        assert smoother.get_history_size(track_id=1) == 1
        assert smoother.get_history_size(track_id=2) == 1
    
    def test_clear_track(self):
        """Test clearing history for specific track."""
        smoother = TemporalSmoother(window_size=3)
        
        pred = {'product': 'Aqua', 'grade': 'A'}
        
        # Add predictions
        smoother.smooth(track_id=1, current_pred=pred)
        smoother.smooth(track_id=2, current_pred=pred)
        
        # Clear track 1
        smoother.clear_track(track_id=1)
        
        # Track 1 should be cleared, track 2 should remain
        assert smoother.get_history_size(track_id=1) == 0
        assert smoother.get_history_size(track_id=2) == 1
    
    def test_clear_all(self):
        """Test clearing all history."""
        smoother = TemporalSmoother(window_size=3)
        
        pred = {'product': 'Aqua', 'grade': 'A'}
        
        # Add predictions for multiple tracks
        smoother.smooth(track_id=1, current_pred=pred)
        smoother.smooth(track_id=2, current_pred=pred)
        smoother.smooth(track_id=3, current_pred=pred)
        
        # Clear all
        smoother.clear_all()
        
        # All tracks should be cleared
        assert len(smoother.history) == 0
    
    def test_get_history_size_nonexistent_track(self):
        """Test getting history size for nonexistent track."""
        smoother = TemporalSmoother(window_size=3)
        
        # Should return 0 for nonexistent track
        assert smoother.get_history_size(track_id=999) == 0
    
    def test_repr(self):
        """Test string representation."""
        smoother = TemporalSmoother(window_size=5)
        
        pred = {'product': 'Aqua', 'grade': 'A'}
        smoother.smooth(track_id=1, current_pred=pred)
        smoother.smooth(track_id=2, current_pred=pred)
        
        repr_str = repr(smoother)
        
        assert 'TemporalSmoother' in repr_str
        assert 'window_size=5' in repr_str
        assert 'active_tracks=2' in repr_str
