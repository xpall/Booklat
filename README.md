# Booklat

Mobile-first, open-source library management system for schools and small organizations.

## Quick Start

```bash
git clone <repo>
cd booklat
cp .env.example .env   # edit as needed
docker compose up
```

Docker Compose runs PostgreSQL 16, Redis 7, and the Django app with Gunicorn. The entrypoint runs migrations, seeds roles/permissions/admin user, and collects static files.

**Default admin**: LRN `ADMIN`, password `Booklat@Admin2026!` (forced password change on first login).

## Technology

**Backend**: Django 5.1 + PostgreSQL 16 + Redis 7 + Gunicorn + WhiteNoise  
**Frontend**: Django Templates + custom CSS design system  
**Auth**: LRN-based login, Argon2id password hashing, DB-driven permissions (no Django admin)  
**Middleware**: Login-required (global), must-change-password enforcement, django-ratelimit  
**Deployment**: Docker Compose, optional Cloudflare Tunnel (`docker-compose.prod.yml`)

## Apps

| App | Purpose |
|-----|---------|
| `accounts` | Custom User model, roles, DB permissions, LRN auth |
| `books` | Book title catalog |
| `inventory` | Physical copies (BookCopy), append-only CopyHistory |
| `loans` | Checkout/return workflows, overdue tracking |
| `requests_app` | Checkout requests with staff approval |
| `audit` | Immutable audit log (JSON metadata) |
| `dashboard` | Statistics, pending requests, overdue loans |
| `core` | Middleware, decorators, utils, base template |
