# Data Schema

Canonical vocabulary and weight tables used by the synthetic data generator and prediction rules. The source of truth is `backend/ml/constants.py`. New symptoms, vitals, or history conditions should be added there, with this document updated to match.

For how these values are used during training and prediction, see [architecture.md](architecture.md).

---

## Symptoms

20 known symptoms, each with a priority weight. Symptoms weighted `2` are also emergency symptoms. Along with contributing to the priority score, they can force priority to `HIGH` in the `patient_router` prediction path.

| Symptom          | Weight | Emergency? |
| ---------------- | ------ | ---------- |
| chest pain       | 2      | Yes        |
| breathlessness   | 2      | Yes        |
| confusion        | 2      | Yes        |
| fatigue          | 1      | No         |
| sweating         | 1      | No         |
| cough            | 1      | No         |
| fever            | 1      | No         |
| headache         | 1      | No         |
| dizziness        | 1      | No         |
| blurred vision   | 1      | No         |
| joint pain       | 1      | No         |
| swelling         | 1      | No         |
| stiffness        | 1      | No         |
| limited movement | 1      | No         |
| abdominal pain   | 1      | No         |
| nausea           | 1      | No         |
| vomiting         | 1      | No         |
| diarrhea         | 1      | No         |
| body pain        | 1      | No         |
| weakness         | 1      | No         |

---

## Vitals

7 known vitals. `bp_low` and `hr_high` are the two emergency vitals.

| Vital     | Weight | Emergency? |
| --------- | ------ | ---------- |
| bp_low    | 3      | Yes        |
| bp_high   | 2      | No         |
| hr_high   | 2      | Yes        |
| hr_low    | 1      | No         |
| temp_high | 0      | No         |
| temp_low  | 0      | No         |
| normal    | 0      | No         |

`temp_high` and `temp_low` have no priority weight. They are still part of the known vocabulary and department profiles, but do not contribute to a `HIGH`, `MEDIUM`, or `LOW` priority decision on their own.

### Opposites used for generation noise

`generate_data.py` uses this map to occasionally replace a vital with its opposite:

```text id="p2u4af"
bp_high ↔ bp_low
hr_high ↔ hr_low
temp_high ↔ temp_low
```

---

## Medical History

6 known conditions, each with a risk weight.

A condition weighted `9` or more, or a cumulative history score of at least `10`, marks the patient as high risk. This can force priority to `HIGH` regardless of the symptom and vital score.

| Condition             | Weight | High-risk alone? |
| --------------------- | ------ | ---------------- |
| previous_heart_attack | 10     | Yes              |
| pregnant              | 9      | Yes              |
| hiv                   | 9      | Yes              |
| on_blood_thinners     | 5      | No               |
| diabetes              | 4      | No               |
| hypertension          | 4      | No               |

Any combination with a total score of at least `10` also triggers high risk. For example, `on_blood_thinners` and `hypertension` have a total score of `9`, which does not reach the threshold. Adding `diabetes` increases the total to `13` and triggers high risk.

---

## Departments

6 departments. Each has a symptom profile, vital profile, age range, and duration range used during synthetic data generation.

These ranges shape the generated rows for each department. They do not restrict prediction input.

| Department  | Symptoms                                          | Vitals             | Age range | Duration range (days) |
| ----------- | ------------------------------------------------- | ------------------ | --------- | --------------------- |
| cardiology  | chest pain, breathlessness, fatigue, sweating     | bp_high, hr_high   | 45–80     | 1–5                   |
| pulmonology | cough, breathlessness, fever, fatigue             | temp_high, hr_high | 20–70     | 1–7                   |
| neurology   | headache, dizziness, confusion, blurred vision    | bp_low, bp_high    | 30–80     | 1–10                  |
| orthopedics | joint pain, swelling, stiffness, limited movement | normal             | 40–85     | 7–30                  |
| gastrology  | abdominal pain, nausea, vomiting, diarrhea        | normal             | 20–65     | 1–5                   |
| general     | fever, body pain, weakness, fatigue               | temp_high          | 15–60     | 1–5                   |

`breathlessness` appears in both the cardiology and pulmonology symptom lists. This overlap is intentional and makes the generated departments less easily separable.

The hand-written edge cases used during model evaluation also include overlapping symptoms. See [architecture.md](architecture.md#model-evaluation).

### History bias by department

`generate_data.py` uses this map to make some history conditions more likely for specific departments.

Each condition has a 35% chance of being added when it is biased towards the department and an 8% chance otherwise.

| Department  | Biased history conditions                              |
| ----------- | ------------------------------------------------------ |
| cardiology  | previous_heart_attack, hypertension, on_blood_thinners |
| neurology   | hypertension, diabetes                                 |
| general     | diabetes                                               |
| pulmonology | hiv                                                    |
| gastrology  | diabetes                                               |
| orthopedics | *(none)*                                               |

---

## Aliases

Free-text normalization map used by `normalize_term()` in `patient_router.py`. See [architecture.md](architecture.md#input-normalization-flow).

| Input variant                                            | Normalizes to  |
| -------------------------------------------------------- | -------------- |
| bp high / high bp                                        | bp_high        |
| bp low / low bp                                          | bp_low         |
| hr high / high hr                                        | hr_high        |
| hr low                                                   | hr_low         |
| temp high / high temp                                    | temp_high      |
| temp low                                                 | temp_low       |
| shortness of breath / short of breath / sob / breathless | breathlessness |
| chest tightness                                          | chest pain     |
| stomach pain / stomach ache / belly pain                 | abdominal pain |
| loose motion / loose motions                             | diarrhea       |
| blurred / blur                                           | blurred vision |
| joint ache                                               | joint pain     |
| tired / tiredness                                        | fatigue        |

Terms not found in this table go through exact matching, space/underscore conversion, and fuzzy matching with a cutoff of `0.75`. If no match is found, the original term is passed through unchanged.

This normalization only applies to the `patient_router` method. The `llm` method sends the input directly to Gemini.

The dashboard's `TagInput` component only accepts values from the frontend option lists, which currently match the backend vocabulary. This makes normalization mainly useful for direct `/predict` API requests.

---

## Confidence Level Mapping

Used by the `llm` predictor to convert Gemini's self-reported confidence level into a fixed numeric value. See [architecture.md](architecture.md#llm---gemini-25-flash).

| Level  | Numeric confidence |
| ------ | ------------------ |
| low    | 0.4                |
| medium | 0.65               |
| high   | 0.85               |

This is a fixed three-level scale, not a continuous model probability.

The local Gradient Boosting model uses `predict_proba` and can return confidence values anywhere between 0 and 1. Gemini confidence is always mapped to `0.4`, `0.65`, or `0.85`.

`CONFIDENCE_THRESHOLD` is currently `0.60`. The local model uses this threshold for its `general` fallback, while the hybrid method uses it to decide whether to keep the local result or call Gemini.
