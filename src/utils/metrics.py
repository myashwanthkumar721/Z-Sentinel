from typing import Any

from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


def classification_metrics(
    y_true,
    y_pred,
    y_probability=None,
) -> dict[str, Any]:

    result = {
        "accuracy": float(
            accuracy_score(y_true, y_pred)
        ),
        "precision": float(
            precision_score(
                y_true,
                y_pred,
                zero_division=0,
            )
        ),
        "recall": float(
            recall_score(
                y_true,
                y_pred,
                zero_division=0,
            )
        ),
        "f1": float(
            f1_score(
                y_true,
                y_pred,
                zero_division=0,
            )
        ),
    }

    if y_probability is not None:
        try:
            result["roc_auc"] = float(
                roc_auc_score(
                    y_true,
                    y_probability,
                )
            )
        except ValueError:
            result["roc_auc"] = None

    return result