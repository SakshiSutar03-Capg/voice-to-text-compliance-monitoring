# Auralis Voice-to-Text Compliance Monitoring

An offline-first banking/finance proof of concept with a distinctive Streamlit review cockpit. It demonstrates sample selection, audio upload, local Vosk transcription, deterministic simulation fallback, rule-based compliance detection, scoring, evidence export and a review queue.

## Quick start

1. Install Python 3.10 or newer.
2. Open a terminal in this folder.
3. Run `pip install -r requirements.txt`.
4. Run `streamlit run app.py` or use `run.bat` / `run.sh`.
5. Open the local address displayed by Streamlit.

## Vosk setup

The app never calls an external API. To enable real speech-to-text, obtain a compatible English Vosk model through your organization's approved software-transfer process, extract it into `models/`, and restart the app. The extracted folder must contain `am/` and `conf/`.

Vosk expects a mono, uncompressed, 16-bit PCM WAV in this prototype. If a model is absent, use **Simulation** or **Auto** mode. The full user journey still works using deterministic local mock transcripts.

## Demo flow

1. Load each built-in sample and compare the scores and evidence.
2. Upload a WAV and choose Simulation for a guaranteed, dependency-free demonstration.
3. Add an analyzed call to the local review queue.
4. Download the evidence JSON.
5. Open the Future architecture tab to explain the scalable version.

## Architecture View

<img width="4032" height="1769" alt="image" src="https://github.com/user-attachments/assets/5f471f8d-f338-4bb8-a374-9b2328e79d45" />


## Samples

The included WAVs are synthetic tone carriers, not recordings of real customers. Sample selection uses the named local transcripts embedded in the prototype to ensure repeatable demos.

## Important limitations

- This is a proof of concept, not a legal determination or production compliance control.
- Rules are illustrative and must be approved by legal/compliance teams.
- Vosk accuracy depends on the selected model, language, channel quality and audio format.
- Production design should add consent, retention, encryption, RBAC, auditability, PII redaction, human review, monitoring and secure integration.

## Project structure

- `app.py`: interactive UI and user journey
- `audio_utils.py`: local Vosk transcription
- `compliance_engine.py`: rule engine and score
- `data/rules.json`: editable policy rules
- `samples/`: local demo audio carriers
- `models/`: place an approved local Vosk model here

## Diagnose
Run `python diagnose.py`. Built-in WAVs are simulation carriers, not spoken recordings for Vosk testing.
