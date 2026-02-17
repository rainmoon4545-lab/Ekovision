# Mode Optimasi untuk Laptop Low-End

## 🎯 Untuk Siapa?

Mode ini dirancang khusus untuk laptop dengan spesifikasi rendah:

- CPU: Intel i3 atau setara
- RAM: 4GB
- Tidak ada GPU dedicated

## 🚀 Cara Menggunakan

### 1. Gunakan Konfigurasi Optimized

```bash
# Jalankan dengan konfigurasi optimized
python run_optimized.py
```

ATAU gunakan config optimized dengan script biasa:

```bash
# Backup config lama
copy config.yaml config.backup.yaml

# Gunakan config optimized
copy config.optimized.yaml config.yaml

# Jalankan seperti biasa
python run_detection_tracking.py
```

### 2. Perbandingan Performa

| Konfigurasi | FPS       | Akurasi | Resolusi |
| ----------- | --------- | ------- | -------- |
| Default     | 1-2 FPS   | Tinggi  | 640x480  |
| Optimized   | 15-25 FPS | Sedang  | 320x240  |

### 3. Apa yang Dioptimasi?

#### ✅ Resolusi Kamera

- **Default**: 640x480
- **Optimized**: 320x240
- **Dampak**: 2-3x lebih cepat

#### ✅ Skip Frame Detection

- **Default**: Detect setiap frame
- **Optimized**: Detect setiap 3 frame (skip_frames: 2)
- **Dampak**: 3-5x lebih cepat
- **Cara kerja**: YOLO hanya berjalan setiap 3 frame, tracking mengisi gap

#### ✅ Image Preprocessing

- **Default**: CLAHE, denoising, normalization
- **Optimized**: Disabled
- **Dampak**: 1.3-1.5x lebih cepat

#### ✅ Temporal Smoothing

- **Default**: Enabled (5 frame window)
- **Optimized**: Disabled
- **Dampak**: 1.2x lebih cepat

#### ✅ Max Tracks

- **Default**: 20 tracks
- **Optimized**: 5 tracks
- **Dampak**: 1.2-1.3x lebih cepat

#### ✅ Classification Overlay

- **Default**: Enabled
- **Optimized**: Disabled
- **Dampak**: 1.1x lebih cepat

#### ✅ Classification Attempts

- **Default**: 2 attempts
- **Optimized**: 1 attempt
- **Dampak**: 1.1x lebih cepat

## 📊 Estimasi Peningkatan

```
Baseline (default):     1-2 FPS
+ Resolusi 320x240:     3-6 FPS
+ Skip Frame (2):       10-20 FPS
+ No Preprocessing:     13-25 FPS
+ No Temporal:          15-30 FPS
+ Max Tracks 5:         18-35 FPS

Target Realistis: 15-25 FPS
```

## ⚙️ Kustomisasi Lebih Lanjut

Edit `config.optimized.yaml` untuk menyesuaikan:

### Jika FPS masih rendah:

```yaml
camera:
  width: 256 # Turunkan lagi resolusi
  height: 192

classification:
  skip_frames: 4 # Skip lebih banyak frame (detect setiap 5 frame)

tracking:
  max_tracks: 3 # Kurangi max tracks
```

### Jika ingin akurasi lebih tinggi:

```yaml
camera:
  width: 416 # Naikkan resolusi
  height: 416

classification:
  skip_frames: 1 # Detect lebih sering (setiap 2 frame)
  enable_preprocessing: true # Aktifkan preprocessing
```

## 🔧 Troubleshooting

### FPS masih rendah (<10 FPS)

1. **Tutup aplikasi lain**
   - Browser, IDE, dll memakan RAM
   - Gunakan Task Manager untuk cek

2. **Cek temperature CPU**
   - CPU throttling jika terlalu panas
   - Bersihkan ventilasi laptop

3. **Gunakan power mode "High Performance"**
   - Windows Settings → Power & Battery → Power Mode

4. **Kurangi resolusi lebih lanjut**

   ```yaml
   camera:
     width: 256
     height: 192
   ```

5. **Skip lebih banyak frame**
   ```yaml
   classification:
     skip_frames: 4 # Detect setiap 5 frame
   ```

### Akurasi menurun drastis

1. **Naikkan resolusi sedikit**

   ```yaml
   camera:
     width: 416
     height: 416
   ```

2. **Aktifkan preprocessing**

   ```yaml
   classification:
     enable_preprocessing: true
   ```

3. **Kurangi skip frame**
   ```yaml
   classification:
     skip_frames: 1 # Detect setiap 2 frame
   ```

## 📈 Monitoring Performa

Saat menjalankan, perhatikan:

```
Frame 30: FPS=18.5, Tracks=3, Classifications=12
Frame 60: FPS=19.2, Tracks=2, Classifications=24
Frame 90: FPS=18.8, Tracks=4, Classifications=35
```

- **FPS**: Harus stabil di 15-25 FPS
- **Tracks**: Jumlah botol yang dilacak
- **Classifications**: Total klasifikasi yang berhasil

## 🎮 Keyboard Controls

- **Q**: Quit
- **T**: Toggle trigger zone
- **S**: Save current frame
- **R**: Reset tracker
- **SPACE**: Pause/Resume

## 💡 Tips Tambahan

1. **Gunakan kamera eksternal dengan resolusi rendah native**
   - Beberapa kamera eksternal lebih efisien di resolusi rendah

2. **Matikan Windows Defender saat testing**
   - Real-time scanning bisa memperlambat

3. **Gunakan SSD jika ada**
   - Loading model lebih cepat

4. **Tutup Windows Update**
   - Background update memakan resource

## 🔄 Kembali ke Mode Normal

```bash
# Restore config lama
copy config.backup.yaml config.yaml

# Atau jalankan script biasa
python run_detection_tracking.py
```

## 📝 Catatan Penting

- **Trade-off**: Speed vs Accuracy
- Resolusi rendah = deteksi kurang akurat untuk objek kecil
- Skip frame = bisa miss objek yang bergerak cepat
- No preprocessing = akurasi klasifikasi sedikit menurun

Untuk production use dengan akurasi tinggi, pertimbangkan upgrade hardware:

- RAM: 8GB atau 16GB
- GPU: NVIDIA GTX 1650 atau lebih tinggi
- CPU: Intel i5/i7 atau AMD Ryzen 5/7

## 📚 Dokumentasi Lengkap

Lihat `docs/FPS_OPTIMIZATION_GUIDE.md` untuk penjelasan detail tentang setiap optimasi.
