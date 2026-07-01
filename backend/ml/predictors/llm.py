import os
import json
from pathlib import Path
from datetime import datetime

from google import genai
from google.genai import types
from dotenv import load_dotenv

from ml.constants import MODEL_VERSION
from ml.rules.history import analyze_history
from utils.logger import logger

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError("GEMINI_API_KEY not found in environment variables.")

client = genai.Client(api_key=api_key)

BASE_DIR = Path(__file__).resolve().parent.parent
LOGS_DIR = BASE_DIR / "../logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)
LLM_PREDICTIONS_LOG = LOGS_DIR / "llm_predictions.jsonl"

VALID_DEPARTMENTS = {
    "cardiology",
    "pulmonology",
    "neurology",
    "orthopedics",
    "gastrology",
    "general",
}

VALID_PRIORITIES = {"low", "medium", "high"}

VALID_CONFIDENCE_LEVELS = {"low", "medium", "high"}

# We don't trust the LLM to produce a calibrated numeric probability, so we
# ask it for a coarse confidence level and map that to a fixed number ourselves.
CONFIDENCE_LEVEL_MAP = {
    "low": 0.4,
    "medium": 0.65,
    "high": 0.85,
}


def build_prompt(symptoms: str, vitals: str, age, gender: str, duration, history: str) -> str:
    prompt = f"""
You are an AI-powered hospital triage assistant.

Choose ONLY one department from:
cardiology, pulmonology, neurology, orthopedics, gastrology, general

Patient Information

Symptoms: {symptoms}
Vitals: {vitals}
Age: {age}
Gender: {gender}
Duration: {duration} days
Medical History: {history}

Schema:
{{
    "recommended": "department",
    "confidence_level": "low | medium | high",
    "priority": "low | medium | high",
    "emergency": false,
    "clinical_reasoning": ["reason 1", "reason 2"]
}}

confidence_level guide:
"high" = symptoms and vitals clearly point to one department
"medium" = symptoms suggest a department but some ambiguity remains
"low" = symptoms are vague or could fit multiple departments

Rules:
Return ONLY a valid JSON object.
Do not use markdown.
Do not use code blocks.
Do not include any explanation.
Do not include any text before or after the JSON object.
If the information is incomplete, return your best clinical judgement.
"""
    return prompt


def predict_llm(data: dict) -> dict:
    symptoms = data.get("symptoms", "").strip()
    vitals = data.get("vitals", "").strip()
    age = data.get("age")
    duration = data.get("duration")
    gender = data.get("gender", "male")
    history = data.get("history", "")

    if not symptoms:
        raise ValueError("Symptoms cannot be empty.")

    vitals_missing = not vitals
    if vitals_missing:
        vitals = "normal"

    if not isinstance(age, (int, float)) or age <= 0 or age > 120:
        raise ValueError(f"Invalid age: {age}")

    if not isinstance(duration, (int, float)) or duration <= 0:
        raise ValueError(f"Invalid duration: {duration}")

    age = int(age)
    duration = int(duration)

    history_list = []
    for h in history.split(","):
        h_clean = h.strip().lower().replace(" ", "_")
        if h_clean:
            history_list.append(h_clean)

    history_score, is_high_risk = analyze_history(history_list)

    prompt = build_prompt(symptoms, vitals, age, gender, duration, history if history else "None")

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0,
            ),
        )
    except Exception as e:
        logger.exception("Gemini API request failed.")
        raise RuntimeError("Failed to get prediction from Gemini.") from e

    raw_text = response.text.strip()
    raw_text = raw_text.replace("```json", "").replace("```", "").strip()

    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError as e:
        logger.exception("Gemini returned invalid JSON.")
        raise ValueError("Gemini returned an invalid response.") from e

    recommended = parsed.get("recommended", "general")
    if recommended not in VALID_DEPARTMENTS:
        logger.warning(f"Gemini returned unknown department: {recommended!r}, falling back to general")
        recommended = "general"

    confidence_level = parsed.get("confidence_level", "low")
    if confidence_level not in VALID_CONFIDENCE_LEVELS:
        logger.warning(f"Gemini returned unknown confidence_level: {confidence_level!r}, falling back to low")
        confidence_level = "low"

    confidence = CONFIDENCE_LEVEL_MAP[confidence_level]

    priority = parsed.get("priority", "low")
    if priority not in VALID_PRIORITIES:
        priority = "low"

    is_emergency = parsed.get("emergency", False)
    if not isinstance(is_emergency, bool):
        is_emergency = False

    clinical_reasoning = parsed.get("clinical_reasoning", [])
    if not isinstance(clinical_reasoning, list):
        clinical_reasoning = []

    if is_high_risk:
        priority = "high"

    reasons = list(clinical_reasoning)

    for condition in history_list:
        reasons.append(f"History: {condition}")

    if age > 60:
        reasons.append(f"Age risk ({age} years)")

    if duration <= 2:
        reasons.append(f"Acute onset ({duration} days)")
    elif duration > 14:
        reasons.append(f"Chronic condition ({duration} days)")

    prediction = {
        "recommended": recommended,
        "departments": [{"department": recommended, "confidence": round(confidence, 3)}],
        "priority": priority,
        "emergency": is_emergency,
        "confidence": round(confidence, 3),
        "confidence_level": confidence_level,
        "reasons": reasons,
        "history": history_list,
        "history_score": history_score,
        "engine": "llm",
        "provider": "gemini",
        "model": "gemini-2.5-flash",
        "backend_version": MODEL_VERSION,
        "warning": "Vitals not provided — rules may be less accurate. Please provide vitals for better results." if vitals_missing else None,
    }

    prediction_log = {
        "timestamp": datetime.now().isoformat(),
        "symptoms": symptoms,
        "vitals": vitals,
        "history": history_list,
        "history_score": history_score,
        "age": age,
        "duration": duration,
        "gender": gender,
        "recommended": recommended,
        "confidence": confidence,
        "confidence_level": confidence_level,
        "priority": priority,
        "emergency": is_emergency,
        "engine": "llm",
        "provider": "gemini",
        "model": "gemini-2.5-flash",
        "backend_version": MODEL_VERSION,
    }

    with open(LLM_PREDICTIONS_LOG, "a") as f:
        f.write(json.dumps(prediction_log) + "\n")

    logger.info(f"LLM prediction | recommended={recommended} confidence={confidence:.3f} priority={priority}")

    return prediction


if __name__ == "__main__":
    sample = {
        "symptoms": "chest pain, breathlessness",
        "vitals": "bp_high, hr_high",
        "age": 65,
        "duration": 15,
        "gender": "male",
        "history": ""
    }
    result = predict_llm(sample)
    print("Predict: \n", json.dumps(result, indent=2))