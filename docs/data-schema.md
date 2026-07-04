# Data Schema

Canonical vocabulary and weight tables used by both `generate_data.py` (synthetic labeling) and the live prediction/priority logic (`patient_router.py`, `priority.py`, `emergency.py`, `history.py`). Source of truth: `backend/ml/constants.py`. New symptoms, vitals, or history conditions should be added there, with this document updated to match. For how these values flow through prediction, see [architecture.md](architecture.md).

---

## Symptoms

20 known symptoms, each with a priority weight. Symptoms weighted `2` are also **emergency symptoms**: beyond contributing to the priority score, they can force priority straight to `HIGH` regardless of the total score.

| Symptom | Weight | Emergency? |
|---|---|---|
| chest pain | 2 | Yes |
| breathlessness | 2 | Yes |
| confusion | 2 | Yes |
| fatigue | 1 | No |
| sweating | 1 | No |
| cough | 1 | No |
| fever | 1 | No |
| headache | 1 | No |
| dizziness | 1 | No |
| blurred vision | 1 | No |
| joint pain | 1 | No |
| swelling | 1 | No |
| stiffness | 1 | No |
| limited movement | 1 | No |
| abdominal pain | 1 | No |
| nausea | 1 | No |
| vomiting | 1 | No |
| diarrhea | 1 | No |
| body pain | 1 | No |
| weakness | 1 | No |

## Vitals

7 known vitals. `bp_low` and `hr_high` are the two emergency vitals.

| Vital | Weight | Emergency? |
|---|---|---|
| bp_low | 3 | Yes |
| bp_high | 2 | No |
| hr_high | 2 | Yes |
| hr_low | 1 | No |
| temp_high | 0 | No |
| temp_low | 0 | No |
| normal | 0 | No |

`temp_high`/`temp_low` carry no priority weight. They exist in the vocabulary and in department vital profiles (e.g. pulmonology, general) but never contribute to a `HIGH`/`MEDIUM`/`LOW` decision on their own.

### Opposites (used for generation noise)

`generate_data.py` uses this map to occasionally flip a vital to its opposite as label noise:

```
bp_high ↔ bp_low
hr_high ↔ hr_low
temp_high ↔ temp_low
```

## Medical History

6 known conditions, each with a risk weight. A condition weighted `≥ 9`, or a cumulative history score `≥ 10`, marks the patient as high risk (`analyze_history()` in `history.py`), which — like emergency detection — forces priority to `HIGH` regardless of the symptom/vital score.

| Condition | Weight | High-risk alone? |
|---|---|---|
| previous_heart_attack | 10 | Yes |
| pregnant | 9 | Yes |
| hiv | 9 | Yes |
| on_blood_thinners | 5 | No (alone) |
| diabetes | 4 | No (alone) |
| hypertension | 4 | No (alone) |

Any combination summing to 10+ also triggers high-risk. `on_blood_thinners` (5) + `hypertension` (4) does not reach the threshold on its own; `on_blood_thinners` + `diabetes` + `hypertension` (5+4+4=13) does.

---

## Departments

6 departments. Each has an associated symptom/vital profile and age/duration range used only for synthetic data generation (`generate_data.py`). These ranges do not constrain real predictions — they shape what realistic-looking synthetic rows look like per department.

| Department | Symptoms | Vitals | Age range | Duration range (days) |
|---|---|---|---|---|
| cardiology | chest pain, breathlessness, fatigue, sweating | bp_high, hr_high | 45–80 | 1–5 |
| pulmonology | cough, breathlessness, fever, fatigue | temp_high, hr_high | 20–70 | 1–7 |
| neurology | headache, dizziness, confusion, blurred vision | bp_low, bp_high | 30–80 | 1–10 |
| orthopedics | joint pain, swelling, stiffness, limited movement | normal | 40–85 | 7–30 |
| gastrology | abdominal pain, nausea, vomiting, diarrhea | normal | 20–65 | 1–5 |
| general | fever, body pain, weakness, fatigue | temp_high | 15–60 | 1–5 |

`breathlessness` appears in both cardiology's and pulmonology's symptom lists. This overlap is intentional: it keeps the synthetic data from being trivially separable, and it is the case the hand-written edge-case set in `model_evaluation.py` targets (see [architecture.md](architecture.md#model-evaluation)).

### History bias by department

`generate_data.py` uses this map to bias which history conditions are more likely to appear for a given department during generation (35% chance if biased, 8% otherwise, per condition):

| Department | Biased history conditions |
|---|---|
| cardiology | previous_heart_attack, hypertension, on_blood_thinners |
| neurology | hypertension, diabetes |
| general | diabetes |
| pulmonology | hiv |
| gastrology | diabetes |
| orthopedics | *(none)* |

---

## Aliases

Free-text normalization map used in `patient_router.py`'s `normalize_term()` (see [architecture.md](architecture.md#input-normalization-flow)).

**Scope:** applies only to the `patient_router`/RF prediction path, not `llm`. Currently relevant only to direct API callers — the shipped dashboard's `TagInput` component restricts input to exact canonical vocabulary via dropdown, so dashboard traffic never needs this table.

| Input variant | Normalizes to |
|---|---|
| bp high / high bp | bp_high |
| bp low / low bp | bp_low |
| hr high / high hr | hr_high |
| hr low | hr_low |
| temp high / high temp | temp_high |
| temp low | temp_low |
| shortness of breath / short of breath / sob / breathless | breathlessness |
| chest tightness | chest pain |
| stomach pain / stomach ache / belly pain | abdominal pain |
| loose motion / loose motions | diarrhea |
| blurred / blur | blurred vision |
| joint ache | joint pain |
| tired / tiredness | fatigue |

Terms not in this table fall through, in order: exact match → space/underscore swap → fuzzy match (cutoff `0.75`) → passed through unchanged. See the normalization flow diagram in [architecture.md](architecture.md#input-normalization-flow).

---

## Confidence Level Mapping

Used by the `llm` predictor to convert Gemini's self-reported confidence level into a fixed number (see [architecture.md](architecture.md#llm--gemini-25-flash)).

| Level | Numeric confidence |
|---|---|
| low | 0.4 |
| medium | 0.65 |
| high | 0.85 |

This is a fixed 3-point scale, not a continuous probability. The RF path's `predict_proba` output can be any value between 0 and 1. Both are compared against the same `CONFIDENCE_THRESHOLD` (`0.60`) for fallback decisions, but only the RF path can land near that threshold — the LLM path is always exactly `0.4`, `0.65`, or `0.85`.