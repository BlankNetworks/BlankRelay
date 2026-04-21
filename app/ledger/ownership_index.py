import json

from sqlalchemy.orm import Session

from app.ledger.models import LedgerBlock, LedgerClaim, OwnershipIndex


def rebuild_ownership_index(db: Session) -> None:
    db.query(OwnershipIndex).delete()

    committed_claims = (
        db.query(LedgerClaim)
        .filter(LedgerClaim.claim_status == "committed")
        .order_by(LedgerClaim.block_index.asc(), LedgerClaim.id.asc())
        .all()
    )

    for claim in committed_claims:
        existing = db.query(OwnershipIndex).filter(OwnershipIndex.blank_id == claim.blank_id).first()
        if existing is None:
            db.add(
                OwnershipIndex(
                    blank_id=claim.blank_id,
                    block_index=claim.block_index,
                    relay_domain=claim.relay_domain,
                    identity_key_base64=claim.identity_key_base64,
                    identity_signing_public_key_base64=claim.identity_signing_public_key_base64,
                    ownership_signature_base64=claim.ownership_signature_base64,
                    claimed_at=claim.claimed_at,
                    client_claim_hash=claim.client_claim_hash,
                )
            )

    db.commit()
