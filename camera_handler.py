import cv2

class CameraHandler:
    def __init__(self):
        self.cap = self.get_first_available_camera()

    def get_first_available_camera(self):
        for i in range(10):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    print(f"Camera found at index {i}")
                    return cap
                else:
                    cap.release()
        raise Exception("No available camera")

    def get_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            print("Failed to get frame from the camera")
            return None, None
        return ret, frame

    def close(self):
        if self.cap.isOpened():
            self.cap.release()
