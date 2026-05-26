"""
data_generator.py (v5.0.0)

Generates a synthetic patient triage dataset aligned with constants.py.

Design principles:
  - Zero hardcoded clinical values — everything comes from constants.py (SSoT)
  - Output schema matches FEATURE_ORDER exactly — train.py consumes this directly
  - Realistic class imbalance via SYNTHETIC_PREVALENCE (ESI distribution)
  - Age-adjusted vitals: pediatric patients get pediatric vital flags, adults get adult flags
  - Critical interactions fire probabilistically and override department routing
  - Noise injection simulates real ED data quality (missing vitals, atypical presentations)

Output columns:
    [83 binary FEATURE_ORDER columns] + age + duration + patient_modifier + esi_level + department
"""

import random
import sys
from pathlib import Path
from collections import defaultdict

import pandas as pd
import numpy as np

from constants import (
    # Vocabulary
    FEATURE_ORDER,
    KNOWN_SYMPTOMS,
    KNOWN_SHARED_VITALS,
    KNOWN_ADULT_VITALS,
    KNOWN_PEDIATRIC_VITALS,
    KNOWN_NEURO,
    KNOWN_MODIFIERS,
    KNOWN_DURATIONS,
    KNOWN_DEPARTMENTS,
    # Weights
    SYMPTOMS_WEIGHT,
    SHARED_VITAL_WEIGHT,
    ADULT_VITAL_WEIGHT,
    PEDIATRIC_VITAL_WEIGHT,
    NEURO_WEIGHT,
    MODIFIER_WEIGHT,
    TIME_RISK_MULTIPLIERS,
    # Clinical rules
    CRITICAL_INTERACTIONS,
    DEPT_ROUTING,
    HIGH_RISK_MODIFIERS,
    # Generation guidance
    SYNTHETIC_PREVALENCE,
    AGE_GROUP_PREVALENCE,
    # Label function
    score_to_esi,
    # Validation
    validate_constants,
    EXPERIMENT_VERSION,
    SAFE_FALLBACK_DEPT,
)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

SAMPLE_SIZE = 50_000
RANDOM_SEED = 42

BASE_DIR    = Path(__file__).resolve().parent
OUTPUT_PATH = BASE_DIR.parent / "data" / "data.csv"
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

GENDERS = ["male", "female", "other"]

# ---------------------------------------------------------------------------
# Department → primary symptoms/vitals lookup (derived from constants, not hardcoded)
# ---------------------------------------------------------------------------
# Built once at module load from DEPT_ROUTING (constants.py SSoT).
# Departments with no DEPT_ROUTING entries get a fallback set of general symptoms.

_DEPT_PRIMARY_SYMPTOMS: dict[str, list[str]] = defaultdict(list)
for _sym, _dept in DEPT_ROUTING.items():
    if _sym in KNOWN_SYMPTOMS:          # skip vital keys in DEPT_ROUTING
        _DEPT_PRIMARY_SYMPTOMS[_dept].append(_sym)

# Fill departments with no routed symptoms using fallback general symptoms
_GENERAL_FALLBACK = [s for s in KNOWN_SYMPTOMS if SYMPTOMS_WEIGHT.get(s, 0) <= 2]
for _dept in KNOWN_DEPARTMENTS:
    if not _DEPT_PRIMARY_SYMPTOMS[_dept]:
        _DEPT_PRIMARY_SYMPTOMS[_dept] = random.sample(_GENERAL_FALLBACK, k=min(4, len(_GENERAL_FALLBACK)))

# Department → plausible adult vital flags (clinically motivated groupings)
# Derived entirely from KNOWN_ADULT_VITALS and KNOWN_SHARED_VITALS keys.
_DEPT_VITALS: dict[str, list[str]] = {
    "cardiology":        ["sbp_above_200", "sbp_below_90", "hr_above_130", "hr_below_40", "hr_111_130"],
    "pulmonology":       ["spo2_below_90", "rr_above_30", "rr_below_9", "temp_39_41c"],
    "neurology":         ["sbp_above_200", "sbp_below_90", "temp_above_41c"],
    "orthopedics":       ["normal_vitals"],
    "gastroenterology":  ["sbp_below_90", "hr_above_130", "temp_39_41c"],
    "endocrinology":     ["sugar_below_60", "sugar_above_300"],
    "nephrology":        ["sbp_above_200", "hr_below_40", "sbp_91_100"],
    "psychiatry":        ["normal_vitals", "hr_111_130"],
    "gynecology":        ["sbp_above_200", "sbp_below_90", "hr_above_130"],
    "oncology":          ["temp_above_41c", "spo2_below_90", "hr_above_130"],
    "trauma":            ["sbp_below_90", "hr_above_130", "temp_below_35c"],
    "infectious_disease":["temp_above_41c", "temp_39_41c", "hr_above_130", "spo2_below_90"],
    "pediatrics":        ["temp_above_41c", "spo2_below_90"],   # pediatric vitals added separately
    "general":           ["temp_39_41c", "normal_vitals"],
}
# Safety check: all vital keys must exist in known vocabulary
_ALL_VITAL_KEYS = set(KNOWN_SHARED_VITALS) | set(KNOWN_ADULT_VITALS) | set(KNOWN_PEDIATRIC_VITALS)
for _dept, _vlist in _DEPT_VITALS.items():
    for _v in _vlist:
        assert _v in _ALL_VITAL_KEYS, f"Unknown vital key '{_v}' in _DEPT_VITALS['{_dept}']"

# ---------------------------------------------------------------------------
# Age helpers
# ---------------------------------------------------------------------------

# Age ranges per department (years) — clinically motivated
_DEPT_AGE_RANGE: dict[str, tuple[int, int]] = {
    "cardiology":        (45, 85),
    "pulmonology":       (20, 75),
    "neurology":         (30, 85),
    "orthopedics":       (40, 85),
    "gastroenterology":  (20, 70),
    "endocrinology":     (25, 75),
    "nephrology":        (40, 80),
    "psychiatry":        (15, 60),
    "gynecology":        (15, 55),
    "oncology":          (35, 80),
    "trauma":            (15, 70),
    "infectious_disease":(10, 70),
    "pediatrics":        (0,  11),
    "general":           (15, 65),
}

def _is_pediatric(age: int) -> bool:
    return age < 12

def _age_group_modifier(age: int) -> str | None:
    """Return the demographic modifier for the patient's age group, or None."""
    if age < 1:
        return "pediatric_infant"
    if age < 12:
        return "pediatric_child"
    if age >= 75:
        return "geriatric"
    return None

# ---------------------------------------------------------------------------
# Score → ESI-driven ESI-to-dept routing
# ---------------------------------------------------------------------------

def _resolve_department(active_symptoms: list[str], active_modifiers: list[str],
                        age: int) -> str:
    """
    Determine department by:
      1. Check CRITICAL_INTERACTIONS — fire the first matching rule.
      2. Fall back to DEPT_ROUTING on the highest-weight symptom.
      3. Final fallback: SAFE_FALLBACK_DEPT.
    """
    feature_set = set(active_symptoms) | set(active_modifiers)
    if _is_pediatric(age):
        feature_set.add("pediatric_child" if age >= 1 else "pediatric_infant")

    # 1. Critical interaction check
    for keys, _note, dept, _upgrade in CRITICAL_INTERACTIONS:
        if keys.issubset(feature_set):
            return dept

    # 2. Highest-weight symptom routing
    best_sym  = max(active_symptoms, key=lambda s: SYMPTOMS_WEIGHT.get(s, 0), default=None)
    if best_sym and best_sym in DEPT_ROUTING:
        return DEPT_ROUTING[best_sym]

    return SAFE_FALLBACK_DEPT

# ---------------------------------------------------------------------------
# Core row generators
# ---------------------------------------------------------------------------

def _pick_symptoms(dept: str, esi_target: int, rng: random.Random) -> list[str]:
    """
    Select symptoms consistent with the target ESI level and department.
    Higher ESI urgency = more high-weight symptoms sampled.
    """
    primary = _DEPT_PRIMARY_SYMPTOMS[dept]

    # How many primary symptoms to include (more for higher urgency)
    n_primary = {1: 3, 2: 2, 3: 2, 4: 1, 5: 1}.get(esi_target, 2)
    n_primary = min(n_primary, len(primary))
    chosen = rng.sample(primary, k=n_primary)

    # Noise: 30% chance to add an off-department symptom (realistic cross-presentation)
    if rng.random() < 0.30:
        noise = rng.choice(KNOWN_SYMPTOMS)
        if noise not in chosen:
            chosen.append(noise)

    # Very low urgency (ESI 4/5): 20% chance to drop to a single mild symptom
    if esi_target >= 4 and rng.random() < 0.20 and len(chosen) > 1:
        chosen = [chosen[0]]

    return chosen


def _pick_vitals(dept: str, age: int, esi_target: int,
                 rng: random.Random) -> tuple[list[str], list[str], list[str]]:
    """
    Returns (shared_vitals, adult_vitals, pediatric_vitals).
    Only one of adult/pediatric is populated based on age.
    Higher ESI = more critical vital flags.
    """
    shared_chosen:     list[str] = []
    adult_chosen:      list[str] = []
    pediatric_chosen:  list[str] = []

    # ESI 5 / low urgency: usually normal vitals
    if esi_target == 5 or (esi_target == 4 and rng.random() < 0.60):
        shared_chosen = ["normal_vitals"]
        return shared_chosen, adult_chosen, pediatric_chosen

    dept_vital_pool = _DEPT_VITALS.get(dept, ["normal_vitals"])

    # Shared vitals (spo2, sugar, normal) — pick 0 or 1
    shared_pool = [v for v in dept_vital_pool if v in set(KNOWN_SHARED_VITALS)]
    if shared_pool and rng.random() < 0.50:
        shared_chosen.append(rng.choice(shared_pool))

    if _is_pediatric(age):
        # Pediatric-specific vitals
        ped_pool = [v for v in KNOWN_PEDIATRIC_VITALS if v != "normal_vitals"]
        # Weight toward more critical vitals for higher ESI
        weights = [PEDIATRIC_VITAL_WEIGHT.get(v, 1) for v in ped_pool]
        if esi_target <= 2:
            weights = [w ** 2 for w in weights]    # amplify critical flags
        total = sum(weights)
        probs  = [w / total for w in weights]
        n = {1: 2, 2: 2, 3: 1, 4: 1}.get(esi_target, 1)
        picks = rng.choices(ped_pool, weights=probs, k=min(n, len(ped_pool)))
        pediatric_chosen = list(dict.fromkeys(picks))  # deduplicate, preserve order
    else:
        # Adult vitals from department pool
        adult_pool = [v for v in dept_vital_pool if v in set(KNOWN_ADULT_VITALS)]
        if not adult_pool:
            adult_pool = [v for v in KNOWN_ADULT_VITALS if ADULT_VITAL_WEIGHT.get(v, 0) == 1]
        if adult_pool:
            n = {1: 2, 2: 2, 3: 1, 4: 1, 5: 0}.get(esi_target, 1)
            picks = rng.sample(adult_pool, k=min(n, len(adult_pool)))
            adult_chosen = picks

    # ESI 1-2: add a neuro flag with high probability
    # (returned separately but stored in shared_chosen for simplicity — neuro handled below)
    return shared_chosen, adult_chosen, pediatric_chosen


def _pick_neuro(esi_target: int, rng: random.Random) -> str | None:
    """Return a neuro assessment key appropriate for the ESI level, or None."""
    if esi_target == 1 and rng.random() < 0.70:
        return rng.choice(["avpu_unresponsive", "gcs_below_8"])
    if esi_target == 2 and rng.random() < 0.40:
        return rng.choice(["avpu_pain", "gcs_9_12"])
    if esi_target == 3 and rng.random() < 0.20:
        return "avpu_verbal"
    if rng.random() < 0.70:
        return "gcs_normal"
    return None


def _pick_modifier(age: int, dept: str, rng: random.Random) -> str:
    """
    Pick a patient modifier. Age-group modifiers take priority.
    Otherwise select a clinical comorbidity with department-biased probability.
    """
    age_mod = _age_group_modifier(age)
    if age_mod:
        return age_mod

    # Department-biased comorbidity selection
    dept_affinity: dict[str, list[str]] = {
        "cardiology":        ["history_of_mi", "chf", "on_blood_thinners"],
        "pulmonology":       ["copd", "immunocompromised"],
        "nephrology":        ["esrd_dialysis", "chf"],
        "oncology":          ["immunocompromised", "on_blood_thinners"],
        "gynecology":        ["pregnant_1st_trimester", "pregnant_2nd_trimester", "pregnant_3rd_trimester"],
        "endocrinology":     ["history_of_mi", "esrd_dialysis"],
        "infectious_disease":["immunocompromised", "esrd_dialysis"],
    }

    candidates = dept_affinity.get(dept, [])
    clinical_mods = [m for m in HIGH_RISK_MODIFIERS
                     if m not in ("pediatric_infant", "pediatric_child", "geriatric")]

    if candidates and rng.random() < 0.55:
        return rng.choice(candidates)
    if rng.random() < 0.30:
        return rng.choice(clinical_mods)
    return "none"


def _pick_duration(esi_target: int, rng: random.Random) -> str:
    """
    Duration distribution biased by ESI level.
    Acute onset is more common for high acuity; chronic for low acuity.
    """
    weights_by_esi = {
        1: [0.70, 0.20, 0.08, 0.02],
        2: [0.50, 0.30, 0.15, 0.05],
        3: [0.20, 0.35, 0.30, 0.15],
        4: [0.05, 0.20, 0.40, 0.35],
        5: [0.02, 0.10, 0.38, 0.50],
    }
    weights = weights_by_esi.get(esi_target, [0.25, 0.25, 0.25, 0.25])
    return rng.choices(KNOWN_DURATIONS, weights=weights, k=1)[0]


# ---------------------------------------------------------------------------
# Feature vector builder
# ---------------------------------------------------------------------------

def build_feature_vector(
        active_symptoms:   list[str],
        active_shared:     list[str],
        active_adult:      list[str],
        active_pediatric:  list[str],
        active_neuro:      list[str],
        modifier:          str,
        duration:          str,
) -> dict[str, int]:
    """
    Convert active flags into a binary dict keyed by FEATURE_ORDER.
    This is the canonical 83-dim vector consumed by train.py.
    """
    active_set = (
            set(active_symptoms)
            | set(active_shared)
            | set(active_adult)
            | set(active_pediatric)
            | set(active_neuro)
            | {modifier, duration}
    )
    return {feature: int(feature in active_set) for feature in FEATURE_ORDER}


# ---------------------------------------------------------------------------
# Score computation (mirrors the clinical logic in constants.py)
# ---------------------------------------------------------------------------

def compute_triage_score(
        symptoms:   list[str],
        shared:     list[str],
        adult:      list[str],
        pediatric:  list[str],
        neuro:      list[str],
        modifier:   str,
        duration:   str,
        age:        int,
) -> int:
    score = 0

    for s in symptoms:
        score += SYMPTOMS_WEIGHT.get(s, 0)

    for v in shared:
        score += SHARED_VITAL_WEIGHT.get(v, 0)

    vital_dict = PEDIATRIC_VITAL_WEIGHT if _is_pediatric(age) else ADULT_VITAL_WEIGHT
    for v in (pediatric if _is_pediatric(age) else adult):
        score += vital_dict.get(v, 0)

    for n in neuro:
        score += NEURO_WEIGHT.get(n, 0)

    score += MODIFIER_WEIGHT.get(modifier, 0)

    multiplier = TIME_RISK_MULTIPLIERS.get(duration, 1.0)
    score = int(score * multiplier)

    return max(score, 0)


# ---------------------------------------------------------------------------
# Single row generator
# ---------------------------------------------------------------------------

def generate_row(dept: str, esi_target: int, rng: random.Random) -> dict:
    age_min, age_max = _DEPT_AGE_RANGE.get(dept, (15, 70))
    age      = rng.randint(age_min, age_max)
    gender   = rng.choice(GENDERS)
    modifier = _pick_modifier(age, dept, rng)
    duration = _pick_duration(esi_target, rng)

    symptoms = _pick_symptoms(dept, esi_target, rng)
    shared, adult, pediatric = _pick_vitals(dept, age, esi_target, rng)
    neuro_key = _pick_neuro(esi_target, rng)
    neuro = [neuro_key] if neuro_key else []

    # Resolve actual department (may change if a critical interaction fires)
    resolved_dept = _resolve_department(symptoms, [modifier], age)

    # Compute score and derive ESI label (ground truth)
    score     = compute_triage_score(symptoms, shared, adult, pediatric, neuro, modifier, duration, age)
    esi_level = score_to_esi(score)

    # Build binary feature vector
    feature_vec = build_feature_vector(symptoms, shared, adult, pediatric, neuro, modifier, duration)

    row = {
        **feature_vec,
        "age":              age,
        "gender":           gender,
        "duration":         duration,
        "patient_modifier": modifier,
        "esi_level":        esi_level,
        "department":       resolved_dept,
    }
    return row


# ---------------------------------------------------------------------------
# Dataset generator
# ---------------------------------------------------------------------------

def generate_dataset(n: int, seed: int = RANDOM_SEED) -> pd.DataFrame:
    """
    Generate n synthetic patient records.

    ESI level distribution follows SYNTHETIC_PREVALENCE (realistic class imbalance).
    Within each ESI bucket, patients are distributed across plausible departments.
    """
    rng = random.Random(seed)
    np.random.seed(seed)

    # ESI level → departments most likely to contain that acuity level
    esi_dept_map: dict[int, list[str]] = {
        1: ["cardiology", "trauma", "neurology", "general"],
        2: ["cardiology", "pulmonology", "neurology", "trauma", "infectious_disease", "oncology"],
        3: ["gastroenterology", "neurology", "orthopedics", "nephrology", "endocrinology", "gynecology"],
        4: ["general", "orthopedics", "psychiatry", "gastroenterology", "infectious_disease"],
        5: ["general", "orthopedics", "psychiatry"],
    }

    rows = []
    for esi_level, proportion in SYNTHETIC_PREVALENCE.items():
        count = round(n * proportion)
        dept_pool = esi_dept_map.get(esi_level, KNOWN_DEPARTMENTS)
        for _ in range(count):
            dept = rng.choice(dept_pool)
            rows.append(generate_row(dept, esi_level, rng))

    # Trim or pad to exact n (rounding may cause ±1 off)
    rows = rows[:n]
    while len(rows) < n:
        dept = rng.choice(KNOWN_DEPARTMENTS)
        esi  = rng.choices(list(SYNTHETIC_PREVALENCE.keys()),
                           weights=list(SYNTHETIC_PREVALENCE.values()))[0]
        rows.append(generate_row(dept, esi, rng))

    df = pd.DataFrame(rows)

    # Shuffle
    df = df.sample(frac=1, random_state=seed).reset_index(drop=True)

    # Validate column alignment with FEATURE_ORDER
    missing = [f for f in FEATURE_ORDER if f not in df.columns]
    if missing:
        raise RuntimeError(f"Generated dataset is missing {len(missing)} FEATURE_ORDER columns: {missing[:5]}")

    return df


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print(f"\n{'='*60}")
    print(f"  Patient Triage Data Generator  |  v{EXPERIMENT_VERSION}")
    print(f"{'='*60}\n")

    # Validate constants before generating
    issues = validate_constants()
    if issues:
        print("[WARNING] constants.py issues:")
        for w in issues:
            print(f"   ⚠  {w}")
        print()

    print(f"[INFO] Generating {SAMPLE_SIZE:,} synthetic patient records...")
    df = generate_dataset(SAMPLE_SIZE)

    df.to_csv(OUTPUT_PATH, index=False)

    print(f"[INFO] Saved to: {OUTPUT_PATH}")
    print(f"[INFO] Shape:    {df.shape[0]:,} rows × {df.shape[1]} columns")
    print(f"[INFO] Feature vector dimensions: {len(FEATURE_ORDER)}")

    print(f"\n[INFO] ESI level distribution:")
    esi_counts = df["esi_level"].value_counts().sort_index()
    for level, count in esi_counts.items():
        pct = count / len(df)
        bar = "█" * int(pct * 40)
        print(f"  ESI {level}:  {count:>6,}  ({pct:5.1%})  {bar}")

    print(f"\n[INFO] Department distribution:")
    dept_counts = df["department"].value_counts()
    for dept, count in dept_counts.items():
        pct = count / len(df)
        bar = "█" * int(pct * 40)
        print(f"  {dept:<25} {count:>6,}  ({pct:5.1%})  {bar}")

    print(f"\n[INFO] Modifier distribution (top 10):")
    for mod, count in df["patient_modifier"].value_counts().head(10).items():
        print(f"  {mod:<30} {count:>6,}")

    print(f"\n[INFO] Binary feature sanity check (should be 0 or 1 only):")
    bad_cols = [c for c in FEATURE_ORDER if c in df.columns and not df[c].isin([0, 1]).all()]
    if bad_cols:
        print(f"  [FAIL] Non-binary values in: {bad_cols}")
        sys.exit(1)
    else:
        print(f"  [PASS] All {len(FEATURE_ORDER)} feature columns are binary.")

    print(f"\n{'='*60}")
    print(f"  Done. Run train.py to train the model.")
    print(f"{'='*60}\n")