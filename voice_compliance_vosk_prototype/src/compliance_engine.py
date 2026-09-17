import json
import re
from pathlib import Path


SEVERITY_SCORE = {
    "Critical": 30,
    "High": 20,
    "Medium": 10,
    "Low": 5,
}


def load_rules():
    # compliance_engine.py is inside the src folder.
    src_directory = Path(__file__).resolve().parent

    # Move one level above src to the project folder.
    project_directory = src_directory.parent

    # The data folder is in the main project folder.
    rules_path = project_directory / "data" / "rules.json"

    if not rules_path.exists():
        raise FileNotFoundError(
            f"Compliance rules file was not found: {rules_path}"
        )

    return json.loads(
        rules_path.read_text(encoding="utf-8")
    )


def analyze(transcript):
    text = transcript.lower()
    findings = []
    rules = load_rules()

    for rule in rules:
        matched_phrases = []
        rule_mode = rule.get("mode", "prohibited")

        for phrase in rule["keywords"]:
            if phrase.lower() in text:
                matched_phrases.append(phrase)

        if rule_mode == "required":
            triggered = not matched_phrases
        else:
            triggered = bool(matched_phrases)

        if triggered:
            if rule_mode == "required":
                evidence = "Required phrase not detected"
            else:
                evidence = ", ".join(matched_phrases)

            findings.append(
                {
                    **rule,
                    "evidence": evidence,
                }
            )

    deducted_score = sum(
        SEVERITY_SCORE.get(
            finding["severity"],
            5,
        )
        for finding in findings
    )

    score = max(
        0,
        100 - deducted_score,
    )

    if score >= 85:
        status = "Compliant"
    elif score >= 60:
        status = "Review"
    else:
        status = "Escalate"

    word_count = len(
        re.findall(
            r"\b\w+\b",
            transcript,
        )
    )

    return {
        "score": score,
        "status": status,
        "findings": findings,
        "word_count": word_count,
    }