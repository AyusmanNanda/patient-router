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

| Field      | Required | Notes                                                |
| ---------- | -------- | ---------------------------------------------------- |
| `symptoms` | Yes      | Comma-separated text                                 |
| `age`      | Yes      | Passed to the selected predictor                     |
| `duration` | Yes      | Passed to the selected predictor                     |
| `vitals`   | No       | Defaults to `"normal"` in the predictors             |
| `gender`   | No       | Defaults to `"male"` in the predictors               |
| `history`  | No       | Comma-separated text; defaults to none               |
| `method`   | No       | `"patient_router"` (default), `"llm"`, or `"hybrid"` |

The API checks that `symptoms` is not empty and that `age` and `duration` are present. It does not currently enforce numeric ranges for age or duration.

**Response: `patient_router`, or `hybrid` using the local model**

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

**Response: `llm`, or `hybrid` using Gemini**

The response has the same shape, except `departments` contains one entry because the Gemini method does not return ranked alternatives. `model_version` contains the Gemini model name instead of the Patient Router version.

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

| Field           | Description                                                                                                |
| --------------- | ---------------------------------------------------------------------------------------------------------- |
| `recommended`   | Recommended department. Falls back to `general` when confidence is below the configured threshold (`0.60`). For the local method this is the model's own confidence; for the `llm` method it is the confidence mapped from Gemini's `confidence_level` |
| `departments`   | Top 3 candidates when the result comes from `patient_router`; 1 entry when the result comes from `llm`. For `llm`, this entry reflects the post-fallback `recommended` value (e.g. `general`), not Gemini's original pick, when the confidence fallback fires |
| `priority`      | `high`, `medium`, or `low`                                                                                 |
| `emergency`     | Emergency status returned by the selected prediction method                                                |
| `confidence`    | Top local model confidence or fixed confidence mapped from the Gemini confidence level                     |
| `reasons`       | Reasons returned by the selected prediction method                                                         |
| `history`       | Parsed medical history values                                                                              |
| `history_score` | Cumulative risk score from the reported medical history                                                    |
| `model_version` | Patient Router version for the local model or Gemini model name                                            |
| `warning`       | Set when vitals are omitted from the request                                                               |

For more details about the differences between the prediction methods, see [architecture.md](architecture.md#prediction-methods).

**Errors**

| Status | Condition                                                                                                             |
| ------ | --------------------------------------------------------------------------------------------------------------------- |
| `400`  | Empty request body, missing symptoms, missing age, missing duration, or another `ValueError` raised during prediction |
| `500`  | Other prediction failures, including errors raised while calling Gemini                                               |

Error body:

```json
{
  "error": "..."
}
```

---

## Feedback

### `POST /feedback`

Submits a correction and appends it as a new row to `data.csv`.

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

| Field                | Required | Notes                                   |
| -------------------- | -------- | --------------------------------------- |
| `correct_department` | Yes      | Department saved as the corrected label |
| `age`                | Yes      | Saved with the feedback row             |
| `duration`           | Yes      | Saved with the feedback row             |
| `symptoms`           | No       | Defaults to an empty string             |
| `vitals`             | No       | Defaults to `"normal"`                  |
| `gender`             | No       | Defaults to `"male"`                    |
| `history`            | No       | Defaults to an empty string             |
| `priority`           | No       | Defaults to `"low"`                     |

The feedback row is appended to `backend/data/data.csv` in this order:

```text
age, duration, symptoms, vitals, history, gender, priority, department
```

**Response**

```json
{
  "message": "Feedback successfully saved to training data."
}
```

**Errors**

| Status | Condition                                                                              |
| ------ | -------------------------------------------------------------------------------------- |
| `400`  | Empty request body, missing `correct_department`, missing `age`, or missing `duration` |
| `500`  | Failed to write the feedback row                                                       |

Error body:

```json
{
  "error": "..."
}
```

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

The exact row count, department counts, and priority counts depend on the current contents of `data.csv`.

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

The route does not currently add its own validation or error handling for the `rows` value.

---

## Training & Evaluation

### `POST /train`

Retrains the Gradient Boosting model on the current `data.csv`.

Training saves the pipeline to `backend/ml/models/model.pkl` and automatically runs the evaluation pipeline before the request finishes.

For more details, see [architecture.md](architecture.md#model-evaluation).

**Response**

```json
{
  "train_accuracy": 99.26,
  "test_accuracy": 98.84,
  "dataset_size": 50000,
  "training_time_insec": 12.44
}
```

`training_time_insec` measures the complete `train()` call, including the automatic evaluation run.

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

If the report does not exist, the endpoint returns:

```json
{
  "error": "Evaluation report not found"
}
```

The missing-report response currently uses HTTP `200`.

### `GET /evaluation/report-image`

Returns `evaluation_report.png` with the `image/png` MIME type.

If the image does not exist, the route does not define its own missing-file response and leaves the error to Flask's `send_file()` handling.

### `GET /evaluation/confusion-matrix`

Attempts to return `confusion_matrix.png` with the `image/png` MIME type.

The current evaluation pipeline does not generate this file. Confusion matrices are included in `evaluation_report.png`, so this endpoint does not match the current generated artifacts.

### `GET /evaluation/comparison`

Returns the contents of `model_comparison.json` from the latest model comparison run.

The comparison can include:

* Decision Tree
* Random Forest
* Gradient Boosting
* Logistic Regression
* K-Nearest Neighbors
* SVM with RBF kernel
* XGBoost

XGBoost is skipped when its package is not installed.

Each model is compared using test accuracy, Macro F1, 5-fold cross-validation accuracy, CV standard deviation, edge-case accuracy, generalisation gap, and training time.

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

The endpoint returns all models stored in the comparison report.

If the report does not exist:

```json
{
  "error": "Comparison report not found"
}
```

The missing-report response currently uses HTTP `200`.

### `GET /evaluation/comparison-image`

Returns `model_comparison.png` with the `image/png` MIME type.

If the image does not exist, the route does not define its own missing-file response and leaves the error to Flask's `send_file()` handling.

---

## Logs

### `GET /logs`

Returns all prediction logs, newest first, along with emergency and fallback counts.

There is currently no server-side limit or pagination.

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

`total_emergencies` and `total_fallbacks` are calculated from all returned log entries.

`model` contains the Patient Router version or Gemini model name used for the prediction.

If `predictions.jsonl` does not exist, the endpoint returns empty counts and an empty `logs` array.

The log reader does not currently skip or handle malformed JSON lines.

### `POST /logs/clear`

Clears `predictions.jsonl`.

**Response**

```json
{
  "message": "Logs cleared"
}
```

If the log file does not exist, it is created as an empty file.