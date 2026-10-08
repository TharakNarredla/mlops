# Docker Setup

The inference service has one production Dockerfile, plus a small overlay for local minikube demos.

---

## Dockerfile (main image)

- **Multi-stage:** stage 1 installs dependencies into a virtualenv; stage 2 copies only that venv and `src/` onto a fresh `python:3.12-slim`. Build tools and pip cache never ship.
- **Non-root:** the app runs as `appuser` (uid 10001), not root.
- **Models are not baked in:** `models/` and `experiments/` are mounted at runtime, so one image serves any model version.
- **Healthcheck:** Docker polls `/health`.

**Build and run:**
```bash
make docker-build
make train          # generate a model to mount
make docker-run     # serves on http://127.0.0.1:8000
```

---

## Image size and security scanning

- `requirements.txt` holds **serving dependencies only**; `pandas` and `mlflow` live in `requirements-train.txt`, and test/lint tools in `requirements-dev.txt`. The image installs only the first file.
- Result: **1.3 GB -> ~600 MB**, and fixable HIGH/CRITICAL CVEs **24 -> 0** (almost all were in `mlflow`, which the API never used).
- `make docker-scan` runs Trivy locally; CI runs the same scan in the `docker-scan` job and fails the build on any fixable HIGH/CRITICAL finding.

---

## Workers (Gunicorn + uvicorn)

The container starts **Gunicorn**, which runs N worker processes; each worker runs the FastAPI app on uvicorn's event loop. One worker uses one CPU core, so N workers use N cores. Gunicorn also replaces workers that crash, hang (`timeout`), or hit `max_requests`.

Set the count with `WEB_CONCURRENCY` (default 2; see `gunicorn.conf.py`):
```bash
docker run -e WEB_CONCURRENCY=2 --cpus=2 ...
```

**Rule of thumb: workers ~= CPUs given to the container.** Measured with `ab -n 6000 -c 50` against a `--cpus=2` container (single run, same machine, so indicative only):

| Workers | req/s | p95 |
|---|---|---|
| 1 | ~2,560 | 23 ms |
| 2 | ~4,150 | 18 ms |
| 4 | ~2,730 | 64 ms |

More workers than CPUs makes tail latency worse. In Kubernetes the usual pattern is a small worker count per Pod (match the Pod's CPU limit) and scale out with more Pods via the HPA.

**Known limitation:** `/metrics` counters are per worker, so with >1 worker the endpoint shows only the answering worker's numbers. Fixed properly with Prometheus multiprocess metrics (Day 46).

**Dependency note:** `mlflow 2.17.2` requires `gunicorn<24`, so gunicorn is pinned to 23.x; `uvicorn-worker` needs `uvicorn>=0.36`.

---

## Dockerfile.k8s-local (minikube only)

A 3-line overlay on the main image that bakes `models/` and `experiments/` in, so a Pod is self-contained without a volume mount. Uses its own `Dockerfile.k8s-local.dockerignore`.

```bash
make train
make docker-build
docker build -t mlops-inference:latest -f Dockerfile.k8s-local .
```

---

## Key Concepts

| Term | Meaning |
|------|---------|
| **Image** | Snapshot: OS + Python + code + dependencies. Built once. |
| **Container** | Running instance of an image. |
| **Volume mount** | Map a host folder into the container at runtime (e.g. `models/`). |
