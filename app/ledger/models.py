from sqlalchemy import Column, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.ledger_database import LedgerBase


class BlankIDReservation(LedgerBase):
    __tablename__ = "blankid_reservations"

    id = Column(Integer, primary_key=True, index=True)
    blank_id = Column(String, unique=True, index=True, nullable=False)
    relay_domain = Column(String, nullable=False)
    status = Column(String, nullable=False, default="reserved")
    reserved_at = Column(String, nullable=False)

class LedgerBlock(LedgerBase):
    __tablename__ = "ledger_blocks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    network_id: Mapped[str] = mapped_column(String(128), nullable=False)
    block_index: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    round_number: Mapped[int] = mapped_column(Integer, nullable=False)
    previous_block_hash: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[str] = mapped_column(String(64), nullable=False)
    round_result: Mapped[str] = mapped_column(String(64), nullable=False)
    validator_relay_domain: Mapped[str] = mapped_column(String(255), nullable=False)
    block_hash: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    validator_signature_base64: Mapped[str] = mapped_column(Text, nullable=False)
    raw_block_json: Mapped[str] = mapped_column(Text, nullable=False)


class LedgerClaim(LedgerBase):
    __tablename__ = "ledger_claims"
    __table_args__ = (UniqueConstraint("client_claim_hash", name="uq_ledger_claim_hash"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    block_index: Mapped[int] = mapped_column(Integer, nullable=False)
    blank_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    relay_domain: Mapped[str] = mapped_column(String(255), nullable=False)
    identity_key_base64: Mapped[str] = mapped_column(Text, nullable=False)
    identity_signing_public_key_base64: Mapped[str] = mapped_column(Text, nullable=False)
    ownership_signature_base64: Mapped[str] = mapped_column(Text, nullable=False)
    claimed_at: Mapped[str] = mapped_column(String(64), nullable=False)
    nonce: Mapped[str] = mapped_column(String(128), nullable=False)
    client_claim_hash: Mapped[str] = mapped_column(Text, nullable=False)
    relay_signature_base64: Mapped[str] = mapped_column(Text, nullable=False)
    claim_status: Mapped[str] = mapped_column(String(64), nullable=False)


class PendingClaim(LedgerBase):
    __tablename__ = "pending_claims"
    __table_args__ = (UniqueConstraint("client_claim_hash", name="uq_pending_claim_hash"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    blank_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    relay_domain: Mapped[str] = mapped_column(String(255), nullable=False)
    identity_key_base64: Mapped[str] = mapped_column(Text, nullable=False)
    identity_signing_public_key_base64: Mapped[str] = mapped_column(Text, nullable=False)
    ownership_signature_base64: Mapped[str] = mapped_column(Text, nullable=False)
    claimed_at: Mapped[str] = mapped_column(String(64), nullable=False)
    nonce: Mapped[str] = mapped_column(String(128), nullable=False)
    client_claim_hash: Mapped[str] = mapped_column(Text, nullable=False)
    relay_signature_base64: Mapped[str] = mapped_column(Text, nullable=False)
    received_at: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False)


class OwnershipIndex(LedgerBase):
    __tablename__ = "ownership_index"

    blank_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    block_index: Mapped[int] = mapped_column(Integer, nullable=False)
    relay_domain: Mapped[str] = mapped_column(String(255), nullable=False)
    identity_key_base64: Mapped[str] = mapped_column(Text, nullable=False)
    identity_signing_public_key_base64: Mapped[str] = mapped_column(Text, nullable=False)
    ownership_signature_base64: Mapped[str] = mapped_column(Text, nullable=False)
    claimed_at: Mapped[str] = mapped_column(String(64), nullable=False)
    client_claim_hash: Mapped[str] = mapped_column(Text, nullable=False, unique=True)


class ConsensusState(LedgerBase):
    __tablename__ = "consensus_state"

    state_key: Mapped[str] = mapped_column(String(128), primary_key=True)
    state_value: Mapped[str] = mapped_column(Text, nullable=False)


class LedgerCommitSignature(LedgerBase):
    __tablename__ = "ledger_commit_signatures"
    __table_args__ = (UniqueConstraint("block_index", "relay_domain", name="uq_block_relay_signature"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    block_index: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    relay_domain: Mapped[str] = mapped_column(String(255), nullable=False)
    signature_base64: Mapped[str] = mapped_column(Text, nullable=False)

class LedgerProposal(LedgerBase):
    __tablename__ = "ledger_proposals"
    __table_args__ = (UniqueConstraint("proposal_hash", name="uq_ledger_proposal_hash"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    round_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    proposer_relay_domain: Mapped[str] = mapped_column(String(255), nullable=False)
    proposal_hash: Mapped[str] = mapped_column(Text, nullable=False)
    block_index: Mapped[int] = mapped_column(Integer, nullable=False)
    raw_block_json: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False)
