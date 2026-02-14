# Quick Setup: Kamera Eksternal

Panduan cepat 5 menit untuk setup kamera eksternal.

---

## Langkah 1: Hubungkan Kamera (1 menit)

```
1. Colokkan kabel USB kamera ke laptop
2. Tunggu Windows mendeteksi perangkat
3. Pastikan lampu indikator kamera menyala
```

---

## Langkah 2: Deteksi Camera ID (1 menit)

Jalankan di terminal:

```bash
python detect_cameras.py
```

Catat Camera ID yang muncul (contoh: Camera ID 1)

---

## Langkah 3: Edit Konfigurasi (2 menit)

Buka file `config.yaml`, ubah bagian ini:

```yaml
camera:
  camera_id: 1 # ← Ganti dengan ID dari langkah 2
  width: 1920 # ← Sesuaikan resolusi kamera
  height: 1080
  fps: 30
```

**Resolusi Umum:**

- 640x480 (VGA)
- 1280x720 (HD)
- 1920x1080 (Full HD)

---

## Langkah 4: Test Kamera (1 menit)

Jalankan aplikasi:

```bash
# Pilih salah satu:
python run_detection_tracking.py    # Mode biasa
python run_web_dashboard.py         # Mode web dashboard
```

Pastikan video muncul dengan jelas.

---

## Troubleshooting Cepat

| Problem                 | Solusi                                    |
| ----------------------- | ----------------------------------------- |
| Kamera tidak terdeteksi | Coba port USB lain, restart laptop        |
| Gambar hitam            | Coba camera_id: 0, 1, 2                   |
| FPS rendah              | Kurangi resolusi ke 640x480               |
| Disconnect tiba-tiba    | Ganti kabel USB, disable USB power saving |

---

## Contoh Konfigurasi

**Logitech C920 (1080p):**

```yaml
camera:
  camera_id: 1
  width: 1920
  height: 1080
  fps: 30
```

**Webcam Budget (720p):**

```yaml
camera:
  camera_id: 1
  width: 1280
  height: 720
  fps: 30
```

**Kamera Laptop Built-in:**

```yaml
camera:
  camera_id: 0
  width: 640
  height: 480
  fps: 30
```

---

## Bantuan Lengkap

Lihat dokumentasi lengkap: `docs/EXTERNAL_CAMERA_GUIDE.md`

---

✓ Setup selesai! Kamera eksternal siap digunakan.
