import cv2
import mediapipe as mp
import pyautogui
import time
import json
import csv
import numpy as np
from datetime import datetime
from camera_handler import CameraHandler
from face_detector import FaceDetector

class AccessibleHeadControlledDriving:
    def __init__(self, config_file='config.json'):
        # Load configuration
        self.config = self.load_config(config_file)

        # Initialize hardware
        self.camera_handler = CameraHandler()
        self.face_detector = FaceDetector(self.camera_handler)

        # Screen and window setup
        self.screen_width, self.screen_height = pyautogui.size()

        # Calibration state
        self.calibrated = False
        self.neutral_x = 0
        self.neutral_y = 0
        self.calibration_samples = []
        self.calibration_start_time = None

        # Movement tracking
        self.last_x, self.last_y = 0, 0

        # Smoothing state (Kalman filter)
        self.kalman_x_state = 0.0
        self.kalman_y_state = 0.0
        self.kalman_x_cov = 1.0
        self.kalman_y_cov = 1.0

        # EMA smoothing state
        self.ema_x = 0.0
        self.ema_y = 0.0

        # Safety state
        self.is_paused = False
        self.face_lost_time = None
        self.last_active_keys = set()

        # Logging
        self.session_start = datetime.now()
        self.movement_log = []

        # UI state
        self.fps = 0
        self.last_fps_time = time.time()
        self.frame_count = 0

        # Initialize MediaPipe Face Mesh for advanced detection
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

        print("Système de conduite accessible initialisé")
        print("Préparez-vous pour la calibration...")

    def load_config(self, config_file):
        """Load configuration from JSON file"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Configuration file {config_file} not found, using defaults")
            return self.get_default_config()

    def get_default_config(self):
        """Return default configuration"""
        return {
            "calibration": {"duration_seconds": 3, "neutral_position": None},
            "sensitivity": {"horizontal": 30, "vertical": 30, "adaptive": True},
            "dead_zone": {"horizontal": 15, "vertical": 20},
            "smoothing": {"enable_kalman": True, "enable_ema": True, "ema_alpha": 0.3, "kalman_R": 0.5, "kalman_Q": 0.5},
            "control_mode": "position",
            "safety": {"enable_auto_pause": True, "pause_delay_seconds": 3, "mouth_open_pause": False},
            "ui": {"show_calibration_guide": True, "show_dead_zone": True, "show_active_keys": True, "show_fps": True, "mirror_video": True},
            "keys": {"forward": "z", "backward": "s", "left": "q", "right": "d"},
            "logging": {"enable": True, "log_file": "driving_sessions.csv"}
        }

    def save_config(self, config_file='config.json'):
        """Save current configuration to JSON file"""
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2)

    def start_calibration(self):
        """Start calibration phase"""
        self.calibration_start_time = time.time()
        self.calibration_samples = []
        self.calibrated = False
        print("\n=== CALIBRATION ===")
        print("Positionnez votre tête dans une position confortable et NEUTRE")
        print(f"Maintenez cette position pendant {self.config['calibration']['duration_seconds']} secondes...")

    def update_calibration(self, x, y, w, h):
        """Update calibration with face position sample"""
        if self.calibration_start_time is None:
            return False

        elapsed = time.time() - self.calibration_start_time
        duration = self.config['calibration']['duration_seconds']

        if elapsed < duration:
            # Collect samples
            center_x = x + w // 2
            center_y = y + h // 2
            self.calibration_samples.append((center_x, center_y))
            return False
        else:
            # Calibration complete - calculate neutral position
            if len(self.calibration_samples) > 0:
                self.neutral_x = int(np.median([s[0] for s in self.calibration_samples]))
                self.neutral_y = int(np.median([s[1] for s in self.calibration_samples]))
                self.last_x = self.neutral_x
                self.last_y = self.neutral_y
                self.ema_x = 0
                self.ema_y = 0
                self.calibrated = True

                # Save to config
                self.config['calibration']['neutral_position'] = {
                    'x': self.neutral_x,
                    'y': self.neutral_y
                }
                self.save_config()

                print(f"\n✓ Calibration terminée!")
                print(f"Position neutre: ({self.neutral_x}, {self.neutral_y})")
                print("Vous pouvez maintenant commencer à conduire!")
                print("Appuyez sur 'c' pour recalibrer, 'p' pour pause, 'q' pour quitter\n")
                return True
            return False

    def kalman_filter(self, measurement, state, cov):
        """Apply Kalman filter to measurement"""
        R = self.config['smoothing']['kalman_R']
        Q = self.config['smoothing']['kalman_Q']

        # Prediction
        pred_state = state
        pred_cov = cov + R

        # Update
        K = pred_cov / (pred_cov + Q)
        new_state = pred_state + K * (measurement - pred_state)
        new_cov = (1 - K) * pred_cov

        return new_state, new_cov

    def apply_ema(self, new_x, new_y):
        """Apply exponential moving average smoothing"""
        alpha = self.config['smoothing']['ema_alpha']
        self.ema_x = alpha * new_x + (1 - alpha) * self.ema_x
        self.ema_y = alpha * new_y + (1 - alpha) * self.ema_y
        return self.ema_x, self.ema_y

    def detect_head_movement(self, x, y, w, h):
        """Detect head movement relative to neutral position"""
        center_x = x + w // 2
        center_y = y + h // 2

        # Calculate displacement from neutral position
        dx = center_x - self.neutral_x
        dy = center_y - self.neutral_y

        # Apply smoothing
        if self.config['smoothing']['enable_kalman']:
            dx, self.kalman_x_cov = self.kalman_filter(dx, self.kalman_x_state, self.kalman_x_cov)
            dy, self.kalman_y_cov = self.kalman_filter(dy, self.kalman_y_state, self.kalman_y_cov)
            self.kalman_x_state = dx
            self.kalman_y_state = dy

        if self.config['smoothing']['enable_ema']:
            dx, dy = self.apply_ema(dx, dy)

        return dx, dy

    def control_car(self, dx, dy):
        """Control car based on head movement with different modes"""
        if self.is_paused:
            self.release_all_keys()
            return

        active_keys = set()

        # Dead zone filtering
        dead_zone_x = self.config['dead_zone']['horizontal']
        dead_zone_y = self.config['dead_zone']['vertical']

        if abs(dx) < dead_zone_x:
            dx = 0
        if abs(dy) < dead_zone_y:
            dy = 0

        # Get key bindings
        keys = self.config['keys']

        # Control mode: position-based
        if self.config['control_mode'] == 'position':
            # Horizontal control
            sens_x = self.config['sensitivity']['horizontal']
            if dx > sens_x:
                active_keys.add(keys['right'])
            elif dx < -sens_x:
                active_keys.add(keys['left'])

            # Vertical control
            sens_y = self.config['sensitivity']['vertical']
            if dy > sens_y:
                active_keys.add(keys['backward'])
            elif dy < -sens_y:
                active_keys.add(keys['forward'])

        # Control mode: velocity-based (movement speed controls intensity)
        elif self.config['control_mode'] == 'velocity':
            sens_x = self.config['sensitivity']['horizontal']
            sens_y = self.config['sensitivity']['vertical']

            # Proportional control based on distance from dead zone
            if abs(dx) > dead_zone_x:
                if dx > 0:
                    active_keys.add(keys['right'])
                else:
                    active_keys.add(keys['left'])

            if abs(dy) > dead_zone_y:
                if dy > 0:
                    active_keys.add(keys['backward'])
                else:
                    active_keys.add(keys['forward'])

        # Control mode: simplified (horizontal only, auto-forward)
        elif self.config['control_mode'] == 'simplified':
            # Always move forward
            active_keys.add(keys['forward'])

            # Only horizontal steering
            sens_x = self.config['sensitivity']['horizontal']
            if dx > sens_x:
                active_keys.add(keys['right'])
            elif dx < -sens_x:
                active_keys.add(keys['left'])

        # Update key states
        self.update_key_states(active_keys)

    def update_key_states(self, active_keys):
        """Update keyboard states based on active keys"""
        # Release keys that are no longer active
        for key in self.last_active_keys - active_keys:
            pyautogui.keyUp(key)

        # Press new active keys
        for key in active_keys - self.last_active_keys:
            pyautogui.keyDown(key)

        self.last_active_keys = active_keys

    def release_all_keys(self):
        """Release all keyboard keys"""
        for key in self.last_active_keys:
            pyautogui.keyUp(key)
        self.last_active_keys.clear()

    def toggle_pause(self):
        """Toggle pause state"""
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.release_all_keys()
            print("⏸ PAUSE")
        else:
            print("▶ REPRISE")

    def draw_ui(self, frame, x, y, w, h, dx, dy):
        """Draw UI overlays on frame"""
        if self.config['ui']['mirror_video']:
            frame = cv2.flip(frame, 1)

        height, width = frame.shape[:2]

        # Draw face detection
        if w > 0 and h > 0:
            if self.config['ui']['mirror_video']:
                x = width - x - w
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        # Draw calibration guide
        if not self.calibrated and self.config['ui']['show_calibration_guide']:
            elapsed = 0
            if self.calibration_start_time:
                elapsed = time.time() - self.calibration_start_time
            remaining = max(0, self.config['calibration']['duration_seconds'] - elapsed)

            # Semi-transparent overlay
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 0), (width, 150), (0, 0, 0), -1)
            cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

            # Text
            cv2.putText(frame, "CALIBRATION EN COURS", (width//2 - 200, 40),
                       cv2.FONT_HERSHEY_BOLD, 1, (0, 255, 255), 2)
            cv2.putText(frame, "Maintenez votre tete en position neutre", (width//2 - 280, 80),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)
            cv2.putText(frame, f"Temps restant: {remaining:.1f}s", (width//2 - 150, 120),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

        # Draw neutral position indicator
        if self.calibrated and self.config['ui']['show_dead_zone']:
            # Calculate screen position for neutral point
            if w > 0:
                face_center_x = x + w // 2
                face_center_y = y + h // 2

                # Draw dead zone
                dead_zone_x = int(self.config['dead_zone']['horizontal'] * w / 100)
                dead_zone_y = int(self.config['dead_zone']['vertical'] * h / 100)

                cv2.circle(frame, (face_center_x, face_center_y), 5, (0, 255, 255), -1)
                cv2.ellipse(frame, (face_center_x, face_center_y),
                           (dead_zone_x, dead_zone_y), 0, 0, 360, (255, 255, 0), 2)

        # Draw active keys
        if self.config['ui']['show_active_keys'] and self.calibrated:
            key_y = height - 100
            key_size = 60
            key_spacing = 80
            center_x = width // 2

            keys = self.config['keys']
            key_positions = {
                keys['forward']: (center_x, key_y - key_spacing),
                keys['left']: (center_x - key_spacing, key_y),
                keys['right']: (center_x + key_spacing, key_y),
                keys['backward']: (center_x, key_y)
            }

            for key, (kx, ky) in key_positions.items():
                color = (0, 255, 0) if key in self.last_active_keys else (100, 100, 100)
                cv2.rectangle(frame, (kx - key_size//2, ky - key_size//2),
                            (kx + key_size//2, ky + key_size//2), color, -1 if key in self.last_active_keys else 2)
                cv2.putText(frame, key.upper(), (kx - 15, ky + 10),
                           cv2.FONT_HERSHEY_BOLD, 1, (255, 255, 255), 2)

        # Draw FPS and status
        if self.config['ui']['show_fps']:
            status_text = "PAUSE" if self.is_paused else "ACTIF"
            status_color = (0, 165, 255) if self.is_paused else (0, 255, 0)

            cv2.putText(frame, f"FPS: {self.fps:.0f}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(frame, f"Statut: {status_text}", (10, 60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
            cv2.putText(frame, f"Mode: {self.config['control_mode']}", (10, 90),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        # Draw movement indicators
        if self.calibrated and dx != 0 or dy != 0:
            indicator_x = width - 150
            indicator_y = 100
            scale = 2

            # Draw crosshair
            cv2.line(frame, (indicator_x - 50, indicator_y), (indicator_x + 50, indicator_y), (100, 100, 100), 1)
            cv2.line(frame, (indicator_x, indicator_y - 50), (indicator_x, indicator_y + 50), (100, 100, 100), 1)

            # Draw movement vector
            end_x = int(indicator_x + dx * scale)
            end_y = int(indicator_y + dy * scale)
            cv2.arrowedLine(frame, (indicator_x, indicator_y), (end_x, end_y), (0, 255, 0), 3)

        # Draw controls help
        cv2.putText(frame, "C:Calibrer P:Pause Q:Quitter", (10, height - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        return frame

    def update_fps(self):
        """Update FPS counter"""
        self.frame_count += 1
        current_time = time.time()
        elapsed = current_time - self.last_fps_time

        if elapsed >= 1.0:
            self.fps = self.frame_count / elapsed
            self.frame_count = 0
            self.last_fps_time = current_time

    def log_session_data(self, dx, dy):
        """Log session data for analysis"""
        if self.config['logging']['enable']:
            self.movement_log.append({
                'timestamp': time.time() - self.session_start.timestamp(),
                'dx': dx,
                'dy': dy,
                'paused': self.is_paused,
                'active_keys': list(self.last_active_keys)
            })

    def save_session_log(self):
        """Save session log to CSV file"""
        if not self.config['logging']['enable'] or len(self.movement_log) == 0:
            return

        log_file = self.config['logging']['log_file']

        with open(log_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['session_start', 'timestamp', 'dx', 'dy', 'paused', 'active_keys'])

            # Write header if file is empty
            if f.tell() == 0:
                writer.writeheader()

            # Write log entries
            for entry in self.movement_log:
                entry['session_start'] = self.session_start.isoformat()
                entry['active_keys'] = ','.join(entry['active_keys'])
                writer.writerow(entry)

        print(f"\nSession enregistrée dans {log_file}")

    def run(self):
        """Main loop"""
        try:
            # Start calibration
            self.start_calibration()

            while True:
                ret, frame = self.camera_handler.get_frame()
                if not ret:
                    print("Erreur: Impossible de lire la frame")
                    continue

                # Detect face
                x, y, w, h, confidence = self.face_detector.detect_face(frame)

                if confidence > 0:
                    # Face detected
                    self.face_lost_time = None

                    if not self.calibrated:
                        # Calibration phase
                        if self.update_calibration(x, y, w, h):
                            pass  # Calibration complete
                    else:
                        # Normal operation
                        dx, dy = self.detect_head_movement(x, y, w, h)
                        self.control_car(dx, dy)
                        self.log_session_data(dx, dy)
                        frame = self.draw_ui(frame, x, y, w, h, dx, dy)
                else:
                    # Face not detected
                    if self.face_lost_time is None:
                        self.face_lost_time = time.time()
                    elif self.config['safety']['enable_auto_pause']:
                        elapsed = time.time() - self.face_lost_time
                        if elapsed > self.config['safety']['pause_delay_seconds']:
                            if not self.is_paused:
                                self.toggle_pause()

                    # Draw UI even without face
                    frame = self.draw_ui(frame, 0, 0, 0, 0, 0, 0)

                # Update FPS
                self.update_fps()

                # Show frame
                cv2.imshow('Conduite Accessible par Mouvements de Tete', frame)

                # Handle keyboard input
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('c'):
                    self.start_calibration()
                elif key == ord('p'):
                    self.toggle_pause()
                elif key == ord('m'):
                    # Cycle through control modes
                    modes = ['position', 'velocity', 'simplified']
                    current_idx = modes.index(self.config['control_mode'])
                    self.config['control_mode'] = modes[(current_idx + 1) % len(modes)]
                    print(f"Mode changé: {self.config['control_mode']}")
                elif key == ord('+') or key == ord('='):
                    # Increase sensitivity
                    self.config['sensitivity']['horizontal'] += 5
                    self.config['sensitivity']['vertical'] += 5
                    print(f"Sensibilité augmentée: {self.config['sensitivity']['horizontal']}")
                elif key == ord('-') or key == ord('_'):
                    # Decrease sensitivity
                    self.config['sensitivity']['horizontal'] = max(5, self.config['sensitivity']['horizontal'] - 5)
                    self.config['sensitivity']['vertical'] = max(5, self.config['sensitivity']['vertical'] - 5)
                    print(f"Sensibilité diminuée: {self.config['sensitivity']['horizontal']}")

                time.sleep(0.01)

        finally:
            # Cleanup
            self.release_all_keys()
            self.save_session_log()
            self.save_config()
            self.camera_handler.close()
            self.face_detector.close()
            self.face_mesh.close()
            cv2.destroyAllWindows()
            print("\nSession terminée. Au revoir!")

if __name__ == "__main__":
    print("="*60)
    print("  SYSTÈME DE CONDUITE ACCESSIBLE PAR MOUVEMENTS DE TÊTE")
    print("="*60)
    print("\nCommandes:")
    print("  C - Recalibrer")
    print("  P - Pause/Reprendre")
    print("  M - Changer de mode de contrôle")
    print("  +/- - Ajuster la sensibilité")
    print("  Q - Quitter")
    print("\n" + "="*60)

    try:
        driver = AccessibleHeadControlledDriving()
        driver.run()
    except KeyboardInterrupt:
        print("\n\nInterrompu par l'utilisateur")
    except Exception as e:
        print(f"\n\nErreur: {e}")
        import traceback
        traceback.print_exc()
