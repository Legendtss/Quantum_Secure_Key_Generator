"""Simple post-deploy smoke test for core endpoints."""

import json
from urllib import request as urlrequest


BASE_URL = 'http://localhost:5000'
ENDPOINTS = [
    '/api/health',
    '/api/ml/status',
    '/api/admin/system-health',
    '/api/admin/performance-metrics',
]


def fetch(path):
    with urlrequest.urlopen(f'{BASE_URL}{path}', timeout=10) as resp:
        data = resp.read().decode('utf-8')
        return resp.status, json.loads(data)


def main():
    for ep in ENDPOINTS:
        status, body = fetch(ep)
        print(ep, status, body.get('success', body.get('status')))


if __name__ == '__main__':
    main()
