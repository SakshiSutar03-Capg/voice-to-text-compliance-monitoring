from pathlib import Path
import json
import wave


def find_models(base):
    """
    Find all valid Vosk models inside the models directory.

    A valid Vosk model folder must contain:
    - am
    - conf
    """

    base = Path(base)

    if not base.exists():
        return []

    available_models = []

    for model_folder in base.iterdir():
        if (
            model_folder.is_dir()
            and (model_folder / "am").exists()
            and (model_folder / "conf").exists()
        ):
            available_models.append(model_folder)

    # Sort models alphabetically by folder name
    return sorted(
        available_models,
        key=lambda model_path: model_path.name.lower()
    )


def transcribe_vosk(audio_path, model_path):
    """
    Transcribe a WAV audio file using the selected Vosk model.
    """

    from vosk import Model, KaldiRecognizer

    wf = wave.open(str(audio_path), "rb")

    try:
        if (
            wf.getnchannels() != 1
            or wf.getsampwidth() != 2
            or wf.getcomptype() != "NONE"
        ):
            raise ValueError(
                "Vosk input must be a mono, uncompressed, "
                "16-bit PCM WAV file."
            )

        model = Model(str(model_path))

        recognizer = KaldiRecognizer(
            model,
            wf.getframerate()
        )

        transcript_chunks = []

        while True:
            audio_data = wf.readframes(4000)

            if not audio_data:
                break

            if recognizer.AcceptWaveform(audio_data):
                result = json.loads(recognizer.Result())
                text = result.get("text", "").strip()

                if text:
                    transcript_chunks.append(text)

        final_result = json.loads(
            recognizer.FinalResult()
        )

        final_text = final_result.get("text", "").strip()

        if final_text:
            transcript_chunks.append(final_text)

        return " ".join(transcript_chunks).strip()

    finally:
        wf.close()