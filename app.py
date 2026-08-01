import sys
import os
import tempfile
import subprocess
from pathlib import Path
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtQml import QQmlApplicationEngine
from PyQt6.QtCore import QObject, pyqtSlot, pyqtProperty, pyqtSignal, QThread
import ast

if getattr(sys, 'frozen', False):
    # Running in a PyInstaller bundle
    BASE_DIR = Path(sys._MEIPASS)
else:
    # Running in normal Python environment
    BASE_DIR = Path(__file__).resolve().parent

# Fix for missing QtQuick Controls Windows style plugin on PyQt6
os.environ["QT_QUICK_CONTROLS_STYLE"] = "Basic"

class TTSWorker(QThread):
    """
    Runs TTS inference in a completely separate Python subprocess.
    When the subprocess exits, the OS reclaims ALL memory including
    ONNX Runtime internal pools — the only reliable way to prevent leaks.
    """
    resultReady = pyqtSignal(bool, str)
    
    def __init__(self, text, filepath, voice, style, parent=None):
        super().__init__(parent)
        self.text = text
        self.filepath = filepath
        self.voice = voice
        
        # Map QML style selections back to API keys
        style_map = {
            "tự nhiên": "tu_nhien",
            "kể chuyện": "ke_chuyen",
            "tin tức": "tin_tuc"
        }
        self.style = style_map.get(style, style)
        
    def run(self):
        # Write text to a temp file to avoid Windows command-line length limits
        tmp = tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", suffix=".txt", delete=False
        )
        try:
            tmp.write(self.text)
            tmp.close()

            # Locate the worker script next to app.py or inside the bundle
            if getattr(sys, 'frozen', False):
                worker_script = Path(sys._MEIPASS) / "tts_process.py"
            else:
                worker_script = BASE_DIR / "tts_process.py"

            result = subprocess.run(
                [sys.executable, str(worker_script),
                 tmp.name, self.voice, self.style, self.filepath],
                capture_output=True,
                text=True,
                encoding="utf-8"
            )

            stdout = result.stdout.strip()
            if result.returncode == 0 and stdout == "OK":
                self.resultReady.emit(True, f"Successfully saved to {self.filepath}")
            else:
                error = result.stderr.strip() or stdout
                self.resultReady.emit(False, error)
        except Exception as e:
            self.resultReady.emit(False, str(e))
        finally:
            # Always clean up the temp text file
            try:
                os.unlink(tmp.name)
            except Exception:
                pass

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
        self.model = None
        self.worker = None
        
    def load_model(self):
        self.set_statusText("Loading model...")
        try:
            if getattr(sys, 'frozen', False):
                voices_script = Path(sys._MEIPASS) / "voices_output.txt"
            else:
                voices_script = BASE_DIR / "voices_output.txt"

            with open(voices_script, "r", encoding="utf-8") as f:
                content = f.read()
            voices = ast.literal_eval(content)
            self._voiceLabels = [v[0] for v in voices]
            self._voiceVids = [v[1] for v in voices]
            self.voiceLabelsChanged.emit()
            self.voiceVidsChanged.emit()
            
            self._isModelLoaded = True
            self.isModelLoadedChanged.emit()
            self.set_statusText("Ready.")
        except Exception as e:
            self.set_statusText(f"Model Error: {str(e)}")

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
        if self._isGenerating:
            self.set_statusText("Error: Audio generation is already in progress.")
            return
            
        if not text.strip():
            self.set_statusText("Error: Text is empty.")
            return
        if not output_dir.strip():
            self.set_statusText("Error: Please select an output directory.")
            return
            
        filepath = os.path.join(output_dir, filename)
        
        self._isGenerating = True
        self.isGeneratingChanged.emit()
        self.set_statusText(f"Đang tạo audio với {voice} ({style})...")
        
        # No model reference needed — subprocess loads its own model instance
        self.worker = TTSWorker(text, filepath, voice, style, parent=self)
        self.worker.resultReady.connect(self.on_generation_finished)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.start()

    @pyqtSlot(bool, str)
    def on_generation_finished(self, success, message):
        self._isGenerating = False
        self.isGeneratingChanged.emit()
        self.set_statusText(message if success else f"Error: {message}")
        
        # Clean up the Python reference to the worker. 
        # The C++ object will be deleted by the 'finished' signal connected to 'deleteLater'.
        if self.worker:
            self.worker = None

    @pyqtSlot()
    def cleanup(self):
        """Wait for the worker thread to finish when the application closes."""
        if self.worker and self.worker.isRunning():
            self.worker.wait()

if __name__ == "__main__":
    # Fix for PyInstaller subprocess (intercept tts_process.py execution)
    if len(sys.argv) > 1 and sys.argv[1].endswith("tts_process.py"):
        sys.argv.pop(0)  # Remove the executable from sys.argv
        import runpy
        try:
            runpy.run_path(sys.argv[0], run_name="__main__")
        except Exception as e:
            print(str(e), file=sys.stderr)
        sys.exit(0)

    app = QGuiApplication(sys.argv)
    engine = QQmlApplicationEngine()
    
    backend = Backend()
    engine.rootContext().setContextProperty("backend", backend)
    
    # Load model and expose preset voices
    backend.load_model()
    
    qml_file = BASE_DIR / "main.qml"
    engine.load(qml_file.as_uri())
    
    if not engine.rootObjects():
        sys.exit(-1)
        
    app.aboutToQuit.connect(backend.cleanup)
    
    # Close PyInstaller splash screen if it was built with one
    try:
        import pyi_splash
        pyi_splash.close()
    except ImportError:
        pass
    
    sys.exit(app.exec())
