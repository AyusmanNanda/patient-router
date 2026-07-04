# Architecture

This document covers the internals referenced from the main [README](../README.md): the ML training pipeline, priority scoring, emergency detection, input normalization, and the feedback loop. If you're looking for setup instructions or the API contract, see [README.md](../README.md) and [api.md](api.md) instead.

---

## ML Pipeline

How the model itself gets built, from synthetic data to a trained artifact.

```mermaid
flowchart LR
    A[generate_data.py\nsynthetic rows] --> B[data.csv]
    B --> C[train.py\nRandom Forest + CountVectorizer + OneHotEncoder]
    C --> D[model.pkl]
    D --> E[predict.py\npredict_case]
    C --> F[model_evaluation.py\naccuracy, CV, confusion matrix]
    G[User Feedback] --> B
```

### Dataset

Generated synthetically using `generate_data.py`, with configurable size (default `SAMPLE_SIZE` in `constants.py`).

| Property | Detail |
|---|---|
| Departments | 6 (cardiology, pulmonology, neurology, orthopedics, gastrology, general) |
| Distribution | Evenly split across departments, then shuffled |
| Symptoms | 20, grouped by department with cross-department overlap noise |
| Vitals | bp_high, bp_low, hr_high, hr_low, temp_high, temp_low, normal |
| History | pregnant, previous_heart_attack, on_blood_thinners, hiv, diabetes, hypertension |

**Noise applied during generation** (this is what keeps the synthetic data from being trivially separable):

| Noise Type | Probability |
|---|---|
| Cross-department symptom added | 40% |
| Symptom dropout (drop one if >1) | 20% |
| Vital measurement flipped to opposite | 15% |
| Extra unrelated vital added | 30% |
| Vitals reported as "normal" only | 10% |
| Unrelated history condition added | 15% (if history non-empty) |
| History condition dropped | 10% (if >1 present) |
| History cleared entirely | 20% |

---

## Priority Scoring Logic

Runs after a department is chosen, in `priority.py`.

```mermaid
flowchart TD
    A[Start Scoring] --> B[Add symptom weights\nchest pain +2, breathlessness +2, confusion +2]
    B --> C[Add vital weights\nbp_low +3, bp_high +2, hr_high +2, hr_low +1]
    C --> D{Age > 60?}
    D -- Yes --> E[score + 1]
    D -- No --> F[Continue]
    E --> G{Severe symptom\n+ duration <= 2?}
    F --> G
    G -- Yes --> H[score + 1]
    G -- No --> I[Continue]
    H --> J{Score >= 4\nAND severe_score >= 2?}
    I --> J
    J -- Yes --> K[Priority: HIGH]
    J -- No --> L{Score >= 2?}
    L -- Yes --> M[Priority: MEDIUM]
    L -- No --> N[Priority: LOW]
```

> **Note:** `priority.py` requires both an overall score **and** a minimum "severe" symptom/vital contribution to reach HIGH — this is stricter than the simplified scoring used to label synthetic training data in `generate_data.py`. This mismatch is a known source of label/inference drift (see [Limitations](../README.md#limitations)).

---

## Emergency & History Risk Detection

Runs in parallel with priority scoring, in `emergency.py` and `history.py`. Either one can force priority to HIGH regardless of the score above.

```mermaid
flowchart TD
    A[Check Risk] --> B{Any emergency symptom?\nchest pain, breathlessness, confusion}
    B -- Yes --> D[is_emergency = True]
    B -- No --> C{Any emergency vital?\nbp_low, hr_high}
    C -- Yes --> D
    C -- No --> E[is_emergency = False]
    A --> F{History score >= 10\nor any single condition >= 9?\ne.g. previous_heart_attack, hiv, pregnant}
    F -- Yes --> G[is_high_risk = True]
    D --> H[Force priority = HIGH]
    G --> H
    E --> I[Keep computed priority]
```

---

## Input Normalization Flow

Before symptoms/vitals reach the vectorizer, free-text input is normalized against the known vocabulary.

```mermaid
flowchart TD
    A[Raw user input] --> B[Lowercase + strip]
    B --> C{In alias map?}
    C -- Yes --> D[Map to correct term\ne.g. shortness of breath → breathlessness]
    C -- No --> E{Exact match in\nknown terms?}
    E -- Yes --> F[Use as-is]
    E -- No --> G{Space/underscore swap\nmatches known term?}
    G -- Yes --> H[Use swapped term\ne.g. bp high → bp_high]
    G -- No --> I{Fuzzy match\ncutoff 0.75?}
    I -- Yes --> J[Use closest match\ne.g. breathlessnes → breathlessness]
    I -- No --> K[Pass through as-is]
```

---

## Feedback Loop

How a correction made in the dashboard makes it back into the model.

```mermaid
flowchart LR
    A[Prediction Made] --> B[User confirms or corrects department]
    B --> C[Appended directly to data.csv]
    C --> D[Dataset Manager / Training page]
    D --> E[Retrain model on demand]
    E --> F[New model.pkl saved + evaluation re-run]
```

Feedback is appended straight into the same `data.csv` used for training (not a separate file) — a row with the corrected department becomes part of the next training run as soon as `/train` is called. There's currently no validation on these rows beyond what the API layer enforces (see [Limitations](../README.md#limitations)).