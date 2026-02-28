# Docker Setup

This project provides two Dockerfiles for the inference service.

---

## Dockerfile.inference (Local Development)

Uses volume mounts for `models/` and `experiments/` so you can train on the host and serve without rebuilding.

**Build:**
```bash
docker build -f Dockerfile.inference -t mlops-inference .
```

**Run:**
```bash
docker run -p 8000:8000 \
  -v $(pwd)/models:/app/models \
  -v $(pwd)/experiments:/app/experiments \
  mlops-inference
```

---

## Dockerfile.inference.k8s (Kubernetes)

Bakes `models/` and `experiments/` into the image. Used when deploying to Kubernetes (e.g. minikube) where volume mounts are not used.

**Build:**
```bash
# Train first to generate models/
python3 src/train.py

docker build -f Dockerfile.inference.k8s -t mlops-inference:latest .
```

---

## Key Concepts

| Term | Meaning |
|------|---------|
| **Image** | Snapshot: OS + Python + code + dependencies. Built once. |
| **Container** | Running instance of an image. |
| **Volume mount** | Map a host folder into the container at runtime (e.g. `models/`). |
