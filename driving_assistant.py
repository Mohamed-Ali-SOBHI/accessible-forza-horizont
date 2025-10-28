"""
Driving Assistant Module
Provides intelligent assistance for easier control with limited mobility:
- Trajectory smoothing
- Input stabilization
- Multiple assistance levels
"""

import numpy as np
from collections import deque


class DrivingAssistant:
    def __init__(self, assistance_level=2):
        """
        Initialize driving assistant

        Args:
            assistance_level: 0 = Off, 1 = Minimal, 2 = Medium, 3 = Maximum
        """
        self.assistance_level = assistance_level

        # Trajectory smoothing
        self.trajectory_history = deque(maxlen=10)

        # Input stabilization
        self.stable_direction = 'center'
        self.stable_throttle = 'neutral'
        self.direction_change_threshold = 3  # Consecutive frames to change direction
        self.direction_counter = {'left': 0, 'right': 0, 'center': 0}
        self.throttle_counter = {'forward': 0, 'backward': 0, 'neutral': 0}

        # Auto-centering (for max assistance)
        self.auto_center_enabled = False
        self.center_pull_strength = 0.2  # How strongly to pull toward center

    def set_assistance_level(self, level):
        """
        Set assistance level

        Args:
            level: 0-3 (0=Off, 1=Minimal, 2=Medium, 3=Maximum)
        """
        self.assistance_level = max(0, min(3, level))

        # Configure based on level
        if level == 0:
            # No assistance
            self.auto_center_enabled = False
            self.direction_change_threshold = 1
        elif level == 1:
            # Minimal - just basic smoothing
            self.auto_center_enabled = False
            self.direction_change_threshold = 2
        elif level == 2:
            # Medium - smoothing + stabilization
            self.auto_center_enabled = False
            self.direction_change_threshold = 3
        elif level == 3:
            # Maximum - all features
            self.auto_center_enabled = True
            self.direction_change_threshold = 4

    def process_steering(self, yaw_angle, sensitivity=15):
        """
        Process steering input with assistance

        Args:
            yaw_angle: Head yaw angle in degrees
            sensitivity: Angle threshold for steering

        Returns:
            str: 'left', 'right', or 'center'
        """
        if self.assistance_level == 0:
            # No assistance - direct mapping
            if yaw_angle < -sensitivity:
                return 'left'
            elif yaw_angle > sensitivity:
                return 'right'
            else:
                return 'center'

        # Determine raw direction
        if yaw_angle < -sensitivity:
            raw_direction = 'left'
        elif yaw_angle > sensitivity:
            raw_direction = 'right'
        else:
            raw_direction = 'center'

        # Apply stabilization (debouncing)
        stable_direction = self._stabilize_direction(raw_direction)

        # Apply auto-centering if enabled
        if self.auto_center_enabled and stable_direction == 'center':
            # Gently pull toward center
            self.trajectory_history.append(0)
        else:
            value = -1 if stable_direction == 'left' else (1 if stable_direction == 'right' else 0)
            self.trajectory_history.append(value)

        return stable_direction

    def process_throttle(self, pitch_angle, forward_threshold=-10, backward_threshold=10):
        """
        Process throttle input with assistance

        Args:
            pitch_angle: Head pitch angle in degrees
            forward_threshold: Angle for forward acceleration
            backward_threshold: Angle for braking

        Returns:
            str: 'forward', 'backward', or 'neutral'
        """
        if self.assistance_level == 0:
            # No assistance - direct mapping
            if pitch_angle < forward_threshold:
                return 'forward'
            elif pitch_angle > backward_threshold:
                return 'backward'
            else:
                return 'neutral'

        # Determine raw throttle
        if pitch_angle < forward_threshold:
            raw_throttle = 'forward'
        elif pitch_angle > backward_threshold:
            raw_throttle = 'backward'
        else:
            raw_throttle = 'neutral'

        # Apply stabilization
        stable_throttle = self._stabilize_throttle(raw_throttle)

        return stable_throttle

    def _stabilize_direction(self, raw_direction):
        """
        Stabilize direction input to prevent rapid oscillation

        Args:
            raw_direction: Raw direction input

        Returns:
            str: Stabilized direction
        """
        # Increment counter for raw direction
        self.direction_counter[raw_direction] += 1

        # Decrement counters for other directions
        for direction in self.direction_counter:
            if direction != raw_direction:
                self.direction_counter[direction] = max(0, self.direction_counter[direction] - 1)

        # Change stable direction only if threshold met
        for direction, count in self.direction_counter.items():
            if count >= self.direction_change_threshold:
                self.stable_direction = direction
                break

        return self.stable_direction

    def _stabilize_throttle(self, raw_throttle):
        """Stabilize throttle input similar to direction"""
        self.throttle_counter[raw_throttle] += 1

        for throttle in self.throttle_counter:
            if throttle != raw_throttle:
                self.throttle_counter[throttle] = max(0, self.throttle_counter[throttle] - 1)

        for throttle, count in self.throttle_counter.items():
            if count >= self.direction_change_threshold:
                self.stable_throttle = throttle
                break

        return self.stable_throttle

    def get_smoothed_trajectory(self):
        """
        Get smoothed trajectory value

        Returns:
            float: Smoothed value (-1 to 1, negative = left, positive = right)
        """
        if len(self.trajectory_history) == 0:
            return 0

        # Apply weighted average (more recent = higher weight)
        weights = np.exp(np.linspace(-1, 0, len(self.trajectory_history)))
        weights /= weights.sum()

        smoothed = np.average(list(self.trajectory_history), weights=weights)

        return smoothed

    def get_assistance_description(self):
        """
        Get description of current assistance level

        Returns:
            str: Description
        """
        descriptions = {
            0: "Aucune assistance - Contrôle direct",
            1: "Assistance minimale - Lissage basique",
            2: "Assistance moyenne - Stabilisation des inputs",
            3: "Assistance maximale - Auto-centrage activé"
        }
        return descriptions.get(self.assistance_level, "Inconnu")

    def reset(self):
        """Reset assistant state"""
        self.trajectory_history.clear()
        self.stable_direction = 'center'
        self.stable_throttle = 'neutral'
        self.direction_counter = {'left': 0, 'right': 0, 'center': 0}
        self.throttle_counter = {'forward': 0, 'backward': 0, 'neutral': 0}


if __name__ == "__main__":
    # Test driving assistant
    print("Testing Driving Assistant")
    print("="*50)

    # Test different assistance levels
    for level in range(4):
        print(f"\nTesting Assistance Level {level}:")
        assistant = DrivingAssistant(assistance_level=level)
        print(f"  {assistant.get_assistance_description()}")

        # Simulate noisy steering input
        print("  Simulating oscillating input...")
        inputs = [20, -15, 18, -12, 20, 22, 20]  # Oscillating around threshold
        for yaw in inputs:
            direction = assistant.process_steering(yaw, sensitivity=15)

        print(f"  Final stable direction: {direction}")

    print("\n" + "="*50)
    print("Test completed")
