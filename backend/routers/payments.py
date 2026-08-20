i# Master peon - Penetration & AI Navigator
# Copyright (C) 2026 UWAZIE DANIEL CHIDUBEM 
# SPDX-License-Identifier: GPL-3.0-or-later

mport secrets
from datetime import datetime, timedelta, timezone
import hmac
import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from config.database import get_db
from config.settings import settings
from backend import models
from backend.auth import get_current_user, is_admin

router = APIRouter(prefix="/api/payments", tags=["payments"])
FLW = "https://api.flutterwave.com/v3"

@router.post("/initiate")
async def initiate(tier: str, period: str, user=Depends(get_current_user), db: Session = Depends(get_db)):
    t = settings.tier_limits.get(tier)
    if not t: raise HTTPException(400, "Bad tier")
    amount = t["price_month"] if period == "month" else t["price_year"] if period == "year" else None
    if amount is None: raise HTTPException(400, "Bad period")
    if amount <= 0: raise HTTPException(400, "That tier is free")
    tx_ref = f"MP-{user.id}-{secrets.token_hex(4)}"
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.post(f"{FLW}/payments",
                         headers={"Authorization": f"Bearer {settings.flw_secret_key}"},
                         json={"tx_ref": tx_ref, "amount": amount, "currency": "NGN",
                               "redirect_url": f"{settings.base_url}/profile.html",
                               "customer": {"email": user.email, "name": user.username},
                               "customizations": {"title": "Master Peon",
                                                  "description": f"{tier} tier ({period})"}})
        r.raise_for_status()
        link = r.json()["data"]["link"]
    db.add(models.Payment(user_id=user.id, tx_ref=tx_ref, tier=tier, period=period, amount=amount))
    db.commit()
    return {"link": link}

@router.post("/webhook")
async def webhook(request: Request, db: Session = Depends(get_db)):
    # ---- AUTH: TWO valid paths (either one is enough) ----
    # 1) verif-hash      -> alert came DIRECTLY from Flutterwave (dashboard)
    # 2) X-Forward-Token -> alert was FORWARDED by the OLD election project
    #    (Flutterwave allows only ONE dashboard webhook URL per account,
    #     and that URL belongs to the election project)
    verif = request.headers.get("verif-hash", "")
    fwd = request.headers.get("X-Forward-Token", "")
    ok_direct = bool(verif) and hmac.compare_digest(verif, settings.flw_webhook_hash)
    ok_forward = bool(fwd) and hmac.compare_digest(fwd, settings.flw_forward_token)
    if not (ok_direct or ok_forward):
        raise HTTPException(401, "Bad hash")

    body = await request.json()
    data = body.get("data", {}) or {}
    tx_ref = data.get("tx_ref", "")
    if not tx_ref:
        return {"ok": True, "status": "ignored"}

    pay = db.query(models.Payment).filter(models.Payment.tx_ref == tx_ref).first()
    if not pay:
        # Not one of our transactions — ignore quietly, never 404 a webhook.
        # (A webhook is not a user request; an error here would trigger
        #  Flutterwave retries for nothing.)
        return {"ok": True, "status": "ignored"}

    if pay.status == "SUCCESS":
        # Idempotency: Flutterwave retries + forward retries must not
        # re-grant the tier or reset the expiry date.
        return {"ok": True, "status": "already-processed"}

    if data.get("status") == "successful":
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.get(f"{FLW}/transactions/{data.get('id')}/verify",
                            headers={"Authorization": f"Bearer {settings.flw_secret_key}"})
            v = r.json().get("data", {})
        if v.get("status") == "successful" and float(v.get("amount", 0)) >= pay.amount:
            pay.status = "SUCCESS"
            pay.flw_id = str(data.get("id", ""))
            u = db.query(models.User).get(pay.user_id)
            u.tier = pay.tier
            u.tier_expiry = datetime.now(timezone.utc) + timedelta(days=365 if pay.period == "year" else 30)
            db.commit()
    return {"ok": True}

@router.post("/withdraw")
async def withdraw(amount: float, user=Depends(get_current_user)):
    if not is_admin(user.username): raise HTTPException(403, "Admin only")
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.post(f"{FLW}/transfers",
                         headers={"Authorization": f"Bearer {settings.flw_secret_key}"},
                         json={"account_bank": settings.flw_bank_code,
                               "account_number": settings.flw_account_number,
                               "amount": amount, "currency": "NGN",
                               "narration": "Master Peon payout"})
    return {"status": r.status_code, "body": r.json()}
