# Perubahan: Teks Klasifikasi Lebih Besar

## 📝 Yang Diubah

File: `src/tracking/pipeline.py`

### 1. Teks Klasifikasi (8 Atribut)

- **Font size**: 0.5 → 0.8 (60% lebih besar)
- **Spacing**: 20px → 30px (lebih renggang)
- **Background**: Ditambah kotak hitam di belakang teks
- **Visibility**: Jauh lebih mudah dibaca

### 2. Track ID

- **Font size**: 0.6 → 0.9 (50% lebih besar)
- **Background**: Ditambah kotak hitam
- **Thickness**: Tetap 2 (sudah cukup tebal)

### 3. FPS Counter

- **Font size**: 1.0 → 1.2 (20% lebih besar)
- **Thickness**: 2 → 3 (lebih tebal)
- **Background**: Ditambah kotak hitam
- **Color**: Tetap hijau (0, 255, 0)

### 4. Statistics

- **Font size**: 0.6 → 0.8 (33% lebih besar)
- **Background**: Ditambah kotak hitam
- **Thickness**: Tetap 2

---

## 🎨 Perbandingan

### Sebelum:

```
Font size kecil (0.5)
Tidak ada background
Sulit dibaca
```

### Sesudah:

```
Font size besar (0.8)
Ada background hitam
Mudah dibaca ✅
```

---

## 🚀 Cara Menggunakan

```bash
# Jalankan sistem seperti biasa
python run_detection_tracking.py

# Teks sekarang jauh lebih besar dan mudah dibaca!
```

---

## 📊 Detail Perubahan

### Klasifikasi Text (8 atribut):

```python
# SEBELUM:
cv2.putText(annotated, text, (x1, y_offset + i * 20),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, text_color, 2)

# SESUDAH:
# 1. Tambah background hitam
cv2.rectangle(annotated, (x1-2, y_offset+i*30-h-2),
              (x1+w+2, y_offset+i*30+2), (0,0,0), -1)

# 2. Teks lebih besar
cv2.putText(annotated, text, (x1, y_offset + i * 30),
            cv2.FONT_HERSHEY_SIMPLEX, 0.8, text_color, 2)
```

### Track ID:

```python
# SEBELUM:
cv2.putText(annotated, track_text, (x1, y1-10),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

# SESUDAH:
# 1. Tambah background hitam
cv2.rectangle(annotated, (x1-2, y1-h-12),
              (x1+w+2, y1-2), (0,0,0), -1)

# 2. Teks lebih besar
cv2.putText(annotated, track_text, (x1, y1-10),
            cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
```

### FPS Counter:

```python
# SEBELUM:
cv2.putText(annotated, fps_text, (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0,255,0), 2)

# SESUDAH:
# 1. Tambah background hitam
cv2.rectangle(annotated, (5, 5), (15+w, 40), (0,0,0), -1)

# 2. Teks lebih besar dan tebal
cv2.putText(annotated, fps_text, (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0,255,0), 3)
```

---

## ✅ Keuntungan

1. **Lebih Mudah Dibaca** - Font 60% lebih besar
2. **Kontras Lebih Baik** - Background hitam membuat teks lebih jelas
3. **Spacing Lebih Baik** - Jarak antar baris lebih renggang
4. **Professional Look** - Tampilan lebih rapi dan modern

---

## 🔧 Jika Masih Terlalu Kecil

Edit `src/tracking/pipeline.py` dan ubah nilai font size:

### Untuk Teks Klasifikasi:

```python
# Line ~460
cv2.putText(
    annotated, text, (x1, y_offset + i * 30),
    cv2.FONT_HERSHEY_SIMPLEX,
    1.0,  # Ubah dari 0.8 → 1.0 (lebih besar lagi)
    text_color, 2
)
```

### Untuk Track ID:

```python
# Line ~440
cv2.putText(
    annotated, track_text, (x1, y1 - 10),
    cv2.FONT_HERSHEY_SIMPLEX,
    1.2,  # Ubah dari 0.9 → 1.2 (lebih besar lagi)
    color, 2
)
```

### Untuk FPS:

```python
# Line ~510
cv2.putText(
    annotated, fps_text, (10, 30),
    cv2.FONT_HERSHEY_SIMPLEX,
    1.5,  # Ubah dari 1.2 → 1.5 (lebih besar lagi)
    (0, 255, 0), 3
)
```

---

## 📸 Screenshot Comparison

### Sebelum:

- Font kecil
- Sulit dibaca dari jauh
- Tidak ada background

### Sesudah:

- Font besar ✅
- Mudah dibaca ✅
- Ada background hitam ✅
- Spacing lebih baik ✅

---

**Status**: ✅ Selesai  
**File Modified**: `src/tracking/pipeline.py`  
**Testing**: Jalankan `python run_detection_tracking.py`
