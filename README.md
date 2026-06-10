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

## Setup & Installation (Production VPS)

### Prerequisites
- Fresh VPS running Ubuntu 22.04+ or Debian 12+
- SSH access as root
- Target URL (e.g. `booklat.bettercalauan.org`) pointing to your VPS

> **Steps 1–3 are for remote VPS setups only.** Skip to step 4 if you're self-hosting on a dedicated PC or laptop you have direct access to.

### 1. Generate SSH Key (Local Machine)

If you don't have an SSH key pair yet, generate one on your local machine:

```bash
ssh-keygen -t ed25519 -C "your-email@example.com"
```

Your public key is at `~/.ssh/id_ed25519.pub` — copy its contents for the next step.

### 2. SSH Key Authentication

```bash
su - booklat
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
adduser booklat
usermod -aG sudo booklat
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
- `ALLOWED_HOSTS` — set to your target URL (e.g. `booklat.bettercalauan.org`)
- `ADMIN_LRN` and `ADMIN_PASSWORD` — change the default admin credentials

```bash
docker compose up -d
```

### 10. Cloudflare Tunnel (Optional)

Deploy the tunnel through the [Cloudflare Zero Trust dashboard](https://one.dash.cloudflare.com/) rather than the CLI:

1. Go to **Networks → Tunnels** and click **Create a tunnel**.
2. Name it (e.g. `booklat`), select your OS, and copy the install command.
3. Run the installer on your VPS — it installs and authenticates the `cloudflared` daemon automatically.
4. Back in the dashboard, configure a **Public Hostname**:
   - **Subdomain/Domain**: your-domain.com
   - **Service type**: HTTP
   - **URL**: `localhost:8000` (or your Gunicorn port)

The tunnel will stay connected as long as `cloudflared` is running. For persistence, see `docker-compose.prod.yml` which bundles cloudflared with the stack.

## Technology

**Backend**: Django 5.1 + PostgreSQL 16 + Redis 7 + Gunicorn + WhiteNoise + Celery  
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
| `core` | Middleware, decorators, utils, base template, about page |
| `freedom_wall` | Sticky-note posts with upvotes, moderation queue |
