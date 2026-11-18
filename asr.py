"""Model download, loading and inference for Qwen3-ASR-0.6B (CPU by default)."""

from __future__ import annotations

import os
import threading
from pathlib import Path

import numpy as np
import torch

MODEL_ID = "Qwen/Qwen3-ASR-0.6B"
ROOT = Path(__file__).resolve().parent
MODEL_DIR = Path(os.environ.get("QWEN3_ASR_MODEL_DIR", ROOT / "models" / "Qwen3-ASR-0.6B"))
SR = 16_000
MAX_SECONDS = 10 * 60

# Canonical Qwen3-ASR language names -> (native name, ISO code)
LANGUAGES = {
    "Chinese": ("中文", "zh"),
    "English": ("English", "en"),
    "Cantonese": ("粵語", "yue"),
    "Arabic": ("العربية", "ar"),
    "German": ("Deutsch", "de"),
    "French": ("Français", "fr"),
    "Spanish": ("Español", "es"),
    "Portuguese": ("Português", "pt"),
    "Indonesian": ("Bahasa Indonesia", "id"),
    "Italian": ("Italiano", "it"),
    "Korean": ("한국어", "ko"),
    "Russian": ("Русский", "ru"),
    "Thai": ("ไทย", "th"),
    "Vietnamese": ("Tiếng Việt", "vi"),
    "Japanese": ("日本語", "ja"),
    "Turkish": ("Türkçe", "tr"),
    "Hindi": ("हिन्दी", "hi"),
    "Malay": ("Bahasa Melayu", "ms"),
    "Dutch": ("Nederlands", "nl"),
    "Swedish": ("Svenska", "sv"),
    "Danish": ("Dansk", "da"),
    "Finnish": ("Suomi", "fi"),
    "Polish": ("Polski", "pl"),
    "Czech": ("Čeština", "cs"),
    "Filipino": ("Filipino", "fil"),
    "Persian": ("فارسی", "fa"),
    "Greek": ("Ελληνικά", "el"),
    "Romanian": ("Română", "ro"),
    "Hungarian": ("Magyar", "hu"),
    "Macedonian": ("Македонски", "mk"),
}

_model = None
_lock = threading.Lock()


def pick_device(requested: str = "auto") -> str:
    if requested != "auto":
        return requested
    return "cuda:0" if torch.cuda.is_available() else "cpu"


def download_model() -> Path:
    """Download the model once into ./models (skipped when it is already there)."""
    if (MODEL_DIR / "config.json").exists() and any(MODEL_DIR.glob("*.safetensors")):
        return MODEL_DIR
    from huggingface_hub import snapshot_download

    print(f"Downloading {MODEL_ID} to {MODEL_DIR} (about 1.9 GB, first run only) ...", flush=True)
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    snapshot_download(MODEL_ID, local_dir=str(MODEL_DIR))
    print("Download complete.", flush=True)
    return MODEL_DIR


def load_model(device: str = "auto"):
    global _model
    if _model is not None:
        return _model
    from qwen_asr import Qwen3ASRModel

    path = download_model()
    device = pick_device(device)
    dtype = torch.bfloat16 if device.startswith("cuda") else torch.float32
    print(f"Loading model on {device} ({str(dtype).replace('torch.', '')}) ...", flush=True)
    kwargs = dict(dtype=dtype, device_map=device, max_inference_batch_size=1, max_new_tokens=512)
    try:
        _model = Qwen3ASRModel.from_pretrained(str(path), attn_implementation="sdpa", **kwargs)
    except TypeError:
        _model = Qwen3ASRModel.from_pretrained(str(path), **kwargs)
    print("Model ready.", flush=True)
    return _model


def read_audio(path: str) -> tuple[np.ndarray, bool]:
    import librosa

    audio, _ = librosa.load(path, sr=SR, mono=True)
    audio = np.asarray(audio, dtype=np.float32)
    limit = MAX_SECONDS * SR
    if audio.shape[0] > limit:
        return audio[:limit], True
    return audio, False


def transcribe_array(audio: np.ndarray, language: str | None = None) -> tuple[str, str]:
    """Returns (language, text). language=None means auto-detect."""
    with _lock:
        results = load_model().transcribe(audio=(audio, SR), language=language)
    if not results:
        return "", ""
    first = results[0]
    return (getattr(first, "language", "") or "").strip(), (getattr(first, "text", "") or "").strip()


def transcribe_file(path: str, language: str | None = None) -> tuple[str, str]:
    audio, _ = read_audio(path)
    return transcribe_array(audio, language)
