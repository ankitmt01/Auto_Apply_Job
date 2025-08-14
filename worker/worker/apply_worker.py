import asyncio
import os
import traceback
from playwright.async_api import async_playwright
from apply_db import dequeue_next, update_task_status, increment_attempts

RESUME_PATH = os.getenv("RESUME_PATH", "/data/resume.pdf")
COVER_LETTER_PATH = os.getenv("COVER_LETTER_PATH", "/data/cover_letter.pdf")

async def apply_greenhouse(job):
    """Example: apply to a Greenhouse job"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        print(f"Opening job URL: {job['url']}")
        await page.goto(job["url"])

        # Example: Click "Apply" button
        await page.click("text=Apply")

        # Fill form fields (selectors will depend on the portal form)
        await page.fill('input[name="first_name"]', os.getenv("APPLICANT_FIRST_NAME", "John"))
        await page.fill('input[name="last_name"]', os.getenv("APPLICANT_LAST_NAME", "Doe"))
        await page.fill('input[name="email"]', os.getenv("APPLICANT_EMAIL", "john@example.com"))
        await page.fill('input[name="phone"]', os.getenv("APPLICANT_PHONE", "1234567890"))

        # Upload resume
        await page.set_input_files('input[type="file"]', RESUME_PATH)

        # Upload cover letter (if required)
        if await page.query_selector('input[name*="cover_letter"]'):
            await page.set_input_files('input[name*="cover_letter"]', COVER_LETTER_PATH)

        # Submit
        await page.click('button[type="submit"]')
        await browser.close()

async def process_task():
    task = dequeue_next()
    if not task:
        print("No queued tasks. Sleeping...")
        return

    task_id = task["task_id"]
    job = task["job"]
    print(f"Processing task {task_id} for job {job['title']} at {job['company']}")

    increment_attempts(task_id)
    try:
        if job.get("portal") == "greenhouse":
            await apply_greenhouse(job)
        else:
            raise NotImplementedError(f"Portal {job.get('portal')} not supported yet")

        update_task_status(task_id, "DONE")
        print(f"✅ Task {task_id} completed")
    except Exception as e:
        traceback.print_exc()
        update_task_status(task_id, "FAILED", error=str(e))
        print(f"❌ Task {task_id} failed: {e}")

async def main_loop():
    while True:
        await process_task()
        await asyncio.sleep(5)  # Check for new jobs every 5 seconds

if __name__ == "__main__":
    asyncio.run(main_loop())
