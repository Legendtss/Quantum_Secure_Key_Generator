# Developer Guide - ML Integration

## Architecture
Frontend (React) -> Flask API -> Quantum generator + ML classifier + CSV logs/models

Core paths:
- `backend/app.py`
- `backend/ml_model_trainer.py`
- `backend/ml_error_corrector.py`
- `backend/monitoring_setup.py`
- `backend/error_handler.py`
- `frontend/src/components/*`

## Local Development
1. Backend: `cd backend && python app.py`
2. Frontend: `cd frontend && npm start`
3. Build frontend: `cd frontend && npm run build`

## Testing
- Backend tests: `pytest backend/test_*.py -v`
- Frontend build sanity: `cd frontend && npm run build`
- Python compile sanity: `python -m py_compile backend/*.py`

## Deployment Flow
1. Validate tests/build.
2. Backup `backend/data/` and `backend/models/`.
3. Deploy backend and frontend.
4. Verify health:
   - `/api/health`
   - `/api/admin/system-health`
   - `/api/admin/performance-metrics`
5. Monitor logs and alert thresholds.

## Monitoring
- Structured logs: `backend/logs/production.log`
- Alerts log: `backend/logs/alerts.log`
- In-memory metrics endpoint: `/api/admin/performance-metrics`

## Data Operations
- Training data: `backend/data/training_data.csv`
- A/B log: `backend/data/ab_test_log.csv`
- Model artifacts: `backend/models/*.pkl`, `model_metadata.json`

## Maintenance
- Archive oversized CSVs regularly.
- Retrain when model metrics degrade.
- Keep dependencies patched.
- Review error spikes and outliers weekly.
