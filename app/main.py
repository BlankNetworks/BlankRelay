import base64
import binascii
import json
from datetime import datetime, timezone
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.startup_checks import run_startup_checks
from app.ledger.join_state import get_join_mode

from app.ledger.join_state import set_join_mode
from app.ledger.validator_config import IS_JOIN_MODE

from app.ledger.discovery_service import start_discovery_loop

from app.ledger.sync_state import is_relay_syncing
from app.ledger.validator_config import BLOCK_CLIENT_WRITES_WHILE_SYNCING
from app.ledger.commit_service import start_commit_loop

from app.ledger.routes_validator import router as ledger_validator_router
from app.ledger.sync_service import start_sync_checker
from app.db.ledger_database import LedgerBase, ledger_engine, LedgerSessionLocal
from app.ledger.models import ConsensusState
from app.ledger.routes_public import router as ledger_public_router

from datetime import datetime, timezone
from hashlib import sha256

from app.config import RELAY_DOMAIN
from app.db.ledger_database import LedgerSessionLocal
from app.ledger.models import OwnershipIndex, PendingClaim


from .config import (
    ADMIN_DELETE_TOKEN,
    ALLOW_ID_REUSE_AFTER_DELETE,
    API_KEY,
    CORS_ORIGINS,
    EMAIL_DOMAIN,
)
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from .database import Base, engine, get_db
from .models import MessageEnvelope, OneTimePrekey, PrekeyBundle, User
from .schemas import (
    DeleteUserResponse,
    EnvelopePollResponse,
    EnvelopeResponseItem,
    EnvelopeSendRequest,
    EnvelopeSendResponse,
    IDCheckResponse,
    LoginRequest,
    LoginResponse,
    PrekeyBundleFetchResponse,
    PrekeyBundleResponseBundle,
    PrekeyBundleUploadRequest,
    PrekeyBundleUploadResponse,
    ReceiptRequest,
    ReceiptResponse,
    RegisterRequest,
    RegisterResponse,
)
from .security import hash_password, verify_password

Base.metadata.create_all(bind=engine)

LedgerBase.metadata.create_all(bind=ledger_engine)
run_startup_checks()
ledger_bootstrap_db = LedgerSessionLocal()
try:
    set_join_mode(ledger_bootstrap_db, IS_JOIN_MODE)
    ledger_bootstrap_db.commit()
finally:
    ledger_bootstrap_db.close()

app = FastAPI(title="Blank Relay Backend", version="2.0.0")

app.include_router(ledger_public_router)

app.include_router(ledger_validator_router)

origins = [origin.strip() for origin in CORS_ORIGINS.split(",") if origin.strip()]
if not origins:
    origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def build_registration_claim_hash(
    blank_id: str,
    relay_domain: str,
    identity_key_base64: str,
    identity_signing_public_key_base64: str,
    ownership_signature_base64: str,
    claimed_at: str,
    nonce: str,
) -> str:
    canonical = (
        f"networkID:blankchat-mainnet-v1"
        f"|blankID:{blank_id}"
        f"|relayDomain:{relay_domain}"
        f"|identityKey:{identity_key_base64}"
        f"|signingKey:{identity_signing_public_key_base64}"
        f"|ownershipSignature:{ownership_signature_base64}"
        f"|claimedAt:{claimed_at}"
        f"|nonce:{nonce}"
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


def verify_api_key(request: Request):
    key = request.headers.get("x-api-key")
    if key != API_KEY:
        raise HTTPException(status_code=403, detail="Forbidden")

def build_ownership_payload(
    blank_id: str,
    device_id: str,
    identity_key_base64: str,
    identity_signing_public_key_base64: str,
) -> bytes:
    canonical = (
        f"blankID:{blank_id}"
        f"|deviceID:{device_id}"
        f"|identityKey:{identity_key_base64}"
        f"|signingKey:{identity_signing_public_key_base64}"
    )
    return canonical.encode("utf-8")

def initialize_ledger_defaults():
    start_sync_checker()
    start_commit_loop()
    start_discovery_loop()
    db = LedgerSessionLocal()
    try:
        defaults = {
            "network_id": "blankchat-mainnet-v1",
            "is_synced": "true",
            "current_block_index": "0",
            "current_block_hash": "GENESIS",
            "validator_set_version": "1",
        }
        for key, value in defaults.items():
            existing = db.query(ConsensusState).filter(ConsensusState.state_key == key).first()
            if existing is None:
                db.add(ConsensusState(state_key=key, state_value=value))
        db.commit()
    finally:
        db.close()


initialize_ledger_defaults()

def verify_ownership_signature(
    blank_id: str,
    device_id: str,
    identity_key_base64: str,
    identity_signing_public_key_base64: str,
    ownership_signature_base64: str,
) -> None:
    try:
        public_key_bytes = base64.b64decode(identity_signing_public_key_base64)
        signature_bytes = base64.b64decode(ownership_signature_base64)
    except (binascii.Error, ValueError):
        raise HTTPException(status_code=400, detail="invalid ownership signature encoding")

    # CryptoKit/Swift Crypto public key rawRepresentation is not SPKI/DER.
    # Accept uncompressed SEC1/X9.63 (65 bytes, starts with 0x04),
    # and also accept bare X||Y (64 bytes) by prepending 0x04.
    if len(public_key_bytes) == 64:
        public_key_bytes = b"\x04" + public_key_bytes
    elif len(public_key_bytes) == 65 and public_key_bytes[0] == 0x04:
        pass
    else:
        raise HTTPException(status_code=400, detail="invalid signing public key")

    payload = build_ownership_payload(
        blank_id=blank_id,
        device_id=device_id,
        identity_key_base64=identity_key_base64,
        identity_signing_public_key_base64=identity_signing_public_key_base64,
    )

    try:
        public_key = ec.EllipticCurvePublicKey.from_encoded_point(
            ec.SECP256R1(),
            public_key_bytes,
        )
        public_key.verify(
            signature_bytes,
            payload,
            ec.ECDSA(hashes.SHA256()),
        )
    except InvalidSignature:
        raise HTTPException(status_code=401, detail="invalid ownership signature")
    except ValueError:
        raise HTTPException(status_code=400, detail="invalid signing public key")


def get_active_user_or_404(db: Session, blank_id: str) -> User:
    user = db.query(User).filter(User.blank_id == blank_id, User.is_deleted == False).first()  # noqa: E712
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/api/ids/check", response_model=IDCheckResponse)
def check_blank_id(blankID: str = Query(..., min_length=3, max_length=32), db: Session = Depends(get_db)):
    normalized_blank_id = blankID.strip().lower()
    existing_user = db.query(User).filter(User.blank_id == normalized_blank_id).first()
    available = existing_user is None
    if existing_user and existing_user.is_deleted and ALLOW_ID_REUSE_AFTER_DELETE:
        available = True
    return {"blankID": normalized_blank_id, "available": available}


@app.post("/api/register", response_model=RegisterResponse)
def register_user(payload: RegisterRequest, request: Request, db: Session = Depends(get_db)):
    ledger_db = LedgerSessionLocal()
    try:
        # Relay must be synced to accept registration writes
        ledger_sync = ledger_db.query(PendingClaim).first()  # harmless touch so DB is open

        if BLOCK_CLIENT_WRITES_WHILE_SYNCING and is_relay_syncing(ledger_db):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Relay is syncing and not accepting registration writes yet",
            )

        if get_join_mode(ledger_db):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Relay is in join mode and not accepting registration writes yet",
            )

        ownership = ledger_db.query(OwnershipIndex).filter(OwnershipIndex.blank_id == payload.blankID).first()
        if ownership is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Blank ID is already taken",
            )

        claimed_at = datetime.now(timezone.utc).isoformat()
        client_claim_hash = build_registration_claim_hash(
            blank_id=payload.blankID,
            relay_domain=RELAY_DOMAIN,
            identity_key_base64=payload.identityKeyBase64,
            identity_signing_public_key_base64=payload.identitySigningPublicKeyBase64,
            ownership_signature_base64=payload.ownershipSignatureBase64,
            claimed_at=claimed_at,
            nonce=payload.nonce,
        )

        existing_pending = (
            ledger_db.query(PendingClaim)
            .filter(PendingClaim.blank_id == payload.blankID)
            .first()
        )
        if existing_pending is None:
            pending = PendingClaim(
                blank_id=payload.blankID,
                relay_domain=RELAY_DOMAIN,
                identity_key_base64=payload.identityKeyBase64,
                identity_signing_public_key_base64=payload.identitySigningPublicKeyBase64,
                ownership_signature_base64=payload.ownershipSignatureBase64,
                claimed_at=claimed_at,
                nonce=payload.nonce,
                client_claim_hash=client_claim_hash,
                relay_signature_base64="LOCAL_PENDING_NO_VALIDATOR_SIG_YET",
                received_at=claimed_at,
                status="pending_consensus",
            )
            ledger_db.add(pending)
            ledger_db.commit()

        existing_user = db.query(User).filter(User.blank_id == payload.blankID).first()
        if existing_user is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Blank ID is already taken locally",
            )

        email_address = f"{payload.blankID}@{EMAIL_DOMAIN}"

        new_user = User(
            blank_id=payload.blankID,
            display_name=payload.displayName.strip(),
            email_address=email_address,
            password_hash=hash_password(payload.password),
            is_deleted=False,
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return {
            "success": True,
            "blankID": new_user.blank_id,
            "emailAddress": new_user.email_address,
            "message": "User registered successfully",
        }
    finally:
        ledger_db.close()



@app.post("/api/login", response_model=LoginResponse)
def login_user(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.blank_id == payload.blankID).first()
    if user is None or user.is_deleted:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return {"success": True, "blankID": user.blank_id, "message": "Login successful"}


@app.delete("/api/users/{blankID}", response_model=DeleteUserResponse)
def delete_user(blankID: str, db: Session = Depends(get_db), x_admin_token: str | None = Header(default=None, alias="X-Admin-Token")):
    if x_admin_token != ADMIN_DELETE_TOKEN:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    normalized_blank_id = blankID.strip().lower()
    user = db.query(User).filter(User.blank_id == normalized_blank_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if ALLOW_ID_REUSE_AFTER_DELETE:
        db.delete(user)
        db.commit()
        message = "User deleted and Blank ID released"
    else:
        user.is_deleted = True
        db.commit()
        message = "User deleted and Blank ID remains reserved"
    return {"success": True, "blankID": normalized_blank_id, "message": message}


@app.post("/api/prekeys/upload", response_model=PrekeyBundleUploadResponse)
def upload_prekeys(payload: PrekeyBundleUploadRequest, request: Request, db: Session = Depends(get_db)):
    normalized_blank_id = payload.blankID
    user = get_active_user_or_404(db, normalized_blank_id)

    # Claim-and-lock identity ownership per Blank ID
    if user.claimed_identity_key_base64 is None and user.claimed_identity_signing_public_key_base64 is None:
        verify_ownership_signature(
            blank_id=normalized_blank_id,
            device_id=payload.deviceID,
            identity_key_base64=payload.identityKeyBase64,
            identity_signing_public_key_base64=payload.identitySigningPublicKeyBase64,
            ownership_signature_base64=payload.ownershipSignatureBase64,
        )
        user.claimed_identity_key_base64 = payload.identityKeyBase64
        user.claimed_identity_signing_public_key_base64 = payload.identitySigningPublicKeyBase64
        user.claimed_at = datetime.now(timezone.utc)
    else:
        if payload.identityKeyBase64 != user.claimed_identity_key_base64:
            raise HTTPException(status_code=409, detail="identity mismatch")
        if payload.identitySigningPublicKeyBase64 != user.claimed_identity_signing_public_key_base64:
            raise HTTPException(status_code=409, detail="identity mismatch")

        verify_ownership_signature(
            blank_id=normalized_blank_id,
            device_id=payload.deviceID,
            identity_key_base64=payload.identityKeyBase64,
            identity_signing_public_key_base64=payload.identitySigningPublicKeyBase64,
            ownership_signature_base64=payload.ownershipSignatureBase64,
        )

    bundle = (
        db.query(PrekeyBundle)
        .filter(
            PrekeyBundle.blank_id == normalized_blank_id,
            PrekeyBundle.device_id == payload.deviceID,
        )
        .first()
    )

    signed_prekey_json = json.dumps(
        {
            "id": payload.signedPrekey.id,
            "keyID": payload.signedPrekey.keyID,
            "publicKeyBase64": payload.signedPrekey.publicKeyBase64,
            "signatureBase64": payload.signedPrekey.signatureBase64,
            "createdAt": payload.signedPrekey.createdAt.isoformat().replace("+00:00", "Z"),
        }
    )

    if bundle is None:
        bundle = PrekeyBundle(
            blank_id=normalized_blank_id,
            device_id=payload.deviceID,
            identity_key_base64=payload.identityKeyBase64,
            identity_signing_public_key_base64=payload.identitySigningPublicKeyBase64,
            ownership_signature_base64=payload.ownershipSignatureBase64,
            signed_prekey_json=signed_prekey_json,
            generated_at=payload.generatedAt,
        )
        db.add(bundle)
        db.flush()
    else:
        bundle.identity_key_base64 = payload.identityKeyBase64
        bundle.identity_signing_public_key_base64 = payload.identitySigningPublicKeyBase64
        bundle.ownership_signature_base64 = payload.ownershipSignatureBase64
        bundle.signed_prekey_json = signed_prekey_json
        bundle.generated_at = payload.generatedAt
        db.query(OneTimePrekey).filter(OneTimePrekey.bundle_id == bundle.id).delete()

    for prekey in payload.oneTimePrekeys:
        db.add(
            OneTimePrekey(
                bundle_id=bundle.id,
                prekey_uuid=prekey.id,
                blank_id=normalized_blank_id,
                device_id=payload.deviceID,
                key_id=prekey.keyID,
                public_key_base64=prekey.publicKeyBase64,
                is_used=prekey.isUsed,
                created_at=prekey.createdAt,
            )
        )

    db.commit()

    return {
        "success": True,
        "blankID": normalized_blank_id,
        "deviceID": payload.deviceID,
        "message": "Prekey bundle uploaded successfully",
    }



@app.get("/api/prekeys/{blankID}", response_model=PrekeyBundleFetchResponse)
def fetch_prekeys(blankID: str, request: Request, db: Session = Depends(get_db)):
    normalized_blank_id = blankID.strip().lower()
    get_active_user_or_404(db, normalized_blank_id)

    bundle = (
        db.query(PrekeyBundle)
        .filter(PrekeyBundle.blank_id == normalized_blank_id)
        .order_by(PrekeyBundle.updated_at.desc())
        .first()
    )
    if bundle is None:
        raise HTTPException(status_code=404, detail="Prekey bundle not found")

    signed_prekey = json.loads(bundle.signed_prekey_json)

    unused_prekeys = (
        db.query(OneTimePrekey)
        .filter(
            OneTimePrekey.bundle_id == bundle.id,
            OneTimePrekey.is_used == False,  # noqa: E712
        )
        .order_by(OneTimePrekey.key_id.asc())
        .all()
    )

    bundle_payload = PrekeyBundleResponseBundle(
        blankID=bundle.blank_id,
        deviceID=bundle.device_id,
        identityKeyBase64=bundle.identity_key_base64,
        identitySigningPublicKeyBase64=bundle.identity_signing_public_key_base64,
        ownershipSignatureBase64=bundle.ownership_signature_base64,
        signedPrekey=signed_prekey,
        oneTimePrekeys=[
            {
                "id": prekey.prekey_uuid,
                "keyID": prekey.key_id,
                "publicKeyBase64": prekey.public_key_base64,
                "createdAt": prekey.created_at,
                "isUsed": prekey.is_used,
            }
            for prekey in unused_prekeys
        ],
        generatedAt=bundle.generated_at,
    )

    print("DEBUG_BUNDLE_PAYLOAD", bundle_payload.model_dump())

    return {
        "success": True,
        "blankID": normalized_blank_id,
        "bundle": bundle_payload,
        "message": "Prekey bundle fetched successfully",
    }

@app.post("/api/envelopes/send", response_model=EnvelopeSendResponse)
def send_envelope(payload: EnvelopeSendRequest, request: Request, db: Session = Depends(get_db)):
    envelope = payload.envelope
    get_active_user_or_404(db, envelope.senderBlankID)
    get_active_user_or_404(db, envelope.recipientBlankID)

    existing = db.query(MessageEnvelope).filter(MessageEnvelope.envelope_id == envelope.id).first()
    if existing is not None:
        return {"success": True, "envelopeID": existing.envelope_id, "message": "Envelope queued successfully"}

    db.add(
        MessageEnvelope(
            envelope_id=envelope.id,
            type=envelope.type,
            sender_blank_id=envelope.senderBlankID,
            sender_device_id=envelope.senderDeviceID,
            recipient_blank_id=envelope.recipientBlankID,
            recipient_device_id=envelope.recipientDeviceID,
            conversation_id=envelope.conversationID,
            timestamp=envelope.timestamp,
            ratchet_header_type=envelope.ratchetHeaderType,
            ratchet_header_base64=envelope.ratchetHeaderBase64,
            nonce_base64=envelope.nonceBase64,
            ciphertext_base64=envelope.ciphertextBase64,
            protocol_version=envelope.protocolVersion,
            is_delivered_or_processed=False,
        )
    )
    db.commit()
    return {"success": True, "envelopeID": envelope.id, "message": "Envelope queued successfully"}


@app.get("/api/envelopes/poll", response_model=EnvelopePollResponse)
def poll_envelopes(
    recipientBlankID: str = Query(..., min_length=3, max_length=32),
    request: Request = None,
    db: Session = Depends(get_db),
):
    normalized_blank_id = recipientBlankID.strip().lower()
    get_active_user_or_404(db, normalized_blank_id)

    envelopes = (
        db.query(MessageEnvelope)
        .filter(
            MessageEnvelope.recipient_blank_id == normalized_blank_id,
            MessageEnvelope.is_delivered_or_processed == False,  # noqa: E712
        )
        .order_by(MessageEnvelope.timestamp.asc(), MessageEnvelope.created_at.asc())
        .all()
    )

    return {
        "success": True,
        "recipientBlankID": normalized_blank_id,
        "envelopes": [
            EnvelopeResponseItem(
                id=row.envelope_id,
                type=row.type,
                senderBlankID=row.sender_blank_id,
                senderDeviceID=row.sender_device_id,
                recipientBlankID=row.recipient_blank_id,
                recipientDeviceID=row.recipient_device_id,
                conversationID=row.conversation_id,
                timestamp=row.timestamp,
                ratchetHeaderType=row.ratchet_header_type,
                ratchetHeaderBase64=row.ratchet_header_base64,
                nonceBase64=row.nonce_base64,
                ciphertextBase64=row.ciphertext_base64,
                protocolVersion=row.protocol_version,
            )
            for row in envelopes
        ],
    }


@app.post("/api/envelopes/receipt", response_model=ReceiptResponse)
def process_receipt(payload: ReceiptRequest, request: Request, db: Session = Depends(get_db)):
    get_active_user_or_404(db, payload.recipientBlankID)

    matched = (
        db.query(MessageEnvelope)
        .filter(
            MessageEnvelope.recipient_blank_id == payload.recipientBlankID,
            MessageEnvelope.envelope_id.in_(payload.envelopeIDs),
            MessageEnvelope.is_delivered_or_processed == False,  # noqa: E712
        )
        .all()
    )
    processed_count = len(matched)
    for row in matched:
        row.is_delivered_or_processed = True
    db.commit()
    return {"success": True, "processedCount": processed_count, "message": "Receipts processed successfully"}
