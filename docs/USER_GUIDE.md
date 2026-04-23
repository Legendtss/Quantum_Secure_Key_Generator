# Quantum Key Generator with ML - User Guide

## What You Can Do
- Generate 128/256/512-bit quantum keys
- Enable ML correction to retry low-quality generations automatically
- Compare baseline vs ML-improved outcomes in A/B analytics
- Track improvement and latency cost on the dashboard

## Quick Start
1. Open the app and choose **ML Generator**.
2. Select key length and shots.
3. Toggle **Enable ML quality correction**.
4. Generate key and review quality/confidence/attempts.
5. Use **ML Dashboard** and **AB Results** tabs for metrics.

## Understanding Quality
- `good`: ML predicts high-quality generation.
- `bad`: ML predicts lower-quality generation.
- `confidence`: model confidence for predicted label.
- `entropy gain %`: relative improvement from correction loop.

## Recommended Settings
- Key length: `256`
- Shots: `1024`
- Max attempts: `3`
- ML correction: `enabled` for security-priority workflows

## Troubleshooting
- Backend unreachable: verify `/api/health`.
- ML unavailable: check `/api/ml/status`, then train with `/api/ml/train`.
- Slow responses: lower shots and max attempts.
- Low quality persists: use correction and regenerate.

## Security Practices
- Never share keys in plain text channels.
- Rotate keys frequently.
- Prefer green/high-quality keys for critical encryption tasks.
- Do not reuse one-time keys for multiple payloads.

## Support
- Check `docs/RUNBOOK.md` for operator actions.
- Check `docs/DEVELOPER_GUIDE.md` for technical debugging steps.
