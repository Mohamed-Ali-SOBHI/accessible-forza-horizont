import pyautogui
import math
import time
import csv
from typing import Tuple, List

# Disable the fail-safe (use with caution)
pyautogui.FAILSAFE = False

# Sensitivity configuration for mouse movements
sensitivity: int = 100  # Adjust this value to control sensitivity
adaptive_sensitivity: bool = True  # Enable or disable adaptive sensitivity

# Get screen size
screen_width, screen_height = pyautogui.size()

# Directional keys
KEY_FORWARD: str = 'z'
KEY_BACKWARD: str = 's'
KEY_LEFT: str = 'q'
KEY_RIGHT: str = 'd'

# Smoothing parameters
smoothing_factor: float = 0.2  # Adjust this for smoother transitions
deceleration_factor: float = 0.05  # Factor for deceleration
ema_alpha: float = 0.1  # Exponential moving average factor

# Kalman filter parameters
kalman_R: float = 1.0  # Process noise covariance
kalman_Q: float = 1.0  # Measurement noise covariance
kalman_A: float = 1.0  # State transition coefficient
kalman_B: float = 0.0  # Control input coefficient
kalman_H: float = 1.0  # Measurement coefficient

# Kalman filter state variables
kalman_x: float = 0.0  # State estimate
kalman_P: float = 1.0  # Estimate covariance

# Exponential moving average for smoothing
ema_dx: float = 0.0
ema_dy: float = 0.0

# Last pressed keys
last_horizontal_key: str = ""
last_vertical_key: str = ""

# Centering mouse for calibration
center_x, center_y = screen_width // 2, screen_height // 2

# Variables to detect erratic movements
movement_history: List[Tuple[float, float]] = []
erratic_threshold: int = 5  # Number of rapid direction changes to detect erratic movement
cooldown_time: float = 1.0  # Time to stabilize after detecting erratic movement
last_erratic_time: float = 0.0  # Initialize last erratic time

# Dead zone parameters
dead_zone_radius: int = 10

# Data logging
log_file = 'driving_data.csv'
fields = ['timestamp', 'dx', 'dy', 'avg_dx', 'avg_dy', 'norm_dx', 'norm_dy', 'horizontal_key', 'vertical_key']

def center_mouse() -> None:
    """Center the mouse cursor on the screen."""
    pyautogui.moveTo(center_x, center_y)

def get_mouse_displacement() -> Tuple[int, int]:
    """Calculate the displacement of the mouse from the center."""
    x, y = pyautogui.position()
    dx = x - center_x
    dy = y - center_y
    return dx, dy

def normalize_vector(dx: int, dy: int) -> Tuple[float, float]:
    """Normalize the displacement vector."""
    magnitude = math.sqrt(dx ** 2 + dy ** 2)
    if magnitude == 0:
        return 0.0, 0.0
    return dx / magnitude, dy / magnitude

def apply_ema(new_dx: int, new_dy: int) -> Tuple[float, float]:
    """Apply exponential moving average to smooth mouse displacement."""
    global ema_dx, ema_dy

    ema_dx = ema_alpha * new_dx + (1 - ema_alpha) * ema_dx
    ema_dy = ema_alpha * new_dy + (1 - ema_alpha) * ema_dy

    return ema_dx, ema_dy

def kalman_filter(measurement: float) -> float:
    """Apply Kalman filter to the measurement."""
    global kalman_x, kalman_P

    # Prediction update
    kalman_x = kalman_A * kalman_x + kalman_B
    kalman_P = kalman_A * kalman_P * kalman_A + kalman_R

    # Measurement update
    K = kalman_P * kalman_H / (kalman_H * kalman_P * kalman_H + kalman_Q)
    kalman_x = kalman_x + K * (measurement - kalman_H * kalman_x)
    kalman_P = (1 - K * kalman_H) * kalman_P

    return kalman_x

def adaptive_sensitivity_adjustment(dx: int, dy: int) -> float:
    """Adjust sensitivity based on the speed of the mouse movement."""
    speed = math.sqrt(dx**2 + dy**2)
    return min(1.0, speed / sensitivity)

def handle_horizontal_movement(norm_dx: float) -> None:
    """Handle horizontal movement based on normalized mouse displacement."""
    global last_horizontal_key

    if abs(norm_dx) > 0.5:  # Adjust threshold for sensitivity
        if norm_dx > 0:
            if last_horizontal_key != KEY_RIGHT:
                pyautogui.keyUp(KEY_LEFT)
                pyautogui.keyDown(KEY_RIGHT)
                last_horizontal_key = KEY_RIGHT
        else:
            if last_horizontal_key != KEY_LEFT:
                pyautogui.keyUp(KEY_RIGHT)
                pyautogui.keyDown(KEY_LEFT)
                last_horizontal_key = KEY_LEFT
    else:
        if last_horizontal_key:
            pyautogui.keyUp(last_horizontal_key)
            last_horizontal_key = ""

def handle_vertical_movement(norm_dy: float) -> None:
    """Handle vertical movement based on normalized mouse displacement."""
    global last_vertical_key

    if abs(norm_dy) > 0.5:  # Adjust threshold for sensitivity
        if norm_dy > 0:
            if last_vertical_key != KEY_BACKWARD:
                pyautogui.keyUp(KEY_FORWARD)
                pyautogui.keyDown(KEY_BACKWARD)
                last_vertical_key = KEY_BACKWARD
        else:
            if last_vertical_key != KEY_FORWARD:
                pyautogui.keyUp(KEY_BACKWARD)
                pyautogui.keyDown(KEY_FORWARD)
                last_vertical_key = KEY_FORWARD
    else:
        if last_vertical_key:
            pyautogui.keyUp(last_vertical_key)
            last_vertical_key = ""

def detect_erratic_movements() -> bool:
    """Detect rapid direction changes that indicate erratic movement."""
    global movement_history

    if len(movement_history) < erratic_threshold:
        return False

    changes = 0
    for i in range(1, len(movement_history)):
        if (movement_history[i][0] * movement_history[i-1][0] < 0 or
            movement_history[i][1] * movement_history[i-1][1] < 0):
            changes += 1

    return changes >= erratic_threshold

def stabilize_movements() -> None:
    """Stabilize movements by releasing all keys."""
    global last_horizontal_key, last_vertical_key
    if last_horizontal_key:
        pyautogui.keyUp(last_horizontal_key)
        last_horizontal_key = ""
    if last_vertical_key:
        pyautogui.keyUp(last_vertical_key)
        last_vertical_key = ""

def log_data(timestamp: float, dx: int, dy: int, avg_dx: float, avg_dy: float, norm_dx: float, norm_dy: float, horizontal_key: str, vertical_key: str) -> None:
    """Log the data to a CSV file."""
    with open(log_file, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([timestamp, dx, dy, avg_dx, avg_dy, norm_dx, norm_dy, horizontal_key, vertical_key])

def follow_mouse() -> None:
    """Convert mouse movements into directional key presses."""
    global last_erratic_time

    # Initialize log file
    with open(log_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(fields)

    center_mouse()
    last_erratic_time = time.time()

    while True:
        current_time = time.time()
        dx, dy = get_mouse_displacement()
        
        # Apply dead zone
        if math.sqrt(dx**2 + dy**2) < dead_zone_radius:
            dx, dy = 0, 0

        # Adaptive sensitivity adjustment
        if adaptive_sensitivity:
            adapt_factor = adaptive_sensitivity_adjustment(dx, dy)
            dx, dy = dx * adapt_factor, dy * adapt_factor

        # Apply Kalman filter
        dx = kalman_filter(dx)
        dy = kalman_filter(dy)

        avg_dx, avg_dy = apply_ema(dx, dy)
        norm_dx, norm_dy = normalize_vector(int(avg_dx), int(avg_dy))

        movement_history.append((norm_dx, norm_dy))
        if len(movement_history) > erratic_threshold:
            movement_history.pop(0)

        if detect_erratic_movements():
            stabilize_movements()
            last_erratic_time = current_time

        if current_time - last_erratic_time > cooldown_time:
            handle_horizontal_movement(norm_dx)
            handle_vertical_movement(norm_dy)

        # Log data

# Start the mouse tracking function
if __name__ == "__main__":
    print("Script started. Move the mouse to control the game. Press Ctrl+C to stop.")
    try:
        follow_mouse()
    except KeyboardInterrupt:
        print("Script stopped.")
