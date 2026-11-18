"""Command-line transcription and setup check.

  python transcribe.py --download-only          # fetch the model and exit
  python transcribe.py --self-test              # transcribe the bundled samples
  python transcribe.py my_audio.wav [--language Persian]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import asr


def main() -> int:
    p = argparse.ArgumentParser(description="Qwen3-ASR-0.6B: language ID + transcription")
    p.add_argument("audio", nargs="*", help="audio files (wav, mp3, flac, ...)")
    p.add_argument("--language", default=None, help="force a language, e.g. English or Persian")
    p.add_argument("--device", default="auto", help="auto, cpu or cuda:0")
    p.add_argument("--download-only", action="store_true", help="download the model and exit")
    p.add_argument("--self-test", action="store_true", help="transcribe samples/ and check the language")
    args = p.parse_args()

    if args.download_only:
        asr.download_model()
        return 0

    asr.load_model(args.device)

    if args.self_test:
        samples_dir = Path(__file__).resolve().parent / "samples"
        samples = json.loads((samples_dir / "samples.json").read_text(encoding="utf-8"))
        ok = 0
        for s in samples:
            t0 = time.time()
            lang, text = asr.transcribe_file(str(samples_dir / s["file"]))
            good = lang == s["language"]
            ok += good
            print(f'{"OK  " if good else "MISS"} {s["language"]:<8} -> {lang:<10} {time.time() - t0:5.1f}s  {text[:70]}')
        print(f"SELF-TEST: {ok}/{len(samples)} languages detected correctly")
        return 0 if ok >= len(samples) - 1 else 1

    if not args.audio:
        p.print_help()
        return 2
    for f in args.audio:
        lang, text = asr.transcribe_file(f, args.language)
        print(f"[{lang}] {text}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
