import queue
import threading
import time
import tkinter as tk
from tkinter import ttk
from typing import Optional

from camera_handler import CameraHandler
from simple_head_drive import SimpleHeadControlledDrive


class DriveUI:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Simple Head Drive")
        self.root.geometry("780x620")
        self.root.minsize(700, 560)

        self.driver: Optional[SimpleHeadControlledDrive] = None
        self.worker: Optional[threading.Thread] = None
        self.event_queue: queue.Queue = queue.Queue()

        self._configure_style()
        self._build_widgets()
        self._poll_events()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    # ------------------------------------------------------------------ #
    # Styling
    # ------------------------------------------------------------------ #
    def _configure_style(self) -> None:
        self.colors = {
            "bg": "#0f172a",
            "card": "#1f2937",
            "subcard": "#111c2e",
            "accent": "#38bdf8",
            "accent_hover": "#0ea5e9",
            "success": "#34d399",
            "warning": "#fbbf24",
            "danger": "#f87171",
            "text": "#e2e8f0",
            "muted": "#94a3b8",
        }

        self.root.configure(bg=self.colors["bg"])
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("Background.TFrame", background=self.colors["bg"])
        style.configure("Card.TFrame", background=self.colors["card"])
        style.configure("SubCard.TFrame", background=self.colors["subcard"])
        style.configure(
            "HeroTitle.TLabel",
            background=self.colors["accent"],
            foreground="#0b1120",
            font=("Segoe UI", 20, "bold"),
        )
        style.configure(
            "HeroSubtitle.TLabel",
            background=self.colors["accent"],
            foreground="#082f49",
            font=("Segoe UI", 11),
        )
        style.configure(
            "CardTitle.TLabel",
            background=self.colors["card"],
            foreground=self.colors["text"],
            font=("Segoe UI", 12, "bold"),
        )
        style.configure(
            "Info.TLabel",
            background=self.colors["subcard"],
            foreground=self.colors["text"],
            font=("Segoe UI", 10),
            anchor="w",
        )
        style.configure(
            "Small.TLabel",
            background=self.colors["card"],
            foreground=self.colors["muted"],
            font=("Segoe UI", 10),
        )

        style.configure(
            "Accent.TButton",
            background=self.colors["accent"],
            foreground="#031633",
            font=("Segoe UI", 11, "bold"),
            borderwidth=0,
            padding=8,
        )
        style.map(
            "Accent.TButton",
            background=[("active", self.colors["accent_hover"])],
        )
        style.configure(
            "Ghost.TButton",
            background=self.colors["subcard"],
            foreground=self.colors["text"],
            font=("Segoe UI", 10),
            borderwidth=0,
            padding=6,
        )
        style.map("Ghost.TButton", background=[("active", self.colors["card"])])

        style.configure(
            "Combo.TCombobox",
            fieldbackground=self.colors["card"],
            background=self.colors["card"],
            foreground=self.colors["text"],
            bordercolor=self.colors["subcard"],
            arrowcolor=self.colors["accent"],
        )
        style.map(
            "Combo.TCombobox",
            fieldbackground=[("readonly", self.colors["card"]), ("disabled", self.colors["subcard"])],
        )

        style.configure(
            "Accent.Horizontal.TProgressbar",
            troughcolor=self.colors["subcard"],
            background=self.colors["accent"],
            bordercolor=self.colors["subcard"],
            lightcolor=self.colors["accent"],
            darkcolor=self.colors["accent"],
        )

    # ------------------------------------------------------------------ #
    # UI Layout
    # ------------------------------------------------------------------ #
    def _build_widgets(self) -> None:
        self.main = ttk.Frame(self.root, style="Background.TFrame", padding=20)
        self.main.pack(fill="both", expand=True)
        for col in range(2):
            self.main.columnconfigure(col, weight=1)

        hero = tk.Frame(self.main, bg=self.colors["accent"], bd=0, highlightthickness=0)
        hero.grid(column=0, row=0, columnspan=2, sticky="ew", pady=(0, 20))
        hero.grid_columnconfigure(0, weight=1)
        ttk.Label(hero, text="Simple Head-Controlled Driving", style="HeroTitle.TLabel").grid(
            column=0, row=0, sticky="w", padx=16, pady=(16, 4)
        )
        ttk.Label(
            hero,
            text="Mouth = throttle  •  Head down = reverse  •  Head up = brake",
            style="HeroSubtitle.TLabel",
        ).grid(column=0, row=1, sticky="w", padx=16, pady=(0, 16))

        self._build_session_card(row=1, column=0)
        self._build_camera_card(row=1, column=1)
        self._build_status_card(row=2, column=0)
        self._build_log_card(row=2, column=1)

        self._set_status("Status: Idle", "info")
        self.refresh_cameras()

    def _build_session_card(self, row: int, column: int) -> None:
        card = ttk.Frame(self.main, style="Card.TFrame", padding=(18, 18))
        card.grid(row=row, column=column, sticky="nsew", padx=(0 if column == 0 else 12, 12), pady=(0, 18))
        self.main.rowconfigure(row, weight=1)

        ttk.Label(card, text="Session", style="CardTitle.TLabel").pack(anchor="w")

        btn_bar = ttk.Frame(card, style="Card.TFrame")
        btn_bar.pack(anchor="w", pady=(12, 0))
        self.start_button = ttk.Button(btn_bar, text="► Start", style="Accent.TButton", command=self.start_drive)
        self.start_button.pack(side="left", padx=(0, 10))
        self.stop_button = ttk.Button(
            btn_bar, text="■ Stop", style="Ghost.TButton", command=self.stop_drive, state=tk.DISABLED
        )
        self.stop_button.pack(side="left")

        info = ttk.Frame(card, style="SubCard.TFrame", padding=(14, 12))
        info.pack(fill="x", pady=(16, 0))
        instructions = [
            "• Keep a neutral pose during calibration.",
            "• Lift your chin to brake, lower it to reverse.",
            "• Open your mouth wider to increase speed.",
            "• Watch the live event log for feedback.",
        ]
        for line in instructions:
            ttk.Label(info, text=line, style="Info.TLabel", wraplength=320).pack(anchor="w", pady=2)

    def _build_camera_card(self, row: int, column: int) -> None:
        card = ttk.Frame(self.main, style="Card.TFrame", padding=(18, 18))
        card.grid(row=row, column=column, sticky="nsew", padx=(0 if column == 0 else 12, 0), pady=(0, 18))
        self.main.rowconfigure(row, weight=1)

        ttk.Label(card, text="Camera", style="CardTitle.TLabel").pack(anchor="w")

        combo_row = ttk.Frame(card, style="Card.TFrame")
        combo_row.pack(fill="x", pady=(12, 0))
        self.camera_combo = ttk.Combobox(combo_row, state="readonly", values=["Scanning..."], width=22)
        self.camera_combo.pack(side="left", fill="x", expand=True)
        self.camera_combo.current(0)

        self.refresh_button = ttk.Button(
            combo_row, text="⟳ Refresh", style="Ghost.TButton", command=self.refresh_cameras
        )
        self.refresh_button.pack(side="left", padx=(8, 0))

        ttk.Label(
            card,
            text="Select the camera to use before starting.",
            style="Small.TLabel",
            wraplength=320,
        ).pack(anchor="w", pady=(12, 0))

    def _build_status_card(self, row: int, column: int) -> None:
        card = ttk.Frame(self.main, style="Card.TFrame", padding=(18, 18))
        card.grid(row=row, column=column, sticky="nsew", padx=(0 if column == 0 else 12, 12))
        self.main.rowconfigure(row, weight=1)

        status_row = ttk.Frame(card, style="Card.TFrame")
        status_row.pack(fill="x")
        self.status_badge = tk.Label(
            status_row, text="●", font=("Segoe UI", 22), fg=self.colors["muted"], bg=self.colors["card"], bd=0
        )
        self.status_badge.pack(side="left")

        self.status_var = tk.StringVar(value="Status: Idle")
        ttk.Label(status_row, textvariable=self.status_var, style="CardTitle.TLabel").pack(
            side="left", padx=(8, 0)
        )

        self.calibration_bar = ttk.Progressbar(
            card, style="Accent.Horizontal.TProgressbar", mode="indeterminate", length=240
        )
        self.calibration_bar.pack(anchor="w", pady=(14, 0))

    def _build_log_card(self, row: int, column: int) -> None:
        card = ttk.Frame(self.main, style="Card.TFrame", padding=(18, 18))
        card.grid(row=row, column=column, sticky="nsew")
        self.main.rowconfigure(row, weight=1)

        ttk.Label(card, text="Event log", style="CardTitle.TLabel").pack(anchor="w")
        container = ttk.Frame(card, style="Card.TFrame")
        container.pack(fill="both", expand=True, pady=(12, 0))

        self.log_widget = tk.Text(
            container,
            height=12,
            state=tk.DISABLED,
            wrap="word",
            bg=self.colors["subcard"],
            fg=self.colors["text"],
            insertbackground=self.colors["accent"],
            relief="flat",
            borderwidth=0,
            font=("Consolas", 10),
        )
        self.log_widget.pack(side="left", fill="both", expand=True)
        scroll = ttk.Scrollbar(container, command=self.log_widget.yview)
        scroll.pack(side="right", fill="y")
        self.log_widget.configure(yscrollcommand=scroll.set)

    # ------------------------------------------------------------------ #
    # Event system
    # ------------------------------------------------------------------ #
    def _set_status(self, text: str, level: str = "info") -> None:
        palette = {
            "info": self.colors["accent"],
            "success": self.colors["success"],
            "warning": self.colors["warning"],
            "danger": self.colors["danger"],
        }
        self.status_var.set(text)
        self.status_badge.configure(fg=palette.get(level, self.colors["accent"]))

    def _append_log(self, message: str, level: str = "info") -> None:
        color_map = {
            "info": self.colors["muted"],
            "success": self.colors["success"],
            "warning": self.colors["warning"],
            "danger": self.colors["danger"],
        }
        timestamp = time.strftime("%H:%M:%S")
        if level not in self.log_widget.tag_names():
            self.log_widget.tag_config(level, foreground=color_map.get(level, self.colors["muted"]))
        self.log_widget.configure(state=tk.NORMAL)
        self.log_widget.insert(tk.END, f"[{timestamp}] {message}\n", level)
        self.log_widget.see(tk.END)
        self.log_widget.configure(state=tk.DISABLED)

    def _poll_events(self) -> None:
        while True:
            try:
                event, payload = self.event_queue.get_nowait()
            except queue.Empty:
                break
            self._handle_event(event, payload)
        self.root.after(120, self._poll_events)

    def _handle_event(self, event: str, payload: dict) -> None:
        if event == "status":
            text = payload.get("text", "")
            motion = payload.get("motion", "").capitalize() or "Updated"
            self._append_log(text, "info")
            self._set_status(f"Status: {motion}", "success")
        elif event == "calibration":
            stage = payload.get("stage", "")
            if stage == "start":
                self._append_log("Calibration started.", "warning")
                self._set_status("Status: Calibration", "warning")
                self.calibration_bar.start(10)
            elif stage == "failed":
                self._append_log("Calibration failed (no face detected).", "danger")
                self._set_status("Status: Calibration failed", "danger")
                self.calibration_bar.stop()
                self.calibration_bar["value"] = 0
            elif stage == "complete":
                self._append_log("Calibration complete. Control loop running.", "success")
                self._set_status("Status: Active control", "success")
                self.calibration_bar.stop()
                self.calibration_bar["value"] = 0
        elif event == "app":
            state = payload.get("state", "")
            if state == "camera_ready":
                self._append_log("Camera initialized.", "info")
            elif state == "stop_requested":
                self._append_log("Stop requested...", "warning")
                self._set_status("Status: Stopping...", "warning")
            elif state == "stopped":
                self._append_log("Driver stopped.", "info")
                self._set_status("Status: Idle", "info")
                self._set_buttons(start=True, stop=False)
                self.refresh_button.config(state=tk.NORMAL)
                self.driver = None
                self.worker = None
        elif event == "error":
            self._append_log(f"Error: {payload.get('message')}", "danger")
            self._set_status("Status: Error", "danger")
            self._set_buttons(start=True, stop=False)
            self.refresh_button.config(state=tk.NORMAL)

    def _queue_event(self, event: str, payload: Optional[dict] = None) -> None:
        self.event_queue.put((event, payload or {}))

    # ------------------------------------------------------------------ #
    # Camera handling
    # ------------------------------------------------------------------ #
    def refresh_cameras(self) -> None:
        self.camera_combo.configure(state="disabled")
        self.refresh_button.config(state=tk.DISABLED)
        self.camera_combo["values"] = ["Scanning..."]
        self.camera_combo.current(0)
        self.root.update_idletasks()

        available = CameraHandler.list_static()
        values = ["Auto-detect"] + [f"Camera {idx}" for idx in available]
        self.camera_combo["values"] = values or ["Auto-detect"]
        self.camera_combo.current(0)
        self.camera_combo.configure(state="readonly")
        self.refresh_button.config(state=tk.NORMAL)
        self._append_log(f"Cameras found: {available}", "info")

    def _get_selected_camera_index(self) -> int:
        selection = self.camera_combo.get()
        if selection in ("Auto-detect", "Scanning..."):
            return -1
        try:
            return int(selection.split()[-1])
        except Exception:
            return -1

    # ------------------------------------------------------------------ #
    # Driver control
    # ------------------------------------------------------------------ #
    def _set_buttons(self, start: bool, stop: bool) -> None:
        self.start_button.config(state=tk.NORMAL if start else tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL if stop else tk.DISABLED)
        self.refresh_button.config(state=tk.NORMAL if start else tk.DISABLED)

    def start_drive(self) -> None:
        if self.driver is not None:
            return
        camera_index = self._get_selected_camera_index()
        self.driver = SimpleHeadControlledDrive(
            status_callback=self._queue_event,
            camera_override=camera_index,
        )
        self.worker = threading.Thread(target=self._run_driver, daemon=True)
        self.worker.start()
        self._set_buttons(start=False, stop=True)
        self._set_status("Status: Starting...", "info")
        self._append_log("Driver thread started.", "info")

    def stop_drive(self) -> None:
        if self.driver is not None:
            self.driver.request_stop()
            self._append_log("Stop signal sent.", "warning")

    def _run_driver(self) -> None:
        try:
            self.driver.run()
        except Exception as exc:  # pylint: disable=broad-except
            self._queue_event("error", message=str(exc))
        finally:
            if self.driver is not None:
                self.driver.request_stop()
            self._queue_event("app", state="stopped")

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #
    def on_close(self) -> None:
        self.stop_drive()
        if self.worker and self.worker.is_alive():
            self.worker.join(timeout=1.5)
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


if __name__ == "__main__":
    DriveUI().run()
