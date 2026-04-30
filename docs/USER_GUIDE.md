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

## ❤️ Support This Project (Optional)

👨‍💻 About the Developer

Hi, I’m Shashank TS, an AI/ML student focused on building systems at the intersection of quantum computing, machine learning, and cybersecurity.

This project explores how quantum randomness + ML optimization can be used to generate stronger cryptographic keys for real-world security applications.

🚀 What Drives This Project

I’ve always been curious about how theoretical concepts like quantum mechanics can be applied in practical systems.

This project is my attempt to:

- Bridge quantum theory → real-world engineering
- Experiment with next-generation security systems
- Build something that is both technically deep and practically usable

🔗 Connect With Me

- LinkedIn: https://www.linkedin.com/in/shashankts2004/
- GitHub: https://github.com/Legendtss
- Portfolio: https://legendtss.github.io/Portfolio/
- Email: shashankts2026@gmail.com

❤️ Support This Project (Optional)

If you found this project interesting or useful, you can support its development. Your support helps me:

- Improve and scale the system
- Explore more advanced quantum + ML applications
- Continue building open technical projects

(Optional — no obligation at all)

[![UPI QR Code](../frontend/src/assets/upi-qr-code.jpg)](upi://pay?pa=shashankts2004%40oksbi&pn=Shashank%20T%20S&tn=Support%20Quantum%20Key%20Generator)

UPI ID: `shashankts2004@oksbi` — [Pay via UPI](upi://pay?pa=shashankts2004%40oksbi&pn=Shashank%20T%20S&tn=Support%20Quantum%20Key%20Generator)
