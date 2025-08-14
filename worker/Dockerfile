# Use Playwright's official image with browsers preinstalled
FROM mcr.microsoft.com/playwright/python:v1.45.0-jammy

WORKDIR /app
ENV PYTHONPATH=/app

# Python deps for your worker
COPY worker/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Your code
COPY backend /app/backend
COPY backend/apply_db.py /app/apply_db.py
COPY worker /app/worker

# Start the new worker loop
CMD ["python", "-u", "backend/apply_worker.py"]
