# Inference service image (FastAPI + uvicorn).
# Build: docker build -t mlops-inference .
# Run:   docker run -p 8000:8000 -v $(pwd)/models:/app/models -v $(pwd)/experiments:/app/experiments mlops-inference
# Models are NOT baked in: mount models/ and experiments/ at runtime so one image serves any model.

# ---- Stage 1: builder (discarded after build) ----
FROM python:3.12-slim AS builder

ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /build

# Install dependencies into an isolated virtualenv we can copy as one folder
RUN python -m venv /venv
ENV PATH="/venv/bin:$PATH"
COPY requirements.txt .
RUN pip install -r requirements.txt

# ---- Stage 2: runtime (this is what ships) ----
FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PATH="/venv/bin:$PATH"

# Non-root user: if the app is compromised, the attacker is not root
RUN useradd --create-home --uid 10001 appuser

WORKDIR /app
COPY --from=builder /venv /venv
COPY src/ ./src/
COPY gunicorn.conf.py .

# Mount points for models/experiments, writable by the app user
RUN mkdir -p models experiments && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"

# WEB_CONCURRENCY sets the worker count (default 2); see gunicorn.conf.py
CMD ["gunicorn", "-c", "gunicorn.conf.py", "src.serve.app:app"]
