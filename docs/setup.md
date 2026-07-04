# Setup

Detailed environment, configuration, and troubleshooting notes for running Patient Router locally. For quick-start commands, see the [README](../README.md#running-locally). For request/response contracts, see [api.md](api.md). For pipeline internals, see [architecture.md](architecture.md). For production hosting, see [deployment.md](deployment.md).

---

## Prerequisites

| Tool | Version | Notes |
|---|---|---|
| Python | 3.11 | Matches the README badge. Not enforced by a lockfile; stick to 3.11 to avoid scikit-learn/numpy build issues |
| Node.js | 18+ recommended | Not pinned in `package.json`, but required by Vite 8 / React 19 tooling |
| npm | bundled with Node | — |

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

Copy it and fill in real values:

```bash
cp .env.example .env
```

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `FRONTEND_URL` | Yes | — (app fails to boot) | Sole allowed CORS origin, passed to `flask-cors` |
| `FLASK_DEBUG` | No | `false` | Enables Flask debug mode/reloader when `"true"` |
| `PRODUCTION_FRONTEND_URL` | Listed, but unused | — | Present in `.env.example` and referenced in the startup error message, but `app.py` never reads it. See [deployment.md](deployment.md#backend) for the known gap this creates |
| `GEMINI_API_KEY` | Required if the `llm`/`hybrid` predictor is used | — | Consumed by `backend/ml/predictors/llm.py`. See [architecture.md](architecture.md#llm--gemini-25-flash) |

### 3. Generate data and train

```bash
python -m ml.generate_data   # writes backend/data/data.csv (SAMPLE_SIZE = 50000, see ml/constants.py)
python -m ml.train           # writes backend/ml/models/model.pkl + reports/
```

### 4. Run the API

```bash
python app.py
```

Runs on `0.0.0.0:5000` by default (hardcoded in `app.py`).

### Dependencies

`requirements.txt` includes packages beyond the core RF pipeline:

| Package | Role |
|---|---|
| `google-genai` | Gemini client for the `llm`/`hybrid` predictors — see [architecture.md](architecture.md#prediction-methods) |
| `matplotlib`, `seaborn` | Evaluation report images (`confusion_matrix.png`, `evaluation_report.png`) |
| `gunicorn` | Production WSGI server; not used by the local dev server (`app.py` runs its own on port 5000) — see [deployment.md](deployment.md#backend) |
| `beautifulsoup4`, `websockets` | No corresponding code path identified |

---

## Frontend Setup

### Web (Vite dev server)

```bash
cd frontend
npm install
echo "VITE_BACKEND=http://localhost:5000" > .env
npm run dev
```

`vite.config.ts` uses `base: "./"` (relative asset paths). This matters if the built `dist/` output is ever served from a non-root path, and is why the same build also works for the Electron shell below.

| Script | Command | Purpose |
|---|---|---|
| `npm run dev` | `vite` | Local dev server |
| `npm run build` | `tsc -b && vite build` | Type-check + production build |
| `npm run lint` | `eslint .` | Lint |
| `npm run preview` | `vite preview` | Preview a production build locally |

### Desktop (Electron)

`package.json` defines `main: electron/main.ts` and a full `electron-builder` config; the project also ships as a desktop app, separate from the Vercel-hosted web demo.

```bash
npm run electron       # run the Electron shell against the current build
npm run dist           # build installers for the current OS
npm run dist:win       # Windows installer (nsis)
npm run dist:linux     # Linux AppImage
```

Build output goes to `release/installers/`. The Windows build expects an icon at `electron/icon.ico`. See [deployment.md](deployment.md#desktop-electron).

---

## Troubleshooting

| Symptom | Likely Cause |
|---|---|
| `RuntimeError: FRONTEND_URL and PRODUCTION_FRONTEND_URL must be set` on boot | Missing `backend/.env` or missing `FRONTEND_URL` key in it |
| Frontend requests fail with a CORS error | `FRONTEND_URL` in `backend/.env` doesn't match the origin the frontend is actually served from |
| `python -m ml.train` fails with a missing-file error | Run `python -m ml.generate_data` first — `train.py` expects `backend/data/data.csv` to already exist |
| Frontend can't reach the API | `frontend/.env`'s `VITE_BACKEND` doesn't match where `app.py` is actually running (default `http://localhost:5000`) |