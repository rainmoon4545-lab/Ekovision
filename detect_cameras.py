"""
Script untuk mendeteksi semua kamera yang tersedia di sistem.
Gunakan script ini untuk menemukan camera_id yang tepat untuk kamera eksternal Anda.
"""
import cv2
import sys

print("="*70)
print("EKOVISION - DETEKSI KAMERA TERSEDIA")
print("="*70)
print("\nMencari kamera yang tersedia di sistem...")
print("(Proses ini mungkin memakan waktu beberapa detik)\n")

available_cameras = []

# Cek hingga 10 camera index
for i in range(10):
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        ret, frame = cap.read()
        if ret:
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            
            available_cameras.append({
                'id': i,
                'width': width,
                'height': height,
                'fps': fps
            })
            
            print(f"✓ Kamera {i} ditemukan:")
            print(f"  - Resolusi: {width}x{height}")
            print(f"  - FPS: {fps}")
            print()
        cap.release()

if not available_cameras:
    print("✗ Tidak ada kamera yang ditemukan!")
    print("\nPastikan:")
    print("  1. Kamera eksternal sudah terhubung ke laptop")
    print("  2. Driver kamera sudah terinstall")
    print("  3. Kamera tidak sedang digunakan aplikasi lain")
    sys.exit(1)

print("="*70)
print("RINGKASAN")
print("="*70)
print(f"Total kamera ditemukan: {len(available_cameras)}\n")

for cam in available_cameras:
    cam_type = "Kamera Laptop (Built-in)" if cam['id'] == 0 else f"Kamera Eksternal #{cam['id']}"
    print(f"Camera ID {cam['id']}: {cam_type}")
    print(f"  Resolusi: {cam['width']}x{cam['height']}, FPS: {cam['fps']}")

print("\n" + "="*70)
print("CARA MENGGUNAKAN KAMERA YANG DIPILIH")
print("="*70)
print("\n1. Edit file config.yaml")
print("2. Ubah nilai 'camera_id' sesuai kamera yang ingin digunakan:")
print("\n   camera:")
print("     camera_id: X  # Ganti X dengan ID kamera yang dipilih")
print("\n3. Jalankan aplikasi seperti biasa")
print("\nContoh:")
if len(available_cameras) > 1:
    print(f"  - Untuk kamera laptop: camera_id: 0")
    print(f"  - Untuk kamera eksternal: camera_id: {available_cameras[1]['id']}")
else:
    print(f"  - Untuk kamera yang tersedia: camera_id: {available_cameras[0]['id']}")

print("\n" + "="*70)
