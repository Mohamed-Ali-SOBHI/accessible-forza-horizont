import cv2

class CameraHandler:
    def __init__(
        self,
        camera_index=-1,
        prompt_on_multiple=True,
        max_cameras=10,
        preferred_resolution=None,
        preferred_fps=None,
    ):
        """
        Initialize camera handler

        Args:
            camera_index: Index of camera to use (-1 for auto-detection)
            prompt_on_multiple: Ask user to pick when several cameras are available
            max_cameras: Number of devices to probe when searching
            preferred_resolution: Optional tuple (width, height) to request on selection
            preferred_fps: Optional frame rate request
        """
        self.camera_index = camera_index
        self.cap = None
        self.prompt_on_multiple = prompt_on_multiple
        self.max_cameras = max_cameras
        self.preferred_resolution = preferred_resolution
        self.preferred_fps = preferred_fps

        if camera_index == -1:
            available = self.list_available_cameras()
            if not available:
                raise Exception("Aucune camera disponible")

            if self.prompt_on_multiple and len(available) > 1:
                selected_index = self.prompt_camera_selection(available)
            else:
                selected_index = available[0]

            self.cap = self.get_specific_camera(selected_index)
        else:
            self.cap = self.get_specific_camera(camera_index)

        if self.cap is not None:
            self.configure_camera(self.preferred_resolution, self.preferred_fps)

    @staticmethod
    @staticmethod
    def list_static(max_cameras=10):
        available = []
        for i in range(max_cameras):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                ret, _ = cap.read()
                if ret:
                    available.append(i)
            cap.release()
        return available

    def list_available_cameras(self):
        """
        Probe all cameras and return available indices.

        Returns:
            list[int]: List of camera indices that can be opened
        """
        available = []
        print("Detection des cameras disponibles...")
        for i in range(self.max_cameras):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                ret, _ = cap.read()
                if ret:
                    available.append(i)
                    print(f"  - Camera disponible a l'index {i}")
                else:
                    print(f"  - Camera a l'index {i} detectee mais ne repond pas (peut-etre deja utilisee)")
            cap.release()

        if not available:
            print("  Aucune camera detectee.")

        return available

    def prompt_camera_selection(self, available):
        """
        Prompt user to select a camera index from the available list.

        Args:
            available: List of available camera indices

        Returns:
            int: Selected camera index
        """
        print("\nPlusieurs cameras ont ete detectees.")
        for index in available:
            print(f"  [{index}] Camera {index}")

        while True:
            choice = input(
                "Selectionnez l'index de la camera a utiliser "
                "(appuyez sur Entree pour choisir la premiere disponible): "
            ).strip()

            if choice == "":
                print(f"Aucune selection effectuee, utilisation de la camera {available[0]}")
                return available[0]

            if choice.isdigit():
                index = int(choice)
                if index in available:
                    print(f"Camera {index} selectionnee par l'utilisateur")
                    return index

            print("Selection invalide. Merci de choisir un index parmi la liste.")

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
        Get first available camera without quality tests

        Returns:
            cv2.VideoCapture: First available camera
        """
        available = self.list_available_cameras()
        if not available:
            raise Exception("Aucune camera disponible")

        print(f"Camera trouvee a l'index {available[0]}")
        return self.get_specific_camera(available[0])

    def configure_camera(self, resolution=None, fps=None):
        """
        Configure capture properties such as resolution and FPS.

        Args:
            resolution: Optional tuple (width, height)
            fps: Optional frame rate to request
        """
        if self.cap is None or not self.cap.isOpened():
            return

        if resolution:
            width, height = resolution
            if width > 0:
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            if height > 0:
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

        if fps and fps > 0:
            self.cap.set(cv2.CAP_PROP_FPS, fps)

        # Report actual values for debugging/diagnostics
        actual_width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        actual_height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        actual_fps = self.cap.get(cv2.CAP_PROP_FPS)

        print(
            f"Camera configuree a {int(actual_width)}x{int(actual_height)}"
            f" @ {actual_fps:.1f} FPS"
        )

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
