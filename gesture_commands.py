"""
Gesture Commands Module
Maps facial gestures to driving commands with configurable bindings
"""

import pyautogui
import time
from collections import deque


class GestureCommandMapper:
    def __init__(self, config=None):
        """
        Initialize gesture command mapper

        Args:
            config: Dictionary with gesture mappings and settings
        """
        # Default gesture to command mappings
        self.default_mappings = {
            'left_blink': 'turn_signal_left',
            'right_blink': 'turn_signal_right',
            'mouth_open': 'emergency_brake',
            'eyebrow_raise': 'horn',
            'smile': 'confirm_calibration',
            'both_blink': 'toggle_pause'
        }

        # Default key bindings for commands
        self.default_key_bindings = {
            'turn_signal_left': None,  # No default key - visual only
            'turn_signal_right': None,  # No default key - visual only
            'emergency_brake': 's',     # Brake key
            'horn': 'h',               # Horn key
            'confirm_calibration': None,  # Special command
            'toggle_pause': None       # Special command - handled by app
        }

        # Load configuration
        if config:
            self.gesture_mappings = config.get('gesture_mappings', self.default_mappings)
            self.key_bindings = config.get('key_bindings', self.default_key_bindings)
            self.enabled = config.get('enabled', True)
            self.hold_duration = config.get('hold_duration', 0.1)  # How long to hold keys
        else:
            self.gesture_mappings = self.default_mappings
            self.key_bindings = self.default_key_bindings
            self.enabled = True
            self.hold_duration = 0.1

        # State tracking
        self.active_commands = set()
        self.command_start_times = {}
        self.last_command_trigger = {}

        # Visual indicators state
        self.turn_signal_left_active = False
        self.turn_signal_right_active = False
        self.turn_signal_toggle_time = 0
        self.turn_signal_duration = 3.0  # Seconds to keep signal active

        # Cooldown between same command triggers
        self.command_cooldown = 1.0  # Seconds

        # Command history for analysis
        self.command_history = deque(maxlen=100)

    def process_gestures(self, gestures):
        """
        Process detected gestures and trigger corresponding commands

        Args:
            gestures: Dictionary of gesture states from FacialGestureDetector

        Returns:
            dict: Active commands and their states
        """
        if not self.enabled:
            return {}

        active_commands = {}
        current_time = time.time()

        for gesture_name, is_active in gestures.items():
            if not is_active:
                continue

            # Get command for this gesture
            command = self.gesture_mappings.get(gesture_name)
            if not command:
                continue

            # Check cooldown
            last_trigger = self.last_command_trigger.get(command, 0)
            if current_time - last_trigger < self.command_cooldown:
                continue

            # Execute command
            success = self._execute_command(command, current_time)
            if success:
                active_commands[command] = True
                self.last_command_trigger[command] = current_time
                self.command_history.append({
                    'time': current_time,
                    'gesture': gesture_name,
                    'command': command
                })

        # Update turn signals (they auto-expire)
        self._update_turn_signals(current_time)

        # Add turn signal states to active commands
        if self.turn_signal_left_active:
            active_commands['turn_signal_left'] = True
        if self.turn_signal_right_active:
            active_commands['turn_signal_right'] = True

        return active_commands

    def _execute_command(self, command, current_time):
        """
        Execute a specific command

        Args:
            command: Command name to execute
            current_time: Current timestamp

        Returns:
            bool: True if command was executed successfully
        """
        # Handle special commands
        if command == 'turn_signal_left':
            self.turn_signal_left_active = True
            self.turn_signal_toggle_time = current_time
            print("🡐 Turn signal LEFT activated")
            return True

        elif command == 'turn_signal_right':
            self.turn_signal_right_active = True
            self.turn_signal_toggle_time = current_time
            print("🡒 Turn signal RIGHT activated")
            return True

        elif command == 'confirm_calibration':
            print("✓ Calibration confirmed via smile")
            # This is handled by the main application
            return True

        elif command == 'toggle_pause':
            print("⏸ Pause toggled via both eyes blink")
            # This is handled by the main application
            return True

        # Handle keyboard commands
        key = self.key_bindings.get(command)
        if key:
            try:
                # Press and hold key briefly
                pyautogui.keyDown(key)
                time.sleep(self.hold_duration)
                pyautogui.keyUp(key)
                print(f"⌨ Command '{command}' -> Key '{key}' pressed")
                return True
            except Exception as e:
                print(f"Error executing command '{command}': {e}")
                return False

        return False

    def _update_turn_signals(self, current_time):
        """Update turn signal states (auto-expire after duration)"""
        if self.turn_signal_left_active:
            if current_time - self.turn_signal_toggle_time > self.turn_signal_duration:
                self.turn_signal_left_active = False
                print("Turn signal LEFT deactivated")

        if self.turn_signal_right_active:
            if current_time - self.turn_signal_toggle_time > self.turn_signal_duration:
                self.turn_signal_right_active = False
                print("Turn signal RIGHT deactivated")

    def cancel_turn_signals(self):
        """Manually cancel all turn signals"""
        self.turn_signal_left_active = False
        self.turn_signal_right_active = False

    def set_gesture_mapping(self, gesture, command):
        """
        Set custom gesture to command mapping

        Args:
            gesture: Gesture name (e.g., 'left_blink')
            command: Command name (e.g., 'turn_signal_left')
        """
        self.gesture_mappings[gesture] = command
        print(f"Gesture '{gesture}' mapped to command '{command}'")

    def set_key_binding(self, command, key):
        """
        Set custom key binding for command

        Args:
            command: Command name
            key: Key to bind (pyautogui compatible)
        """
        self.key_bindings[command] = key
        print(f"Command '{command}' bound to key '{key}'")

    def enable(self):
        """Enable gesture command processing"""
        self.enabled = True
        print("Gesture commands ENABLED")

    def disable(self):
        """Disable gesture command processing"""
        self.enabled = False
        self.cancel_turn_signals()
        print("Gesture commands DISABLED")

    def get_command_stats(self):
        """
        Get statistics about command usage

        Returns:
            dict: Statistics about command usage
        """
        if len(self.command_history) == 0:
            return {}

        stats = {}
        for entry in self.command_history:
            cmd = entry['command']
            stats[cmd] = stats.get(cmd, 0) + 1

        return stats

    def draw_indicators(self, frame):
        """
        Draw visual indicators for active gesture commands

        Args:
            frame: Image to draw on

        Returns:
            frame: Modified image with indicators
        """
        import cv2
        h, w = frame.shape[:2]

        # Draw turn signal indicators
        if self.turn_signal_left_active:
            # Left arrow
            points = np.array([
                [50, h // 2],
                [100, h // 2 - 30],
                [100, h // 2 + 30]
            ], np.int32)
            cv2.fillPoly(frame, [points], (0, 255, 0))
            cv2.putText(frame, "LEFT", (110, h // 2 + 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        if self.turn_signal_right_active:
            # Right arrow
            points = np.array([
                [w - 50, h // 2],
                [w - 100, h // 2 - 30],
                [w - 100, h // 2 + 30]
            ], np.int32)
            cv2.fillPoly(frame, [points], (0, 255, 0))
            cv2.putText(frame, "RIGHT", (w - 210, h // 2 + 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        return frame

    def get_config(self):
        """
        Get current configuration

        Returns:
            dict: Current configuration
        """
        return {
            'gesture_mappings': self.gesture_mappings,
            'key_bindings': self.key_bindings,
            'enabled': self.enabled,
            'hold_duration': self.hold_duration,
            'turn_signal_duration': self.turn_signal_duration,
            'command_cooldown': self.command_cooldown
        }

    def update_config(self, config):
        """
        Update configuration

        Args:
            config: Dictionary with configuration updates
        """
        if 'gesture_mappings' in config:
            self.gesture_mappings.update(config['gesture_mappings'])

        if 'key_bindings' in config:
            self.key_bindings.update(config['key_bindings'])

        if 'enabled' in config:
            self.enabled = config['enabled']

        if 'hold_duration' in config:
            self.hold_duration = config['hold_duration']

        if 'turn_signal_duration' in config:
            self.turn_signal_duration = config['turn_signal_duration']

        if 'command_cooldown' in config:
            self.command_cooldown = config['command_cooldown']


# Import numpy for drawing
import numpy as np


if __name__ == "__main__":
    # Test gesture command mapper
    print("Testing Gesture Command Mapper")
    print("="*50)

    # Create mapper with default config
    mapper = GestureCommandMapper()

    # Show current mappings
    print("\nDefault Gesture Mappings:")
    for gesture, command in mapper.gesture_mappings.items():
        key = mapper.key_bindings.get(command, 'None')
        print(f"  {gesture:20s} -> {command:20s} (key: {key})")

    # Simulate some gestures
    print("\nSimulating gestures...")

    test_gestures = {
        'left_blink': True,
        'right_blink': False,
        'mouth_open': False,
        'eyebrow_raise': False,
        'smile': False,
        'both_blink': False
    }

    print("\nGesture: Left blink")
    active_commands = mapper.process_gestures(test_gestures)
    print(f"Active commands: {active_commands}")

    time.sleep(1)

    test_gestures['left_blink'] = False
    test_gestures['mouth_open'] = True

    print("\nGesture: Mouth open")
    active_commands = mapper.process_gestures(test_gestures)
    print(f"Active commands: {active_commands}")

    # Show stats
    print("\nCommand statistics:")
    stats = mapper.get_command_stats()
    for cmd, count in stats.items():
        print(f"  {cmd}: {count} times")

    print("\nTest completed")
