# Master Peon

AI-assisted penetration testing platform built on FastAPI + Kali Linux.

## Quick Start

```bash
git clone <REPO_URL>
cd Master-peon

cp .env.example .env
# Fill in at minimum: SECRET_KEY, ADMIN_USERNAME, ADMIN_PASSWORD

docker compose up -d --build