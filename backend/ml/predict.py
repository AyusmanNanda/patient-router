from pathlib import Path
import joblib
import numpy as np
import json
import logging
import difflib

BASE_DIR = Path(__file__).resolve().parent

logging.basicConfig(
    filename=str(BASE_DIR / "triage.log"),
    level=logging.INFO,
    format="%(asctime)s - %(message)s"
)

model = joblib.load(str(BASE_DIR / "models" / "model.pkl"))
vectorizer = joblib.load(str(BASE_DIR / "models" / "vectorizer.pkl"))

MODEL_VERSION = "1.0.0"

SYMPTOMS_WEIGHT = {
    "chest pain": 2,
    "breathlessness": 2,
}

VITAL_WEIGHT = {
    "bp_high": 2,
    "hr_high": 1,
}

EMERGENCY_SYMPTOMS = ["chest pain", "breathlessness", "confusion"]
EMERGENCY_VITALS = ["bp_low", "hr_high"]

CONFIDENCE_THRESHOLD = 0.60
SAFE_FALLBACK_DEPT = "general"

KNOWN_SYMPTOMS = [
    "chest pain", "breathlessness", "fatigue", "sweating",
    "cough", "fever", "headache", "dizziness", "confusion",
    "blurred vision", "joint pain", "swelling", "stiffness",
    "limited movement", "abdominal pain", "nausea", "vomiting",
    "diarrhea", "body pain", "weakness"
]

KNOWN_VITALS = ["bp_high", "bp_low", "hr_high", "hr_low", "temp_high", "temp_low", "normal"]

ALIASES = {
    "bp high": "bp_high",
    "bp low": "bp_low",
    "hr high": "hr_high",
    "hr low": "hr_low",
    "temp high": "temp_high",
    "temp low": "temp_low",
    "high bp": "bp_high",
    "low bp": "bp_low",
    "high hr": "hr_high",
    "high temp": "temp_high",
    "shortness of breath": "breathlessness",
    "short of breath": "breathlessness",
    "sob": "breathlessness",
    "chest tightness": "chest pain",
    "stomach pain": "abdominal pain",
    "stomach ache": "abdominal pain",
    "belly pain": "abdominal pain",
    "loose motion": "diarrhea",
    "loose motions": "diarrhea",
    "blurred": "blurred vision",
    "blur": "blurred vision",
    "joint ache": "joint pain",
    "tired": "fatigue",
    "tiredness": "fatigue",
    "breathless": "breathlessness",
}


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
    vector = vectorizer.transform([text])

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