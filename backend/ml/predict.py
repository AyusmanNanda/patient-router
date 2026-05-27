from pathlib import Path
import joblib
import numpy as np
import pandas as pd 
import json
import logging
import difflib
from constants import (
    ALIASES, KNOWN_VITALS, KNOWN_SYMPTOMS,
    SYMPTOMS_WEIGHT, EMERGENCY_SYMPTOMS, VITAL_WEIGHT,
    EMERGENCY_VITALS, CONFIDENCE_THRESHOLD,
    SAFE_FALLBACK_DEPT, MODEL_VERSION
)

BASE_DIR = Path(__file__).resolve().parent

logging.basicConfig(
    filename=str(BASE_DIR / "../logs/triage.log"),
    level=logging.INFO,
    format="%(asctime)s - %(message)s"
)

model = joblib.load(str(BASE_DIR / "models" / "model.pkl"))


def normalize_term(term: str, known: list) -> str:
    if term in ALIASES:
        return ALIASES[term]

    if term in known:
        return term

    swapped = term.replace(" ", "_") if " " in term else term.replace("_", " ")
    if swapped in known:
        return swapped

    matches = difflib.get_close_matches(term, known, n=1, cutoff=0.75)
    if matches:
        return matches[0]

    return term


def normalize_list(terms: list, known: list) -> list:
    return [normalize_term(t, known) for t in terms]


def predict_case(symptoms: str, vitals: str = "", age: int = 30, duration: int = 1):

    if not symptoms.strip():
        raise ValueError("Symptoms cannot be empty.")

    vitals_missing = not vitals.strip()
    if vitals_missing:
        vitals = "normal"

    if not isinstance(age, (int, float)) or age <= 0 or age > 120:
        raise ValueError(f"Invalid age: {age}")

    if not isinstance(duration, (int, float)) or duration <= 0:
        raise ValueError(f"Invalid duration: {duration}")

    age = int(age)
    duration = int(duration)

    symptoms_list = [s.strip().lower() for s in symptoms.split(",") if s.strip()]
    vitals_list = [v.strip().lower() for v in vitals.split(",") if v.strip()]

    if not symptoms_list:
        raise ValueError("No valid symptoms found after parsing.")

    symptoms_list = normalize_list(symptoms_list, KNOWN_SYMPTOMS)
    vitals_list = normalize_list(vitals_list, KNOWN_VITALS)

    text = " ".join(symptoms_list) + " " + " ".join(vitals_list)

    try:
        probs = model.predict_proba(vector)[0]
    except Exception as e:
        raise RuntimeError(f"Model prediction failed: {e}")

    classes = model.classes_
    top_indices = np.argsort(probs)[::-1][:3]

    departments = []
    for i in top_indices:
        departments.append({
            "department": classes[i],
            "confidence": round(float(probs[i]), 3)
        })

    score = 0

    for symptom in symptoms_list:
        score += SYMPTOMS_WEIGHT.get(symptom, 0)

    for vital in vitals_list:
        score += VITAL_WEIGHT.get(vital, 0)

    if age > 60:
        score += 1

    if any(s in SYMPTOMS_WEIGHT for s in symptoms_list) and duration <= 2:
        score += 1

    if score >= 4:
        priority = "high"
    elif score >= 2:
        priority = "medium"
    else:
        priority = "low"

    is_emergency = any(s in EMERGENCY_SYMPTOMS for s in symptoms_list) or \
                   any(v in EMERGENCY_VITALS for v in vitals_list)

    if is_emergency:
        priority = "high"

    reasons = []

    for symptom in symptoms_list:
        if symptom in SYMPTOMS_WEIGHT or symptom in EMERGENCY_SYMPTOMS:
            if symptom not in reasons:
                reasons.append(symptom)

    for vital in vitals_list:
        if vital in VITAL_WEIGHT or vital in EMERGENCY_VITALS:
            if vital not in reasons:
                reasons.append(vital)

    if age > 60:
        reasons.append(f"Age risk ({age} years)")

    if duration <= 2:
        reasons.append(f"Acute onset ({duration} days)")
    elif duration > 14:
        reasons.append(f"Chronic condition ({duration} days)")

    top_confidence = departments[0]["confidence"]
    recommended = departments[0]["department"]

    if top_confidence < CONFIDENCE_THRESHOLD:
        recommended = SAFE_FALLBACK_DEPT
        reasons.append("Low model confidence — fallback to general")

    result = {
        "recommended": recommended,
        "departments": departments,
        "priority": priority,
        "emergency": is_emergency,
        "confidence": top_confidence,
        "reasons": reasons,
        "model_version": MODEL_VERSION,
        "warning": "Vitals not provided — prediction may be less accurate. Please provide vitals for better results." if vitals_missing else None,
    }

    logging.info(
        f"Input: symptoms={symptoms!r}, vitals={vitals!r}, age={age}, duration={duration} | "
        f"Output: recommended={recommended}, priority={priority}, emergency={is_emergency}"
    )

    return result


if __name__ == "__main__":
    result = predict_case(
        "chest pain, breathlessness",
        "bp_high, hr_high",
        65,
        15
    )
    print("Predict: \n", json.dumps(result, indent=2))