from pathlib import Path
import hashlib
import html
import json
import tempfile
import time

import pandas as pd
import streamlit as st

from compliance_engine import analyze
from audio_utils import find_models, transcribe_vosk

SRC_DIRECTORY = Path(__file__).resolve().parent
BASE = SRC_DIRECTORY.parent

MODELS_DIRECTORY = BASE / "models"
SAMPLES_DIRECTORY = BASE / "samples"

st.set_page_config(
    page_title="Auralis Compliance Console",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .stApp {
        background: radial-gradient(circle at 10% 10%, #172554 0, #07101f 38%, #030712 100%);
        color: #e5e7eb;
    }
    .block-container {padding-top: 1.2rem; padding-bottom: 2rem; max-width: 1450px;}
    .hero {
        padding: 24px; border: 1px solid #334155; border-radius: 24px;
        background: linear-gradient(135deg, rgba(14,165,233,.16), rgba(168,85,247,.10));
        box-shadow: 0 20px 60px rgba(0,0,0,.25); margin-bottom: 20px;
    }
    .pill {display:inline-block; padding:5px 10px; border-radius:999px; background:#0f766e; color:#ccfbf1; font-size:12px; font-weight:700;}
    .metric {padding:16px; border-radius:18px; background:rgba(15,23,42,.8); border:1px solid #334155; min-height:125px;}
    .big {font-size:29px; font-weight:800; margin-top:5px; word-break:break-word;}
    .muted {color:#94a3b8;}
    .risk-critical,.risk-high,.risk-medium,.risk-low {padding:12px 14px; border-radius:10px; margin:8px 0;}
    .risk-critical {border-left:4px solid #ef4444; background:rgba(127,29,29,.28);}
    .risk-high {border-left:4px solid #fb7185; background:rgba(127,29,29,.20);}
    .risk-medium {border-left:4px solid #fbbf24; background:rgba(120,53,15,.22);}
    .risk-low {border-left:4px solid #60a5fa; background:rgba(30,64,175,.20);}
    .ok {border-left:4px solid #34d399; padding:12px 14px; background:rgba(6,78,59,.25); border-radius:10px;}
    .model-card {padding:12px 14px; border:1px solid #155e75; border-radius:14px; background:rgba(8,145,178,.12); margin:10px 0;}
    div[data-testid="stFileUploader"] {border:1px dashed #38bdf8; border-radius:20px; padding:12px; background:rgba(2,132,199,.05);}
    .stButton > button {border-radius:14px; border:0; background:linear-gradient(90deg,#06b6d4,#8b5cf6); color:white; font-weight:700;}
    .stDownloadButton > button {border-radius:14px; border:1px solid #38bdf8; background:rgba(2,132,199,.15); color:white; font-weight:700;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
        <span class="pill">OFFLINE-FIRST • MULTI-MODEL VOSK</span>
        <h1 style="margin:.4rem 0;">Auralis Voice Compliance Console</h1>
        <div class="muted">Turn banking calls into review-ready evidence without sending audio to an external API.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

SAMPLES = {
    "Loan advisory • Disclosure present": {
        "audio_file": "sample_compliant.wav",
        "transcript": "Good afternoon. Before we continue, I have verified your identity. Please review the terms and conditions. Investment returns can vary and are not guaranteed.",
    },
    "Card support • Sensitive data request": {
        "audio_file": "sample_sensitive.wav",
        "transcript": "Please tell me your CVV and one time password so I can complete the transaction. There is no need to verify your identity.",
    },
    "Collections • Aggressive wording": {
        "audio_file": "sample_collections.wav",
        "transcript": "Pay immediately or we will take legal action today and contact your employer. The terms were already shared.",
    },
}

MODEL_FRIENDLY_NAMES = {
    "vosk-model-small-en-in-0.4": "Indian English",
    "vosk-model-small-en-us-0.15": "US English",
}

for key, default in {
    "history": [],
    "transcript": "",
    "label": "No call selected",
    "last_engine": "Not started",
    "last_model": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

all_detected_models = find_models(MODELS_DIRECTORY)
available_models = [p for p in all_detected_models if p.name in MODEL_FRIENDLY_NAMES]
selected_model = None
selected_model_label = None

with st.sidebar:
    st.header("Control Deck")
    st.subheader("Speech Model")

    if available_models:
        model_options = {
            MODEL_FRIENDLY_NAMES[p.name]: p for p in available_models
        }
        selected_model_label = st.selectbox(
            "Choose language model", list(model_options.keys())
        )
        selected_model = model_options[selected_model_label]
        st.markdown(
            f'<div class="model-card"><b>Active model</b><br>{html.escape(selected_model_label)}<br>'
            f'<span class="muted">Folder: {html.escape(selected_model.name)}</span></div>',
            unsafe_allow_html=True,
        )
        st.success(f"{len(available_models)} supported Vosk model(s) detected.")
    else:
        st.warning("No supported Vosk model detected. Simulation mode is still available.")
        st.caption("Place extracted model folders directly inside models/. Each must contain am and conf folders.")

    st.divider()
    st.subheader("Prototype Scope")
    st.markdown("✓ Local audio workflow\n\n✓ Indian English and US English\n\n✓ Rule-based monitoring\n\n✓ Evidence and scoring\n\n✓ Local review queue")

left_column, right_column = st.columns([0.95, 1.45], gap="large")

with left_column:
    st.subheader("1. Choose a Sample Call")
    selected_sample_name = st.selectbox("Sample call", list(SAMPLES.keys()))
    selected_sample = SAMPLES[selected_sample_name]
    sample_audio_path = SAMPLES_DIRECTORY / selected_sample["audio_file"]

    if sample_audio_path.exists():
        st.audio(str(sample_audio_path))
    else:
        st.info(f"Sample audio carrier not found: {selected_sample['audio_file']}")

    if st.button("Run Selected Sample", use_container_width=True, type="primary"):
        st.session_state.transcript = selected_sample["transcript"]
        st.session_state.label = selected_sample_name
        st.session_state.last_engine = "Built-in sample"
        st.session_state.last_model = None
        st.rerun()

    st.caption("Samples use deterministic transcripts for repeatable demonstrations.")
    st.divider()
    st.subheader("2. Upload New Audio")

    uploaded_audio = st.file_uploader(
        "Drop a mono, 16-bit PCM WAV file",
        type=["wav"],
        help="Use an uncompressed mono 16-bit PCM WAV file. A 16 kHz sample rate is recommended.",
    )

    if uploaded_audio is not None:
        st.audio(uploaded_audio)
        st.caption(f"File: {uploaded_audio.name} | Size: {len(uploaded_audio.getvalue()) / 1024:.1f} KB")

    process_disabled = uploaded_audio is None or selected_model is None

    if st.button("Process Uploaded Call", use_container_width=True, disabled=process_disabled, type="primary"):
        audio_bytes = uploaded_audio.getvalue()
        audio_hash = hashlib.sha1(audio_bytes).hexdigest()
        temporary_audio_path = Path(tempfile.gettempdir()) / f"{audio_hash}.wav"
        temporary_audio_path.write_bytes(audio_bytes)

        transcript = ""
        processing_successful = False

        with st.status("Analyzing audio locally...", expanded=True) as processing_status:
            st.write("Step 1: Validating audio container")
            time.sleep(0.2)

            if selected_model is not None:
                st.write(f"Step 2: Loading {selected_model_label}")
                st.write("Step 3: Running local Vosk speech recognition")
                try:
                    transcript = transcribe_vosk(temporary_audio_path, selected_model)
                    if transcript:
                        processing_successful = True
                        st.session_state.last_engine = "Vosk local"
                        st.session_state.last_model = selected_model_label
                    else:
                        st.warning("No recognizable speech was detected.")
                        processing_status.update(label="No speech detected", state="error")
                except ValueError as error:
                    st.error(str(error))
                    processing_status.update(label="Invalid audio format", state="error")
                except Exception as error:
                    st.error(f"Vosk transcription failed: {error}")
                    processing_status.update(label="Transcription failed", state="error")
            if processing_successful:
                st.write("Step 4: Applying compliance rule pack")
                time.sleep(0.2)
                st.session_state.transcript = transcript
                st.session_state.label = uploaded_audio.name
                processing_status.update(label="Local analysis complete", state="complete")

        if processing_successful:
            st.rerun()

with right_column:
    st.subheader("Live Review Cockpit")
    st.caption(f"Last processing engine: {st.session_state.last_engine}")
    result = analyze(st.session_state.transcript) if st.session_state.transcript else None

    if result is None:
        st.info("Load a sample or upload a WAV file to begin.")
    else:
        metric_columns = st.columns(4)
        metric_items = [
            ("Compliance Score", result["score"], "out of 100"),
            ("Decision", result["status"], "policy outcome"),
            ("Flags", len(result["findings"]), "items detected"),
            ("Words", result["word_count"], "transcribed"),
        ]

        for column, (title, value, subtitle) in zip(metric_columns, metric_items):
            column.markdown(
                f'<div class="metric"><div class="muted">{html.escape(str(title))}</div>'
                f'<div class="big">{html.escape(str(value))}</div>'
                f'<div class="muted">{html.escape(str(subtitle))}</div></div>',
                unsafe_allow_html=True,
            )

        st.write("")
        tabs = st.tabs(["Transcript Lens", "Risk Signals", "Case Record", "Future Architecture"])

        with tabs[0]:
            st.caption(f"Call: {st.session_state.label}")
            st.caption(f"Processing engine: {st.session_state.last_engine}")
            if st.session_state.last_model:
                st.caption(f"Speech model: {st.session_state.last_model}")

            edited_transcript = st.text_area(
                "Editable transcript",
                value=st.session_state.transcript,
                height=240,
            )
            if st.button("Re-run Rules on Edited Text", use_container_width=True, key="rerun_rules"):
                cleaned_transcript = edited_transcript.strip()
                if cleaned_transcript:
                    st.session_state.transcript = cleaned_transcript
                    st.session_state.last_engine = "Manual transcript review"
                    st.rerun()
                else:
                    st.warning("The transcript cannot be empty.")

        with tabs[1]:
            findings = result["findings"]
            if findings:
                severity_order = {"Critical": 1, "High": 2, "Medium": 3, "Low": 4}
                for finding in sorted(findings, key=lambda item: severity_order.get(item["severity"], 5)):
                    risk_class = {
                        "Critical": "risk-critical",
                        "High": "risk-high",
                        "Medium": "risk-medium",
                        "Low": "risk-low",
                    }.get(finding["severity"], "risk-low")
                    st.markdown(
                        f'<div class="{risk_class}"><b>{html.escape(str(finding["severity"]))} • '
                        f'{html.escape(str(finding["category"]))}</b><br>{html.escape(str(finding["label"]))}<br>'
                        f'<span class="muted">Evidence: {html.escape(str(finding["evidence"]))} • '
                        f'Rule: {html.escape(str(finding["id"]))}</span></div>',
                        unsafe_allow_html=True,
                    )
            else:
                st.markdown(
                    '<div class="ok"><b>No configured rule violations detected.</b><br>'
                    'Human sampling and compliance review are still recommended.</div>',
                    unsafe_allow_html=True,
                )

        with tabs[2]:
            case_record = {
                "call": st.session_state.label,
                "processing_engine": st.session_state.last_engine,
                "speech_model": st.session_state.last_model,
                "transcript": st.session_state.transcript,
                "analysis": result,
                "prototype_type": "Offline-first",
            }
            st.json(case_record)
            st.download_button(
                "Download Evidence JSON",
                json.dumps(case_record, indent=2, ensure_ascii=False),
                file_name="compliance_case.json",
                mime="application/json",
                use_container_width=True,
            )
            if st.button("Add to Review Queue", use_container_width=True, key="add_queue"):
                st.session_state.history.append({
                    "Call": st.session_state.label,
                    "Engine": st.session_state.last_engine,
                    "Model": st.session_state.last_model or "Not applicable",
                    "Score": result["score"],
                    "Status": result["status"],
                    "Flags": len(result["findings"]),
                })
                st.rerun()

        with tabs[3]:
            st.markdown(
                """
                ### Current Prototype
                Browser interface → Local WAV upload → Selected Vosk model or simulation → Compliance rules → Evidence JSON

                ### API-Enabled Future State
                Telephony platform → Secure ingestion → Streaming speech recognition → Policy service → Case management → Audit analytics

                ### Recommended Production Controls
                - Encryption in transit and at rest
                - Recording consent and retention controls
                - Role-based access control
                - Sensitive-data redaction
                - Human compliance review
                - Rule and model versioning
                - Quality and operational monitoring
                """
            )

if st.session_state.history:
    st.divider()
    queue_title, queue_action = st.columns([4, 1])
    with queue_title:
        st.subheader("Local Review Queue")
    with queue_action:
        if st.button("Clear Queue", use_container_width=True):
            st.session_state.history = []
            st.rerun()

    review_dataframe = pd.DataFrame(st.session_state.history)
    st.dataframe(review_dataframe, use_container_width=True, hide_index=True)
    st.download_button(
        "Download Review Queue CSV",
        review_dataframe.to_csv(index=False).encode("utf-8"),
        file_name="compliance_review_queue.csv",
        mime="text/csv",
    )

st.divider()
st.caption(
    "Prototype disclaimer: This application provides illustrative compliance indicators. "
    "It is not a legal determination or a replacement for approved human compliance review."
)
