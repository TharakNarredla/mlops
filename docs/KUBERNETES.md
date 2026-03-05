# Kubernetes Deployment

Deploy the inference service to Kubernetes (minikube for local; same manifests for cloud).

---

## Prerequisites

- minikube installed and running: `minikube status` → Running
- kubectl: `kubectl get nodes` → one node Ready

---

## Build Image Inside Minikube

Minikube has its own Docker daemon. Build the image inside minikube so the cluster can use it.

```bash
eval $(minikube docker-env)
docker build -f Dockerfile.inference.k8s -t mlops-inference:latest .
```

---

## Deploy (raw manifests)

```bash
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/hpa.yaml
```

## Deploy (Helm)

```bash
helm install mlops-inference helm/mlops-inference
```

---

## Access the API

```bash
kubectl port-forward svc/mlops-inference 8000:8000
```

Then call `http://127.0.0.1:8000/predict` (see `docs/api.md`).

---

## Rollback

Edit the ConfigMap to set `MODEL_RUN_ID` to a different run, then:

```bash
kubectl rollout restart deployment/mlops-inference
```
