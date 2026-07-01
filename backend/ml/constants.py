MODEL_VERSION = "1.1.0"

SAMPLE_SIZE = 50000

GENDERS = ['male', 'female', 'other']

SYMPTOMS_WEIGHT = {
    "chest pain": 2,
    "breathlessness": 2,
    "confusion": 2,
    "fatigue": 1,
    "sweating": 1,
    "cough": 1,
    "fever": 1,
    "headache": 1,
    "dizziness": 1,
    "blurred vision": 1,
    "joint pain": 1,
    "swelling": 1,
    "stiffness": 1,
    "limited movement": 1,
    "abdominal pain": 1,
    "nausea": 1,
    "vomiting": 1,
    "diarrhea": 1,
    "body pain": 1,
    "weakness": 1,
}

VITALS_WEIGHT = {
    "bp_high": 2,
    "hr_high": 2,
    "hr_low": 1,
    "bp_low": 3,
    "temp_high": 0,
    "temp_low": 0,
    "normal": 0,
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

DEPARTMENTS = {
    "cardiology": {
        "symptoms": ["chest pain", "breathlessness", "fatigue", "sweating"],
        "vitals": ["bp_high", "hr_high"],
        "age_range": (45, 80),
        "duration_range": (1, 5)
    },
    "pulmonology": {
        "symptoms": ["cough", "breathlessness", "fever", "fatigue"],
        "vitals": ["temp_high", "hr_high"],
        "age_range": (20, 70),
        "duration_range": (1, 7)
    },
    "neurology": {
        "symptoms": ["headache", "dizziness", "confusion", "blurred vision"],
        "vitals": ["bp_low", "bp_high"],
        "age_range": (30, 80),
        "duration_range": (1, 10)
    },
    "orthopedics": {
        "symptoms": ["joint pain", "swelling", "stiffness", "limited movement"],
        "vitals": ["normal"],
        "age_range": (40, 85),
        "duration_range": (7, 30)
    },
    "gastrology": {
        "symptoms": ["abdominal pain", "nausea", "vomiting", "diarrhea"],
        "vitals": ["normal"],
        "age_range": (20, 65),
        "duration_range": (1, 5)
    },
    "general": {
        "symptoms": ["fever", "body pain", "weakness", "fatigue"],
        "vitals": ["temp_high"],
        "age_range": (15, 60),
        "duration_range": (1, 5)
    }
}

OPPOSITES = {
    "bp_high": "bp_low",
    "hr_high": "hr_low",
    "temp_high": "temp_low",
    "bp_low": "bp_high",
    "hr_low": "hr_high",
    "temp_low": "temp_high",
}
KNOWN_HISTORY = [
    "pregnant",
    "previous_heart_attack",
    "on_blood_thinners",
    "hiv",
    "diabetes",
    "hypertension",
]

HISTORY_WEIGHTS = {
    "pregnant": 9,
    "previous_heart_attack": 10,
    "on_blood_thinners": 5,
    "hiv": 9,
    "diabetes": 4,
    "hypertension": 4,
}

DEPT_HISTORY_BIAS = {
    "cardiology":   ["previous_heart_attack", "hypertension", "on_blood_thinners"],
    "neurology":    ["hypertension", "diabetes"],
    "general":      ["diabetes"],
    "pulmonology":  ["hiv"],
    "gastrology":   ["diabetes"],
    "orthopedics":  [],
}

CONFIDENCE_LEVEL_MAP = {
    "low": 0.4,
    "medium": 0.65,
    "high": 0.85,
}