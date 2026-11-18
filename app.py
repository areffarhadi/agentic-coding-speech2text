"""Local web UI: multilingual speech recognition with language ID (Qwen3-ASR-0.6B, CPU).

  python app.py                 # opens http://127.0.0.1:7860
  python app.py --port 8000 --device cpu
"""

from __future__ import annotations

import argparse
import html
import json
import os
import sys
import time

import gradio as gr

from asr import LANGUAGES, MAX_SECONDS, MODEL_ID, SR, load_model, read_audio, transcribe_array

AUTO = "Auto-detect"
HERE = os.path.dirname(os.path.abspath(__file__))
SAMPLES_DIR = os.path.join(HERE, "samples")
try:
    with open(os.path.join(SAMPLES_DIR, "samples.json"), encoding="utf-8") as fh:
        SAMPLES = sorted(json.load(fh), key=lambda x: x["language"])
except FileNotFoundError:
    SAMPLES = []


def _language_html(lang: str) -> str:
    if not lang:
        return '<div class="lang-card empty">Language will appear here.</div>'
    chips = []
    for name in [x.strip() for x in lang.split(",") if x.strip()]:
        native, code = LANGUAGES.get(name, ("", ""))
        native_part = f'<span class="native">{html.escape(native)}</span>' if native and native != name else ""
        code_part = f'<span class="code">{html.escape(code)}</span>' if code else ""
        chips.append(f'<span class="chip"><b>{html.escape(name)}</b>{native_part}{code_part}</span>')
    return f'<div class="lang-card">{"".join(chips)}</div>'


def transcribe(audio_path: str | None, language_choice: str):
    if not audio_path:
        return _language_html(""), "", "Record or upload audio first."
    try:
        audio, trimmed = read_audio(audio_path)
    except Exception as exc:  # noqa: BLE001
        return _language_html(""), "", f"Could not read that audio ({exc}). Try WAV, MP3, or FLAC."
    if audio.size < int(0.3 * SR):
        return _language_html(""), "", "That clip is shorter than 0.3 seconds. Record a little more speech."
    forced = None if language_choice in (None, "", AUTO) else language_choice
    t0 = time.time()
    try:
        lang, text = transcribe_array(audio, forced)
    except Exception as exc:  # noqa: BLE001
        return _language_html(""), "", f"Transcription failed ({exc})."
    if forced and not lang:
        lang = forced
    note = f"{audio.shape[0] / SR:.1f}s audio · {time.time() - t0:.1f}s on {DEVICE} · "
    note += "language forced" if forced else "language auto-detected"
    if trimmed:
        note += f" · trimmed to the first {MAX_SECONDS // 60} minutes"
    if not text:
        note += " · no speech found"
    return _language_html(lang), text, note


DEVICE = "cpu"



def _supported_md() -> str:
    langs = ", ".join(f"{name} ({code})" for name, (_native, code) in LANGUAGES.items())
    return (
        "### Supported languages\n"
        "Official list from the [Qwen3-ASR-0.6B model card](https://huggingface.co/Qwen/Qwen3-ASR-0.6B): "
        "30 languages, all with automatic language identification.\n\n"
        f"**Languages (30):** {langs}"
    )


theme = gr.themes.Soft(
    primary_hue=gr.themes.colors.blue,
    secondary_hue=gr.themes.colors.slate,
    neutral_hue=gr.themes.colors.slate,
    font=[gr.themes.GoogleFont("Inter"), "sans-serif"],
).set(
    body_background_fill="#ffffff",
    body_text_color="#0f172a",
    block_background_fill="#ffffff",
    block_border_color="#94a3b8",
    block_border_width="1px",
    block_label_background_fill="#f8fafc",
    block_label_border_width="0px",
    block_label_text_color="#0f172a",
    block_radius="8px",
    block_title_text_color="#0f172a",
    body_text_color_subdued="#334155",
    input_background_fill="#f8fafc",
    button_primary_background_fill="#1d4ed8",
    button_primary_background_fill_hover="#1e40af",
    button_primary_text_color="#ffffff",
    button_primary_border_color="#1d4ed8",
    shadow_drop="0 1px 2px rgba(15, 23, 42, 0.06)",
)

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Vazirmatn:wght@400;500;600&display=swap');

.gradio-container {max-width: 1080px !important;}
.header-copy, .footer-copy {
  border: none !important;
  background: transparent !important;
  box-shadow: none !important;
  padding: 0 !important;
}
.header-copy {margin-bottom: 8px !important;}
.header-copy h1 {font-size: 1.35rem; line-height: 1.5; font-weight: 600; margin: 0;}
.header-copy p {margin: 4px 0 0; color: #334155;}
.footer-copy {margin-top: 8px !important;}
.panel-col {gap: 16px !important;}
.field {
  border: 1px solid #94a3b8 !important;
  border-radius: 8px !important;
  background: #ffffff !important;
  overflow: hidden;
}
.lang-box {border: none !important; background: transparent !important; padding: 0 !important;}
.lang-card {
  display: flex; flex-wrap: wrap; gap: 8px; align-items: center;
  min-height: 56px; padding: 10px 12px;
  border: 1px solid #94a3b8; border-radius: 8px; background: #f8fafc;
}
.lang-card.empty {color: #475569;}
.lang-card .chip {
  display: inline-flex; gap: 8px; align-items: baseline;
  padding: 6px 12px; border-radius: 999px;
  background: #dbeafe; color: #1e3a8a; font-size: 1.05rem;
}
.lang-card .native {font-family: Vazirmatn, Inter, sans-serif;}
.lang-card .code {
  font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.04em;
  color: #1d4ed8; background: #ffffff; padding: 1px 6px; border-radius: 4px;
}
/* follow the text's own direction: RTL for Persian / Arabic, LTR otherwise */
.transcript textarea {
  unicode-bidi: plaintext;
  text-align: start;
  font-family: Inter, Vazirmatn, sans-serif;
  font-size: 1.125rem;
  line-height: 1.8;
}
button, a {cursor: pointer;}
a {color: #1d4ed8;}
button:focus-visible, a:focus-visible, textarea:focus-visible, input:focus-visible, select:focus-visible {
  outline: 2px solid #1d4ed8;
  outline-offset: 2px;
}
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {animation: none !important; transition: none !important;}
}
"""

PAGE_TITLE = "🌍 Multilingual Speech Recognition — Qwen3-ASR-0.6B"

with gr.Blocks(theme=theme, css=CSS, title=PAGE_TITLE) as demo:
    gr.Markdown(
        f"# {PAGE_TITLE}\nThe model identifies the spoken language, then transcribes it. 30 languages. Runs locally on your computer.",
        elem_classes=["header-copy"],
    )
    with gr.Row(equal_height=False):
        with gr.Column(scale=1, min_width=320, elem_classes=["panel-col"]):
            audio = gr.Audio(
                sources=["microphone", "upload"],
                type="filepath",
                label=f"Speech, up to {MAX_SECONDS // 60} minutes",
                elem_classes=["field"],
            )
            language = gr.Dropdown(
                choices=[AUTO, *LANGUAGES],
                value=AUTO,
                label="Language",
                info="Leave on Auto-detect to let the model identify it.",
                elem_classes=["field"],
            )
            button = gr.Button("Transcribe", variant="primary")
        with gr.Column(scale=1, min_width=320, elem_classes=["panel-col"]):
            detected = gr.HTML(_language_html(""), label="Detected language", elem_classes=["lang-box"])
            transcript = gr.Textbox(
                label="Transcript",
                lines=10,
                interactive=False,
                show_copy_button=True,
                elem_classes=["field", "transcript"],
            )
            status = gr.Textbox(
                label="Status",
                value="Waiting for audio.",
                lines=1,
                interactive=False,
                elem_classes=["field"],
            )
    if SAMPLES:
        gr.Examples(
            examples=[[os.path.join(SAMPLES_DIR, x["file"])] for x in SAMPLES],
            example_labels=[
                f'{x["language"]} · {LANGUAGES.get(x["language"], ("", ""))[0]} · {x["seconds"]:.0f}s'
                if LANGUAGES.get(x["language"], ("", ""))[0] != x["language"]
                else f'{x["language"]} · {x["seconds"]:.0f}s'
                for x in SAMPLES
            ],
            inputs=[audio],
            label="FLEURS samples (test split). Pick one, then press Transcribe. Or use the microphone above.",
            examples_per_page=10,
        )
    gr.Markdown(_supported_md(), elem_classes=["footer-copy"])
    gr.Markdown(
        f"""
Samples: [FLEURS](https://huggingface.co/datasets/google/fleurs) test split (CC-BY-4.0).

Model: [{MODEL_ID}](https://huggingface.co/{MODEL_ID}) (Apache-2.0) · Online demo: [Hugging Face Space](https://huggingface.co/spaces/areffarhadi/qwen3-asr-multilingual) · Running locally on your machine.
        """,
        elem_classes=["footer-copy"],
    )
    button.click(transcribe, inputs=[audio, language], outputs=[detected, transcript, status])

if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(line_buffering=True)  # so app.log shows progress immediately
    except Exception:  # noqa: BLE001
        pass
    ap = argparse.ArgumentParser(description="Local Qwen3-ASR web UI")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=7860)
    ap.add_argument("--device", default="cpu", help="cpu (default), cuda:0 or auto")
    ap.add_argument("--share", action="store_true", help="also create a public gradio.live link")
    ap.add_argument("--no-browser", action="store_true", help="do not open a browser tab")
    args = ap.parse_args()
    from asr import pick_device

    DEVICE = pick_device(args.device)
    load_model(DEVICE)  # downloads the model on first run, then loads it before the UI starts
    print(f"Open http://{'127.0.0.1' if args.host == '0.0.0.0' else args.host}:{args.port} in your browser.", flush=True)
    demo.queue(max_size=16).launch(
        server_name=args.host,
        server_port=args.port,
        share=args.share,
        inbrowser=not args.no_browser,
    )
