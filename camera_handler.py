import cv2
import time

class CameraHandler:
    def __init__(self, camera_index=-1):
        """
        Initialize camera handler

        Args:
            camera_index: Index of camera to use (-1 for auto-detection)
        """
        self.camera_index = camera_index
        self.cap = None

        if camera_index == -1:
            self.cap = self.get_best_available_camera()
        else:
            self.cap = self.get_specific_camera(camera_index)

    def list_all_cameras(self, max_cameras=10):
        """
        List all available cameras with their details

        Returns:
            list: List of tuples (index, resolution, fps) for each available camera
        """
        available_cameras = []

        print("\n" + "="*60)
        print("  DETECTION DES CAMERAS DISPONIBLES")
        print("="*60)

        for i in range(max_cameras):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                # Try to read a frame
                ret, frame = cap.read()
                if ret:
                    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    fps = int(cap.get(cv2.CAP_PROP_FPS))

                    available_cameras.append((i, (width, height), fps))
                    print(f"  [{i}] Camera trouvee - Resolution: {width}x{height} @ {fps}fps")

                cap.release()

        if not available_cameras:
            print("  X Aucune camera trouvee")

        print("="*60 + "\n")
        return available_cameras

    def test_camera_quality(self, camera_index, num_frames=5):
        """
        Test camera quality by capturing multiple frames

        Args:
            camera_index: Index of camera to test
            num_frames: Number of frames to test

        Returns:
            float: Quality score (0-1), higher is better
        """
        cap = cv2.VideoCapture(camera_index)
        if not cap.isOpened():
            return 0.0

        successful_frames = 0
        total_brightness = 0

        # Let camera warm up
        time.sleep(0.2)

        for _ in range(num_frames):
            ret, frame = cap.read()
            if ret and frame is not None and frame.size > 0:
                successful_frames += 1
                # Calculate average brightness as a simple quality metric
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                brightness = gray.mean()
                total_brightness += brightness

        cap.release()

        if successful_frames == 0:
            return 0.0

        success_rate = successful_frames / num_frames
        avg_brightness = total_brightness / successful_frames

        # Score based on success rate and brightness (0-255 normalized to 0-1)
        # Prefer cameras with good brightness (50-200 range is ideal)
        brightness_score = min(1.0, avg_brightness / 100) if avg_brightness < 200 else 0.5

        return (success_rate * 0.7) + (brightness_score * 0.3)

    def get_best_available_camera(self, max_cameras=10):
        """
        Find and return the best available camera based on quality tests

        Returns:
            cv2.VideoCapture: The best camera found
        """
        cameras = self.list_all_cameras(max_cameras)

        if not cameras:
            raise Exception("X Aucune camera disponible")

        if len(cameras) == 1:
            index = cameras[0][0]
            print(f"Une seule camera trouvee, utilisation de la camera {index}")
            self.camera_index = index
            return cv2.VideoCapture(index)

        # Multiple cameras, test quality of each
        print("\nTest de qualite des cameras...")
        best_camera = None
        best_score = 0
        best_index = -1

        for camera_index, resolution, fps in cameras:
            score = self.test_camera_quality(camera_index)
            print(f"  Camera {camera_index}: Score de qualite = {score:.2f}")

            if score > best_score:
                best_score = score
                best_index = camera_index

        if best_index != -1:
            print(f"\nMeilleure camera: {best_index} (score: {best_score:.2f})")
            self.camera_index = best_index
            return cv2.VideoCapture(best_index)

        # Fallback to first camera if quality test failed
        print(f"\nTests de qualite echoues, utilisation de la camera {cameras[0][0]}")
        self.camera_index = cameras[0][0]
        return cv2.VideoCapture(cameras[0][0])

    def get_specific_camera(self, camera_index):
        """
        Get a specific camera by index

        Args:
            camera_index: Index of camera to get

        Returns:
            cv2.VideoCapture: The requested camera
        """
        cap = cv2.VideoCapture(camera_index)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                print(f"Camera {camera_index} selectionnee")
                self.camera_index = camera_index
                return cap
            else:
                cap.release()
                raise Exception(f"Camera {camera_index} ne peut pas capturer d'images")
        else:
            raise Exception(f"Camera {camera_index} n'est pas disponible")

    def get_first_available_camera(self):
        """
        Legacy method for compatibility - finds first working camera

        Returns:
            cv2.VideoCapture: First available camera
        """
        for i in range(10):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    print(f"Camera found at index {i}")
                    self.camera_index = i
                    return cap
                else:
                    cap.release()
        raise Exception("No available camera")

    def get_frame(self):
        """
        Get a frame from the camera

        Returns:
            tuple: (success, frame)
        """
        if self.cap is None or not self.cap.isOpened():
            print("Erreur: Camera non initialisee")
            return False, None

        ret, frame = self.cap.read()
        if not ret:
            print("Echec de capture d'image")
            return False, None
        return ret, frame

    def close(self):
        """Close the camera"""
        if self.cap is not None and self.cap.isOpened():
            self.cap.release()
            print(f"Camera {self.camera_index} fermee")
