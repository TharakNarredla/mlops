# Helm Chart — MLOps Inference

Deploy the inference API to Kubernetes via Helm.

## Install

```bash
helm install mlops-inference ./mlops-inference -f ./mlops-inference/values.yaml
```

## Upgrade

```bash
helm upgrade mlops-inference ./mlops-inference -f ./mlops-inference/values.yaml
```

## Override image (EKS/ECR)

```bash
helm install mlops-inference ./mlops-inference \
  --set image.repository=123456789.dkr.ecr.eu-central-1.amazonaws.com/mlops-inference \
  --set image.tag=v1.0.0 \
  --set image.pullPolicy=Always
```

## Uninstall

```bash
helm uninstall mlops-inference
```
