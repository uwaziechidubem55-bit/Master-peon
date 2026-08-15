from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, ForeignKey
from config.database import Base

def utcnow():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(120), unique=True, index=True)
    password_hash = Column(String(200))
    tier = Column(String(20), default="free")
    tier_expiry = Column(DateTime, nullable=True)
    selfie_smile = Column(String(300), default="")
    selfie_vex = Column(String(300), default="")
    suspended = Column(Boolean, default=False)
    chats_today = Column(Integer, default=0)
    tool_calls_today = Column(Integer, default=0)
    last_reset = Column(DateTime, default=utcnow)
    created_at = Column(DateTime, default=utcnow)

class ToolRequest(Base):
    __tablename__ = "tool_requests"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    tool = Column(String(50))
    args = Column(Text, default="[]")
    status = Column(String(20), default="PENDING")
    output = Column(Text, default="")
    denial_reason = Column(String(300), default="")
    created_at = Column(DateTime, default=utcnow)

class Payment(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    tx_ref = Column(String(100), unique=True)
    flw_id = Column(String(100), default="")
    tier = Column(String(20))
    period = Column(String(10))
    amount = Column(Float)
    status = Column(String(20), default="PENDING")
    created_at = Column(DateTime, default=utcnow)

class PolicyRule(Base):
    __tablename__ = "policy_rules"
    id = Column(Integer, primary_key=True)
    text = Column(Text)
    active = Column(Boolean, default=True)

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    role = Column(String(10))
    content = Column(Text)
    created_at = Column(DateTime, default=utcnow)
