"""
tts_process.py — Standalone worker script for TTS inference.

This script is executed by app.py as a separate subprocess for each generation request.
When the subprocess exits, the OS reclaims ALL memory including
ONNX Runtime internal pools — the only reliable way to prevent leaks.
"""
import sys
import os
from pathlib import Path

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print(f"Invalid arguments. Expected 5, got {len(sys.argv)}", file=sys.stderr)
        sys.exit(1)
        
    text_file = sys.argv[1]
    voice = sys.argv[2]
    style = sys.argv[3]
    filepath = sys.argv[4]
    
    try:
        with open(text_file, "r", encoding="utf-8") as f:
            text = f.read()

        if getattr(sys, 'frozen', False):
            base_dir = Path(sys._MEIPASS)
        else:
            base_dir = Path(__file__).resolve().parent
            
        os.environ["HF_HOME"] = str(base_dir / "hf_cache")
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"
        
        from vieneu import Vieneu
        model = Vieneu(backend="onnx")
        
        audio = model.infer(text, voice=voice, style=style)
        model.save(audio, filepath)
        
        # Must print exactly "OK" to stdout for app.py to detect success
        print("OK")
    except Exception as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
