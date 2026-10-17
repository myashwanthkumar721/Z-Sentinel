"""
Z-Sentinel Decision Engine

Applies policy rules after the weighted risk engine produces
a base decision.

Architecture:

    ML / Anomaly / Network / Fraud Ring / Context
                       |
                       v
                Risk Engine
                       |
                 Base Decision
                       |
                       v
               Decision Engine
                       |
              Final Decision
"""


def apply_decision_policy(
    base_decision: str,
    ml_probability: float,
) -> str:
    """
    Apply decision-level safety policies.

    Current policy:
        - ML probability >= 0.90 cannot remain ALLOW.
        - It is upgraded to VERIFY.
        - Existing VERIFY/HOLD decisions are preserved.

    Parameters
    ----------
    base_decision:
        Decision returned by the weighted risk engine.

    ml_probability:
        Fraud probability returned by the ML model.

    Returns
    -------
    str
        Final decision: ALLOW, VERIFY, or HOLD.
    """

    decision = str(base_decision).upper().strip()

    probability = max(
        0.0,
        min(1.0, float(ml_probability)),
    )

    # Never downgrade an existing high-risk decision.
    if decision in {"VERIFY", "HOLD"}:
        return decision

    # Very high ML confidence prevents ALLOW.
    if probability >= 0.90:
        return "VERIFY"

    return "ALLOW"


if __name__ == "__main__":
    print("Z-Sentinel Decision Engine")
    print("-" * 40)

    test_cases = [
        ("ALLOW", 0.50),
        ("ALLOW", 0.89),
        ("ALLOW", 0.90),
        ("ALLOW", 0.99),
        ("VERIFY", 0.20),
        ("HOLD", 0.10),
    ]

    for base_decision, probability in test_cases:
        final_decision = apply_decision_policy(
            base_decision=base_decision,
            ml_probability=probability,
        )

        print(
            f"Base={base_decision:<7} "
            f"ML={probability:.2f} "
            f"-> Final={final_decision}"
        )