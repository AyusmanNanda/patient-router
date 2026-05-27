"""
app.py (v5.0.0)

REST API gateway for the Patient Triage System.

Routes:
    GET  /api/health          — liveness check
    GET  /api/vocab           — returns all vocabulary lists for the frontend
    POST /api/triage          — main inference endpoint
    POST /api/feedback        — human-in-the-loop correction capture
"""

import os
import sys
import csv
import datetime
import logging
from pathlib import Path

from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------

CURRENT_DIR = Path(__file__).resolve().parent   # backend/app/
BASE_DIR    = CURRENT_DIR.parent                # backend/
ML_DIR      = BASE_DIR / "ml"
DATA_DIR    = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(ML_DIR))

from predict import predict_case
from constants import (
    KNOWN_SYMPTOMS,
    KNOWN_SHARED_VITALS,
    KNOWN_ADULT_VITALS,
    KNOWN_PEDIATRIC_VITALS,
    KNOWN_NEURO,
    KNOWN_MODIFIERS,
    KNOWN_DURATIONS,
    KNOWN_DEPARTMENTS,
    ALIASES,
    EXPERIMENT_VERSION,
)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=str(LOG_DIR / "triage.log"),
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = Flask(__name__)
CORS(app)

# ---------------------------------------------------------------------------
# Vocabulary data served to the frontend (built once at startup)
# ---------------------------------------------------------------------------

# Human-readable label -> canonical value, sorted by ESI weight (most urgent first)
_SYMPTOM_OPTIONS = [
    {"label": s.replace("_", " ").title(), "value": s}
    for s in KNOWN_SYMPTOMS
]
# Also expose common aliases so the autocomplete can show them
for _alias, _canon in ALIASES.items():
    if _canon in set(KNOWN_SYMPTOMS):
        _SYMPTOM_OPTIONS.append({"label": _alias.title(), "value": _alias})

_VITAL_OPTIONS = [
    {"label": v.replace("_", " ").upper(), "value": v}
    for v in (KNOWN_SHARED_VITALS + KNOWN_ADULT_VITALS + KNOWN_PEDIATRIC_VITALS + KNOWN_NEURO)
    if v != "normal_vitals"
]
for _alias, _canon in ALIASES.items():
    _vital_set = set(KNOWN_SHARED_VITALS + KNOWN_ADULT_VITALS + KNOWN_PEDIATRIC_VITALS + KNOWN_NEURO)
    if _canon in _vital_set:
        _VITAL_OPTIONS.append({"label": _alias.title(), "value": _alias})

_MODIFIER_OPTIONS = [
    {"value": "none",                    "label": "None"},
    {"value": "immunocompromised",       "label": "Immunocompromised (Chemo / HIV / Cancer)"},
    {"value": "pregnant_1st_trimester",  "label": "Pregnant — 1st Trimester"},
    {"value": "pregnant_2nd_trimester",  "label": "Pregnant — 2nd Trimester"},
    {"value": "pregnant_3rd_trimester",  "label": "Pregnant — 3rd Trimester"},
    {"value": "on_blood_thinners",       "label": "On Blood Thinners (Warfarin / Eliquis)"},
    {"value": "history_of_mi",           "label": "History of Heart Attack (MI)"},
    {"value": "esrd_dialysis",           "label": "Kidney Failure / On Dialysis"},
    {"value": "copd",                    "label": "COPD / Emphysema"},
    {"value": "chf",                     "label": "Chronic Heart Failure (CHF)"},
    {"value": "pediatric_infant",        "label": "Neonate / Infant (< 1 year)"},
    {"value": "pediatric_child",         "label": "Child (1–11 years)"},
    {"value": "geriatric",               "label": "Elderly Patient (75+)"},
]

_DURATION_OPTIONS = [
    {"value": "acute_under_6_hours",     "label": "Acute (< 6 hours)"},
    {"value": "subacute_under_24_hours", "label": "Subacute (6–24 hours)"},
    {"value": "standard",                "label": "Standard (1–30 days)"},
    {"value": "chronic_over_30_days",    "label": "Chronic (> 30 days)"},
]

_DEPARTMENT_OPTIONS = [
    {"value": d, "label": d.replace("_", " ").title()}
    for d in KNOWN_DEPARTMENTS
]

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/api/health")
def health():
    """Liveness check."""
    return jsonify({"status": "ok", "version": EXPERIMENT_VERSION}), 200


@app.route("/api/vocab")
def vocab():
    """
    Returns all vocabulary lists needed by the frontend.
    The frontend fetches this once on load — no hardcoded lists in HTML.
    """
    return jsonify({
        "symptoms":    _SYMPTOM_OPTIONS,
        "vitals":      _VITAL_OPTIONS,
        "modifiers":   _MODIFIER_OPTIONS,
        "durations":   _DURATION_OPTIONS,
        "departments": _DEPARTMENT_OPTIONS,
    }), 200


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/triage", methods=["POST"])
def triage():
    """
    Main inference endpoint.

    Accepts JSON:
        symptoms  — str, comma-separated (required)
        vitals    — str, comma-separated (optional)
        age       — int (required)
        gender    — str (optional, stored for feedback only, not used by model)
        duration  — str, one of KNOWN_DURATIONS (optional, default "standard")
        modifier  — str, one of KNOWN_MODIFIERS (optional, default "none")
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "JSON request body required."}), 400

    symptoms = str(data.get("symptoms", "")).strip()
    vitals   = str(data.get("vitals",   "")).strip()
    age      = data.get("age")
    gender   = str(data.get("gender",   "unknown")).strip()   # stored only
    duration = str(data.get("duration", "standard")).strip()
    modifier = str(data.get("modifier", "none")).strip()

    if not symptoms:
        return jsonify({"error": "symptoms is required."}), 400
    if age is None:
        return jsonify({"error": "age is required."}), 400

    try:
        age = int(age)
    except (ValueError, TypeError):
        return jsonify({"error": f"age must be an integer, got {age!r}."}), 400

    try:
        # gender is intentionally NOT passed — predict_case doesn't accept it
        result = predict_case(
            symptoms=symptoms,
            vitals=vitals,
            age=age,
            duration=duration,
            modifier=modifier,
        )
        # Attach gender to result so the frontend can include it in feedback payload
        result["gender"] = gender

        logger.info(
            "TRIAGE symptoms=%r age=%d gender=%s duration=%s modifier=%s "
            "-> recommended=%s esi=%d priority=%s",
            symptoms, age, gender, duration, modifier,
            result["recommended"], result["esi_level"], result["priority"],
        )
        return jsonify({"status": "success", "data": result}), 200

    except ValueError as exc:
        logger.warning("TRIAGE validation error: %s", exc)
        return jsonify({"error": str(exc)}), 400

    except RuntimeError as exc:
        logger.error("TRIAGE runtime error: %s", exc)
        return jsonify({"error": str(exc)}), 500

    except Exception as exc:
        logger.exception("TRIAGE unexpected error")
        return jsonify({"error": "Internal server error."}), 500


@app.route("/api/feedback", methods=["POST"])
def feedback():
    """
    Human-in-the-loop correction endpoint.
    Saves doctor corrections to a staging CSV (never touches data.csv directly).

    Accepts JSON:
        symptoms, vitals, age, gender, duration, modifier  — original inputs
        recommended       — what the model predicted
        correct_department — the clinician's correction (required)
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "JSON request body required."}), 400

    correct_dept = str(data.get("correct_department", "")).strip()
    if not correct_dept:
        return jsonify({"error": "correct_department is required."}), 400

    # Validate correct_department is a known department
    if correct_dept not in set(KNOWN_DEPARTMENTS):
        return jsonify({
            "error": f"Unknown department '{correct_dept}'. "
                     f"Must be one of: {KNOWN_DEPARTMENTS}"
        }), 400

    corrections_path = DATA_DIR / "human_corrections.csv"
    file_exists = corrections_path.exists()

    FIELDNAMES = [
        "timestamp", "age", "gender", "modifier", "duration",
        "symptoms", "vitals", "ml_recommended", "correct_department",
    ]

    try:
        with open(corrections_path, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction="ignore")
            if not file_exists:
                writer.writeheader()
            writer.writerow({
                "timestamp":          datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "age":                data.get("age", ""),
                "gender":             data.get("gender", ""),
                "modifier":           data.get("modifier", "none"),
                "duration":           data.get("duration", "standard"),
                "symptoms":           data.get("symptoms", ""),
                "vitals":             data.get("vitals", ""),
                "ml_recommended":     data.get("recommended", ""),
                "correct_department": correct_dept,
            })

        logger.info(
            "FEEDBACK ml_recommended=%s correct_department=%s age=%s",
            data.get("recommended", ""), correct_dept, data.get("age", ""),
        )
        return jsonify({"message": "Correction saved to human review staging."}), 200

    except OSError as exc:
        logger.error("FEEDBACK write error: %s", exc)
        return jsonify({"error": f"Failed to save correction: {exc}"}), 500


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    port  = int(os.getenv("PORT", 5000))
    print(f"\n{'='*55}")
    print(f"  Patient Triage API  |  v{EXPERIMENT_VERSION}")
    print(f"  http://0.0.0.0:{port}")
    print(f"{'='*55}\n")
    app.run(host="0.0.0.0", port=port, debug=debug)