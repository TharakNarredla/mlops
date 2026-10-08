"""Gunicorn settings for the inference service.

Gunicorn is the process manager (starts/restarts workers); each worker runs our
FastAPI app through uvicorn's event loop.
"""
import os

bind = "0.0.0.0:8000"
worker_class = "uvicorn_worker.UvicornWorker"

# Number of worker processes. Set WEB_CONCURRENCY to match the CPUs you give the container.
workers = int(os.environ.get("WEB_CONCURRENCY", "2"))

# A worker silent for this long is killed and replaced.
timeout = 30
# On shutdown, let in-flight requests finish for this long (matches K8s SIGTERM handling).
graceful_timeout = 20
keepalive = 5

# Recycle workers periodically (with jitter so they don't all restart together).
max_requests = 10000
max_requests_jitter = 1000

# Log to stdout/stderr so `docker logs` and Kubernetes see them.
accesslog = "-"
errorlog = "-"
