
import requests
from typing import List, Dict, Any
from datetime import datetime

URL = "https://api.lever.co/v0/postings/{company}?mode=json"

def fetch_lever_jobs(company: str, roles: List[str], locations: List[str]) -> List[Dict[str, Any]]:
    url = URL.format(company=company)
    r = requests.get(url, timeout=20)
    if r.status_code != 200:
        return []
    data = r.json()
    out = []
    for j in data:
        title = j.get("text","")
        loc = j.get("categories",{}).get("location","") or ""
        role_ok = True if not roles else any(k.lower() in title.lower() for k in roles)
        loc_ok = True if not locations else any(k.lower() in loc.lower() for k in locations)
        if not (role_ok and loc_ok):
            continue
        jd = j.get("descriptionPlain","") or j.get("description","") or ""
        out.append({
            "id": f"lever-{company}-{j.get('id')}",
            "title": title,
            "company": company,
            "location": loc or "—",
            "source": "Lever",
            "url": j.get("hostedUrl") or j.get("applyUrl") or "",
            "jd_text": jd[:800],
            "created_at": j.get("createdAt") or datetime.utcnow().isoformat(),
        })
    return out
