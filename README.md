
# Agentic Job Assistant — Advanced Starter (Windows & Linux, with UI)

This is a ready-to-run starter with a **modern UI (React + Tailwind)** and a **FastAPI mock backend**.
Run locally on Windows now; move to Linux later with the same Docker command.

## Prereqs (Windows)
- Docker Desktop
- (Optional) Node 20+ & Python 3.11+ if you want to run without Docker

## Run with Docker (recommended)
1) Open Terminal and `cd` into this folder
2) Run: `docker compose up --build`
3) UI: http://localhost:5173
4) API docs: http://localhost:8000/docs

## What works now
- UI loads advanced dashboard (Jobs, Drafts, Applications, Tailoring)
- Jobs tab shows demo cards
- Backend `POST /search/jobs` returns mock jobs

## Next steps (swap mocks with real logic)
- Implement real connectors in backend `/search/jobs`
- Add `/jobs/{id}/tailor` for resume & cover-letter generation
- Add `/applications/draft` and checkpoints for save/resume

Tip: keep all config in `.env` and use volumes for data.
