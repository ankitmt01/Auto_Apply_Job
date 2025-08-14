import time, os, requests
from apply_db import get_next_task, transition

API_BASE = os.getenv("API_BASE", "http://api:8000")  # talk to backend
POLL_SEC = 3

def run_once():
    task = get_next_task()
    if not task:
        return False
    app_id, task_id = task["application_id"], task["id"]
    transition(app_id, task_id, "TAILORING")
    # 1) Tailor materials (reuse your API)
    try:
        job = {"title": task["title"], "company": task["company"], "jd_text": "" }
        r = requests.post(f"{API_BASE}/jobs/tailor", json={"job": job}, timeout=60)
        r.raise_for_status()
        tailored = r.json()
    except Exception as e:
        transition(app_id, task_id, "FAILED", error=str(e)); return True

    # 2) For now, stop at NAVIGATING (we’ll add adapters next)
    transition(app_id, task_id, "STUCK", error="Adapter not implemented yet")
    return True

if __name__ == "__main__":
    while True:
        worked = run_once()
        time.sleep(POLL_SEC if not worked else 0.5)
