import json
import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session
from config.database import get_db
from config.settings import settings
from backend import models
from backend.auth import require_admin
from backend.tool_modules.executor import execute

FLW = "https://api.flutterwave.com/v3"
router = APIRouter(prefix="/api/admin", tags=["admin"])

class RunToolIn(BaseModel):
    tool: str
    args: list[str] = []

@router.get("/stats")
def stats(db: Session = Depends(get_db), admin=Depends(require_admin)):
    rev = db.query(func.coalesce(func.sum(models.Payment.amount), 0))\
        .filter(models.Payment.status == "SUCCESS").scalar()
    return {"users": db.query(models.User).count(),
            "pending": db.query(models.ToolRequest)
                       .filter(models.ToolRequest.status == "PENDING").count(),
            "revenue": float(rev)}

@router.get("/queue")
def queue(db: Session = Depends(get_db), admin=Depends(require_admin)):
    return [{"id": r.id, "user_id": r.user_id, "tool": r.tool, "args": r.args,
             "status": r.status, "created": str(r.created_at)}
            for r in db.query(models.ToolRequest)
            .filter(models.ToolRequest.status == "PENDING")
            .order_by(models.ToolRequest.id).all()]

@router.post("/approve/{rid}")
async def approve(rid: int, db: Session = Depends(get_db), admin=Depends(require_admin)):
    req = db.query(models.ToolRequest).get(rid)
    if not req: raise HTTPException(404, "Not found")
    req.status = "RUNNING"
    db.commit()
    output = await execute(req.id, req.tool, json.loads(req.args or "[]"))
    req.output = output
    req.status = "DONE"
    db.commit()
    return {"ok": True, "tool": req.tool, "output_preview": output[:500]}

@router.post("/deny/{rid}")
def deny(rid: int, reason: str = "", db: Session = Depends(get_db), admin=Depends(require_admin)):
    req = db.query(models.ToolRequest).get(rid)
    if not req: raise HTTPException(404, "Not found")
    req.status = "DENIED"
    req.denial_reason = reason
    db.commit()
    return {"ok": True}

@router.post("/run-tool")  # OWNER direct use - bypasses the queue
async def run_tool(b: RunToolIn, db: Session = Depends(get_db), admin=Depends(require_admin)):
    req = models.ToolRequest(user_id=0, tool=b.tool, args=json.dumps(b.args), status="RUNNING")
    db.add(req); db.commit(); db.refresh(req)
    output = await execute(req.id, b.tool, b.args)
    req.output = output; req.status = "DONE"; db.commit()
    return {"ok": True, "output": output[-5000:]}

@router.get("/users")
def users(db: Session = Depends(get_db), admin=Depends(require_admin)):
    return [{"id": u.id, "username": u.username, "email": u.email, "tier": u.tier,
             "expiry": str(u.tier_expiry) if u.tier_expiry else "",
             "suspended": u.suspended, "selfie_smile": u.selfie_smile,
             "selfie_vex": u.selfie_vex}
            for u in db.query(models.User).all()]

@router.post("/users/{uid}/suspend")
def suspend(uid: int, db: Session = Depends(get_db), admin=Depends(require_admin)):
    u = db.query(models.User).get(uid)
    if not u: raise HTTPException(404, "User not found")
    u.suspended = not u.suspended
    db.commit()
    return {"ok": True, "suspended": u.suspended}

@router.get("/limits")
def get_limits(admin=Depends(require_admin)):
    return settings.tier_limits

@router.post("/limits")
def set_limits(payload: dict, admin=Depends(require_admin)):
    settings.tier_limits.update(payload.get("tiers", {}))
    return {"ok": True}

@router.get("/policy")
def policy(db: Session = Depends(get_db), admin=Depends(require_admin)):
    return [{"id": r.id, "text": r.text, "active": r.active}
            for r in db.query(models.PolicyRule).all()]

@router.post("/policy/enforce")
def enforce(payload: dict, db: Session = Depends(get_db), admin=Depends(require_admin)):
    for r in db.query(models.PolicyRule).all():
        db.delete(r)
    for text in payload.get("rules", []):
        db.add(models.PolicyRule(text=text))
    db.commit()
    return {"ok": True, "enforced": True}

@router.get("/finance")
async def finance(admin=Depends(require_admin)):
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.get(f"{FLW}/balances/NGN",
                        headers={"Authorization": f"Bearer {settings.flw_secret_key}"})
        data = r.json().get("data", [])
    return {"balance": data}
