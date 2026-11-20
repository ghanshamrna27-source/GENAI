# Dockerfile for GitGuru API and Streamlit UI
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    GITGURU_API_URL=http://api:8000

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY analysis/ ./analysis/
COPY app/ ./app/
COPY data/ ./data/
COPY docs/ ./docs/
COPY eval/ ./eval/
COPY prompts/ ./prompts/
COPY ui/ ./ui/
COPY tests/ ./tests/
COPY pyproject.toml README.md .

# Expose ports for FastAPI (8000) and Streamlit (8501)
EXPOSE 8000
EXPOSE 8501

# Default command starts FastAPI API service
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
