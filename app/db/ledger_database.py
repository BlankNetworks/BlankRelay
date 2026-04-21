from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

LEDGER_DATABASE_URL = "sqlite:///./identity_ledger.db"

ledger_engine = create_engine(
    LEDGER_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

LedgerSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=ledger_engine)

LedgerBase = declarative_base()


def get_ledger_db():
    db = LedgerSessionLocal()
    try:
        yield db
    finally:
        db.close()
