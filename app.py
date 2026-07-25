import sys
import os
import multiprocessing
import subprocess
from pathlib import Path
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtQml import QQmlApplicationEngine
from PyQt6.QtCore import QObject, pyqtSlot, pyqtProperty, pyqtSignal, QThread

if getattr(sys, 'frozen', False):
    # Running in a PyInstaller bundle
    BASE_DIR = Path(sys._MEIPASS)
else:
    # Running in normal Python environment
    BASE_DIR = Path(__file__).resolve().parent

# Fix for missing QtQuick Controls Windows style plugin on PyQt6
os.environ["QT_QUICK_CONTROLS_STYLE"] = "Basic"

# Ensure model is strictly loaded offline from hf_cache
os.environ.setdefault("HF_HOME", str(BASE_DIR / "hf_cache"))
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")


class ResultWatcher(QThread):
    """
    Watches the result_queue in a background thread and emits a signal
    back to the main Qt thread when a result arrives.
    """
    finished = pyqtSignal(bool, str)

    def __init__(self, result_queue):
        super().__init__()
        self.result_queue = result_queue
        self._running = True

    def run(self):
        while self._running:
            try:
                # Block with a timeout so we can check _running periodically
                result = self.result_queue.get(timeout=0.5)
                if result is None:
                    break
                status, payload = result
                if status == "ok":
                    self.finished.emit(True, f"Successfully saved to {payload}")
                elif status == "error":
                    self.finished.emit(False, payload)
                # "ready" is handled by Backend.on_worker_ready — skip here
            except Exception:
                # Queue.get timeout — loop again
                continue

    def stop(self):
        self._running = False


class Backend(QObject):
    statusChanged = pyqtSignal()
    isGeneratingChanged = pyqtSignal()
    isModelLoadedChanged = pyqtSignal()
    voiceLabelsChanged = pyqtSignal()
    voiceVidsChanged = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._statusText = "Initializing..."
        self._isGenerating = False
        self._isModelLoaded = False
        self._voiceLabels = []
        self._voiceVids = []

        # Multiprocessing queues for IPC with the worker process
        self._request_queue = multiprocessing.Queue()
        self._result_queue  = multiprocessing.Queue()
        self._worker_process = None
        self._watcher = None

    def start_worker(self):
        """
        Spawns the persistent worker process and waits for it to signal ready.
        Also starts the ResultWatcher thread to relay results back to QML.
        """
        self.set_statusText("Loading model (first launch may take a moment)...")

        from tts_process import worker_main
        self._worker_process = multiprocessing.Process(
            target=worker_main,
            args=(self._request_queue, self._result_queue, str(BASE_DIR)),
            daemon=True
        )

        # On Windows, temporarily patch subprocess.Popen so that
        # multiprocessing (which uses it internally) spawns with no console window.
        if sys.platform == "win32":
            _orig = subprocess.Popen.__init__
            def _no_window_popen(self_inner, *args, **kwargs):
                kwargs.setdefault("creationflags", 0)
                kwargs["creationflags"] |= subprocess.CREATE_NO_WINDOW
                _orig(self_inner, *args, **kwargs)
            subprocess.Popen.__init__ = _no_window_popen
            try:
                self._worker_process.start()
            finally:
                subprocess.Popen.__init__ = _orig  # always restore
        else:
            self._worker_process.start()

        # Wait for the worker to finish loading the model
        status, payload = self._result_queue.get()
        if status == "ready":
            # Now fetch voice list from the MAIN process (no model needed)
            os.environ.setdefault("HF_HOME", str(BASE_DIR / "hf_cache"))
            os.environ["HF_HUB_OFFLINE"] = "1"
            os.environ["TRANSFORMERS_OFFLINE"] = "1"
            from vieneu import Vieneu
            tmp_model = Vieneu(backend="onnx")
            voices = tmp_model.list_preset_voices()
            self._voiceLabels = [v[0] for v in voices]
            self._voiceVids   = [v[1] for v in voices]
            self.voiceLabelsChanged.emit()
            self.voiceVidsChanged.emit()
            del tmp_model

            self._isModelLoaded = True
            self.isModelLoadedChanged.emit()
            self.set_statusText("Ready.")
        else:
            self.set_statusText(f"Model Error: {payload}")
            return

        # Start the watcher thread that relays results from the queue to Qt signals
        self._watcher = ResultWatcher(self._result_queue)
        self._watcher.finished.connect(self.on_generation_finished)
        self._watcher.start()

    def shutdown(self):
        """Cleanly shut down the worker process and watcher thread."""
        if self._watcher:
            self._watcher.stop()
        if self._worker_process and self._worker_process.is_alive():
            self._request_queue.put(None)  # poison pill
            self._worker_process.join(timeout=3)

    @pyqtProperty(str, notify=statusChanged)
    def statusText(self):
        return self._statusText

    def set_statusText(self, text):
        self._statusText = text
        self.statusChanged.emit()

    @pyqtProperty(bool, notify=isGeneratingChanged)
    def isGenerating(self):
        return self._isGenerating

    @pyqtProperty(bool, notify=isModelLoadedChanged)
    def isModelLoaded(self):
        return self._isModelLoaded

    @pyqtProperty(list, notify=voiceLabelsChanged)
    def voiceLabels(self):
        return self._voiceLabels

    @pyqtProperty(list, notify=voiceVidsChanged)
    def voiceVids(self):
        return self._voiceVids

    @pyqtSlot(str, str, str, str, str)
    def generate_audio(self, text, output_dir, filename, voice, style):
        if not text.strip():
            self.set_statusText("Error: Text is empty.")
            return
        if not output_dir.strip():
            self.set_statusText("Error: Please select an output directory.")
            return

        # Map style label to API key
        style_map = {
            "tự nhiên": "tu_nhien",
            "kể chuyện": "ke_chuyen",
            "tin tức": "tin_tuc"
        }
        style_key = style_map.get(style, style)

        filepath = os.path.join(output_dir, filename)

        self._isGenerating = True
        self.isGeneratingChanged.emit()
        self.set_statusText(f"Generating with {voice} ({style})...")

        # Send job to the persistent worker process
        self._request_queue.put((text, voice, style_key, filepath))

    @pyqtSlot(bool, str)
    def on_generation_finished(self, success, message):
        self._isGenerating = False
        self.isGeneratingChanged.emit()
        self.set_statusText(message if success else f"Error: {message}")


if __name__ == "__main__":
    # Required for multiprocessing on Windows (PyInstaller freeze-safe)
    multiprocessing.freeze_support()

    app = QGuiApplication(sys.argv)
    engine = QQmlApplicationEngine()

    backend = Backend()
    engine.rootContext().setContextProperty("backend", backend)

    # Start the persistent worker process (loads model once)
    backend.start_worker()

    qml_file = BASE_DIR / "main.qml"
    engine.load(qml_file.as_uri())

    if not engine.rootObjects():
        sys.exit(-1)

    exit_code = app.exec()
    backend.shutdown()
    sys.exit(exit_code)
