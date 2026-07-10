# Deployment

For local development and environment configuration, see [setup.md](setup.md).

---

## Frontend (Vercel)

`frontend/vercel.json`:

```json
{
  "rewrites": [
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}
```

The SPA rewrite is required for `react-router-dom` client-side routing. Without it, direct navigation to routes other than `/` can return a 404.

**Build:** Vercel detects Vite from `package.json` and builds the frontend.

**Required environment variable**

| Variable       | Value                    |
| -------------- | ------------------------ |
| `VITE_BACKEND` | Production Flask API URL |

The frontend Axios client uses `VITE_BACKEND` as its API base URL.

`vite.config.ts` sets `base: "./"` for relative asset paths. This is separate from the Vercel rewrite rule and also allows the same frontend build to be loaded by the Electron application.

---

## Backend

The repository does not include deployment configuration for a specific backend hosting provider. `frontend/vercel.json` only configures the frontend deployment.

`requirements.txt` includes `gunicorn` as a production WSGI server. Local development uses Flask's `app.run()` server.

**Production requirements**

| Requirement                                                                        | Reason                                                                                       |
| ---------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| A Python hosting environment with dependencies from `requirements.txt`             | Required to run the Flask backend and ML pipeline                                            |
| `FRONTEND_URL` set to the deployed frontend origin                                 | Used as the allowed CORS origin                                                              |
| `GEMINI_API_KEY` configured if the `llm` or low-confidence `hybrid` paths are used | Required by the Gemini predictor                                                             |
| Access to the model, dataset, and generated report files                           | Used by prediction, dataset management, training, evaluation, and model comparison endpoints |

`.env.example` also lists `PRODUCTION_FRONTEND_URL`, but `app.py` does not currently read it. Only `FRONTEND_URL` is passed to the CORS configuration.

This means the allowed frontend origin has to be configured through `FRONTEND_URL` for each deployment environment.

The repository does not currently define a backend hosting provider or deployment-specific start command. How `model.pkl`, `data.csv`, and generated reports are stored or persisted depends on the selected hosting environment.

---

## Desktop (Electron)

The same React frontend is also packaged as an Electron desktop application for Windows and Linux.

```bash
npm run dist         # build for the current OS
npm run dist:win     # Windows NSIS installer
npm run dist:linux   # Linux AppImage
```

Each script runs the frontend production build before starting `electron-builder`.

Build output is written to:

```text
frontend/release/installers/
```

Windows builds use `electron/icon.ico`, while Linux builds use `electron/icon.png`.

The Electron application loads the built `dist/index.html` locally. The frontend still communicates with the Flask backend through the API URL configured by `VITE_BACKEND`.

The current GitHub Actions workflows run backend and frontend CI checks. Desktop packaging and release publishing are not handled by these workflows, so release builds are created separately using the Electron build commands above.
