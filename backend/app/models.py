import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db import Base


def new_uuid() -> str:
    return str(uuid.uuid4())


class Officer(Base):
    __tablename__ = "officers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    name_kn: Mapped[str] = mapped_column(String, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    psk_district: Mapped[str] = mapped_column(String, nullable=False, default="Bangalore Urban")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    decisions: Mapped[list["Decision"]] = relationship(back_populates="officer")


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    app_no: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    applicant_name: Mapped[str] = mapped_column(String, nullable=False)
    applicant_name_kn: Mapped[str] = mapped_column(String, nullable=False)
    gender: Mapped[str] = mapped_column(String, nullable=False)
    dob: Mapped[str] = mapped_column(String, nullable=False)  # ISO date string
    phone_masked: Mapped[str] = mapped_column(String, nullable=False)
    aadhaar_masked: Mapped[str] = mapped_column(String, nullable=False)
    application_type: Mapped[str] = mapped_column(String, nullable=False, default="fresh")
    documents: Mapped[dict] = mapped_column(JSON, nullable=False, default=list)
    status: Mapped[str] = mapped_column(String, nullable=False, default="pending")
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    appointment_date: Mapped[str] = mapped_column(String, nullable=False)  # ISO date string
    deadline_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    ai_analyses: Mapped[list["AiAnalysis"]] = relationship(back_populates="application")
    decisions: Mapped[list["Decision"]] = relationship(back_populates="application")
    audit_events: Mapped[list["AuditEvent"]] = relationship(back_populates="application")


class AiAnalysis(Base):
    __tablename__ = "ai_analyses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    application_id: Mapped[str] = mapped_column(ForeignKey("applications.id"), nullable=False)
    input_hash: Mapped[str] = mapped_column(String, nullable=False)
    prompt_version: Mapped[str] = mapped_column(String, nullable=False)
    model: Mapped[str] = mapped_column(String, nullable=False)
    result: Mapped[dict] = mapped_column(JSON, nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    application: Mapped["Application"] = relationship(back_populates="ai_analyses")


class Decision(Base):
    __tablename__ = "decisions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    application_id: Mapped[str] = mapped_column(ForeignKey("applications.id"), nullable=False)
    officer_id: Mapped[str] = mapped_column(ForeignKey("officers.id"), nullable=False)
    action: Mapped[str] = mapped_column(String, nullable=False)  # accept|return|reject
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_suggestion: Mapped[str | None] = mapped_column(String, nullable=True)
    agreed_with_ai: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    officer: Mapped["Officer"] = relationship(back_populates="decisions")
    application: Mapped["Application"] = relationship(back_populates="decisions")


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    application_id: Mapped[str] = mapped_column(ForeignKey("applications.id"), nullable=False)
    officer_id: Mapped[str | None] = mapped_column(ForeignKey("officers.id"), nullable=True)
    event: Mapped[str] = mapped_column(String, nullable=False)
    detail: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    application: Mapped["Application"] = relationship(back_populates="audit_events")
