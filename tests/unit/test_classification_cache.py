"""
Unit tests for ClassificationCache class.
"""
import pytest
from threading import Thread
from src.tracking.classification_cache import ClassificationCache, CacheStats


class TestCacheStats:
    """Tests for CacheStats dataclass."""
    
    def test_initialization(self):
        """Test cache stats initialization."""
        stats = CacheStats(hits=10, misses=5, size=15, max_size=100)
        assert stats.hits == 10
        assert stats.misses == 5
        assert stats.size == 15
        assert stats.max_size == 100
    
    def test_hit_rate_calculation(self):
        """Test hit rate calculation."""
        stats = CacheStats(hits=80, misses=20)
        assert stats.hit_rate == pytest.approx(0.8)
    
    def test_miss_rate_calculation(self):
        """Test miss rate calculation."""
        stats = CacheStats(hits=80, misses=20)
        assert stats.miss_rate == pytest.approx(0.2)
    
    def test_hit_rate_zero_requests(self):
        """Test hit rate with zero requests."""
        stats = CacheStats(hits=0, misses=0)
        assert stats.hit_rate == 0.0
    
    def test_repr(self):
        """Test string representation."""
        stats = CacheStats(hits=10, misses=5, size=15, max_size=100)
        repr_str = repr(stats)
        assert "CacheStats" in repr_str
        assert "hits=10" in repr_str


class TestClassificationCache:
    """Tests for ClassificationCache class."""
    
    def test_initialization(self):
        """Test cache initialization."""
        cache = ClassificationCache(max_size=50)
        assert cache.max_size == 50
        assert cache.get_size() == 0
    
    def test_put_and_get(self):
        """Test storing and retrieving results."""
        cache = ClassificationCache()
        results = {'product': 'Aqua', 'volume': '600ml'}
        
        cache.put(track_id=1, results=results)
        retrieved = cache.get(track_id=1)
        
        assert retrieved == results
        assert cache.get_size() == 1
    
    def test_get_miss(self):
        """Test cache miss returns None."""
        cache = ClassificationCache()
        
        retrieved = cache.get(track_id=999)
        
        assert retrieved is None
    
    def test_put_updates_existing(self):
        """Test putting same track ID updates value."""
        cache = ClassificationCache()
        
        cache.put(track_id=1, results={'product': 'Aqua'})
        cache.put(track_id=1, results={'product': 'Coca Cola'})
        
        retrieved = cache.get(track_id=1)
        assert retrieved['product'] == 'Coca Cola'
        assert cache.get_size() == 1  # Still only 1 entry
    
    def test_lru_eviction(self):
        """Test LRU eviction when cache is full."""
        cache = ClassificationCache(max_size=3)
        
        # Fill cache
        cache.put(1, {'product': 'A'})
        cache.put(2, {'product': 'B'})
        cache.put(3, {'product': 'C'})
        
        # Add one more (should evict track 1)
        cache.put(4, {'product': 'D'})
        
        assert cache.get_size() == 3
        assert cache.get(1) is None  # Evicted
        assert cache.get(2) is not None
        assert cache.get(3) is not None
        assert cache.get(4) is not None
    
    def test_lru_access_updates_order(self):
        """Test accessing entry moves it to end (most recent)."""
        cache = ClassificationCache(max_size=3)
        
        cache.put(1, {'product': 'A'})
        cache.put(2, {'product': 'B'})
        cache.put(3, {'product': 'C'})
        
        # Access track 1 (moves to end)
        cache.get(1)
        
        # Add new entry (should evict track 2, not 1)
        cache.put(4, {'product': 'D'})
        
        assert cache.get(1) is not None  # Still in cache
        assert cache.get(2) is None      # Evicted
        assert cache.get(3) is not None
        assert cache.get(4) is not None
    
    def test_remove(self):
        """Test removing entry from cache."""
        cache = ClassificationCache()
        cache.put(1, {'product': 'Aqua'})
        
        result = cache.remove(1)
        
        assert result is True
        assert cache.get(1) is None
        assert cache.get_size() == 0
    
    def test_remove_not_found(self):
        """Test removing non-existent entry returns False."""
        cache = ClassificationCache()
        
        result = cache.remove(999)
        
        assert result is False
    
    def test_clear(self):
        """Test clearing all cache entries."""
        cache = ClassificationCache()
        cache.put(1, {'product': 'A'})
        cache.put(2, {'product': 'B'})
        cache.put(3, {'product': 'C'})
        
        cache.clear()
        
        assert cache.get_size() == 0
        assert cache.get(1) is None
        assert cache.get(2) is None
        assert cache.get(3) is None
    
    def test_get_stats(self):
        """Test getting cache statistics."""
        cache = ClassificationCache(max_size=100)
        
        cache.put(1, {'product': 'A'})
        cache.get(1)  # Hit
        cache.get(2)  # Miss
        
        stats = cache.get_stats()
        
        assert stats.hits == 1
        assert stats.misses == 1
        assert stats.size == 1
        assert stats.max_size == 100
        assert stats.hit_rate == pytest.approx(0.5)
    
    def test_reset_stats(self):
        """Test resetting statistics."""
        cache = ClassificationCache()
        cache.put(1, {'product': 'A'})
        cache.get(1)  # Hit
        cache.get(2)  # Miss
        
        cache.reset_stats()
        
        stats = cache.get_stats()
        assert stats.hits == 0
        assert stats.misses == 0
        assert stats.size == 1  # Data still in cache
    
    def test_contains(self):
        """Test checking if track ID is in cache."""
        cache = ClassificationCache()
        cache.put(1, {'product': 'A'})
        
        assert cache.contains(1) is True
        assert cache.contains(2) is False
    
    def test_contains_operator(self):
        """Test 'in' operator."""
        cache = ClassificationCache()
        cache.put(1, {'product': 'A'})
        
        assert 1 in cache
        assert 2 not in cache
    
    def test_get_all_ids(self):
        """Test getting all track IDs."""
        cache = ClassificationCache()
        cache.put(1, {'product': 'A'})
        cache.put(2, {'product': 'B'})
        cache.put(3, {'product': 'C'})
        
        ids = cache.get_all_ids()
        
        assert ids == [1, 2, 3]
    
    def test_get_all_ids_ordered_by_recency(self):
        """Test IDs are ordered by recency."""
        cache = ClassificationCache()
        cache.put(1, {'product': 'A'})
        cache.put(2, {'product': 'B'})
        cache.put(3, {'product': 'C'})
        
        # Access track 1 (moves to end)
        cache.get(1)
        
        ids = cache.get_all_ids()
        assert ids == [2, 3, 1]  # 1 is now most recent
    
    def test_is_full(self):
        """Test checking if cache is full."""
        cache = ClassificationCache(max_size=2)
        
        assert cache.is_full() is False
        
        cache.put(1, {'product': 'A'})
        assert cache.is_full() is False
        
        cache.put(2, {'product': 'B'})
        assert cache.is_full() is True
    
    def test_get_oldest_id(self):
        """Test getting oldest track ID."""
        cache = ClassificationCache()
        cache.put(1, {'product': 'A'})
        cache.put(2, {'product': 'B'})
        cache.put(3, {'product': 'C'})
        
        oldest = cache.get_oldest_id()
        
        assert oldest == 1
    
    def test_get_oldest_id_empty_cache(self):
        """Test getting oldest ID from empty cache."""
        cache = ClassificationCache()
        
        oldest = cache.get_oldest_id()
        
        assert oldest is None
    
    def test_get_newest_id(self):
        """Test getting newest track ID."""
        cache = ClassificationCache()
        cache.put(1, {'product': 'A'})
        cache.put(2, {'product': 'B'})
        cache.put(3, {'product': 'C'})
        
        newest = cache.get_newest_id()
        
        assert newest == 3
    
    def test_get_newest_id_empty_cache(self):
        """Test getting newest ID from empty cache."""
        cache = ClassificationCache()
        
        newest = cache.get_newest_id()
        
        assert newest is None
    
    def test_len_operator(self):
        """Test len() operator."""
        cache = ClassificationCache()
        cache.put(1, {'product': 'A'})
        cache.put(2, {'product': 'B'})
        
        assert len(cache) == 2
    
    def test_repr(self):
        """Test string representation."""
        cache = ClassificationCache(max_size=100)
        cache.put(1, {'product': 'A'})
        
        repr_str = repr(cache)
        
        assert "ClassificationCache" in repr_str
        assert "size=1/100" in repr_str
    
    def test_thread_safety_concurrent_puts(self):
        """Test thread safety with concurrent puts."""
        cache = ClassificationCache(max_size=1000)
        
        def put_items(start, count):
            for i in range(start, start + count):
                cache.put(i, {'product': f'Product{i}'})
        
        threads = []
        for i in range(10):
            t = Thread(target=put_items, args=(i * 100, 100))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # All 1000 items should be in cache
        assert cache.get_size() == 1000
    
    def test_thread_safety_concurrent_gets(self):
        """Test thread safety with concurrent gets."""
        cache = ClassificationCache()
        cache.put(1, {'product': 'A'})
        
        results = []
        
        def get_item():
            result = cache.get(1)
            results.append(result)
        
        threads = []
        for _ in range(100):
            t = Thread(target=get_item)
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # All gets should succeed
        assert len(results) == 100
        assert all(r == {'product': 'A'} for r in results)
    
    def test_data_isolation(self):
        """Test that returned data is isolated (copy)."""
        cache = ClassificationCache()
        original = {'product': 'Aqua', 'volume': '600ml'}
        cache.put(1, original)
        
        # Modify retrieved data
        retrieved = cache.get(1)
        retrieved['product'] = 'Modified'
        
        # Original in cache should be unchanged
        cached = cache.get(1)
        assert cached['product'] == 'Aqua'
    
    def test_multiple_evictions(self):
        """Test multiple evictions in sequence."""
        cache = ClassificationCache(max_size=2)
        
        cache.put(1, {'product': 'A'})
        cache.put(2, {'product': 'B'})
        cache.put(3, {'product': 'C'})  # Evicts 1
        cache.put(4, {'product': 'D'})  # Evicts 2
        
        assert cache.get(1) is None
        assert cache.get(2) is None
        assert cache.get(3) is not None
        assert cache.get(4) is not None
