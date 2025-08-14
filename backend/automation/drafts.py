import sqlite3
import os
from typing import List, Dict, Any

DB_PATH = os.path.join("data", "drafts.db")

def init_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS drafts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT NOT NULL,
            title TEXT,
            company TEXT,
            content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def list_drafts() -> List[Dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, job_id, title, company, content, created_at FROM drafts ORDER BY created_at DESC")
    rows = c.fetchall()
    conn.close()
    return [
        {"id": r[0], "job_id": r[1], "title": r[2], "company": r[3], "content": r[4], "created_at": r[5]}
        for r in rows
    ]

def get_draft(draft_id: int) -> Dict[str, Any]:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, job_id, title, company, content, created_at FROM drafts WHERE id=?", (draft_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return {"id": row[0], "job_id": row[1], "title": row[2], "company": row[3], "content": row[4], "created_at": row[5]}
    return None

def save_draft(job_id: str, title: str, company: str, content: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO drafts (job_id, title, company, content) VALUES (?, ?, ?, ?)", 
              (job_id, title, company, content))
    conn.commit()
    conn.close()

def delete_draft(draft_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM drafts WHERE id=?", (draft_id,))
    conn.commit()
    conn.close()
    