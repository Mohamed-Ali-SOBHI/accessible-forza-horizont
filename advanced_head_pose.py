"""
Advanced Head Pose Estimation Module
Calculates 3D head orientation (Yaw, Pitch, Roll) using MediaPipe Face Mesh
and Perspective-n-Point (PnP) algorithm for improved driving control.
"""

import cv2
import numpy as np
import mediapipe as mp


class AdvancedHeadPose:
    def __init__(self):
        """Initialize head pose estimator with MediaPipe Face Mesh"""
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

        # 3D model points for key facial landmarks (based on average human face)
        # Units are in arbitrary scale, relative proportions matter
        self.model_points = np.array([
            (0.0, 0.0, 0.0),          # Nose tip (landmark 1)
            (0.0, -330.0, -65.0),     # Chin (landmark 152)
            (-225.0, 170.0, -135.0),  # Left eye left corner (landmark 33)
            (225.0, 170.0, -135.0),   # Right eye right corner (landmark 263)
            (-150.0, -150.0, -125.0), # Left mouth corner (landmark 61)
            (150.0, -150.0, -125.0)   # Right mouth corner (landmark 291)
        ], dtype=np.float64)

        # MediaPipe Face Mesh landmark indices for these points
        self.landmark_indices = [1, 152, 33, 263, 61, 291]

        # Camera matrix (will be initialized with actual frame size)
        self.camera_matrix = None
        self.dist_coeffs = np.zeros((4, 1))  # Assuming no lens distortion

        # Smoothing state for angles
        self.prev_yaw = 0.0
        self.prev_pitch = 0.0
        self.prev_roll = 0.0
        self.smoothing_factor = 0.4  # Lower = more smoothing

    def initialize_camera(self, frame_width, frame_height):
        """Initialize camera matrix based on frame dimensions"""
        focal_length = frame_width
        center = (frame_width / 2, frame_height / 2)

        self.camera_matrix = np.array([
            [focal_length, 0, center[0]],
            [0, focal_length, center[1]],
            [0, 0, 1]
        ], dtype=np.float64)

    def estimate_pose(self, frame):
        """
        Estimate head pose from frame

        Returns:
            tuple: (yaw, pitch, roll, success, image_points)
            - yaw: Rotation around Y-axis (left/right looking) in degrees
            - pitch: Rotation around X-axis (up/down looking) in degrees
            - roll: Rotation around Z-axis (head tilt) in degrees
            - success: Boolean indicating if pose was estimated
            - image_points: 2D coordinates of facial landmarks used
        """
        # Initialize camera matrix if not done
        if self.camera_matrix is None:
            h, w = frame.shape[:2]
            self.initialize_camera(w, h)

        # Convert to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_frame)

        if not results.multi_face_landmarks:
            return self.prev_yaw, self.prev_pitch, self.prev_roll, False, None

        # Get first face landmarks
        face_landmarks = results.multi_face_landmarks[0]

        # Extract 2D image points for key landmarks
        h, w = frame.shape[:2]
        image_points = []

        for idx in self.landmark_indices:
            landmark = face_landmarks.landmark[idx]
            x = int(landmark.x * w)
            y = int(landmark.y * h)
            image_points.append([x, y])

        image_points = np.array(image_points, dtype=np.float64)

        # Solve PnP to get rotation and translation vectors
        success, rotation_vec, translation_vec = cv2.solvePnP(
            self.model_points,
            image_points,
            self.camera_matrix,
            self.dist_coeffs,
            flags=cv2.SOLVEPNP_ITERATIVE
        )

        if not success:
            return self.prev_yaw, self.prev_pitch, self.prev_roll, False, image_points

        # Convert rotation vector to rotation matrix
        rotation_mat, _ = cv2.Rodrigues(rotation_vec)

        # Calculate Euler angles from rotation matrix
        yaw, pitch, roll = self._rotation_matrix_to_euler_angles(rotation_mat)

        # Apply smoothing
        yaw = self._smooth_angle(yaw, self.prev_yaw)
        pitch = self._smooth_angle(pitch, self.prev_pitch)
        roll = self._smooth_angle(roll, self.prev_roll)

        # Update previous values
        self.prev_yaw = yaw
        self.prev_pitch = pitch
        self.prev_roll = roll

        return yaw, pitch, roll, True, image_points

    def _rotation_matrix_to_euler_angles(self, R):
        """
        Convert rotation matrix to Euler angles (Yaw, Pitch, Roll)

        Args:
            R: 3x3 rotation matrix

        Returns:
            tuple: (yaw, pitch, roll) in degrees
        """
        # Calculate yaw (rotation around Y-axis)
        sy = np.sqrt(R[0, 0] ** 2 + R[1, 0] ** 2)
        singular = sy < 1e-6

        if not singular:
            yaw = np.arctan2(R[1, 0], R[0, 0])
            pitch = np.arctan2(-R[2, 0], sy)
            roll = np.arctan2(R[2, 1], R[2, 2])
        else:
            yaw = np.arctan2(-R[1, 2], R[1, 1])
            pitch = np.arctan2(-R[2, 0], sy)
            roll = 0

        # Convert from radians to degrees
        yaw = np.degrees(yaw)
        pitch = np.degrees(pitch)
        roll = np.degrees(roll)

        return yaw, pitch, roll

    def _smooth_angle(self, new_angle, prev_angle):
        """Apply exponential smoothing to angle"""
        return self.smoothing_factor * new_angle + (1 - self.smoothing_factor) * prev_angle

    def set_smoothing(self, factor):
        """
        Set smoothing factor

        Args:
            factor: Float between 0 and 1
                   0 = maximum smoothing (very laggy)
                   1 = no smoothing (jittery)
                   0.3-0.5 = recommended range
        """
        self.smoothing_factor = max(0.0, min(1.0, factor))

    def draw_pose_info(self, frame, yaw, pitch, roll, image_points=None):
        """
        Draw pose information on frame

        Args:
            frame: Image to draw on
            yaw: Yaw angle in degrees
            pitch: Pitch angle in degrees
            roll: Roll angle in degrees
            image_points: Optional 2D landmark points to visualize
        """
        h, w = frame.shape[:2]

        # Draw angle values
        text_y = 120
        cv2.putText(frame, f"Yaw (L/R): {yaw:.1f}deg", (10, text_y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        cv2.putText(frame, f"Pitch (U/D): {pitch:.1f}deg", (10, text_y + 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        cv2.putText(frame, f"Roll (Tilt): {roll:.1f}deg", (10, text_y + 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

        # Draw 3D axis representation
        if image_points is not None and len(image_points) > 0:
            # Use nose tip as origin
            nose_tip = tuple(image_points[0].astype(int))

            # Calculate axis endpoints
            axis_length = 100

            # Convert angles to radians
            yaw_rad = np.radians(yaw)
            pitch_rad = np.radians(pitch)

            # X-axis (red) - points right
            x_end = (
                int(nose_tip[0] + axis_length * np.cos(yaw_rad)),
                int(nose_tip[1] - axis_length * np.sin(pitch_rad))
            )
            cv2.arrowedLine(frame, nose_tip, x_end, (0, 0, 255), 3, tipLength=0.3)

            # Y-axis (green) - points up
            y_end = (
                int(nose_tip[0]),
                int(nose_tip[1] - axis_length)
            )
            cv2.arrowedLine(frame, nose_tip, y_end, (0, 255, 0), 3, tipLength=0.3)

            # Z-axis (blue) - points forward (toward camera)
            z_end = (
                int(nose_tip[0] + axis_length * np.sin(yaw_rad)),
                int(nose_tip[1] + axis_length * np.sin(pitch_rad))
            )
            cv2.arrowedLine(frame, nose_tip, z_end, (255, 0, 0), 3, tipLength=0.3)

            # Draw landmark points
            for point in image_points:
                cv2.circle(frame, tuple(point.astype(int)), 3, (255, 255, 0), -1)

        return frame

    def get_direction_from_yaw(self, yaw, threshold=15):
        """
        Get steering direction from yaw angle

        Args:
            yaw: Yaw angle in degrees (negative = looking left, positive = looking right)
            threshold: Angle threshold to trigger direction

        Returns:
            str: 'left', 'right', or 'center'
        """
        if yaw < -threshold:
            return 'left'
        elif yaw > threshold:
            return 'right'
        else:
            return 'center'

    def get_throttle_from_pitch(self, pitch, forward_threshold=-10, backward_threshold=10):
        """
        Get throttle control from pitch angle

        Args:
            pitch: Pitch angle in degrees (negative = looking up, positive = looking down)
            forward_threshold: Angle for forward acceleration
            backward_threshold: Angle for braking/reverse

        Returns:
            str: 'forward', 'backward', or 'neutral'
        """
        if pitch < forward_threshold:
            return 'forward'
        elif pitch > backward_threshold:
            return 'backward'
        else:
            return 'neutral'

    def close(self):
        """Clean up resources"""
        if hasattr(self, 'face_mesh'):
            self.face_mesh.close()


if __name__ == "__main__":
    # Test the head pose estimator
    print("Testing Advanced Head Pose Estimation")
    print("Press 'q' to quit")

    cap = cv2.VideoCapture(0)
    pose_estimator = AdvancedHeadPose()

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Estimate pose
        yaw, pitch, roll, success, image_points = pose_estimator.estimate_pose(frame)

        if success:
            # Draw pose information
            frame = pose_estimator.draw_pose_info(frame, yaw, pitch, roll, image_points)

            # Get direction and throttle
            direction = pose_estimator.get_direction_from_yaw(yaw)
            throttle = pose_estimator.get_throttle_from_pitch(pitch)

            # Display control commands
            cv2.putText(frame, f"Direction: {direction.upper()}", (10, 210),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame, f"Throttle: {throttle.upper()}", (10, 240),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        else:
            cv2.putText(frame, "NO FACE DETECTED", (10, 210),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        cv2.imshow('Advanced Head Pose Estimation', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    pose_estimator.close()
    cv2.destroyAllWindows()
    print("Test completed")
