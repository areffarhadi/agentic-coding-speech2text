# agentic-coding-speech2text — multilingual speech recognition on your CPU, set up by your coding agent

A local web UI that **identifies the spoken language and transcribes it**, using [Qwen/Qwen3-ASR-0.6B](https://huggingface.co/Qwen/Qwen3-ASR-0.6B). 30 languages. Runs on CPU, offline after setup.

Online demo: [huggingface.co/spaces/areffarhadi/qwen3-asr-multilingual](https://huggingface.co/spaces/areffarhadi/qwen3-asr-multilingual)

## Easiest way: let your coding agent do it

Give [`AGENT.md`](AGENT.md) to your coding agent (Claude Code, Codex, Cursor, …) and say:

> Follow AGENT.md and launch the UI for me.

The agent installs everything, downloads the model, runs a self-test and opens the UI.

## Manual setup

Requires Python 3.10–3.12, about 5 GB of disk and 8 GB of RAM.

```bash
git clone https://github.com/areffarhadi/agentic-coding-speech2text.git
cd agentic-coding-speech2text
python3 -m venv .venv
.venv/bin/pip install torch==2.8.0 --index-url https://download.pytorch.org/whl/cpu   # Linux/Windows; skip on macOS
.venv/bin/pip install -r requirements.txt
.venv/bin/python transcribe.py --self-test      # downloads the model on first run
.venv/bin/python app.py                         # opens http://127.0.0.1:7860
```

On Windows use `.venv\Scripts\python.exe` instead of `.venv/bin/python`.

## Command line

```bash
.venv/bin/python transcribe.py audio.wav                     # auto-detect language
.venv/bin/python transcribe.py audio.wav --language Persian  # force a language
```

Supported languages (official list from the [model card](https://huggingface.co/Qwen/Qwen3-ASR-0.6B)): Chinese, English, Cantonese, Arabic, German, French, Spanish, Portuguese, Indonesian, Italian, Korean, Russian, Thai, Vietnamese, Japanese, Turkish, Hindi, Malay, Dutch, Swedish, Danish, Finnish, Polish, Czech, Filipino, Persian, Greek, Romanian, Hungarian, Macedonian.

## License

Code: Apache-2.0. Model: Apache-2.0 (Qwen). Samples: [FLEURS](https://huggingface.co/datasets/google/fleurs) test split, CC-BY-4.0.
