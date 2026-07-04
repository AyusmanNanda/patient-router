# Deployment

For local development, see [setup.md](setup.md).

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

SPA rewrite required for `react-router-dom` client-side routing. Without it, direct navigation to any route other than `/` returns a 404.

**Build:** Vercel auto-detects Vite from `package.json`. No custom build command needed.

**Required env var**

| Var | Value |
|---|---|
| `VITE_BACKEND` | Production Flask API URL |

`vite.config.ts` sets `base: "./"` (relative asset paths). Unrelated to the rewrite rule, but relevant if the app is served from a subpath.

---

## Backend

No deployment config for the backend exists in this repo; `vercel.json` covers the frontend only.

**Production requirements, inferred from code**

| Requirement | Source |
|---|---|
| WSGI server (`gunicorn`) instead of `app.run()` | `requirements.txt` includes `gunicorn`; `app.py`'s dev server is single-threaded with a debug flag |
| `FRONTEND_URL` set to the deployed frontend's origin | `app.py` — CORS `origins` |
| `GEMINI_API_KEY` set if `llm`/`hybrid` methods should work | `llm.py` |

**Known gap:** `.env.example` lists `PRODUCTION_FRONTEND_URL`, but `app.py` never reads it. There is no way to allow both a local and a production frontend origin at once — `FRONTEND_URL` must be swapped per environment, or the CORS `origins` list extended manually.

**Outstanding items**

| Item | Status |
|---|---|
| Hosting provider and start command | Not documented |
| Whether `model.pkl` / `data.csv` are baked into the deploy image or generated post-deploy | Not documented |
| Whether `GEMINI_API_KEY` is set in production | Not documented |

---

## Desktop (Electron)

```bash
npm run dist         # current OS
npm run dist:win     # Windows installer (nsis)
npm run dist:linux   # Linux AppImage
```

Output: `release/installers/`. Windows build requires `electron/icon.ico`.

Packaging is a manual step; no CI workflow builds or publishes these.