# EkoVision Detection-Tracking-Trigger System

## Running Guide

## Overview

Sistem ini menggunakan **Detection-Tracking-Trigger Architecture** untuk mengoptimalkan deteksi dan klasifikasi botol PET secara real-time dengan kamera lokal.

### Enhanced Features (Phase 1-5)

#### Phase 1: YAML Configuration Support ✅

- Centralized configuration file (`config.yaml`)
- Type validation and error checking
- Sample config generation
- Hot-reload support (restart required)

**Documentation**: [Configuration Guide](docs/CONFIGURATION_GUIDE.md)

#### Phase 2: Data Logging & Export ✅

- **CSV Export** (`e` key): All detection data with timestamps
- **JSON Export** (`j` key): Classification history per bottle
- **Video Recording** (`v` key): Annotated MP4 with bounding boxes
- **Session Summary**: Auto-saved statistics on exit
- Timestamped filenames: `ekovision_YYYY-MM-DD_HH-MM-SS.{ext}`

**Documentation**: [Data Logging Guide](docs/DATA_LOGGING_GUIDE.md)

#### Phase 3: Runtime Camera Controls ✅

- **Manual Exposure** (`[` / `]`): Adjust shutter speed for motion blur
- **Brightness** (`-` / `+`): Compensate lighting conditions
- **Auto-Exposure Toggle** (`a`): Switch between manual/auto
- **Camera Presets** (`1`/`2`/`3`): Indoor/Outdoor/High Speed
- **Camera Mode** (`c`): Toggle controls on/off

**Documentation**: [Camera Controls Guide](docs/CAMERA_CONTROLS_GUIDE.md)

#### Phase 5: Performance Monitoring ✅

- **Real-time Metrics** (`m`): FPS, GPU/CPU usage, VRAM tracking
- **Performance Graphs** (`g`): Save detailed performance graphs to PNG
- **Warning Indicators**: Color-coded alerts for performance issues
- **Frame Time Breakdown**: Time spent in detection, tracking, classification, rendering

**Documentation**: [Performance Monitoring Guide](docs/PERFORMANCE_MONITORING_GUIDE.md)

### Key Features

- ✅ **80-90% Computational Reduction** - Klasifikasi hanya saat botol di trigger zone
- ✅ **Pure Python** - Tidak ada C++ dependencies
- ✅ **Real-time Performance** - 17+ FPS dengan tracking
- ✅ **Smart Caching** - LRU cache untuk hasil klasifikasi
- ✅ **State Management** - NEW → TRACKED → CLASSIFIED → FAILED
- ✅ **Max Retry Logic** - Maksimal 2 percobaan klasifikasi per botol
- ✅ **YAML Configuration** - Centralized config file (Phase 1)
- ✅ **Data Logging & Export** - CSV/JSON/Video recording (Phase 2)
- ✅ **Runtime Camera Controls** - Adjust exposure/brightness on-the-fly (Phase 3)
- ✅ **Performance Monitoring** - Real-time FPS, GPU/CPU/VRAM tracking (Phase 5)

## System Requirements

### Hardware

- **GPU**: NVIDIA RTX Series (6GB+ VRAM recommended)
- **CPU**: Intel Core i7 / AMD Ryzen 7 or better
- **RAM**: 16GB minimum (32GB recommended)
- **Camera**: USB webcam or industrial camera

### Software

- **OS**: Windows 10/11, Linux, or macOS
- **Python**: 3.8 - 3.11
- **CUDA**: 11.x or 12.x (for GPU acceleration)

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Verify Model Files

Pastikan file-file berikut ada:

- `best.pt` - YOLO model
- `dinov3_multilabel_encoder.pkl` - Encoder
- `label_mapping_dict.joblib` - Mapping dictionary
- `OVR_Checkpoints-20251018T053026Z-1-001/OVR_Checkpoints/` - 314 classifier models

## Running the System

### Basic Usage

```bash
python run_detection_tracking.py
```

### Configuration

**IMPORTANT**: Sistem sekarang menggunakan YAML configuration file.

Edit `config.yaml` untuk mengubah konfigurasi:

```yaml
# Camera settings
camera:
  index: 0 # 0 = default camera, 1 = second camera
  width: 640
  height: 480

# Detection settings
detection:
  confidence_threshold: 0.5 # 0.0 - 1.0

# Trigger zone (percentage of frame)
trigger_zone:
  x_offset_pct: 30.0 # X offset from left (0-50%)
  y_offset_pct: 20.0 # Y offset from top (0-50%)
  width_pct: 40.0 # Zone width (20-80%)
  height_pct: 60.0 # Zone height (20-80%)

# Tracking settings
tracking:
  track_thresh: 0.5
  track_buffer: 30
  match_thresh: 0.8

# Cache settings
cache:
  max_size: 100
  max_classification_attempts: 2

# Logging settings
logging:
  export_dir: "exports"
  video_codec: "mp4v"
  video_fps: 20.0
```

Untuk membuat sample config file:

```bash
python -c "from src.config_loader import ConfigLoader; ConfigLoader.create_sample_config()"
```

Lihat dokumentasi lengkap: [Configuration Guide](docs/CONFIGURATION_GUIDE.md)

## Controls

Saat sistem berjalan, gunakan keyboard controls:

### Basic Controls

| Key | Action                                          |
| --- | ----------------------------------------------- |
| `q` | Quit - Keluar dari aplikasi                     |
| `r` | Reset - Reset pipeline (clear cache & tracking) |
| `s` | Statistics - Tampilkan statistik lengkap        |
| `t` | Toggle - Show/hide trigger zone overlay         |

### Data Export Controls

| Key | Action                                      |
| --- | ------------------------------------------- |
| `e` | Export CSV - Export detection data ke CSV   |
| `j` | Export JSON - Export classification history |
| `v` | Video Recording - Toggle video recording    |

### Camera Controls

| Key | Action                                            |
| --- | ------------------------------------------------- |
| `c` | Camera Mode - Toggle camera control mode          |
| `[` | Exposure Down - Kurangi exposure (faster shutter) |
| `]` | Exposure Up - Tambah exposure (slower shutter)    |
| `-` | Brightness Down - Kurangi brightness              |
| `+` | Brightness Up - Tambah brightness                 |
| `a` | Auto-Exposure - Toggle auto/manual exposure       |
| `1` | Preset Indoor - Optimal untuk indoor lighting     |
| `2` | Preset Outdoor - Optimal untuk outdoor lighting   |
| `3` | Preset High Speed - Optimal untuk conveyor cepat  |

**Note**: Camera controls hanya aktif saat camera control mode diaktifkan (tekan `c`).

### Performance Monitoring Controls

| Key | Action                                       |
| --- | -------------------------------------------- |
| `m` | Toggle Overlay - Show/hide performance stats |
| `g` | Save Graph - Save performance graph to PNG   |

Lihat dokumentasi lengkap:

- [Data Logging Guide](docs/DATA_LOGGING_GUIDE.md)
- [Camera Controls Guide](docs/CAMERA_CONTROLS_GUIDE.md)
- [Performance Monitoring Guide](docs/PERFORMANCE_MONITORING_GUIDE.md)

## Understanding the Display

### Bounding Box Colors

- **Yellow (NEW)**: Botol baru terdeteksi
- **Cyan (TRACKED)**: Botol sedang di-track, belum di trigger zone
- **Green (CLASSIFIED)**: Botol sudah berhasil diklasifikasi
- **Red (FAILED)**: Klasifikasi gagal setelah 2 percobaan

### On-Screen Information

- **Track ID**: ID unik untuk setiap botol
- **8 Attributes**: product, grade, cap, label, brand, type, subtype, volume
- **FPS Counter**: Frame rate real-time
- **Statistics**: Jumlah tracks dan klasifikasi
- **Trigger Zone**: Area hijau semi-transparan (zona trigger)
- **Camera Mode Indicator**: "CAMERA CONTROLS: ON" saat camera mode aktif
- **Performance Overlay**: Real-time FPS, GPU/CPU usage, VRAM (tekan `m` untuk toggle)
- **Recording Indicator**: "● REC" saat video recording aktif
- **Recording Indicator**: "● REC" saat video recording aktif

### Export Files

Saat export data (tekan `e`, `j`, atau `v`), file akan disimpan di folder `exports/`:

- **CSV**: `ekovision_YYYY-MM-DD_HH-MM-SS.csv` - All detection data
- **JSON**: `ekovision_YYYY-MM-DD_HH-MM-SS.json` - Classification history per bottle
- **Summary**: `ekovision_YYYY-MM-DD_HH-MM-SS.summary.json` - Session statistics
- **Video**: `ekovision_YYYY-MM-DD_HH-MM-SS.mp4` - Annotated video recording

Lihat [Data Logging Guide](docs/DATA_LOGGING_GUIDE.md) untuk format detail.

## Performance Optimization

### GPU Acceleration

Sistem otomatis menggunakan GPU jika tersedia:

```
Using device: cuda
```

Jika GPU tidak terdeteksi:

```
Using device: cpu
```

### Expected Performance

- **With GPU**: 15-20 FPS
- **With CPU**: 5-10 FPS (tergantung CPU)
- **Classification Time**: ~33ms untuk 314 classifiers
- **Computational Reduction**: 80-90% vs per-frame classification

## Troubleshooting

### Camera Not Opening

```
✗ Failed to open camera 0
```

**Solution**:

- Cek apakah kamera terhubung
- Coba ubah `camera.index` di `config.yaml` ke 1, 2, dst
- Pastikan tidak ada aplikasi lain yang menggunakan kamera

### Model Not Found

```
✗ YOLO model not found: best.pt
```

**Solution**:

- Pastikan file `best.pt` ada di root directory
- Cek path di `models.yolo_path` di `config.yaml`

### Configuration Error

```
✗ Configuration validation failed
```

**Solution**:

- Cek format YAML di `config.yaml`
- Pastikan semua required fields ada
- Generate sample config: `python -c "from src.config_loader import ConfigLoader; ConfigLoader.create_sample_config()"`
- Lihat [Configuration Guide](docs/CONFIGURATION_GUIDE.md)

### Export Failed

```
✗ Failed to export CSV/JSON
```

**Solution**:

- Pastikan folder `exports/` ada (auto-created jika tidak ada)
- Cek write permissions
- Pastikan disk space cukup
- Lihat [Data Logging Guide](docs/DATA_LOGGING_GUIDE.md)

### Camera Controls Not Working

```
Camera control not responding
```

**Solution**:

- Pastikan camera control mode aktif (tekan `c`)
- Tidak semua kamera support manual exposure control
- Coba gunakan industrial camera dengan manual controls
- Lihat [Camera Controls Guide](docs/CAMERA_CONTROLS_GUIDE.md)

### Low FPS

**Possible causes**:

- GPU tidak terdeteksi (running on CPU)
- Resolution terlalu tinggi
- Terlalu banyak botol di frame
- Video recording aktif (overhead ~2-3 FPS)

**Solutions**:

- Install CUDA dan PyTorch dengan GPU support
- Kurangi `camera.width` dan `camera.height` di `config.yaml`
- Pastikan max 5-10 botol per frame
- Stop video recording jika tidak diperlukan

### Classification Errors

```
Classification error: ...
```

**Solution**:

- Cek apakah semua 314 classifier models ter-load
- Pastikan DINOv3 model ter-download
- Cek VRAM usage (jangan sampai penuh)
- Increase `cache.max_classification_attempts` di `config.yaml` jika perlu

## Architecture Overview

```
┌─────────────┐
│   Camera    │ ← Runtime controls (exposure, brightness, presets)
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────┐
│  Detection-Tracking-Trigger Pipeline   │
├─────────────────────────────────────────┤
│  1. YOLO Detection                      │
│  2. ByteTrack Tracking                  │
│  3. Trigger Zone Check                  │
│  4. DINOv3 + Classifiers (if triggered) │
│  5. LRU Cache                           │
│  6. State Management                    │
└──────┬──────────────────────────────────┘
       │
       ▼
┌─────────────┐
│   Display   │ ← Real-time visualization
│   Logger    │ ← CSV/JSON/Video export
└─────────────┘
```

### Configuration Flow

```
config.yaml
    │
    ├─→ Camera settings
    ├─→ Detection parameters
    ├─→ Trigger zone config
    ├─→ Tracking settings
    ├─→ Cache settings
    ├─→ Model paths
    ├─→ Display options
    └─→ Logging options
```

Lihat [Configuration Guide](docs/CONFIGURATION_GUIDE.md) untuk detail.

## Statistics Interpretation

Press `s` untuk melihat statistik:

```
STATISTICS
============================================================
Frames processed: 1000
Classifications: 150
Reduction: 85.0%
Average FPS: 17.5

Tracker:
  Total tracks: 5
  Active tracks: 3
  Classified: 2
  Failed: 0

Cache:
  Size: 5/100
  Hit rate: 75.0%
  Hits: 300
  Misses: 100
============================================================
```

**Interpretation**:

- **Reduction 85%**: Sistem hanya melakukan klasifikasi 15% dari total frames
- **Hit rate 75%**: 75% requests menggunakan cached results
- **Active tracks 3**: Ada 3 botol yang sedang di-track
- **Classified 2**: 2 botol sudah berhasil diklasifikasi

## Advanced Configuration

### Trigger Zone Tuning

Edit `config.yaml` untuk menyesuaikan trigger zone.

Untuk conveyor belt yang cepat:

```yaml
trigger_zone:
  x_offset_pct: 40.0 # Lebih ke tengah
  y_offset_pct: 30.0
  width_pct: 20.0 # Zone lebih kecil
  height_pct: 40.0
```

Untuk conveyor belt yang lambat:

```yaml
trigger_zone:
  x_offset_pct: 20.0 # Zone lebih lebar
  y_offset_pct: 10.0
  width_pct: 60.0
  height_pct: 80.0
```

### Max Classification Attempts

Edit `config.yaml`:

```yaml
cache:
  max_classification_attempts: 3 # Default: 2
```

### Cache Size

Edit `config.yaml`:

```yaml
cache:
  max_size: 200 # Default: 100
```

### Camera Presets

Edit `config.yaml` untuk custom presets:

```yaml
camera:
  presets:
    indoor:
      exposure: -6 # 1/500 sec
      brightness: 10
      contrast: 1.2
    outdoor:
      exposure: -7 # 1/1000 sec
      brightness: -10
      contrast: 1.0
    high_speed:
      exposure: -8 # 1/2000 sec
      brightness: 0
      contrast: 1.5
```

Lihat [Camera Controls Guide](docs/CAMERA_CONTROLS_GUIDE.md) untuk detail.

## Testing

Run unit tests:

```bash
pytest tests/unit/ -v
```

Expected output:

```
99 passed in 0.85s
```

## Support

Untuk pertanyaan atau issues, silakan buka issue di repository.

## License

[Your License Here]
