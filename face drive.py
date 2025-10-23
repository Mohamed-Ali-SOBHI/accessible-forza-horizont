import cv2
import mediapipe as mp
import pyautogui
import time
from camera_handler import CameraHandler
from face_detector import FaceDetector

# Directional keys
KEY_FORWARD = 'z'
KEY_BACKWARD = 's'
KEY_LEFT = 'q'
KEY_RIGHT = 'd'

class HeadControlledDriving:
    def __init__(self):
        self.camera_handler = CameraHandler()
        self.face_detector = FaceDetector(self.camera_handler)
        self.screen_width, self.screen_height = pyautogui.size()
        self.center_x, self.center_y = self.screen_width // 2, self.screen_height // 2
        
        # Parameters for head movement detection
        self.head_move_threshold = 30  # Adjust this value to change sensitivity
        self.last_x, self.last_y = 0, 0

    def detect_head_movement(self, x, y, w, h):
        center_x = x + w // 2
        center_y = y + h // 2
        
        dx = center_x - self.last_x
        dy = center_y - self.last_y
        
        self.last_x, self.last_y = center_x, center_y
        
        return dx, dy

    def control_car(self, dx, dy):
        if abs(dx) > self.head_move_threshold:
            if dx > 0:
                pyautogui.keyDown(KEY_RIGHT)
                pyautogui.keyUp(KEY_LEFT)
            else:
                pyautogui.keyDown(KEY_LEFT)
                pyautogui.keyUp(KEY_RIGHT)
        else:
            pyautogui.keyUp(KEY_LEFT)
            pyautogui.keyUp(KEY_RIGHT)
        
        if abs(dy) > self.head_move_threshold:
            if dy > 0:
                pyautogui.keyDown(KEY_BACKWARD)
                pyautogui.keyUp(KEY_FORWARD)
            else:
                pyautogui.keyDown(KEY_FORWARD)
                pyautogui.keyUp(KEY_BACKWARD)
        else:
            pyautogui.keyUp(KEY_FORWARD)
            pyautogui.keyUp(KEY_BACKWARD)

    def run(self):
        try:
            while True:
                ret, frame = self.camera_handler.get_frame()
                if not ret:
                    print("Failed to get frame")
                    continue

                x, y, w, h, confidence = self.face_detector.detect_face(frame)
                if confidence > 0:
                    frame = self.face_detector.draw_face_rectangle(frame, x, y, w, h)
                    dx, dy = self.detect_head_movement(x, y, w, h)
                    self.control_car(dx, dy)

                cv2.imshow('Head Controlled Driving', frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

                time.sleep(0.01)  # Small delay to prevent high CPU usage

        finally:
            self.camera_handler.close()
            self.face_detector.close()
            cv2.destroyAllWindows()

if __name__ == "__main__":
    head_controlled_driving = HeadControlledDriving()
    head_controlled_driving.run()