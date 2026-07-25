# download_models.py
from pathlib import Path
import os
BASE_DIR = Path(__file__).resolve().parent

# Redirect HF cache to project-local folder — MUST be set before importing vieneu
os.environ.setdefault("HF_HOME", str(BASE_DIR / "hf_cache"))
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

import numpy as np

from vieneu import Vieneu

SAMPLE_RATE = 48_000
vieneu = None
def load_model():
    global vieneu
    cache_dir = Path(os.environ["HF_HOME"])
    if not cache_dir.exists():
        raise RuntimeError(f"HF cache not found at {cache_dir} — copy hf_cache folder first.")
    print("⏳ Loading VieNeu-TTS v3 Turbo (int8, CPU, local) ...")
    vieneu = Vieneu(
        backend="onnx",              # forces CPU/ONNX path explicitly — never tries CUDA
    )
    print(f"✅ Ready. Model: int8 | intra_op threads: {getattr(vieneu.engine, 'ort_intra_op_threads', '?')}")

load_model()


audio = vieneu.infer(
    "Trận Caen là một trận đánh trong Chiến tranh Trăm Năm giữa Anh và Pháp diễn ra vào ngày 26 tháng 7 năm 1346 khi quân viễn chinh Anh dưới sự chỉ huy của Edward III tấn công thành Caen do quân Pháp nắm giữ.",
    voice="Phạm Tuyên",
    style="tin_tuc",
)
vieneu.save(audio, "test.wav")
print("Model cached successfully.")
