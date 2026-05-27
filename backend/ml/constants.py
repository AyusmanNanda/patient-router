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