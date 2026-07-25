# Comprehensive Project Log: Offline Text-to-Speech (TTS) Desktop App

This document serves as the complete, exhaustive record of the entire development, debugging, and production packaging process for the PyQt6 + QtQuick Offline TTS application based on the `vieneu` model.

---

## 1. Project Inception & Requirements
The goal was to convert a simple python script (`develop.py`) into a fully offline Windows Desktop GUI application capable of generating audio from Vietnamese text using the HuggingFace `vieneu` model.
*   **Offline Requirement**: The app needed to rely entirely on a local `hf_cache` directory located next to the script.
*   **UI Requirement**: A modern interface built with **PyQt6** and **QtQuick (QML)**.
*   **Features Required**:
    *   Text input capable of handling 100,000+ characters.
    *   Folder selector and filename input for outputting `.wav` files.
    *   Drop-down selection for Voice and Style.
    *   Non-blocking "Generate" button so the UI remains responsive during generation.

---

## 2. Core Architecture Implementation

### The Frontend (`main.qml`)
We built a hardware-accelerated, dark-themed UI using QML.
*   **Controls Used**: `ApplicationWindow`, `ColumnLayout`, `RowLayout`, `TextField`, `TextArea`, `ComboBox`, `Button`.
*   **FolderDialog**: Utilized `QtQuick.Dialogs` to open a native Windows folder picker for the save location.
*   **State Management**: Bound the "Generate Audio" button's enabled state to `!backend.isGenerating && backend.isModelLoaded`. The status label color dynamically changes (green for ready, yellow for generating, red for errors).

### The Backend (`app.py`)
*   **Environment Lock-down**: To guarantee 100% offline usage, the script sets `HF_HOME`, `HF_HUB_OFFLINE`, and `TRANSFORMERS_OFFLINE` to force HuggingFace libraries to strictly read from `hf_cache` before any model is imported.
*   **PyInstaller Path Handling**: Used `sys._MEIPASS` check to dynamically adjust `BASE_DIR` so `hf_cache` is found correctly both in the IDE and when running as a compiled `.exe`.
*   **Threading**: Implemented `TTSWorker` (inheriting from `QThread`) to run `vieneu.infer(...)` in the background. It emits a `finished` signal with success state and messages back to the main thread.
*   **QML Bridge**: Created a `Backend` class inheriting from `QObject` with `@pyqtSlot` (callable from QML) and `@pyqtProperty` (variables QML can read and bind to).

---

## 3. Bug Fixes During Development

### Bug 1: PyQt6 QtQuick Controls Crash
*   **Error**: `Cannot load library qtquickcontrols2windowsstyleimplplugin.dll: The specified module could not be found.`
*   **Cause**: PyQt6 on Windows often fails to load the native Windows style plugin for QML Controls.
*   **Solution**: Forced the app to bypass the Windows plugin by adding `os.environ["QT_QUICK_CONTROLS_STYLE"] = "Basic"` at the top of `app.py`.

### Bug 2: Empty Voice Selection / Binding Failure
*   **Error**: QML failed to extract the `vid` and `label` from the Python list of dictionaries passed to `voiceList`.
*   **Cause**: QML's `ComboBox` `textRole` and `valueRole` do not automatically map to Python lists of dictionaries (`QVariantList` of dicts) without a heavy `QAbstractListModel` wrapper.
*   **Solution**: Split the data into two simple lists: `voiceLabels` (bound directly to the ComboBox model) and `voiceVids` (used internally by Python). QML simply passes `backend.voiceVids[voiceComboBox.currentIndex]` back to Python when generating.

### Bug 3: Model Tuple Indices Error
*   **Error**: `model error: tuple indicies must be integers or slices, not str`
*   **Cause**: We assumed `vieneu.list_preset_voices()` returned dictionaries (`v["label"]`). It actually returns a list of tuples: `('Minh Đức — ...', 'Minh Đức')`.
*   **Solution**: Updated the list comprehension in `app.py` to use tuple indexing: `v[0]` for the label and `v[1]` for the `vid`.

---

## 4. Production Packaging

To distribute the app to users without Python installed, we established a two-stage build process.

### Stage 1: PyInstaller Compilation (`build.spec`)
We needed to package the python environment into a standalone folder.
*   **Configuration**: We used `--onedir` mode (as opposed to `--onefile`) because extracting a 285MB model cache to a Temp folder on every startup would be unacceptably slow.
*   **Data Bundling**: Explicitly mapped `hf_cache` and `main.qml` in the `datas` array so PyInstaller copies them next to the `.exe`.

### Stage 2: Inno Setup (`installer.iss`)
*   **Configuration**: We wrote a script that compresses the entire PyInstaller `dist/OfflineTTS` folder using `lzma2/ultra64` compression.
*   **Output**: Produces a single `OfflineTTS_Setup.exe` that creates Start Menu shortcuts, Desktop icons, and installs the software cleanly into the user's Program Files.

---

## 5. Post-Compilation Bugs & Fixes

### Bug 4: Empty Voice Dropdown in the Compiled `.exe`
*   **Error**: The UI loaded, but the Voice dropdown was blank.
*   **Cause**: The `vieneu` package relies on internal text/JSON files inside its `assets` folder to list voices. PyInstaller ignores non-python files inside `site-packages` by default.
*   **Solution**: Imported `collect_data_files` from `PyInstaller.utils.hooks` and added `collect_data_files('vieneu')` to the `build.spec` to bundle the missing assets.

### Bug 5: Inno Setup Deprecation Warning
*   **Error**: `Warning: Constant "pf" has been renamed.`
*   **Cause**: Inno Setup 6+ deprecated `{pf}` (Program Files).
*   **Solution**: Replaced `{pf}` with the modern `{autopf}` constant in `installer.iss`.

### Bug 6: Rust 'OS Error 2' During Audio Generation
*   **Error**: Clicking "Generate Audio" threw `The system can not find the file specified (os error 2)`.
*   **Cause**: `os error 2` from Rust indicates a missing file. The Grapheme-to-Phoneme converter library (`sea_g2p`), which is a dependency of `vieneu`, required a massive 50MB internal file called `sea_g2p.bin`. PyInstaller stripped this `.bin` file out of the compiled package.
*   **Solution**: Added `collect_data_files('sea_g2p')` to the `build.spec` to ensure the binary dictionary was packaged alongside the application.

---
## Final Build Commands
To generate a clean production release:
1. `del /s /q build dist` (Clean old cache)
2. `.venv\Scripts\pyinstaller --clean build.spec`
3. Compile `installer.iss` in Inno Setup.
