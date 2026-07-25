import os
os.environ["HF_HOME"] = "hf_cache"
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

from vieneu import Vieneu
model = Vieneu(backend="onnx")
voices = model.list_preset_voices()
with open("voices_output.txt", "w", encoding="utf-8") as f:
    f.write(repr(voices))
