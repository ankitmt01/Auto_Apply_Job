from fastapi import APIRouter
from pydantic import BaseModel
import uuid
import sqlite3
import time
from pathlib import Path
import json
from playwright.sync_api import sync_playwright

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "drafts.sqlite3"

router = APIRouter()

class DraftRequest(BaseModel):
    job_url: str
    company: str
    title: str
    resume_path: str = None

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS drafts (
            id TEXT PRIMARY KEY,
            job_url TEXT,
            company TEXT,
            title TEXT,
            status TEXT,
            step TEXT,
            screenshot_path TEXT,
            snapshot_path TEXT,
            created_at REAL
        )
    """)
    conn.commit()
    conn.close()

init_db()

@router.post("/applications/draft")
def create_draft(req: DraftRequest):
    draft_id = str(uuid.uuid4())
    screenshot_path = str(DATA_DIR / f"{draft_id}.png")
    snapshot_path = str(DATA_DIR / f"{draft_id}.html")
    
    # Playwright automation
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(req.job_url, timeout=60000)
            time.sleep(3)
            page.screenshot(path=screenshot_path)
            Path(snapshot_path).write_text(page.content(), encoding="utf-8")
        finally:
            browser.close()

    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO drafts (id, job_url, company, title, status, step, screenshot_path, snapshot_path, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (draft_id, req.job_url, req.company, req.title, "stuck", "autofill", screenshot_path, snapshot_path, time.time())
    )
    conn.commit()
    conn.close()

    return {"id": draft_id, "status": "stuck", "screenshot": f"/files/{Path(screenshot_path).name}"}

@router.get("/applications/drafts")
def list_drafts():
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT * FROM drafts").fetchall()
    conn.close()
    return [
        {
            "id": r[0],
            "job_url": r[1],
            "company": r[2],
            "title": r[3],
            "status": r[4],
            "step": r[5],
            "screenshot_url": f"/files/{Path(r[6]).name}" if r[6] else None,
            "snapshot_url": f"/files/{Path(r[7]).name}" if r[7] else None,
            "created_at": r[8]
        }
        for r in rows
    ]

@router.post("/applications/resume/{draft_id}")
def resume_draft(draft_id: str):
    return {"id": draft_id, "status": "resume_not_implemented_yet"}

@router.delete("/applications/{draft_id}")
def delete_draft(draft_id: str):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM drafts WHERE id = ?", (draft_id,))
    conn.commit()
    conn.close()
    return {"id": draft_id, "status": "deleted"}
