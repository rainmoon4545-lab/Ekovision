# Project Structure - Detection-Tracking-Trigger System

## Clean Directory Structure

```
project/
│
├── 📁 src/                          # Source code
│   ├── __init__.py
│   └── tracking/                    # Tracking components
│       ├── __init__.py
│       ├── bytetrack.py            # Pure Python ByteTrack
│       ├── trigger_zone.py         # Trigger zone logic
│       ├── bottle_tracker.py       # State management
│       ├── classification_cache.py # LRU cache
│       └── pipeline.py             # Main pipeline
│
├── 📁 tests/                        # Test suite
│   ├── __init__.py
│   ├── conftest.py                 # Pytest configuration
│   ├── unit/                       # Unit tests (99 tests)
│   │   ├── __init__.py
│   │   ├── test_bytetrack.py      # 17 tests
│   │   ├── test_trigger_zone.py   # 24 tests
│   │   ├── test_bottle_tracker.py # 27 tests
│   │   └── test_classification_cache.py # 31 tests
│   └── property/                   # Property-based tests (optional)
│       └── __init__.py
│
├── 📁 .kiro/                        # Spec files
│   └── specs/
│       └── detection-tracking-trigger/
│           ├── requirements.md
│           ├── design.md
│           └── tasks.md
│
├── 📁 OVR_Checkpoints-.../          # Classifier models
│   └── OVR_Checkpoints/
│       ├── clf_0_1.pkl
│       ├── clf_1_100ml.pkl
│       └── ... (314 classifiers)
│
├── 🎯 run_detection_tracking.py    # ⭐ MAIN APPLICATION
├── 📋 test_pipeline_import.py      # Quick dependency test
├── 📊 benchmark_classifiers.py     # Performance benchmark
│
├── 📄 requirements.txt              # Python dependencies
├── 📄 pytest.ini                   # Pytest configuration
│
├── 🤖 best.pt                       # YOLO model
├── 🤖 dinov3_multilabel_encoder.pkl # Encoder
├── 🤖 label_mapping_dict.joblib    # Label mapping
│
├── 📖 README.md                     # Project overview
├── 📖 RUNNING_GUIDE.md             # User guide
├── 📖 PROJECT_REVIEW.md            # Compliance review
├── 📖 PROJECT_STRUCTURE.md         # This file
├── 📊 BENCHMARK_RESULTS.md         # Performance results
└── 📊 benchmark_results.json       # Benchmark data
```

## File Categories

### 🎯 Essential Files (Must Have)

**Application**:

- `run_detection_tracking.py` - Main application entry point
- `src/tracking/*.py` - All tracking components
- `requirements.txt` - Python dependencies

**Models**:

- `best.pt` - YOLO detection model
- `dinov3_multilabel_encoder.pkl` - Label encoder
- `label_mapping_dict.joblib` - Mapping dictionary
- `OVR_Checkpoints-*/` - 314 classifier models

### 📖 Documentation Files

- `RUNNING_GUIDE.md` - How to run the system
- `PROJECT_REVIEW.md` - Compliance & review
- `PROJECT_STRUCTURE.md` - This file
- `BENCHMARK_RESULTS.md` - Performance analysis
- `README.md` - Project overview

### 🧪 Testing Files

- `tests/unit/*.py` - 99 unit tests
- `test_pipeline_import.py` - Quick dependency check
- `benchmark_classifiers.py` - Performance benchmark
- `pytest.ini` - Test configuration

### 📋 Spec Files (Reference)

- `.kiro/specs/detection-tracking-trigger/` - Requirements, design, tasks

### 🗑️ Removed Files (Legacy)

- ~~`app.py`~~ - Old Streamlit application (deleted)
- ~~`app_cursor.py`~~ - Old Streamlit application (deleted)
- ~~`realtime_test.py`~~ - Old test script (deleted)
- ~~`.streamlit/`~~ - Streamlit config folder (deleted)

## Quick Start

### 1. Verify Dependencies

```bash
python test_pipeline_import.py
```

### 2. Run System

```bash
python run_detection_tracking.py
```

### 3. Run Tests

```bash
pytest tests/unit/ -v
```

## File Sizes (Approximate)

| Category      | Files         | Size        |
| ------------- | ------------- | ----------- |
| Source Code   | 6 files       | ~50 KB      |
| Tests         | 4 files       | ~40 KB      |
| Models        | 316 files     | ~500 MB     |
| Documentation | 5 files       | ~100 KB     |
| **Total**     | **331 files** | **~500 MB** |

## Dependencies

See `requirements.txt` for complete list. Key dependencies:

- `torch` - PyTorch for GPU acceleration
- `opencv-python` - Camera input & visualization
- `ultralytics` - YOLO detection
- `transformers` - DINOv3 feature extraction
- `scikit-learn` - Classifiers
- `numpy`, `joblib`, `Pillow` - Utilities
- `pytest`, `hypothesis` - Testing

## Notes

- All Streamlit references removed
- Pure Python implementation (no C++ dependencies)
- 99 unit tests (100% passing)
- Ready for production proof-of-concept
- Clean, minimal structure
