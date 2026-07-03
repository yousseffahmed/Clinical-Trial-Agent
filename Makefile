PYTHON ?= python
VENV ?= venv
PIP := $(VENV)/bin/pip
PYTEST := $(VENV)/bin/pytest
UVICORN := $(VENV)/bin/uvicorn

.PHONY: install test run ingest docker-build docker-run clean

install:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install -r requirements.txt

test:
	$(PYTEST) -q

run:
	$(UVICORN) app.main:app --reload --port 8000

ingest:
	curl -s -X POST http://localhost:8000/ingest

docker-build:
	docker build -t clinical-trial-agent .

docker-run:
	docker run --rm -p 8000:8000 --env-file .env clinical-trial-agent

clean:
	$(PYTHON) scripts/clean_submission.py
