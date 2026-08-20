# Master peon - Penetration & AI Navigator
# Copyright (C) 2026 UWAZIE DANIEL CHIDUBEM 
# SPDX-License-Identifier: GPL-3.0-or-later

from datetime import datetime, timedelta, timezone
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from config.database import get_db
from config.settings import settings
from backend import models

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer = HTTPBearer(auto_error=False)

def hash_password(pw): return pwd.hash(pw)
def verify_password(pw, h): return pwd.verify(pw, h)

def make_token(user_id: int) -> str:
    exp = datetime.now(timezone.utc) + timedelta(days=7)
    return jwt.encode({"sub": str(user_id), "exp": exp}, settings.secret_key, algorithm="HS256")

def get_current_user(cred=Depends(bearer), db: Session = Depends(get_db)) -> models.User:
    if not cred:
        raise HTTPException(401, "Not authenticated")
    try:
        payload = jwt.decode(cred.credentials, settings.secret_key, algorithms=["HS256"])
        user = db.query(models.User).get(int(payload["sub"]))
    except Exception:
        raise HTTPException(401, "Invalid token")
    if not user:
        raise HTTPException(401, "User not found")
    if user.suspended:
        raise HTTPException(403, "Account suspended")
    return user

def require_admin(user: models.User = Depends(get_current_user)) -> models.User:
    if user.username != settings.admin_username:
        raise HTTPException(403, "Admin only")
    return user

def is_admin(username: str) -> bool:
    return username == settings.admin_username
