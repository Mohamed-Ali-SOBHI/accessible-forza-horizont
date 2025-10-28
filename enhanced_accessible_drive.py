"""
Enhanced Accessible Driving System
Version améliorée avec:
- Estimation de pose 3D (Yaw/Pitch/Roll)
- Détection de gestes faciaux
- Filtrage avancé anti-tremblements (DES + Kalman adaptatif)
- Prédiction de mouvement
- Assistant de conduite intelligent
- Monitoring de fatigue
"""

import cv2
import pyautogui
import time
import json
import csv
import numpy as np
from datetime import datetime
from camera_handler import CameraHandler

# Import new advanced modules
from advanced_head_pose import AdvancedHeadPose
from facial_gestures import FacialGestureDetector
from gesture_commands import GestureCommandMapper
from advanced_filters import CompositeFilter
from tremor_detector import TremorDetector
from motion_predictor import MotionPredictor
from driving_assistant import DrivingAssistant
from fatigue_monitor import FatigueMonitor


class EnhancedAccessibleDriving:
    def __init__(self, config_file='enhanced_config.json'):
        """Initialize enhanced accessible driving system"""
        print("="*70)
        print(" SYSTÈME DE CONDUITE ACCESSIBLE AMÉLIORÉ - VERSION AVANCÉE")
        print("="*70)

        # Load configuration
        self.config = self.load_config(config_file)
        self.config_file = config_file

        # Initialize camera
        camera_config = self.config.get('camera', {})
        camera_index = camera_config.get('index', -1)
        preferred_resolution = None
        if camera_config.get('width') and camera_config.get('height'):
            preferred_resolution = (
                int(camera_config['width']),
                int(camera_config['height'])
            )
        preferred_fps = camera_config.get('fps')
        prompt_on_multiple = not camera_config.get('auto_select', False)

        print("\nConfiguration camera amelioree:")
        print(f"  - Index preferentiel: {camera_index}")
        if preferred_resolution:
            print(f"  - Resolution demandee: {preferred_resolution[0]}x{preferred_resolution[1]}")
        if preferred_fps:
            print(f"  - FPS demandes: {preferred_fps}")

        self.camera_handler = CameraHandler(
            camera_index=camera_index,
            prompt_on_multiple=prompt_on_multiple,
            preferred_resolution=preferred_resolution,
            preferred_fps=preferred_fps,
        )

        # Screen setup
        self.screen_width, self.screen_height = pyautogui.size()

        # PyAutoGUI configuration (fail-safe handling)
        pyauto_cfg = self.config.get('pyautogui', {})
        self.original_pyautogui_failsafe = pyautogui.FAILSAFE
        if 'failsafe' in pyauto_cfg:
            pyautogui.FAILSAFE = bool(pyauto_cfg['failsafe'])
            state = "activ\u00e9" if pyautogui.FAILSAFE else "d\u00e9sactiv\u00e9"
            print(f"  - PyAutoGUI fail-safe {state} via configuration")
        self.pyautogui_auto_recover = pyauto_cfg.get('auto_recover', True)
        self.pyautogui_safe_margin = max(1, int(pyauto_cfg.get('safe_margin', 20)))

        # Initialize advanced modules
        print("\nInitialisation des modules avancés...")

        # 1. Head Pose Estimation (3D)
        print("  [1/8] Estimation de pose 3D...")
        self.head_pose = AdvancedHeadPose()
        self.head_pose.set_smoothing(self.config.get('head_pose', {}).get('smoothing', 0.4))

        head_pose_cfg = self.config.setdefault('head_pose', {})
        head_pose_cfg.setdefault('auto_accelerate', True)
        head_pose_cfg.setdefault('reverse_pitch_threshold', 18)
        head_pose_cfg.setdefault('reverse_pitch_release', 12)
        head_pose_cfg.setdefault('reverse_activation_frames', 5)

        self.auto_accelerate = bool(head_pose_cfg.get('auto_accelerate', True))
        self.reverse_pitch_threshold = float(head_pose_cfg.get('reverse_pitch_threshold', 18))
        self.reverse_pitch_release = float(head_pose_cfg.get('reverse_pitch_release', 12))
        if self.reverse_pitch_release >= self.reverse_pitch_threshold:
            self.reverse_pitch_release = max(self.reverse_pitch_threshold - 4, self.reverse_pitch_threshold * 0.7)
            head_pose_cfg['reverse_pitch_release'] = self.reverse_pitch_release
        self.reverse_activation_frames = max(1, int(head_pose_cfg.get('reverse_activation_frames', 5)))

        # 2. Facial Gestures
        print("  [2/8] Détection de gestes faciaux...")
        self.gesture_detector = FacialGestureDetector()

        # 3. Gesture Commands
        print("  [3/8] Mapping des commandes gestuelles...")
        gesture_config = self.config.get('gesture_commands', {})
        self.gesture_mapper = GestureCommandMapper(gesture_config)

        # 4. Advanced Filtering
        print("  [4/8] Filtres avancés anti-tremblements...")
        filter_config = self.config.get('advanced_filtering', {})
        self.composite_filter = CompositeFilter(filter_config)

        # 5. Tremor Detection
        print("  [5/8] Détecteur de tremblements...")
        tremor_config = self.config.get('tremor_detection', {})
        self.tremor_detector = TremorDetector(tremor_config)

        # 6. Motion Prediction
        print("  [6/8] Prédicteur de mouvement...")
        prediction_steps = self.config.get('motion_prediction', {}).get('steps', 2)
        self.motion_predictor = MotionPredictor(prediction_steps=prediction_steps)

        # 7. Driving Assistant
        print("  [7/8] Assistant de conduite intelligent...")
        assistance_level = self.config.get('driving_assistant', {}).get('level', 2)
        self.driving_assistant = DrivingAssistant(assistance_level=assistance_level)

        # 8. Fatigue Monitor
        print("  [8/8] Moniteur de fatigue...")
        self.fatigue_monitor = FatigueMonitor()

        # Calibration state
        self.calibrated = False
        self.calibration_start_time = None
        self.calibrating_gestures = False

        # Control state
        self.is_paused = False
        self.last_active_keys = set()
        self.motion_state = 'neutral'
        self.reverse_active = False
        self.reverse_counter = 0

        # Key bindings
        self.keys = self.config.get('keys', {
            'forward': 'z',
            'backward': 's',
            'left': 'q',
            'right': 'd'
        })

        # UI and logging
        self.fps = 0
        self.last_fps_time = time.time()
        self.frame_count = 0
        self.movement_log = []
        self.session_start = datetime.now()

        # Statistics
        self.stats = {
            'total_corrections': 0,
            'tremor_episodes': 0,
            'gesture_commands_used': 0
        }

        print("\n✓ Système initialisé avec succès!")
        print("\nPréparez-vous pour la calibration...")

    def load_config(self, config_file):
        """Load configuration from JSON file"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Fichier de configuration {config_file} non trouvé")
            print("Création d'une configuration par défaut...")
            config = self.get_default_config()
            self.save_config(config, config_file)
            return config

    def get_default_config(self):
        """Return default configuration"""
        return {
            "camera": {"index": -1},
            "head_pose": {
                "smoothing": 0.4,
                "yaw_sensitivity": 15,
                "pitch_sensitivity": 12,
                "use_yaw_for_steering": True,
                "use_pitch_for_throttle": False,
                "auto_accelerate": True,
                "reverse_pitch_threshold": 18,
                "reverse_pitch_release": 12,
                "reverse_activation_frames": 5
            },
            "gesture_commands": {
                "enabled": True,
                "gesture_mappings": {
                    "left_blink": "turn_signal_left",
                    "right_blink": "turn_signal_right",
                    "mouth_open": "emergency_brake",
                    "both_blink": "toggle_pause"
                },
                "key_bindings": {
                    "emergency_brake": "s"
                }
            },
            "advanced_filtering": {
                "use_des": True,
                "use_kalman": True,
                "use_lowpass": False,
                "des_alpha": 0.3,
                "des_beta": 0.1
            },
            "tremor_detection": {
                "tremor_frequency_range": [4, 12],
                "min_tremor_amplitude": 2.0
            },
            "motion_prediction": {
                "enabled": True,
                "steps": 2
            },
            "driving_assistant": {
                "level": 2,
                "auto_increase_on_fatigue": True
            },
            "keys": {
                "forward": "z",
                "backward": "s",
                "left": "q",
                "right": "d"
            },
            "ui": {
                "show_3d_pose": True,
                "show_gestures": True,
                "show_tremor_info": True,
                "show_fatigue": True,
                "mirror_video": True
            },
            "logging": {
                "enable": True,
                "log_file": "enhanced_driving_sessions.csv"
            }
        }

    def save_config(self, config=None, filename=None):
        """Save configuration to JSON file"""
        if config is None:
            config = self.config
        if filename is None:
            filename = self.config_file

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

    def start_calibration(self, calibrate_gestures=True):
        """Start calibration phase"""
        self.calibration_start_time = time.time()
        self.calibrating_gestures = calibrate_gestures
        self.calibrated = False

        print("\n" + "="*70)
        print(" CALIBRATION")
        print("="*70)
        if calibrate_gestures:
            print("Maintenez une expression neutre pendant 3 secondes...")
        else:
            print("Calibration des gestes seulement...")

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

                # Calibration phase
                if not self.calibrated:
                    if self.calibrating_gestures:
                        complete = self.gesture_detector.calibrate(frame, duration=3.0)
                        if complete:
                            self.calibrated = True
                            print("\n✓ Calibration terminée!")
                            self.print_controls()

                        # Show calibration UI
                        elapsed = time.time() - self.calibration_start_time if self.calibration_start_time else 0
                        remaining = max(0, 3.0 - elapsed)
                        self._draw_calibration_ui(frame, remaining)
                    else:
                        self.calibrated = True

                # Normal operation
                else:
                    # Estimate head pose (3D)
                    yaw, pitch, roll, pose_success, image_points = self.head_pose.estimate_pose(frame)

                    if pose_success:
                        # Apply advanced filtering
                        filtered_yaw, filtered_pitch = self.composite_filter.filter(yaw, pitch)

                        # Detect tremor
                        tremor_analysis = self.tremor_detector.update(yaw, pitch)

                        # Predict motion (compensate latency)
                        if self.config.get('motion_prediction', {}).get('enabled', True):
                            self.motion_predictor.update(filtered_yaw, filtered_pitch)
                            pred_yaw, pred_pitch = self.motion_predictor.predict()
                        else:
                            pred_yaw, pred_pitch = filtered_yaw, filtered_pitch

                        # Driving assistance
                        yaw_sens = self.config.get('head_pose', {}).get('yaw_sensitivity', 15)
                        pitch_sens = self.config.get('head_pose', {}).get('pitch_sensitivity', 12)

                        direction = self.driving_assistant.process_steering(pred_yaw, yaw_sens)
                        throttle = self.driving_assistant.process_throttle(
                            pred_pitch, -pitch_sens, pitch_sens
                        )

                        # Detect facial gestures before applying motion to use continuous signals
                        gestures = self.gesture_detector.detect_gestures(frame)

                        motion_state = self.determine_motion_state(pred_pitch, throttle, gestures)
                        self.control_car(direction, motion_state)

                        # Process gesture commands (ignore continuous mouth brake signal)
                        if self.config.get('gesture_commands', {}).get('enabled', True):
                            command_gestures = dict(gestures)
                            command_gestures.pop('mouth_open_active', None)
                            if command_gestures.get('mouth_open'):
                                command_gestures['mouth_open'] = False

                            active_commands = self.gesture_mapper.process_gestures(command_gestures)

                            if 'toggle_pause' in active_commands:
                                self.toggle_pause()

                        # Update fatigue monitor
                        input_variance = tremor_analysis.get('amplitude', 0)
                        fatigue_result = self.fatigue_monitor.update(
                            is_paused=self.is_paused,
                            input_variance=input_variance,
                            correction_count=self.stats['total_corrections']
                        )

                        # Auto-increase assistance on fatigue
                        if (self.config.get('driving_assistant', {}).get('auto_increase_on_fatigue', True) and
                            fatigue_result.get('suggested_assistance_increase', 0) > 0):
                            current_level = self.driving_assistant.assistance_level
                            new_level = min(3, current_level + 1)
                            if new_level != current_level:
                                self.driving_assistant.set_assistance_level(new_level)
                                print(f"⚠ Fatigue détectée - Assistance augmentée au niveau {new_level}")

                        # Draw comprehensive UI
                        frame = self._draw_main_ui(
                            frame, yaw, pitch, roll, image_points,
                            gestures, tremor_analysis, fatigue_result
                        )

                        # Log data
                        self.log_session_data(yaw, pitch, tremor_analysis, gestures)

                    else:
                        # No face detected
                        self._draw_no_face_ui(frame)
                        if self.last_active_keys:
                            self.release_all_keys()
                        self.motion_state = 'neutral'

                # Update FPS
                self.update_fps()

                # Show frame
                window_name = 'Conduite Accessible Améliorée - Version Avancée'
                cv2.imshow(window_name, frame)

                # Handle keyboard input
                key = cv2.waitKey(1) & 0xFF
                if not self._handle_keyboard(key):
                    break

                time.sleep(0.01)

        finally:
            self.cleanup()

    def determine_motion_state(self, pitch, throttle, gestures):
        """
        Determine desired motion state based on head pitch, optional throttle,
        and facial gestures. Returns one of: 'forward', 'reverse', 'brake', 'neutral'.
        """
        mouth_brake = gestures.get('mouth_open_active', gestures.get('mouth_open', False))

        if mouth_brake:
            self.motion_state = 'brake'
            self.reverse_active = False
            self.reverse_counter = 0
            return self.motion_state

        if not self.auto_accelerate:
            if throttle == 'forward':
                self.motion_state = 'forward'
            elif throttle == 'backward':
                self.motion_state = 'reverse'
            else:
                self.motion_state = 'neutral'
            return self.motion_state

        if pitch > self.reverse_pitch_threshold:
            self.reverse_counter = min(self.reverse_activation_frames, self.reverse_counter + 1)
        else:
            self.reverse_counter = max(0, self.reverse_counter - 1)

        if not self.reverse_active and self.reverse_counter >= self.reverse_activation_frames:
            self.reverse_active = True
        elif self.reverse_active and pitch < self.reverse_pitch_release:
            self.reverse_active = False
            self.reverse_counter = 0

        self.motion_state = 'reverse' if self.reverse_active else 'forward'
        return self.motion_state

    def control_car(self, direction, motion_state):
        """Control car based on steering direction and motion state"""
        if self.is_paused:
            self.release_all_keys()
            self.motion_state = 'neutral'
            return

        active_keys = set()

        # Steering
        if direction == 'left':
            active_keys.add(self.keys['left'])
        elif direction == 'right':
            active_keys.add(self.keys['right'])

        # Motion / throttle control
        if motion_state == 'forward':
            active_keys.add(self.keys['forward'])
        elif motion_state in ('reverse', 'brake'):
            active_keys.add(self.keys['backward'])

        # Update key states
        self.update_key_states(active_keys)

    def _recover_cursor_from_failsafe(self):
        """Recenter the cursor to recover from PyAutoGUI fail-safe triggers."""
        if not self.pyautogui_auto_recover:
            return

        print("⚠ PyAutoGUI fail-safe d\u00e9tect\u00e9e, recentrage du curseur...")
        previous_state = pyautogui.FAILSAFE
        try:
            pyautogui.FAILSAFE = False
            center_x = max(
                self.pyautogui_safe_margin,
                min(self.screen_width - self.pyautogui_safe_margin, self.screen_width // 2)
            )
            center_y = max(
                self.pyautogui_safe_margin,
                min(self.screen_height - self.pyautogui_safe_margin, self.screen_height // 2)
            )
            pyautogui.moveTo(center_x, center_y, duration=0)
        except Exception as err:
            print(f"  Impossible de recentrer automatiquement le curseur: {err}")
        finally:
            pyautogui.FAILSAFE = previous_state

    def _perform_key_action(self, action, key):
        """Execute PyAutoGUI key actions with optional fail-safe recovery."""
        attempts = 2 if self.pyautogui_auto_recover else 1
        action_name = getattr(action, "__name__", "action")

        for attempt in range(attempts):
            try:
                action(key)
                return True
            except pyautogui.FailSafeException:
                if not self.pyautogui_auto_recover:
                    raise
                if attempt == 0:
                    self._recover_cursor_from_failsafe()
                else:
                    print(f"  Impossible d'ex\u00e9cuter {action_name} sur '{key}' malgr\u00e9 la r\u00e9cup\u00e9ration.")
                    return False
        return False

    def update_key_states(self, active_keys):
        """Update keyboard states"""
        # Release keys no longer active
        for key in self.last_active_keys - active_keys:
            self._perform_key_action(pyautogui.keyUp, key)

        # Press new active keys
        for key in active_keys - self.last_active_keys:
            self._perform_key_action(pyautogui.keyDown, key)

        self.last_active_keys = active_keys

    def release_all_keys(self):
        """Release all keyboard keys"""
        for key in self.last_active_keys:
            self._perform_key_action(pyautogui.keyUp, key)
        self.last_active_keys.clear()

    def toggle_pause(self):
        """Toggle pause state"""
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.release_all_keys()
            self.motion_state = 'neutral'
            print("[PAUSE] Controle suspendu")
        else:
            print("[REPRISE] Controle actif")

    def _draw_calibration_ui(self, frame, remaining):
        """Draw calibration UI"""
        h, w = frame.shape[:2]
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, 150), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

        cv2.putText(frame, "CALIBRATION EN COURS", (w//2 - 200, 40),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 3)
        cv2.putText(frame, "Maintenez une expression neutre", (w//2 - 220, 80),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)
        cv2.putText(frame, f"Temps restant: {remaining:.1f}s", (w//2 - 120, 120),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

        return frame

    def _draw_main_ui(self, frame, yaw, pitch, roll, image_points, gestures, tremor_info, fatigue_info):
        """Draw comprehensive UI"""
        if self.config.get('ui', {}).get('mirror_video', True):
            frame = cv2.flip(frame, 1)

        # Draw 3D pose info
        if self.config.get('ui', {}).get('show_3d_pose', True):
            self.head_pose.draw_pose_info(frame, yaw, pitch, roll, image_points)

        # Draw gesture indicators
        if self.config.get('ui', {}).get('show_gestures', True):
            frame = self.gesture_detector.draw_gesture_indicators(frame, gestures)

        # Draw tremor info
        if self.config.get('ui', {}).get('show_tremor_info', True) and tremor_info.get('tremor_detected'):
            h, w = frame.shape[:2]
            tremor_text = f"Tremblements: {tremor_info['tremor_intensity']:.1%}"
            cv2.putText(frame, tremor_text, (w - 250, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)

        # Draw fatigue info
        if self.config.get('ui', {}).get('show_fatigue', True):
            h, w = frame.shape[:2]
            fatigue_color = (0, 255, 0) if fatigue_info['fatigue_level'] == "None" else (0, 165, 255)
            cv2.putText(frame, f"Fatigue: {fatigue_info['fatigue_level']}", (w - 250, 60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, fatigue_color, 2)

        # Draw active keys
        self._draw_active_keys(frame)

        # Draw status info
        self._draw_status(frame)

        return frame

    def _draw_active_keys(self, frame):
        """Draw active key indicators"""
        h, w = frame.shape[:2]
        key_y = h - 100
        key_size = 50
        key_spacing = 70
        center_x = w // 2

        key_positions = {
            self.keys['forward']: (center_x, key_y - key_spacing),
            self.keys['left']: (center_x - key_spacing, key_y),
            self.keys['right']: (center_x + key_spacing, key_y),
            self.keys['backward']: (center_x, key_y)
        }

        for key, (kx, ky) in key_positions.items():
            color = (0, 255, 0) if key in self.last_active_keys else (80, 80, 80)
            thickness = -1 if key in self.last_active_keys else 2
            cv2.rectangle(frame, (kx - key_size//2, ky - key_size//2),
                        (kx + key_size//2, ky + key_size//2), color, thickness)
            cv2.putText(frame, key.upper(), (kx - 12, ky + 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

    def _draw_status(self, frame):
        """Draw status information"""
        status_text = "PAUSE" if self.is_paused else "ACTIF"
        status_color = (0, 165, 255) if self.is_paused else (0, 255, 0)

        cv2.putText(frame, f"FPS: {self.fps:.0f}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(frame, f"Statut: {status_text}", (10, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, status_color, 2)

        assistance_level = self.driving_assistant.assistance_level
        cv2.putText(frame, f"Assistance: Niveau {assistance_level}", (10, 90),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        motion_labels = {
            'forward': 'AVANT',
            'reverse': 'ARRIERE',
            'brake': 'FREIN',
            'neutral': 'NEUTRE'
        }
        motion_text = motion_labels.get(self.motion_state, self.motion_state.upper())
        cv2.putText(frame, f"Mouvement: {motion_text}", (10, 120),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    def _draw_no_face_ui(self, frame):
        """Draw UI when no face detected"""
        h, w = frame.shape[:2]
        cv2.putText(frame, "AUCUN VISAGE DÉTECTÉ", (w//2 - 200, h//2),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

    def _handle_keyboard(self, key):
        """Handle keyboard input. Returns False to quit."""
        if key == ord('q'):
            return False
        elif key == ord('c'):
            self.start_calibration()
        elif key == ord('p'):
            self.toggle_pause()
        elif key == ord('a'):
            # Cycle assistance level
            new_level = (self.driving_assistant.assistance_level + 1) % 4
            self.driving_assistant.set_assistance_level(new_level)
            print(f"Assistance: {self.driving_assistant.get_assistance_description()}")
        elif key == ord('b'):
            # Mark break taken
            self.fatigue_monitor.mark_break_taken()

        return True

    def update_fps(self):
        """Update FPS counter"""
        self.frame_count += 1
        current_time = time.time()
        elapsed = current_time - self.last_fps_time

        if elapsed >= 1.0:
            self.fps = self.frame_count / elapsed
            self.frame_count = 0
            self.last_fps_time = current_time

    def log_session_data(self, yaw, pitch, tremor_info, gestures):
        """Log session data"""
        if not self.config.get('logging', {}).get('enable', True):
            return

        self.movement_log.append({
            'timestamp': time.time() - self.session_start.timestamp(),
            'yaw': yaw,
            'pitch': pitch,
            'tremor_detected': tremor_info.get('tremor_detected', False),
            'tremor_intensity': tremor_info.get('tremor_intensity', 0),
            'active_gestures': [k for k, v in gestures.items() if v],
            'paused': self.is_paused
        })

    def save_session_log(self):
        """Save session log to CSV"""
        if not self.config.get('logging', {}).get('enable', True) or len(self.movement_log) == 0:
            return

        log_file = self.config.get('logging', {}).get('log_file', 'enhanced_driving_sessions.csv')

        try:
            with open(log_file, 'a', newline='', encoding='utf-8') as f:
                fieldnames = ['session_start', 'timestamp', 'yaw', 'pitch',
                            'tremor_detected', 'tremor_intensity', 'active_gestures', 'paused']
                writer = csv.DictWriter(f, fieldnames=fieldnames)

                if f.tell() == 0:
                    writer.writeheader()

                for entry in self.movement_log:
                    entry['session_start'] = self.session_start.isoformat()
                    entry['active_gestures'] = ','.join(entry['active_gestures'])
                    writer.writerow(entry)

            print(f"\n✓ Session enregistrée dans {log_file}")
        except Exception as e:
            print(f"\n⚠ Erreur lors de la sauvegarde du log: {e}")

    def print_controls(self):
        """Print control instructions"""
        print("\n" + "="*70)
        print(" COMMANDES DISPONIBLES")
        print("="*70)
        print("  C - Recalibrer")
        print("  P - Pause/Reprendre")
        print("  A - Changer niveau d'assistance (0-3)")
        print("  B - Marquer pause (reset fatigue)")
        print("  Q - Quitter")
        print("="*70 + "\n")

    def cleanup(self):
        """Cleanup resources"""
        print("\nArrêt du système...")

        self.release_all_keys()
        self.save_session_log()
        self.save_config()

        # Print session statistics
        stats = self.fatigue_monitor.get_session_stats()
        print("\n" + "="*70)
        print(" STATISTIQUES DE SESSION")
        print("="*70)
        print(f"  Durée totale: {stats['session_duration_minutes']:.1f} minutes")
        print(f"  Temps actif: {stats['active_time_minutes']:.1f} minutes")
        print(f"  Niveau de fatigue final: {stats['fatigue_level']}")
        print("="*70)

        pyautogui.FAILSAFE = self.original_pyautogui_failsafe
        self.camera_handler.close()
        self.head_pose.close()
        self.gesture_detector.close()
        cv2.destroyAllWindows()

        print("\n✓ Session terminée. Au revoir!")


if __name__ == "__main__":
    try:
        driver = EnhancedAccessibleDriving()
        driver.run()
    except KeyboardInterrupt:
        print("\n\nInterrompu par l'utilisateur")
    except Exception as e:
        print(f"\n\nErreur: {e}")
        import traceback
        traceback.print_exc()
