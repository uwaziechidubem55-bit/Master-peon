# Master poen
### Penetration & Everything AI Navigator

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Kali%20Linux-red)](https://www.kali.org)

Master P.E.A.N is an AI-assisted penetration testing platform. It combines a conversational AI with 25+ industry-standard security tools, all containerized on Kali Linux for authorized red team operations.

**Disclaimer: For Authorized Use Only.** See [SAFETY.md](SAFETY.md)

---

## 1. Key Features

| Category | Tools & Capabilities |
| --- | --- |
| **AI Core** | FastAPI + LLM Agent. Natural language to commands. Explains results. |
| **Recon** | `nmap`, `whatweb`, `sublist3r`, `whois`, `netdiscover` |
| **Web App Testing** | `nikto`, `dirb`, `ffuf`, `sqlmap`, `burpsuite` |
| **Password Attacks** | `hydra`, `john`, `hashcat`, `medusa`, `crunch` |
| **Network** | `tcpdump`, `tshark`, `chisel`, `ligolo-ng`, `netcat` |
| **Post Exploitation** | `linpeas`, `winpeas`, `pspy`, `msfconsole` |
| **IoT/Router** | `routersploit` |

---

## 2. Tech Stack
- **Backend**: Python 3.11, FastAPI, SQLAlchemy, Pydantic
- **AI/LLM**: Pluggable - OpenAI, Claude, Gemini, or Local LLM
- **Database**: PostgreSQL
- **Platform**: Docker + Kali Linux Rolling
- **Auth**: JWT + Bcrypt

---

## 3. Quick Start

### Prerequisites
- Docker & Docker Compose
- 8GB+ RAM. Some tools are memory intensive.

### Installation
```bash
git clone <REPO_URL>
cd Master-P.E.A.N

cp .env.example .env
# IMPORTANT: Fill in SECRET_KEY, ADMIN_USERNAME, ADMIN_PASSWORD, DB_URL