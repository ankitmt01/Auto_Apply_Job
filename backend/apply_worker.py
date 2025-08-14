import asyncio, os, traceback
from apply_db import init_apply, dequeue_next, increment_attempts, update_task_status, set_artifacts
from tailor import tailor

FAKE = os.getenv("AUTO_APPLY_FAKE", "0") == "1"

PROFILE = {
    "first_name": os.getenv("PROFILE_FIRST_NAME",""),
    "last_name":  os.getenv("PROFILE_LAST_NAME",""),
    "email":      os.getenv("PROFILE_EMAIL",""),
    "phone":      os.getenv("PROFILE_PHONE",""),
    "linkedin":   os.getenv("PROFILE_LINKEDIN",""),
}

SLEEP_IDLE_SEC = 3
MAX_RETRIES = 2

async def submit_real(job, files, profile):
    from playwright.async_api import async_playwright
    from automation.autofill_playwright import submit_for_job
    async with async_playwright() as pw_ctx:
        return await submit_for_job(pw_ctx, job, files, profile)

async def process_one():
    item = dequeue_next()
    if not item:
        await asyncio.sleep(SLEEP_IDLE_SEC)
        return

    task_id, job = item["task_id"], item["job"]
    print(f"[worker] picked task={task_id} portal={item.get('portal')} title={item.get('title')} url={item.get('url')}")

    try:
        increment_attempts(task_id)
        update_task_status(task_id, "IN_PROGRESS")

        # 1) Tailor
        tailored = tailor(job, PROFILE)
        files = {}
        if tailored.get("resume_docx_path"): files["resume"] = tailored["resume_docx_path"]
        if tailored.get("cover_letter_path"): files["cover_letter"] = tailored["cover_letter_path"]

        # 2) Submit
        if FAKE:
            print("[worker] FAKE mode: skipping real submission, marking SUBMITTED")
            result = {"portal": job.get("portal") or job.get("source"), "submitted": True, "fake": True}
        else:
            result = await submit_real(job, files, PROFILE)

        # 3) Save artifacts + status
        set_artifacts(task_id, {"tailored": tailored, "submission": result})
        if result.get("submitted"):
            update_task_status(task_id, "SUBMITTED")
            update_task_status(task_id, "DONE")
        else:
            update_task_status(task_id, "FAILED", error="Submission did not confirm")

    except Exception as e:
        tb = traceback.format_exc()
        print(f"[worker] ERROR task={task_id}: {e}\n{tb}")
        # read attempts, then decide retry or fail
        from apply_db import _conn
        with _conn() as c:
            attempts = c.execute("SELECT attempts FROM tasks WHERE id=?", (task_id,)).fetchone()[0]
        if attempts >= MAX_RETRIES:
            update_task_status(task_id, "FAILED", error=str(e))
        else:
            update_task_status(task_id, "QUEUED", error=str(e))

async def main():
    init_apply()
    print(f"[worker] started with APPLY_DB_PATH={os.getenv('APPLY_DB_PATH')}, FAKE={FAKE}")
    while True:
        await process_one()

if __name__ == "__main__":
    asyncio.run(main())
