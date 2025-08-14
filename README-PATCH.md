
# Backend Patch 1 — Live Greenhouse/Lever search

## What this adds
- `/search/jobs` now fetches **real jobs** from Greenhouse and Lever boards.
- Simple keyword scoring and de-duplication.
- Config via env vars: `GH_BOARDS`, `LEVER_COMPANIES`

## How to use
1) Copy the `backend/` folder into your project (replace existing backend).
2) In your project root, create a `.env` file based on `.env.example`:

```
GH_BOARDS=openai,stripe
LEVER_COMPANIES=vercel
```

3) Rebuild & run Docker:
```
docker compose up --build
```
4) Test health:
- http://localhost:8000/health — you should see your board tokens
5) The UI Jobs tab will now show **real postings** when it calls `/search/jobs`.

## Notes
- Some companies may not expose public JSON endpoints; if a board returns 404 or blocks, just remove it from the env list.
- Next patches will add: better ranking, `/jobs/{id}/tailor`, and Playwright drafting with save/resume.
