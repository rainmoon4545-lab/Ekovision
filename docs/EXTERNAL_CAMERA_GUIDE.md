# Panduan Menghubungkan Kamera Eksternal ke EkoVision

Panduan lengkap untuk menggunakan kamera eksternal (USB webcam, IP camera, dll) dengan sistem EkoVision.

---

## Daftar Isi

1. [Persiapan Hardware](#persiapan-hardware)
2. [Deteksi Kamera Tersedia](#deteksi-kamera-tersedia)
3. [Konfigurasi Kamera](#konfigurasi-kamera)
4. [Troubleshooting](#troubleshooting)
5. [Tips Pemilihan Kamera](#tips-pemilihan-kamera)

---

## Persiapan Hardware

### Jenis Kamera yang Didukung

EkoVision mendukung berbagai jenis kamera:

1. **USB Webcam**
   - Webcam USB standar (Logitech, Microsoft, dll)
   - Kamera DSLR/Mirrorless dengan USB output
   - Kamera industri dengan interface USB

2. **Kamera Laptop Built-in**
   - Kamera bawaan laptop (biasanya Camera ID 0)

3. **IP Camera** (dengan konfigurasi tambahan)
   - RTSP stream
   - HTTP/MJPEG stream

### Langkah Persiapan

1. **Hubungkan Kamera ke Laptop**

   ```
   - Colokkan kabel USB kamera ke port USB laptop
   - Tunggu hingga Windows mendeteksi perangkat
   - Pastikan lampu indikator kamera menyala (jika ada)
   ```

2. **Verifikasi Driver Terinstall**

   ```
   - Buka Device Manager (Win + X → Device Manager)
   - Cari "Cameras" atau "Imaging devices"
   - Pastikan kamera muncul tanpa tanda seru kuning
   ```

3. **Test Kamera di Windows**
   ```
   - Buka aplikasi Camera bawaan Windows
   - Pastikan kamera dapat menampilkan gambar
   - Coba switch antar kamera jika ada lebih dari satu
   ```

---

## Deteksi Kamera Tersedia

### Metode 1: Menggunakan Script Deteksi (Recommended)

Jalankan script deteksi kamera yang disediakan:

```bash
python detect_cameras.py
```

**Output yang diharapkan:**

```
======================================================================
EKOVISION - DETEKSI KAMERA TERSEDIA
======================================================================

Mencari kamera yang tersedia di sistem...
(Proses ini mungkin memakan waktu beberapa detik)

✓ Kamera 0 ditemukan:
  - Resolusi: 640x480
  - FPS: 30

✓ Kamera 1 ditemukan:
  - Resolusi: 1920x1080
  - FPS: 30

======================================================================
RINGKASAN
======================================================================
Total kamera ditemukan: 2

Camera ID 0: Kamera Laptop (Built-in)
  Resolusi: 640x480, FPS: 30
Camera ID 1: Kamera Eksternal #1
  Resolusi: 1920x1080, FPS: 30
```

### Metode 2: Test Manual dengan Python

Jika script deteksi tidak bekerja, coba test manual:

```python
import cv2

# Test camera ID 0, 1, 2, dst
for i in range(5):
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        print(f"Camera {i}: Available")
        cap.release()
    else:
        print(f"Camera {i}: Not available")
```

---

## Konfigurasi Kamera

### Langkah 1: Edit config.yaml

Buka file `config.yaml` dan ubah bagian `camera`:

```yaml
camera:
  camera_id: 1 # Ganti dengan ID kamera eksternal Anda
  width: 1920 # Sesuaikan dengan resolusi kamera
  height: 1080
  fps: 30
```

**Penjelasan Parameter:**

- `camera_id`: ID kamera yang ditemukan dari script deteksi
  - `0` = Kamera laptop built-in (default)
  - `1` = Kamera eksternal pertama
  - `2` = Kamera eksternal kedua, dst

- `width` & `height`: Resolusi video
  - Gunakan resolusi yang didukung kamera Anda
  - Resolusi umum: 640x480, 1280x720, 1920x1080

- `fps`: Frame rate
  - Biasanya 30 FPS untuk webcam standar
  - Beberapa kamera mendukung 60 FPS

### Langkah 2: Test Konfigurasi

Jalankan aplikasi untuk test kamera:

```bash
# Test dengan mode deteksi biasa
python run_detection_tracking.py

# Test dengan web dashboard
python run_web_dashboard.py
```

### Langkah 3: Verifikasi

Pastikan:

- ✓ Video stream muncul dengan jelas
- ✓ Tidak ada lag atau frame drop
- ✓ Resolusi sesuai dengan yang dikonfigurasi
- ✓ FPS stabil (cek dengan Performance Monitor)

---

## Troubleshooting

### Problem 1: Kamera Tidak Terdeteksi

**Gejala:**

```
✗ Tidak ada kamera yang ditemukan!
```

**Solusi:**

1. **Cek Koneksi Fisik**

   ```
   - Cabut dan colokkan ulang kabel USB
   - Coba port USB yang berbeda
   - Pastikan kabel tidak rusak
   ```

2. **Cek Device Manager**

   ```
   - Buka Device Manager
   - Cari kamera di "Cameras" atau "Imaging devices"
   - Jika ada tanda seru kuning, update driver
   ```

3. **Restart Kamera**

   ```
   - Cabut kamera dari USB
   - Tunggu 10 detik
   - Colokkan kembali
   ```

4. **Tutup Aplikasi Lain**
   ```
   - Tutup aplikasi yang mungkin menggunakan kamera:
     * Zoom, Skype, Teams
     * OBS Studio
     * Aplikasi Camera Windows
   ```

### Problem 2: Kamera Terdeteksi Tapi Tidak Ada Gambar

**Gejala:**

```
Camera opened: 0x0
atau
Black screen / frozen frame
```

**Solusi:**

1. **Coba Camera ID Berbeda**

   ```yaml
   camera:
     camera_id: 0 # Coba 0, 1, 2, dst
   ```

2. **Kurangi Resolusi**

   ```yaml
   camera:
     width: 640
     height: 480
   ```

3. **Tambahkan Delay Inisialisasi**
   - Beberapa kamera butuh waktu warm-up
   - Tunggu 2-3 detik setelah aplikasi start

### Problem 3: FPS Rendah / Lag

**Gejala:**

```
FPS: 5-10 (seharusnya 25-30)
Video terlihat patah-patah
```

**Solusi:**

1. **Kurangi Resolusi**

   ```yaml
   camera:
     width: 640 # Dari 1920
     height: 480 # Dari 1080
   ```

2. **Gunakan USB 3.0 Port**
   - Port USB 3.0 (biru) lebih cepat dari USB 2.0
   - Hindari USB hub, colok langsung ke laptop

3. **Tutup Aplikasi Background**
   - Tutup aplikasi yang menggunakan banyak resource
   - Cek Task Manager untuk CPU/GPU usage

4. **Adjust Detection Settings**
   ```yaml
   detection:
     confidence_threshold: 0.6 # Naikkan threshold
     iou_threshold: 0.5
   ```

### Problem 4: Kamera Disconnect Tiba-tiba

**Gejala:**

```
Camera error: Unable to read frame
Connection lost
```

**Solusi:**

1. **Cek Kabel dan Port**
   - Gunakan kabel USB berkualitas baik
   - Hindari kabel yang terlalu panjang (>3 meter)
   - Gunakan port USB yang stabil

2. **Disable USB Power Saving**

   ```
   - Control Panel → Power Options
   - Change plan settings → Advanced
   - USB settings → USB selective suspend → Disabled
   ```

3. **Update USB Driver**
   - Device Manager → Universal Serial Bus controllers
   - Right-click → Update driver

### Problem 5: Warna Tidak Akurat

**Gejala:**

```
Warna terlalu gelap/terang
Warna tidak natural
```

**Solusi:**

1. **Adjust Kamera Settings**
   - Gunakan software kamera untuk adjust:
     - Brightness
     - Contrast
     - Saturation
     - White balance

2. **Perbaiki Pencahayaan**
   - Tambahkan lampu di area deteksi
   - Hindari backlight (cahaya dari belakang objek)
   - Gunakan cahaya putih natural

---

## Tips Pemilihan Kamera

### Untuk Deteksi Botol PET

Rekomendasi spesifikasi kamera:

1. **Resolusi Minimum**
   - 720p (1280x720) untuk jarak dekat (<2 meter)
   - 1080p (1920x1080) untuk jarak menengah (2-4 meter)
   - 4K untuk jarak jauh (>4 meter)

2. **Frame Rate**
   - Minimum 30 FPS
   - 60 FPS lebih baik untuk conveyor belt cepat

3. **Field of View (FOV)**
   - 60-90° untuk area kecil
   - 90-120° untuk area luas

4. **Fitur Tambahan**
   - Auto-focus untuk jarak bervariasi
   - Low-light performance untuk pencahayaan rendah
   - Manual exposure control

### Kamera yang Direkomendasikan

**Budget (<500k):**

- Logitech C270 (720p, 30fps)
- Microsoft LifeCam HD-3000

**Mid-range (500k-1.5jt):**

- Logitech C920 (1080p, 30fps) ⭐ Recommended
- Logitech C922 (1080p, 60fps)
- Microsoft LifeCam Studio

**High-end (>1.5jt):**

- Logitech Brio (4K, 60fps)
- Razer Kiyo Pro
- Elgato Facecam

**Industrial:**

- Basler USB3 Vision cameras
- FLIR USB3 cameras
- IDS uEye cameras

---

## Konfigurasi IP Camera (Advanced)

Jika menggunakan IP camera dengan RTSP stream:

### Langkah 1: Dapatkan RTSP URL

Format umum:

```
rtsp://username:password@ip_address:port/stream
```

Contoh:

```
rtsp://admin:admin123@192.168.1.100:554/stream1
```

### Langkah 2: Modifikasi camera_controller.py

Edit `src/camera_controller.py`:

```python
# Ganti camera_id dengan RTSP URL
def __init__(self, camera_id="rtsp://admin:admin123@192.168.1.100:554/stream1", ...):
    self.camera_id = camera_id
    # ... rest of code
```

### Langkah 3: Test Koneksi

```python
import cv2

rtsp_url = "rtsp://admin:admin123@192.168.1.100:554/stream1"
cap = cv2.VideoCapture(rtsp_url)

if cap.isOpened():
    print("✓ IP Camera connected")
else:
    print("✗ Connection failed")
```

---

## Checklist Setup Kamera Eksternal

Gunakan checklist ini untuk memastikan setup berhasil:

- [ ] Kamera terhubung ke laptop via USB
- [ ] Driver kamera terinstall (cek Device Manager)
- [ ] Kamera berfungsi di aplikasi Camera Windows
- [ ] Script `detect_cameras.py` mendeteksi kamera
- [ ] Camera ID sudah dicatat
- [ ] File `config.yaml` sudah diupdate dengan camera_id yang benar
- [ ] Resolusi dan FPS sudah disesuaikan
- [ ] Test run aplikasi berhasil
- [ ] Video stream muncul dengan jelas
- [ ] FPS stabil (25-30 FPS)
- [ ] Tidak ada error di console

---

## Contoh Konfigurasi Lengkap

### Scenario 1: Webcam USB Logitech C920

```yaml
camera:
  camera_id: 1 # Kamera eksternal pertama
  width: 1920
  height: 1080
  fps: 30
```

### Scenario 2: Webcam Budget 720p

```yaml
camera:
  camera_id: 1
  width: 1280
  height: 720
  fps: 30
```

### Scenario 3: Dual Camera Setup

Untuk menggunakan 2 kamera sekaligus, jalankan 2 instance aplikasi:

**Terminal 1 (Kamera 1):**

```bash
# Edit config.yaml: camera_id: 1
python run_detection_tracking.py
```

**Terminal 2 (Kamera 2):**

```bash
# Edit config2.yaml: camera_id: 2
python run_detection_tracking.py --config config2.yaml
```

---

## Bantuan Lebih Lanjut

Jika masih mengalami masalah:

1. **Jalankan Diagnostic Script**

   ```bash
   python detect_cameras.py
   ```

2. **Cek Log File**

   ```
   Lihat file log di folder logs/
   Cari error message untuk troubleshooting
   ```

3. **Test dengan OpenCV Langsung**

   ```python
   import cv2
   cap = cv2.VideoCapture(1)  # Ganti 1 dengan camera_id Anda

   while True:
       ret, frame = cap.read()
       if ret:
           cv2.imshow('Test', frame)
       if cv2.waitKey(1) & 0xFF == ord('q'):
           break

   cap.release()
   cv2.destroyAllWindows()
   ```

4. **Dokumentasi Terkait**
   - `docs/CONFIGURATION_GUIDE.md` - Panduan konfigurasi lengkap
   - `docs/CAMERA_CONTROLS_GUIDE.md` - Kontrol kamera saat runtime
   - `docs/WEB_DASHBOARD_GUIDE.md` - Monitoring via web

---

**Dibuat untuk EkoVision PET Detection System**  
**Versi: 1.0**  
**Terakhir diupdate: 2026-02-12**
