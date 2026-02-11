FROM python:3.12-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code
COPY backend/ .

# Ensure start.sh is executable & has Unix line endings
RUN chmod +x /app/start.sh && \
    sed -i 's/\r$//' /app/start.sh

# Railway assigns PORT dynamically; default 8000 for local dev
ENV PORT=8000
EXPOSE ${PORT}

# Always run start.sh (migrations + uvicorn) — not bare uvicorn
CMD ["/app/start.sh"]
