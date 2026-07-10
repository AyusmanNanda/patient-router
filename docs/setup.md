# Setup

Detailed environment, configuration, and troubleshooting notes for running Patient Router locally. For quick-start commands, see the [README](../README.md#running-locally). For request/response contracts, see [api.md](api.md). For pipeline internals, see [architecture.md](architecture.md). For production hosting, see [deployment.md](deployment.md).

---

## Prerequisites

| Tool    | Version           | Notes                                                                                                        |
| ------- | ----------------- | ------------------------------------------------------------------------------------------------------------ |
| Python  | 3.11              | Matches the README badge. Not enforced by a lockfile; stick to 3.11 to avoid scikit-learn/numpy build issues |
| Node.js | 20.19+ or 22.12+  | Required by the current Vite 8 tooling                                                                       |
| npm     | bundled with Node | None                                                                                                         |

---

## Backend Setup

### 1. Install dependencies

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment variables

`app.py` loads a `.env` file via `python-dotenv` and refuses to start without `FRONTEND_URL` set, raising a `RuntimeError` on boot otherwise:

```python
frontend_url = os.getenv("FRONTEND_URL")
if not frontend_url:
    raise RuntimeError("FRONTEND_URL and PRODUCTION_FRONTEND_URL must be set")
```

The repo ships a `backend/.env.example`:

```bash
FLASK_DEBUG=true
FRONTEND_URL=http://localhost:5173
PRODUCTION_FRONTEND_URL=
GEMINI_API_KEY=
```

Copy it and fill in the required values:

```bash
cp .env.example .env
```

| Variable                  | Required                                                 | Default                 | Purpose                                                                                                                                                    |
| ------------------------- | -------------------------------------------------------- | ----------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `FRONTEND_URL`            | Yes                                                      | None, app fails to boot | Allowed CORS origin, passed to `flask-cors`                                                                                                                |
| `FLASK_DEBUG`             | No                                                       | `false`                 | Enables Flask debug mode and reloader when `"true"`                                                                                                        |
| `PRODUCTION_FRONTEND_URL` | Listed, but unused                                       | None                    | Present in `.env.example` and referenced in the startup error message, but `app.py` does not currently read it. See [deployment.md](deployment.md#backend) |
| `GEMINI_API_KEY`          | Required for the `llm` and low-confidence `hybrid` paths | None                    | Used by the Gemini predictor. See [architecture.md](architecture.md#llm---gemini-25-flash)                                                                 |

### 3. Generate data and train

```bash
python -m ml.generate_data   # writes backend/data/data.csv
python -m ml.train           # trains the model and runs evaluation
```

The generated dataset size is controlled by `SAMPLE_SIZE` in `ml/constants.py`, currently `50000`.

Training saves the Gradient Boosting pipeline to `backend/ml/models/model.pkl` and automatically runs model evaluation. See [architecture.md](architecture.md#model-evaluation) for the evaluation workflow and generated reports.

### 4. Run the API

```bash
python app.py
```

Runs on `0.0.0.0:5000` by default.

### Dependencies

`requirements.txt` includes packages beyond the local ML pipeline:

| Package                 | Role                                                                                                                   |
| ----------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| `google-genai`          | Gemini client for the `llm` and `hybrid` prediction methods. See [architecture.md](architecture.md#prediction-methods) |
| `matplotlib`, `seaborn` | Evaluation and model comparison report images                                                                          |
| `xgboost`               | Optional XGBoost model used by the model comparison script                                                             |
| `gunicorn`              | Production WSGI server; not used by the local development server. See [deployment.md](deployment.md#backend)           |

---

## Frontend Setup

### Web (Vite dev server)

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

`vite.config.ts` uses `base: "./"` for relative asset paths. The same frontend build can therefore be loaded by the Electron application.

| Script            | Command                | Purpose                            |
| ----------------- | ---------------------- | ---------------------------------- |
| `npm run dev`     | `vite`                 | Local development server           |
| `npm run build`   | `tsc -b && vite build` | Type-check and production build    |
| `npm run lint`    | `eslint .`             | Lint                               |
| `npm run preview` | `vite preview`         | Preview a production build locally |

### Desktop (Electron)

`package.json` defines `electron/main.ts` as the Electron entrypoint and uses `electron-builder` for Windows and Linux builds.

```bash
npm run build          # build the frontend first
npm run electron       # run the Electron shell against dist/
npm run dist           # build an installer for the current OS
npm run dist:win       # Windows NSIS installer
npm run dist:linux     # Linux AppImage
```

`npm run electron` does not build the frontend automatically. Run `npm run build` first so that `dist/index.html` exists.

The `dist`, `dist:win`, and `dist:linux` scripts run the frontend build automatically before starting `electron-builder`.

Installer output goes to `release/installers/`. Windows builds use `electron/icon.ico`, while Linux builds use `electron/icon.png`.

See [deployment.md](deployment.md#desktop-electron) for deployment and release details.

---

## Troubleshooting

| Symptom                                                                      | Likely Cause                                                                                                   |
| ---------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| `RuntimeError: FRONTEND_URL and PRODUCTION_FRONTEND_URL must be set` on boot | Missing `backend/.env` or missing `FRONTEND_URL` key in it                                                     |
| Frontend requests fail with a CORS error                                     | `FRONTEND_URL` in `backend/.env` does not match the origin the frontend is served from                         |
| `python -m ml.train` prints `Failed to load data.csv` and exits              | Run `python -m ml.generate_data` first. Training expects `backend/data/data.csv` to already exist              |
| Frontend cannot reach the API                                                | The frontend backend URL does not match where `app.py` is running, which is `http://localhost:5000` by default |
| `npm run electron` fails to load the application                             | Run `npm run build` first. The Electron development path expects `frontend/dist/index.html` to exist           |
| `llm` or low-confidence `hybrid` prediction fails                            | Check that `GEMINI_API_KEY` is configured in `backend/.env`                                                    |
