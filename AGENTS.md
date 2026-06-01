# AGENTS.md

## Setup & Commands

```bash
# Local dev (needs PostgreSQL + Redis, or use Docker)
python manage.py migrate
python manage.py seed_data       # creates roles, permissions, admin user (ADMIN / Booklat@Admin2026!)
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

Single Django 5.1 project (Python 3.12), **not** a monorepo. 8 Django apps in one project:

| App | Purpose |
|-----|---------|
| `accounts` | Custom User model, roles, DB-backed permissions, LRN-based auth |
| `books` | Book title catalog |
| `inventory` | BookCopy (physical copies), CopyHistory (append-only, immutable) |
| `loans` | Checkout/return workflows, overdue tracking |
| `requests_app` | Checkout requests (named this to avoid Python stdlib clash) |
| `audit` | Immutable audit log (JSONField metadata via `core.utils.log_action`) |
| `dashboard` | Admin/staff dashboard statistics |
| `core` | Cross-cutting: middleware, permission decorators, CSV export/import utils, base template |

Stack: Django 5.1 + PostgreSQL 16 + Redis 7 + Gunicorn + WhiteNoise + Pico CSS v2 (CDN).

## Critical Gotchas

### No Django Admin
`django.contrib.admin` is **not** in INSTALLED_APPS. All user, book, and loan management is through custom views. Do not try to use or register ModelAdmin.

### Custom User Model — NOT an AbstractUser subclass
`accounts.User` does its own password hashing (Argon2id), auth properties, and permission checks. It has an `id` property that returns `pk`. References to `request.user` will be this custom model. Use `AUTH_USER_MODEL = "accounts.User"` in ForeignKey definitions.

### Permission system is DB-driven, not Django's built-in
Permissions are rows in `accounts.Permission` linked to `accounts.Role` via `RolePermission`. Use:
- `user.has_perm(codename)` — checks DB via RolePermission
- Decorators: `@permission_required("loans.create")`, `@any_permission_required("a", "b")`, `@admin_or_staff_required`
- Django's `User.has_perm(perm)` exists but looks up our custom model's method, not Django's default permission system
- Do NOT use `user.has_perm("app_label.codename")` — the codenames are strings like `"loans.create"`, not Django's `"loans.add_loan"` format

### Global login middleware — every URL is protected
`core.middleware.LoginRequiredMiddleware` redirects all unauthenticated requests to login. Only `/accounts/login/`, `/accounts/password-change/`, and `/static/` are exempt. New public URLs must be added to the exempt list in the middleware.

### Must-change-password enforcement
`core.middleware.MustChangePasswordMiddleware` forces users with `must_change_password=True` to the password change page. The admin seed user has this flag set. Only login, password_change, and logout are exempt from this redirect.

### `requests_app` naming
The app is `requests_app`, not `requests`, to avoid colliding with Python's `requests` library. URL namespace is `requests:` and templates go in `templates/requests_app/`.

### `seed_data` is required
The `manage.py seed_data` command is idempotent (uses `get_or_create`) and must run before first use. It creates three roles (Administrator, Staff, Member), all permissions, and an admin user (LRN: ADMIN, password: Booklat@Admin2026!, forced password change on first login). The Docker entrypoint runs this automatically.

### Soft deletes
No actual DELETE operations. Users use `status=archived`, BookCopies use status choices (Available/Borrowed/Reserved/Lost/Damaged/Under Repair/Archived). Always filter by status when querying.

### Session behavior
- Sessions stored in DB + cached in Redis (`cached_db` backend)
- Expires on browser close (`SESSION_EXPIRE_AT_BROWSER_CLOSE = True`)
- Max 24-hour cookie age (`SESSION_COOKIE_AGE = 86400`)

### Static files
WhiteNoise with `CompressedManifestStaticFilesStorage`. Static root is `staticfiles/`. Pico CSS is loaded from CDN (not bundled).

### Environment & settings
No dotenv package — env vars are read directly in `settings.py` with fallback defaults. `.env` is only used by Docker Compose. Database uses persistent connections (`CONN_MAX_AGE=600`). Timezone is `Asia/Manila`.

### Celery is NOT implemented
Mentioned in SPEC.md but not in requirements.txt and no tasks exist. Do not create Celery tasks without adding the dependency and wiring it up.

## Key files

- `SPEC.md` — 1046-line exhaustive spec covering all features, permission model, workflows
- `config/settings.py` — all Django settings, env loading, app registration
- `accounts/models.py` — custom User, Role, Permission models
- `core/middleware.py` — login and password-change enforcement
- `core/decorators.py` — permission decorators
- `accounts/management/commands/seed_data.py` — seeds roles, permissions, admin user
- `entrypoint.sh` — Docker startup: migrate → collectstatic → seed_data → gunicorn