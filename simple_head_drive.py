import time
import cv2
import numpy as np
import mediapipe as mp
import pyautogui

from camera_handler import CameraHandler


class SimpleHeadControlledDrive:
    """
    Minimal head-controlled accessibility driver.

    - Auto-selects the first available camera (unless specified) with option to change.
    - Acceleration is proportional to mouth opening (small opening = low speed, wide opening = full throttle).
    - Tilt head down strongly to engage reverse.
    - Lift your head (chin up) to brake (voluntary, independent of mouth motion).
    - Turn by looking left/right; steering uses a pulse pattern to mimic analog control.
    """

    def __init__(
        self,
        forward_key: str = 'z',
        backward_key: str = 's',
        left_key: str = 'q',
        right_key: str = 'd',
        calibration_seconds: float = 2.0,
        mirror_horizontal: bool = True,
        cruise_mode: str = 'continuous',
        status_callback=None,
        camera_override: int = -1,
    ) -> None:
        self.forward_key = forward_key
        self.backward_key = backward_key
        self.left_key = left_key
        self.right_key = right_key
        self.calibration_seconds = calibration_seconds
        self.mirror_horizontal = mirror_horizontal
        self.cruise_mode = cruise_mode  # 'continuous' or 'pulsed'
        self.status_callback = status_callback
        self.camera_override = camera_override

        self.camera = None
        self._camera_kwargs = {
            "camera_index": camera_override,
            "prompt_on_multiple": camera_override == -1,
        }
        self.face_mesh = mp.solutions.face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )

        # Calibration baselines
        self.neutral_center = None
        self.neutral_width = None
        self.neutral_height = None
        self.mouth_baseline = None
        self.mouth_accel_start = None
        self.mouth_accel_max = None
        self.reverse_threshold = None
        self.brake_threshold = None

        # Steering thresholds
        self.steer_dead_zone = None
        self.steer_full_threshold = None

        # Runtime state
        self.active_keys = set()
        self.window_name = "Simple Head Drive"

        self.original_failsafe = pyautogui.FAILSAFE
        pyautogui.FAILSAFE = False

        # Cruise control state
        self.cruise_period = 0.5
        self._cruise_state = True
        self._cruise_last_toggle = time.time()

        # Steering pulse state
        self.steer_pulse_base = 0.35
        self._steer_prev_direction = 'center'
        self._steer_pulse_state = False
        self._steer_pulse_last_switch = time.time()
        self._steer_on_duration = self.steer_pulse_base
        self._steer_off_duration = self.steer_pulse_base

        self.stop_requested = False

    def _notify(self, event, **payload):
        if self.status_callback:
            try:
                self.status_callback(event, payload)
            except Exception:
                pass

    # --------------------------------------------------------------------- #
    # Main control flow
    # --------------------------------------------------------------------- #

    def run(self) -> None:
        try:
            self._initialize_camera()
            self._notify("app", state="camera_ready")

            while True:
                if self.stop_requested:
                    break

                if not self._calibrate():
                    if not self._handle_calibration_failure():
                        break
                    continue

                if self.stop_requested:
                    break

                self._loop()
                break
        finally:
            self._cleanup()

    # --------------------------------------------------------------------- #
    # Calibration & camera management
    # --------------------------------------------------------------------- #

    def _initialize_camera(self) -> None:
        if self.camera is not None:
            self.camera.close()
        self.camera = CameraHandler(**self._camera_kwargs)

    def _handle_calibration_failure(self) -> bool:
        print("\nCalibration failed: no face detected.")
        print("Make sure you are visible to the selected camera.")
        response = input("Enter = retry | C = change camera | Q = quit : ").strip().lower()

        if response == 'q':
            return False
        if response == 'c':
            print("\nSelecting camera...")
            self._initialize_camera()
            self._notify("app", state="camera_ready")
        return True

    def _calibrate(self) -> bool:
        self.stop_requested = False
        print("\n=== CALIBRATION ===")
        print("Keep your head straight, mouth closed, and relaxed for a few seconds...")
        self._notify("calibration", stage="start")

        centers = []
        widths = []
        heights = []
        mouth_ratios = []

        start_time = time.time()
        last_frame = np.zeros((480, 640, 3), dtype=np.uint8)

        while time.time() - start_time < self.calibration_seconds:
            if self.stop_requested:
                return False
            success, frame, metrics = self._capture_metrics()
            if frame is not None:
                last_frame = frame

            if not success:
                self._show_frame(frame, "No face detected - stay centered")
                continue

            centers.append((metrics['center_x'], metrics['center_y']))
            widths.append(metrics['width'])
            heights.append(metrics['height'])
            mouth_ratios.append(metrics['mouth_ratio'])

            remaining = max(0.0, self.calibration_seconds - (time.time() - start_time))
            self._show_frame(frame, f"Calibration... {remaining:0.1f}s")

        if not centers:
            self._show_frame(last_frame, "Calibration failed - no face detected")
            cv2.waitKey(500)
            self._notify("calibration", stage="failed")
            return False

        centers = np.array(centers)
        widths = np.array(widths)
        heights = np.array(heights)
        mouth_ratios = np.array(mouth_ratios)

        self.neutral_center = centers.mean(axis=0)
        self.neutral_width = widths.mean()
        self.neutral_height = heights.mean()

        self.steer_dead_zone = max(5.0, self.neutral_width * 0.08)
        self.steer_full_threshold = max(15.0, self.neutral_width * 0.22)
        self.reverse_threshold = max(12.0, self.neutral_height * 0.22)

        self.mouth_baseline = float(np.median(mouth_ratios))
        mouth_std = float(np.std(mouth_ratios))
        self.mouth_accel_start = self.mouth_baseline + max(0.04, mouth_std * 1.5)
        mouth_full = self.mouth_baseline + max(0.25, self.mouth_baseline * 0.6, mouth_std * 4.0)
        if mouth_full <= self.mouth_accel_start:
            mouth_full = self.mouth_accel_start + 0.12
        self.mouth_accel_max = mouth_full

        self.brake_threshold = max(10.0, self.neutral_height * 0.16)

        print("Calibration complete.")
        print(f"  Neutral center: {self.neutral_center}")
        print(f"  Neutral width: {self.neutral_width:.1f}px")
        print(f"  Neutral height: {self.neutral_height:.1f}px")
        print(f"  Steering dead zone: {self.steer_dead_zone:.1f}px | full turn: {self.steer_full_threshold:.1f}px")
        print(f"  Reverse threshold: {self.reverse_threshold:.1f}px")
        print(f"  Mouth baseline: {self.mouth_baseline:.3f}")
        print(f"  Mouth acceleration start: {self.mouth_accel_start:.3f}, full: {self.mouth_accel_max:.3f}")
        print(f"  Head-up brake threshold (pixels): {self.brake_threshold:.1f}")

        self._show_frame(last_frame, "Calibration OK - ready!")
        self._notify("calibration", stage="complete")
        cv2.waitKey(500)

        self._cruise_state = True
        self._cruise_last_toggle = time.time()
        self._reset_steering_state()
        return True

    # --------------------------------------------------------------------- #
    # Runtime loop
    # --------------------------------------------------------------------- #

    def _loop(self) -> None:
        print("\n=== ACTIVE CONTROL ===")
        print("Turn your head left/right to steer (joystick style).")
        print("Open your mouth to accelerate (small opening = low speed, wide opening = full throttle).")
        print("Lift your head up to brake; drop your head down for reverse. Press Q or ESC to quit.")

        last_state = {"steer": "center:0", "motion": "idle"}

        while True:
            if self.stop_requested:
                break
            success, frame, metrics = self._capture_metrics()

            if not success:
                self._update_keys(set())
                self._reset_steering_state()
                self._cruise_state = True
                self._cruise_last_toggle = time.time()
                self._show_frame(frame, "Face lost - controls released")
                key = cv2.waitKey(1) & 0xFF
                if key in (ord('q'), 27):
                    break
                continue

            dx = metrics['center_x'] - self.neutral_center[0]
            dy = metrics['center_y'] - self.neutral_center[1]
            mouth_ratio = metrics['mouth_ratio']

            if self.mirror_horizontal:
                dx = -dx

            steering_keys, steer_direction, steer_intensity = self._compute_steering(dx)

            if self.mouth_accel_max > self.mouth_accel_start:
                accel_intensity = (mouth_ratio - self.mouth_accel_start) / (
                    self.mouth_accel_max - self.mouth_accel_start
                )
            else:
                accel_intensity = 0.0
            accel_intensity = max(0.0, min(1.0, accel_intensity))

            head_up_brake = (
                self.brake_threshold is not None
                and (-dy) > self.brake_threshold
            )

            if dy > self.reverse_threshold:
                motion = "reverse"
            elif head_up_brake:
                motion = "brake"
            elif accel_intensity > 0:
                motion = "accelerate"
            else:
                motion = "idle"

            keys_to_hold = self._compute_motion_keys(motion, accel_intensity)
            keys_to_hold.update(steering_keys)
            self._update_keys(keys_to_hold)

            if steer_direction == "center":
                steer_label = "CENTER"
            else:
                direction_text = "LEFT" if steer_direction == "left" else "RIGHT"
                steer_label = f"{direction_text} {int(steer_intensity * 100):02d}%"

            if motion == "accelerate":
                motion_label = f"ACCELERATION {int(accel_intensity * 100):02d}%"
            elif motion == "reverse":
                motion_label = "REVERSE"
            elif motion == "brake":
                motion_label = "BRAKE (head up)"
            else:
                motion_label = "COAST"

            status_text = f"Head: {steer_label} | Motion: {motion_label}"
            self._show_frame(frame, status_text)
            self._notify("status", text=status_text, motion=motion, steer=steer_label)

            steer_state_repr = f"{steer_direction}:{int(steer_intensity * 100)}"
            motion_state_repr = (
                f"{motion}:{int(accel_intensity * 100)}" if motion == "accelerate" else motion
            )
            if (steer_state_repr != last_state["steer"]) or (motion_state_repr != last_state["motion"]):
                print(status_text)
                last_state["steer"] = steer_state_repr
                last_state["motion"] = motion_state_repr

            key = cv2.waitKey(1) & 0xFF
            if key in (ord('q'), 27):
                break

            time.sleep(0.01)

    def request_stop(self):
        self.stop_requested = True
        self._notify("app", state="stop_requested")

    # --------------------------------------------------------------------- #
    # Metrics & helpers
    # --------------------------------------------------------------------- #

    def _capture_metrics(self):
        ret, frame = self.camera.get_frame()
        if not ret:
            empty = np.zeros((480, 640, 3), dtype=np.uint8)
            return False, empty, {}

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb)

        if not results.multi_face_landmarks:
            return False, frame, {}

        landmarks = results.multi_face_landmarks[0].landmark
        h, w = frame.shape[:2]

        xs = np.array([lm.x for lm in landmarks])
        ys = np.array([lm.y for lm in landmarks])

        min_x, max_x = xs.min(), xs.max()
        min_y, max_y = ys.min(), ys.max()

        center_x = (min_x + max_x) * 0.5 * w
        center_y = (min_y + max_y) * 0.5 * h
        width = (max_x - min_x) * w
        height = (max_y - min_y) * h

        mouth_vertical, mouth_horizontal = self._mouth_dimensions(landmarks, w, h)
        mouth_ratio = 0.0 if mouth_horizontal <= 1e-6 else mouth_vertical / mouth_horizontal

        metrics = {
            'center_x': center_x,
            'center_y': center_y,
            'width': width,
            'height': height,
            'mouth_ratio': mouth_ratio,
                    }

        return True, frame, metrics

    @staticmethod
    def _mouth_dimensions(landmarks, width, height):
        upper = landmarks[13]
        lower = landmarks[14]
        left = landmarks[61]
        right = landmarks[291]

        vertical = np.hypot(
            (upper.x - lower.x) * width,
            (upper.y - lower.y) * height,
        )
        horizontal = np.hypot(
            (left.x - right.x) * width,
            (left.y - right.y) * height,
        )
        return vertical, horizontal


    def _reset_steering_state(self):
        self._steer_prev_direction = 'center'
        self._steer_pulse_state = False
        self._steer_pulse_last_switch = time.time()
        self._steer_on_duration = self.steer_pulse_base
        self._steer_off_duration = self.steer_pulse_base

    def _compute_steering(self, dx):
        keys = set()
        now = time.time()
        abs_dx = abs(dx)

        if abs_dx <= self.steer_dead_zone:
            self._reset_steering_state()
            return keys, "center", 0.0

        direction = "right" if dx > 0 else "left"
        if self._steer_prev_direction != direction:
            self._steer_prev_direction = direction
            self._steer_pulse_state = True
            self._steer_pulse_last_switch = now

        intensity = min(1.0, abs_dx / self.steer_full_threshold)
        key = self.right_key if direction == "right" else self.left_key

        if abs_dx >= self.steer_full_threshold:
            keys.add(key)
            self._steer_pulse_state = True
            self._steer_on_duration = self.steer_pulse_base
            self._steer_off_duration = 0.0
            self._steer_pulse_last_switch = now
        else:
            duty_cycle = min(0.95, max(0.25, 0.35 + 0.5 * intensity))
            period = max(0.15, self.steer_pulse_base * (1.1 - 0.6 * intensity))
            self._steer_on_duration = duty_cycle * period
            self._steer_off_duration = max(0.01, period - self._steer_on_duration)

            elapsed = now - self._steer_pulse_last_switch
            if self._steer_pulse_state and elapsed >= self._steer_on_duration:
                self._steer_pulse_state = False
                self._steer_pulse_last_switch = now
            elif (not self._steer_pulse_state) and elapsed >= self._steer_off_duration:
                self._steer_pulse_state = True
                self._steer_pulse_last_switch = now

            if self._steer_pulse_state:
                keys.add(key)

        return keys, direction, intensity

    def _compute_motion_keys(self, motion, intensity=0.0):
        keys = set()
        now = time.time()

        if motion == "accelerate":
            intensity = max(0.0, min(1.0, intensity))

            if self.cruise_mode == 'continuous' and intensity >= 0.85:
                keys.add(self.forward_key)
                self._cruise_state = True
                self._cruise_last_toggle = now
            else:
                effective = max(0.05, intensity)
                base_period = max(0.1, self.cruise_period * (1.1 - 0.5 * effective))
                on_ratio = min(0.98, max(0.25, 0.25 + effective * 0.6))
                on_duration = on_ratio * base_period
                off_duration = max(0.02, base_period - on_duration)

                elapsed = now - self._cruise_last_toggle
                if self._cruise_state and elapsed >= on_duration:
                    self._cruise_state = False
                    self._cruise_last_toggle = now
                elif (not self._cruise_state) and elapsed >= off_duration:
                    self._cruise_state = True
                    self._cruise_last_toggle = now

                if self._cruise_state:
                    keys.add(self.forward_key)
        elif motion in ("reverse", "brake"):
            self._cruise_state = True
            self._cruise_last_toggle = now
            keys.add(self.backward_key)
        else:
            self._cruise_state = True
            self._cruise_last_toggle = now

        return keys

    def _update_keys(self, target_keys):
        to_release = self.active_keys - target_keys
        to_press = target_keys - self.active_keys

        for key in to_release:
            try:
                pyautogui.keyUp(key)
            except pyautogui.FailSafeException:
                pass

        for key in to_press:
            try:
                pyautogui.keyDown(key)
            except pyautogui.FailSafeException:
                pass

        self.active_keys = set(target_keys)

    def _show_frame(self, frame, status_text):
        display = frame.copy()
        cv2.putText(display, status_text, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        cv2.imshow(self.window_name, display)

    def _cleanup(self):
        self._update_keys(set())
        if self.camera is not None:
            self.camera.close()
        if getattr(self, "face_mesh", None):
            self.face_mesh.close()
        cv2.destroyAllWindows()
        pyautogui.FAILSAFE = self.original_failsafe
        self._notify("app", state="stopped")
        print("\nCleanup complete. Goodbye!")


if __name__ == "__main__":
    try:
        driver = SimpleHeadControlledDrive()
        driver.run()
    except KeyboardInterrupt:
        print("\nStopped by user.")
