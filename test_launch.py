"""
Script de test rapide pour vérifier que accessible_face_drive.py se lance sans erreur
"""
import sys
import io
import threading
import time

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def auto_quit():
    """Auto-quit après 5 secondes"""
    time.sleep(5)
    print("\n[TEST] Fermeture automatique après 5 secondes...")
    import os
    os._exit(0)

if __name__ == "__main__":
    print("="*60)
    print("  TEST DE LANCEMENT - accessible_face_drive.py")
    print("="*60)
    print("\nLe programme va se lancer et se fermer automatiquement après 5 secondes...")
    print("Ceci permet de tester qu'il n'y a pas d'erreur au démarrage.\n")

    # Lancer le timer d'auto-quit
    timer = threading.Thread(target=auto_quit, daemon=True)
    timer.start()

    # Importer et lancer le programme
    try:
        from accessible_face_drive import AccessibleHeadControlledDriving

        print("Initialisation du système...")
        driver = AccessibleHeadControlledDriving()

        print("✓ Programme initialisé avec succès!")
        print("✓ Pas d'erreur au démarrage!")
        print("\nNote: En utilisation normale, le programme affichera une fenêtre")
        print("      et attendra votre calibration. Ce test vérifie juste qu'il")
        print("      se lance sans erreur.\n")

        # Attendre l'auto-quit
        time.sleep(10)

    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
