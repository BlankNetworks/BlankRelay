from fastapi import Header, HTTPException, status

from app.config import ADMIN_DELETE_TOKEN


def require_ledger_admin(x_admin_token: str | None = Header(default=None, alias="X-Admin-Token")):
    if not ADMIN_DELETE_TOKEN or x_admin_token != ADMIN_DELETE_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid or missing admin token",
        )
