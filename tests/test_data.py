from src.data.cleaner import (
    clean_transactions,
)

from src.data.generator import (
    generate_transactions,
)

from src.data.validator import (
    validate_transactions,
)


def test_generated_data():

    df = generate_transactions(
        100,
        seed=1,
    )

    assert validate_transactions(
        df,
        require_target=True,
    )

    assert len(df) == 100

    assert df["is_fraud"].nunique() == 2


def test_clean_data():

    df = generate_transactions(
        100,
        seed=1,
    )

    cleaned = clean_transactions(
        df
    )

    assert len(cleaned) == 100
    assert (
        cleaned["amount"] >= 0
    ).all()