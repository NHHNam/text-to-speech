import os

# Point HF_HOME at the local project folder before importing anything from huggingface_hub
os.environ["HF_HOME"] = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hf_cache")

from huggingface_hub import snapshot_download

models = [
    "pnnbao-ump/VieNeu-TTS-0.3B",
    "neuphonic/distill-neucodec",
    "pnnbao-ump/VieNeu-TTS-v3-Turbo",
    "OpenMOSS-Team/MOSS-Audio-Tokenizer-Nano-ONNX",
]

for repo_id in models:
    print(f"Downloading {repo_id} ...")
    path = snapshot_download(repo_id)
    print(f"✅ {repo_id} -> {path}")

print("\nAll models downloaded.")
print(f"Cache location: {os.environ['HF_HOME']}")
