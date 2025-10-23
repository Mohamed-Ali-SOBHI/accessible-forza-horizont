# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an accessible driving control system for Forza Horizon (or similar racing games) that allows users to control the game using alternative input methods. The project provides two control modes:

1. **Head/Face-controlled driving** - Uses webcam and facial detection to control the car based on head movements
2. **Mouse-controlled driving** - Uses mouse displacement from screen center to simulate keyboard inputs

Both systems translate physical movements into keyboard inputs (ZQSD/WASD keys) to control the game.

### New: Enhanced Accessible Version

The **accessible_face_drive.py** provides a significantly improved version with:
- Personalized calibration system
- Configurable dead zones
- Advanced smoothing (Kalman + EMA filters)
- Multiple control modes (position, velocity, simplified)
- Real-time visual feedback UI
- Auto-pause safety features
- Session logging and analysis
- Persistent configuration

## Architecture

### Core Components

The codebase follows a modular architecture with separated concerns:

- **[camera_handler.py](camera_handler.py)** - `CameraHandler` class that manages webcam access, handles camera detection (scans indices 0-10), and provides frame capture functionality
- **[face_detector.py](face_detector.py)** - `FaceDetector` class that wraps MediaPipe face detection, processes frames to detect face position/bounding boxes, and returns normalized face coordinates
- **[face drive.py](face drive.py)** - `HeadControlledDriving` basic application (legacy version)
- **[accessible_face_drive.py](accessible_face_drive.py)** - **RECOMMENDED** Enhanced accessible version with calibration, multiple control modes, advanced smoothing, visual feedback UI, and comprehensive accessibility features
- **[mouse drive.py](mouse drive.py)** - Standalone mouse-based control system with sophisticated filtering (Kalman filter, EMA smoothing, dead zones, erratic movement detection)
- **[config.json](config.json)** - Configuration file for accessible_face_drive.py with all adjustable parameters

### Control Flow

**Face-controlled mode:**
1. CameraHandler acquires video frames
2. FaceDetector processes frames to find face bounding box
3. HeadControlledDriving tracks face position changes (dx, dy)
4. Movement deltas exceeding threshold trigger pyautogui key presses/releases

**Mouse-controlled mode:**
1. Mouse displacement from screen center is continuously measured
2. Multiple filters applied: dead zone check, adaptive sensitivity, Kalman filtering, EMA smoothing
3. Erratic movement detection prevents jittery inputs
4. Normalized displacement vectors control directional keys

### Key Configuration

Both systems use ZQSD keys (French AZERTY layout equivalent to WASD):
- Z = Forward
- S = Backward
- Q = Left
- D = Right

## Running the Application

### Accessible Face-controlled driving (RECOMMENDED):
```bash
python accessible_face_drive.py
```
- **First use**: 3-second calibration to learn your neutral head position
- **Controls during use**:
  - `C` - Recalibrate
  - `P` - Pause/Resume
  - `M` - Cycle through control modes (position/velocity/simplified)
  - `+/-` - Adjust sensitivity
  - `Q` - Quit
- Displays comprehensive UI with visual feedback
- Auto-pauses if face not detected for 3 seconds
- All settings saved to config.json
- Session data logged to driving_sessions.csv

See [GUIDE_UTILISATION.md](GUIDE_UTILISATION.md) for detailed French user guide.

### Basic Face-controlled driving (legacy):
```bash
python "face drive.py"
```
- Simple version without calibration or advanced features
- Press 'q' to quit
- Adjust `head_move_threshold` in [face drive.py:22](face drive.py#L22) to change sensitivity

### Mouse-controlled driving:
```bash
python "mouse drive.py"
```
- Centers mouse cursor automatically
- Move mouse from center to control direction
- Press Ctrl+C in terminal to stop
- Logs movement data to `driving_data.csv`

## Configuration & Tuning

### Accessible Face Control (config.json)

All parameters are stored in [config.json](config.json) and can be modified:

**Sensitivity** (horizontal/vertical):
- Lower values = more sensitive (10-20 = very sensitive, 30-40 = medium, 50+ = less sensitive)
- Adjust during runtime with `+/-` keys

**Dead Zones** (horizontal/vertical):
- Prevents involuntary movements and tremors
- Increase if you have tremors or want more stability
- Measured in pixels of head displacement from neutral position

**Smoothing**:
- `ema_alpha`: 0.1 = very smooth but laggy, 0.5 = responsive but less smooth
- `kalman_R` and `kalman_Q`: Adjust noise filtering

**Control Modes**:
- `position`: Head position controls direction (default)
- `velocity`: Head movement speed controls intensity
- `simplified`: Auto-forward, only left/right steering

**Safety**:
- `enable_auto_pause`: Auto-pause if face not detected
- `pause_delay_seconds`: Time before triggering auto-pause

### Basic Face Control (legacy)
Modify in [face drive.py:22](face drive.py#L22):
```python
self.head_move_threshold = 30  # Lower = more sensitive
```

### Mouse Control Parameters
Key settings in [mouse drive.py](mouse drive.py):
- **Line 11**: `sensitivity = 100` - Overall sensitivity multiplier
- **Line 24**: `smoothing_factor = 0.2` - Transition smoothing (0-1)
- **Line 26**: `ema_alpha = 0.1` - Exponential moving average weight
- **Line 57**: `dead_zone_radius = 10` - Minimum displacement to register (pixels)
- **Line 52**: `erratic_threshold = 5` - Direction changes to trigger stabilization

### Kalman Filter Tuning
Lines 28-33 in [mouse drive.py](mouse drive.py) control noise filtering. Increase `kalman_Q` for more responsive (less smooth) tracking.

## Dependencies

This project requires:
- OpenCV (`cv2`) - Video capture and display
- MediaPipe (`mediapipe`) - Face detection model
- PyAutoGUI (`pyautogui`) - Keyboard input simulation

Install with:
```bash
pip install opencv-python mediapipe pyautogui
```

## Important Notes

- **pyautogui.FAILSAFE is disabled** in mouse drive mode ([mouse drive.py:8](mouse drive.py#L8)) - moving mouse to screen corners won't stop execution
- Both systems assume the game window is focused and accepting keyboard input
- The camera handler scans camera indices 0-9 and uses the first available camera
- Face detection uses MediaPipe with default confidence threshold of 0.5 (configurable in FaceDetector constructor)
- Mouse control logs all movement data to CSV for analysis/debugging