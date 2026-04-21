from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    blank_id: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(128), nullable=False)
    email_address: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    claimed_identity_key_base64: Mapped[str | None] = mapped_column(Text, nullable=True)
    claimed_identity_signing_public_key_base64: Mapped[str | None] = mapped_column(Text, nullable=True)
    claimed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    prekey_bundles = relationship("PrekeyBundle", back_populates="user", cascade="all, delete-orphan")


class PrekeyBundle(Base):
    __tablename__ = "prekey_bundles"
    __table_args__ = (UniqueConstraint("blank_id", "device_id", name="uq_prekey_bundle_blank_device"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    blank_id: Mapped[str] = mapped_column(String(32), ForeignKey("users.blank_id"), index=True, nullable=False)
    device_id: Mapped[str] = mapped_column(String(128), nullable=False)
    identity_key_base64: Mapped[str] = mapped_column(Text, nullable=False)
    identity_signing_public_key_base64: Mapped[str] = mapped_column(Text, nullable=False)
    ownership_signature_base64: Mapped[str | None] = mapped_column(Text, nullable=True)
    signed_prekey_json: Mapped[str] = mapped_column(Text, nullable=False)
    generated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User", back_populates="prekey_bundles")
    one_time_prekeys = relationship("OneTimePrekey", back_populates="bundle", cascade="all, delete-orphan")


class OneTimePrekey(Base):
    __tablename__ = "one_time_prekeys"
    __table_args__ = (UniqueConstraint("blank_id", "device_id", "key_id", name="uq_one_time_prekey_blank_device_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    bundle_id: Mapped[int] = mapped_column(Integer, ForeignKey("prekey_bundles.id", ondelete="CASCADE"), nullable=False, index=True)
    prekey_uuid: Mapped[str] = mapped_column(String(128), nullable=False)
    blank_id: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    device_id: Mapped[str] = mapped_column(String(128), nullable=False)
    key_id: Mapped[int] = mapped_column(Integer, nullable=False)
    public_key_base64: Mapped[str] = mapped_column(Text, nullable=False)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)

    bundle = relationship("PrekeyBundle", back_populates="one_time_prekeys")


class MessageEnvelope(Base):
    __tablename__ = "message_envelopes"
    __table_args__ = (UniqueConstraint("envelope_id", name="uq_message_envelope_envelope_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    envelope_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(64), nullable=False)
    sender_blank_id: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    sender_device_id: Mapped[str] = mapped_column(String(128), nullable=False)
    recipient_blank_id: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    recipient_device_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    conversation_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    timestamp: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    ratchet_header_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    ratchet_header_base64: Mapped[str | None] = mapped_column(Text, nullable=True)
    nonce_base64: Mapped[str | None] = mapped_column(Text, nullable=True)
    ciphertext_base64: Mapped[str] = mapped_column(Text, nullable=False)
    protocol_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_delivered_or_processed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
