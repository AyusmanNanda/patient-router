"""
constants.py (v5.0.0 - Research Grade)

Single Source of Truth (SSoT) for the Patient Triage System.

Fixes from v4.0.0:
  - CRITICAL_INTERACTIONS now uses only canonical vocabulary keys
  - TIME_RISK_MULTIPLIERS includes explicit 'standard' fallback (1.0)
  - SCORE_TO_ESI mapping added for label generation in data_generator.py
  - FEATURE_ORDER added for reproducible feature vectors across all scripts
  - Pediatric/adult vitals kept as SEPARATE dicts (no unsafe concatenation)
  - 'pregnant' alias replaced with 'pregnant_unknown' safe fallback
  - 'normal_vitals' weight documented explicitly as 0
  - DEPT_ROUTING added so predict.py can map ESI+symptoms → department
  - SYNTHETIC_PREVALENCE added to guide realistic class distribution in data_generator.py
"""

# ===========================================================================
# EXPERIMENT REGISTRY
# ===========================================================================

EXPERIMENT_VERSION = "5.0.0"
CONFIDENCE_THRESHOLD = 0.65
SAFE_FALLBACK_DEPT = "general"

# Hyperparameters for train.py — ensures reproducible research
MODEL_CONFIG = {
    "n_estimators": 200,
    "max_depth": 15,
    "min_samples_split": 5,
    "min_samples_leaf": 2,
    "class_weight": "balanced",
    "random_state": 42
}

# ===========================================================================
# TARGET DEPARTMENTS
# ===========================================================================

KNOWN_DEPARTMENTS = [
    "cardiology", "pulmonology", "gastroenterology", "neurology",
    "orthopedics", "endocrinology", "nephrology", "psychiatry",
    "gynecology", "oncology", "trauma", "infectious_disease",
    "pediatrics", "general"
]

# ===========================================================================
# CLINICAL SCORING — ESI Triage Level Mapping
# ===========================================================================
# Points map to ESI levels via SCORE_TO_ESI at the bottom of this file.
# ESI 1 = Resuscitation, ESI 2 = Emergent, ESI 3 = Urgent,
# ESI 4 = Less Urgent, ESI 5 = Non-Urgent

SYMPTOMS_WEIGHT = {
    # --- ESI Level 1 (Resuscitation): 4 points ---
    "cardiac_arrest":       4,
    "unresponsive":         4,
    "severe_trauma":        4,
    "active_seizure":       4,
    "anaphylaxis":          4,
    "massive_hemorrhage":   4,

    # --- ESI Level 2 (Emergent): 3 points ---
    "chest_pain":           3,
    "severe_breathlessness":3,
    "stroke_symptoms":      3,
    "drooping_face":        3,
    "coughing_blood":       3,
    "suicidal_ideation":    3,
    "severe_burns":         3,
    "sudden_vision_loss":   3,
    "stiff_neck":           3,
    "lethargy":             3,

    # --- ESI Level 3 (Urgent): 2 points ---
    "moderate_abdominal_pain": 2,
    "closed_fracture":      2,
    "dislocation":          2,
    "persistent_vomiting":  2,
    "dehydration":          2,
    "confusion":            2,
    "palpitations":         2,
    "severe_headache":      2,
    "high_fever":           2,

    # --- ESI Level 4/5 (Less/Non-Urgent): 1 point ---
    "mild_fever":           1,
    "dizziness":            1,
    "mild_abdominal_pain":  1,
    "cough":                1,
    "sore_throat":          1,
    "rash":                 1,
    "minor_cut":            1,
    "joint_pain":           1,
    "fatigue":              1,
    "diarrhea":             1,
    "earache":              1,
}

# ===========================================================================
# AGE-ADJUSTED VITAL THRESHOLDS
# ===========================================================================
# IMPORTANT: Do NOT concatenate these in data_generator.py.
# Select the correct dict based on patient age before building feature vectors.

# Vitals shared across all age groups (same threshold, same weight)
SHARED_VITAL_WEIGHT = {
    "spo2_below_90":    3,   # critical hypoxia regardless of age
    "sugar_below_60":   2,   # hypoglycaemia regardless of age
    "sugar_above_300":  1,   # hyperglycaemia regardless of age
    "normal_vitals":    0,   # explicitly scored zero for feature completeness
}

# Adult-only Vitals (Age >= 12)
ADULT_VITAL_WEIGHT = {
    # 3 points — critical
    "rr_above_30":      3,
    "rr_below_9":       3,
    "sbp_below_90":     3,
    "hr_above_130":     3,
    # 2 points — serious
    "hr_below_40":      2,
    "sbp_above_200":    2,
    "temp_above_41c":   2,
    "temp_below_35c":   2,
    # 1 point — concerning
    "hr_111_130":       1,
    "sbp_91_100":       1,
    "temp_39_41c":      1,
}

# Pediatric-only Vitals (Age < 12) — higher baseline HR and RR are normal
PEDIATRIC_VITAL_WEIGHT = {
    # 3 points — critical
    "rr_above_50":      3,
    "rr_below_15":      3,
    "sbp_below_70":     3,
    "hr_above_180":     3,
    # 2 points — serious
    "hr_below_80":      2,
    "temp_above_40c":   2,
    "temp_below_36c":   2,
    # 1 point — concerning
    "hr_160_180":       1,
    "temp_38_40c":      1,
}

# Neurological Assessment (Universal — applies to all age groups)
NEURO_WEIGHT = {
    "avpu_unresponsive": 4,
    "avpu_pain":         3,
    "avpu_verbal":       2,
    "gcs_below_8":       4,
    "gcs_9_12":          2,
    "gcs_normal":        0,  # explicitly scored zero for feature completeness
}

# ===========================================================================
# TEMPORAL MODIFIERS — Duration Risk Scaling
# ===========================================================================
# Multiplied against the raw symptom score.
# All 4 duration categories in KNOWN_DURATIONS are covered here.

TIME_RISK_MULTIPLIERS = {
    "acute_under_6_hours":      1.5,   # hyper-acute onset = highest urgency
    "subacute_under_24_hours":  1.2,
    "standard":                 1.0,   # no modifier — baseline
    "chronic_over_30_days":     0.5,   # long-term stable issues downgraded
}

# ===========================================================================
# PATIENT MODIFIERS — Comorbidities & Clinical Context
# ===========================================================================

HIGH_RISK_MODIFIERS = [
    "immunocompromised",
    "pregnant_1st_trimester",
    "pregnant_2nd_trimester",   # added — lower acuity than 1st/3rd but relevant
    "pregnant_3rd_trimester",
    "on_blood_thinners",
    "history_of_mi",
    "esrd_dialysis",
    "copd",
    "chf",
    "pediatric_infant",         # age < 1 year — neonatal protocols apply
    "pediatric_child",          # age 1–11
    "geriatric",                # age >= 75 — atypical presentation risk
]

# Modifier risk weights — used as additive score bonus in scoring engine
MODIFIER_WEIGHT = {
    "immunocompromised":        2,
    "pregnant_1st_trimester":   2,
    "pregnant_2nd_trimester":   1,
    "pregnant_3rd_trimester":   2,
    "on_blood_thinners":        2,
    "history_of_mi":            2,
    "esrd_dialysis":            2,
    "copd":                     1,
    "chf":                      2,
    "pediatric_infant":         2,
    "pediatric_child":          1,
    "geriatric":                1,
    "none":                     0,
}

# ===========================================================================
# CRITICAL INTERACTIONS — Non-linear Medical Risk Rules
# ===========================================================================
# ALL keys must match canonical vocabulary from SYMPTOMS_WEIGHT,
# ADULT/PEDIATRIC_VITAL_WEIGHT, NEURO_WEIGHT, or HIGH_RISK_MODIFIERS.
# No raw text aliases here — they will silently fail to match.

CRITICAL_INTERACTIONS = [
    # --- Demographics + Vitals ---
    (
        {"pediatric_infant", "high_fever"},
        "Neonatal Sepsis Protocol",
        "pediatrics", 2
    ),
    (
        {"esrd_dialysis", "hr_below_40"},
        "Hyperkalemia / Cardiac Arrhythmia Risk",
        "nephrology", 2
    ),

    # --- Comorbidities + Symptoms ---
    (
        {"immunocompromised", "high_fever"},
        "Neutropenic Sepsis Protocol",
        "oncology", 2
    ),
    (
        {"on_blood_thinners", "severe_trauma"},
        "Intracranial Hemorrhage Risk",
        "trauma", 1
    ),
    (
        {"pregnant_1st_trimester", "moderate_abdominal_pain"},
        "Ectopic Pregnancy Risk",
        "gynecology", 2
    ),
    (
        {"pregnant_1st_trimester", "mild_abdominal_pain"},
        "Possible Ectopic Pregnancy",
        "gynecology", 2
    ),
    (
        {"pregnant_3rd_trimester", "sbp_above_200"},
        "Preeclampsia Risk",
        "gynecology", 2
    ),
    (
        {"history_of_mi", "chest_pain"},
        "High Suspicion Repeat Myocardial Infarction",
        "cardiology", 1
    ),
    (
        {"chf", "severe_breathlessness"},
        "Acute Heart Failure Exacerbation",
        "cardiology", 2
    ),
    (
        {"copd", "severe_breathlessness"},
        "Acute COPD Exacerbation",
        "pulmonology", 2
    ),

    # --- Symptom + Symptom ---
    (
        {"chest_pain", "severe_breathlessness"},
        "Immediate Cardiac/Pulmonary Risk (MI or PE)",
        "cardiology", 1
    ),
    (
        {"dizziness", "sbp_below_90"},
        "Shock / Hypotension / Internal Bleeding Risk",
        "trauma", 1
    ),
    (
        {"drooping_face", "stroke_symptoms"},
        "Acute Stroke — Activate Neurology",
        "neurology", 1
    ),
    (
        {"high_fever", "stiff_neck"},
        "Possible Meningitis — Isolate and Neurology Consult",
        "neurology", 1
    ),
    (
        {"high_fever", "confusion"},
        "Septic Encephalopathy Risk",
        "infectious_disease", 2
    ),
    (
        {"suicidal_ideation", "lethargy"},
        "High-Risk Psychiatric Emergency",
        "psychiatry", 2
    ),

    # --- Vitals + Vitals ---
    (
        {"sbp_below_90", "hr_above_130"},
        "Hemodynamic Instability / Distributive Shock",
        "trauma", 1
    ),
    (
        {"spo2_below_90", "rr_above_30"},
        "Acute Respiratory Failure",
        "pulmonology", 1
    ),
]
# CRITICAL_INTERACTIONS tuple format:
#   ( frozenset_of_keys, clinical_note, suggested_dept, esi_upgrade_amount )
# esi_upgrade_amount: how many ESI levels to upgrade (e.g. 1 = more urgent by 1 level)

# ===========================================================================
# ESI SCORE → TRIAGE LEVEL MAPPING
# ===========================================================================
# Used by data_generator.py to assign ground truth labels and by predict.py
# to interpret model output scores.
# Format: list of (min_score_inclusive, esi_level) sorted descending by score.

SCORE_TO_ESI = [
    (12, 1),   # score >= 12 → ESI 1 (Resuscitation)
    (8,  2),   # score >= 8  → ESI 2 (Emergent)
    (5,  3),   # score >= 5  → ESI 3 (Urgent)
    (2,  4),   # score >= 2  → ESI 4 (Less Urgent)
    (0,  5),   # score >= 0  → ESI 5 (Non-Urgent)
]

def score_to_esi(score: int) -> int:
    """Convert raw triage score to ESI level (1–5)."""
    for threshold, level in SCORE_TO_ESI:
        if score >= threshold:
            return level
    return 5

# ===========================================================================
# DEPARTMENT ROUTING
# ===========================================================================
# Primary symptom → department mapping for predict.py output.
# CRITICAL_INTERACTIONS override this when a matching interaction fires.

DEPT_ROUTING = {
    "cardiac_arrest":           "cardiology",
    "chest_pain":               "cardiology",
    "palpitations":             "cardiology",
    "severe_breathlessness":    "pulmonology",
    "cough":                    "pulmonology",
    "stroke_symptoms":          "neurology",
    "drooping_face":            "neurology",
    "severe_headache":          "neurology",
    "stiff_neck":               "neurology",
    "confusion":                "neurology",
    "active_seizure":           "neurology",
    "moderate_abdominal_pain":  "gastroenterology",
    "mild_abdominal_pain":      "gastroenterology",
    "persistent_vomiting":      "gastroenterology",
    "diarrhea":                 "gastroenterology",
    "coughing_blood":           "gastroenterology",
    "closed_fracture":          "orthopedics",
    "dislocation":              "orthopedics",
    "joint_pain":               "orthopedics",
    "severe_trauma":            "trauma",
    "massive_hemorrhage":       "trauma",
    "minor_cut":                "trauma",
    "severe_burns":             "trauma",
    "high_fever":               "infectious_disease",
    "mild_fever":               "infectious_disease",
    "rash":                     "infectious_disease",
    "suicidal_ideation":        "psychiatry",
    "lethargy":                 "psychiatry",
    "sudden_vision_loss":       "neurology",
    "anaphylaxis":              "general",
    "unresponsive":             "general",
    "dehydration":              "general",
    "dizziness":                "general",
    "fatigue":                  "general",
    "sore_throat":              "general",
    "earache":                  "general",
    "sugar_below_60":           "endocrinology",
    "sugar_above_300":          "endocrinology",
}

# ===========================================================================
# SYNTHETIC DATA PREVALENCE GUIDE
# ===========================================================================
# Approximate real-world ED visit distribution by ESI level.
# Use these weights in data_generator.py to create a realistic class imbalance.
# Source: US NHAMCS ED survey approximate averages.

SYNTHETIC_PREVALENCE = {
    1: 0.02,   # ESI 1 — 2% of visits
    2: 0.10,   # ESI 2 — 10%
    3: 0.35,   # ESI 3 — 35%
    4: 0.32,   # ESI 4 — 32%
    5: 0.21,   # ESI 5 — 21%
}

# Age group distribution for synthetic patient generation
AGE_GROUP_PREVALENCE = {
    "pediatric_infant": 0.04,   # 0–11 months
    "pediatric_child":  0.10,   # 1–11 years
    "adult":            0.68,   # 12–74 years
    "geriatric":        0.18,   # 75+ years
}

# ===========================================================================
# KNOWN VOCABULARIES — Dynamic Matrices
# ===========================================================================
# IMPORTANT: Adult and pediatric vitals are kept separate.
# data_generator.py must select the appropriate set per patient.

KNOWN_SYMPTOMS   = list(SYMPTOMS_WEIGHT.keys())
KNOWN_SHARED_VITALS    = list(SHARED_VITAL_WEIGHT.keys())
KNOWN_ADULT_VITALS     = list(ADULT_VITAL_WEIGHT.keys())
KNOWN_PEDIATRIC_VITALS = list(PEDIATRIC_VITAL_WEIGHT.keys())
KNOWN_NEURO      = list(NEURO_WEIGHT.keys())
KNOWN_MODIFIERS  = HIGH_RISK_MODIFIERS + ["none"]
KNOWN_DURATIONS  = list(TIME_RISK_MULTIPLIERS.keys())
KNOWN_DEPARTMENTS = KNOWN_DEPARTMENTS  # re-exported for convenience

# Canonical feature order for reproducibility.
# ALL scripts (data_generator.py, train.py, predict.py) must build
# feature vectors using this exact order. Never sort or reorder independently.
# For pediatric patients: set ADULT_VITAL block to 0, populate PEDIATRIC block.
# For adult patients:     set PEDIATRIC_VITAL block to 0, populate ADULT block.
FEATURE_ORDER = (
        KNOWN_SYMPTOMS
        + KNOWN_SHARED_VITALS
        + KNOWN_ADULT_VITALS
        + KNOWN_PEDIATRIC_VITALS
        + KNOWN_NEURO
        + KNOWN_MODIFIERS
        + KNOWN_DURATIONS
)

# ===========================================================================
# NORMALIZATION ALIASES — Input text → canonical vocabulary key
# ===========================================================================
# Used by the NLP pre-processing layer before scoring.
# Every value MUST exist in KNOWN_SYMPTOMS, KNOWN_ADULT_VITALS,
# KNOWN_PEDIATRIC_VITALS, KNOWN_NEURO, or KNOWN_MODIFIERS.

ALIASES = {
    # --- Vitals ---
    "low oxygen":               "spo2_below_90",
    "hypoxia":                  "spo2_below_90",
    "oxygen saturation low":    "spo2_below_90",

    # --- Neurological ---
    "coma":                     "avpu_unresponsive",
    "passed out":               "avpu_unresponsive",
    "unconscious":              "avpu_unresponsive",
    "only responds to pain":    "avpu_pain",
    "responds to voice":        "avpu_verbal",

    # --- Symptoms ---
    "sob":                      "severe_breathlessness",
    "shortness of breath":      "severe_breathlessness",
    "difficulty breathing":     "severe_breathlessness",
    "chest tightness":          "chest_pain",
    "stomach ache":             "moderate_abdominal_pain",
    "belly pain":               "moderate_abdominal_pain",
    "abdominal pain":           "moderate_abdominal_pain",
    "loose motion":             "diarrhea",
    "loose stools":             "diarrhea",
    "spitting blood":           "coughing_blood",
    "hemoptysis":               "coughing_blood",
    "face drooping":            "drooping_face",
    "facial droop":             "drooping_face",
    "heart pounding":           "palpitations",
    "racing heart":             "palpitations",
    "broken bone":              "closed_fracture",
    "fracture":                 "closed_fracture",
    "throwing up":              "persistent_vomiting",
    "vomiting":                 "persistent_vomiting",
    "very hot":                 "high_fever",
    "fever":                    "high_fever",
    "temperature":              "mild_fever",
    "fit":                      "active_seizure",
    "seizure":                  "active_seizure",
    "fits":                     "active_seizure",
    "can't see":                "sudden_vision_loss",
    "vision loss":              "sudden_vision_loss",
    "headache":                 "severe_headache",
    "head pain":                "severe_headache",
    "neck stiffness":           "stiff_neck",
    "stiff neck":               "stiff_neck",
    "altered consciousness":    "confusion",
    "disoriented":              "confusion",
    "not responding":           "unresponsive",
    "unresponsive":             "unresponsive",
    "no pulse":                 "cardiac_arrest",
    "heart stopped":            "cardiac_arrest",
    "allergic reaction":        "anaphylaxis",
    "severe allergy":           "anaphylaxis",
    "heavy bleeding":           "massive_hemorrhage",
    "bleeding out":             "massive_hemorrhage",
    "burn":                     "severe_burns",
    "scalded":                  "severe_burns",
    "accident":                 "severe_trauma",
    "road traffic accident":    "severe_trauma",
    "rta":                      "severe_trauma",
    "want to die":              "suicidal_ideation",
    "self harm":                "suicidal_ideation",
    "tired":                    "fatigue",
    "weak":                     "fatigue",
    "cut":                      "minor_cut",
    "laceration":               "minor_cut",

    # --- Modifiers ---
    "chemo":                    "immunocompromised",
    "chemotherapy":             "immunocompromised",
    "hiv":                      "immunocompromised",
    "aids":                     "immunocompromised",
    "cancer":                   "immunocompromised",
    "warfarin":                 "on_blood_thinners",
    "eliquis":                  "on_blood_thinners",
    "apixaban":                 "on_blood_thinners",
    "blood thinner":            "on_blood_thinners",
    "dialysis":                 "esrd_dialysis",
    "kidney failure":           "esrd_dialysis",
    "renal failure":            "esrd_dialysis",
    "heart failure":            "chf",
    "emphysema":                "copd",
    "previous heart attack":    "history_of_mi",
    "old mi":                   "history_of_mi",

    # --- Pregnancy (safe: requires explicit trimester from intake form) ---
    # Do NOT map bare "pregnant" — always ask for trimester.
    "first trimester":          "pregnant_1st_trimester",
    "second trimester":         "pregnant_2nd_trimester",
    "third trimester":          "pregnant_3rd_trimester",
    "9 months":                 "pregnant_3rd_trimester",
    "8 months":                 "pregnant_3rd_trimester",
    "newborn":                  "pediatric_infant",
    "neonate":                  "pediatric_infant",
    "infant":                   "pediatric_infant",
    "baby":                     "pediatric_infant",
    "elderly":                  "geriatric",
    "old age":                  "geriatric",
}

# ===========================================================================
# VALIDATION HELPER
# ===========================================================================

def validate_constants() -> list[str]:
    """
    Validate internal consistency of this constants file.
    Call this at the top of data_generator.py and train.py during development.
    Returns a list of warning strings (empty = all clear).
    """
    warnings = []

    # 1. All CRITICAL_INTERACTIONS keys must exist in vocabulary
    all_vocab = (
            set(KNOWN_SYMPTOMS)
            | set(KNOWN_SHARED_VITALS)
            | set(KNOWN_ADULT_VITALS)
            | set(KNOWN_PEDIATRIC_VITALS)
            | set(KNOWN_NEURO)
            | set(KNOWN_MODIFIERS)
    )
    for i, (keys, note, dept, _upgrade) in enumerate(CRITICAL_INTERACTIONS):
        for k in keys:
            if k not in all_vocab:
                warnings.append(
                    f"CRITICAL_INTERACTIONS[{i}]: key '{k}' not in any vocabulary dict "
                    f"(rule: '{note}')"
                )

    # 2. All ALIASES values must exist in vocabulary
    for alias, canonical in ALIASES.items():
        if canonical not in all_vocab:
            warnings.append(
                f"ALIASES: '{alias}' → '{canonical}' but '{canonical}' not in vocabulary"
            )

    # 3. DEPT_ROUTING departments must exist in KNOWN_DEPARTMENTS
    for symptom, dept in DEPT_ROUTING.items():
        if dept not in KNOWN_DEPARTMENTS:
            warnings.append(
                f"DEPT_ROUTING: symptom '{symptom}' maps to unknown dept '{dept}'"
            )

    # 4. SCORE_TO_ESI must be sorted descending
    scores = [s for s, _ in SCORE_TO_ESI]
    if scores != sorted(scores, reverse=True):
        warnings.append("SCORE_TO_ESI is not sorted in descending score order")

    # 5. SYNTHETIC_PREVALENCE must sum to ~1.0
    total = sum(SYNTHETIC_PREVALENCE.values())
    if not (0.99 <= total <= 1.01):
        warnings.append(f"SYNTHETIC_PREVALENCE sums to {total:.3f}, expected ~1.0")

    # 6. FEATURE_ORDER must have no duplicates
    if len(FEATURE_ORDER) != len(set(FEATURE_ORDER)):
        dupes = [f for f in FEATURE_ORDER if FEATURE_ORDER.count(f) > 1]
        warnings.append(f"FEATURE_ORDER has duplicates: {list(set(dupes))}")

    return warnings


if __name__ == "__main__":
    issues = validate_constants()
    if not issues:
        print(f"[constants v{EXPERIMENT_VERSION}] All validation checks passed.")
        print(f"  Symptoms:          {len(KNOWN_SYMPTOMS)}")
        print(f"  Shared vitals:     {len(KNOWN_SHARED_VITALS)}")
        print(f"  Adult vitals:      {len(KNOWN_ADULT_VITALS)}")
        print(f"  Pediatric vitals:  {len(KNOWN_PEDIATRIC_VITALS)}")
        print(f"  Neuro markers:     {len(KNOWN_NEURO)}")
        print(f"  Modifiers:         {len(KNOWN_MODIFIERS)}")
        print(f"  Durations:         {len(KNOWN_DURATIONS)}")
        print(f"  Feature vector:    {len(FEATURE_ORDER)} dimensions")
        print(f"  Aliases:           {len(ALIASES)}")
        print(f"  Interactions:      {len(CRITICAL_INTERACTIONS)}")
    else:
        print(f"[constants v{EXPERIMENT_VERSION}] {len(issues)} issue(s) found:")
        for w in issues:
            print(f"  ⚠  {w}")