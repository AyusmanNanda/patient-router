# API Reference

Request/response reference for every route. For the one-line route table, see the [README](../README.md#api). For how a prediction is computed, see [architecture.md](architecture.md).

Base URL (local): `http://localhost:5000`

---

## Core

### `GET /`

Service info.

**Response**
```json
{
  "service": "Patient Router API",
  "status": "ok"
}
```

### `GET /health`

Health check.

**Response**
```json
{
  "status": "ok"
}
```

---

## Prediction

### `POST /predict`

Runs a triage prediction using one of three methods. See [architecture.md](architecture.md#prediction-methods) for method details.

**Request**
```json
{
  "symptoms": "chest pain, breathlessness",
  "vitals": "bp_high, hr_high",
  "age": 65,
  "duration": 2,
  "gender": "male",
  "history": "previous_heart_attack",
  "method": "patient_router"
}
```

| Field | Required | Notes |
|---|---|---|
| `symptoms` | Yes | Comma-separated free text |
| `age` | Yes | 1–120 |
| `duration` | Yes | Days, > 0 |
| `vitals` | No | Defaults to `"normal"` |
| `gender` | No | Defaults to `"male"` |
| `history` | No | Comma-separated free text; defaults to none |
| `method` | No | `"patient_router"` (default), `"llm"`, or `"hybrid"` |

**Response — `patient_router`, or `hybrid` falling back to the RF model**
```json
{
  "recommended": "cardiology",
  "departments": [
    { "department": "cardiology", "confidence": 0.97 },
    { "department": "pulmonology", "confidence": 0.02 },
    { "department": "general", "confidence": 0.01 }
  ],
  "priority": "high",
  "emergency": true,
  "confidence": 0.97,
  "reasons": [
    "chest pain",
    "breathlessness",
    "bp_high",
    "hr_high",
    "History: previous_heart_attack",
    "Age risk (65 years)",
    "Acute onset (2 days)"
  ],
  "history": ["previous_heart_attack"],
  "history_score": 10,
  "model_version": "1.1.0",
  "warning": null
}
```

**Response — `method: "llm"`, or `hybrid` falling through to Gemini**

Same shape, except `departments` contains a single entry (the LLM does not return ranked alternatives), and `model_version` is the model name rather than the app version.

```json
{
  "recommended": "cardiology",
  "departments": [
    { "department": "cardiology", "confidence": 0.85 }
  ],
  "priority": "high",
  "emergency": true,
  "confidence": 0.85,
  "reasons": ["..."],
  "history": ["previous_heart_attack"],
  "history_score": 10,
  "model_version": "gemini-2.5-flash",
  "warning": null
}
```

**Field reference**

| Field | Description |
|---|---|
| `recommended` | Top department. For `patient_router`, falls back to `general` below a 0.60 confidence threshold ([architecture.md](architecture.md#ml-pipeline)) |
| `departments` | Top 3 candidates for `patient_router`; 1 entry for `llm` |
| `priority` | `high` / `medium` / `low` |
| `emergency` | `patient_router`: rule-based detection. `llm`: Gemini's self-reported value. Not computed the same way between methods — see [architecture.md](architecture.md#prediction-methods) |
| `reasons` | Everything that contributed to the priority/emergency decision |
| `history_score` | Cumulative risk score from reported medical history; same logic for both methods |
| `model_version` | App version (e.g. `"1.1.0"`) for `patient_router`; model name (e.g. `"gemini-2.5-flash"`) for `llm` |
| `warning` | Set if `vitals` was omitted from the request |

**Errors**

| Status | Condition |
|---|---|
| `400` | Missing/invalid `symptoms`, `age`, or `duration`; empty request body |
| `500` | Unexpected failure (e.g. Gemini API error on `method: "llm"`) |

Error body: `{"error": "..."}`

---

## Feedback

### `POST /feedback`

Submits a correction for a previous prediction. Appended to `data.csv`.

**Request**
```json
{
  "symptoms": "chest pain, breathlessness",
  "vitals": "bp_high, hr_high",
  "age": 65,
  "duration": 2,
  "gender": "male",
  "history": "previous_heart_attack",
  "correct_department": "cardiology",
  "priority": "high"
}
```

| Field | Required | Notes |
|---|---|---|
| `correct_department` | Yes | |
| `symptoms`, `vitals`, `age`, `duration`, `gender` | No | Passed through as-is; `vitals` defaults to `"normal"`, `gender` to `"male"` |
| `priority` | No | Defaults to `"low"` |
| `history` | No | Accepted but not currently saved (see Known Issues) |

**Response**
```json
{
  "message": "Feedback successfully saved to training data."
}
```

**Errors**

| Status | Condition |
|---|---|
| `400` | `correct_department` missing (`"Correct department is required"`); empty body (`"Request body is required"`) |
| `500` | Write failure |

**Known issues**

Feedback rows are written with misaligned columns. `data.csv`'s header is:

```
age, duration, symptoms, vitals, history, gender, priority, department
```

The feedback writer outputs 7 values in this order, omitting `history`:

```
age, duration, symptoms, vitals, gender, priority, correct_dept
```

Effect: `gender` is stored under the `history` column, `priority` under `gender`, `correct_department` under `priority`, and `department` is left empty. This corrupts feedback-sourced rows before they reach training.

**Fix location:** `feedbackService.py`. Should be resolved before the feedback loop is used for retraining.

---

## Dataset

### `GET /data`

Dataset stats.

**Response**
```json
{
  "total_rows": 50000,
  "total_columns": 8,
  "departments": {
    "cardiology": 8333,
    "pulmonology": 8333,
    "neurology": 8333,
    "orthopedics": 8334,
    "gastrology": 8333,
    "general": 8334
  },
  "priorities": {
    "high": 12500,
    "medium": 21000,
    "low": 16500
  }
}
```

### `POST /data/generate`

Regenerates the synthetic dataset and overwrites `data.csv`.

**Request**
```json
{ "rows": 50000 }
```

`rows` — optional, defaults to `50000`.

**Response**
```json
{
  "status": "success",
  "rows_generated": 50000
}
```

---

## Training & Evaluation

### `POST /train`

Retrains the model on the current `data.csv` and triggers a full evaluation run. `evaluation_metrics.json`, `evaluation_report.txt`, and `evaluation_report.png` are regenerated as part of this call, not just `model.pkl`. See [architecture.md](architecture.md#model-evaluation).

**Response**
```json
{
  "train_accuracy": 99.87,
  "test_accuracy": 94.32,
  "dataset_size": 50000,
  "training_time_insec": 12.44
}
```

The response does not include `model_version` or `model_path`. The model artifact is always written to `backend/ml/models/model.pkl`.

### `GET /evaluation`

Contents of `evaluation_metrics.json` from the last `/train` run, including the synthetic-vs-real-world generalization gap (see [architecture.md](architecture.md#model-evaluation)).

**Response**
```json
{
  "synthetic_accuracy": 94.32,
  "cv_accuracy": 93.8,
  "cv_std": 0.6,
  "edge_case_accuracy": 78.12,
  "generalization_gap": 16.2,
  "total_edge_cases": 32,
  "passed_edge_cases": 25,
  "failed_edge_cases": 7
}
```

If `/train` has not been run: `{"error": "Evaluation report not found"}`

### `GET /evaluation/confusion-matrix`

Returns `confusion_matrix.png` as an image response.

### `GET /evaluation/report-image`

Returns `evaluation_report.png` (6-panel chart, see [architecture.md](architecture.md#model-evaluation)) as an image response.

---

## Logs

### `GET /logs`

Full prediction history, newest first, with emergency/fallback counts. All logged predictions are returned; there is no server-side limit or pagination.

**Response**
```json
{
  "total_predictions": 1204,
  "total_emergencies": 87,
  "total_fallbacks": 42,
  "logs": [
    {
      "timestamp": "2026-07-01T14:32:10Z",
      "symptoms": ["chest pain", "breathlessness"],
      "vitals": ["bp_high", "hr_high"],
      "history": ["previous_heart_attack"],
      "history_score": 10,
      "age": 65,
      "duration": 2,
      "gender": "male",
      "recommended": "cardiology",
      "confidence": 0.97,
      "priority": "high",
      "emergency": true,
      "fallback_used": false,
      "model": "patient-router-1.1.0"
    }
  ]
}
```

`model` — `"patient-router-{MODEL_VERSION}"` or `"gemini-2.5-flash"`, matching the `method` used at prediction time.

### `POST /logs/clear`

Clears the prediction log.

**Response**
```json
{
  "message": "Logs cleared"
}
```