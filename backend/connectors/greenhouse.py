
import requests
from typing import List, Dict, Any
from datetime import datetime

API = "https://boards-api.greenhouse.io/v1/boards/{token}/jobs"

def _strip_html(html: str) -> str:
    import re
    text = re.sub(r"<[^>]+>", " ", html or "")
    text = re.sub(r"\s+", " ", text).strip()
    return text[:800]

def fetch_greenhouse_jobs(board_token: str, roles: List[str], locations: List[str]) -> List[Dict[str, Any]]:
    url = API.format(token=board_token)
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    data = r.json().get("jobs", [])
    out = []
    for j in data:
        title = j.get("title","")
        offices = [o.get("name","") for o in j.get("offices",[])]
        loc_ok = True if not locations else any(any(loc.lower() in off.lower() for off in offices) for loc in locations)
        role_ok = True if not roles else any(rk.lower() in title.lower() for rk in roles)
        if not (loc_ok and role_ok):
            continue
        gh_url = j.get("absolute_url") or j.get("url") or ""
        jd = j.get("content","") or ""
        created = j.get("updated_at") or j.get("created_at") or datetime.utcnow().isoformat()
        location = offices[0] if offices else (j.get("location",{}) or {}).get("name","")
        out.append({
            "id": f"gh-{board_token}-{j.get('id')}",
            "title": title,
            "company": board_token,
            "location": location or "—",
            "source": "Greenhouse",
            "url": gh_url,
            "jd_text": _strip_html(jd),
            "created_at": created,
        })
    return out
