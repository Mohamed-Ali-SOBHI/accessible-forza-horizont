"""
Script de Test Rapide pour Tous les Modules
Permet de tester individuellement chaque module sans lancer le système complet
"""

import sys


def test_menu():
    """Affiche le menu de test"""
    print("\n" + "="*70)
    print(" MENU DE TEST DES MODULES")
    print("="*70)
    print("\n1. Test Advanced Head Pose (Yaw/Pitch/Roll)")
    print("2. Test Facial Gestures Detection")
    print("3. Test Gesture Commands Mapping")
    print("4. Test Advanced Filters (DES + Kalman)")
    print("5. Test Tremor Detector")
    print("6. Test Motion Predictor")
    print("7. Test Driving Assistant")
    print("8. Test Fatigue Monitor")
    print("9. Test Système Complet (Enhanced)")
    print("0. Quitter")
    print("\n" + "="*70)


def test_head_pose():
    """Test du module advanced_head_pose"""
    print("\n[TEST] Advanced Head Pose")
    print("-" * 70)
    try:
        from advanced_head_pose import AdvancedHeadPose
        import cv2

        cap = cv2.VideoCapture(0)
        pose = AdvancedHeadPose()

        print("✓ Module chargé avec succès")
        print("📹 Webcam activée - Tournez la tête dans différentes directions")
        print("Appuyez sur 'q' pour quitter\n")

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            yaw, pitch, roll, success, points = pose.estimate_pose(frame)

            if success:
                frame = pose.draw_pose_info(frame, yaw, pitch, roll, points)
                direction = pose.get_direction_from_yaw(yaw)
                print(f"Yaw: {yaw:6.1f}° | Pitch: {pitch:6.1f}° | Roll: {roll:6.1f}° | Direction: {direction:>6s}", end='\r')

            cv2.imshow('Test Head Pose', frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        pose.close()
        cv2.destroyAllWindows()
        print("\n\n✓ Test terminé avec succès!")

    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()


def test_facial_gestures():
    """Test du module facial_gestures"""
    print("\n[TEST] Facial Gestures Detection")
    print("-" * 70)
    try:
        from facial_gestures import FacialGestureDetector
        import cv2
        import time

        cap = cv2.VideoCapture(0)
        detector = FacialGestureDetector()

        print("✓ Module chargé avec succès")
        print("📹 Calibration en cours (3 secondes)...")
        print("Gardez une expression neutre!\n")

        calibrating = True
        start_time = time.time()

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if calibrating:
                complete = detector.calibrate(frame, duration=3.0)
                if complete:
                    calibrating = False
                    print("\n✓ Calibration terminée!")
                    print("Essayez différentes expressions:")
                    print("  - Cligner œil gauche")
                    print("  - Cligner œil droit")
                    print("  - Ouvrir la bouche")
                    print("  - Lever les sourcils")
                    print("  - Sourire\n")

                remaining = max(0, 3.0 - (time.time() - start_time))
                cv2.putText(frame, f"CALIBRATION: {remaining:.1f}s", (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
            else:
                gestures = detector.detect_gestures(frame)
                frame = detector.draw_gesture_indicators(frame, gestures)

                active = [k for k, v in gestures.items() if v]
                if active:
                    print(f"Gestes actifs: {', '.join(active):50s}", end='\r')

            cv2.imshow('Test Facial Gestures', frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        detector.close()
        cv2.destroyAllWindows()
        print("\n\n✓ Test terminé avec succès!")

    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()


def test_filters():
    """Test du module advanced_filters"""
    print("\n[TEST] Advanced Filters")
    print("-" * 70)
    try:
        from advanced_filters import DoubleExponentialSmoothing, AdaptiveKalmanFilter, CompositeFilter
        import numpy as np
        import matplotlib.pyplot as plt

        print("✓ Module chargé avec succès")
        print("Génération signal bruité et application des filtres...\n")

        # Génère signal test
        np.random.seed(42)
        t = np.linspace(0, 10, 200)
        signal_clean = np.sin(t)
        noise = np.random.normal(0, 0.3, 200)
        signal_noisy = signal_clean + noise

        # Test filtres
        des = DoubleExponentialSmoothing(alpha=0.3, beta=0.1)
        kalman = AdaptiveKalmanFilter()
        composite = CompositeFilter({'use_des': True, 'use_kalman': True})

        signal_des = []
        signal_kalman = []
        signal_composite = []

        for s in signal_noisy:
            signal_des.append(des.update(s))
            signal_kalman.append(kalman.update(s))
            comp_x, _ = composite.filter(s, 0)
            signal_composite.append(comp_x)

        # Calcule erreurs
        error_noisy = np.mean((signal_noisy - signal_clean)**2)
        error_des = np.mean((np.array(signal_des) - signal_clean)**2)
        error_kalman = np.mean((np.array(signal_kalman) - signal_clean)**2)
        error_composite = np.mean((np.array(signal_composite) - signal_clean)**2)

        print(f"Erreur signal bruité:     {error_noisy:.4f}")
        print(f"Erreur DES:               {error_des:.4f} ({(1-error_des/error_noisy)*100:+.1f}%)")
        print(f"Erreur Kalman:            {error_kalman:.4f} ({(1-error_kalman/error_noisy)*100:+.1f}%)")
        print(f"Erreur Composite:         {error_composite:.4f} ({(1-error_composite/error_noisy)*100:+.1f}%)")

        smoothness = composite.get_smoothness_metric()
        print(f"\nMétrique de lissage (composite): {smoothness:.4f}")

        print("\n✓ Test terminé avec succès!")
        print("Note: Pour visualisation graphique, décommentez le code matplotlib")

        # Décommenter pour voir le graphique:
        # plt.figure(figsize=(12, 6))
        # plt.plot(t, signal_clean, 'g-', label='Signal propre', linewidth=2)
        # plt.plot(t, signal_noisy, 'r.', label='Signal bruité', alpha=0.5)
        # plt.plot(t, signal_composite, 'b-', label='Filtre composite', linewidth=2)
        # plt.legend()
        # plt.title('Test Filtres Avancés')
        # plt.xlabel('Temps')
        # plt.ylabel('Amplitude')
        # plt.grid(True)
        # plt.show()

    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()


def test_tremor_detector():
    """Test du module tremor_detector"""
    print("\n[TEST] Tremor Detector")
    print("-" * 70)
    try:
        from tremor_detector import TremorDetector
        import numpy as np
        import time

        print("✓ Module chargé avec succès")
        print("Simulation de différents patterns de mouvement...\n")

        detector = TremorDetector()

        # Test 1: Mouvement intentionnel
        print("Test 1: Mouvement intentionnel (ligne droite)")
        for i in range(30):
            x = i * 3
            y = 50
            result = detector.update(x, y)
            time.sleep(0.01)

        print(f"  Tremblements détectés: {result['tremor_detected']}")
        print(f"  Confiance intention: {result['intention_confidence']:.2f}")

        detector.reset()
        time.sleep(0.1)

        # Test 2: Tremblements
        print("\nTest 2: Simulation tremblements (8 Hz)")
        t = 0
        for i in range(60):
            x = 50 + 5 * np.sin(2 * np.pi * 8 * t)
            y = 50 + 5 * np.cos(2 * np.pi * 8 * t)
            result = detector.update(x, y)
            t += 0.033
            time.sleep(0.01)

        print(f"  Tremblements détectés: {result['tremor_detected']}")
        print(f"  Intensité: {result['tremor_intensity']:.2f}")
        print(f"  Fréquence: {result['tremor_frequency']:.1f} Hz")
        print(f"  Filtrage recommandé: {result['recommended_filter_strength']:.2f}")

        print("\n✓ Test terminé avec succès!")

    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()


def test_motion_predictor():
    """Test du module motion_predictor"""
    print("\n[TEST] Motion Predictor")
    print("-" * 70)
    try:
        from motion_predictor import MotionPredictor
        import numpy as np

        print("✓ Module chargé avec succès")
        print("Test prédiction sur mouvement accéléré...\n")

        predictor = MotionPredictor(prediction_steps=3)

        errors = []
        for i in range(20):
            x = i**2 * 0.5  # Mouvement accéléré
            y = 50

            pred_x, pred_y = predictor.update(x, y)

            if i > 5:
                # Position réelle 3 steps en avance
                actual_future_x = (i + 3)**2 * 0.5
                error = abs(pred_x - actual_future_x)
                errors.append(error)

                print(f"  Step {i:2d}: Position={x:5.1f} | Prédiction={pred_x:5.1f} | Réel futur={actual_future_x:5.1f} | Erreur={error:5.1f}")

        avg_error = np.mean(errors)
        print(f"\nErreur moyenne de prédiction: {avg_error:.2f} pixels")

        print("\n✓ Test terminé avec succès!")

    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()


def test_driving_assistant():
    """Test du module driving_assistant"""
    print("\n[TEST] Driving Assistant")
    print("-" * 70)
    try:
        from driving_assistant import DrivingAssistant

        print("✓ Module chargé avec succès")
        print("Test des différents niveaux d'assistance...\n")

        for level in range(4):
            assistant = DrivingAssistant(assistance_level=level)
            print(f"\nNiveau {level}: {assistant.get_assistance_description()}")

            # Simule input oscillant
            inputs = [20, -15, 18, -12, 20, 22, 20, 19]
            directions = []

            for yaw in inputs:
                direction = assistant.process_steering(yaw, sensitivity=15)
                directions.append(direction)

            print(f"  Inputs: {inputs}")
            print(f"  Directions: {directions}")
            print(f"  Stabilité: {len(set(directions))} changements")

        print("\n✓ Test terminé avec succès!")

    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()


def test_fatigue_monitor():
    """Test du module fatigue_monitor"""
    print("\n[TEST] Fatigue Monitor")
    print("-" * 70)
    try:
        from fatigue_monitor import FatigueMonitor
        import time

        print("✓ Module chargé avec succès")
        print("Simulation session de 15 minutes avec fatigue progressive...\n")

        monitor = FatigueMonitor()

        for minute in range(15):
            # Simule dégradation performance
            input_variance = 1.0 + (minute * 0.3)
            corrections = 2 + (minute * 0.5)

            # Update plusieurs fois par "minute"
            for _ in range(6):
                result = monitor.update(
                    is_paused=False,
                    input_variance=input_variance,
                    correction_count=corrections
                )
                monitor.total_active_time += 10  # Simule 10 secondes

            if (minute + 1) % 5 == 0:
                print(f"Minute {minute + 1:2d}: Fatigue={result['fatigue_level']:8s} | Score={result['fatigue_score']:.2f} | Pause recommandée={result['recommend_break']}")

        print("\nStatistiques finales:")
        stats = monitor.get_session_stats()
        for key, value in stats.items():
            if isinstance(value, float):
                print(f"  {key}: {value:.2f}")
            else:
                print(f"  {key}: {value}")

        print("\n✓ Test terminé avec succès!")

    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()


def test_enhanced_system():
    """Lance le système complet amélioré"""
    print("\n[TEST] Système Complet Enhanced")
    print("-" * 70)
    try:
        print("Lancement du système amélioré...\n")
        from enhanced_accessible_drive import EnhancedAccessibleDriving

        driver = EnhancedAccessibleDriving()
        driver.run()

    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Fonction principale"""
    test_functions = {
        '1': test_head_pose,
        '2': test_facial_gestures,
        '3': lambda: print("\n⚠ Test nécessite simulation - Voir gesture_commands.py main"),
        '4': test_filters,
        '5': test_tremor_detector,
        '6': test_motion_predictor,
        '7': test_driving_assistant,
        '8': test_fatigue_monitor,
        '9': test_enhanced_system,
        '0': lambda: sys.exit(0)
    }

    while True:
        test_menu()
        choice = input("\nChoisissez un test (0-9): ").strip()

        if choice in test_functions:
            print()
            test_functions[choice]()
            input("\nAppuyez sur Entrée pour continuer...")
        else:
            print("\n❌ Choix invalide!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrompu par l'utilisateur")
    except Exception as e:
        print(f"\n\nErreur fatale: {e}")
        import traceback
        traceback.print_exc()
