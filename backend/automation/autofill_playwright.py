# backend/automation/autofill_playwright.py
import os, json, asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from playwright.async_api import async_playwright, Page, Browser

DATA_DIR = Path("data")
DATA_DIR.mkdir(parents=True, exist_ok=True)

def _now(): return datetime.utcnow().isoformat()+"Z"

async def run_draft(pw, job: Dict[str,Any]) -> Dict[str,Any]:
    """Your existing draft: open page, take screenshot + DOM."""
    browser = await pw.chromium.launch(headless=True)
    ctx = await browser.new_context()
    page = await ctx.new_page()
    await page.goto(job["url"], wait_until="domcontentloaded", timeout=60000)

    appid = job.get("id") or f"{int(datetime.utcnow().timestamp())}"
    out_dir = DATA_DIR / "drafts" / str(appid)
    out_dir.mkdir(parents=True, exist_ok=True)

    shot = out_dir / "screenshot.png"
    dom  = out_dir / "dom.html"
    await page.screenshot(path=str(shot), full_page=True)
    await Path(dom).write_text(await page.content(), encoding="utf-8")

    await ctx.close(); await browser.close()
    return {
        "id": str(appid),
        "status": "DRAFTED",
        "screenshot_path": str(shot),
        "snapshot_path": str(dom),
    }

# ---------------- REAL SUBMISSION ----------------

async def _upload_if_visible(page: Page, selector: str, filepath: str):
    try:
        input_ = await page.wait_for_selector(selector, timeout=2500)
        await input_.set_input_files(filepath)
        return True
    except Exception:
        return False

async def _fill_if_visible(page: Page, selector: str, value: str):
    try:
        el = await page.wait_for_selector(selector, timeout=2000)
        await el.fill(value)
        return True
    except Exception:
        return False

async def submit_greenhouse(page: Page, job: Dict[str,Any], files: Dict[str,str], profile: Dict[str,Any]) -> Dict[str,Any]:
    # common Greenhouse patterns
    # 1) Click apply
    for sel in ["a[href*='applications/new']", "a[href*='apply']", "button:has-text('Apply')"]:
        try:
            el = await page.wait_for_selector(sel, timeout=3000)
            await el.click()
            break
        except Exception:
            pass

    # 2) Upload résumé/CL
    if files.get("resume"):
        await _upload_if_visible(page, "input[type='file'][name*='resume']", files["resume"])
        await _upload_if_visible(page, "input[type='file'][id*='resume']", files["resume"])
    if files.get("cover_letter"):
        await _upload_if_visible(page, "input[type='file'][name*='cover']", files["cover_letter"])

    # 3) Basic fields
    p = profile or {}
    await _fill_if_visible(page, "input[name*='first_name']", p.get("first_name",""))
    await _fill_if_visible(page, "input[name*='last_name']",  p.get("last_name",""))
    await _fill_if_visible(page, "input[type='email']",       p.get("email",""))
    await _fill_if_visible(page, "input[type='tel']",         p.get("phone",""))
    await _fill_if_visible(page, "input[name*='linkedin']",   p.get("linkedin",""))

    # 4) Submit
    for sel in ["button[type='submit']", "button:has-text('Submit')", "input[type='submit']"]:
        try:
            b = await page.wait_for_selector(sel, timeout=3000)
            await b.click()
            break
        except Exception:
            pass

    # 5) Success heuristic
    success_texts = ["Thank you", "Application submitted", "We received your application"]
    html = (await page.content()).lower()
    ok = any(t.lower() in html for t in success_texts)
    return {"portal":"greenhouse","submitted":ok}

async def submit_lever(page: Page, job: Dict[str,Any], files: Dict[str,str], profile: Dict[str,Any]) -> Dict[str,Any]:
    # 1) Click apply
    for sel in ["a[href*='apply']", "button:has-text('Apply')"]:
        try:
            el = await page.wait_for_selector(sel, timeout=3000)
            await el.click()
            break
        except Exception:
            pass

    # 2) Upload résumé / CL
    if files.get("resume"):
        await _upload_if_visible(page, "input[type='file'][name*='resume']", files["resume"])
        await _upload_if_visible(page, "input[type='file'][id*='resume']", files["resume"])
    if files.get("cover_letter"):
        await _upload_if_visible(page, "input[type='file'][name*='cover']", files["cover_letter"])

    # 3) Basics
    p = profile or {}
    for sel,val in [
        ("input[name='name']", f"{p.get('first_name','')} {p.get('last_name','')}".strip()),
        ("input[type='email']", p.get("email","")),
        ("input[type='tel']",   p.get("phone","")),
        ("input[name*='linkedin']", p.get("linkedin","")),
    ]:
        if val: await _fill_if_visible(page, sel, val)

    # 4) Submit
    for sel in ["button[type='submit']", "button:has-text('Submit')", "input[type='submit']"]:
        try:
            b = await page.wait_for_selector(sel, timeout=3000)
            await b.click(); break
        except Exception: pass

    html = (await page.content()).lower()
    ok = any(t in html for t in ["thank you","we received your application","application submitted"])
    return {"portal":"lever","submitted":ok}

async def submit_for_job(pw, job: Dict[str,Any], files: Dict[str,str], profile: Dict[str,Any]) -> Dict[str,Any]:
    """Open job URL and submit on known portals. Returns artifacts."""
    browser = await pw.chromium.launch(headless=True)
    ctx = await browser.new_context()
    page = await ctx.new_page()
    await page.goto(job["url"], wait_until="domcontentloaded", timeout=90000)

    # choose submitter
    portal = (job.get("portal") or job.get("source") or "").lower()
    if not portal:
        url = job.get("url","").lower()
        portal = "greenhouse" if "greenhouse.io" in url else "lever" if "lever.co" in url else "other"

    result = {"portal": portal, "submitted": False}

    if portal == "greenhouse":
        result = await submit_greenhouse(page, job, files, profile)
    elif portal == "lever":
        result = await submit_lever(page, job, files, profile)
    else:
        # fallback: just take a screenshot as artifact
        pass

    # save artifacts
    appid = job.get("id") or f"{int(datetime.utcnow().timestamp())}"
    out_dir = DATA_DIR / "applications" / str(appid)
    out_dir.mkdir(parents=True, exist_ok=True)
    shot = out_dir / "after-submit.png"
    await page.screenshot(path=str(shot), full_page=True)

    await ctx.close(); await browser.close()
    return {**result, "screenshot_path": str(shot), "submitted_at": _now()}
