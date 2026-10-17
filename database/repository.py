import json

from database.database import SessionLocal
from database.models import Transaction


def transaction_exists(
    transaction_id: str,
) -> bool:
    """
    Check whether a transaction ID already exists
    in the database.
    """

    with SessionLocal() as session:

        row = (
            session.query(Transaction)
            .filter(
                Transaction.transaction_id
                == str(transaction_id)
            )
            .first()
        )

        return row is not None


def save_result(
    result: dict,
) -> None:
    """
    Save one analyzed transaction result.
    """

    with SessionLocal() as session:

        item = Transaction(
            transaction_id=str(
                result["transaction_id"]
            ),
            account_id=str(
                result.get(
                    "account_id",
                    "",
                )
            ),
            amount=float(
                result.get(
                    "amount",
                    0,
                )
            ),
            risk_score=float(
                result.get(
                    "risk_score",
                    0,
                )
            ),
            decision=str(
                result.get(
                    "decision",
                    "",
                )
            ),
            reasons=json.dumps(
                result.get(
                    "reasons",
                    [],
                )
            ),
        )

        session.add(item)
        session.commit()


def recent_results(
    limit: int = 50,
) -> list[dict]:
    """
    Return the most recent transaction results.
    """

    with SessionLocal() as session:

        rows = (
            session.query(
                Transaction
            )
            .order_by(
                Transaction.created_at.desc()
            )
            .limit(limit)
            .all()
        )

        return [
            {
                "transaction_id":
                    row.transaction_id,

                "account_id":
                    row.account_id,

                "amount":
                    row.amount,

                "risk_score":
                    row.risk_score,

                "decision":
                    row.decision,

                "reasons":
                    json.loads(
                        row.reasons
                    ),

                "created_at":
                    (
                        row.created_at.isoformat()
                        if row.created_at
                        else None
                    ),
            }
            for row in rows
        ]