# Secure App (Baseline)

This project demonstrates a production-grade Linux service with:

- Non-root execution
- Externalized secrets
- systemd lifecycle management
- Hot reload (SIGHUP)
- Graceful shutdown
- HTTP health endpoint

## Notes

This repository intentionally contains **no secrets**.
Secrets are injected at runtime via systemd.
