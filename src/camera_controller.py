"""
Camera Controller for EkoVision Detection-Tracking-Trigger System

Handles runtime camera configuration including exposure, brightness, contrast, and presets.
"""
import cv2
import numpy as np
from dataclasses import dataclass
from typing import Optional, Dict, Tuple


@dataclass
class CameraPreset:
    """Predefined camera configuration preset."""
    name: str
    exposure: float      # Shutter speed in seconds (1/250 to 1/2000)
    brightness: int      # -50 to +50
    contrast: float      # 0.5 to 2.0
    auto_exposure: bool


class CameraController:
    """
    Manages camera configuration for optimal bottle detection.
    
    Features:
    - Manual exposure control (shutter speed)
    - Brightness adjustment
    - Contrast adjustment
    - Auto-exposure toggle
    - Predefined presets (Indoor, Outdoor, High Speed)
    - Settings validation
    - Histogram-based brightness validation
    """
    
    # Predefined camera presets
    PRESETS = {
        "Indoor": CameraPreset("Indoor", 1/500, 10, 1.2, False),
        "Outdoor": CameraPreset("Outdoor", 1/1000, -10, 1.0, False),
        "High Speed": CameraPreset("High Speed", 1/2000, 0, 1.5, False)
    }
    
    def __init__(self, video_capture: cv2.VideoCapture):
        """
        Initialize camera controller.
        
        Args:
            video_capture: OpenCV VideoCapture instance
        """
        self.cap = video_capture
        
        # Current settings
        self.exposure = -6  # OpenCV exposure value (log scale)
        self.brightness = 0
        self.contrast = 1.0
        self.auto_exposure = True
        
        # Validation flag
        self.supports_manual_control = True
        
        # Get initial settings
        self._read_current_settings()
    
    def _read_current_settings(self):
        """Read current camera settings."""
        try:
            # Try to read exposure
            exp = self.cap.get(cv2.CAP_PROP_EXPOSURE)
            if exp != 0:
                self.exposure = exp
            
            # Try to read brightness
            bright = self.cap.get(cv2.CAP_PROP_BRIGHTNESS)
            if bright != 0:
                self.brightness = int(bright)
            
            # Try to read auto-exposure
            auto_exp = self.cap.get(cv2.CAP_PROP_AUTO_EXPOSURE)
            self.auto_exposure = (auto_exp > 0.5)
            
        except Exception as e:
            print(f"⚠ Could not read camera settings: {e}")
    
    def set_exposure(self, shutter_speed: float) -> bool:
        """
        Set manual exposure (shutter speed).
        
        Args:
            shutter_speed: Shutter speed in seconds (1/250 to 1/2000)
                          e.g., 1/500 = 0.002, 1/1000 = 0.001
        
        Returns:
            True if successful, False otherwise
        """
        # Clamp to valid range
        shutter_speed = max(1/2000, min(1/250, shutter_speed))
        
        # Convert to OpenCV exposure value (log scale)
        # OpenCV uses log2 scale: exposure = log2(shutter_speed)
        exposure_value = np.log2(shutter_speed)
        
        try:
            # Disable auto-exposure first
            self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)  # Manual mode
            
            # Set exposure
            success = self.cap.set(cv2.CAP_PROP_EXPOSURE, exposure_value)
            
            if success:
                # Validate by reading back
                actual_value = self.cap.get(cv2.CAP_PROP_EXPOSURE)
                if abs(actual_value - exposure_value) < 1.0:  # Allow some tolerance
                    self.exposure = exposure_value
                    self.auto_exposure = False
                    return True
                else:
                    print(f"⚠ Exposure validation failed: set {exposure_value:.2f}, got {actual_value:.2f}")
                    self.supports_manual_control = False
                    return False
            else:
                print("⚠ Failed to set exposure")
                self.supports_manual_control = False
                return False
                
        except Exception as e:
            print(f"✗ Error setting exposure: {e}")
            self.supports_manual_control = False
            return False
    
    def adjust_exposure(self, delta: int) -> bool:
        """
        Adjust exposure by delta steps.
        
        Args:
            delta: Number of steps to adjust (+1 = faster, -1 = slower)
        
        Returns:
            True if successful, False otherwise
        """
        # Each step is approximately 1 EV (double/half the exposure time)
        new_exposure = self.exposure + delta
        
        # Clamp to reasonable range
        new_exposure = max(-11, min(-8, new_exposure))  # Roughly 1/2000 to 1/250
        
        try:
            self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)
            success = self.cap.set(cv2.CAP_PROP_EXPOSURE, new_exposure)
            
            if success:
                self.exposure = new_exposure
                self.auto_exposure = False
                return True
            return False
        except:
            return False
    
    def set_brightness(self, brightness: int) -> bool:
        """
        Set brightness adjustment.
        
        Args:
            brightness: Brightness value (-50 to +50)
        
        Returns:
            True if successful, False otherwise
        """
        # Clamp to valid range
        brightness = max(-50, min(50, brightness))
        
        try:
            success = self.cap.set(cv2.CAP_PROP_BRIGHTNESS, brightness)
            
            if success:
                # Validate by reading back
                actual_value = self.cap.get(cv2.CAP_PROP_BRIGHTNESS)
                if abs(actual_value - brightness) < 10:  # Allow some tolerance
                    self.brightness = brightness
                    return True
                else:
                    print(f"⚠ Brightness validation failed: set {brightness}, got {actual_value:.1f}")
                    return False
            else:
                print("⚠ Failed to set brightness")
                return False
                
        except Exception as e:
            print(f"✗ Error setting brightness: {e}")
            return False
    
    def adjust_brightness(self, delta: int) -> bool:
        """
        Adjust brightness by delta.
        
        Args:
            delta: Amount to adjust (+5 = brighter, -5 = darker)
        
        Returns:
            True if successful, False otherwise
        """
        new_brightness = self.brightness + delta
        return self.set_brightness(new_brightness)
    
    def set_contrast(self, contrast: float) -> bool:
        """
        Set contrast adjustment.
        
        Args:
            contrast: Contrast multiplier (0.5 to 2.0)
        
        Returns:
            True if successful, False otherwise
        """
        # Clamp to valid range
        contrast = max(0.5, min(2.0, contrast))
        
        try:
            # OpenCV contrast is typically 0-100 scale
            contrast_value = int(contrast * 50)
            success = self.cap.set(cv2.CAP_PROP_CONTRAST, contrast_value)
            
            if success:
                self.contrast = contrast
                return True
            else:
                print("⚠ Failed to set contrast")
                return False
                
        except Exception as e:
            print(f"✗ Error setting contrast: {e}")
            return False
    
    def set_auto_exposure(self, enabled: bool) -> bool:
        """
        Enable or disable auto-exposure.
        
        Args:
            enabled: True to enable auto-exposure, False for manual
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # OpenCV auto-exposure: 0.75 = auto, 0.25 = manual
            value = 0.75 if enabled else 0.25
            success = self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, value)
            
            if success:
                self.auto_exposure = enabled
                return True
            else:
                print("⚠ Failed to set auto-exposure")
                return False
                
        except Exception as e:
            print(f"✗ Error setting auto-exposure: {e}")
            return False
    
    def load_preset(self, preset_name: str) -> bool:
        """
        Load and apply a predefined camera preset.
        
        Args:
            preset_name: Name of preset ("Indoor", "Outdoor", "High Speed")
        
        Returns:
            True if successful, False otherwise
        """
        if preset_name not in self.PRESETS:
            print(f"✗ Unknown preset: {preset_name}")
            return False
        
        preset = self.PRESETS[preset_name]
        
        print(f"Loading preset: {preset.name}")
        
        # Apply settings
        success = True
        success &= self.set_auto_exposure(preset.auto_exposure)
        if not preset.auto_exposure:
            success &= self.set_exposure(preset.exposure)
        success &= self.set_brightness(preset.brightness)
        success &= self.set_contrast(preset.contrast)
        
        if success:
            print(f"✓ Preset '{preset.name}' loaded")
        else:
            print(f"⚠ Preset '{preset.name}' partially loaded (some settings failed)")
        
        return success
    
    def get_current_settings(self) -> Dict[str, any]:
        """
        Get current camera settings.
        
        Returns:
            Dict with keys: exposure, brightness, contrast, auto_exposure
        """
        return {
            'exposure': self.exposure,
            'exposure_readable': f"1/{int(1 / (2 ** self.exposure))}",
            'brightness': self.brightness,
            'contrast': self.contrast,
            'auto_exposure': self.auto_exposure,
            'supports_manual_control': self.supports_manual_control
        }
    
    def check_brightness_histogram(self, frame: np.ndarray) -> str:
        """
        Validate frame brightness using histogram analysis.
        
        Args:
            frame: Input frame (BGR format)
        
        Returns:
            "too_dark", "ok", or "too_bright"
        """
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Calculate histogram
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        
        # Calculate mean brightness
        mean_brightness = np.mean(gray)
        
        # Thresholds
        if mean_brightness < 60:
            return "too_dark"
        elif mean_brightness > 200:
            return "too_bright"
        else:
            return "ok"
    
    def print_settings(self):
        """Print current camera settings to console."""
        settings = self.get_current_settings()
        
        print("\n" + "="*50)
        print("CAMERA SETTINGS")
        print("="*50)
        print(f"Auto-exposure: {'ON' if settings['auto_exposure'] else 'OFF'}")
        if not settings['auto_exposure']:
            print(f"Exposure: {settings['exposure_readable']} sec")
        print(f"Brightness: {settings['brightness']}")
        print(f"Contrast: {settings['contrast']:.1f}")
        print(f"Manual control: {'Supported' if settings['supports_manual_control'] else 'Not supported'}")
        print("="*50)
    
    def show_controls_help(self):
        """Display camera controls help."""
        print("\n" + "="*50)
        print("CAMERA CONTROLS")
        print("="*50)
        print("  [ / ]  - Decrease/Increase exposure")
        print("  - / +  - Decrease/Increase brightness")
        print("  a      - Toggle auto-exposure")
        print("  1      - Load 'Indoor' preset")
        print("  2      - Load 'Outdoor' preset")
        print("  3      - Load 'High Speed' preset")
        print("  c      - Close camera controls")
        print("="*50)


if __name__ == "__main__":
    # Test camera controller
    print("Testing CameraController...")
    print()
    
    # Open camera
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("✗ Failed to open camera")
        exit(1)
    
    print("✓ Camera opened")
    
    # Create controller
    controller = CameraController(cap)
    
    # Print current settings
    controller.print_settings()
    
    # Test exposure adjustment
    print("\nTesting exposure adjustment...")
    controller.adjust_exposure(-1)  # Faster shutter
    
    # Test brightness adjustment
    print("\nTesting brightness adjustment...")
    controller.adjust_brightness(10)  # Brighter
    
    # Print updated settings
    controller.print_settings()
    
    # Test preset
    print("\nTesting preset...")
    controller.load_preset("Indoor")
    controller.print_settings()
    
    # Cleanup
    cap.release()
    print("\n✓ CameraController test complete")
