"""
Z-Sentinel Model Configuration.

Controls which fraud prediction model is used by the
application.

Supported models:
    - existing
    - paysim
"""

from __future__ import annotations


SUPPORTED_MODELS = {
    "existing",
    "paysim",
}


DEFAULT_MODEL = "existing"


def normalize_model_name(model_name: str | None) -> str:
    """
    Normalize and validate the requested model name.

    Parameters
    ----------
    model_name:
        Requested model name.

    Returns
    -------
    str
        Normalized model name.

    Raises
    ------
    ValueError
        If the model is unsupported.
    """

    if model_name is None:
        return DEFAULT_MODEL

    normalized = str(
        model_name
    ).strip().lower()

    if normalized not in SUPPORTED_MODELS:
        raise ValueError(
            f"Unsupported model '{model_name}'. "
            f"Supported models: "
            f"{sorted(SUPPORTED_MODELS)}"
        )

    return normalized


def get_default_model() -> str:
    """Return the default fraud prediction model."""

    return DEFAULT_MODEL


if __name__ == "__main__":
    print("=" * 70)
    print("Z-SENTINEL MODEL CONFIGURATION")
    print("=" * 70)

    print(
        f"Default model : {get_default_model()}"
    )

    print(
        f"Supported     : "
        f"{sorted(SUPPORTED_MODELS)}"
    )

    print(
        "\nModel configuration test complete."
    )