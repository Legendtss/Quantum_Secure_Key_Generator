# Operations Runbook

## Emergency: Service Down
1. Check `/api/health`.
2. Check `/api/admin/system-health`.
3. Inspect `backend/logs/production.log` for latest errors.
4. Restart service and validate key endpoints.
5. If still down, rollback to last known good release.

## High Error Rate
1. Open `/api/admin/performance-metrics`.
2. Identify endpoint with elevated errors.
3. Inspect logs and traceback details.
4. Apply fix or disable unstable feature path.
5. Re-check metrics after deployment.

## ML Degradation
1. Check `/api/ml/status` and metadata accuracy.
2. Retrain model via `/api/ml/train` if needed.
3. Validate `/api/ml/improvement-summary` and A/B deltas.

## Storage Pressure
1. Check storage usage from `/api/admin/system-health`.
2. Run archive script: `python backend/scripts/archive_old_data.py`.
3. Confirm free space increased and logs still writable.

## Routine Cadence
- Daily: health + performance snapshot.
- Weekly: error trend + alert threshold review.
- Monthly: dependency updates and backup restore test.
- Quarterly: incident drill and docs refresh.
