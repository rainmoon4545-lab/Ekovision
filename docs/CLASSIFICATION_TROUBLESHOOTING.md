# Troubleshooting: Hasil Klasifikasi Tidak Muncul

Panduan untuk mengatasi masalah ketika botol sudah masuk trigger zone dan memiliki ID, tapi hasil klasifikasi tidak muncul.

---

## Gejala Problem

- ✓ Botol terdeteksi (ada bounding box)
- ✓ Botol memiliki Track ID (contoh: "ID: 1")
- ✓ Botol masuk ke trigger zone (kotak hijau)
- ✗ Hasil klasifikasi tidak muncul (tidak ada text product, grade, cap, dll)

---

## Kemungkinan Penyebab & Solusi

### 1. Botol Belum Cukup Lama di Trigger Zone

**Penyebab:**
Sistem membutuhkan beberapa frame untuk melakukan klasifikasi. Jika botol bergerak terlalu cepat, klasifikasi mungkin belum selesai.

**Solusi:**

```
1. Perlambat gerakan botol
2. Tahan botol di dalam trigger zone selama 1-2 detik
3. Perhatikan perubahan warna bounding box:
   - Kuning (NEW) → Cyan (TRACKED) → Hijau (CLASSIFIED)
```

**Cara Test:**

- Letakkan botol statis di dalam trigger zone
- Tunggu 2-3 detik
- Hasil klasifikasi seharusnya muncul

---

### 2. Confidence Threshold Terlalu Tinggi

**Penyebab:**
Jika confidence threshold terlalu tinggi, sistem akan menolak hasil klasifikasi yang kurang yakin.

**Cek Config:**

```yaml
# config.yaml
classification:
  confidence_threshold: 0.5 # Nilai default
```

**Solusi:**

```yaml
# Turunkan threshold untuk testing
classification:
  confidence_threshold: 0.3 # Lebih permisif
```

**Restart aplikasi setelah edit config.**

---

### 3. Kualitas Gambar Botol Kurang Baik

**Penyebab:**

- Pencahayaan terlalu gelap/terang
- Botol terlalu kecil (terlalu jauh dari kamera)
- Botol blur (gerakan terlalu cepat)
- Botol tertutup objek lain

**Solusi:**

**A. Perbaiki Pencahayaan:**

```
- Tambahkan lampu di area deteksi
- Hindari backlight (cahaya dari belakang)
- Gunakan cahaya putih natural
```

**B. Adjust Jarak Kamera:**

```
- Dekatkan kamera ke conveyor belt
- Pastikan botol mengisi minimal 30% dari frame
- Resolusi botol minimal 100x100 pixel
```

**C. Adjust Camera Settings:**

```
Tekan 'c' saat aplikasi berjalan untuk masuk camera control mode:
- '[' / ']' untuk adjust exposure
- '-' / '+' untuk adjust brightness
- 'a' untuk toggle auto-exposure
```

---

### 4. Max Classification Attempts Tercapai

**Penyebab:**
Sistem memiliki batas maksimal percobaan klasifikasi per track. Jika gagal terus, track akan di-mark sebagai FAILED.

**Cek Config:**

```yaml
# config.yaml
tracking:
  max_classification_attempts: 3 # Default
```

**Solusi:**

```yaml
# Naikkan max attempts
tracking:
  max_classification_attempts: 5 # Lebih banyak percobaan
```

**Cara Identifikasi:**

- Bounding box berubah warna merah
- Text "FAILED" muncul di atas bounding box

---

### 5. Model Classifier Tidak Ter-load dengan Benar

**Penyebab:**
File model classifier rusak atau tidak lengkap.

**Cek Console Output:**

```
Saat startup, harus muncul:
✓ Loaded 308 classifiers
```

**Jika muncul error atau jumlah classifier kurang dari 308:**

**Solusi:**

```bash
# Cek file model ada
dir OVR_Checkpoints\OVR_Checkpoints\*.pkl

# Harus ada 314 file .pkl (308 classifiers + 6 metadata)
```

**Jika file tidak lengkap:**

- Download ulang model files
- Extract ulang dari archive
- Pastikan path benar di config.yaml

---

### 6. Trigger Zone Terlalu Kecil atau Salah Posisi

**Penyebab:**
Trigger zone tidak mencakup area yang tepat, sehingga botol tidak benar-benar masuk zone.

**Cara Cek:**

```
1. Tekan 't' untuk toggle trigger zone visibility
2. Pastikan kotak hijau muncul
3. Perhatikan apakah center botol benar-benar di dalam kotak
```

**Solusi:**

```yaml
# config.yaml - Adjust trigger zone
trigger_zone:
  x_offset_pct: 30.0 # Posisi horizontal (0-100)
  y_offset_pct: 20.0 # Posisi vertikal (0-100)
  width_pct: 40.0 # Lebar zone (0-100)
  height_pct: 60.0 # Tinggi zone (0-100)
```

**Tips:**

- Perbesar zone untuk testing: width_pct: 60, height_pct: 80
- Posisikan zone di tengah frame: x_offset_pct: 20, y_offset_pct: 10

---

### 7. FPS Terlalu Rendah

**Penyebab:**
Jika FPS terlalu rendah (<10 FPS), sistem mungkin tidak sempat melakukan klasifikasi sebelum botol keluar dari zone.

**Cara Cek:**

```
Lihat FPS counter di pojok kiri atas frame
FPS: 25.3  ← Harus >15 FPS
```

**Solusi:**

**A. Kurangi Resolusi Kamera:**

```yaml
camera:
  width: 640 # Dari 1920
  height: 480 # Dari 1080
```

**B. Naikkan Detection Threshold:**

```yaml
detection:
  confidence_threshold: 0.6 # Dari 0.5
```

**C. Gunakan GPU:**

```yaml
device: cuda # Jika ada GPU NVIDIA
```

---

## Debug Script

Gunakan script debug untuk melihat detail proses klasifikasi:

```bash
python debug_classification.py
```

**Output yang diharapkan:**

```
[Frame 30]
  Active tracks: 1
  Total classifications: 0
  Cache size: 0
  FPS: 28.5

  Track ID 1: IN TRIGGER ZONE (waiting classification)
    - Center: (320, 240)
    - Classification attempts: 1

[Frame 60]
  Active tracks: 1
  Total classifications: 1
  Cache size: 1
  FPS: 27.8

  Track ID 1: CLASSIFIED
    - product: Aqua
    - grade: A
    - cap: Blue
    - label: Clear
    - brand: Danone
    - type: PET
    - subtype: Bottle
    - volume: 600ml
```

**Jika tidak ada output "CLASSIFIED":**

- Cek apakah track masuk trigger zone
- Cek classification attempts (harus <max_attempts)
- Cek console untuk error messages

---

## Checklist Troubleshooting

Ikuti checklist ini secara berurutan:

- [ ] Botol terdeteksi dengan bounding box
- [ ] Track ID muncul di atas bounding box
- [ ] Trigger zone visible (tekan 't' jika tidak terlihat)
- [ ] Botol center benar-benar di dalam trigger zone (kotak hijau)
- [ ] Botol diam di zone minimal 2 detik
- [ ] Bounding box berubah warna: Kuning → Cyan → Hijau
- [ ] FPS >15 (lihat pojok kiri atas)
- [ ] Pencahayaan cukup (tidak terlalu gelap/terang)
- [ ] Botol tidak blur (tidak bergerak terlalu cepat)
- [ ] Console tidak menunjukkan error "Classification error"
- [ ] Jumlah classifiers = 308 (cek startup log)

**Jika semua checklist ✓ tapi masih tidak muncul:**

- Jalankan `python debug_classification.py`
- Lihat log detail di console
- Cari error message atau warning

---

## Konfigurasi Optimal untuk Testing

Gunakan konfigurasi ini untuk testing awal:

```yaml
# config.yaml - Optimal untuk testing
camera:
  camera_id: 0
  width: 640
  height: 480
  fps: 30

detection:
  confidence_threshold: 0.5
  iou_threshold: 0.5

classification:
  confidence_threshold: 0.3 # Lebih permisif untuk testing

tracking:
  max_age: 30
  min_hits: 3
  iou_threshold: 0.3
  max_classification_attempts: 5 # Lebih banyak percobaan

trigger_zone:
  x_offset_pct: 20.0 # Zone lebih besar
  y_offset_pct: 10.0
  width_pct: 60.0
  height_pct: 80.0

cache:
  max_size: 100
```

**Setelah testing berhasil, adjust kembali ke nilai optimal.**

---

## Contoh Kasus & Solusi

### Kasus 1: Botol Bergerak Terlalu Cepat

**Gejala:**

- Track ID muncul
- Botol masuk zone
- Tapi langsung keluar sebelum klasifikasi selesai

**Solusi:**

```
1. Perlambat conveyor belt
2. Perbesar trigger zone (width_pct: 70)
3. Kurangi min_hits di tracking (min_hits: 2)
```

---

### Kasus 2: Pencahayaan Buruk

**Gejala:**

- Botol terdeteksi tapi gambar gelap
- Hasil klasifikasi selalu "UNKNOWN"

**Solusi:**

```
1. Tambahkan lampu LED putih
2. Adjust camera brightness:
   - Tekan 'c' untuk camera control
   - Tekan '+' beberapa kali untuk naikkan brightness
3. Adjust exposure:
   - Tekan ']' untuk naikkan exposure
```

---

### Kasus 3: Botol Terlalu Kecil

**Gejala:**

- Botol terdeteksi tapi sangat kecil di frame
- Klasifikasi gagal atau tidak akurat

**Solusi:**

```
1. Dekatkan kamera ke conveyor
2. Zoom in kamera (jika ada fitur zoom)
3. Atau gunakan kamera dengan focal length lebih panjang
```

---

## Bantuan Lebih Lanjut

Jika masalah masih berlanjut:

1. **Jalankan Debug Script:**

   ```bash
   python debug_classification.py
   ```

2. **Capture Screenshot:**
   - Screenshot frame dengan botol di trigger zone
   - Screenshot console output

3. **Cek Log Files:**

   ```
   Lihat folder logs/ untuk error messages
   ```

4. **Test dengan Video File:**

   ```bash
   # Test dengan video sample
   python run_detection_tracking.py --video sample_video.mp4
   ```

5. **Dokumentasi Terkait:**
   - `docs/CONFIGURATION_GUIDE.md` - Penjelasan semua parameter
   - `docs/CAMERA_CONTROLS_GUIDE.md` - Adjust camera settings
   - `RUNNING_GUIDE.md` - Panduan lengkap menjalankan sistem

---

**Dibuat untuk EkoVision PET Detection System**  
**Versi: 1.0**  
**Terakhir diupdate: 2026-02-12**
