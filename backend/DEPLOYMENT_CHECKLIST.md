# Production Deployment Checklist

## Pre-Deployment (1 Week Before)

### Code Quality
- [ ] All tests pass: `pytest backend/test_*.py`
- [ ] No console errors or warnings
- [ ] Security dependency scan completed: `pip audit`
- [ ] Code reviewed
- [ ] Git history clean and documented

### Configuration
- [ ] Environment variables set (`FLASK_ENV`, `DEBUG`, `LOG_LEVEL`)
- [ ] Backups enabled for `backend/data/` and `backend/models/`
- [ ] CORS restricted to production domains
- [ ] API rate limiting configured
- [ ] Admin endpoints protected (IP allowlist or auth)

### Performance
- [ ] Load test completed and baseline recorded
- [ ] Frontend build optimized
- [ ] Logging volume validated under load
- [ ] Timeout and retry strategy verified
- [ ] Resource limits validated (CPU/RAM/storage)

### Security
- [ ] HTTPS/SSL active and auto-renew configured
- [ ] Secrets removed from repository and moved to env
- [ ] Input validation verified on all write endpoints
- [ ] Sensitive payloads excluded from logs
- [ ] Incident response contacts documented

### Infrastructure
- [ ] Uptime monitor configured
- [ ] Log retention and rotation policy configured
- [ ] Backup restore tested
- [ ] Monitoring alerts configured
- [ ] DNS and deploy target validated

### Documentation
- [ ] User guide published
- [ ] Developer guide updated
- [ ] Runbook tested by teammate
- [ ] Deployment runbook approved

---

## Deployment Day

### Pre-Deploy
- [ ] Backup data and model artifacts
- [ ] Notify stakeholders
- [ ] Confirm rollback target

### Steps
1. Build frontend: `cd frontend && npm run build`
2. Run backend sanity checks
3. Deploy backend
4. Deploy frontend assets
5. Validate `/api/health` and `/api/admin/system-health`
6. Validate ML endpoints (`/api/ml/*`)
7. Review logs and error rates for 15 minutes

### Post-Deploy
- [ ] Validate key user journeys
- [ ] Confirm no alert spikes
- [ ] Mark deployment complete and log outcome

---

## First Week Post-Deploy
- [ ] Monitor hourly for error-rate anomalies
- [ ] Confirm entropy improvement remains stable
- [ ] Capture user feedback and triage bugs
- [ ] Record baseline metrics for future regression checks

---

## Ongoing Operations
- [ ] Daily health checks
- [ ] Weekly log and error review
- [ ] Monthly security patch cycle
- [ ] Quarterly disaster recovery drill
