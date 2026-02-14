"""
Configuration Loader for EkoVision Detection-Tracking-Trigger System

Loads configuration from YAML file with validation and fallback to defaults.
"""
import os
import yaml
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class CameraConfig:
    """Camera configuration."""
    index: int = 0
    width: int = 640
    height: int = 480


@dataclass
class DetectionConfig:
    """Detection configuration."""
    confidence_threshold: float = 0.5
    iou_threshold: float = 0.5


@dataclass
class ClassificationConfig:
    """Classification configuration."""
    confidence_threshold: float = 0.5
    expand_bbox_ratio: float = 0.1
    min_crop_size: int = 224
    enable_temporal_smoothing: bool = True
    temporal_window_size: int = 5
    enable_preprocessing: bool = True
    enable_ensemble: bool = False


@dataclass
class TriggerZoneConfig:
    """Trigger zone configuration (single zone - legacy)."""
    x_offset_pct: float = 30.0
    y_offset_pct: float = 20.0
    width_pct: float = 40.0
    height_pct: float = 60.0


@dataclass
class MultiZoneConfig:
    """Multiple trigger zones configuration."""
    enabled: bool = False  # Use multiple zones instead of single zone
    max_zones: int = 3
    zones: list = field(default_factory=lambda: [
        {
            'x_offset_pct': 30.0,
            'y_offset_pct': 20.0,
            'width_pct': 40.0,
            'height_pct': 60.0,
            'enabled': True,
            'name': 'Zone 1'
        }
    ])


@dataclass
class TrackingConfig:
    """Tracking configuration."""
    max_age: int = 30
    min_hits: int = 1
    iou_threshold: float = 0.3
    max_tracks: int = 20
    max_classification_attempts: int = 2


@dataclass
class CacheConfig:
    """Cache configuration."""
    max_size: int = 100


@dataclass
class ModelConfig:
    """Model paths configuration."""
    yolo_path: str = "best.pt"
    dinov3_model: str = "facebook/dinov3-convnext-small-pretrain-lvd1689m"
    encoder_path: str = "dinov3_multilabel_encoder.pkl"
    mapping_path: str = "label_mapping_dict.joblib"
    classifiers_dir: str = "OVR_Checkpoints-20251018T053026Z-1-001/OVR_Checkpoints"


@dataclass
class LabelConfig:
    """Label configuration."""
    columns: list = field(default_factory=lambda: [
        'product', 'grade', 'cap', 'label', 'brand', 'type', 'subtype', 'volume'
    ])


@dataclass
class DisplayConfig:
    """Display configuration."""
    show_trigger_zone: bool = True
    show_fps: bool = True
    show_statistics: bool = True


@dataclass
class PerformanceConfig:
    """Performance configuration."""
    device: str = "auto"
    warmup_classifiers: bool = True


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str = "INFO"
    log_to_file: bool = False
    log_file: str = "ekovision.log"


@dataclass
class Config:
    """Complete system configuration."""
    camera: CameraConfig = field(default_factory=CameraConfig)
    detection: DetectionConfig = field(default_factory=DetectionConfig)
    classification: ClassificationConfig = field(default_factory=ClassificationConfig)
    trigger_zone: TriggerZoneConfig = field(default_factory=TriggerZoneConfig)
    multi_zone: MultiZoneConfig = field(default_factory=MultiZoneConfig)
    tracking: TrackingConfig = field(default_factory=TrackingConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    models: ModelConfig = field(default_factory=ModelConfig)
    labels: LabelConfig = field(default_factory=LabelConfig)
    display: DisplayConfig = field(default_factory=DisplayConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)


class ConfigLoader:
    """
    Configuration loader with validation and fallback to defaults.
    
    Usage:
        config = ConfigLoader.load("config.yaml")
        print(config.camera.width)
    """
    
    @staticmethod
    def load(config_path: str = "config.yaml") -> Config:
        """
        Load configuration from YAML file.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Config object with loaded or default values
        """
        config = Config()
        
        if not os.path.exists(config_path):
            print(f"⚠ Config file not found: {config_path}")
            print(f"✓ Using default configuration")
            return config
        
        try:
            with open(config_path, 'r') as f:
                data = yaml.safe_load(f)
            
            if data is None:
                print(f"⚠ Config file is empty: {config_path}")
                print(f"✓ Using default configuration")
                return config
            
            # Load each section with validation
            config = ConfigLoader._load_config(data)
            print(f"✓ Configuration loaded from: {config_path}")
            
        except yaml.YAMLError as e:
            print(f"✗ Error parsing YAML file: {e}")
            print(f"✓ Using default configuration")
        except Exception as e:
            print(f"✗ Error loading config: {e}")
            print(f"✓ Using default configuration")
        
        return config
    
    @staticmethod
    def _load_config(data: Dict[str, Any]) -> Config:
        """Load configuration from dictionary with validation."""
        config = Config()
        
        # Camera
        if 'camera' in data:
            cam = data['camera']
            config.camera = CameraConfig(
                index=ConfigLoader._validate_int(cam.get('index'), 0, 0, 10),
                width=ConfigLoader._validate_int(cam.get('width'), 640, 320, 1920),
                height=ConfigLoader._validate_int(cam.get('height'), 480, 240, 1080)
            )
        
        # Detection
        if 'detection' in data:
            det = data['detection']
            config.detection = DetectionConfig(
                confidence_threshold=ConfigLoader._validate_float(
                    det.get('confidence_threshold'), 0.5, 0.0, 1.0
                ),
                iou_threshold=ConfigLoader._validate_float(
                    det.get('iou_threshold'), 0.5, 0.0, 1.0
                )
            )
        
        # Classification
        if 'classification' in data:
            cls = data['classification']
            config.classification = ClassificationConfig(
                confidence_threshold=ConfigLoader._validate_float(
                    cls.get('confidence_threshold'), 0.5, 0.0, 1.0
                ),
                expand_bbox_ratio=ConfigLoader._validate_float(
                    cls.get('expand_bbox_ratio'), 0.1, 0.0, 0.3
                ),
                min_crop_size=ConfigLoader._validate_int(
                    cls.get('min_crop_size'), 224, 64, 512
                ),
                enable_temporal_smoothing=bool(cls.get('enable_temporal_smoothing', True)),
                temporal_window_size=ConfigLoader._validate_int(
                    cls.get('temporal_window_size'), 5, 2, 10
                ),
                enable_preprocessing=bool(cls.get('enable_preprocessing', True)),
                enable_ensemble=bool(cls.get('enable_ensemble', False))
            )
        
        # Trigger Zone
        if 'trigger_zone' in data:
            tz = data['trigger_zone']
            config.trigger_zone = TriggerZoneConfig(
                x_offset_pct=ConfigLoader._validate_float(tz.get('x_offset_pct'), 30.0, 0.0, 50.0),
                y_offset_pct=ConfigLoader._validate_float(tz.get('y_offset_pct'), 20.0, 0.0, 50.0),
                width_pct=ConfigLoader._validate_float(tz.get('width_pct'), 40.0, 20.0, 80.0),
                height_pct=ConfigLoader._validate_float(tz.get('height_pct'), 60.0, 20.0, 80.0)
            )
        
        # Tracking
        if 'tracking' in data:
            trk = data['tracking']
            config.tracking = TrackingConfig(
                max_age=ConfigLoader._validate_int(trk.get('max_age'), 30, 10, 60),
                min_hits=ConfigLoader._validate_int(trk.get('min_hits'), 1, 1, 5),
                iou_threshold=ConfigLoader._validate_float(trk.get('iou_threshold'), 0.3, 0.1, 0.9),
                max_tracks=ConfigLoader._validate_int(trk.get('max_tracks'), 20, 5, 50),
                max_classification_attempts=ConfigLoader._validate_int(
                    trk.get('max_classification_attempts'), 2, 1, 5
                )
            )
        
        # Cache
        if 'cache' in data:
            cache = data['cache']
            config.cache = CacheConfig(
                max_size=ConfigLoader._validate_int(cache.get('max_size'), 100, 10, 500)
            )
        
        # Models
        if 'models' in data:
            mod = data['models']
            config.models = ModelConfig(
                yolo_path=mod.get('yolo_path', 'best.pt'),
                dinov3_model=mod.get('dinov3_model', 'facebook/dinov3-convnext-small-pretrain-lvd1689m'),
                encoder_path=mod.get('encoder_path', 'dinov3_multilabel_encoder.pkl'),
                mapping_path=mod.get('mapping_path', 'label_mapping_dict.joblib'),
                classifiers_dir=mod.get('classifiers_dir', 'OVR_Checkpoints-20251018T053026Z-1-001/OVR_Checkpoints')
            )
        
        # Labels
        if 'labels' in data:
            lbl = data['labels']
            columns = lbl.get('columns')
            if columns and isinstance(columns, list) and len(columns) == 8:
                config.labels = LabelConfig(columns=columns)
            else:
                print("⚠ Invalid label columns, using defaults")
        
        # Display
        if 'display' in data:
            disp = data['display']
            config.display = DisplayConfig(
                show_trigger_zone=bool(disp.get('show_trigger_zone', True)),
                show_fps=bool(disp.get('show_fps', True)),
                show_statistics=bool(disp.get('show_statistics', True))
            )
        
        # Performance
        if 'performance' in data:
            perf = data['performance']
            device = perf.get('device', 'auto')
            if device not in ['auto', 'cuda', 'cpu']:
                print(f"⚠ Invalid device '{device}', using 'auto'")
                device = 'auto'
            config.performance = PerformanceConfig(
                device=device,
                warmup_classifiers=bool(perf.get('warmup_classifiers', True))
            )
        
        # Logging
        if 'logging' in data:
            log = data['logging']
            level = log.get('level', 'INFO')
            if level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR']:
                print(f"⚠ Invalid log level '{level}', using 'INFO'")
                level = 'INFO'
            config.logging = LoggingConfig(
                level=level,
                log_to_file=bool(log.get('log_to_file', False)),
                log_file=log.get('log_file', 'ekovision.log')
            )
        
        return config
    
    @staticmethod
    def _validate_int(value: Any, default: int, min_val: int, max_val: int) -> int:
        """Validate and clamp integer value."""
        if value is None:
            return default
        try:
            val = int(value)
            if val < min_val or val > max_val:
                print(f"⚠ Value {val} out of range [{min_val}, {max_val}], using {default}")
                return default
            return val
        except (ValueError, TypeError):
            print(f"⚠ Invalid integer value '{value}', using {default}")
            return default
    
    @staticmethod
    def _validate_float(value: Any, default: float, min_val: float, max_val: float) -> float:
        """Validate and clamp float value."""
        if value is None:
            return default
        try:
            val = float(value)
            if val < min_val or val > max_val:
                print(f"⚠ Value {val} out of range [{min_val}, {max_val}], using {default}")
                return default
            return val
        except (ValueError, TypeError):
            print(f"⚠ Invalid float value '{value}', using {default}")
            return default
    
    @staticmethod
    def save_sample(output_path: str = "config.sample.yaml"):
        """
        Save a sample configuration file with all options documented.
        
        Args:
            output_path: Path to save sample config
        """
        sample_config = """# EkoVision Detection-Tracking-Trigger Configuration
# This file contains all configurable parameters for the system

# Camera Configuration
camera:
  index: 0              # Camera device index (0 = default, 1 = second camera, etc.)
  width: 640            # Frame width in pixels (320-1920)
  height: 480           # Frame height in pixels (240-1080)

# Detection Configuration
detection:
  confidence_threshold: 0.5  # YOLO confidence threshold (0.0-1.0)

# Trigger Zone Configuration
trigger_zone:
  x_offset_pct: 30.0    # X offset from left edge (0-50%)
  y_offset_pct: 20.0    # Y offset from top edge (0-50%)
  width_pct: 40.0       # Zone width as percentage of frame (20-80%)
  height_pct: 60.0      # Zone height as percentage of frame (20-80%)

# Tracking Configuration
tracking:
  max_age: 30           # Maximum frames to keep track without detection (10-60)
  min_hits: 1           # Minimum detections before confirming track (1-5)
  iou_threshold: 0.3    # IoU threshold for matching detections (0.1-0.9)
  max_tracks: 20        # Maximum number of simultaneous tracks (5-50)
  max_classification_attempts: 2  # Maximum retry attempts before FAILED state (1-5)

# Cache Configuration
cache:
  max_size: 100         # Maximum number of cached classification results (10-500)

# Model Paths
models:
  yolo_path: "best.pt"
  dinov3_model: "facebook/dinov3-convnext-small-pretrain-lvd1689m"
  encoder_path: "dinov3_multilabel_encoder.pkl"
  mapping_path: "label_mapping_dict.joblib"
  classifiers_dir: "OVR_Checkpoints-20251018T053026Z-1-001/OVR_Checkpoints"

# Label Columns (8 attributes for classification)
labels:
  columns:
    - product
    - grade
    - cap
    - label
    - brand
    - type
    - subtype
    - volume

# Display Configuration
display:
  show_trigger_zone: true   # Show trigger zone overlay on startup
  show_fps: true            # Show FPS counter
  show_statistics: true     # Show statistics overlay

# Performance Configuration
performance:
  device: "auto"            # Device for inference: "auto", "cuda", or "cpu"
  warmup_classifiers: true  # Warmup classifiers on startup to prevent lag

# Logging Configuration
logging:
  level: "INFO"             # Logging level: DEBUG, INFO, WARNING, ERROR
  log_to_file: false        # Save logs to file
  log_file: "ekovision.log" # Log file path (if log_to_file is true)
"""
        
        with open(output_path, 'w') as f:
            f.write(sample_config)
        
        print(f"✓ Sample configuration saved to: {output_path}")


if __name__ == "__main__":
    # Test configuration loader
    print("Testing ConfigLoader...")
    print()
    
    # Load config
    config = ConfigLoader.load("config.yaml")
    
    print()
    print("Loaded Configuration:")
    print(f"  Camera: {config.camera.width}x{config.camera.height} (index {config.camera.index})")
    print(f"  Detection threshold: {config.detection.confidence_threshold}")
    print(f"  Trigger zone: {config.trigger_zone.width_pct}% x {config.trigger_zone.height_pct}%")
    print(f"  Max tracks: {config.tracking.max_tracks}")
    print(f"  Cache size: {config.cache.max_size}")
    print(f"  Device: {config.performance.device}")
    
    print()
    # Save sample config
    ConfigLoader.save_sample()
