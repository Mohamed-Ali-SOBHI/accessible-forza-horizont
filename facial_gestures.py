"""
Facial Gestures Detection Module
Detects facial expressions and micro-gestures for additional control commands:
- Eye blinks (left, right, both)
- Mouth open/close
- Eyebrow raises
- Smile detection
"""

import cv2
import numpy as np
import mediapipe as mp
from collections import deque
import time


class FacialGestureDetector:
    def __init__(self):
        """Initialize facial gesture detector with MediaPipe Face Mesh"""
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

        # Landmark indices for different facial features
        # Left eye landmarks
        self.LEFT_EYE_UPPER = [159, 145]
        self.LEFT_EYE_LOWER = [23, 117]

        # Right eye landmarks
        self.RIGHT_EYE_UPPER = [386, 374]
        self.RIGHT_EYE_LOWER = [253, 346]

        # Mouth landmarks
        self.MOUTH_UPPER = [13, 14]
        self.MOUTH_LOWER = [13, 14]
        self.MOUTH_LEFT = [61]
        self.MOUTH_RIGHT = [291]
        self.MOUTH_TOP = 13
        self.MOUTH_BOTTOM = 14

        # Eyebrow landmarks
        self.LEFT_EYEBROW = [70, 63, 105]
        self.RIGHT_EYEBROW = [300, 293, 334]

        # Mouth corners for smile detection
        self.MOUTH_CORNER_LEFT = 61
        self.MOUTH_CORNER_RIGHT = 291
        self.NOSE_BOTTOM = 2

        # Calibration values (will be set during calibration)
        self.neutral_left_eye_ratio = 0.2
        self.neutral_right_eye_ratio = 0.2
        self.neutral_mouth_ratio = 0.0
        self.neutral_eyebrow_height = 0.0
        self.neutral_smile_width = 0.0

        # Detection thresholds
        self.EYE_CLOSED_THRESHOLD = 0.5  # Ratio reduction for eye close
        self.MOUTH_OPEN_THRESHOLD = 1.5  # Ratio increase for mouth open
        self.EYEBROW_RAISE_THRESHOLD = 1.15  # Height increase for eyebrow raise
        self.SMILE_THRESHOLD = 1.1  # Width increase for smile

        # Gesture state tracking with debouncing
        self.gesture_history = {
            'left_blink': deque(maxlen=5),
            'right_blink': deque(maxlen=5),
            'both_blink': deque(maxlen=5),
            'mouth_open': deque(maxlen=5),
            'eyebrow_raise': deque(maxlen=5),
            'smile': deque(maxlen=5)
        }

        # Last gesture trigger times (for cooldown)
        self.last_gesture_time = {
            'left_blink': 0,
            'right_blink': 0,
            'both_blink': 0,
            'mouth_open': 0,
            'eyebrow_raise': 0,
            'smile': 0
        }

        self.gesture_cooldown = 0.5  # Seconds between gesture triggers

        # Calibration state
        self.is_calibrated = False
        self.calibration_samples = []

    def calibrate(self, frame, duration=3.0):
        """
        Calibrate neutral facial position

        Args:
            frame: Video frame
            duration: Calibration duration in seconds

        Returns:
            bool: True if calibration complete, False if still collecting
        """
        if len(self.calibration_samples) == 0:
            self.calibration_start_time = time.time()

        elapsed = time.time() - self.calibration_start_time

        if elapsed < duration:
            # Collect sample
            metrics = self._get_facial_metrics(frame)
            if metrics:
                self.calibration_samples.append(metrics)
            return False
        else:
            # Complete calibration
            if len(self.calibration_samples) > 0:
                # Calculate median values
                self.neutral_left_eye_ratio = np.median([s['left_eye_ratio'] for s in self.calibration_samples])
                self.neutral_right_eye_ratio = np.median([s['right_eye_ratio'] for s in self.calibration_samples])
                self.neutral_mouth_ratio = np.median([s['mouth_ratio'] for s in self.calibration_samples])
                self.neutral_eyebrow_height = np.median([s['eyebrow_height'] for s in self.calibration_samples])
                self.neutral_smile_width = np.median([s['smile_width'] for s in self.calibration_samples])

                self.is_calibrated = True
                print("Facial gestures calibration complete!")
                print(f"  Neutral left eye: {self.neutral_left_eye_ratio:.3f}")
                print(f"  Neutral right eye: {self.neutral_right_eye_ratio:.3f}")
                print(f"  Neutral mouth: {self.neutral_mouth_ratio:.3f}")

            self.calibration_samples = []
            return True

    def _get_facial_metrics(self, frame):
        """Extract facial metrics from frame"""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_frame)

        if not results.multi_face_landmarks:
            return None

        face_landmarks = results.multi_face_landmarks[0]
        h, w = frame.shape[:2]

        # Calculate all metrics
        left_eye_ratio = self._calculate_eye_aspect_ratio(face_landmarks, w, h, is_left=True)
        right_eye_ratio = self._calculate_eye_aspect_ratio(face_landmarks, w, h, is_left=False)
        mouth_ratio = self._calculate_mouth_aspect_ratio(face_landmarks, w, h)
        eyebrow_height = self._calculate_eyebrow_height(face_landmarks, w, h)
        smile_width = self._calculate_smile_width(face_landmarks, w, h)

        return {
            'left_eye_ratio': left_eye_ratio,
            'right_eye_ratio': right_eye_ratio,
            'mouth_ratio': mouth_ratio,
            'eyebrow_height': eyebrow_height,
            'smile_width': smile_width
        }

    def detect_gestures(self, frame):
        """
        Detect all facial gestures in frame

        Returns:
            dict: Dictionary of detected gestures with True/False values.
                  Includes both event-style triggers (debounced) and
                  sustained states for certain gestures such as
                  `mouth_open_active` which remains True while the mouth
                  stays open.
        """
        if not self.is_calibrated:
            return {
                'left_blink': False,
                'right_blink': False,
                'both_blink': False,
                'mouth_open': False,
                'mouth_open_active': False,
                'eyebrow_raise': False,
                'smile': False
            }

        metrics = self._get_facial_metrics(frame)
        if not metrics:
            return {
                'left_blink': False,
                'right_blink': False,
                'both_blink': False,
                'mouth_open': False,
                'mouth_open_active': False,
                'eyebrow_raise': False,
                'smile': False
            }

        current_time = time.time()
        gestures = {}

        # Detect left eye blink
        left_closed = metrics['left_eye_ratio'] < (self.neutral_left_eye_ratio * self.EYE_CLOSED_THRESHOLD)
        self.gesture_history['left_blink'].append(left_closed)
        gestures['left_blink'] = self._is_gesture_stable('left_blink', current_time, threshold=3)

        # Detect right eye blink
        right_closed = metrics['right_eye_ratio'] < (self.neutral_right_eye_ratio * self.EYE_CLOSED_THRESHOLD)
        self.gesture_history['right_blink'].append(right_closed)
        gestures['right_blink'] = self._is_gesture_stable('right_blink', current_time, threshold=3)

        # Detect both eyes blink
        both_closed = left_closed and right_closed
        self.gesture_history['both_blink'].append(both_closed)
        gestures['both_blink'] = self._is_gesture_stable('both_blink', current_time, threshold=3)

        # Detect mouth open
        mouth_open_raw = metrics['mouth_ratio'] > (self.neutral_mouth_ratio + self.MOUTH_OPEN_THRESHOLD)
        self.gesture_history['mouth_open'].append(mouth_open_raw)
        gestures['mouth_open'] = self._is_gesture_stable('mouth_open', current_time, threshold=4)
        gestures['mouth_open_active'] = mouth_open_raw

        # Detect eyebrow raise
        eyebrow_raised = metrics['eyebrow_height'] > (self.neutral_eyebrow_height * self.EYEBROW_RAISE_THRESHOLD)
        self.gesture_history['eyebrow_raise'].append(eyebrow_raised)
        gestures['eyebrow_raise'] = self._is_gesture_stable('eyebrow_raise', current_time, threshold=4)

        # Detect smile
        smiling = metrics['smile_width'] > (self.neutral_smile_width * self.SMILE_THRESHOLD)
        self.gesture_history['smile'].append(smiling)
        gestures['smile'] = self._is_gesture_stable('smile', current_time, threshold=4)

        return gestures

    def _is_gesture_stable(self, gesture_name, current_time, threshold=3):
        """Check if gesture is stable (debouncing) and not in cooldown"""
        # Check cooldown
        if current_time - self.last_gesture_time[gesture_name] < self.gesture_cooldown:
            return False

        # Check if gesture is stable (majority of recent samples)
        history = self.gesture_history[gesture_name]
        if len(history) < threshold:
            return False

        stable = sum(history) >= threshold

        if stable:
            self.last_gesture_time[gesture_name] = current_time

        return stable

    def _calculate_eye_aspect_ratio(self, landmarks, w, h, is_left=True):
        """Calculate eye aspect ratio (EAR) for blink detection"""
        if is_left:
            upper_points = self.LEFT_EYE_UPPER
            lower_points = self.LEFT_EYE_LOWER
        else:
            upper_points = self.RIGHT_EYE_UPPER
            lower_points = self.RIGHT_EYE_LOWER

        # Get vertical distance
        upper = landmarks.landmark[upper_points[0]]
        lower = landmarks.landmark[lower_points[0]]

        vertical_dist = np.sqrt((upper.x - lower.x)**2 + (upper.y - lower.y)**2)

        # Get horizontal distance
        left_point = landmarks.landmark[upper_points[0]]
        right_point = landmarks.landmark[upper_points[1]]

        horizontal_dist = np.sqrt((left_point.x - right_point.x)**2 + (left_point.y - right_point.y)**2)

        if horizontal_dist == 0:
            return 0

        # EAR = vertical / horizontal
        ear = vertical_dist / horizontal_dist
        return ear

    def _calculate_mouth_aspect_ratio(self, landmarks, w, h):
        """Calculate mouth aspect ratio for mouth open detection"""
        # Vertical distance (top to bottom)
        top = landmarks.landmark[self.MOUTH_TOP]
        bottom = landmarks.landmark[self.MOUTH_BOTTOM]
        vertical_dist = np.sqrt((top.x - bottom.x)**2 + (top.y - bottom.y)**2)

        # Horizontal distance (left to right)
        left = landmarks.landmark[self.MOUTH_CORNER_LEFT]
        right = landmarks.landmark[self.MOUTH_CORNER_RIGHT]
        horizontal_dist = np.sqrt((left.x - right.x)**2 + (left.y - right.y)**2)

        if horizontal_dist == 0:
            return 0

        # MAR = vertical / horizontal
        mar = vertical_dist / horizontal_dist
        return mar

    def _calculate_eyebrow_height(self, landmarks, w, h):
        """Calculate average eyebrow height (for eyebrow raise detection)"""
        eyebrow_points = self.LEFT_EYEBROW + self.RIGHT_EYEBROW
        avg_y = np.mean([landmarks.landmark[idx].y for idx in eyebrow_points])
        return avg_y

    def _calculate_smile_width(self, landmarks, w, h):
        """Calculate smile width (mouth corners distance)"""
        left = landmarks.landmark[self.MOUTH_CORNER_LEFT]
        right = landmarks.landmark[self.MOUTH_CORNER_RIGHT]

        distance = np.sqrt((left.x - right.x)**2 + (left.y - right.y)**2)
        return distance

    def draw_gesture_indicators(self, frame, gestures):
        """
        Draw gesture indicators on frame

        Args:
            frame: Image to draw on
            gestures: Dictionary of gesture states
        """
        h, w = frame.shape[:2]
        y_offset = h - 200

        # Draw background panel
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, y_offset - 10), (300, h - 10), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)

        # Draw gesture labels and status
        gesture_labels = {
            'left_blink': 'Clign. Gauche',
            'right_blink': 'Clign. Droit',
            'both_blink': 'Clign. 2 Yeux',
            'mouth_open': 'Bouche Ouverte',
            'eyebrow_raise': 'Sourcils Leves',
            'smile': 'Sourire'
        }

        y = y_offset
        for gesture_key, label in gesture_labels.items():
            active = gestures.get(gesture_key, False)
            color = (0, 255, 0) if active else (100, 100, 100)

            # Draw status indicator
            cv2.circle(frame, (25, y + 5), 8, color, -1)

            # Draw label
            cv2.putText(frame, label, (45, y + 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

            y += 30

        return frame

    def close(self):
        """Clean up resources"""
        if hasattr(self, 'face_mesh'):
            self.face_mesh.close()


if __name__ == "__main__":
    # Test facial gesture detection
    print("Testing Facial Gesture Detection")
    print("Calibration will start in 3 seconds...")
    print("Keep a neutral expression during calibration")
    time.sleep(3)

    cap = cv2.VideoCapture(0)
    detector = FacialGestureDetector()

    calibrating = True
    calibration_start = time.time()

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if calibrating:
            # Calibration phase
            complete = detector.calibrate(frame, duration=3.0)
            if complete:
                calibrating = False
                print("Calibration complete! Try different facial expressions:")
                print("- Blink left eye")
                print("- Blink right eye")
                print("- Open mouth wide")
                print("- Raise eyebrows")
                print("- Smile")

            # Show calibration progress
            elapsed = time.time() - calibration_start
            remaining = max(0, 3.0 - elapsed)
            cv2.putText(frame, f"CALIBRATION: {remaining:.1f}s", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
        else:
            # Detection phase
            gestures = detector.detect_gestures(frame)
            frame = detector.draw_gesture_indicators(frame, gestures)

            # Show active gestures
            active_gestures = [k for k, v in gestures.items() if v]
            if active_gestures:
                text = "Active: " + ", ".join(active_gestures)
                cv2.putText(frame, text, (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        cv2.imshow('Facial Gesture Detection', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    detector.close()
    cv2.destroyAllWindows()
    print("Test completed")
