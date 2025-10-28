"""
Fatigue Monitoring Module
Detects signs of user fatigue and suggests breaks or adjusts assistance
"""

import time
import numpy as np
from collections import deque


class FatigueMonitor:
    def __init__(self):
        """Initialize fatigue monitor"""
        # Session tracking
        self.session_start_time = time.time()
        self.total_active_time = 0
        self.last_update_time = time.time()

        # Performance metrics
        self.input_precision_history = deque(maxlen=100)
        self.correction_frequency_history = deque(maxlen=50)
        self.response_time_history = deque(maxlen=30)

        # Fatigue indicators
        self.fatigue_score = 0.0  # 0-1, higher = more fatigued
        self.fatigue_level = "None"  # None, Low, Medium, High

        # Thresholds
        self.max_continuous_time = 15 * 60  # 15 minutes
        self.break_recommendation_time = 10 * 60  # 10 minutes

        # Last break time
        self.last_break_time = time.time()

    def update(self, is_paused=False, input_variance=0.0, correction_count=0):
        """
        Update fatigue monitoring

        Args:
            is_paused: Whether system is currently paused
            input_variance: Variance in user inputs (higher = less precise)
            correction_count: Number of corrections in recent window

        Returns:
            dict: Fatigue analysis
        """
        current_time = time.time()

        # Update active time
        if not is_paused:
            self.total_active_time += (current_time - self.last_update_time)

        self.last_update_time = current_time

        # Track metrics
        self.input_precision_history.append(input_variance)
        self.correction_frequency_history.append(correction_count)

        # Calculate fatigue score
        self._calculate_fatigue_score()

        # Determine fatigue level
        self._determine_fatigue_level()

        # Check if break recommended
        time_since_break = current_time - self.last_break_time
        recommend_break = time_since_break > self.break_recommendation_time or self.fatigue_level in ["High"]

        # Calculate remaining time before mandatory break
        time_until_break = max(0, self.break_recommendation_time - time_since_break)

        return {
            'fatigue_score': self.fatigue_score,
            'fatigue_level': self.fatigue_level,
            'recommend_break': recommend_break,
            'session_duration': current_time - self.session_start_time,
            'active_time': self.total_active_time,
            'time_since_break': time_since_break,
            'time_until_break': time_until_break,
            'suggested_assistance_increase': self._get_assistance_suggestion()
        }

    def _calculate_fatigue_score(self):
        """Calculate overall fatigue score from various metrics"""
        scores = []

        # Time-based fatigue
        time_active = self.total_active_time
        time_score = min(1.0, time_active / self.max_continuous_time)
        scores.append(time_score * 0.4)  # 40% weight

        # Precision degradation
        if len(self.input_precision_history) > 20:
            recent_precision = np.mean(list(self.input_precision_history)[-20:])
            early_precision = np.mean(list(self.input_precision_history)[:20])

            if early_precision > 0:
                precision_degradation = (recent_precision - early_precision) / early_precision
                precision_score = max(0, min(1.0, precision_degradation))
                scores.append(precision_score * 0.3)  # 30% weight

        # Correction frequency increase
        if len(self.correction_frequency_history) > 10:
            recent_corrections = np.mean(list(self.correction_frequency_history)[-10:])
            early_corrections = np.mean(list(self.correction_frequency_history)[:10])

            if early_corrections > 0:
                correction_increase = (recent_corrections - early_corrections) / max(early_corrections, 1)
                correction_score = max(0, min(1.0, correction_increase / 2))  # Normalize
                scores.append(correction_score * 0.3)  # 30% weight

        # Calculate weighted average
        if scores:
            self.fatigue_score = np.mean(scores)
        else:
            self.fatigue_score = 0.0

    def _determine_fatigue_level(self):
        """Determine fatigue level from score"""
        if self.fatigue_score < 0.25:
            self.fatigue_level = "None"
        elif self.fatigue_score < 0.5:
            self.fatigue_level = "Low"
        elif self.fatigue_score < 0.75:
            self.fatigue_level = "Medium"
        else:
            self.fatigue_level = "High"

    def _get_assistance_suggestion(self):
        """
        Suggest assistance level increase based on fatigue

        Returns:
            int: Suggested assistance increase (0-2)
        """
        if self.fatigue_level == "None":
            return 0
        elif self.fatigue_level == "Low":
            return 0
        elif self.fatigue_level == "Medium":
            return 1
        else:  # High
            return 2

    def mark_break_taken(self):
        """Mark that user has taken a break"""
        self.last_break_time = time.time()
        print("✓ Break marked - Fatigue monitoring reset")

        # Partially reset fatigue score
        self.fatigue_score *= 0.5  # Reduce by half

    def get_session_stats(self):
        """
        Get session statistics

        Returns:
            dict: Session statistics
        """
        current_time = time.time()
        session_duration = current_time - self.session_start_time

        return {
            'session_duration_minutes': session_duration / 60,
            'active_time_minutes': self.total_active_time / 60,
            'break_time_minutes': (session_duration - self.total_active_time) / 60,
            'fatigue_score': self.fatigue_score,
            'fatigue_level': self.fatigue_level,
            'average_input_precision': np.mean(self.input_precision_history) if self.input_precision_history else 0,
            'average_corrections': np.mean(self.correction_frequency_history) if self.correction_frequency_history else 0
        }

    def should_suggest_break(self):
        """
        Check if break should be suggested

        Returns:
            bool: True if break recommended
        """
        time_since_break = time.time() - self.last_break_time
        return (time_since_break > self.break_recommendation_time or
                self.fatigue_level == "High")

    def reset(self):
        """Reset monitor for new session"""
        self.session_start_time = time.time()
        self.total_active_time = 0
        self.last_update_time = time.time()
        self.last_break_time = time.time()

        self.input_precision_history.clear()
        self.correction_frequency_history.clear()
        self.response_time_history.clear()

        self.fatigue_score = 0.0
        self.fatigue_level = "None"


if __name__ == "__main__":
    # Test fatigue monitor
    print("Testing Fatigue Monitor")
    print("="*50)

    monitor = FatigueMonitor()

    # Simulate session with increasing fatigue
    print("\nSimulating 15-minute session with gradual fatigue...")

    for minute in range(15):
        # Simulate degrading performance
        input_variance = 1.0 + (minute * 0.3)  # Increasing variance
        corrections = 2 + (minute * 0.5)  # Increasing corrections

        # Update every "minute" (simulated)
        for _ in range(6):  # Simulate 10-second updates
            result = monitor.update(
                is_paused=False,
                input_variance=input_variance,
                correction_count=corrections
            )
            monitor.total_active_time += 10  # Simulate 10 seconds

        # Print status every 3 minutes
        if (minute + 1) % 3 == 0:
            print(f"\nAfter {minute + 1} minutes:")
            print(f"  Fatigue Level: {result['fatigue_level']}")
            print(f"  Fatigue Score: {result['fatigue_score']:.2f}")
            print(f"  Recommend Break: {result['recommend_break']}")
            print(f"  Suggested Assistance Increase: +{result['suggested_assistance_increase']}")

    # Print final stats
    print("\n" + "="*50)
    print("Final Session Statistics:")
    stats = monitor.get_session_stats()
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.2f}")
        else:
            print(f"  {key}: {value}")

    print("\n" + "="*50)
    print("Test completed")
