"""
Script de test pour vérifier que toutes les dépendances sont installées
et que le système est prêt à fonctionner.
"""

import sys
import io

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def test_imports():
    """Test all required imports"""
    print("🔍 Vérification des dépendances...\n")

    errors = []
    warnings = []

    # Test OpenCV
    try:
        import cv2
        print(f"✅ OpenCV: {cv2.__version__}")
    except ImportError as e:
        errors.append(("OpenCV", "pip install opencv-python"))
        print("❌ OpenCV: Non installé")

    # Test MediaPipe
    try:
        import mediapipe as mp
        print(f"✅ MediaPipe: {mp.__version__}")
    except ImportError as e:
        errors.append(("MediaPipe", "pip install mediapipe"))
        print("❌ MediaPipe: Non installé")

    # Test PyAutoGUI
    try:
        import pyautogui
        print(f"✅ PyAutoGUI: {pyautogui.__version__}")
    except ImportError as e:
        errors.append(("PyAutoGUI", "pip install pyautogui"))
        print("❌ PyAutoGUI: Non installé")

    # Test NumPy
    try:
        import numpy as np
        print(f"✅ NumPy: {np.__version__}")
    except ImportError as e:
        errors.append(("NumPy", "pip install numpy"))
        print("❌ NumPy: Non installé")

    # Test JSON (built-in)
    try:
        import json
        print("✅ JSON: OK (built-in)")
    except ImportError:
        warnings.append("JSON module non disponible (très inhabituel)")

    # Test CSV (built-in)
    try:
        import csv
        print("✅ CSV: OK (built-in)")
    except ImportError:
        warnings.append("CSV module non disponible (très inhabituel)")

    # Test Time (built-in)
    try:
        import time
        print("✅ Time: OK (built-in)")
    except ImportError:
        warnings.append("Time module non disponible (très inhabituel)")

    print("\n" + "="*60)

    if errors:
        print("\n❌ ERREURS DÉTECTÉES:\n")
        for pkg, install_cmd in errors:
            print(f"  {pkg}: {install_cmd}")
        print("\nInstallez les dépendances manquantes avec:")
        print("  pip install opencv-python mediapipe pyautogui numpy")
        return False

    if warnings:
        print("\n⚠️ AVERTISSEMENTS:\n")
        for warning in warnings:
            print(f"  - {warning}")

    print("\n✅ TOUTES LES DÉPENDANCES SONT INSTALLÉES!")
    return True

def test_camera():
    """Test camera availability"""
    print("\n🎥 Test de la caméra...\n")

    try:
        import cv2

        camera_found = False
        for i in range(5):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    print(f"✅ Caméra trouvée à l'index {i}")
                    print(f"   Résolution: {frame.shape[1]}x{frame.shape[0]}")
                    camera_found = True
                    cap.release()
                    break
                cap.release()

        if not camera_found:
            print("❌ Aucune caméra trouvée")
            print("   Vérifiez que votre webcam est branchée et autorisée")
            return False

        return True

    except Exception as e:
        print(f"❌ Erreur lors du test de la caméra: {e}")
        return False

def test_config():
    """Test configuration file"""
    print("\n⚙️ Test du fichier de configuration...\n")

    try:
        import json
        import os

        config_file = "config.json"

        if os.path.exists(config_file):
            print(f"✅ Fichier {config_file} trouvé")

            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)

            print("   Configuration chargée avec succès")

            # Check essential keys
            essential_keys = ['calibration', 'sensitivity', 'dead_zone', 'smoothing', 'control_mode']
            missing = [key for key in essential_keys if key not in config]

            if missing:
                print(f"⚠️ Clés manquantes dans la configuration: {missing}")
            else:
                print("   Toutes les clés essentielles présentes")

        else:
            print(f"⚠️ Fichier {config_file} non trouvé")
            print("   Il sera créé automatiquement au premier lancement")

        return True

    except Exception as e:
        print(f"❌ Erreur lors du test de configuration: {e}")
        return False

def test_files():
    """Test that all required files exist"""
    print("\n📁 Vérification des fichiers...\n")

    import os

    required_files = [
        ("accessible_face_drive.py", "Programme principal"),
        ("camera_handler.py", "Gestionnaire de caméra"),
        ("face_detector.py", "Détecteur de visage")
    ]

    optional_files = [
        ("config.json", "Configuration"),
        ("GUIDE_UTILISATION.md", "Guide d'utilisation"),
        ("README.md", "Documentation")
    ]

    all_good = True

    print("Fichiers requis:")
    for filename, description in required_files:
        if os.path.exists(filename):
            print(f"  ✅ {filename} ({description})")
        else:
            print(f"  ❌ {filename} ({description}) - MANQUANT!")
            all_good = False

    print("\nFichiers optionnels:")
    for filename, description in optional_files:
        if os.path.exists(filename):
            print(f"  ✅ {filename} ({description})")
        else:
            print(f"  ⚠️ {filename} ({description}) - Absent")

    return all_good

def main():
    """Run all tests"""
    print("="*60)
    print("  TEST DE CONFIGURATION DU SYSTÈME")
    print("="*60)
    print()

    results = {
        "Dépendances": test_imports(),
        "Caméra": test_camera(),
        "Configuration": test_config(),
        "Fichiers": test_files()
    }

    print("\n" + "="*60)
    print("  RÉSUMÉ")
    print("="*60)
    print()

    for test_name, result in results.items():
        status = "✅ OK" if result else "❌ ÉCHEC"
        print(f"{test_name:.<40} {status}")

    all_passed = all(results.values())

    print("\n" + "="*60)

    if all_passed:
        print("\n✅ SYSTÈME PRÊT!")
        print("\nVous pouvez lancer le programme avec:")
        print("  python accessible_face_drive.py")
        print("\nConsultez GUIDE_UTILISATION.md pour plus d'informations.")
    else:
        print("\n❌ PROBLÈMES DÉTECTÉS")
        print("\nRésolvez les problèmes ci-dessus avant de lancer le programme.")
        print("Consultez GUIDE_UTILISATION.md section 'Dépannage'.")

    print("\n" + "="*60)

    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
