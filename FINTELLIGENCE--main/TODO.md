# TODO - FINTELLIGENCE M4 (Backend additive + Frontend full app)

## Backend (additive)
- [x] Create new DB models + Alembic migrations (additive-only):
  - registration_requests
  - case_escalations

- [x] Add `POST /api/auth/register-request` (store pending request only)


- [x] Add `GET /api/auth/pending-registrations` (admin-only)

- [x] Add `POST /api/auth/approve-registration/<id>` (admin-only; creates user)
- [x] Add `scripts/seed_admin.py` to seed demo admin user

- [x] Add escalation workflow routes (new file `app/routes/escalation.py`):
  - `POST /api/cases/<case_id>/escalate` (investigator-only)
  - `GET /api/escalations` (supervisor-only)
  - `POST /api/escalations/<id>` (supervisor review: close / recommend FIR)
- [x] Add dashboard aggregate endpoint (new file `app/routes/dashboard.py`):
  - `GET /api/dashboard/overview`
- [x] Wire new route blueprints in `app/__init__.py` (ensure additive registration)

## Frontend (create missing structure)
- [x] Scaffold required frontend directories/files (pages/components/api/store/utils)
- [x] Implement authStore (token + user + role)
- [x] Implement Login/Register pages matching reference UI design
- [x] Implement AppLayout + Sidebar (role-gated Escalations)
- [x] Implement routing + role-based guards
- [x] Implement pages:
  - Dashboard
  - CaseList
  - CaseDetail (AI sections, detectors, notes, escalation)
  - Transactions
  - FraudAnalysis
  - FundFlow (fix graph component issues)
  - AIInvestigator
  - Reports
  - EvidenceLocker
- [x] Implement `frontend/src/api/*` clients mapping to Flask endpoints

## Final validation
- [ ] Run backend migrations and start server; verify existing endpoints
- [ ] Run frontend dev server; manually test flows
- [ ] Confirm: no files modified under restricted directories (`app/parsers`, `app/normalizer`, `app/graph`, `app/detectors`, `app/ai`)
