# MasterPeon
### Penetration & AI Navigator

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Kali%20Linux-red)](https://www.kali.org)

MasterPeon is an AI-assisted penetration testing platform. It combines a conversational AI with 30 industry-standard security tools, all containerized on Kali Linux for authorized red team operations.

**Disclaimer: For Authorized Use Only.** See [SAFETY.md](SAFETY.md)

---

## 1. Key Features

| Category | Tools & Capabilities |
| --- | --- |
| **AI Core** | FastAPI + LLM Agent. Natural language to commands. Explains results + suggests next steps. |
| **Recon & OSINT** | `nmap`, `masscan`, `whatweb`, `sublist3r`, `whois`, `netdiscover` |
| **Web App Testing** | `nikto`, `dirb`, `ffuf`, `gobuster`, `nuclei`, `wpscan`, `sqlmap`, `burp` |
| **Password Attacks** | `hydra`, `medusa`, `john`, `hashcat`, `crunch`, `hash-identifier` |
| **Network & Sniffing** | `tcpdump`, `tshark`, `netcat`, `chisel`, `ligolo` |
| **Post Exploitation** | `linpeas`, `winpeas`, `pspy`, `metasploit` |
| **Exploit Frameworks** | `metasploit`, `routersploit` |

All tools are pre-installed and accessible via the AI Agent or directly in the container shell.

---

## 2. Tech Stack
- **Backend**: Python 3.11, FastAPI, SQLAlchemy, Pydantic
- **AI/LLM**: Pluggable - OpenAI, Claude, Gemini, or Local LLM via Ollama
- **Database**: PostgreSQL
- **Platform**: Docker + Kali Linux Rolling
- **Auth**: JWT + Bcrypt
- **Frontend**: React + Tailwind, Mode: `Ask` / `Agent`

---

## 3. Quick Start

### Prerequisites
- Docker & Docker Compose
- 8GB+ RAM. Some tools like `hashcat` and `masscan` are memory/cpu intensive.

### Installation
```bash
git clone <REPO_URL>
cd MasterPeon

cp .env.example .env
# IMPORTANT: Fill in SECRET_KEY, ADMIN_USERNAME, ADMIN_PASSWORD, DB_URL

docker compose up -d --build