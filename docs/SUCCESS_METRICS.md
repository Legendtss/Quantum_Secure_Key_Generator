# Production Success Metrics

## Reliability
- Uptime target: 99.5%
- Error rate target: < 1%
- Alert when error rate > 5%

## Performance
- Average API response target: < 500ms
- p99 response target: < 2s
- Alert when avg response > 5s

## ML Quality
- Accuracy target: > 85%
- Alert threshold: < 75%
- Entropy gain target: > 2%
- ML correction adoption target: > 50%

## Capacity
- Storage warning: > 85%
- Storage critical: > 95%

## Operational Tracking
- Source endpoints:
  - `/api/admin/system-health`
  - `/api/admin/performance-metrics`
  - `/api/ml/improvement-summary`
  - `/api/ml/correction-stats`
