# EnvGuard

EnvGuard is a lightweight **environment variable readiness scanner**.

- Upload a `.env.example` file in the dashboard
- The backend checks which keys are present (and non-empty) in the backend runtime environment
- You get a **Found / Missing** report and a deployment readiness badge

## Project structure

- `backend/`: FastAPI API service (`POST /api/scan`)
- `frontend/`: static dashboard served by Nginx
- `docker-compose.yml`: runs both services
- `backend.env`: environment variables used by the backend container (do not commit secrets)

## Prerequisites

- Docker Desktop (with `docker compose` working)

## Run (Docker Compose)

From the repo root:

```bash
docker compose up --build
```

## Verify in browser

Ports can be changed in `docker-compose.yml`. Defaults in this repo:

- Frontend dashboard: `http://localhost:8081/`
- Backend docs (Swagger): `http://localhost:8001/docs`

The dashboard calls the API via same-origin `/api/scan` (Nginx reverse-proxy to the backend container).

## How scanning works

- You upload a `.env.example`
- EnvGuard extracts keys (supports `export KEY=...`, ignores comments, tolerates inline comments)
- A key is marked **Found** only if it exists in the backend environment **and its value is not empty**

## Configure environment variables (Option B: env_file)

This repo uses `backend.env` and `docker-compose.yml` loads it into the backend container:

- Edit `backend.env` and set your real values
- Restart containers:

```bash
docker compose up --build
```

If you scan a `.env.example` that contains keys from `backend.env`, they should show as **Found**.

## Test the API without the UI

### Using Swagger UI

Open `http://localhost:8001/docs` → `POST /api/scan` → **Try it out** → upload your `.env.example`.

### Using curl

```bash
curl -s -X POST "http://localhost:8001/api/scan" ^
  -H "accept: application/json" ^
  -F "file=@.env.example"
```

## Notes

- `backend.env` is listed in `.gitignore`. Treat it as secret material.
- If ports conflict with other apps (e.g. Grafana on `3000`), update `docker-compose.yml` ports.

