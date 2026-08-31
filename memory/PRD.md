# PRD — Portal Corporativo Interno

## Problem Statement (original, verbatim)
> Quiero crear una aplicación que tenga login inicial y luego pueda acceder a diferentes aplicaciones segun privilegios de acceso.

## User choices (2026-02)
- Auth: JWT clásico (email + password)
- Aplicaciones internas: **formularios de toma de datos**
- Roles: **Admin, Editor, Usuario** (3 roles)
- Admin puede crear/gestionar usuarios y asignar accesos a las apps desde la UI
- Estilo visual: **Corporativo / profesional**

## Architecture
- **Backend**: FastAPI + Motor/MongoDB, JWT auth (HS256, 24h). bcrypt for passwords.
- **Frontend**: React 19 + React Router 7 + shadcn/ui + Phosphor Icons + Sonner toasts.
- **Auth flow**: `POST /api/auth/login` -> `{token, user}` -> token stored in localStorage under `portal_token`, sent as `Authorization: Bearer <token>` on every request. `GET /api/auth/me` re-hydrates session on reload.
- **RBAC**:
  - `admin`: full access to all apps + `/api/admin/*` user management.
  - `editor`: access to allowed apps, sees all submissions inside those apps.
  - `user`: access to allowed apps, sees only their own submissions.
- **Apps** are hard-coded in `server.py::APPS` (id, name, description, icon, accent, fields[]). 4 apps shipped: `clientes`, `incidentes`, `productos`, `empleados`.
- Submissions stored in `submissions` collection with `app_id`, `user_id`, `data`, `created_at`.

## What's been implemented (2026-02-XX — v1)
- Login page (Spanish) with split visual layout + test-account hint card
- Portal layout: fixed sidebar (Mis aplicaciones / Usuarios y accesos), top bar with user dropdown + logout
- Dashboard: role-scoped grid of app cards
- App form page: renders dynamic fields (text/email/number/date/select/textarea), validates required fields, tabs for `Nuevo registro` / `Registros` (paginated table)
- Admin panel: users table with role badge + allowed-apps chips, create/edit dialog with checkbox list of apps, delete with confirm dialog, self-delete guard
- Seeded accounts: `admin@portal.com` / `admin123`, `editor@portal.com` / `editor123`, `user@portal.com` / `user123`
- Design tokens: Work Sans + IBM Plex Sans, tinted-navy palette (light + dark ready), grid backdrop on login hero
- All interactive elements carry `data-testid`; testing agent verified 100% backend + frontend flows.

## Prioritized Backlog
### P0 (next iteration if requested)
- Registro de auditoría / logs de accesos por usuario
- Búsqueda + filtros en tablas de registros
- Exportar registros a CSV/Excel

### P1
- Constructor de formularios (crear apps desde UI en lugar de código)
- Roles/permisos por acción (no solo por app) — leer / crear / editar
- Recuperación de contraseña por email (requiere integración Resend/SendGrid)

### P2
- Dark mode toggle en la UI
- Multi-tenant / workspaces
- 2FA para admins

## Test credentials
Ver `/app/memory/test_credentials.md`.
