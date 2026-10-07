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
