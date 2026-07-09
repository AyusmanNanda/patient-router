# API Reference

Request/response reference for every route. For a short project overview, see the [README](../README.md). For how the prediction pipeline works, see [architecture.md](architecture.md).

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

Runs a prediction using one of three methods. See [architecture.md](architecture.md#prediction-methods) for how each method works.

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

**Response — `patient_router`, or `hybrid` using the local model**

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

**Response — `method: "llm"`, or `hybrid` using Gemini**

The response has the same shape, except `departments` contains a single entry because the Gemini method does not return ranked alternatives. `model_version` contains the model name instead of the Patient Router version.

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
| `recommended` | Recommended department. The local Patient Router method falls back to `general` below the configured confidence threshold |
| `departments` | Top 3 candidates for `patient_router`; 1 entry for `llm` |
| `priority` | `high` / `medium` / `low` |
| `emergency` | Emergency status returned by the selected prediction method |
| `reasons` | Reasons that contributed to the priority or emergency decision |
| `history_score` | Cumulative risk score from the reported medical history |
| `model_version` | Patient Router version for the local model or model name for the Gemini method |
| `warning` | Set if `vitals` was omitted from the request |

For more details about the differences between the prediction methods, see [architecture.md](architecture.md#prediction-methods).

**Errors**

| Status | Condition |
|---|---|
| `400` | Missing or invalid `symptoms`, `age`, or `duration`; empty request body |
| `500` | Unexpected prediction failure |

Error body:

```json
{
  "error": "..."
}
```

---

## Feedback

### `POST /feedback`

Submits a correction for a previous prediction and appends it to `data.csv`.

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
| `correct_department` | Yes | Correct department selected by the user |
| `symptoms` | No | Passed through from the original prediction |
| `vitals` | No | Defaults to `"normal"` |
| `age` | No | Passed through from the original prediction |
| `duration` | No | Passed through from the original prediction |
| `gender` | No | Defaults to `"male"` |
| `history` | No | Saved with the feedback row |
| `priority` | No | Defaults to `"low"` |

**Response**

```json
{
  "message": "Feedback successfully saved to training data."
}
```

**Errors**

| Status | Condition |
|---|---|
| `400` | `correct_department` missing or empty request body |
| `500` | Failed to save feedback |

---

## Dataset

### `GET /data`

Returns basic statistics about the current dataset.

**Response**

```json
{
  "total_rows": 50000,
  "total_columns": 8,
  "departments": {
    "cardiology": 8334,
    "pulmonology": 8334,
    "neurology": 8333,
    "orthopedics": 8333,
    "gastrology": 8333,
    "general": 8333
  },
  "priorities": {
    "high": 12500,
    "medium": 21000,
    "low": 16500
  }
}
```

The exact department and priority counts can change when the synthetic dataset is regenerated.

### `POST /data/generate`

Regenerates the synthetic dataset and overwrites `data.csv`.

**Request**

```json
{
  "rows": 50000
}
```

`rows` is optional and defaults to `50000`.

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

Retrains the Gradient Boosting model on the current `data.csv` and runs the evaluation pipeline.

The trained model is saved to `backend/ml/models/model.pkl`. Evaluation reports are also regenerated as part of the training process.

For more details about training and evaluation, see [architecture.md](architecture.md#model-evaluation).

**Response**

```json
{
  "train_accuracy": 99.26,
  "test_accuracy": 98.84,
  "dataset_size": 50000,
  "training_time_insec": 12.44
}
```

### `GET /evaluation`

Returns the contents of `evaluation_metrics.json` from the latest evaluation run.

**Response**

```json
{
  "synthetic_accuracy": 98.84,
  "cv_accuracy": 99.04,
  "cv_std": 0.07,
  "edge_case_accuracy": 91.18,
  "generalization_gap": 7.7,
  "total_edge_cases": 34,
  "passed_edge_cases": 31,
  "failed_edge_cases": 3
}
```

If the evaluation report is not available:

```json
{
  "error": "Evaluation report not found"
}
```

### `GET /evaluation/confusion-matrix`

Returns `confusion_matrix.png` as an image response.

### `GET /evaluation/report-image`

Returns `evaluation_report.png` as an image response.

### `GET /evaluation/comparison`

Returns the latest model comparison results from the generated JSON report.

The comparison currently includes:

- Decision Tree
- Random Forest
- Gradient Boosting
- Logistic Regression
- K-Nearest Neighbors
- SVM with RBF kernel
- XGBoost

Each model is compared using test accuracy, Macro F1 score, 5-fold cross-validation, cross-validation standard deviation, edge-case accuracy, generalisation gap, and training time.

**Response**

```json
[
  {
    "Model": "Gradient Boosting",
    "Test Accuracy (%)": 98.84,
    "Macro F1 (%)": 98.84,
    "5-Fold CV (%)": 99.04,
    "CV Std (±%)": 0.07,
    "Edge-Case Acc (%)": 91.18,
    "Generalisation Gap": 7.7,
    "Train Time (s)": 12.14
  }
]
```

The endpoint returns results for all models included in the comparison.

### `GET /evaluation/comparison-image`

Returns `model_comparison.png` as an image response.

---

## Logs

### `GET /logs`

Returns the prediction history, newest first, along with emergency and fallback counts.

All logged predictions are returned. There is currently no server-side limit or pagination.

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

`model` contains the Patient Router version or Gemini model name used for the prediction.

### `POST /logs/clear`

Clears the prediction log.

**Response**

```json
{
  "message": "Logs cleared"
}
```