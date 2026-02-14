"""
ClassificationCache for storing and retrieving bottle classification results.
"""
from collections import OrderedDict
from threading import Lock
from typing import Dict, Optional, Any
from dataclasses import dataclass


@dataclass
class CacheStats:
    """Statistics for cache performance."""
    hits: int = 0
    misses: int = 0
    size: int = 0
    max_size: int = 0
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return self.hits / total
    
    @property
    def miss_rate(self) -> float:
        """Calculate cache miss rate."""
        return 1.0 - self.hit_rate
    
    def __repr__(self) -> str:
        """String representation."""
        return (
            f"CacheStats(hits={self.hits}, misses={self.misses}, "
            f"size={self.size}/{self.max_size}, hit_rate={self.hit_rate:.2%})"
        )


class ClassificationCache:
    """
    LRU cache for storing classification results.
    
    Thread-safe cache with automatic eviction of least recently used entries
    when capacity is reached.
    """
    
    def __init__(self, max_size: int = 100):
        """
        Initialize classification cache.
        
        Args:
            max_size: Maximum number of entries in cache
        """
        self.max_size = max_size
        self._cache: OrderedDict[int, Dict[str, str]] = OrderedDict()
        self._lock = Lock()
        self._stats = CacheStats(max_size=max_size)
    
    def get(self, track_id: int) -> Optional[Dict[str, str]]:
        """
        Get classification results for a track.
        
        Args:
            track_id: Track ID
        
        Returns:
            Classification results dict or None if not found
        """
        with self._lock:
            if track_id in self._cache:
                # Move to end (most recently used)
                self._cache.move_to_end(track_id)
                self._stats.hits += 1
                return self._cache[track_id].copy()
            else:
                self._stats.misses += 1
                return None
    
    def put(self, track_id: int, results: Dict[str, str]) -> None:
        """
        Store classification results for a track.
        
        Args:
            track_id: Track ID
            results: Classification results dict
        """
        with self._lock:
            # If already exists, update and move to end
            if track_id in self._cache:
                self._cache[track_id] = results.copy()
                self._cache.move_to_end(track_id)
            else:
                # Add new entry
                self._cache[track_id] = results.copy()
                
                # Evict oldest if over capacity
                if len(self._cache) > self.max_size:
                    # Remove first item (least recently used)
                    self._cache.popitem(last=False)
            
            self._stats.size = len(self._cache)
    
    def remove(self, track_id: int) -> bool:
        """
        Remove classification results for a track.
        
        Args:
            track_id: Track ID
        
        Returns:
            True if removed, False if not found
        """
        with self._lock:
            if track_id in self._cache:
                del self._cache[track_id]
                self._stats.size = len(self._cache)
                return True
            return False
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            self._stats.size = 0
    
    def get_stats(self) -> CacheStats:
        """
        Get cache statistics.
        
        Returns:
            CacheStats object with current statistics
        """
        with self._lock:
            return CacheStats(
                hits=self._stats.hits,
                misses=self._stats.misses,
                size=len(self._cache),
                max_size=self.max_size
            )
    
    def reset_stats(self) -> None:
        """Reset cache statistics (but keep cached data)."""
        with self._lock:
            self._stats.hits = 0
            self._stats.misses = 0
    
    def contains(self, track_id: int) -> bool:
        """
        Check if track ID is in cache.
        
        Args:
            track_id: Track ID
        
        Returns:
            True if in cache, False otherwise
        """
        with self._lock:
            return track_id in self._cache
    
    def get_all_ids(self) -> list[int]:
        """
        Get all track IDs in cache.
        
        Returns:
            List of track IDs (ordered by recency, most recent last)
        """
        with self._lock:
            return list(self._cache.keys())
    
    def get_size(self) -> int:
        """
        Get current cache size.
        
        Returns:
            Number of entries in cache
        """
        with self._lock:
            return len(self._cache)
    
    def is_full(self) -> bool:
        """
        Check if cache is at capacity.
        
        Returns:
            True if cache is full, False otherwise
        """
        with self._lock:
            return len(self._cache) >= self.max_size
    
    def get_oldest_id(self) -> Optional[int]:
        """
        Get the oldest (least recently used) track ID.
        
        Returns:
            Track ID or None if cache is empty
        """
        with self._lock:
            if len(self._cache) == 0:
                return None
            # First item is oldest
            return next(iter(self._cache))
    
    def get_newest_id(self) -> Optional[int]:
        """
        Get the newest (most recently used) track ID.
        
        Returns:
            Track ID or None if cache is empty
        """
        with self._lock:
            if len(self._cache) == 0:
                return None
            # Last item is newest
            return next(reversed(self._cache))
    
    def __len__(self) -> int:
        """Get cache size."""
        return self.get_size()
    
    def __contains__(self, track_id: int) -> bool:
        """Check if track ID is in cache."""
        return self.contains(track_id)
    
    def __repr__(self) -> str:
        """String representation."""
        stats = self.get_stats()
        return (
            f"ClassificationCache(size={stats.size}/{stats.max_size}, "
            f"hits={stats.hits}, misses={stats.misses}, "
            f"hit_rate={stats.hit_rate:.2%})"
        )
