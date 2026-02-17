# Implementation Plan: Classification Results Overlay

## Overview

Implementasi fitur overlay hasil klasifikasi akan dilakukan secara incremental dengan fokus pada:

1. Membuat komponen ClassificationOverlay yang modular
2. Integrasi dengan pipeline yang ada tanpa merusak fungsionalitas existing
3. Testing komprehensif menggunakan unit tests dan property-based tests

## Tasks

- [x] 1. Buat struktur dasar ClassificationOverlay class
  - Buat file baru `src/tracking/classification_overlay.py`
  - Implementasi `__init__` dengan semua parameter konfigurasi
  - Definisikan data classes: `OverlayConfig` dan `OverlayLayout`
  - Import dependencies yang diperlukan (cv2, numpy, dataclasses)
  - _Requirements: 1.1, 1.3, 1.5_

- [ ]\* 1.1 Write unit tests untuk konfigurasi overlay
  - Test default configuration values
  - Test custom configuration values
  - Test configuration validation
  - _Requirements: 1.3, 3.2_

- [x] 2. Implementasi layout calculation logic
  - [x] 2.1 Implementasi method `_calculate_layout`
    - Hitung dimensi overlay berdasarkan jumlah tracks
    - Implementasi logic untuk multi-column layout (> 2 tracks)
    - Hitung posisi overlay berdasarkan parameter position (top-center)
    - Validasi bahwa koordinat tidak melebihi dimensi frame
    - _Requirements: 1.2, 1.4, 1.5, 4.2, 7.4_
  - [ ]\* 2.2 Write property test untuk layout calculation
    - **Property 12: Minimum Overlay Height**
    - **Property 15: Coordinate Bounds Validation**
    - **Validates: Requirements 1.4, 7.4**
  - [ ]\* 2.3 Write property test untuk multi-column layout
    - **Property 9: Multi-Column Layout Activation**
    - **Validates: Requirements 4.2**
  - [ ]\* 2.4 Write property test untuk dynamic resolution adaptation
    - **Property 16: Dynamic Resolution Adaptation**
    - **Validates: Requirements 7.5**

- [x] 3. Implementasi background rendering
  - [x] 3.1 Implementasi method `_draw_background`
    - Buat semi-transparent background menggunakan cv2.addWeighted
    - Gunakan background_color dan background_alpha dari config
    - Handle edge case ketika overlay area melebihi frame
    - _Requirements: 1.1, 1.3_
  - [ ]\* 3.2 Write unit tests untuk background rendering
    - Test transparency calculation
    - Test background color application
    - Test bounds handling
    - _Requirements: 1.1, 1.3_

- [x] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Implementasi track results rendering
  - [x] 5.1 Implementasi method `_draw_track_results`
    - Render track ID sebagai header
    - Render semua 8 atribut klasifikasi dengan format "name: value"
    - Gunakan CATEGORY_COLORS untuk setiap atribut
    - Render text background untuk setiap text element
    - Handle incomplete classification results (missing attributes → "N/A")
    - Arrange attributes vertically dengan spacing yang tepat
    - _Requirements: 2.2, 2.4, 3.1, 3.3, 3.5, 4.1, 4.3, 7.2_
  - [ ]\* 5.2 Write property test untuk complete attribute rendering
    - **Property 3: Complete Attribute Rendering**
    - **Validates: Requirements 2.2, 3.3**
  - [ ]\* 5.3 Write property test untuk track ID header display
    - **Property 5: Track ID Header Display**
    - **Validates: Requirements 2.4, 4.3**
  - [ ]\* 5.4 Write property test untuk color scheme consistency
    - **Property 6: Color Scheme Consistency**
    - **Validates: Requirements 3.1**
  - [ ]\* 5.5 Write property test untuk text background rendering
    - **Property 7: Text Background Rendering**
    - **Validates: Requirements 3.5**
  - [ ]\* 5.6 Write property test untuk vertical column layout
    - **Property 8: Vertical Column Layout**
    - **Validates: Requirements 4.1**
  - [ ]\* 5.7 Write property test untuk incomplete classification handling
    - **Property 14: Incomplete Classification Handling**
    - **Validates: Requirements 7.2**

- [x] 6. Implementasi empty state rendering
  - [x] 6.1 Implementasi method `_draw_empty_state`
    - Render pesan "Menunggu klasifikasi..." di center overlay
    - Gunakan font yang konsisten dengan track results
    - _Requirements: 5.3, 7.1_
  - [ ]\* 6.2 Write unit test untuk empty state
    - Test empty state dengan no tracks
    - Test empty state dengan tracks tapi no classifications
    - _Requirements: 5.3, 7.1_

- [x] 7. Implementasi main render method
  - [x] 7.1 Implementasi method `render`
    - Filter tracks untuk hanya CLASSIFIED tracks
    - Sort tracks berdasarkan track_id (ascending)
    - Limit tracks ke max_tracks_display
    - Tambahkan "+N more" indicator jika ada tracks tambahan
    - Call \_calculate_layout, \_draw_background, \_draw_track_results
    - Handle empty state (no classified tracks)
    - Wrap semua logic dalam try-except untuk error handling
    - Return original frame jika terjadi error
    - _Requirements: 2.1, 2.3, 4.4, 4.5, 5.3, 7.3_
  - [ ]\* 7.2 Write property test untuk classified tracks visibility
    - **Property 2: Classified Tracks Visibility**
    - **Validates: Requirements 2.1**
  - [ ]\* 7.3 Write property test untuk multiple track separation
    - **Property 4: Multiple Track Separation**
    - **Validates: Requirements 2.3**
  - [ ]\* 7.4 Write property test untuk track ID sorting
    - **Property 10: Track ID Sorting**
    - **Validates: Requirements 4.4**
  - [ ]\* 7.5 Write property test untuk track display limit
    - **Property 11: Track Display Limit**
    - **Validates: Requirements 4.5**
  - [ ]\* 7.6 Write property test untuk data immutability
    - **Property 13: Data Immutability**
    - **Validates: Requirements 6.5**
  - [ ]\* 7.7 Write unit test untuk error handling
    - Test exception handling in render method
    - Test graceful degradation
    - _Requirements: 7.3_

- [x] 8. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 9. Integrasi dengan DetectionTrackingPipeline
  - [x] 9.1 Modifikasi `DetectionTrackingPipeline.__init__`
    - Import ClassificationOverlay
    - Initialize self.overlay dengan konfigurasi default
    - _Requirements: 6.1, 6.2, 6.3, 6.4_
  - [x] 9.2 Modifikasi `DetectionTrackingPipeline._render_frame`
    - Tambahkan call ke self.overlay.render() di akhir method (setelah semua rendering lain)
    - Pass frame, tracks, dan self.cache ke overlay.render()
    - _Requirements: 6.1, 6.2, 6.3, 6.4_
  - [ ]\* 9.3 Write integration tests
    - Test overlay is initialized in pipeline
    - Test overlay.render is called in \_render_frame
    - Test overlay uses same cache as per-bottle labels
    - Test overlay uses same color scheme as per-bottle labels
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [x] 10. Write property test untuk overlay position consistency
  - [x]\* 10.1 Implementasi property test
    - **Property 1: Overlay Position Consistency**
    - **Validates: Requirements 1.2**

- [x] 11. Setup Hypothesis test infrastructure
  - [x] 11.1 Buat file `tests/test_classification_overlay_properties.py`
    - Setup Hypothesis strategies untuk frame generation
    - Setup Hypothesis strategies untuk track generation
    - Setup Hypothesis strategies untuk classification results generation
    - Configure Hypothesis settings (min 100 iterations)
    - _Requirements: All property tests_
  - [x]\* 11.2 Write helper strategies
    - Implementasi st_frame() strategy
    - Implementasi st_classified_track() strategy
    - Implementasi st_classification_results() strategy
    - _Requirements: All property tests_

- [x] 12. Final checkpoint - Ensure all tests pass
  - Run all unit tests and property tests
  - Verify FPS impact is < 5%
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties (minimum 100 iterations each)
- Unit tests validate specific examples and edge cases
- Integration tests ensure seamless integration with existing pipeline
- All property tests should be tagged with: `# Feature: classification-results-overlay, Property N: [property text]`
