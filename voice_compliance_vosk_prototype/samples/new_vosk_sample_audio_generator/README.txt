NEW SPOKEN VOSK SAMPLE AUDIO GENERATOR

1. Extract this ZIP on a Windows computer.
2. Double-click run_generator.bat.
3. Wait until the window says Finished.
4. Open the newly created samples folder.
5. Play each WAV file to confirm it contains speech.
6. Copy all three WAV files into your project samples folder.
7. Replace the old files when Windows asks.
8. Restart Streamlit.

Generated format:
- WAV
- Mono
- 16-bit PCM
- 16,000 Hz
- Suitable for the prototype's Vosk validation

Files created:
- sample_compliant.wav
- sample_sensitive.wav
- sample_collections.wav

The generator uses Windows System.Speech locally and does not call an external API.
