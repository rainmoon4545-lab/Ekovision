# Installation Guide - EkoVision Dependencies

**Date**: February 12, 2026  
**Status**: 8/13 packages installed, 5 missing

---

## Current Status

### ✅ Installed Packages (8/13)

- ✓ opencv-python
- ✓ numpy
- ✓ joblib
- ✓ Pillow
- ✓ scikit-learn
- ✓ hypothesis
- ✓ pytest
- ✓ pyyaml

### ❌ Missing Packages (5/13)

- ✗ torch (PyTorch - Deep Learning framework)
- ✗ transformers (Hugging Face - for DINOv3)
- ✗ ultralytics (YOLOv10 framework)
- ✗ protobuf (Protocol Buffers)
- ✗ pytest-cov (Test coverage tool)

---

## Installation Instructions

### Option 1: Install All Requirements (Recommended)

```bash
pip install -r requirements.txt
```

**Note**: This will install CPU-only PyTorch. For GPU support, see Option 2.

---

### Option 2: Install with GPU Support (Recommended for Production)

#### Step 1: Check CUDA Version

```bash
nvidia-smi
```

Look for "CUDA Version" in the output (e.g., 11.8, 12.1, 12.4)

#### Step 2: Install PyTorch with CUDA Support

**For CUDA 11.8:**

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

**For CUDA 12.1:**

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

**For CUDA 12.4:**

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
```

**For CPU only (no GPU):**

```bash
pip install torch torchvision torchaudio
```

#### Step 3: Install Other Dependencies

```bash
pip install transformers ultralytics protobuf pytest-cov
```

---

### Option 3: Install Missing Packages Only

```bash
pip install torch transformers ultralytics protobuf pytest-cov
```

**Note**: This installs CPU-only PyTorch. For GPU, use Option 2.

---

## Verification

After installation, verify all packages are installed:

```bash
python check_dependencies.py
```

Expected output:

```
✅ All dependencies are installed!
```

---

## Testing After Installation

### 1. Run Integration Tests

```bash
python test_integration.py
```

Expected: 6/6 tests passed

### 2. Run Unit Tests

```bash
pytest tests/unit/ -v
```

Expected: 99 tests passed

### 3. Run Full Test Suite with Coverage

```bash
pytest tests/ -v --cov=src --cov-report=html
```

This will generate a coverage report in `htmlcov/index.html`

---

## Troubleshooting

### Issue: PyTorch CUDA not detected

**Symptom:**

```python
import torch
print(torch.cuda.is_available())  # Returns False
```

**Solution:**

1. Check CUDA version: `nvidia-smi`
2. Reinstall PyTorch with correct CUDA version
3. Verify installation:
   ```python
   import torch
   print(torch.cuda.is_available())  # Should return True
   print(torch.cuda.get_device_name(0))  # Should show GPU name
   ```

### Issue: Ultralytics installation fails

**Solution:**

```bash
pip install ultralytics --no-deps
pip install -r requirements.txt
```

### Issue: Transformers installation fails

**Solution:**

```bash
pip install transformers --no-deps
pip install protobuf<4
pip install transformers
```

### Issue: Out of memory during installation

**Solution:**
Install packages one by one:

```bash
pip install torch
pip install transformers
pip install ultralytics
pip install protobuf
pip install pytest-cov
```

---

## Package Sizes (Approximate)

- **torch**: ~2.5 GB (with CUDA)
- **transformers**: ~500 MB
- **ultralytics**: ~100 MB
- **protobuf**: ~5 MB
- **pytest-cov**: ~1 MB

**Total**: ~3.1 GB

**Disk Space Required**: At least 5 GB free space recommended

---

## Installation Time Estimate

- **Fast internet (100 Mbps)**: 5-10 minutes
- **Medium internet (10 Mbps)**: 20-30 minutes
- **Slow internet (1 Mbps)**: 1-2 hours

---

## Post-Installation Checklist

- [ ] All dependencies installed (`python check_dependencies.py`)
- [ ] PyTorch CUDA available (if GPU installed)
- [ ] Integration tests pass (`python test_integration.py`)
- [ ] Unit tests pass (`pytest tests/unit/ -v`)
- [ ] Model files present (best.pt, dinov3_multilabel_encoder.pkl, etc.)
- [ ] Config file present (config.yaml)

---

## Next Steps After Installation

1. **Run Dependency Check**

   ```bash
   python check_dependencies.py
   ```

2. **Run Integration Tests**

   ```bash
   python test_integration.py
   ```

3. **Run Unit Tests**

   ```bash
   pytest tests/unit/ -v
   ```

4. **Test Main Application** (if camera available)

   ```bash
   python run_detection_tracking.py
   ```

5. **Proceed to Option B or C**
   - Option B: Advanced Features (Phase 5)
   - Option C: Production Deployment

---

## Support

If you encounter any issues during installation:

1. Check the error message carefully
2. Refer to the Troubleshooting section above
3. Check package documentation:
   - PyTorch: https://pytorch.org/get-started/locally/
   - Ultralytics: https://docs.ultralytics.com/
   - Transformers: https://huggingface.co/docs/transformers/

---

**Created By**: Kiro AI Assistant  
**Date**: February 12, 2026
