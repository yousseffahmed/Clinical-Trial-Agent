# Final submission checklist

## Submit

- [ ] `app/` — all Python source files, including `mcp_server.py`
- [ ] `data/` — all three synthetic `.txt` documents
- [ ] `docs/` — architecture, demo, presentation, speaker notes, and Q&A
- [ ] `tests/` — all pytest files
- [ ] `memory/.gitkeep`
- [ ] `vector_store/.gitkeep`
- [ ] `.env` — with `OPENAI_API_KEY=` blank
- [ ] `.env.example`
- [ ] `.gitignore` and `.dockerignore`
- [ ] `README.md`
- [ ] `requirements.txt` and `pytest.ini`
- [ ] `Dockerfile` and `docker-compose.yml`
- [ ] `Makefile`
- [ ] `scripts/clean_submission.py`
- [ ] `SUBMISSION_CHECKLIST.md`

## Exclude

- [ ] No `venv/` or `.venv/`
- [ ] No `__pycache__/` or `*.pyc`
- [ ] No `.pytest_cache/`
- [ ] No `memory/*.db`
- [ ] No generated files under `vector_store/` except `.gitkeep`
- [ ] No real API keys, tokens, passwords, or confidential study documents
- [ ] No `.DS_Store`
- [ ] No ZIP, RAR, TAR, or other compressed archive
- [ ] No local absolute paths or personal usernames in documentation

## Final verification commands

```bash
python scripts/clean_submission.py
python -m venv /tmp/clinical-trial-agent-verify
source /tmp/clinical-trial-agent-verify/bin/activate
pip install -r requirements.txt
pytest -q
uvicorn app.main:app --port 8000
```

In another terminal:

```bash
curl -s -X POST http://localhost:8000/ingest
curl -s http://localhost:8000/health
curl -s http://localhost:8000/tools
```

Docker:

```bash
docker build -t clinical-trial-agent .
docker run --rm -p 8000:8000 --env-file .env clinical-trial-agent
```

## Classroom reminders

- [ ] Upload the project as individual required files/folders, not a compressed
      archive.
- [ ] Do **not** upload the presentation slides to Google Classroom if the
      assignment instructions prohibit slide upload; use the three-slide
      outline and speaker notes for the live presentation.
- [ ] Open `.env` immediately before submission and confirm the API key remains
      blank.
