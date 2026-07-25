"""
tts_process.py — Persistent worker process for TTS inference.

This process is spawned ONCE when the app starts. It loads the model once,
then waits for jobs from the main app via a multiprocessing Queue.
After each inference, the audio array is explicitly deleted to keep memory stable.
"""
import os
import sys
from pathlib import Path

def worker_main(request_queue, result_queue, base_dir: str):
    """
    Runs in the worker process.
    Loads the model once, then loops waiting for generation jobs.
    """
    base = Path(base_dir)
    os.environ.setdefault("HF_HOME", str(base / "hf_cache"))
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"

    try:
        from vieneu import Vieneu
        model = Vieneu(backend="onnx")
        result_queue.put(("ready", None))
    except Exception as e:
        result_queue.put(("error", str(e)))
        return

    # Main job loop — stays alive for the duration of the app
    while True:
        job = request_queue.get()

        # Poison pill — shut down cleanly
        if job is None:
            break

        text, voice, style, filepath = job
        try:
            audio = model.infer(text, voice=voice, style=style)
            model.save(audio, filepath)
            # Explicitly free the large audio array immediately after saving
            del audio
            result_queue.put(("ok", filepath))
        except Exception as e:
            result_queue.put(("error", str(e)))
