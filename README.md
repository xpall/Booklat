# Booklat

Mobile-first, open-source library management system for schools and small organizations.

**Live Demo**: [booklat-demo.bettercalauan.org](https://booklat-demo.bettercalauan.org)

![Booklat Mobile UI](assets/booklat-mobile-view.webp)

## Quick Start

```bash
git clone https://github.com/xpall/Booklat.git
cd booklat
cp .env.example .env   # edit as needed
docker compose up
```

Docker Compose runs PostgreSQL 16, Redis 7, and the Django app with Gunicorn. The entrypoint runs migrations, seeds roles/permissions/admin user, and collects static files.

## Setup & Installation (Production VPS)

### Prerequisites
- Fresh VPS running Ubuntu 22.04+ or Debian 12+
- SSH access as root
- Target URL (e.g. `booklat.bettercalauan.org`) pointing to your VPS

> **Steps 1–3 are for remote VPS setups only.** Skip to step 4 if you're self-hosting on a dedicated PC or laptop you have direct access to.

**Video Walkthrough**: [How to Setup Booklat on a VPS](https://www.youtube.com/watch?v=Rirgmc_sLmI) (audio in Filipino)

### 1. Generate SSH Key (Local Machine)

If you don't have an SSH key pair yet, generate one on your local machine:

```bash
ssh-keygen -t ed25519 -C "your-email@example.com"
```

Your public key is at `~/.ssh/id_ed25519.pub` — copy its contents for the next step.

### 2. SSH Key Authentication

```bash
# Create the booklat user first (also done in step 4; duplicated here for VPS setups)
adduser booklat-demo
usermod -aG sudo booklat-demo

su - booklat-demo
mkdir -p ~/.ssh && chmod 700 ~/.ssh
vim ~/.ssh/authorized_keys   # paste your public key
chmod 600 ~/.ssh/authorized_keys
```

### 3. Harden SSH

```bash
sudo vim /etc/ssh/sshd_config
```

Set: `PasswordAuthentication no`, `PermitRootLogin no`, `UsePAM no`.
Check for override files in `/etc/ssh/sshd_config.d/` and update them too, then:

```bash
sudo systemctl reload ssh
```

### 4. Update System & Create User

```bash
sudo apt update && sudo apt upgrade -y
adduser booklat-demo
usermod -aG sudo booklat-demo
```

### 5. Firewall (UFW)

```bash
sudo apt install ufw
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow OpenSSH
sudo ufw enable
```

### 6. Fail2ban

```bash
sudo apt install fail2ban
sudo cp /etc/fail2ban/fail2ban.conf /etc/fail2ban/fail2ban.local
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local
sudo systemctl enable --now fail2ban
```

### 7. Automatic Security Updates

```bash
sudo apt install unattended-upgrades
sudo dpkg-reconfigure unattended-upgrades   # select Yes
```

### 8. Install Docker & Docker Compose

```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
newgrp docker
```

### 9. Deploy Booklat

```bash
git clone git@github.com:xpall/Booklat.git booklat
cd booklat
cp .env.example .env
vim .env
```

In `.env`, update the following:
- `SECRET_KEY` — generate a strong random value (e.g. `openssl rand -base64 48`)
- `ALLOWED_HOSTS` — public hostname plus `127.0.0.1` for the container healthcheck (e.g. `booklat.bettercalauan.org,127.0.0.1`)
- `CSRF_TRUSTED_ORIGINS` — set to the public HTTPS origin (e.g. `https://booklat.bettercalauan.org`)
- `APP_PORT` — unique host port for this app (default `8010`; the container stays on `8000` internally)
- `ADMIN_LRN` and `ADMIN_PASSWORD` — change the default admin credentials

```bash
docker compose up -d
```

### 10. Cloudflare Tunnel

Deploy the tunnel through the [Cloudflare Zero Trust dashboard](https://one.dash.cloudflare.com/) rather than the CLI:

1. Go to **Networks → Tunnels** and click **Create a tunnel**.
2. Name it (e.g. `booklat`), select your OS, and copy the install command.
3. Run the installer on your VPS — it installs and authenticates the `cloudflared` daemon automatically.
4. Back in the dashboard, configure a **Public Hostname**:
   - **Subdomain/Domain**: your-domain.com
   - **Service type**: HTTP
   - **URL**: `http://127.0.0.1:<APP_PORT>` (e.g. `http://127.0.0.1:8010`)

The tunnel will stay connected as long as `cloudflared` is running.

#### Multiple apps on one VPS

Run **one** `cloudflared` instance on the host and give each app a unique `APP_PORT`. Add one public hostname per app, each pointing to that app's loopback port:

| App | `.env` | Public hostname service URL |
|-----|--------|-----------------------------|
| Booklat | `APP_PORT=8010` | `http://127.0.0.1:8010` |
| App 2 | `APP_PORT=8011` | `http://127.0.0.1:8011` |
| App 3 | `APP_PORT=8012` | `http://127.0.0.1:8012` |

The ports stay bound to `127.0.0.1`, so the apps are only reachable through the tunnel (or locally on the VPS). If you change an app's `APP_PORT` later, update its public hostname's service URL in the dashboard to match, then recreate the container with `docker compose up -d`.

`docker-compose.prod.yml` includes an optional `bundled-tunnel` profile for a **dedicated** tunnel per app. Do not enable it when using the shared host-level tunnel; it would create a second connector for the same tunnel.

To verify the published port:

```bash
docker compose up -d
docker compose port web 8000   # e.g. 127.0.0.1:8010
curl -I http://127.0.0.1:8010/accounts/login/
```

## Technology

**Backend**: Django 5.1 + PostgreSQL 16 + Redis 7 + Gunicorn + WhiteNoise + Celery  
**Frontend**: Django Templates + custom CSS design system  
**Auth**: LRN-based login, Argon2id password hashing, DB-driven permissions (no Django admin)  
**Middleware**: Login-required (global), must-change-password enforcement, django-ratelimit  
**Deployment**: Docker Compose, shared host-level Cloudflare Tunnel (optional per-app tunnel profile in `docker-compose.prod.yml`)

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
| `core` | Middleware, decorators, utils, base template, about page |
| `freedom_wall` | Sticky-note posts with upvotes, moderation queue |
