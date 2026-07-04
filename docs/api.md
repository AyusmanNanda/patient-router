# API Reference

Full request/response examples for every route. For the one-line route table, see the [README](../README.md#api). For how a prediction is actually computed, see [architecture.md](architecture.md).

Base URL when running locally: `http://localhost:5000`

---

## Core

### `GET /`

Service info.

**Response:**
```json
{
  "service": "patient-router",
  "status": "running",
  "version": "1.1.0"
}
```

### `GET /health`

Health check.

**Response:**
```json
{
  "status": "ok"
}
```

---

## Prediction

### `POST /predict`

Runs a full triage prediction: department classification, confidence scoring, priority scoring, and emergency detection.

**Request:**
```json
{
  "symptoms": "chest pain, breathlessness",
  "vitals": "bp_high, hr_high",
  "age": 65,
  "duration": 2,
  "gender": "male",
  "history": "previous_heart_attack"
}
```

**Response:**
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

| Field | Description |
|---|---|
| `recommended` | Top-confidence department after the 0.60 fallback check (see [architecture.md](architecture.md#ml-pipeline)) |
| `departments` | Top 3 candidate departments with confidence scores |
| `priority` | `high` / `medium` / `low`, from the priority scoring logic |
| `emergency` | `true` if an emergency symptom or vital was detected |
| `reasons` | Human-readable list of everything that contributed to the priority/emergency decision |
| `history_score` | Cumulative risk score from reported medical history |
| `warning` | Populated if confidence fell below the 0.60 threshold and the department fell back to `general` |

---

## Feedback

### `POST /feedback`

Submits a correction for a previous prediction. Appended directly to `data.csv` and picked up by the next `/train` call.

**Request:**
```json
{
  "symptoms": "chest pain, breathlessness",
  "vitals": "bp_high, hr_high",
  "age": 65,
  "duration": 2,
  "gender": "male",
  "history": "previous_heart_attack",
  "correct_department": "cardiology"
}
```

**Response:**
```json
{
  "status": "recorded",
  "message": "Feedback appended to training data"
}
```

---

## Dataset

### `GET /data`

Returns dataset stats.

**Response:**
```json
{
  "rows": 50000,
  "columns": 6,
  "department_distribution": {
    "cardiology": 8333,
    "pulmonology": 8333,
    "neurology": 8333,
    "orthopedics": 8334,
    "gastrology": 8333,
    "general": 8334
  },
  "priority_distribution": {
    "high": 12500,
    "medium": 21000,
    "low": 16500
  }
}
```

### `POST /data/generate`

Regenerates the synthetic dataset.

**Request:**
```json
{ "rows": 50000 }
```

**Response:**
```json
{
  "status": "generated",
  "rows_written": 50000,
  "path": "backend/data/data.csv"
}
```

---

## Training & Evaluation

### `POST /train`

Retrains the model on the current `data.csv`.

**Response:**
```json
{
  "status": "trained",
  "model_version": "1.1.0",
  "accuracy": 0.94,
  "model_path": "backend/ml/models/model.pkl"
}
```

### `GET /evaluation`

Returns evaluation metrics as JSON.

**Response:**
```json
{
  "accuracy": 0.94,
  "cross_val_scores": [0.93, 0.94, 0.95, 0.94, 0.93],
  "cross_val_mean": 0.938,
  "per_class_f1": {
    "cardiology": 0.96,
    "pulmonology": 0.93,
    "neurology": 0.92,
    "orthopedics": 0.95,
    "gastrology": 0.91,
    "general": 0.89
  }
}
```

### `GET /evaluation/confusion-matrix`

Returns `confusion_matrix.png` as an image response.

### `GET /evaluation/report-image`

Returns `evaluation_report.png` as an image response.

---

## Logs

### `GET /logs`

Returns prediction history plus emergency/fallback counts.

**Response:**
```json
{
  "total_predictions": 1204,
  "emergency_count": 87,
  "fallback_count": 42,
  "recent": [
    {
      "timestamp": "2026-07-01T14:32:10Z",
      "recommended": "cardiology",
      "priority": "high",
      "emergency": true
    }
  ]
}
```

### `POST /logs/clear`

Clears the prediction log.

**Response:**
```json
{
  "status": "cleared"
}
```