# ShopMind AI — Pre-Commit File Audit Report

Date: 2026-06-14  
Scope: Entire repository, production/public GitHub release readiness

## Classification Summary

- **KEEP**: runtime source, configuration templates, essential docs, reproducibility scripts
- **REMOVE**: generated artifacts, temporary diagnostics, build outputs, test result dumps
- **IGNORE**: local secrets, environments, caches, dependency trees, generated indexes
- **ARCHIVE**: legacy/deprecated design docs and one-off historical reports not needed for runtime

## KEEP (core release files)

- `backend/main_api.py`
- `backend/scheduler.py`
- `backend/services/**`
- `backend/phase3_5_integration.py` (used by `/analyze-reviews` endpoint)
- `frontend/src/**`
- `frontend/index.html`
- `frontend/package.json`
- `frontend/package-lock.json`
- `frontend/vite.config.ts`
- `frontend/tsconfig.json`
- `frontend/tsconfig.node.json`
- `frontend/eslint.config.js`
- `requirements.txt`
- `.gitignore`
- `README.md` (to be regenerated)
- `LICENSE`
- `.env.example`
- `backend/.env.example`
- `backend/.env.production.example`
- `frontend/.env.local.example`
- `frontend/.env.production.example`
- `data/amazon.csv` (small enough to include)
- `data/ingest_and_embed.py`

## REMOVE (from release branch)

- Generated build output: `frontend/dist/**`
- Python cache folders/files: `**/__pycache__/**`, `*.pyc`
- One-off temporary audit scripts:
  - `_auth_audit.py`
  - `_dashboard_me_audit.py`
  - `_production_api_audit.py`
  - `backend/_final_audit_api.py`
  - `backend/_retrieval_probe.py`
- Generated test/audit result files:
  - `integration_test_results.json`
  - `TEST_RESULTS.json`
  - `PRODUCTION_AUDIT_REPORT.json`

## IGNORE (via .gitignore; keep local only)

- `.env`, `.env.local`, `.env.production`, `.env.development`
- `backend/.env`, `frontend/.env.local`
- `node_modules/`, `.venv/`, `venv/`, `env/`
- `dist/`, `build/`, `coverage/`, `.pytest_cache/`, `.cache/`
- `*.log`, `*.tmp`, `*.bak`, `*.sqlite`, `*.db`
- `.vscode/`, `.idea/`, `.DS_Store`, `Thumbs.db`
- FAISS/index artifacts to regenerate: `*.idx`, `*id_map*.pkl`

## ARCHIVE (move to docs/archive)

- Historical audit and status reports not needed for runtime:
  - `AUDIT_EXECUTIVE_SUMMARY.md`
  - `AUDIT_MANIFEST.md`
  - `AUDIT_REPORT.html`
  - `AUTHENTICATION_IMPLEMENTATION_PLAN.md`
  - `FINAL_PRODUCTION_READINESS_REPORT.md`
  - `FRONTEND_SETUP.md`
  - `IMPLEMENTATION_STATUS.md`
  - `MONGODB_CHECK_SUMMARY.txt`
  - `MONGODB_CONNECTIVITY_CONFIGURED.md`
  - `MVP_SUMMARY.md`
  - `PRODUCTION_AUDIT_REPORT.md`
  - `PRODUCTION_DASHBOARD.md`
  - `PROJECT_SUMMARY.md`
  - `README_COMPLETE.md`
- Legacy/deprecated backend modules not needed by current app runtime:
  - `backend/retrieval_api.py`
  - `backend/rag_copilot.py`
  - `backend/recommender.py`
  - `backend/review_intelligence.py`
  - `backend/phase6_mongodb_design.py`
  - `backend/mongodb_schema.py`

## Security Findings (pre-cleanup)

- Sensitive values were previously present in `backend/.env` and Mongo test helpers.
- Action taken in this release workflow:
  - replaced committed secrets with placeholders
  - moved auth for Gemini API key to header-based request (no query-string key)
  - updated Mongo test helpers to use env-based URI placeholders

## Next Actions

1. Apply cleanup (remove/archive artifacts and legacy files).
2. Regenerate release-grade `README.md`, `.gitignore`, `datasets/README.md`, and `scripts/build_faiss.py`.
3. Re-run build/startup verification and generate final GitHub release report.
