"""
predict.py (v5.0.0)

Patient triage inference engine.

Takes free-text symptom/vital input, normalises it to canonical vocabulary,
builds the same 83-dim binary feature vector used in training, and returns
a structured triage result.

Usage (CLI):
    python predict.py

Usage (import):
    from predict import predict_case
    result = predict_case(
        symptoms="chest pain, breathlessness",
        vitals="sbp_below_90, hr_above_130",
        age=65,
        duration="acute_under_6_hours",
        modifier="history_of_mi"
    )
"""

import json
import logging
import difflib
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

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
    # Weights (for score computation and emergency detection)
    SYMPTOMS_WEIGHT,
    SHARED_VITAL_WEIGHT,
    ADULT_VITAL_WEIGHT,
    PEDIATRIC_VITAL_WEIGHT,
    NEURO_WEIGHT,
    MODIFIER_WEIGHT,
    TIME_RISK_MULTIPLIERS,
    # Clinical rules
    ALIASES,
    CRITICAL_INTERACTIONS,
    DEPT_ROUTING,
    # Output helpers
    score_to_esi,
    CONFIDENCE_THRESHOLD,
    SAFE_FALLBACK_DEPT,
    EXPERIMENT_VERSION,
)

# ---------------------------------------------------------------------------
# Paths & logging
# ---------------------------------------------------------------------------

BASE_DIR       = Path(__file__).resolve().parent
MODEL_DIR      = BASE_DIR / "models"
PIPELINE_PATH  = MODEL_DIR / "triage_pipeline.pkl"
LOG_PATH       = BASE_DIR.parent / "logs" / "triage.log"
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=str(LOG_PATH),
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Load model (once at import time)
# ---------------------------------------------------------------------------

if not PIPELINE_PATH.exists():
    raise FileNotFoundError(
        f"Trained pipeline not found at {PIPELINE_PATH}. "
        "Run train.py first."
    )

_pipeline = joblib.load(PIPELINE_PATH)

# ---------------------------------------------------------------------------
# Derived emergency sets (from constants weights — no hardcoding)
# ---------------------------------------------------------------------------
# ESI-1 symptoms (weight == 4) and ESI-2 symptoms (weight == 3) trigger
# immediate emergency flag regardless of model confidence.

_EMERGENCY_SYMPTOMS: frozenset[str] = frozenset(
    s for s, w in SYMPTOMS_WEIGHT.items() if w >= 3
)
_EMERGENCY_VITALS: frozenset[str] = frozenset(
    v for v, w in {**SHARED_VITAL_WEIGHT, **ADULT_VITAL_WEIGHT, **PEDIATRIC_VITAL_WEIGHT}.items()
    if w >= 3
)
_EMERGENCY_NEURO: frozenset[str] = frozenset(
    n for n, w in NEURO_WEIGHT.items() if w >= 3
)

# All canonical keys across every vocabulary block
_ALL_KNOWN: list[str] = (
        KNOWN_SYMPTOMS
        + KNOWN_SHARED_VITALS
        + KNOWN_ADULT_VITALS
        + KNOWN_PEDIATRIC_VITALS
        + KNOWN_NEURO
        + KNOWN_MODIFIERS
        + KNOWN_DURATIONS
)

# ---------------------------------------------------------------------------
# Input normalisation
# ---------------------------------------------------------------------------

def _normalise_term(raw: str) -> str | None:
    """
    Map a raw input string to a canonical vocabulary key.

    Resolution order:
      1. Direct match in ALIASES
      2. Direct match in any known vocabulary list
      3. Space/underscore swap
      4. Fuzzy match (cutoff 0.75)
      5. Return None (unrecognised — caller decides how to handle)
    """
    term = raw.strip().lower()

    if term in ALIASES:
        return ALIASES[term]

    if term in _ALL_KNOWN:
        return term

    swapped = term.replace(" ", "_") if " " in term else term.replace("_", " ")
    if swapped in _ALL_KNOWN:
        return swapped

    matches = difflib.get_close_matches(term, _ALL_KNOWN, n=1, cutoff=0.75)
    if matches:
        return matches[0]

    return None


def _parse_csv_input(raw: str) -> list[str]:
    """Split a comma-separated input string into a cleaned list."""
    return [t.strip().lower() for t in raw.split(",") if t.strip()]


def _classify_terms(
        raw_terms: list[str],
) -> tuple[list[str], list[str], list[str], list[str], list[str], list[str]]:
    """
    Classify a flat list of normalised canonical keys into their vocabulary buckets.
    Returns (symptoms, shared_vitals, adult_vitals, pediatric_vitals, neuro, modifiers).
    Unrecognised keys are silently dropped (already warned by caller).
    """
    symptoms, shared, adult, pediatric, neuro, modifiers = [], [], [], [], [], []

    sym_set  = set(KNOWN_SYMPTOMS)
    sha_set  = set(KNOWN_SHARED_VITALS)
    adl_set  = set(KNOWN_ADULT_VITALS)
    ped_set  = set(KNOWN_PEDIATRIC_VITALS)
    neu_set  = set(KNOWN_NEURO)
    mod_set  = set(KNOWN_MODIFIERS)

    for term in raw_terms:
        if   term in sym_set:  symptoms.append(term)
        elif term in sha_set:  shared.append(term)
        elif term in adl_set:  adult.append(term)
        elif term in ped_set:  pediatric.append(term)
        elif term in neu_set:  neuro.append(term)
        elif term in mod_set:  modifiers.append(term)

    return symptoms, shared, adult, pediatric, neuro, modifiers


# ---------------------------------------------------------------------------
# Feature vector builder (mirrors data_generator.py exactly)
# ---------------------------------------------------------------------------

def _build_feature_vector(
        symptoms:   list[str],
        shared:     list[str],
        adult:      list[str],
        pediatric:  list[str],
        neuro:      list[str],
        modifier:   str,
        duration:   str,
) -> dict[str, int]:
    active = set(symptoms) | set(shared) | set(adult) | set(pediatric) | set(neuro) | {modifier, duration}
    return {f: int(f in active) for f in FEATURE_ORDER}


# ---------------------------------------------------------------------------
# Triage score (mirrors data_generator.compute_triage_score)
# ---------------------------------------------------------------------------

def _compute_score(
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
    is_ped = age < 12

    for s in symptoms:
        score += SYMPTOMS_WEIGHT.get(s, 0)
    for v in shared:
        score += SHARED_VITAL_WEIGHT.get(v, 0)

    vital_dict = PEDIATRIC_VITAL_WEIGHT if is_ped else ADULT_VITAL_WEIGHT
    for v in (pediatric if is_ped else adult):
        score += vital_dict.get(v, 0)

    for n in neuro:
        score += NEURO_WEIGHT.get(n, 0)

    score += MODIFIER_WEIGHT.get(modifier, 0)

    multiplier = TIME_RISK_MULTIPLIERS.get(duration, 1.0)
    return max(int(score * multiplier), 0)


# ---------------------------------------------------------------------------
# Critical interaction checker
# ---------------------------------------------------------------------------

def _check_interactions(
        feature_set: set[str],
) -> list[dict]:
    """
    Return all firing CRITICAL_INTERACTIONS as a list of dicts.
    Each dict has: keys, note, suggested_dept, esi_upgrade.
    """
    fired = []
    for keys, note, dept, upgrade in CRITICAL_INTERACTIONS:
        if keys.issubset(feature_set):
            fired.append({
                "keys":          sorted(keys),
                "note":          note,
                "suggested_dept": dept,
                "esi_upgrade":   upgrade,
            })
    return fired


# ---------------------------------------------------------------------------
# Duration / modifier resolution helpers
# ---------------------------------------------------------------------------

def _resolve_duration(raw: str) -> str:
    """Map a raw duration string to a KNOWN_DURATIONS key."""
    norm = _normalise_term(raw)
    if norm in KNOWN_DURATIONS:
        return norm

    # Accept integer days as a convenience
    try:
        days = int(raw)
        if days < 1:
            return "standard"
        if days <= 1:
            return "acute_under_6_hours"
        if days <= 1:
            return "acute_under_6_hours"
        if days <= 3:
            return "subacute_under_24_hours"
        if days <= 30:
            return "standard"
        return "chronic_over_30_days"
    except (ValueError, TypeError):
        pass

    return "standard"   # safe fallback


def _resolve_modifier(raw: str) -> str:
    """Map a raw modifier string to a KNOWN_MODIFIERS key."""
    if not raw or raw.strip().lower() in ("", "none", "no", "nil"):
        return "none"
    norm = _normalise_term(raw.strip().lower())
    return norm if norm in KNOWN_MODIFIERS else "none"


# ---------------------------------------------------------------------------
# Main prediction function
# ---------------------------------------------------------------------------

def predict_case(
        symptoms:   str,
        vitals:     str  = "",
        age:        int  = 30,
        duration:   str  = "standard",
        modifier:   str  = "none",
) -> dict:
    """
    Predict triage department and priority for a patient presentation.

    Parameters
    ----------
    symptoms : str
        Comma-separated symptom terms (free text or canonical keys).
        Example: "chest pain, breathlessness" or "chest_pain, severe_breathlessness"
    vitals : str
        Comma-separated vital/neuro flags (optional).
        Example: "sbp_below_90, hr_above_130" or "low oxygen"
    age : int
        Patient age in years (1–120).
    duration : str
        One of KNOWN_DURATIONS, or integer days as a string.
        Example: "acute_under_6_hours" or "2"
    modifier : str
        One of KNOWN_MODIFIERS or free-text comorbidity.
        Example: "history_of_mi" or "warfarin"

    Returns
    -------
    dict with keys:
        recommended       — top department string
        departments       — list of {department, confidence} (top 3)
        esi_level         — int 1–5
        priority          — "immediate" | "emergent" | "urgent" | "less_urgent" | "non_urgent"
        emergency         — bool — true if any ESI-1/2 symptom or critical vital present
        confidence        — float, top department confidence
        score             — raw triage score (int)
        interactions      — list of fired critical interaction dicts
        reasons           — list of reason strings for the triage decision
        unrecognised      — list of input terms that could not be normalised
        vitals_missing    — bool
        model_version     — str
    """
    # --- Input validation ---
    if not isinstance(symptoms, str) or not symptoms.strip():
        raise ValueError("symptoms must be a non-empty string.")
    if not isinstance(age, (int, float)) or not (1 <= int(age) <= 120):
        raise ValueError(f"age must be between 1 and 120, got {age!r}.")

    age          = int(age)
    vitals_missing = not vitals.strip()

    # --- Parse and normalise all input terms ---
    raw_symptom_terms = _parse_csv_input(symptoms)
    raw_vital_terms   = _parse_csv_input(vitals) if not vitals_missing else []

    all_raw = raw_symptom_terms + raw_vital_terms
    normalised_map: dict[str, str | None] = {t: _normalise_term(t) for t in all_raw}

    unrecognised = [raw for raw, canon in normalised_map.items() if canon is None]
    canon_terms  = [canon for canon in normalised_map.values() if canon is not None]

    # Classify into vocabulary buckets
    sym, shared, adult, pediatric, neuro, mods = _classify_terms(canon_terms)

    # Modifier and duration
    resolved_modifier = _resolve_modifier(modifier)
    resolved_duration = _resolve_duration(str(duration))

    # Age-group modifier override (demographic context)
    if age < 1:
        resolved_modifier = "pediatric_infant"
    elif age < 12 and resolved_modifier == "none":
        resolved_modifier = "pediatric_child"
    elif age >= 75 and resolved_modifier == "none":
        resolved_modifier = "geriatric"

    # If no symptoms were recognised, abort
    if not sym and not shared and not adult and not pediatric and not neuro:
        raise ValueError(
            "No recognisable symptoms or vitals found. "
            f"Unrecognised terms: {unrecognised}"
        )

    # --- Build feature vector (83-dim binary) ---
    feature_vec = _build_feature_vector(
        sym, shared, adult, pediatric, neuro, resolved_modifier, resolved_duration
    )

    # --- Compute clinical score and ESI level ---
    score     = _compute_score(sym, shared, adult, pediatric, neuro,
                               resolved_modifier, resolved_duration, age)
    esi_level = score_to_esi(score)

    # --- Check critical interactions ---
    feature_set = set(feature_vec.keys()) & ({k for k, v in feature_vec.items() if v == 1})
    interactions = _check_interactions(feature_set)

    # Upgrade ESI level if a critical interaction fires
    if interactions:
        max_upgrade = max(i["esi_upgrade"] for i in interactions)
        esi_level   = max(1, esi_level - max_upgrade)

    # --- Model prediction ---
    X = pd.DataFrame([{
        **feature_vec,
        "age":              age,
        "duration":         resolved_duration,
        "patient_modifier": resolved_modifier,
    }])

    try:
        probs   = _pipeline.predict_proba(X)[0]
        classes = _pipeline.classes_
    except Exception as exc:
        raise RuntimeError(f"Pipeline prediction failed: {exc}") from exc

    top_indices = np.argsort(probs)[::-1][:3]
    departments = [
        {"department": classes[i], "confidence": round(float(probs[i]), 4)}
        for i in top_indices
    ]
    top_confidence  = departments[0]["confidence"]
    recommended_dept = departments[0]["department"]

    # Override with interaction-suggested department if confidence is low
    # or if an interaction explicitly routes to a specific department
    if interactions:
        interaction_dept = interactions[0]["suggested_dept"]
        if top_confidence < CONFIDENCE_THRESHOLD or esi_level <= 2:
            recommended_dept = interaction_dept
    elif top_confidence < CONFIDENCE_THRESHOLD:
        recommended_dept = SAFE_FALLBACK_DEPT

    # --- Emergency flag ---
    active_syms_set   = set(sym)
    active_vital_set  = set(shared) | set(adult) | set(pediatric)
    active_neuro_set  = set(neuro)

    is_emergency = bool(
        active_syms_set  & _EMERGENCY_SYMPTOMS or
        active_vital_set & _EMERGENCY_VITALS    or
        active_neuro_set & _EMERGENCY_NEURO     or
        esi_level <= 2
    )

    # --- Priority label ---
    _ESI_TO_PRIORITY = {
        1: "immediate",
        2: "emergent",
        3: "urgent",
        4: "less_urgent",
        5: "non_urgent",
    }
    priority = _ESI_TO_PRIORITY[esi_level]

    # --- Reasons (human-readable explanation) ---
    reasons: list[str] = []

    for s in sym:
        if s in _EMERGENCY_SYMPTOMS or SYMPTOMS_WEIGHT.get(s, 0) >= 2:
            reasons.append(f"Symptom: {s.replace('_', ' ')} (weight {SYMPTOMS_WEIGHT.get(s, 0)})")

    for v in list(shared) + list(adult) + list(pediatric):
        w = {**SHARED_VITAL_WEIGHT, **ADULT_VITAL_WEIGHT, **PEDIATRIC_VITAL_WEIGHT}.get(v, 0)
        if w >= 2:
            reasons.append(f"Vital: {v.replace('_', ' ')} (weight {w})")

    for n in neuro:
        w = NEURO_WEIGHT.get(n, 0)
        if w >= 2:
            reasons.append(f"Neuro: {n.replace('_', ' ')} (weight {w})")

    if resolved_modifier != "none":
        reasons.append(f"Modifier: {resolved_modifier.replace('_', ' ')}")

    if resolved_duration == "acute_under_6_hours":
        reasons.append("Acute onset — temporal risk multiplier 1.5×")
    elif resolved_duration == "chronic_over_30_days":
        reasons.append("Chronic presentation — temporal risk reduced 0.5×")

    if age < 1:
        reasons.append(f"Neonatal patient ({age} months) — elevated risk")
    elif age < 12:
        reasons.append(f"Pediatric patient (age {age})")
    elif age >= 75:
        reasons.append(f"Geriatric patient (age {age}) — atypical presentation risk")

    for ix in interactions:
        reasons.append(f"Critical interaction: {ix['note']}")

    if top_confidence < CONFIDENCE_THRESHOLD:
        reasons.append(
            f"Low model confidence ({top_confidence:.0%}) — routed to {recommended_dept}"
        )

    if vitals_missing:
        reasons.append("Vitals not provided — prediction may be less accurate")

    if unrecognised:
        reasons.append(f"Unrecognised input terms (ignored): {unrecognised}")

    # --- Build result ---
    result = {
        "recommended":     recommended_dept,
        "departments":     departments,
        "esi_level":       esi_level,
        "priority":        priority,
        "emergency":       is_emergency,
        "confidence":      round(top_confidence, 4),
        "score":           score,
        "interactions":    interactions,
        "reasons":         reasons,
        "unrecognised":    unrecognised,
        "vitals_missing":  vitals_missing,
        "model_version":   EXPERIMENT_VERSION,
    }

    logger.info(
        "symptoms=%r vitals=%r age=%d duration=%r modifier=%r | "
        "recommended=%r esi=%d priority=%r emergency=%s confidence=%.3f score=%d",
        symptoms, vitals, age, resolved_duration, resolved_modifier,
        recommended_dept, esi_level, priority, is_emergency, top_confidence, score,
    )

    return result


# ---------------------------------------------------------------------------
# CLI demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    test_cases = [
        {
            "label": "ESI-1 cardiac arrest",
            "input": dict(symptoms="cardiac arrest", vitals="sbp_below_90, hr_above_130",
                          age=58, duration="acute_under_6_hours", modifier="history_of_mi"),
        },
        {
            "label": "ESI-2 stroke",
            "input": dict(symptoms="drooping face, stroke symptoms",
                          vitals="sbp_above_200", age=72, duration="acute_under_6_hours"),
        },
        {
            "label": "ESI-3 urgent abdominal pain (pregnant)",
            "input": dict(symptoms="abdominal pain", vitals="",
                          age=28, duration="subacute_under_24_hours",
                          modifier="first trimester"),
        },
        {
            "label": "ESI-5 sore throat",
            "input": dict(symptoms="sore throat, mild fever", vitals="",
                          age=24, duration="standard"),
        },
        {
            "label": "Alias resolution test",
            "input": dict(symptoms="sob, throwing up", vitals="low oxygen",
                          age=45, duration="2"),
        },
    ]

    for case in test_cases:
        print(f"\n{'─'*60}")
        print(f"  {case['label']}")
        print(f"{'─'*60}")
        try:
            result = predict_case(**case["input"])
            print(json.dumps(result, indent=2))
        except (ValueError, RuntimeError) as exc:
            print(f"  [ERROR] {exc}")