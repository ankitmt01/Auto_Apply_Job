import sys, os
sys.path.append(os.path.dirname(__file__) or ".")

import os, json
from datetime import datetime
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# connectors
from connectors.greenhouse import fetch_greenhouse_jobs
from connectors.lever import fetch_lever_jobs

# tailoring
from tailor import tailor

# drafts / automation
from automation.drafts import init_db, list_drafts, get_draft, delete_draft
from automation.autofill_playwright import run_draft
from playwright.async_api import async_playwright

# >>> apply queue (NEW)
from apply_db import init_apply, enqueue_application, list_applications  # <-- make sure backend/apply_db.py exists

app = FastAPI(title="Agentic Job Assistant API", version="0.5.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve generated files (DOCX, cover letter, screenshots, DOM snapshots)
app.mount("/files", StaticFiles(directory="data"), name="files")

# Env config
GH_BOARDS = [x.strip() for x in os.getenv("GH_BOARDS","").split(",") if x.strip()]
LEVER_COMPANIES = [x.strip() for x in os.getenv("LEVER_COMPANIES","").split(",") if x.strip()]

# ------------ Models ------------
class SearchRequest(BaseModel):
    roles: List[str] = []
    locations: List[str] = []
    keywords: List[str] = []
    min_score: Optional[int] = 0  # 0–100

class JobPosting(BaseModel):
    id: str
    title: str
    company: str
    location: str
    source: str
    url: str
    jd_text: str
    score: float
    created_at: datetime

class TailorRequest(BaseModel):
    job: Dict[str, Any]
    profile: Optional[Dict[str, Any]] = None

class DraftRequest(BaseModel):
    job: Dict[str, Any]

# ------------ Startup ------------
@app.on_event("startup")
async def _startup():
    # drafts DB (screenshots/snapshots list)
    init_db()
    # apply queue DB (applications/tasks)
    init_apply()

@app.get("/health")
def health():
    return {"status": "ok", "gh_boards": GH_BOARDS, "lever_companies": LEVER_COMPANIES}

# ------------ Helpers ------------
def score_job(j, req: SearchRequest) -> int:
    title = (j.get("title") or "").lower()
    jd = (j.get("jd_text") or "").lower()
    loc_text = (j.get("location") or "").lower()

    raw = (req.roles or []) + (req.keywords or [])
    tokens = []
    for item in raw:
        if not item:
            continue
        s = item.lower().strip()
        tokens.append(s)  # phrase
        tokens.extend([t for t in s.replace("/", " ").replace("-", " ").split() if t])

    score = 0
    for t in tokens:
        if t in title:
            score += 25
        elif t in jd:
            score += 10

    for l in (req.locations or []):
        if l and l.lower() in loc_text:
            score += 10
            break

    if score == 0:
        score = 50
    return max(0, min(100, score))

# ------------ Search ------------
@app.post("/search/jobs", response_model=List[JobPosting])
def search_jobs(req: SearchRequest):
    jobs = []
    # Greenhouse
    for token in GH_BOARDS:
        try:
            jobs.extend(fetch_greenhouse_jobs(token, req.roles, req.locations))
        except Exception as e:
            print(f"[GH] {token} error: {e}")
    # Lever
    for company in LEVER_COMPANIES:
        try:
            jobs.extend(fetch_lever_jobs(company, req.roles, req.locations))
        except Exception as e:
            print(f"[Lever] {company} error: {e}")

    # Score + filter + sort + dedupe
    resp: List[JobPosting] = []
    for j in jobs:
        s = score_job(j, req)
        jp = JobPosting(
            id=j["id"],
            title=j["title"],
            company=j["company"],
            location=j["location"],
            source=j["source"],
            url=j["url"],
            jd_text=j["jd_text"],
            created_at=datetime.fromisoformat(j["created_at"].replace("Z","+00:00")) if isinstance(j["created_at"], str) else j["created_at"],
            score=s/100.0,
        )
        if (req.min_score or 0) <= s:
            resp.append(jp)

    resp.sort(key=lambda x: x.score, reverse=True)
    seen = set()
    dedup: List[JobPosting] = []
    for r in resp:
        key = (r.company.lower(), r.title.lower(), r.url)
        if key in seen:
            continue
        seen.add(key)
        dedup.append(r)
    return dedup

# ------------ Tailor ------------
@app.post("/jobs/tailor")
def tailor_job(req: TailorRequest, request: Request):
    job = req.job or {}
    if not job.get("title"):
        raise HTTPException(400, "Missing job object")
    result = tailor(job, req.profile)

    # absolute URLs for downloads
    base = str(request.base_url).rstrip("/")  # e.g., http://localhost:8000
    for k in ("resume_docx_path","cover_letter_path"):
        p = result.get(k)
        if p and p.startswith("data/"):
            filename = p.split("data/", 1)[1]
            result[k.replace("_path","_url")] = f"{base}/files/{filename}"
    return result

# ------------ Drafts (Playwright) ------------
@app.get("/applications/drafts")
def api_list_drafts():
    items = list_drafts()
    # add public URLs
    for it in items:
        for key in ("screenshot_path","snapshot_path"):
            p = it.get(key) or ""
            if p.startswith("data/"):
                it[key.replace("_path","_url")] = f"/files/{p.split('data/',1)[1]}"
    return items

@app.post("/applications/draft")
async def api_create_draft(req: DraftRequest):
    job = req.job or {}
    if not job.get("url"):
        raise HTTPException(400, "Missing job.url")
    async with async_playwright() as pw:
        result = await run_draft(pw, job)
    return result

@app.post("/applications/resume/{draft_id}")
def api_resume_draft(draft_id: str):
    d = get_draft(draft_id)
    if not d:
        raise HTTPException(404, "Draft not found")
    # Stub for now — can implement real resume logic later.
    return {"id": draft_id, "status": d["status"], "message": "Resume not yet implemented – open the job URL to continue manually."}

@app.delete("/applications/{draft_id}")
def api_delete_draft(draft_id: str):
    delete_draft(draft_id)
    return {"ok": True}

# ------------ Apply queue (NEW) ------------
class ApplyRequest(BaseModel):
    jobs: list[dict]

@app.post("/apply")
def apply_jobs(req: ApplyRequest):
    ids = [enqueue_application(j) for j in (req.jobs or [])]
    return {"application_ids": ids}

@app.get("/applications")
def applications_list():
    return list_applications()
