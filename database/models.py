from datetime import datetime, timezone

from sqlalchemy import (
    DateTime,
    Float,
    String,
    Text,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from database.database import Base


class Transaction(Base):

    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    transaction_id: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
    )

    account_id: Mapped[str] = mapped_column(
        String(64),
        index=True,
    )

    amount: Mapped[float] = mapped_column(
        Float
    )

    risk_score: Mapped[float] = mapped_column(
        Float
    )

    decision: Mapped[str] = mapped_column(
        String(20)
    )

    reasons: Mapped[str] = mapped_column(
        Text
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(
            timezone.utc
        ),
    )