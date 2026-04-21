from datetime import datetime, timezone
from hashlib import sha256
from pydantic import BaseModel, Field, field_validator


def normalize_blank_id(value: str) -> str:
    return value.strip().lower()


def build_claim_hash(
    network_id: str,
    blank_id: str,
    relay_domain: str,
    identity_key_base64: str,
    identity_signing_public_key_base64: str,
    ownership_signature_base64: str,
    claimed_at: str,
    nonce: str,
) -> str:
    canonical = (
        f"networkID:{network_id}"
        f"|blankID:{blank_id}"
        f"|relayDomain:{relay_domain}"
        f"|identityKey:{identity_key_base64}"
        f"|signingKey:{identity_signing_public_key_base64}"
        f"|ownershipSignature:{ownership_signature_base64}"
        f"|claimedAt:{claimed_at}"
        f"|nonce:{nonce}"
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


class LedgerClaimStatusResponse(BaseModel):
    blankID: str
    status: str
    clientClaimHash: str


class LedgerStatusResponse(BaseModel):
    networkID: str
    isSynced: bool
    currentBlockIndex: int
    currentBlockHash: str
    validatorSetVersion: int
    thisRelayDomain: str
    highestPeerBlockIndex: int
    lastSyncCheck: str


class LedgerIDCheckResponse(BaseModel):
    blankID: str
    available: bool
    source: str
    isSynced: bool
    currentBlockIndex: int


class LedgerClaimSubmitRequest(BaseModel):
    blankID: str = Field(min_length=3, max_length=32)
    relayDomain: str = Field(min_length=1, max_length=255)
    identityKeyBase64: str
    identitySigningPublicKeyBase64: str
    ownershipSignatureBase64: str
    claimedAt: str
    nonce: str = Field(min_length=1, max_length=128)
    relaySignatureBase64: str

    @field_validator("blankID")
    @classmethod
    def normalize_blank_id_field(cls, v: str) -> str:
        return normalize_blank_id(v)


class LedgerClaimSubmitResponse(BaseModel):
    success: bool
    status: str
    blankID: str
    clientClaimHash: str
    message: str

def build_block_hash(
    network_id: str,
    block_index: int,
    round_number: int,
    previous_block_hash: str,
    timestamp: str,
    claims_hash: str,
    round_result: str,
    validator_relay_domain: str,
) -> str:
    canonical = (
        f"networkID:{network_id}"
        f"|index:{block_index}"
        f"|round:{round_number}"
        f"|prev:{previous_block_hash}"
        f"|timestamp:{timestamp}"
        f"|claimsHash:{claims_hash}"
        f"|roundResult:{round_result}"
        f"|validator:{validator_relay_domain}"
    )
    return sha256(canonical.encode("utf-8")).hexdigest()
class LedgerVoteRequest(BaseModel):
    blockIndex: int
    relayDomain: str
    signatureBase64: str


class LedgerVoteResponse(BaseModel):
    success: bool
    message: str


class ForwardClaimRequest(BaseModel):
    blankID: str
    relayDomain: str
    identityKeyBase64: str
    identitySigningPublicKeyBase64: str
    ownershipSignatureBase64: str
    claimedAt: str
    nonce: str
    relaySignatureBase64: str


class ForwardClaimResponse(BaseModel):
    success: bool
    message: str

    blockIndex: int
    rawBlock: str


class LedgerProposalRequest(BaseModel):
    roundNumber: int
    proposerRelayDomain: str
    proposalHash: str
    blockIndex: int
    rawBlock: str


class LedgerProposalResponse(BaseModel):
    success: bool
    message: str

class RelayJoinModeRequest(BaseModel):
    enabled: bool


class RelayJoinModeResponse(BaseModel):
    success: bool
    joinModeCurrent: bool
    message: str

class RelayJoinRunResponse(BaseModel):
    success: bool
    joinModeCurrent: bool
    isSyncing: bool
    selectedPeer: str | None
    message: str

class RelayAdmissionStatusResponse(BaseModel):
    relayDomain: str
    readyForJoin: bool
    reason: str
    isSynced: bool
    isSyncing: bool
    joinModeCurrent: bool
    activeSyncClients: int
    maxSyncClients: int
    syncSourceWeight: int
    currentBlockIndex: int

class SyncSlotRequest(BaseModel):
    relayDomain: str


class SyncSlotResponse(BaseModel):
    success: bool
    activeSyncClients: int
    maxSyncClients: int
    message: str
