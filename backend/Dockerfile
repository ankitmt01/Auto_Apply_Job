FROM python:3.11-slim

# System deps (kept light)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Workdir where main.py lives
WORKDIR /app/backend
#ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

# ---- Dependencies (cache-friendly) ----
COPY backend/requirements.txt /app/backend/
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Playwright + Chromium for /applications/draft endpoint
# RUN pip install --no-cache-dir playwright && \
#     python -m playwright install --with-deps chromium

# ---- App code ----
# Copy full backend first
COPY backend /app/backend
# Ensure templates are present even if the host mount is missing
# (redundant if backend/templates exists in the previous COPY, but harmless)
COPY backend/templates /app/backend/templates

# Data dir for generated files
RUN mkdir -p /app/data

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
