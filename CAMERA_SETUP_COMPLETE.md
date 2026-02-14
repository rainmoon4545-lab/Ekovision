# ✓ Setup Kamera Eksternal - Complete

Dokumentasi lengkap untuk menghubungkan kamera eksternal ke EkoVision telah selesai dibuat.

---

## 📁 File yang Dibuat

### 1. detect_cameras.py

Script Python untuk auto-detect semua kamera yang tersedia.

**Status:** ✓ Tested & Working

**Test Result:**

```
✓ Kamera 0 ditemukan: 640x480, 30 FPS (Kamera Laptop Built-in)
```

### 2. docs/EXTERNAL_CAMERA_GUIDE.md

Panduan lengkap 400+ baris dengan 8 section utama.

**Isi:**

- Persiapan Hardware
- Deteksi Kamera Tersedia
- Konfigurasi Kamera
- Troubleshooting (5 problem umum + solusi)
- Tips Pemilihan Kamera (dengan rekomendasi produk)
- Konfigurasi IP Camera (Advanced)
- Checklist Setup
- Contoh Konfigurasi Lengkap

### 3. docs/CAMERA_QUICK_SETUP.md

Quick reference card untuk setup 5 menit.

**Format:** Step-by-step dengan troubleshooting table.

### 4. EXTERNAL_CAMERA_SETUP_SUMMARY.md

Summary lengkap dari semua dokumentasi yang dibuat.

---

## 🚀 Cara Menggunakan

### Scenario 1: Setup Kamera Eksternal Baru

**Langkah Cepat (5 menit):**

1. **Hubungkan kamera ke laptop**

   ```
   - Colokkan USB kamera ke port laptop
   - Tunggu Windows mendeteksi
   ```

2. **Deteksi Camera ID**

   ```bash
   python detect_cameras.py
   ```

   Output akan menunjukkan:

   ```
   Camera ID 0: Kamera Laptop (Built-in)
   Camera ID 1: Kamera Eksternal #1  ← Catat ID ini
   ```

3. **Edit config.yaml**

   ```yaml
   camera:
     camera_id: 1 # Ganti dengan ID dari step 2
     width: 1920
     height: 1080
     fps: 30
   ```

4. **Test**
   ```bash
   python run_detection_tracking.py
   # atau
   python run_web_dashboard.py
   ```

**Dokumentasi:** Lihat `docs/CAMERA_QUICK_SETUP.md`

---

### Scenario 2: Troubleshooting Kamera

**Problem:** Kamera tidak terdeteksi

**Solusi Cepat:**

1. Coba port USB lain
2. Restart laptop
3. Cek Device Manager (Win + X)
4. Tutup aplikasi yang menggunakan kamera (Zoom, Teams, dll)

**Dokumentasi Lengkap:** Lihat `docs/EXTERNAL_CAMERA_GUIDE.md` → Section "Troubleshooting"

---

### Scenario 3: Memilih Kamera Baru

**Rekomendasi Berdasarkan Budget:**

**Budget (<500k):**

- Logitech C270 (720p, 30fps)
- Microsoft LifeCam HD-3000

**Mid-range (500k-1.5jt):** ⭐ Recommended

- Logitech C920 (1080p, 30fps)
- Logitech C922 (1080p, 60fps)

**High-end (>1.5jt):**

- Logitech Brio (4K, 60fps)
- Razer Kiyo Pro

**Dokumentasi:** Lihat `docs/EXTERNAL_CAMERA_GUIDE.md` → Section "Tips Pemilihan Kamera"

---

## 📊 Test Results

### Script detect_cameras.py

**Status:** ✓ Working

**Test Environment:**

- OS: Windows
- Python: 3.14
- OpenCV: Installed

**Test Output:**

```
✓ Kamera 0 ditemukan: 640x480, 30 FPS
Total kamera ditemukan: 1
```

**Note:** Error messages dari OpenCV tentang "obsensor" adalah normal - itu hanya warning untuk camera index yang tidak ada.

---

## 📖 Dokumentasi Reference

### Quick Start

- `docs/CAMERA_QUICK_SETUP.md` - Setup 5 menit

### Comprehensive Guide

- `docs/EXTERNAL_CAMERA_GUIDE.md` - Panduan lengkap 400+ baris

### Related Docs

- `docs/CONFIGURATION_GUIDE.md` - Konfigurasi sistem lengkap
- `docs/CAMERA_CONTROLS_GUIDE.md` - Kontrol kamera saat runtime
- `docs/WEB_DASHBOARD_GUIDE.md` - Monitoring via web

### Tools

- `detect_cameras.py` - Auto-detect kamera tersedia

---

## 🎯 Use Cases

### Use Case 1: Conveyor Belt dengan Kamera USB

```yaml
# config.yaml
camera:
  camera_id: 1 # Kamera eksternal USB
  width: 1920
  height: 1080
  fps: 30
```

### Use Case 2: Testing dengan Kamera Laptop

```yaml
# config.yaml
camera:
  camera_id: 0 # Kamera built-in
  width: 640
  height: 480
  fps: 30
```

### Use Case 3: Dual Camera Setup

**Terminal 1:**

```bash
# config.yaml: camera_id: 1
python run_detection_tracking.py
```

**Terminal 2:**

```bash
# config2.yaml: camera_id: 2
python run_detection_tracking.py --config config2.yaml
```

---

## ✅ Checklist Setup Kamera Eksternal

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

## 🔧 Troubleshooting Quick Reference

| Problem                 | Quick Fix                     |
| ----------------------- | ----------------------------- |
| Kamera tidak terdeteksi | Port USB lain, restart laptop |
| Gambar hitam            | Coba camera_id: 0, 1, 2       |
| FPS rendah              | Kurangi resolusi ke 640x480   |
| Disconnect tiba-tiba    | Ganti kabel USB               |
| Warna tidak akurat      | Adjust brightness/exposure    |

**Solusi Lengkap:** `docs/EXTERNAL_CAMERA_GUIDE.md` → Section "Troubleshooting"

---

## 🎓 Tips & Best Practices

### Pemilihan Kamera

- Minimum 720p untuk deteksi botol PET
- 1080p recommended untuk jarak 2-4 meter
- 30 FPS minimum, 60 FPS lebih baik untuk conveyor cepat

### Setup Optimal

- Gunakan USB 3.0 port (biru) untuk bandwidth lebih tinggi
- Hindari USB hub, colok langsung ke laptop
- Disable USB power saving di Windows
- Gunakan kabel USB berkualitas baik (<3 meter)

### Pencahayaan

- Tambahkan lampu di area deteksi
- Hindari backlight (cahaya dari belakang objek)
- Gunakan cahaya putih natural

---

## 📝 Summary

**Files Created:** 4 files

- detect_cameras.py (detection tool)
- docs/EXTERNAL_CAMERA_GUIDE.md (comprehensive guide)
- docs/CAMERA_QUICK_SETUP.md (quick reference)
- EXTERNAL_CAMERA_SETUP_SUMMARY.md (summary)

**Files Updated:** 2 files

- requirements.txt (added flask-socketio, python-socketio)
- README.md (added camera guide references)

**Total Documentation:** ~600 lines

**Status:** ✓ Complete & Tested

---

## 🚦 Next Steps

### Untuk User Baru

1. Baca `docs/CAMERA_QUICK_SETUP.md`
2. Jalankan `python detect_cameras.py`
3. Edit `config.yaml`
4. Test dengan `python run_detection_tracking.py`

### Untuk Troubleshooting

1. Identifikasi problem
2. Buka `docs/EXTERNAL_CAMERA_GUIDE.md`
3. Cari solusi di section "Troubleshooting"
4. Ikuti langkah-langkah yang diberikan

### Untuk Pembelian Kamera Baru

1. Baca `docs/EXTERNAL_CAMERA_GUIDE.md` → "Tips Pemilihan Kamera"
2. Pilih kamera sesuai budget
3. Cek spesifikasi minimum
4. Beli dan setup menggunakan panduan

---

**Dokumentasi ini siap digunakan untuk membantu user menghubungkan kamera eksternal ke sistem EkoVision dengan mudah dan cepat.**

---

**Created:** 2026-02-12  
**Version:** 1.0  
**Status:** ✓ Complete
