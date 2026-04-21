import requests

from app.ledger.peers import get_peer_relays


def forward_claim_to_peers(claim_payload: dict) -> None:
    for peer in get_peer_relays():
        try:
            requests.post(
                f"{peer}/ledger/claims/forward",
                json=claim_payload,
                timeout=3,
            )
        except Exception:
            pass
