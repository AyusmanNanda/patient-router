<p align="center">
  <img src="docs/assets/icons/favicon.svg" width="72" alt="Patient Router logo" />
</p>

<h1 align="center">Patient Router</h1>

<p align="center">
  <a href="https://github.com/AyusmanNanda/patient-router/actions/workflows/backend-ci.yml">
    <img src="https://github.com/AyusmanNanda/patient-router/actions/workflows/backend-ci.yml/badge.svg" alt="Backend CI status" />
  </a>
  <a href="https://github.com/AyusmanNanda/patient-router/actions/workflows/frontend-ci.yml">
    <img src="https://github.com/AyusmanNanda/patient-router/actions/workflows/frontend-ci.yml/badge.svg" alt="Frontend CI status" />
  </a>
  <a href="https://patient-router.vercel.app">
    <img src="https://img.shields.io/badge/demo-live-2E4374" alt="Live demo" />
  </a>
  <img src="https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/Flask-black?logo=flask&logoColor=white" alt="Flask" />
  <img src="https://img.shields.io/badge/React-20232A?logo=react&logoColor=61DAFB" alt="React" />
  <img src="https://img.shields.io/badge/TypeScript-3178C6?logo=typescript&logoColor=white" alt="TypeScript" />
  <img src="https://img.shields.io/badge/scikit--learn-F7931E?logo=scikitlearn&logoColor=white" alt="scikit-learn" />
  <a href="LICENSE">
    <img src="https://img.shields.io/github/license/AyusmanNanda/patient-router?color=lightgrey" alt="License" />
  </a>
</p>

<p align="center">
  <b><a href="https://patient-router.vercel.app">Live Demo →</a></b>
</p>

> This is a student research prototype, not a validated clinical tool. It has not been tested on real patients, so please don't use it to make actual triage decisions.

---

## Overview

In hospital emergency departments, patients are often sent to the wrong department at first, and that wastes time that matters. For this project I tried to see if a simple ML model could help with that first triage step: a Random Forest trained on structured patient data, plus some rule-based logic on top for priority and emergency cases, and a feedback loop so corrections go back into the training data.

It's trained only on synthetic data I generated myself, so please treat the predictions as a proof of concept, not something clinically reliable.

The project has three parts:

| Part | Location | Responsibility |
|---|---|---|
| ML core | `backend/ml/` | Synthetic data generation, training, evaluation, inference |
| Flask API | `backend/app.py`, `routes/`, `services/` | Exposes the ML pipeline over HTTP |
| React dashboard | `frontend/` | Patient intake form, feedback collection, dataset manager, training runner, evaluation viewer, logs |

For the full pipeline, API contract, environment setup, and everything else, see the table below.

---

## Documentation

| Doc | Covers |
|---|---|
| [docs/architecture.md](docs/architecture.md) | ML pipeline, the three prediction methods, priority scoring, emergency detection, normalization, evaluation, feedback loop |
| [docs/api.md](docs/api.md) | Full request/response examples for every route |
| [docs/setup.md](docs/setup.md) | Environment variables, local setup, troubleshooting |
| [docs/frontend.md](docs/frontend.md) | React dashboard structure: pages, hooks, shared components |
| [docs/data-schema.md](docs/data-schema.md) | Symptom/vital/history vocabulary and weight tables |
| [docs/deployment.md](docs/deployment.md) | Vercel frontend, backend hosting requirements, desktop builds |

---

## System Flow

```mermaid
flowchart LR
    A[Patient Input] --> B[ML Pipeline\nRandom Forest / LLM / Hybrid]
    B --> C[Priority & Emergency Rules]
    C --> D[Recommendation + Logged Prediction]
```

Full breakdown of each stage (normalization, the three prediction methods, priority scoring, and emergency detection) lives in `docs/architecture.md`.

---

## Screenshots

<details>
<summary>Click to expand</summary>

| Patient Router | Train Model |
|---|---|
| ![Patient Router](docs/assets/screenshots/home.png) | ![Train Model](docs/assets/screenshots/train.png) |

| Data Manager | Evaluation |
|---|---|
| ![Data Manager](docs/assets/screenshots/datamanager.png) | ![Evaluation](docs/assets/screenshots/evaluation.png) |

| System Logs |
|---|
| ![System Logs](docs/assets/screenshots/logs.png) |

</details>

---

## API

**Core:** `GET /`, `GET /health`
**Prediction & Feedback:** `POST /predict`, `POST /feedback`
**Dataset:** `GET /data`, `POST /data/generate`
**Training & Evaluation:** `POST /train`, `GET /evaluation`, `GET /evaluation/confusion-matrix`, `GET /evaluation/report-image`
**Logs:** `GET /logs`, `POST /logs/clear`

Full request/response examples for every route: `docs/api.md`

---

## Running Locally

```bash
# backend
cd backend && python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python -m ml.generate_data && python -m ml.train
python app.py

# frontend
cd frontend && npm install
echo "VITE_BACKEND=http://localhost:5000" > .env && npm run dev
```

Environment variables, config, and troubleshooting: `docs/setup.md`

---

## Limitations

- Everything is trained on synthetic data I generated, not real patient records, so I can't say how it would actually perform in a hospital
- Only 6 departments, 20 symptoms, 7 vitals, and 6 history conditions: this was a scope decision to keep the project manageable, not something I ran out of time to add

---

## Tech Stack

**Backend:** Python, Flask, scikit-learn, pandas, numpy, joblib
**Frontend:** React, TypeScript, Vite, lucide-react
**ML:** RandomForestClassifier, CountVectorizer, OneHotEncoder