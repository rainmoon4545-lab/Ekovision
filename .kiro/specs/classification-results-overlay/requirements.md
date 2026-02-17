# Dokumen Requirements

## Pendahuluan

Fitur ini menambahkan overlay permanen di bagian atas layar yang menampilkan hasil klasifikasi botol secara real-time. Overlay ini akan melengkapi label klasifikasi yang sudah ada (yang mengikuti setiap botol), memberikan tampilan ringkasan yang mudah dibaca untuk semua botol yang sedang dilacak dan diklasifikasi.

## Glosarium

- **System**: Sistem deteksi dan pelacakan botol berbasis computer vision
- **Overlay**: Area tampilan permanen di bagian atas layar video
- **Classification_Results**: Hasil klasifikasi yang mencakup 8 atribut (product, grade, cap, label, brand, type, subtype, volume)
- **Track**: Objek botol yang sedang dilacak dengan ID unik
- **Active_Track**: Track dengan status TRACKED atau CLASSIFIED yang masih terlihat di frame
- **Render_Frame**: Metode yang menggambar anotasi pada frame video

## Requirements

### Requirement 1: Overlay Display Area

**User Story:** Sebagai pengguna, saya ingin melihat area overlay permanen di bagian atas layar, sehingga saya dapat melihat hasil klasifikasi tanpa harus mengikuti pergerakan botol.

#### Acceptance Criteria

1. THE System SHALL menampilkan area overlay di bagian atas layar dengan latar belakang semi-transparan
2. WHEN frame video di-render, THE Overlay SHALL selalu muncul di posisi yang sama terlepas dari pergerakan botol
3. THE Overlay SHALL memiliki latar belakang gelap (hitam atau abu-abu gelap) dengan transparansi 0.7 untuk keterbacaan
4. THE Overlay SHALL memiliki tinggi yang cukup untuk menampilkan minimal 3 baris informasi klasifikasi
5. THE Overlay SHALL diposisikan di bagian atas-tengah layar dengan margin 10 piksel dari tepi atas

### Requirement 2: Classification Results Display

**User Story:** Sebagai pengguna, saya ingin melihat hasil klasifikasi dari semua botol aktif di overlay, sehingga saya dapat memantau semua klasifikasi secara bersamaan.

#### Acceptance Criteria

1. WHEN sebuah Track memiliki status CLASSIFIED, THE System SHALL menampilkan hasil klasifikasinya di Overlay
2. THE System SHALL menampilkan semua 8 atribut klasifikasi (product, grade, cap, label, brand, type, subtype, volume) untuk setiap Track
3. WHEN terdapat multiple Active_Tracks dengan klasifikasi, THE System SHALL menampilkan hasil klasifikasi untuk setiap Track secara terpisah
4. THE System SHALL menampilkan Track ID di sebelah setiap hasil klasifikasi untuk identifikasi
5. WHEN sebuah Track tidak lagi aktif atau hilang dari frame, THE System SHALL menghapus hasil klasifikasinya dari Overlay dalam waktu 2 detik

### Requirement 3: Visual Formatting and Readability

**User Story:** Sebagai pengguna, saya ingin hasil klasifikasi di overlay mudah dibaca dan dibedakan, sehingga saya dapat dengan cepat memahami informasi yang ditampilkan.

#### Acceptance Criteria

1. THE System SHALL menggunakan warna yang berbeda untuk setiap kategori atribut sesuai dengan skema warna yang sudah ada (product: biru, grade: hijau, cap: merah, dll)
2. THE System SHALL menggunakan ukuran font minimal 0.6 untuk keterbacaan
3. THE System SHALL menampilkan setiap atribut dalam format "nama_atribut: nilai"
4. WHEN menampilkan multiple Tracks, THE System SHALL memisahkan hasil klasifikasi setiap Track dengan garis pemisah atau spasi yang jelas
5. THE System SHALL menampilkan hasil klasifikasi dengan latar belakang teks untuk kontras yang lebih baik

### Requirement 4: Layout and Organization

**User Story:** Sebagai pengguna, saya ingin hasil klasifikasi ditampilkan dengan layout yang terorganisir, sehingga saya dapat dengan mudah menemukan informasi yang saya butuhkan.

#### Acceptance Criteria

1. THE System SHALL menampilkan hasil klasifikasi dalam format kolom vertikal untuk setiap Track
2. WHEN terdapat lebih dari 2 Tracks dengan klasifikasi, THE System SHALL menggunakan layout multi-kolom untuk mengoptimalkan penggunaan ruang
3. THE System SHALL menampilkan Track ID sebagai header untuk setiap kolom hasil klasifikasi
4. THE System SHALL mengurutkan Tracks berdasarkan Track ID secara ascending
5. WHEN Overlay penuh, THE System SHALL menampilkan maksimal 3 Tracks dan menambahkan indikator "+N more" untuk Tracks tambahan

### Requirement 5: Performance and Efficiency

**User Story:** Sebagai pengguna, saya ingin overlay tidak mempengaruhi performa sistem, sehingga frame rate tetap optimal.

#### Acceptance Criteria

1. THE System SHALL me-render Overlay tanpa mengurangi FPS lebih dari 5%
2. THE System SHALL menggunakan cache untuk hasil klasifikasi yang sudah ada
3. WHEN tidak ada Active_Tracks dengan klasifikasi, THE System SHALL menampilkan pesan "Menunggu klasifikasi..." di Overlay
4. THE System SHALL memperbarui Overlay hanya ketika ada perubahan pada hasil klasifikasi atau status Track
5. THE System SHALL membatasi jumlah operasi drawing OpenCV untuk Overlay maksimal 50 operasi per frame

### Requirement 6: Integration with Existing System

**User Story:** Sebagai developer, saya ingin overlay terintegrasi dengan sistem yang ada tanpa merusak fungsionalitas existing, sehingga sistem tetap stabil dan maintainable.

#### Acceptance Criteria

1. THE System SHALL mempertahankan label klasifikasi yang mengikuti botol (existing functionality)
2. THE System SHALL menggunakan data klasifikasi yang sama dari cache untuk Overlay dan label per-botol
3. WHEN me-render frame, THE System SHALL menggambar Overlay setelah semua elemen lain (trigger zone, bounding boxes, labels)
4. THE System SHALL menggunakan skema warna yang konsisten antara Overlay dan label per-botol
5. THE System SHALL tidak mengubah struktur data Track atau classification_results yang sudah ada

### Requirement 7: Error Handling and Edge Cases

**User Story:** Sebagai pengguna, saya ingin sistem menangani kondisi error dengan baik, sehingga overlay tetap berfungsi dalam berbagai situasi.

#### Acceptance Criteria

1. WHEN tidak ada Tracks yang terdeteksi, THE System SHALL tetap menampilkan Overlay dengan pesan informasi
2. IF hasil klasifikasi tidak lengkap (kurang dari 8 atribut), THEN THE System SHALL menampilkan atribut yang tersedia dengan indikator "N/A" untuk yang hilang
3. WHEN terjadi error saat rendering Overlay, THE System SHALL menangkap exception dan melanjutkan rendering frame tanpa Overlay
4. THE System SHALL memvalidasi bahwa koordinat Overlay tidak melebihi dimensi frame
5. WHEN resolusi frame berubah, THE System SHALL menyesuaikan ukuran dan posisi Overlay secara dinamis
