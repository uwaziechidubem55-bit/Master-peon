# Master peon - Penetration & AI Navigator
# Copyright (C) 2026 UWAZIE DANIEL CHIDUBEM 
# SPDX-License-Identifier: GPL-3.0-or-later

import json
import os
from datetime import datetime, timezone
from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from config.database import Base, engine, SessionLocal, get_db
from config.settings import settings
from backend import models
from backend.auth import get_current_user, hash_password, verify_password, make_token
from backend.storage import save_selfie
from backend.ai_engine.brain import brain
from backend.ai_engine.personal_brain import personal_brain
from backend.policy_engine import check_request
from backend.routers import payments, admin_api, terminal
from backend.tool_modules.executor import TOOL_COMMANDS

MCP_SERVERS = {
    "brave-search": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-brave-search"],
        "env": {
            "BRAVE_API_KEY": os.getenv("BRAVE_API_KEY", ""),
        },
    },
    "fetch": {
        "command": "uvx",
        "args": ["mcp-server-fetch"],
    },
    "postgres": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-postgres", os.getenv("DATABASE_URL", settings.database_url)],
    },
}

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Master Peon API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(payments.router)
app.include_router(admin_api.router)
app.include_router(terminal.router)

@app.on_event("startup")
def seed_admin():
    db = SessionLocal()
    try:
        if not db.query(models.User).filter(models.User.username == settings.admin_username).first():
            db.add(models.User(username=settings.admin_username,
                               email=settings.admin_username,
                               password_hash=hash_password(settings.admin_password),
                               tier="master"))
            db.commit()
    finally:
        db.close()

def reset_daily(user: models.User):
    now = datetime.now(timezone.utc)
    if user.last_reset and user.last_reset.date() < now.date():
        user.chats_today = 0
        user.tool_calls_today = 0
        user.last_reset = now

def tier_allowed(user: models.User) -> list[str]:
    t = settings.tier_limits.get(user.tier, {})
    tools = t.get("tools", [])
    if tools == ["ALL"]:
        return list(TOOL_COMMANDS.keys())
    return tools

class RegisterIn(BaseModel):
    username: str
    email: str
    password: str
    selfie_smile: str
    selfie_vex: str

@app.post("/api/auth/register")
def register(b: RegisterIn, db: Session = Depends(get_db)):
    exists = db.query(models.User).filter(
        (models.User.email == b.email) | (models.User.username == b.username)).first()
    if exists: raise HTTPException(400, "Email or username taken")
    u = models.User(username=b.username, email=b.email, password_hash=hash_password(b.password))
    db.add(u); db.commit(); db.refresh(u)
    u.selfie_smile = save_selfie(b.selfie_smile, f"u{u.id}_smile")
    u.selfie_vex = save_selfie(b.selfie_vex, f"u{u.id}_vex")
    db.commit()
    return {"token": make_token(u.id), "user": u.username, "tier": u.tier}

class LoginIn(BaseModel):
    email: str
    password: str

@app.post("/api/auth/login")
def login(b: LoginIn, db: Session = Depends(get_db)):
    u = db.query(models.User).filter(models.User.email == b.email).first()
    if not u or not verify_password(b.password, u.password_hash):
        raise HTTPException(401, "Bad credentials")
    if u.suspended: raise HTTPException(403, "Account suspended")
    return {"token": make_token(u.id), "user": u.username, "tier": u.tier}

@app.get("/api/me")
def me(user=Depends(get_current_user), db: Session = Depends(get_db)):
    reset_daily(user); db.commit()
    t = settings.tier_limits.get(user.tier, {})
    return {"username": user.username, "tier": user.tier,
            "expiry": str(user.tier_expiry) if user.tier_expiry else "",
            "chats_today": user.chats_today, "chat_limit": t.get("chats", 0),
            "tool_calls_today": user.tool_calls_today, "tool_limit": t.get("tool_calls", 0),
            "allowed_tools": list(tier_allowed(user))}

class ChatIn(BaseModel):
    message: str

@app.post("/api/chat")
async def chat(b: ChatIn, user=Depends(get_current_user), db: Session = Depends(get_db)):
    reset_daily(user)
    t = settings.tier_limits.get(user.tier, {})
    limit = t.get("chats", 0)
    if limit and user.chats_today >= limit:
        raise HTTPException(429, "Daily chat limit reached")
    allowed = list(tier_allowed(user))
    result = await personal_brain.chat(b.message, user.tier, allowed)
    db.add(models.ChatMessage(user_id=user.id, role="user", content=b.message))
    user.chats_today += 1
    tr = result.get("tool_request")
    if tr:
        ok, why = check_request(tr["args"], db)
        if not ok:
            user.suspended = True
            db.commit()
            raise HTTPException(403, f"Account suspended - policy violation: {why}")
        tlimit = t.get("tool_calls", 0)
        if tlimit and user.tool_calls_today >= tlimit:
            db.commit()
            raise HTTPException(429, "Daily tool-call limit reached")
        user.tool_calls_today += 1
        req = models.ToolRequest(user_id=user.id, tool=tr["tool"], args=json.dumps(tr["args"]))
        db.add(req); db.commit()
        tr["id"] = req.id
        tr["status"] = "PENDING"
        result["reply"] += " (⏳ Waiting for admin approval.)"
    db.add(models.ChatMessage(user_id=user.id, role="assistant", content=json.dumps(result)[:2000]))
    db.commit()
    return result

@app.get("/api/tool_requests/mine")
def my_requests(user=Depends(get_current_user), db: Session = Depends(get_db)):
    return [{"id": r.id, "tool": r.tool, "status": r.status,
             "output": r.output[-2000:], "reason": r.denial_reason}
            for r in db.query(models.ToolRequest)
            .filter(models.ToolRequest.user_id == user.id)
            .order_by(models.ToolRequest.id.desc()).limit(20)]

@app.get("/api/health")
def health():
    return {"status": "ok", "service": "master-peon"}

@app.get(settings.admin_secret_path)
async def stealth():
    return FileResponse("templates/stealth_admin.html")

app.mount("/selfies", StaticFiles(directory=settings.selfies_dir), name="selfies")
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/", StaticFiles(directory="templates", html=True), name="templates")