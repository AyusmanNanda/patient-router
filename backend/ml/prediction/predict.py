from pathlib import Path
from datetime import datetime
import joblib
import numpy as np
import pandas as pd 
import json
import logging
import difflib
from ml.constants import (
    ALIASES, KNOWN_VITALS, KNOWN_SYMPTOMS,
    SYMPTOMS_WEIGHT, EMERGENCY_SYMPTOMS, VITALS_WEIGHT,
    EMERGENCY_VITALS, CONFIDENCE_THRESHOLD,
    SAFE_FALLBACK_DEPT, MODEL_VERSION
)
from ml.prediction.priority import calculate_priority
from ml.prediction.emergency import detect_emergency
from ml.prediction.history import analyze_history

BASE_DIR = Path(__file__).resolve().parent.parent
LOGS_DIR = BASE_DIR / "../logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)
MODEL_DIR = BASE_DIR / "models" / "model.pkl"
PREDICTIONS_LOG = LOGS_DIR / "predictions.jsonl"

logging.basicConfig(
    filename=str(LOGS_DIR / "triage.log"),
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(module)s:%(lineno)d | %(message)s"
)
logger = logging.getLogger(__name__)

try:
    model = joblib.load(str(MODEL_DIR))
    logger.info(f"Model loaded successfully from {MODEL_DIR}")
except FileNotFoundError:
    print(f"Failed to load model from {MODEL_DIR}")
    logger.error(f"Failed to load model from {MODEL_DIR}")
    exit(1)


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


def predict_case(symptoms: str, vitals: str = "", age: int = 30, duration: int = 1, gender: str = "male", history: str = ""):
    logger.info(
        f"Prediction request | "
        f"symptoms={symptoms!r} "
        f"vitals={vitals!r} "
        f"age={age} "
        f"duration={duration} "
        f"gender={gender} "
        f"history={history!r}"
    )
    if not symptoms.strip():
        raise ValueError("Symptoms cannot be empty.")

    vitals_missing = not vitals.strip()
    if vitals_missing:
        vitals = "normal"

    if not isinstance(age, (int, float)) or age <= 0 or age > 120:
        logger.error(f"Invalid age received: {age}")
        raise ValueError(f"Invalid age: {age}")

    if not isinstance(duration, (int, float)) or duration <= 0:
        raise ValueError(f"Invalid duration: {duration}")

    age = int(age)
    duration = int(duration)

    symptoms_list = [s.strip().lower() for s in symptoms.split(",") if s.strip()]
    vitals_list = [v.strip().lower() for v in vitals.split(",") if v.strip()]
    history_list = [h.strip().lower().replace(" ", "_") for h in history.split(",") if h.strip()]
    history_score, is_high_risk = analyze_history(history_list)

    if not symptoms_list:
        raise ValueError("No valid symptoms found after parsing.")

    symptoms_list = normalize_list(symptoms_list, KNOWN_SYMPTOMS)
    vitals_list = normalize_list(vitals_list, KNOWN_VITALS)

    text = " ".join(symptoms_list) + " " + " ".join(vitals_list) + " " + " ".join(history_list)
    input_df = pd.DataFrame([{"text": text, "age": age, "duration": duration, "gender": gender}])
    probs = model.predict_proba(input_df)[0]


    classes = model.classes_
    top_indices = np.argsort(probs)[::-1][:3]

    departments = []
    for i in top_indices:
        departments.append({
            "department": classes[i],
            "confidence": round(float(probs[i]), 3)
        })

    priority = calculate_priority(symptoms_list, vitals_list, age, duration)
    is_emergency = detect_emergency(symptoms_list, vitals_list)

    if is_emergency or is_high_risk:
        priority = "high"

    reasons = []

    for symptom in symptoms_list:
        if symptom in SYMPTOMS_WEIGHT or symptom in EMERGENCY_SYMPTOMS:
            if symptom not in reasons:
                reasons.append(symptom)

    for vital in vitals_list:
        if vital in VITALS_WEIGHT or vital in EMERGENCY_VITALS:
            if vital not in reasons:
                reasons.append(vital)

    for condition in history_list:
        reasons.append(f"History: {condition}")

    if age > 60:
        reasons.append(f"Age risk ({age} years)")

    if duration <= 2:
        reasons.append(f"Acute onset ({duration} days)")
    elif duration > 14:
        reasons.append(f"Chronic condition ({duration} days)")

    top_confidence = departments[0]["confidence"]
    recommended = departments[0]["department"]

    if top_confidence < CONFIDENCE_THRESHOLD:
        logger.warning(
            f"Low confidence ({top_confidence:.3f}) "
            f"falling back to {SAFE_FALLBACK_DEPT}"
        )
        recommended = SAFE_FALLBACK_DEPT
        reasons.append("Low model confidence - fallback to general")

    results = {
        "recommended": recommended,
        "departments": departments,
        "priority": priority,
        "emergency": is_emergency,
        "confidence": top_confidence,
        "reasons": reasons,
        "history": history_list,
        "history_score": history_score,
        "model_version": MODEL_VERSION,
        "warning": "Vitals not provided — prediction may be less accurate. Please provide vitals for better results." if vitals_missing else None,
    }

    logger.info(
        f"Prediction completed | "
        f"recommended={recommended} "
        f"confidence={top_confidence:.3f} "
        f"priority={priority} "
        f"emergency={is_emergency}"
    )
    prediction_log = {
        "timestamp": datetime.now().isoformat(),
        "symptoms": symptoms_list,
        "vitals": vitals_list,
        "history": history_list,
        "history_score": history_score,
        "age": age,
        "duration": duration,
        "gender": gender,
        "recommended": recommended,
        "confidence": top_confidence,
        "priority": priority,
        "emergency": is_emergency,
        "fallback_used": top_confidence < CONFIDENCE_THRESHOLD,
        "model_version": MODEL_VERSION,
    }
    with open(PREDICTIONS_LOG, "a") as f:
        f.write(json.dumps(prediction_log) + "\n")

    return results


if __name__ == "__main__":
    result = predict_case(
        "chest pain, breathlessness",
        "bp_high, hr_high",
        65,
        15
    )
    print("Predict: \n", json.dumps(result, indent=2))