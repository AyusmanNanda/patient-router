from pathlib import Path
import joblib
import numpy as np
import json

BASE_DIR = Path(__file__).resolve().parent

model = joblib.load(str(BASE_DIR / "models" / "model.pkl"))
vectorizer = joblib.load(str(BASE_DIR / "models" / "vectorizer.pkl"))

SYMPTOMS_WEIGHT = {
    "chest pain": 2,
    "breathlessness": 2,

}

VITAL_WEIGHT = {
    "bp_high": 2,
    "hr_high": 1,
}

EMERGENCY_SYMPTOMS = ["chest pain", "breathlessness", "confusion"]
EMERGENCY_VITAL = ["bp_low", "hr_high"]

CONFIDENCE_THRESHOLD = 0.60
SAFE_FALLBACK_DEPT = "general"

def predict_case(symptoms: str, vitals: str, age: int = 30, duration: int = 1):
    text = symptoms + " " + vitals
    vector = vectorizer.transform([text])

    probs = model.predict_proba(vector)[0]
    classes = model.classes_

    top_indices = np.argsort(probs)[::-1][:3]

    departments = []

    for i in top_indices:
        departments.append({
            "department": classes[i],
            "confidence": round(float(probs[i]),3)
        })

    symptoms_list = [symptom.strip() for symptom in symptoms.split(",")]
    vitals_list = [raw_vitals.strip() for raw_vitals in vitals.split(",")]

    score = 0
    for symptom in symptoms_list:
        if symptom in SYMPTOMS_WEIGHT:
            score += SYMPTOMS_WEIGHT[symptom]
            if duration <= 2:
                score += 1

    for vital in vitals_list:
        if vital in VITAL_WEIGHT:
            score += VITAL_WEIGHT[vital]

    if age > 60:
        score += 1

    if score >= 4:
        priority = "high"
    elif score >=2:
        priority = "medium"
    else:
        priority = "low"


    is_emergency = False
    for symptom in symptoms_list:
        if symptom in EMERGENCY_SYMPTOMS:
            is_emergency = True

    for vital in vitals_list:
        if vital in EMERGENCY_VITAL:
            is_emergency = True

    reasons = []
    for symptom in symptoms_list:
        if symptom in SYMPTOMS_WEIGHT or symptom in EMERGENCY_SYMPTOMS:
            if symptom not in reasons:
                reasons.append(symptom)

    for vital in vitals_list:
        if vital in VITAL_WEIGHT or vital in EMERGENCY_VITAL:
            if vital not in reasons:
                reasons.append(vital)

    if duration <= 2:
        reasons.append(f"Acute onset ({duration} days)")
    elif duration > 14:
        reasons.append(f"Chronic condition ({duration} days)")

    top_confidence = departments[0]["confidence"]
    recommended = departments[0]["department"]

    if top_confidence < CONFIDENCE_THRESHOLD:
        recommended = SAFE_FALLBACK_DEPT
        reasons.append("Low confidence fallback")

    return{
        "department": departments,
        "priority": priority,
        "emergency": is_emergency,
        "recommended": recommended,
        "confidence": top_confidence,
        "reasons": reasons,
    }


if __name__ == "__main__":
    result = predict_case(
        "chest pain, breathlessness",
        "bp_high, hr_high",
        65,
        15
    )
    print("Predict: \n", json.dumps(result, indent=2))