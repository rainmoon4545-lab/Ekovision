# Panduan Meningkatkan Akurasi Model YOLO dan DINOv3

Panduan lengkap untuk meningkatkan akurasi deteksi dan klasifikasi tanpa re-training model dari awal.

---

## Daftar Isi

1. [Meningkatkan Akurasi YOLO (Detection)](#1-meningkatkan-akurasi-yolo-detection)
2. [Meningkatkan Akurasi DINOv3 (Classification)](#2-meningkatkan-akurasi-dinov3-classification)
3. [Optimasi Image Quality](#3-optimasi-image-quality)
4. [Post-Processing Techniques](#4-post-processing-techniques)
5. [Data Collection & Fine-tuning](#5-data-collection--fine-tuning)

---

## 1. Meningkatkan Akurasi YOLO (Detection)

### 1.1 Adjust Confidence Threshold

**Cara Termudah** - Tidak perlu re-training!

**Problem**: False positives (deteksi yang salah) atau false negatives (botol tidak terdeteksi)

**Solusi**:

```yaml
# config.yaml
detection:
  confidence_threshold: 0.5  # Default

# Untuk mengurangi false positives (deteksi salah):
  confidence_threshold: 0.6  # Lebih strict

# Untuk mengurangi false negatives (botol tidak terdeteksi):
  confidence_threshold: 0.4  # Lebih permisif
```

**Cara Test**:

```bash
# Test dengan threshold berbeda
python run_detection_tracking.py
# Adjust slider di UI atau edit config.yaml
```

**Rekomendasi**:

- Start: 0.5 (default)
- Production: 0.55-0.65 (balance antara precision dan recall)
- Testing: 0.4-0.45 (catch semua botol)

---

### 1.2 Adjust IoU Threshold

**IoU (Intersection over Union)** = Overlap threshold untuk Non-Maximum Suppression

**Problem**: Multiple boxes untuk satu botol atau boxes yang overlap

**Solusi**:

```yaml
# config.yaml
detection:
  iou_threshold: 0.5  # Default

# Untuk mengurangi duplicate detections:
  iou_threshold: 0.3  # Lebih aggressive NMS

# Untuk keep more detections:
  iou_threshold: 0.7  # Less aggressive NMS
```

**Rekomendasi**:

- Bottles close together: 0.3-0.4
- Bottles far apart: 0.5-0.6

---

### 1.3 Image Preprocessing

**Meningkatkan kualitas input image sebelum YOLO**

#### A. Contrast Enhancement

```python
# Tambahkan di pipeline.py sebelum YOLO inference

import cv2

def enhance_contrast(frame):
    """Enhance contrast using CLAHE"""
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    l = clahe.apply(l)

    enhanced = cv2.merge([l, a, b])
    return cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)

# Usage in _detect_bottles():
frame_enhanced = enhance_contrast(frame_rgb)
results = self.yolo_model(frame_enhanced)
```

#### B. Brightness Normalization

```python
def normalize_brightness(frame, target_mean=128):
    """Normalize image brightness"""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    current_mean = gray.mean()

    if current_mean > 0:
        alpha = target_mean / current_mean
        normalized = cv2.convertScaleAbs(frame, alpha=alpha, beta=0)
        return normalized
    return frame
```

#### C. Denoising

```python
def denoise_frame(frame):
    """Remove noise from frame"""
    return cv2.fastNlMeansDenoisingColored(frame, None, 10, 10, 7, 21)
```

**Rekomendasi**:

- Use CLAHE untuk low-light conditions
- Use brightness normalization untuk varying lighting
- Use denoising untuk noisy cameras

---

### 1.4 Multi-Scale Detection

**Detect bottles at different scales**

```python
def multi_scale_detect(frame, scales=[0.8, 1.0, 1.2]):
    """Run YOLO at multiple scales"""
    all_detections = []

    for scale in scales:
        # Resize frame
        h, w = frame.shape[:2]
        resized = cv2.resize(frame, (int(w*scale), int(h*scale)))

        # Detect
        results = self.yolo_model(resized)

        # Scale back coordinates
        for det in results:
            det.bbox = det.bbox / scale
            all_detections.append(det)

    # Apply NMS to remove duplicates
    return non_max_suppression(all_detections)
```

**Trade-off**: 3x slower, tapi lebih akurat untuk bottles dengan ukuran bervariasi

---

### 1.5 Test-Time Augmentation (TTA)

**Run inference dengan augmented versions**

```python
def tta_detect(frame):
    """Test-time augmentation for detection"""
    detections = []

    # Original
    detections.extend(self.yolo_model(frame))

    # Horizontal flip
    flipped = cv2.flip(frame, 1)
    flipped_dets = self.yolo_model(flipped)
    # Flip back coordinates
    for det in flipped_dets:
        det.bbox[0] = frame.shape[1] - det.bbox[0]
    detections.extend(flipped_dets)

    # Slight rotation
    for angle in [-5, 5]:
        rotated = rotate_image(frame, angle)
        rotated_dets = self.yolo_model(rotated)
        # Rotate back coordinates
        detections.extend(rotate_back(rotated_dets, -angle))

    # Ensemble: vote or average
    return ensemble_detections(detections)
```

**Trade-off**: 4-5x slower, tapi significantly more robust

---

## 2. Meningkatkan Akurasi DINOv3 (Classification)

### 2.1 Adjust Classification Threshold

**Confidence threshold untuk classification results**

```yaml
# config.yaml
classification:
  confidence_threshold: 0.5  # Default

# Untuk lebih strict (less "UNKNOWN"):
  confidence_threshold: 0.4

# Untuk lebih confident (more "UNKNOWN"):
  confidence_threshold: 0.6
```

**Rekomendasi**:

- Production: 0.5 (balanced)
- High precision needed: 0.6-0.7
- High recall needed: 0.3-0.4

---

### 2.2 Improve Crop Quality

**Better crops = better features = better classification**

#### A. Expand Bounding Box

```python
def expand_bbox(bbox, frame_shape, expand_ratio=0.1):
    """Expand bbox to include more context"""
    x1, y1, x2, y2 = bbox
    w, h = x2 - x1, y2 - y1

    # Expand by 10%
    x1 = max(0, x1 - w * expand_ratio)
    y1 = max(0, y1 - h * expand_ratio)
    x2 = min(frame_shape[1], x2 + w * expand_ratio)
    y2 = min(frame_shape[0], y2 + h * expand_ratio)

    return (x1, y1, x2, y2)

# Usage in _classify_bottle():
expanded_bbox = expand_bbox(bbox, frame_pil.size)
image_crop = frame_pil.crop(expanded_bbox)
```

**Benefit**: Include more context around bottle

#### B. Crop Preprocessing

```python
def preprocess_crop(crop):
    """Enhance crop before DINOv3"""
    # Convert to numpy
    crop_np = np.array(crop)

    # Enhance contrast
    lab = cv2.cvtColor(crop_np, cv2.COLOR_RGB2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    l = clahe.apply(l)
    enhanced = cv2.merge([l, a, b])
    enhanced_rgb = cv2.cvtColor(enhanced, cv2.COLOR_LAB2RGB)

    # Convert back to PIL
    return Image.fromarray(enhanced_rgb)
```

#### C. Minimum Crop Size

```python
def ensure_minimum_size(crop, min_size=224):
    """Ensure crop is at least min_size x min_size"""
    w, h = crop.size

    if w < min_size or h < min_size:
        # Pad to minimum size
        new_crop = Image.new('RGB', (max(w, min_size), max(h, min_size)), (128, 128, 128))
        new_crop.paste(crop, ((max(w, min_size) - w) // 2, (max(h, min_size) - h) // 2))
        return new_crop

    return crop
```

**Rekomendasi**:

- Expand bbox: 5-15% (10% default)
- Minimum crop size: 224x224 (DINOv3 input size)
- Preprocess crops untuk low-quality images

---

### 2.3 Feature Augmentation

**Augment features before classification**

```python
def augment_features(features, n_augmentations=3):
    """Augment DINOv3 features"""
    augmented = [features]

    for _ in range(n_augmentations):
        # Add small noise
        noise = np.random.normal(0, 0.01, features.shape)
        augmented.append(features + noise)

    # Average predictions
    return np.mean(augmented, axis=0)
```

**Trade-off**: Slightly slower, tapi more robust

---

### 2.4 Ensemble Classification

**Use multiple crops/angles for same bottle**

```python
def ensemble_classify(frame_pil, bbox):
    """Classify with multiple crops"""
    predictions = []

    # Original crop
    crop = frame_pil.crop(bbox)
    pred1 = self._classify_single(crop)
    predictions.append(pred1)

    # Slightly expanded crop
    expanded = expand_bbox(bbox, frame_pil.size, 0.15)
    crop2 = frame_pil.crop(expanded)
    pred2 = self._classify_single(crop2)
    predictions.append(pred2)

    # Enhanced crop
    enhanced = preprocess_crop(crop)
    pred3 = self._classify_single(enhanced)
    predictions.append(pred3)

    # Vote or average
    return ensemble_predictions(predictions)
```

**Benefit**: More robust, less sensitive to crop quality

---

### 2.5 Classifier Calibration

**Calibrate classifier probabilities**

```python
from sklearn.calibration import CalibratedClassifierCV

# Calibrate classifiers on validation set
calibrated_classifiers = []
for clf in self.classifiers:
    calibrated = CalibratedClassifierCV(clf, method='sigmoid', cv=5)
    calibrated.fit(X_val, y_val)
    calibrated_classifiers.append(calibrated)
```

**Benefit**: Better probability estimates, more reliable confidence scores

---

## 3. Optimasi Image Quality

### 3.1 Camera Settings

**Optimize camera untuk bottle detection**

```yaml
# config.yaml - Optimal settings for bottle detection
camera:
  exposure: 0.002 # 1/500 sec (fast shutter for moving bottles)
  brightness: 10
  contrast: 1.2
  auto_exposure: false
```

**Rekomendasi**:

- Fast shutter (1/500 - 1/2000) untuk moving bottles
- Disable auto-exposure untuk consistent lighting
- Adjust brightness untuk target mean ~128

---

### 3.2 Lighting Setup

**Physical lighting improvements**

**Recommendations**:

1. **Diffuse Lighting**: Avoid harsh shadows
2. **Backlight**: Light from behind camera, not behind bottles
3. **Color Temperature**: 5000-6500K (daylight white)
4. **Intensity**: 500-1000 lux at bottle position

**DIY Setup**:

```
Camera
  ↓
[LED Panel 1]  [LED Panel 2]
      ↘          ↙
        Conveyor Belt
```

---

### 3.3 Background Optimization

**Improve bottle-background contrast**

**Recommendations**:

- Use solid color background (white or light gray)
- Avoid patterns or textures
- Matte finish (not glossy)
- High contrast with bottle colors

---

## 4. Post-Processing Techniques

### 4.1 Temporal Smoothing

**Smooth classifications across frames**

```python
class TemporalSmoother:
    """Smooth classifications over time"""
    def __init__(self, window_size=5):
        self.history = {}
        self.window_size = window_size

    def smooth(self, track_id, current_pred):
        """Smooth prediction using history"""
        if track_id not in self.history:
            self.history[track_id] = []

        self.history[track_id].append(current_pred)

        # Keep only last N predictions
        if len(self.history[track_id]) > self.window_size:
            self.history[track_id].pop(0)

        # Vote: most common prediction
        return self._vote(self.history[track_id])

    def _vote(self, predictions):
        """Majority vote across predictions"""
        from collections import Counter
        result = {}

        for key in predictions[0].keys():
            values = [p[key] for p in predictions]
            most_common = Counter(values).most_common(1)[0][0]
            result[key] = most_common

        return result
```

**Usage**:

```python
# In pipeline
smoother = TemporalSmoother(window_size=5)

# After classification
smoothed_result = smoother.smooth(track_id, classification_result)
```

**Benefit**: Reduce flickering, more stable results

---

### 4.2 Confidence-Based Filtering

**Only accept high-confidence predictions**

```python
def filter_low_confidence(predictions, min_confidence=0.6):
    """Replace low-confidence predictions with UNKNOWN"""
    filtered = {}

    for key, value in predictions.items():
        # Extract confidence if present
        if '(' in value and ')' in value:
            conf_str = value.split('(')[1].split('%')[0]
            confidence = float(conf_str) / 100

            if confidence < min_confidence:
                filtered[key] = "UNKNOWN"
            else:
                filtered[key] = value
        else:
            filtered[key] = value

    return filtered
```

---

### 4.3 Consistency Checking

**Check if predictions make sense**

```python
def check_consistency(predictions):
    """Check if predictions are consistent"""
    # Example: If product is "Aqua", brand should be "Danone"
    rules = {
        'Aqua': {'brand': 'Danone', 'type': 'Water'},
        'Coca-Cola': {'brand': 'Coca-Cola', 'type': 'Soda'},
        # Add more rules
    }

    product = predictions.get('product')
    if product in rules:
        for key, expected in rules[product].items():
            if predictions.get(key) != expected:
                # Fix inconsistency
                predictions[key] = expected

    return predictions
```

---

## 5. Data Collection & Fine-tuning

### 5.1 Collect Misclassified Examples

**Identify and collect errors for fine-tuning**

```python
def log_misclassification(track_id, crop, prediction, ground_truth):
    """Log misclassified examples"""
    # Save crop
    crop.save(f"misclassified/{track_id}_{ground_truth}.jpg")

    # Log to CSV
    with open("misclassifications.csv", "a") as f:
        f.write(f"{track_id},{prediction},{ground_truth}\n")
```

**Usage**:

1. Run system in production
2. Manually label misclassifications
3. Collect 100-500 examples
4. Use for fine-tuning

---

### 5.2 Fine-tune YOLO

**Re-train YOLO dengan data tambahan**

```python
from ultralytics import YOLO

# Load pretrained model
model = YOLO('best.pt')

# Fine-tune on new data
model.train(
    data='bottle_dataset.yaml',
    epochs=50,
    imgsz=640,
    batch=16,
    patience=10,
    save=True,
    device='cuda'
)
```

**Requirements**:

- 500-1000 annotated images (minimum)
- YOLO format annotations
- 2-4 hours training time (GPU)

---

### 5.3 Fine-tune DINOv3 Classifiers

**Re-train classifiers dengan features baru**

```python
# Collect new training data
X_new = []  # DINOv3 features
y_new = []  # Labels

# Extract features from new images
for img_path, label in new_data:
    img = Image.open(img_path)
    features = extract_dinov3_features(img)
    X_new.append(features)
    y_new.append(label)

# Combine with old data
X_combined = np.vstack([X_old, X_new])
y_combined = np.vstack([y_old, y_new])

# Re-train classifiers
for i, clf in enumerate(classifiers):
    clf.fit(X_combined, y_combined[:, i])
    joblib.dump(clf, f'clf_{i}_finetuned.pkl')
```

**Requirements**:

- 100-500 new examples per class
- Balanced dataset
- 30-60 minutes training time

---

## 6. Quick Wins (No Re-training)

### Priority 1: Adjust Thresholds ⭐⭐⭐

**Effort**: 5 minutes  
**Impact**: Medium-High

```yaml
# config.yaml
detection:
  confidence_threshold: 0.55 # From 0.5
  iou_threshold: 0.45 # From 0.5

classification:
  confidence_threshold: 0.45 # From 0.5
```

---

### Priority 2: Improve Lighting ⭐⭐⭐

**Effort**: 1-2 hours (hardware)  
**Impact**: High

- Add LED panels
- Adjust camera exposure
- Use solid background

---

### Priority 3: Expand Bounding Boxes ⭐⭐

**Effort**: 15 minutes (code change)  
**Impact**: Medium

```python
# In pipeline.py
expanded_bbox = expand_bbox(bbox, frame.shape, expand_ratio=0.1)
```

---

### Priority 4: Temporal Smoothing ⭐⭐

**Effort**: 30 minutes (code change)  
**Impact**: Medium

Implement TemporalSmoother class (see section 4.1)

---

### Priority 5: Image Preprocessing ⭐

**Effort**: 1 hour (code change)  
**Impact**: Low-Medium

Add CLAHE contrast enhancement before YOLO

---

## 7. Monitoring & Evaluation

### 7.1 Track Accuracy Metrics

```python
def calculate_metrics(predictions, ground_truth):
    """Calculate accuracy metrics"""
    correct = sum(p == gt for p, gt in zip(predictions, ground_truth))
    total = len(predictions)

    accuracy = correct / total

    # Per-attribute accuracy
    per_attr = {}
    for attr in ['product', 'grade', 'cap', 'label', 'brand', 'type', 'subtype', 'volume']:
        attr_correct = sum(p[attr] == gt[attr] for p, gt in zip(predictions, ground_truth))
        per_attr[attr] = attr_correct / total

    return {
        'overall_accuracy': accuracy,
        'per_attribute': per_attr
    }
```

---

### 7.2 A/B Testing

**Compare different configurations**

```python
# Test configuration A
config_a = {'confidence_threshold': 0.5, 'expand_ratio': 0.0}
accuracy_a = test_configuration(config_a)

# Test configuration B
config_b = {'confidence_threshold': 0.55, 'expand_ratio': 0.1}
accuracy_b = test_configuration(config_b)

# Choose better configuration
best_config = config_a if accuracy_a > accuracy_b else config_b
```

---

## 8. Summary & Recommendations

### Quick Wins (No Re-training)

| Method              | Effort | Impact      | Recommended |
| ------------------- | ------ | ----------- | ----------- |
| Adjust thresholds   | 5 min  | Medium-High | ⭐⭐⭐ YES  |
| Improve lighting    | 1-2 hr | High        | ⭐⭐⭐ YES  |
| Expand bboxes       | 15 min | Medium      | ⭐⭐ YES    |
| Temporal smoothing  | 30 min | Medium      | ⭐⭐ YES    |
| Image preprocessing | 1 hr   | Low-Medium  | ⭐ MAYBE    |

### Advanced (Requires Re-training)

| Method                | Effort  | Impact    | Recommended             |
| --------------------- | ------- | --------- | ----------------------- |
| Fine-tune YOLO        | 4-8 hr  | High      | ⭐⭐⭐ If accuracy <90% |
| Fine-tune classifiers | 2-4 hr  | High      | ⭐⭐⭐ If accuracy <85% |
| Collect more data     | Ongoing | Very High | ⭐⭐⭐ Always           |

### Recommended Implementation Order

1. **Week 1**: Adjust thresholds + Improve lighting
2. **Week 2**: Expand bboxes + Temporal smoothing
3. **Week 3**: Collect misclassified examples
4. **Week 4**: Fine-tune models (if needed)

---

## 9. Expected Improvements

### Realistic Expectations

| Method              | Expected Improvement |
| ------------------- | -------------------- |
| Threshold tuning    | +2-5% accuracy       |
| Better lighting     | +5-10% accuracy      |
| Expand bboxes       | +2-3% accuracy       |
| Temporal smoothing  | +3-5% accuracy       |
| Image preprocessing | +1-3% accuracy       |
| Fine-tuning         | +5-15% accuracy      |

### Combined Effect

**Baseline**: 80% accuracy  
**After quick wins**: 85-90% accuracy (+5-10%)  
**After fine-tuning**: 90-95% accuracy (+10-15%)

---

## 10. Troubleshooting

### Problem: Low Detection Rate

**Symptoms**: Bottles not detected

**Solutions**:

1. Lower confidence threshold (0.4-0.45)
2. Improve lighting
3. Check camera focus
4. Fine-tune YOLO with more data

### Problem: False Positives

**Symptoms**: Non-bottles detected as bottles

**Solutions**:

1. Raise confidence threshold (0.6-0.7)
2. Use solid background
3. Fine-tune YOLO with negative examples

### Problem: Inconsistent Classifications

**Symptoms**: Same bottle classified differently

**Solutions**:

1. Implement temporal smoothing
2. Improve crop quality
3. Use ensemble classification
4. Fine-tune classifiers

---

**Dibuat untuk EkoVision PET Detection System**  
**Versi: 1.0**  
**Terakhir diupdate: 2026-02-13**
