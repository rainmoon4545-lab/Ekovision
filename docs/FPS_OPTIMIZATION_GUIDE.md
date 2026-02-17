# Panduan Optimasi FPS untuk Laptop Low-End

## Spesifikasi Laptop Anda

- **CPU**: Intel Core i3-10110U (2 core, 4 thread, 2.1-2.6 GHz)
- **RAM**: 4GB (3.84GB usable)
- **GPU**: Intel UHD Graphics (integrated, tidak ada GPU dedicated)

## Masalah Saat Ini

FPS yang dihasilkan: **1-2 FPS** (sangat rendah)

## Bottleneck Utama

Sistem computer vision Anda memiliki beberapa operasi berat:

1. **YOLO Detection** - Deteksi objek setiap frame
2. **DINOv3 Feature Extraction** - Ekstraksi fitur 768 dimensi
3. **314 Classifier Models** - Prediksi untuk 8 atribut klasifikasi
4. **Image Preprocessing** - CLAHE, denoising, normalization
5. **Rendering** - Drawing bounding boxes, labels, overlay

## Solusi Optimasi (Prioritas Tinggi ke Rendah)

### 🔴 PRIORITAS 1: Kurangi Resolusi Kamera (DAMPAK BESAR)

**Masalah**: Resolusi 640x480 terlalu besar untuk CPU lemah

**Solusi**: Turunkan ke 320x240 atau 416x416

```yaml
# config.yaml
camera:
  width: 320 # Turun dari 640
  height: 240 # Turun dari 480
```

**Estimasi Peningkatan**: 2-3x lebih cepat (dari 1-2 FPS → 3-6 FPS)

---

### 🔴 PRIORITAS 2: Skip Frame Detection (DAMPAK BESAR)

**Masalah**: YOLO detection berjalan setiap frame (sangat lambat)

**Solusi**: Jalankan detection hanya setiap N frame, gunakan tracking untuk frame lainnya

**Implementasi**: Saya akan membuat modifikasi pada pipeline

**Estimasi Peningkatan**: 3-5x lebih cepat (dari 3-6 FPS → 10-20 FPS)

---

### 🟡 PRIORITAS 3: Disable Image Preprocessing (DAMPAK SEDANG)

**Masalah**: CLAHE, denoising, dan normalization memakan waktu

**Solusi**: Matikan preprocessing

```yaml
# config.yaml
classification:
  enable_preprocessing: false # Ubah dari true
```

**Estimasi Peningkatan**: 1.3-1.5x lebih cepat

---

### 🟡 PRIORITAS 4: Disable Temporal Smoothing (DAMPAK SEDANG)

**Masalah**: Temporal smoothing memerlukan buffer dan komputasi tambahan

**Solusi**: Matikan temporal smoothing

```yaml
# config.yaml
classification:
  enable_temporal_smoothing: false # Ubah dari true
```

**Estimasi Peningkatan**: 1.2x lebih cepat

---

### 🟡 PRIORITAS 5: Kurangi Max Tracks (DAMPAK SEDANG)

**Masalah**: Tracking 20 objek sekaligus memakan resource

**Solusi**: Kurangi max tracks

```yaml
# config.yaml
tracking:
  max_tracks: 5 # Turun dari 20
```

**Estimasi Peningkatan**: 1.2-1.3x lebih cepat

---

### 🟢 PRIORITAS 6: Disable Overlay (DAMPAK KECIL)

**Masalah**: Overlay menambah 4ms per frame

**Solusi**: Matikan overlay sementara untuk testing

**Implementasi**: Saya akan tambahkan opsi config

**Estimasi Peningkatan**: 1.1x lebih cepat

---

### 🟢 PRIORITAS 7: Kurangi Classification Attempts (DAMPAK KECIL)

**Masalah**: Retry classification 2x jika gagal

**Solusi**: Kurangi ke 1x

```yaml
# config.yaml
tracking:
  max_classification_attempts: 1 # Turun dari 2
```

**Estimasi Peningkatan**: 1.1x lebih cepat

---

## Estimasi FPS Setelah Optimasi

| Optimasi                             | FPS Estimasi |
| ------------------------------------ | ------------ |
| Baseline (sekarang)                  | 1-2 FPS      |
| + Resolusi 320x240                   | 3-6 FPS      |
| + Skip Frame (detect setiap 3 frame) | 10-20 FPS    |
| + Disable Preprocessing              | 13-25 FPS    |
| + Disable Temporal Smoothing         | 15-30 FPS    |
| + Max Tracks = 5                     | 18-35 FPS    |

**Target Realistis**: 15-25 FPS dengan semua optimasi

---

## Konfigurasi Optimal untuk Laptop Anda

```yaml
# config.yaml - OPTIMIZED FOR LOW-END LAPTOP

camera:
  index: 0
  width: 320 # ⬇️ Turun dari 640
  height: 240 # ⬇️ Turun dari 480

detection:
  confidence_threshold: 0.55
  iou_threshold: 0.45
  skip_frames: 2 # 🆕 Detect setiap 3 frame (0, 3, 6, 9...)

trigger_zone:
  x_offset_pct: 30.0
  y_offset_pct: 20.0
  width_pct: 40.0
  height_pct: 60.0

tracking:
  max_age: 30
  min_hits: 1
  iou_threshold: 0.3
  max_tracks: 5 # ⬇️ Turun dari 20
  max_classification_attempts: 1 # ⬇️ Turun dari 2

cache:
  max_size: 50 # ⬇️ Turun dari 100 (hemat RAM)

classification:
  confidence_threshold: 0.45
  expand_bbox_ratio: 0.1
  min_crop_size: 224
  enable_temporal_smoothing: false # ⬇️ Matikan
  temporal_window_size: 5
  enable_preprocessing: false # ⬇️ Matikan
  enable_ensemble: false

display:
  show_trigger_zone: true
  show_fps: true
  show_statistics: true
  show_overlay: false # 🆕 Matikan overlay untuk performa maksimal

performance:
  device: "cpu" # Laptop Anda tidak punya GPU dedicated
  warmup_classifiers: true
```

---

## Implementasi Skip Frame Detection

Saya akan memodifikasi pipeline untuk menambahkan fitur skip frame detection.

---

## Rekomendasi Hardware (Jika Budget Ada)

Untuk performa optimal, pertimbangkan upgrade:

1. **RAM**: 8GB atau 16GB (4GB sangat terbatas)
2. **Laptop dengan GPU Dedicated**:
   - NVIDIA GTX 1650 atau lebih tinggi
   - Akan meningkatkan FPS 5-10x lipat
3. **CPU**: Intel i5 atau i7 generasi terbaru (minimal 4 core)

---

## Monitoring Performa

Setelah optimasi, monitor FPS dengan:

- Tekan `F` untuk toggle FPS display
- Lihat console output untuk breakdown waktu per operasi

---

## Troubleshooting

### Jika FPS masih rendah setelah optimasi:

1. **Tutup aplikasi lain** - Browser, IDE, dll memakan RAM
2. **Gunakan Task Manager** - Pastikan tidak ada proses background berat
3. **Cek temperature** - CPU throttling jika terlalu panas
4. **Gunakan power mode "High Performance"** di Windows

---

## Kesimpulan

Dengan laptop spesifikasi Anda (i3, 4GB RAM, no GPU), target realistis adalah:

- **15-25 FPS** dengan semua optimasi
- **Akurasi sedikit berkurang** karena resolusi lebih rendah dan preprocessing dimatikan
- **Trade-off**: Speed vs Accuracy

Untuk production use dengan akurasi tinggi, pertimbangkan upgrade hardware.
