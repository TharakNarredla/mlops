.PHONY: venv install test lint fmt train run docker-build docker-scan docker-run clean

PY := $(shell command -v python3.12 || command -v python3.11 || command -v python3)

venv:
	$(PY) -m venv .venv

install:
	.venv/bin/pip install -q --upgrade pip
	.venv/bin/pip install -q -r requirements-dev.txt

test:
	.venv/bin/pytest -q

lint:
	.venv/bin/ruff check .

fmt:
	.venv/bin/ruff check --fix .

train:
	.venv/bin/python src/train.py

run:
	.venv/bin/uvicorn src.serve.app:app --host 0.0.0.0 --port 8000

docker-build:
	docker build -t mlops-inference .

docker-scan:
	docker run --rm -v /var/run/docker.sock:/var/run/docker.sock -v trivy-cache:/root/.cache aquasec/trivy:latest image --severity HIGH,CRITICAL --ignore-unfixed --exit-code 1 mlops-inference:latest

docker-run:
	docker run --rm -p 8000:8000 -v $(CURDIR)/models:/app/models -v $(CURDIR)/experiments:/app/experiments mlops-inference

clean:
	rm -rf .venv .pytest_cache .ruff_cache
	find . -name "__pycache__" -not -path "./.venv/*" -exec rm -rf {} +
