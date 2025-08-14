# backend/skills_taxonomy.py
from __future__ import annotations
import re
from typing import Dict, List, Set

ROLE_KEYWORDS: Dict[str, Set[str]] = {
    "devops": {
        "devops","sre","platform","site reliability","infra","observability",
        "aws","gcp","azure","kubernetes","k8s","helm","terraform","pulumi",
        "ansible","packer","docker","container","eks","ec2","vpc",
        "ci","cd","github actions","gitlab ci","jenkins","argo","argo cd","flux",
        "prometheus","grafana","loki","otel","datadog","new relic","elk","splunk",
        "linux","bash","python","go","network","security","iam","vault"
    },
    "sales": {
        "sales","account executive","ae","quota","pipeline","crm","salesforce",
        "prospecting","enterprise","mid-market","smb","renewals","expansion",
        "baas","payments","fintech","saas","demo","discovery","closing","forecast"
    },
    "data": {
        "data","ml","machine learning","ai","nlp","llm","analytics",
        "python","pandas","spark","sql","dbt","warehouse","snowflake","bigquery",
        "airflow","orchestration","feature store","model","training","inference"
    },
    "backend": {
        "backend","server","api","microservices","grpc","rest","python","go","java",
        "kafka","redis","postgres","mysql","nosql","kubernetes","docker","ci","cd","aws"
    },
}

def detect_role(title: str, jd: str, explicit_role: str|None=None) -> str:
    if explicit_role:
        return explicit_role.lower().strip()
    text = f"{title} {jd}".lower()
    best_role, best_hits = "general", 0
    for role, kws in ROLE_KEYWORDS.items():
        hits = sum(1 for kw in kws if kw in text)
        if hits > best_hits:
            best_hits = hits
            best_role = role
    return best_role
