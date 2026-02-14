"""
Unit tests for image enhancement module.
"""
import pytest
import numpy as np
import cv2
from PIL import Image
from src.image_enhancement import (
    enhance_contrast,
    normalize_brightness,
    denoise_frame,
    preprocess_crop,
    expand_bbox,
    ensure_minimum_crop_size
)


class TestEnhanceContrast:
    """Tests for enhance_contrast function."""
    
    def test_enhance_contrast_basic(self):
        """Test basic contrast enhancement."""
        # Create test frame
        frame = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)
        
        # Enhance contrast
        enhanced = enhance_contrast(frame)
        
        # Check output shape and type
        assert enhanced.shape == frame.shape
        assert enhanced.dtype == np.uint8
    
    def test_enhance_contrast_low_contrast(self):
        """Test enhancement on low contrast image."""
        # Create low contrast frame (all values around 128)
        frame = np.full((480, 640, 3), 128, dtype=np.uint8)
        frame += np.random.randint(-10, 10, (480, 640, 3), dtype=np.int16).astype(np.uint8)
        
        # Enhance contrast
        enhanced = enhance_contrast(frame)
        
        # Enhanced should have higher contrast
        assert enhanced.std() >= frame.std() * 0.9  # Allow some tolerance


class TestNormalizeBrightness:
    """Tests for normalize_brightness function."""
    
    def test_normalize_brightness_basic(self):
        """Test basic brightness normalization."""
        # Create test frame
        frame = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)
        
        # Normalize brightness
        normalized = normalize_brightness(frame, target_mean=128)
        
        # Check output shape and type
        assert normalized.shape == frame.shape
        assert normalized.dtype == np.uint8
    
    def test_normalize_brightness_dark_image(self):
        """Test normalization on dark image."""
        # Create dark frame
        frame = np.random.randint(0, 50, (480, 640, 3), dtype=np.uint8)
        
        # Normalize to target mean
        normalized = normalize_brightness(frame, target_mean=128)
        
        # Normalized should be brighter
        assert normalized.mean() > frame.mean()
    
    def test_normalize_brightness_bright_image(self):
        """Test normalization on bright image."""
        # Create bright frame
        frame = np.random.randint(200, 256, (480, 640, 3), dtype=np.uint8)
        
        # Normalize to target mean
        normalized = normalize_brightness(frame, target_mean=128)
        
        # Normalized should be darker
        assert normalized.mean() < frame.mean()


class TestDenoiseFrame:
    """Tests for denoise_frame function."""
    
    def test_denoise_frame_basic(self):
        """Test basic denoising."""
        # Create test frame with noise
        frame = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)
        
        # Denoise
        denoised = denoise_frame(frame, h=10)
        
        # Check output shape and type
        assert denoised.shape == frame.shape
        assert denoised.dtype == np.uint8


class TestPreprocessCrop:
    """Tests for preprocess_crop function."""
    
    def test_preprocess_crop_basic(self):
        """Test basic crop preprocessing."""
        # Create test crop
        crop_np = np.random.randint(0, 256, (224, 224, 3), dtype=np.uint8)
        crop = Image.fromarray(crop_np)
        
        # Preprocess
        enhanced = preprocess_crop(crop)
        
        # Check output type and size
        assert isinstance(enhanced, Image.Image)
        assert enhanced.size == crop.size
    
    def test_preprocess_crop_low_contrast(self):
        """Test preprocessing on low contrast crop."""
        # Create low contrast crop
        crop_np = np.full((224, 224, 3), 128, dtype=np.uint8)
        crop = Image.fromarray(crop_np)
        
        # Preprocess
        enhanced = preprocess_crop(crop)
        
        # Check output
        assert isinstance(enhanced, Image.Image)
        assert enhanced.size == crop.size


class TestExpandBbox:
    """Tests for expand_bbox function."""
    
    def test_expand_bbox_basic(self):
        """Test basic bbox expansion."""
        bbox = np.array([100, 100, 200, 200])
        frame_shape = (480, 640)
        
        # Expand by 10%
        expanded = expand_bbox(bbox, frame_shape, expand_ratio=0.1)
        
        # Check expansion
        assert expanded[0] < bbox[0]  # x1 decreased
        assert expanded[1] < bbox[1]  # y1 decreased
        assert expanded[2] > bbox[2]  # x2 increased
        assert expanded[3] > bbox[3]  # y2 increased
    
    def test_expand_bbox_edge_clipping(self):
        """Test bbox expansion with edge clipping."""
        # Bbox near edge
        bbox = np.array([10, 10, 50, 50])
        frame_shape = (480, 640)
        
        # Expand by 50%
        expanded = expand_bbox(bbox, frame_shape, expand_ratio=0.5)
        
        # Check clipping
        assert expanded[0] >= 0  # x1 clipped to 0
        assert expanded[1] >= 0  # y1 clipped to 0
        assert expanded[2] <= frame_shape[1]  # x2 clipped to width
        assert expanded[3] <= frame_shape[0]  # y2 clipped to height
    
    def test_expand_bbox_zero_ratio(self):
        """Test bbox expansion with zero ratio."""
        bbox = np.array([100, 100, 200, 200])
        frame_shape = (480, 640)
        
        # No expansion
        expanded = expand_bbox(bbox, frame_shape, expand_ratio=0.0)
        
        # Should be same as input
        assert expanded[0] == bbox[0]
        assert expanded[1] == bbox[1]
        assert expanded[2] == bbox[2]
        assert expanded[3] == bbox[3]


class TestEnsureMinimumCropSize:
    """Tests for ensure_minimum_crop_size function."""
    
    def test_ensure_minimum_crop_size_large_crop(self):
        """Test with crop larger than minimum."""
        # Create large crop
        crop = Image.new('RGB', (300, 300), (128, 128, 128))
        
        # Ensure minimum size
        result = ensure_minimum_crop_size(crop, min_size=224)
        
        # Should be unchanged
        assert result.size == crop.size
    
    def test_ensure_minimum_crop_size_small_crop(self):
        """Test with crop smaller than minimum."""
        # Create small crop
        crop = Image.new('RGB', (100, 100), (128, 128, 128))
        
        # Ensure minimum size
        result = ensure_minimum_crop_size(crop, min_size=224)
        
        # Should be padded
        assert result.size == (224, 224)
    
    def test_ensure_minimum_crop_size_exact(self):
        """Test with crop exactly at minimum."""
        # Create exact size crop
        crop = Image.new('RGB', (224, 224), (128, 128, 128))
        
        # Ensure minimum size
        result = ensure_minimum_crop_size(crop, min_size=224)
        
        # Should be unchanged
        assert result.size == crop.size
