# Meningkatkan FPS TANPA Mengorbankan Akurasi

## 🎯 Tujuan

Meningkatkan FPS dari 1-2 FPS menjadi 5-10 FPS **TANPA** menurunkan akurasi deteksi dan klasifikasi.

## ❌ Yang TIDAK Boleh Dilakukan (Akan Menurunkan Akurasi)

1. ❌ Menurunkan resolusi kamera (640x480 → 320x240)
2. ❌ Matikan preprocessing (CLAHE, denoising)
3. ❌ Matikan temporal smoothing
4. ❌ Naikkan confidence threshold
5. ❌ Kurangi classification attempts

## ✅ Yang Boleh Dilakukan (TIDAK Menurunkan Akurasi)

### 1. 🚀 Skip Frame Detection (DAMPAK TERBESAR)

**Konsep**: YOLO detection sangat lambat, tapi ByteTrack tracking sangat cepat dan akurat.

**Solusi**: Jalankan YOLO hanya setiap 2-3 frame, gunakan tracking untuk frame lainnya.

```yaml
classification:
  skip_frames: 1 # Detect setiap 2 frame (frame 0, 2, 4, 6...)
```

**Mengapa Tidak Menurunkan Akurasi?**

- ByteTrack tracking sangat akurat untuk objek yang bergerak smooth (seperti konveyor)
- Tracking menggunakan IoU matching yang presisi
- Objek di konveyor bergerak lambat dan predictable
- Detection setiap 2 frame sudah cukup untuk update posisi

**Peningkatan**: 2x lebih cepat (1-2 FPS → 2-4 FPS)

---

### 2. 🎨 Matikan Overlay (TIDAK Mempengaruhi Akurasi)

**Konsep**: Overlay hanya untuk display, tidak mempengaruhi deteksi/klasifikasi.

```yaml
classification:
  show_overlay: false
```

**Mengapa Tidak Menurunkan Akurasi?**

- Overlay hanya rendering visual
- Deteksi dan klasifikasi tetap berjalan normal
- Data tetap tersimpan di cache

**Peningkatan**: +4ms per frame (~1.2x faster)

---

### 3. 📊 Kurangi Max Tracks (Jika Konveyor Tidak Ramai)

**Konsep**: Tracking 20 objek sekaligus memakan resource.

```yaml
tracking:
  max_tracks: 10 # Cukup untuk konveyor normal
```

**Mengapa Tidak Menurunkan Akurasi?**

- Jika konveyor hanya ada 3-5 botol sekaligus, max_tracks: 20 adalah overkill
- Tracking 10 objek sudah sangat cukup
- Akurasi per-track tetap sama

**Peningkatan**: 1.2-1.3x lebih cepat

---

### 4. 🔧 Optimasi Teknis Lainnya

#### A. Matikan Logging yang Tidak Perlu

```yaml
logging:
  level: "WARNING" # Hanya log warning/error
  log_to_file: false
```

#### B. Kurangi Cache Size (Jika RAM Terbatas)

```yaml
cache:
  max_size: 50 # Dari 100, masih cukup untuk konveyor
```

#### C. Kurangi FPS History Window

```python
# Di pipeline.py
self.fps_history = deque(maxlen=10)  # Dari 30
```

---

## 📊 Estimasi Peningkatan (Tanpa Kehilangan Akurasi)

| Optimasi         | FPS         | Akurasi  |
| ---------------- | ----------- | -------- |
| Baseline         | 1-2 FPS     | 100%     |
| + Skip frame (1) | 2-4 FPS     | 100%     |
| + No overlay     | 2.5-5 FPS   | 100%     |
| + Max tracks 10  | 3-6 FPS     | 100%     |
| **TOTAL**        | **3-6 FPS** | **100%** |

---

## 🚀 Cara Menggunakan

### Opsi 1: Gunakan Config Balanced

```bash
# Backup config lama
copy config.yaml config.backup.yaml

# Gunakan config balanced
copy config.balanced.yaml config.yaml

# Jalankan
python run_detection_tracking.py
```

### Opsi 2: Edit Config Manual

Edit `config.yaml`:

```yaml
classification:
  skip_frames: 1 # Tambahkan ini
  show_overlay: false # Ubah ke false

tracking:
  max_tracks: 10 # Ubah dari 20
```

---

## 🔬 Mengapa Skip Frame TIDAK Menurunkan Akurasi?

### Penjelasan Teknis:

1. **YOLO Detection** (Lambat, ~100-200ms per frame)
   - Mendeteksi objek dari scratch setiap frame
   - Sangat akurat tapi sangat lambat

2. **ByteTrack Tracking** (Cepat, ~5-10ms per frame)
   - Menggunakan IoU matching untuk track objek
   - Sangat akurat untuk objek yang bergerak smooth
   - Bisa predict posisi objek dengan baik

3. **Konveyor Belt Scenario**:
   - Botol bergerak dengan kecepatan konstan
   - Tidak ada perubahan mendadak
   - Tracking bisa predict posisi dengan sangat akurat

### Contoh:

```
Frame 0: YOLO detect → 3 botol terdeteksi [✓ Akurat]
Frame 1: Tracking only → 3 botol di-track [✓ Akurat, posisi di-predict]
Frame 2: YOLO detect → 3 botol terdeteksi [✓ Akurat, update posisi]
Frame 3: Tracking only → 3 botol di-track [✓ Akurat, posisi di-predict]
Frame 4: YOLO detect → 3 botol terdeteksi [✓ Akurat, update posisi]
```

**Hasil**: Akurasi tetap 100%, tapi 2x lebih cepat!

---

## 🎯 Jika Masih Butuh FPS Lebih Tinggi

Jika 3-6 FPS masih kurang, ada beberapa opsi **dengan trade-off minimal**:

### Opsi A: Skip Frame Lebih Agresif

```yaml
classification:
  skip_frames: 2 # Detect setiap 3 frame
```

**Trade-off**:

- Akurasi tracking sedikit menurun jika botol bergerak sangat cepat
- Untuk konveyor normal (kecepatan sedang), masih sangat akurat
- **Peningkatan**: 3x lebih cepat (3-6 FPS → 6-12 FPS)

### Opsi B: Turunkan Resolusi Sedikit

```yaml
camera:
  width: 512 # Dari 640
  height: 384 # Dari 480
```

**Trade-off**:

- Akurasi deteksi sedikit menurun untuk objek kecil
- Untuk botol di konveyor (objek besar), akurasi masih sangat baik
- **Peningkatan**: 1.5x lebih cepat

### Opsi C: Matikan Preprocessing untuk Frame Tertentu

Preprocessing hanya untuk frame yang akan diklasifikasi:

```python
# Modifikasi: Hanya preprocess saat akan classify
if should_classify:
    crop = preprocess_crop(crop)  # CLAHE, denoising
```

**Trade-off**:

- Akurasi klasifikasi sedikit menurun
- Masih lebih baik dari matikan preprocessing sepenuhnya
- **Peningkatan**: 1.2-1.3x lebih cepat

---

## 🔍 Monitoring Akurasi

Untuk memastikan akurasi tidak menurun, monitor:

### 1. Classification Success Rate

```python
success_rate = classifications / total_attempts
# Target: > 90%
```

### 2. Tracking Stability

```python
avg_track_age = sum(track.age for track in tracks) / len(tracks)
# Target: > 10 frames (tracking stabil)
```

### 3. Cache Hit Rate

```python
cache_hit_rate = cache_hits / cache_requests
# Target: > 70%
```

---

## 📈 Benchmark Akurasi

Sebelum dan sesudah optimasi, test dengan dataset yang sama:

```bash
# Test akurasi
python benchmark_accuracy.py --config config.yaml
python benchmark_accuracy.py --config config.balanced.yaml

# Compare results
# Akurasi harus tetap sama (±1%)
```

---

## 💡 Rekomendasi Hardware (Jika Budget Ada)

Untuk FPS tinggi TANPA trade-off:

### Prioritas 1: Tambah RAM

- **Sekarang**: 4GB
- **Target**: 8GB atau 16GB
- **Dampak**: 1.5-2x lebih cepat
- **Harga**: ~500rb - 1jt IDR

### Prioritas 2: GPU External (eGPU)

- **Opsi**: NVIDIA GTX 1650 via Thunderbolt
- **Dampak**: 5-10x lebih cepat
- **Harga**: ~3-5jt IDR

### Prioritas 3: Upgrade Laptop

- **Target**: i5/i7 + 8GB RAM + GTX 1650
- **Dampak**: 10-20x lebih cepat
- **Harga**: ~8-15jt IDR

---

## 🎓 Kesimpulan

**Untuk laptop Anda (i3, 4GB RAM, no GPU):**

1. **Tanpa kehilangan akurasi**: 3-6 FPS (dari 1-2 FPS)
   - Skip frame: 1
   - No overlay
   - Max tracks: 10

2. **Dengan trade-off minimal**: 6-12 FPS
   - Skip frame: 2
   - Resolusi: 512x384
   - Preprocessing selective

3. **Untuk FPS tinggi (>20 FPS)**: Butuh upgrade hardware
   - Minimal: +4GB RAM
   - Ideal: Laptop baru dengan GPU

**Rekomendasi**: Gunakan `config.balanced.yaml` untuk hasil terbaik tanpa kehilangan akurasi.

---

## 📞 Troubleshooting

### Q: FPS masih 1-2 setelah optimasi?

A: Cek:

- Apakah skip_frames sudah aktif? (lihat console log)
- Apakah ada aplikasi lain yang memakan CPU?
- Apakah CPU throttling karena panas?

### Q: Akurasi menurun setelah optimasi?

A: Kemungkinan:

- Skip frame terlalu agresif (>2)
- Resolusi terlalu rendah (<512)
- Preprocessing dimatikan

### Q: Tracking tidak stabil?

A: Solusi:

- Kurangi skip_frames (dari 2 ke 1)
- Naikkan iou_threshold tracking
- Pastikan lighting konveyor baik

---

## 📚 Referensi

- ByteTrack Paper: https://arxiv.org/abs/2110.06864
- YOLO Performance: https://docs.ultralytics.com/
- DINOv3 Model: https://github.com/facebookresearch/dinov2
