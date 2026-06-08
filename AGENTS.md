# AGENTS.md

## Setup & Commands

```bash
# Local dev (needs PostgreSQL + Redis, or use Docker)
python manage.py migrate
python manage.py seed_data       # creates roles, permissions, admin user (set ADMIN_LRN + ADMIN_PASSWORD in .env)
python manage.py runserver

# Docker dev (preferred — runs migrate + seed_data + collectstatic automatically)
docker compose up

# Run tests (all stub files — no tests written yet)
python manage.py test
python manage.py test accounts
python manage.py test accounts.tests.SomeTest.test_something
```

No linting, formatting, typechecking, or CI is configured. No Makefile.

## Architecture

Single Django 5.1 project (Python 3.12), **not** a monorepo. 9 Django apps in one project:

| App | Purpose |
|-----|---------|
| `accounts` | Custom User model, roles, DB-backed permissions, LRN-based auth |
| `books` | Book title catalog, categories |
| `inventory` | BookCopy (physical copies), CopyHistory (append-only, immutable) |
| `loans` | Checkout/return workflows, overdue tracking |
| `requests_app` | Checkout requests (named this to avoid Python stdlib clash) |
| `audit` | Immutable audit log (JSONField metadata via `core.utils.log_action`) |
| `dashboard` | Admin/staff/student dashboard statistics |
| `core` | Cross-cutting: middleware, permission decorators, CSV export/import utils, base template, about page |
| `freedom_wall` | Sticky-note posts with upvotes, pending queue moderation, Celery midnight purge |

Stack: Django 5.1 + PostgreSQL 16 + Redis 7 + Celery + Gunicorn + WhiteNoise + custom design-system.css + django-ratelimit. Python 3.12.

## Critical Gotchas

### No Django Admin
`django.contrib.admin` is **not** in INSTALLED_APPS. All user, book, and loan management is through custom views. Do not try to use or register ModelAdmin.

### Custom User Model — NOT an AbstractUser subclass
`accounts.User` does its own password hashing (Argon2id), auth properties, and permission checks. References to `request.user` will be this custom model. Use `AUTH_USER_MODEL = "accounts.User"` in ForeignKey definitions.

The model has `is_admin`, `is_staff_user`, `is_member` — **not** Django's `is_superuser` or `is_staff`. It also has an `id` property that returns `pk`.

### Auth: LRN-based, not username/email
`accounts.backends.LRNAuthenticationBackend` authenticates by LRN (`lrn` field) + password — the only auth backend configured. Login form must use `lrn` as the credential field name.

### Password rules are unusually strict
Custom validators in `accounts/validators.py`: **minimum 16 characters**, 1 uppercase, 1 lowercase, 1 number, 1 special character. Agents creating test users frequently get this wrong and wonder why the form rejects.

### Permission system is DB-driven, not Django's built-in
Permissions are rows in `accounts.Permission` linked to `accounts.Role` via `RolePermission`. Use:
- `user.has_perm(codename)` — checks DB via RolePermission
- Decorators: `@permission_required("loans.create")`, `@any_permission_required("a", "b")`, `@admin_or_staff_required`
- Django's `User.has_perm(perm)` exists but looks up our custom model's method, not Django's default permission system
- Do NOT use `user.has_perm("app_label.codename")` — the codenames are strings like `"loans.create"`, not Django's `"loans.add_loan"` format

### Global login middleware — every URL is protected
`core.middleware.LoginRequiredMiddleware` redirects all unauthenticated requests to login. Only `/accounts/login/`, `/accounts/password-change/`, `/about/`, and `/static/` are exempt. New public URLs must be added to the exempt list in the middleware.

### Must-change-password enforcement
`core.middleware.MustChangePasswordMiddleware` forces users with `must_change_password=True` to the password change page. The admin seed user has this flag set. Only login, password_change, and logout are exempt from this redirect.

### `requests_app` naming
The app is `requests_app`, not `requests`, to avoid colliding with Python's `requests` library. URL namespace is `requests:` and templates go in `templates/requests_app/`.

### `seed_data` is required
The `manage.py seed_data` command is idempotent (uses `get_or_create`) and must run before first use. It creates three roles (Administrator, Staff, Member), all permissions, and an admin user (LRN: ADMIN, password: Booklat@Admin2026!, forced password change on first login). The Docker entrypoint runs this automatically. The `.env.example` exists as a template for env vars.

### Soft deletes
No actual DELETE operations. Users use `status=archived`, BookCopies use status choices (Available/Borrowed/Reserved/Lost/Damaged/Under Repair/Archived). Always filter by status when querying.

### Ratelimit: disabled in DEBUG, active in production
`django-ratelimit` is installed. `RATELIMIT_ENABLE = not DEBUG` — so ratelimits are off during local dev but apply in Docker/production. Test auth rate-limiting behavior with DEBUG=0.

### Session behavior
- Sessions stored in DB + cached in Redis (`cached_db` backend)
- Expires on browser close (`SESSION_EXPIRE_AT_BROWSER_CLOSE = True`)
- Max 24-hour cookie age (`SESSION_COOKIE_AGE = 86400`)

### Static files
WhiteNoise with `CompressedManifestStaticFilesStorage`. Static root is `staticfiles/`. Custom CSS design system at `core/static/core/css/design-system.css` (mobile-first, dark mode, app shell layout). The `data/` directory is gitignored but used for Docker volumes (postgres + staticfiles).

### Environment & settings
No dotenv package — env vars are read directly in `settings.py` with fallback defaults. `.env` is only used by Docker Compose. Database uses persistent connections (`CONN_MAX_AGE=600`). Timezone is `Asia/Manila`.

### Celery
Celery 5.4 is configured with Redis as broker (db 1) and result backend (db 2). Beat schedule runs a daily midnight task (`purge-freedom-posts-midnight`) that deletes all FreedomPost records. Worker and beat services are included in docker-compose.yml. `config/__init__.py` wires the Celery app.

## Key files

- `SPEC.md` — 1061-line exhaustive spec covering all features, permission model, workflows
- `config/settings.py` — all Django settings, env loading, app registration
- `accounts/models.py` — custom User, Role, Permission models
- `core/middleware.py` — login and password-change enforcement
- `core/decorators.py` — permission decorators
- `accounts/management/commands/seed_data.py` — seeds roles, permissions, admin user
- `accounts/validators.py` — password validation rules (16-char minimum, etc.)
- `accounts/backends.py` — LRN-based authentication backend
- `entrypoint.sh` — Docker startup: migrate → collectstatic → seed_data → gunicorn
- `config/celery.py` — Celery app and beat schedule