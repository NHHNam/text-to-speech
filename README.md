# Offline Text-to-Speech (Vietnamese) Desktop App

Chuyển đổi văn bản thành giọng nói — a fully **offline** Windows desktop application that converts Vietnamese text into natural-sounding speech, built with **PyQt6 + QtQuick (QML)** and the [`vieneu`](https://pypi.org/project/vieneu/) TTS model running on the ONNX backend. It created base on [`VieNeu-TTS`](https://github.com/pnnbao97/VieNeu-TTS).

## Features

- 🔌 **100% offline** — the HuggingFace model cache (`hf_cache`) is loaded locally; `HF_HUB_OFFLINE` and `TRANSFORMERS_OFFLINE` are forced on, so no internet connection is required after the model is cached.
- 🖥️ **Modern dark-themed UI** built with QtQuick/QML (`main.qml`).
- 📝 Large text input, capable of handling 100,000+ characters.
- 📁 Folder picker and filename field for saving generated `.wav` files.
- 🎙️ Voice and style selection via drop-down menus.
- ⚡ **Non-blocking generation** — inference runs in a persistent background worker process, so the UI stays responsive and the model is loaded only once per session.

## Project structure

| File                | Description                                                                                                                                                   |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `app.py`            | Main entry point. Boots the PyQt6/QML application, spawns the persistent TTS worker process, and exposes a `Backend` bridge (QObject) between Python and QML. |
| `main.qml`          | The QtQuick UI: text input, folder/filename selectors, voice/style dropdowns, and the generate button.                                                        |
| `tts_process.py`    | Persistent worker process. Loads the `vieneu` model once and processes generation jobs sent over a multiprocessing queue.                                     |
| `server.py`         | Optional server-side entry point/API for the TTS engine.                                                                                                      |
| `develop.py`        | Original standalone script the desktop app was built from — useful for quick local testing without the GUI.                                                   |
| `dump_voices.py`    | Utility script to list/inspect the voices available in the loaded `vieneu` model.                                                                             |
| `voices_output.txt` | Sample output of the available voice list.                                                                                                                    |
| `build.spec`        | PyInstaller spec used to package the app into a standalone `--onedir` build (bundles `hf_cache`, `main.qml`, and required `vieneu`/`sea_g2p` data files).     |
| `installer.iss`     | Inno Setup script used to build a Windows installer (`OfflineTTS_Setup.exe`) from the PyInstaller output.                                                     |
| `WRITE.md`          | Full development log documenting the architecture, bugs encountered, and their fixes.                                                                         |

## Requirements

- Python 3.10+ (recommended)
- Windows is the primary target platform (native folder dialogs, PyInstaller/Inno Setup packaging), though the Python/PyQt6 core should run cross-platform.
- See [`requirements.txt`](./requirements.txt) for Python dependencies.

## Setup

1. Clone the repository:

   ```bash
   git clone https://github.com/NHHNam/text-to-speech.git
   cd text-to-speech
   ```

2. Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   .venv\Scripts\activate      # Windows
   source .venv/bin/activate   # macOS/Linux
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Make sure a local HuggingFace cache exists at `hf_cache/` next to the project root (populated automatically the first time `vieneu` downloads the model — or copy a pre-downloaded cache there for a fully offline setup).

## Usage

Run the desktop app:

```bash
python app.py
```

On first launch, the app loads the `vieneu` model (this may take a moment). Once ready:

1. Type or paste text into the text area.
2. Choose an output folder and filename.
3. Select a voice and style from the drop-downs.
4. Click **Generate Audio** — generation runs in the background worker process, so the UI stays responsive.
5. The resulting `.wav` file is saved to your chosen location.

To inspect available voices without launching the GUI:

```bash
python dump_voices.py
```

## Building a standalone Windows installer

The project ships with a two-stage production build process (see `WRITE.md` for full details):

1. **PyInstaller** — package the app and its dependencies (including `vieneu` and `sea_g2p` data files) into a standalone folder:

   ```bash
   pyinstaller --clean build.spec
   ```

2. **Inno Setup** — compile `installer.iss` (in the Inno Setup IDE or via `iscc`) to produce a single `OfflineTTS_Setup.exe` installer with Start Menu/Desktop shortcuts.

## Notes

- The app forces `QT_QUICK_CONTROLS_STYLE=Basic` to avoid a known PyQt6 crash on Windows when the native Windows QtQuick Controls style plugin is missing.
- `HF_HOME`, `HF_HUB_OFFLINE`, and `TRANSFORMERS_OFFLINE` are set before any model import to guarantee strictly offline model loading from `hf_cache`.

## License

No license file is currently included in the repository. Check with the repository owner ([NHHNam](https://github.com/NHHNam)) before reuse or redistribution.
