# Release Notes — AI Fleet Intelligence v2.1.0

## Implemented

This release completes the missing fleet contracts and hardens the supplied simulation. It adds strict Pydantic models for vehicles, drivers, and telemetry; an explainable three-signal violation engine for speed, fuel, and engine temperature; a PostgreSQL schema with uniqueness and review-state constraints; and a Telegram alert adapter that remains simulation-only and approval-gated.

It also adds a local Docker Compose environment with an internal network, a non-root backend container, dropped Linux capabilities, read-only application container, health-gated PostgreSQL startup, and no published database port. The dashboard and Arabic operating guide clearly identify the simulation boundary.

## Verification

The local test suite passes 7 tests. Python compilation and a static secret scan pass. Docker Compose build/runtime was not executed because Docker is unavailable in the validation environment. PostgreSQL runtime migrations were not executed for the same reason.

## Safety boundary

The project does not send Telegram messages, dispatch vehicles, issue vehicle commands, or make employment, disciplinary, safety, or maintenance decisions automatically. Any future live connector requires owner authorization, TLS, least-privilege credentials, consent, audit logging, staging validation, rate limits, kill switch, and an independently reviewed operational safety case.
