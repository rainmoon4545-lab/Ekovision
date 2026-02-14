"""
Image Enhancement Module for EkoVision

Provides image preprocessing functions to improve detection and classification accuracy.
"""
import cv2
import numpy as np
from PIL import Image
from typing import Tuple


def enhance_contrast(frame: np.ndarray, clip_limit: float = 2.0, tile_size: Tuple[int, int] = (8, 8)) -> np.ndarray:
    """
    Enhance contrast using CLAHE (Contrast Limited Adaptive Histogram Equalization).
    
    Args:
        frame: Input frame in BGR format
        clip_limit: Threshold for contrast limiting (1.0-4.0)
        tile_size: Size of grid for histogram equalization
    
    Returns:
        Enhanced frame in BGR format
    """
    # Convert to LAB color space
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    
    # Apply CLAHE to L channel
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_size)
    l_enhanced = clahe.apply(l)
    
    # Merge channels and convert back to BGR
    enhanced_lab = cv2.merge([l_enhanced, a, b])
    enhanced_bgr = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
    
    return enhanced_bgr


def normalize_brightness(frame: np.ndarray, target_mean: int = 128) -> np.ndarray:
    """
    Normalize image brightness to target mean value.
    
    Args:
        frame: Input frame in BGR format
        target_mean: Target mean brightness (0-255)
    
    Returns:
        Brightness-normalized frame
    """
    # Convert to grayscale to calculate mean
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    current_mean = gray.mean()
    
    if current_mean > 0:
        # Calculate scaling factor
        alpha = target_mean / current_mean
        # Apply scaling
        normalized = cv2.convertScaleAbs(frame, alpha=alpha, beta=0)
        return normalized
    
    return frame


def denoise_frame(frame: np.ndarray, h: int = 10, template_window: int = 7, search_window: int = 21) -> np.ndarray:
    """
    Remove noise from frame using Non-local Means Denoising.
    
    Args:
        frame: Input frame in BGR format
        h: Filter strength (higher = more denoising)
        template_window: Size of template patch
        search_window: Size of search area
    
    Returns:
        Denoised frame
    """
    return cv2.fastNlMeansDenoisingColored(frame, None, h, h, template_window, search_window)


def preprocess_crop(crop: Image.Image, clip_limit: float = 2.0) -> Image.Image:
    """
    Enhance crop quality before feature extraction.
    
    Args:
        crop: PIL Image crop
        clip_limit: CLAHE clip limit
    
    Returns:
        Enhanced PIL Image
    """
    # Convert to numpy array
    crop_np = np.array(crop)
    
    # Convert RGB to BGR for OpenCV
    crop_bgr = cv2.cvtColor(crop_np, cv2.COLOR_RGB2BGR)
    
    # Enhance contrast using CLAHE
    lab = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(8, 8))
    l_enhanced = clahe.apply(l)
    
    enhanced_lab = cv2.merge([l_enhanced, a, b])
    enhanced_bgr = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
    
    # Convert back to RGB
    enhanced_rgb = cv2.cvtColor(enhanced_bgr, cv2.COLOR_BGR2RGB)
    
    # Convert back to PIL Image
    return Image.fromarray(enhanced_rgb)


def expand_bbox(
    bbox: np.ndarray,
    frame_shape: Tuple[int, int],
    expand_ratio: float = 0.1
) -> Tuple[int, int, int, int]:
    """
    Expand bounding box to include more context.
    
    Args:
        bbox: Bounding box [x1, y1, x2, y2]
        frame_shape: Frame shape (height, width)
        expand_ratio: Expansion ratio (0.0-0.3)
    
    Returns:
        Expanded bounding box (x1, y1, x2, y2)
    """
    x1, y1, x2, y2 = bbox
    w, h = x2 - x1, y2 - y1
    
    # Expand by ratio
    x1_new = max(0, x1 - w * expand_ratio)
    y1_new = max(0, y1 - h * expand_ratio)
    x2_new = min(frame_shape[1], x2 + w * expand_ratio)
    y2_new = min(frame_shape[0], y2 + h * expand_ratio)
    
    return (int(x1_new), int(y1_new), int(x2_new), int(y2_new))


def ensure_minimum_crop_size(crop: Image.Image, min_size: int = 224) -> Image.Image:
    """
    Ensure crop meets minimum size requirements by padding if necessary.
    
    Args:
        crop: PIL Image crop
        min_size: Minimum width/height in pixels
    
    Returns:
        Padded PIL Image if needed
    """
    w, h = crop.size
    
    if w >= min_size and h >= min_size:
        return crop
    
    # Calculate new size
    new_w = max(w, min_size)
    new_h = max(h, min_size)
    
    # Create new image with gray background
    new_crop = Image.new('RGB', (new_w, new_h), (128, 128, 128))
    
    # Paste original crop in center
    paste_x = (new_w - w) // 2
    paste_y = (new_h - h) // 2
    new_crop.paste(crop, (paste_x, paste_y))
    
    return new_crop
