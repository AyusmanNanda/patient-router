MODEL_VERSION = "1.1.0"

SAMPLE_SIZE = 50000

GENDERS = ['male', 'female', 'other']

SYMPTOMS_WEIGHT = {
    "chest_pain": 2,
    "breathlessness": 2,
    "confusion": 2,
    "fatigue": 1,
    "sweating": 1,
    "cough": 1,
    "fever": 1,
    "headache": 1,
    "dizziness": 1,
    "blurred_vision": 1,
    "joint_pain": 1,
    "swelling": 1,
    "stiffness": 1,
    "limited_movement": 1,
    "abdominal_pain": 1,
    "nausea": 1,
    "vomiting": 1,
    "diarrhea": 1,
    "body_pain": 1,
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
    "unknown" : 0
}

EMERGENCY_SYMPTOMS = ["chest_pain", "breathlessness", "confusion"]
EMERGENCY_VITALS = ["bp_low", "hr_high"]

CONFIDENCE_THRESHOLD = 0.60
SAFE_FALLBACK_DEPT = "general"

KNOWN_SYMPTOMS = [
    "chest_pain", "breathlessness", "fatigue", "sweating",
    "cough", "fever", "headache", "dizziness", "confusion",
    "blurred_vision", "joint_pain", "swelling", "stiffness",
    "limited_movement", "abdominal_pain", "nausea", "vomiting",
    "diarrhea", "body_pain", "weakness"
]

KNOWN_VITALS = ["bp_high", "bp_low", "hr_high", "hr_low", "temp_high", "temp_low", "normal", "unknown"]

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
    "chest tightness": "chest_pain",
    "stomach pain": "abdominal_pain",
    "stomach ache": "abdominal_pain",
    "belly pain": "abdominal_pain",
    "loose motion": "diarrhea",
    "loose motions": "diarrhea",
    "blurred": "blurred_vision",
    "blur": "blurred_vision",
    "joint ache": "joint_pain",
    "tired": "fatigue",
    "tiredness": "fatigue",
    "breathless": "breathlessness",
}

DEPARTMENTS = {
    "cardiology": {
        "symptoms": [
            "chest_pain",
            "breathlessness",
            "fatigue",
            "sweating"
        ],
        "vitals": [
            "bp_high",
            "hr_high",
            "normal"
        ],
        "age_range": (40, 85),
        "duration_range": (1, 7)
    },

    "pulmonology": {
        "symptoms": [
            "cough",
            "breathlessness",
            "fever",
            "fatigue"
        ],
        "vitals": [
            "temp_high",
            "hr_high",
            "normal"
        ],
        "age_range": (15, 75),
        "duration_range": (1, 10)
    },

    "neurology": {
        "symptoms": [
            "headache",
            "dizziness",
            "confusion",
            "blurred_vision"
        ],
        "vitals": [
            "bp_high",
            "bp_low",
            "normal"
        ],
        "age_range": (20, 85),
        "duration_range": (1, 14)
    },

    "orthopedics": {
        "symptoms": [
            "joint_pain",
            "swelling",
            "stiffness",
            "limited_movement"
        ],
        "vitals": [
            "normal",
            "hr_high",
            "temp_high"
        ],
        "age_range": (30, 90),
        "duration_range": (3, 45)
    },

    "gastrology": {
        "symptoms": [
            "abdominal_pain",
            "nausea",
            "vomiting",
            "diarrhea"
        ],
        "vitals": [
            "normal",
            "bp_low",
            "hr_high",
            "temp_high"
        ],
        "age_range": (15, 75),
        "duration_range": (1, 10)
    },

    "general": {
        "symptoms": [
            "fever",
            "body_pain",
            "weakness",
            "fatigue"
        ],
        "vitals": [
            "normal",
            "temp_high",
            "hr_high"
        ],
        "age_range": (10, 85),
        "duration_range": (1, 14)
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