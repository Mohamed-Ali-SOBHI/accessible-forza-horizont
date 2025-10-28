"""
Motion Prediction Module
Predicts future head position to compensate for processing latency
and improve responsiveness of the control system
"""

import numpy as np
from collections import deque


class MotionPredictor:
    def __init__(self, prediction_steps=2, history_length=10):
        """
        Initialize motion predictor

        Args:
            prediction_steps: Number of frames ahead to predict
            history_length: Number of historical positions to use
        """
        self.prediction_steps = prediction_steps
        self.history_length = history_length

        # Position and velocity history
        self.position_history = deque(maxlen=history_length)
        self.velocity_history = deque(maxlen=history_length)
        self.acceleration_history = deque(maxlen=history_length - 1)

        # Last prediction
        self.last_prediction = (0, 0)

    def update(self, x, y):
        """
        Update predictor with new position

        Args:
            x: Current X position
            y: Current Y position

        Returns:
            tuple: (predicted_x, predicted_y)
        """
        # Add to history
        self.position_history.append((x, y))

        # Need at least 2 positions to calculate velocity
        if len(self.position_history) < 2:
            self.last_prediction = (x, y)
            return x, y

        # Calculate current velocity
        prev_pos = self.position_history[-2]
        current_pos = self.position_history[-1]

        vx = current_pos[0] - prev_pos[0]
        vy = current_pos[1] - prev_pos[1]

        self.velocity_history.append((vx, vy))

        # Calculate acceleration if we have velocity history
        if len(self.velocity_history) >= 2:
            prev_vel = self.velocity_history[-2]
            current_vel = self.velocity_history[-1]

            ax = current_vel[0] - prev_vel[0]
            ay = current_vel[1] - prev_vel[1]

            self.acceleration_history.append((ax, ay))

        # Predict future position
        predicted_x, predicted_y = self._predict()

        self.last_prediction = (predicted_x, predicted_y)
        return predicted_x, predicted_y

    def predict(self):
        """
        Predict future position using the current history without adding new data.

        Returns:
            tuple: (predicted_x, predicted_y)
        """
        if len(self.position_history) == 0:
            return self.last_prediction

        predicted_x, predicted_y = self._predict()
        self.last_prediction = (predicted_x, predicted_y)
        return predicted_x, predicted_y

    def _predict(self):
        """
        Predict future position using kinematic equations

        Returns:
            tuple: (predicted_x, predicted_y)
        """
        if len(self.position_history) == 0:
            return 0, 0

        # Current position
        x, y = self.position_history[-1]

        # If we don't have enough history, just return current position
        if len(self.velocity_history) == 0:
            return x, y

        # Average velocity over recent history
        avg_vx = np.mean([v[0] for v in self.velocity_history])
        avg_vy = np.mean([v[1] for v in self.velocity_history])

        # Use constant velocity model by default
        pred_x = x + avg_vx * self.prediction_steps
        pred_y = y + avg_vy * self.prediction_steps

        # If we have acceleration data, use constant acceleration model
        if len(self.acceleration_history) > 0:
            avg_ax = np.mean([a[0] for a in self.acceleration_history])
            avg_ay = np.mean([a[1] for a in self.acceleration_history])

            # Kinematic equation: s = s0 + v*t + 0.5*a*t^2
            t = self.prediction_steps
            pred_x = x + avg_vx * t + 0.5 * avg_ax * t**2
            pred_y = y + avg_vy * t + 0.5 * avg_ay * t**2

        return pred_x, pred_y

    def get_velocity(self):
        """
        Get current velocity estimate

        Returns:
            tuple: (vx, vy) velocity components
        """
        if len(self.velocity_history) == 0:
            return 0, 0

        return self.velocity_history[-1]

    def get_speed(self):
        """
        Get current speed (velocity magnitude)

        Returns:
            float: Speed
        """
        vx, vy = self.get_velocity()
        return np.sqrt(vx**2 + vy**2)

    def is_moving(self, threshold=0.5):
        """
        Check if significant movement is detected

        Args:
            threshold: Minimum speed to consider as moving

        Returns:
            bool: True if moving
        """
        return self.get_speed() > threshold

    def get_movement_direction(self):
        """
        Get direction of movement in degrees

        Returns:
            float: Direction in degrees (0 = right, 90 = up, 180 = left, 270 = down)
        """
        vx, vy = self.get_velocity()

        if vx == 0 and vy == 0:
            return 0

        # Calculate angle in degrees
        angle = np.degrees(np.arctan2(-vy, vx))  # -vy because y-axis is inverted

        # Normalize to 0-360
        if angle < 0:
            angle += 360

        return angle

    def reset(self):
        """Reset predictor state"""
        self.position_history.clear()
        self.velocity_history.clear()
        self.acceleration_history.clear()
        self.last_prediction = (0, 0)


if __name__ == "__main__":
    # Test motion predictor
    print("Testing Motion Predictor")
    print("="*50)

    predictor = MotionPredictor(prediction_steps=3)

    # Simulate linear movement
    print("\n1. Testing linear movement...")
    for i in range(20):
        x = i * 2
        y = 50

        pred_x, pred_y = predictor.update(x, y)

        if i > 5:  # After some history
            print(f"   Position: ({x:5.1f}, {y:5.1f}) -> Predicted: ({pred_x:5.1f}, {pred_y:5.1f})")

    # Reset
    predictor.reset()

    # Simulate accelerating movement
    print("\n2. Testing accelerating movement...")
    for i in range(20):
        x = i**2 * 0.5  # Quadratic (accelerating)
        y = 50

        pred_x, pred_y = predictor.update(x, y)

        if i > 5:
            actual_next_x = (i + 3)**2 * 0.5  # Actual position 3 steps ahead
            error = abs(pred_x - actual_next_x)
            print(f"   Position: ({x:5.1f}, {y:5.1f}) -> Predicted: ({pred_x:5.1f}, {pred_y:5.1f}) Error: {error:5.1f}")

    # Reset
    predictor.reset()

    # Simulate circular movement
    print("\n3. Testing circular movement...")
    for i in range(30):
        angle = i * 0.2
        x = 50 + 30 * np.cos(angle)
        y = 50 + 30 * np.sin(angle)

        pred_x, pred_y = predictor.update(x, y)

        if i > 5:
            speed = predictor.get_speed()
            direction = predictor.get_movement_direction()
            print(f"   Speed: {speed:4.1f}, Direction: {direction:6.1f}°")

    print("\n" + "="*50)
    print("Test completed")
