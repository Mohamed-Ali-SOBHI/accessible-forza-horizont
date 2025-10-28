"""
Tremor Detection Module
Distinguishes between intentional movements and involuntary tremors
to enable adaptive filtering and improve control precision
"""

import numpy as np
from collections import deque
import time


class TremorDetector:
    def __init__(self, config=None):
        """
        Initialize tremor detector

        Args:
            config: Dictionary with detection parameters
        """
        if config is None:
            config = {}

        # Tremor characteristics
        self.tremor_frequency_range = config.get('tremor_frequency_range', (4, 12))  # Hz
        self.min_tremor_amplitude = config.get('min_tremor_amplitude', 2.0)  # pixels
        self.detection_window = config.get('detection_window', 1.0)  # seconds

        # Movement history
        self.position_history = deque(maxlen=100)
        self.timestamp_history = deque(maxlen=100)

        # Tremor state
        self.tremor_detected = False
        self.tremor_intensity = 0.0  # 0-1 scale
        self.tremor_frequency = 0.0  # Hz

        # Intentional movement detection
        self.large_movement_threshold = config.get('large_movement_threshold', 10.0)  # pixels
        self.last_large_movement_time = 0
        self.intention_confidence = 0.0  # 0-1, higher = more confident it's intentional

    def update(self, x, y):
        """
        Update tremor detection with new position

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            dict: Tremor analysis results
        """
        current_time = time.time()

        # Add to history
        self.position_history.append((x, y))
        self.timestamp_history.append(current_time)

        # Clean old data outside detection window
        self._clean_old_data(current_time)

        # Analyze movement
        analysis = self._analyze_movement()

        return analysis

    def _clean_old_data(self, current_time):
        """Remove data older than detection window"""
        while (len(self.timestamp_history) > 0 and
               current_time - self.timestamp_history[0] > self.detection_window):
            self.position_history.popleft()
            self.timestamp_history.popleft()

    def _analyze_movement(self):
        """
        Analyze movement patterns to detect tremor

        Returns:
            dict: Analysis results
        """
        if len(self.position_history) < 10:
            return {
                'tremor_detected': False,
                'tremor_intensity': 0.0,
                'tremor_frequency': 0.0,
                'intention_confidence': 1.0,
                'recommended_filter_strength': 0.0
            }

        # Convert to numpy arrays
        positions = np.array(list(self.position_history))
        timestamps = np.array(list(self.timestamp_history))

        # Calculate velocities
        velocities = self._calculate_velocities(positions, timestamps)

        # Detect large intentional movements
        self._detect_intentional_movement(positions, timestamps[-1])

        # Analyze frequency components
        dominant_frequency = self._estimate_dominant_frequency(positions, timestamps)

        # Calculate movement amplitude
        amplitude = self._calculate_amplitude(positions)

        # Determine if tremor is present
        is_tremor_frequency = (self.tremor_frequency_range[0] <= dominant_frequency <=
                              self.tremor_frequency_range[1])
        is_sufficient_amplitude = amplitude >= self.min_tremor_amplitude

        # Low intention confidence + tremor characteristics = tremor detected
        self.tremor_detected = (is_tremor_frequency and
                               is_sufficient_amplitude and
                               self.intention_confidence < 0.5)

        # Calculate tremor intensity (0-1)
        if self.tremor_detected:
            # Intensity based on amplitude and frequency deviation
            frequency_center = np.mean(self.tremor_frequency_range)
            frequency_deviation = abs(dominant_frequency - frequency_center)
            frequency_score = 1.0 - (frequency_deviation / frequency_center)

            amplitude_score = min(amplitude / 20.0, 1.0)  # Normalize to 0-1

            self.tremor_intensity = (frequency_score + amplitude_score) / 2.0
        else:
            self.tremor_intensity = 0.0

        self.tremor_frequency = dominant_frequency

        # Recommend filter strength based on tremor intensity
        # Higher tremor = stronger filtering needed
        recommended_filter_strength = self.tremor_intensity * 0.8  # Max 0.8

        return {
            'tremor_detected': self.tremor_detected,
            'tremor_intensity': self.tremor_intensity,
            'tremor_frequency': self.tremor_frequency,
            'intention_confidence': self.intention_confidence,
            'recommended_filter_strength': recommended_filter_strength,
            'amplitude': amplitude,
            'velocity_rms': np.sqrt(np.mean(velocities**2)) if len(velocities) > 0 else 0
        }

    def _calculate_velocities(self, positions, timestamps):
        """Calculate velocities from positions and timestamps"""
        if len(positions) < 2:
            return np.array([])

        # Calculate displacements
        displacements = np.diff(positions, axis=0)

        # Calculate time differences
        time_diffs = np.diff(timestamps)
        time_diffs = np.maximum(time_diffs, 0.001)  # Avoid division by zero

        # Calculate velocity magnitudes
        velocities = np.sqrt(np.sum(displacements**2, axis=1)) / time_diffs

        return velocities

    def _detect_intentional_movement(self, positions, current_time):
        """Detect large intentional movements"""
        if len(positions) < 5:
            self.intention_confidence = 0.5
            return

        # Calculate displacement over recent history
        recent_displacement = np.linalg.norm(positions[-1] - positions[-5])

        # Large displacement = likely intentional
        if recent_displacement > self.large_movement_threshold:
            self.last_large_movement_time = current_time
            self.intention_confidence = 1.0
        else:
            # Decay intention confidence over time
            time_since_large_movement = current_time - self.last_large_movement_time
            decay_rate = 0.5  # Seconds to halve confidence

            self.intention_confidence = 1.0 * np.exp(-time_since_large_movement / decay_rate)

            # Never go below 0.1
            self.intention_confidence = max(0.1, self.intention_confidence)

    def _estimate_dominant_frequency(self, positions, timestamps):
        """
        Estimate dominant frequency using zero-crossing method

        Returns:
            float: Dominant frequency in Hz
        """
        if len(positions) < 10:
            return 0.0

        # Use x-axis signal for frequency analysis
        signal = positions[:, 0]

        # Remove mean (detrend)
        signal = signal - np.mean(signal)

        # Count zero crossings
        zero_crossings = np.where(np.diff(np.sign(signal)))[0]

        if len(zero_crossings) < 2:
            return 0.0

        # Calculate average time between zero crossings
        crossing_times = timestamps[zero_crossings]
        avg_period = np.mean(np.diff(crossing_times)) * 2  # *2 because zero crossing is half period

        if avg_period == 0:
            return 0.0

        # Frequency = 1 / period
        frequency = 1.0 / avg_period

        return frequency

    def _calculate_amplitude(self, positions):
        """Calculate movement amplitude (peak-to-peak)"""
        if len(positions) < 2:
            return 0.0

        # Calculate range in both dimensions
        x_range = np.ptp(positions[:, 0])
        y_range = np.ptp(positions[:, 1])

        # Use maximum range
        amplitude = max(x_range, y_range)

        return amplitude

    def is_tremor_present(self):
        """
        Check if tremor is currently detected

        Returns:
            bool: True if tremor detected
        """
        return self.tremor_detected

    def get_tremor_intensity(self):
        """
        Get current tremor intensity

        Returns:
            float: Intensity (0-1)
        """
        return self.tremor_intensity

    def get_filter_recommendation(self):
        """
        Get recommended filter strength

        Returns:
            float: Filter strength (0-1, higher = more filtering)
        """
        if self.tremor_detected:
            return self.tremor_intensity * 0.8
        else:
            # Always apply minimal filtering
            return 0.2

    def reset(self):
        """Reset detector state"""
        self.position_history.clear()
        self.timestamp_history.clear()
        self.tremor_detected = False
        self.tremor_intensity = 0.0
        self.tremor_frequency = 0.0
        self.last_large_movement_time = 0
        self.intention_confidence = 0.0


if __name__ == "__main__":
    # Test tremor detector
    print("Testing Tremor Detector")
    print("="*50)

    detector = TremorDetector()

    # Simulate different movement patterns
    print("\n1. Testing intentional movement (no tremor)...")
    t = 0
    for i in range(50):
        x = i * 2  # Linear movement
        y = 50
        result = detector.update(x, y)
        t += 0.033  # ~30 FPS
        time.sleep(0.001)

    print(f"   Tremor detected: {result['tremor_detected']}")
    print(f"   Intention confidence: {result['intention_confidence']:.2f}")
    print(f"   Recommended filter: {result['recommended_filter_strength']:.2f}")

    # Reset
    detector.reset()
    time.sleep(0.1)

    print("\n2. Testing tremor-like movement (8 Hz oscillation)...")
    t = 0
    for i in range(100):
        x = 50 + 5 * np.sin(2 * np.pi * 8 * t)  # 8 Hz tremor
        y = 50 + 5 * np.cos(2 * np.pi * 8 * t)
        result = detector.update(x, y)
        t += 0.033
        time.sleep(0.001)

    print(f"   Tremor detected: {result['tremor_detected']}")
    print(f"   Tremor intensity: {result['tremor_intensity']:.2f}")
    print(f"   Tremor frequency: {result['tremor_frequency']:.1f} Hz")
    print(f"   Intention confidence: {result['intention_confidence']:.2f}")
    print(f"   Recommended filter: {result['recommended_filter_strength']:.2f}")

    # Reset
    detector.reset()
    time.sleep(0.1)

    print("\n3. Testing mixed movement (intentional + tremor)...")
    t = 0
    for i in range(100):
        # Intentional movement + tremor overlay
        x = i * 0.5 + 3 * np.sin(2 * np.pi * 6 * t)
        y = 50 + 3 * np.cos(2 * np.pi * 6 * t)
        result = detector.update(x, y)
        t += 0.033
        time.sleep(0.001)

    print(f"   Tremor detected: {result['tremor_detected']}")
    print(f"   Tremor intensity: {result['tremor_intensity']:.2f}")
    print(f"   Intention confidence: {result['intention_confidence']:.2f}")
    print(f"   Recommended filter: {result['recommended_filter_strength']:.2f}")

    print("\n" + "="*50)
    print("Test completed")
