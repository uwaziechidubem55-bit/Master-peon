# Master Peon

AI-assisted penetration testing platform built on FastAPI + Kali Linux.

## Quick Start

```bash
# Clone the repo
git clone <REPO_URL>
cd Master-peon

# Copy and edit env
cp .env.example .env
# Fill in at minimum: SECRET_KEY, ADMIN_USERNAME, ADMIN_PASSWORD

# Launch everything
docker compose up -d --build