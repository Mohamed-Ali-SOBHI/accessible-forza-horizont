"""
Script pour tester la detection et selection de cameras
"""
import sys
import io

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from camera_handler import CameraHandler

print("="*60)
print("  TEST DE DETECTION DES CAMERAS")
print("="*60)

try:
    # Test 1: Auto-detection
    print("\n[TEST 1] Detection automatique de la meilleure camera...")
    cam = CameraHandler(camera_index=-1)
    print(f"\nCamera selectionnee: {cam.camera_index}")

    # Test frame capture
    ret, frame = cam.get_frame()
    if ret:
        print(f"Capture d'image OK - Resolution: {frame.shape[1]}x{frame.shape[0]}")
    else:
        print("ERREUR: Impossible de capturer une image")

    cam.close()

    print("\n" + "="*60)
    print("TEST REUSSI!")
    print("="*60)

except Exception as e:
    print(f"\nERREUR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
