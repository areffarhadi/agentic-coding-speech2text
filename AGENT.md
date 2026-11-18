# AGENT.md — set up and launch the local Qwen3-ASR speech-recognition UI

You are a coding agent working on the user's computer. The user gave you this file so that you prepare **everything** and **launch the UI for them**. They should not need to type any command.

Do every step below in order. Run the commands yourself. Check each step's result before you continue. If a step fails, use the **Troubleshooting** table, fix it, and retry. Only stop and ask the user when you need their permission (for example a system package install that needs `sudo` or an admin prompt).

## What you are installing

- A local web UI (Gradio) for multilingual speech recognition. It identifies the spoken language and transcribes it. 30 languages.
- Model: [Qwen/Qwen3-ASR-0.6B](https://huggingface.co/Qwen/Qwen3-ASR-0.6B), Apache-2.0. It runs on **CPU**. No GPU and no account or token are needed.
- Repository: `https://github.com/areffarhadi/qwen3-asr-local`

| Need | Amount |
|---|---|
| Disk | about 5 GB (1.9 GB model + about 2.5 GB Python packages) |
| RAM | 8 GB or more recommended |
| Python | 3.10, 3.11 or 3.12. **Not 3.13** (a dependency has no 3.13 wheel). |
| Internet | Only during setup. After setup everything runs offline. |
| Time | 5 to 20 minutes, mostly downloads |

## Step 0 — Detect the system

Find out the OS (Linux, macOS or Windows) and the shell. Use the matching commands below:

- **Linux / macOS**: bash or zsh commands.
- **Windows**: PowerShell commands. Use `.venv\Scripts\python.exe` wherever Linux uses `.venv/bin/python`.

## Step 1 — Prerequisites

1. **git**: run `git --version`. If missing, install it (Linux: the distro package manager, macOS: `xcode-select --install` or `brew install git`, Windows: `winget install --id Git.Git -e`).
2. **uv** (recommended, it also provides the right Python version): run `uv --version`. If missing, install it:
   - Linux / macOS: `curl -LsSf https://astral.sh/uv/install.sh | sh`, then open a new shell or run `source $HOME/.local/bin/env`.
   - Windows: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`, then open a new PowerShell.
   - If you cannot install uv, use the **plain venv fallback** in Step 3.
3. **ffmpeg** (optional, needed only for some uploaded formats such as `.m4a`, `.webm`, `.ogg`): run `ffmpeg -version`. If missing, install it if you can (Linux: `sudo apt-get install -y ffmpeg`, macOS: `brew install ffmpeg`, Windows: `winget install --id Gyan.FFmpeg -e`). If it needs a password and the user is not available, skip it. WAV, MP3 and FLAC work without it.

## Step 2 — Get the code

Choose a folder in the user's home directory (for example `~/qwen3-asr-local` or `%USERPROFILE%\qwen3-asr-local`).

```bash
git clone https://github.com/areffarhadi/qwen3-asr-local.git
cd qwen3-asr-local
```

If the folder already exists, `cd` into it and run `git pull` instead. Run **all following commands from inside this folder**.

## Step 3 — Create the Python environment and install packages

### With uv (recommended)

Linux / Windows (CPU build of torch, avoids a 3 GB CUDA download):

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv torch==2.8.0 --index-url https://download.pytorch.org/whl/cpu
uv pip install --python .venv -r requirements.txt
```

macOS (the normal torch wheel is already CPU-only):

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv -r requirements.txt
```

### Plain venv fallback (no uv)

Use an existing Python 3.10, 3.11 or 3.12 (check with `python3 --version`, or `py -3.12 --version` on Windows).

```bash
python3 -m venv .venv                      # Windows: py -3.12 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install torch==2.8.0 --index-url https://download.pytorch.org/whl/cpu   # skip this line on macOS
.venv/bin/python -m pip install -r requirements.txt
```

**Check**: `.venv/bin/python -c "import torch, qwen_asr, gradio; print('ok', torch.__version__)"` prints `ok 2.8.0...`.

## Step 4 — Download the model

```bash
.venv/bin/python transcribe.py --download-only
```

This saves the model to `./models/Qwen3-ASR-0.6B` (about 1.9 GB). It is skipped if the model is already there. On Windows use `.venv\Scripts\python.exe transcribe.py --download-only`.

## Step 5 — Self-test on CPU

```bash
.venv/bin/python transcribe.py --self-test --device cpu
```

It transcribes the 6 bundled FLEURS samples (English, Persian, Arabic, Chinese, French, German) and prints one line each. **Pass** = the last line says `SELF-TEST: 5/6` or `6/6`, and the command exits with code 0. It takes about 5 to 30 seconds per sample, depending on the CPU.

## Step 6 — Launch the UI for the user

Start the app as a **long-running background process** (it must keep running after your command returns), and write its log to `app.log`:

- Linux / macOS:
  ```bash
  nohup .venv/bin/python app.py --device cpu > app.log 2>&1 &
  ```
- Windows (PowerShell):
  ```powershell
  Start-Process -FilePath ".venv\Scripts\python.exe" -ArgumentList "app.py","--device","cpu" -RedirectStandardOutput app.log -RedirectStandardError app.err.log -WindowStyle Hidden
  ```

Wait until the page answers (usually 10 to 60 seconds; the model loads first). Check every few seconds: `curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:7860` returns `200` (Windows: `(Invoke-WebRequest http://127.0.0.1:7860 -UseBasicParsing).StatusCode`). `app.log` then contains `Running on local URL`. If the process exits instead, read `app.log` (and `app.err.log` on Windows) and use the Troubleshooting table.

The app opens a browser tab by itself. If it did not, open **http://127.0.0.1:7860** for the user (Linux: `xdg-open`, macOS: `open`, Windows: `start`).

If port 7860 is busy, add `--port 7861` (or another free port) and use that port in the URL.

## Step 7 — Tell the user

Reply to the user with a short message:

- The UI is running at **http://127.0.0.1:7860**.
- How to use it: record with the microphone, upload a file, or click one of the 6 sample clips, then press **Transcribe**. The detected language and the transcript are shown. The Language dropdown can force a language instead of auto-detect.
- How to start it again later: from the `qwen3-asr-local` folder run `.venv/bin/python app.py` (Windows: `.venv\Scripts\python.exe app.py`).
- How to stop it: close the terminal, or stop the `app.py` process (Linux / macOS: `pkill -f "python app.py"`).
- The self-test result from Step 5.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `No matching distribution` for `nagisa`, or a build error while installing | Python is 3.13 or newer. Recreate the env with Python 3.12 (`uv venv --python 3.12 .venv`). |
| pip starts downloading `nvidia-*` / CUDA packages (several GB) | torch was installed from PyPI on Linux/Windows. Run the CPU torch command from Step 3 first, then `requirements.txt` again. |
| `OSError: libsndfile` / `sndfile library not found` (Linux) | `sudo apt-get install -y libsndfile1`, then retry. |
| Model download fails or is very slow | Retry `transcribe.py --download-only` (it resumes). Behind a proxy, set `HTTPS_PROXY`. In regions where huggingface.co is blocked, set `HF_ENDPOINT=https://hf-mirror.com`. |
| `Killed` or out-of-memory while loading | Close other programs. The model needs about 3 GB of free RAM in float32. |
| Microphone does not work in the browser | Use `http://127.0.0.1:7860` or `http://localhost:7860` (browsers only allow the mic on localhost or HTTPS) and allow the mic permission prompt. |
| `Address already in use` | Another app uses 7860. Start with `--port 7861`. |
| Uploaded `.m4a` / `.webm` / `.ogg` fails | Install ffmpeg (Step 1.3), then restart the app. |
| A GPU is available and the user wants it | Install the CUDA torch build instead of the CPU one and start with `--device cuda:0`. CPU is the default and is enough for this model. |

## Files in this repo

| File | Purpose |
|---|---|
| `app.py` | The web UI (same layout as the online demo). Options: `--host`, `--port`, `--device`, `--share`, `--no-browser`. |
| `asr.py` | Model download, loading and transcription. |
| `transcribe.py` | Command line: `--download-only`, `--self-test`, or `python transcribe.py file.wav [--language Persian]`. |
| `requirements.txt` | Python packages. |
| `samples/` | 6 FLEURS test clips (CC-BY-4.0). |
