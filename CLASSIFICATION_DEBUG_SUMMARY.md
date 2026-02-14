# Summary: Troubleshooting Klasifikasi Tidak Muncul

Dokumentasi dan tools untuk debug masalah "botol masuk trigger zone tapi hasil klasifikasi tidak muncul".

---

## Problem yang Dihadapi

**Gejala:**

- ✓ Botol terdeteksi (ada bounding box)
- ✓ Botol memiliki Track ID (contoh: "ID: 1")
- ✓ Botol masuk ke trigger zone (kotak hijau)
- ✗ Hasil klasifikasi tidak muncul (tidak ada text product, grade, cap, dll)

---

## File yang Dibuat

### 1. debug_classification.py

**Fungsi:** Script Python untuk monitoring detail proses klasifikasi real-time

**Fitur:**

- Menampilkan log detail setiap track
- Monitoring track state (NEW → TRACKED → CLASSIFIED)
- Menampilkan posisi track di trigger zone
- Menampilkan hasil klasifikasi lengkap
- Menampilkan classification attempts
- Statistics real-time (FPS, cache, dll)

**Cara Menggunakan:**

```bash
python debug_classification.py
```

**Keyboard Controls:**

- `q` - Quit
- `t` - Toggle trigger zone visibility
- `s` - Show statistics

**Output Example:**

```
[Frame 30]
  Active tracks: 1
  Total classifications: 0

  Track ID 1: IN TRIGGER ZONE (waiting classification)
    - Center: (320, 240)
    - Classification attempts: 1

[Frame 60]
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

---

### 2. docs/CLASSIFICATION_TROUBLESHOOTING.md

**Fungsi:** Panduan lengkap troubleshooting masalah klasifikasi

**Isi Dokumentasi:**

1. **Gejala Problem**
   - Deskripsi lengkap problem yang dihadapi

2. **7 Kemungkinan Penyebab & Solusi:**
   - Botol belum cukup lama di trigger zone
   - Confidence threshold terlalu tinggi
   - Kualitas gambar botol kurang baik
   - Max classification attempts tercapai
   - Model classifier tidak ter-load dengan benar
   - Trigger zone terlalu kecil atau salah posisi
   - FPS terlalu rendah

3. **Debug Script**
   - Cara menggunakan debug_classification.py
   - Interpretasi output

4. **Checklist Troubleshooting**
   - 11 item checklist untuk diagnosa sistematis

5. **Konfigurasi Optimal untuk Testing**
   - Config.yaml yang sudah di-tune untuk testing

6. **Contoh Kasus & Solusi**
   - Kasus 1: Botol bergerak terlalu cepat
   - Kasus 2: Pencahayaan buruk
   - Kasus 3: Botol terlalu kecil

7. **Bantuan Lebih Lanjut**
   - Langkah-langkah jika masalah masih berlanjut

**Total:** ~400 baris dokumentasi troubleshooting

---

## Kemungkinan Penyebab Utama

Berdasarkan analisis kode, kemungkinan penyebab utama:

### 1. Botol Bergerak Terlalu Cepat ⭐ (Paling Umum)

**Penjelasan:**

- Sistem butuh beberapa frame untuk klasifikasi (~0.5-1 detik)
- Jika botol keluar dari trigger zone sebelum klasifikasi selesai, hasil tidak akan muncul

**Solusi Cepat:**

```
1. Tahan botol di dalam trigger zone selama 2-3 detik
2. Atau perlambat gerakan botol
```

---

### 2. Confidence Threshold Terlalu Tinggi

**Penjelasan:**

- Default threshold: 0.5 (50%)
- Jika model tidak yakin (confidence <50%), hasil ditolak

**Solusi Cepat:**

```yaml
# config.yaml
classification:
  confidence_threshold: 0.3 # Turunkan untuk testing
```

---

### 3. Pencahayaan Kurang Baik

**Penjelasan:**

- Gambar terlalu gelap/terang mengurangi akurasi klasifikasi
- Model DINOv3 sensitif terhadap kualitas gambar

**Solusi Cepat:**

```
1. Tambahkan lampu di area deteksi
2. Adjust camera brightness (tekan 'c' lalu '+')
```

---

### 4. Trigger Zone Tidak Tepat

**Penjelasan:**

- Center botol harus benar-benar di dalam trigger zone
- Jika zone terlalu kecil, botol mungkin tidak trigger klasifikasi

**Solusi Cepat:**

```yaml
# config.yaml - Perbesar zone
trigger_zone:
  width_pct: 60.0 # Dari 40.0
  height_pct: 80.0 # Dari 60.0
```

---

## Cara Debug Step-by-Step

### Step 1: Verifikasi Setup Dasar

```bash
# Cek apakah semua model ter-load
python run_detection_tracking.py

# Harus muncul di console:
# ✓ Loaded 308 classifiers
```

### Step 2: Test dengan Botol Statis

```
1. Jalankan aplikasi
2. Letakkan botol di dalam trigger zone
3. JANGAN gerakkan botol selama 3 detik
4. Perhatikan perubahan warna bounding box:
   - Kuning (NEW)
   - Cyan (TRACKED)
   - Hijau (CLASSIFIED) ← Hasil klasifikasi muncul
```

### Step 3: Jalankan Debug Script

```bash
python debug_classification.py

# Perhatikan console output:
# - Apakah track masuk trigger zone?
# - Berapa classification attempts?
# - Apakah ada error message?
```

### Step 4: Adjust Konfigurasi

```yaml
# Gunakan config optimal untuk testing
# (lihat docs/CLASSIFICATION_TROUBLESHOOTING.md)

classification:
  confidence_threshold: 0.3 # Lebih permisif

tracking:
  max_classification_attempts: 5 # Lebih banyak percobaan

trigger_zone:
  width_pct: 60.0 # Zone lebih besar
  height_pct: 80.0
```

### Step 5: Test Ulang

```
1. Restart aplikasi dengan config baru
2. Test dengan botol statis
3. Jika berhasil, adjust config ke nilai optimal
```

---

## Quick Fix Recommendations

### Fix 1: Untuk Testing Cepat

```yaml
# config.yaml
classification:
  confidence_threshold: 0.3

trigger_zone:
  x_offset_pct: 20.0
  y_offset_pct: 10.0
  width_pct: 60.0
  height_pct: 80.0
```

### Fix 2: Untuk Pencahayaan Buruk

```
Runtime adjustment:
1. Tekan 'c' untuk camera control mode
2. Tekan '+' 5-10 kali untuk brightness
3. Tekan ']' 3-5 kali untuk exposure
4. Tekan 'c' lagi untuk exit camera mode
```

### Fix 3: Untuk Botol Bergerak Cepat

```yaml
# config.yaml
tracking:
  min_hits: 2 # Dari 3, lebih cepat trigger
  max_classification_attempts: 5 # Lebih banyak percobaan
```

---

## Interpretasi Visual

### Warna Bounding Box:

- **Kuning** = NEW (baru terdeteksi)
- **Cyan** = TRACKED (sedang di-track)
- **Hijau** = CLASSIFIED (sudah diklasifikasi) ✓
- **Merah** = FAILED (klasifikasi gagal)

### Text yang Muncul:

**Jika CLASSIFIED:**

```
ID: 1
product: Aqua
grade: A
cap: Blue
label: Clear
brand: Danone
type: PET
subtype: Bottle
volume: 600ml
```

**Jika TRACKED:**

```
ID: 1
TRACKED
```

**Jika FAILED:**

```
ID: 1
FAILED
```

---

## Testing Checklist

Gunakan checklist ini untuk systematic debugging:

**Hardware:**

- [ ] Kamera terhubung dan berfungsi
- [ ] Pencahayaan cukup (tidak terlalu gelap/terang)
- [ ] Botol dalam kondisi baik (tidak rusak/kotor)

**Software:**

- [ ] Aplikasi berjalan tanpa error
- [ ] 308 classifiers ter-load
- [ ] FPS >15
- [ ] Trigger zone visible (tekan 't')

**Testing:**

- [ ] Botol terdeteksi dengan bounding box
- [ ] Track ID muncul
- [ ] Botol center di dalam trigger zone
- [ ] Botol diam di zone minimal 2 detik
- [ ] Bounding box berubah warna: Kuning → Cyan → Hijau
- [ ] Hasil klasifikasi muncul (8 attributes)

**Jika gagal:**

- [ ] Jalankan debug_classification.py
- [ ] Cek console untuk error
- [ ] Adjust config sesuai panduan
- [ ] Test ulang

---

## Expected Behavior

### Normal Flow:

```
1. Botol masuk frame
   → Bounding box kuning muncul
   → Text: "ID: 1" dan "NEW"

2. Botol di-track beberapa frame
   → Bounding box berubah cyan
   → Text: "ID: 1" dan "TRACKED"

3. Botol masuk trigger zone
   → Klasifikasi dimulai
   → Classification attempts: 1, 2, 3...

4. Klasifikasi berhasil
   → Bounding box berubah hijau
   → Text: "ID: 1" + 8 attributes muncul
   → Hasil di-cache untuk reuse

5. Botol keluar frame
   → Track dihapus setelah max_age
   → Cache tetap tersimpan
```

### Abnormal Flow:

```
1. Botol masuk frame → Terdeteksi ✓
2. Botol masuk trigger zone ✓
3. Klasifikasi dimulai ✓
4. Klasifikasi gagal (confidence <threshold)
5. Retry klasifikasi (attempts: 2, 3...)
6. Max attempts tercapai
7. Bounding box berubah merah
8. Text: "FAILED" muncul
```

---

## Dokumentasi Terkait

- `docs/CLASSIFICATION_TROUBLESHOOTING.md` - Panduan lengkap troubleshooting
- `docs/CONFIGURATION_GUIDE.md` - Penjelasan semua parameter config
- `docs/CAMERA_CONTROLS_GUIDE.md` - Adjust camera settings runtime
- `RUNNING_GUIDE.md` - Panduan menjalankan sistem
- `debug_classification.py` - Debug script

---

## Summary

**Problem:** Hasil klasifikasi tidak muncul meskipun botol sudah masuk trigger zone

**Root Causes (Most Common):**

1. Botol bergerak terlalu cepat (tidak cukup lama di zone)
2. Confidence threshold terlalu tinggi
3. Pencahayaan kurang baik
4. Trigger zone terlalu kecil

**Solutions:**

1. Tahan botol di zone 2-3 detik
2. Turunkan confidence_threshold ke 0.3
3. Tambahkan lampu / adjust camera brightness
4. Perbesar trigger zone (width: 60%, height: 80%)

**Debug Tools:**

- `python debug_classification.py` - Real-time monitoring
- `docs/CLASSIFICATION_TROUBLESHOOTING.md` - Comprehensive guide

**Quick Test:**

```bash
# 1. Jalankan debug script
python debug_classification.py

# 2. Letakkan botol statis di trigger zone
# 3. Tunggu 3 detik
# 4. Perhatikan console output dan bounding box color
```

---

**Status:** ✓ Complete  
**Files Created:** 2 files  
**Total Documentation:** ~500 lines  
**Dibuat:** 2026-02-12
