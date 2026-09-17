from pathlib import Path
import sys, importlib.util
base=Path(__file__).parent
print("Python:",sys.version)
for name in ["streamlit","vosk","pandas"]:
 print(name, "OK" if importlib.util.find_spec(name) else "MISSING")
models=[p.name for p in (base/"models").iterdir() if p.is_dir() and (p/"am").exists() and (p/"conf").exists()]
print("Vosk models detected:", models or "NONE")
