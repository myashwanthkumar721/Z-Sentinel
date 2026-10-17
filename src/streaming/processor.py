"""
Real-time transaction processor for Z-Sentinel.

Connects incoming transaction events to the existing
ML, anomaly, network, coordinated fraud-ring and
decision-policy engines.

The ML prediction layer can use either:
    - the existing Z-Sentinel fraud model
    - the PaySim fraud model

The existing model remains the default.
"""

from __future__ import annotations

import joblib
import pandas as pd

from config.settings import settings

from src.anomaly.detector import anomaly_score
from src.detection.model_loader import load_fraud_model
from src.detection.model_router import predict_transaction

from src.network.graph_builder import (
    build_transaction_graph,
)

from src.network.history import (
    load_network_history,
    save_network_transaction,
)

from src.network.network_analysis import (
    account_network_degree,
    calculate_network_signal_from_degree,
)

from src.network.fraud_rings import (
    find_connected_accounts,
    calculate_fraud_ring_score,
)

from src.risk.risk_engine import evaluate_risk
from src.risk.decision_engine import apply_decision_policy


class TransactionProcessor:
    """
    Process individual transactions through the
    complete Z-Sentinel detection pipeline.
    """

    def __init__(
        self,
        model_dir=None,
        model_name: str = "existing",
    ) -> None:

        if model_dir is None:
            model_dir = settings.model_dir

        self.model_dir = model_dir

        # ----------------------------------------------------
        # Selected fraud prediction model
        # ----------------------------------------------------

        self.model_name = str(
            model_name
        ).strip().lower()

        if self.model_name not in {
            "existing",
            "paysim",
        }:
            raise ValueError(
                "Unsupported model_name: "
                f"{model_name}. "
                "Supported models: "
                "existing, paysim"
            )

        # ----------------------------------------------------
        # Load supervised fraud model
        #
        # Only the existing model needs to be loaded here.
        # PaySim is loaded lazily by its predictor.
        # ----------------------------------------------------

        self.fraud_model = None

        if self.model_name == "existing":
            self.fraud_model = load_fraud_model(
                self.model_dir
            )

        # ----------------------------------------------------
        # Load anomaly detection model
        # ----------------------------------------------------

        anomaly_model_path = (
            self.model_dir
            / "anomaly_model.pkl"
        )

        if not anomaly_model_path.exists():
            raise FileNotFoundError(
                "Anomaly model not found: "
                f"{anomaly_model_path}"
            )

        self.anomaly_model = joblib.load(
            anomaly_model_path
        )

    # ========================================================
    # MODEL CONFIGURATION
    # ========================================================

    def get_model_name(self) -> str:
        """Return the currently selected fraud model."""

        return self.model_name

    def set_model(
        self,
        model_name: str,
    ) -> None:
        """
        Change the fraud prediction model.

        Supported models:
            - existing
            - paysim

        The existing model is loaded only when selected.
        """

        selected_model = str(
            model_name
        ).strip().lower()

        if selected_model not in {
            "existing",
            "paysim",
        }:
            raise ValueError(
                "Unsupported model_name: "
                f"{model_name}. "
                "Supported models: "
                "existing, paysim"
            )

        if selected_model == "existing":
            if self.fraud_model is None:
                self.fraud_model = load_fraud_model(
                    self.model_dir
                )

        self.model_name = selected_model

    # ========================================================
    # NETWORK INTELLIGENCE
    # ========================================================

    def _build_current_graph(
        self,
        transaction: dict,
    ):
        """
        Build the network graph containing historical
        transactions plus the current transaction.
        """

        history = load_network_history()

        current_record = pd.DataFrame(
            [
                {
                    "account_id":
                        transaction["account_id"],

                    "device_id":
                        transaction["device_id"],

                    "ip_address":
                        transaction["ip_address"],

                    "merchant_id":
                        transaction["merchant_id"],
                }
            ]
        )

        if history.empty:

            combined = current_record

        else:

            historical_columns = [
                "account_id",
                "device_id",
                "ip_address",
                "merchant_id",
            ]

            combined = pd.concat(
                [
                    history[
                        historical_columns
                    ],
                    current_record,
                ],
                ignore_index=True,
            )

        return build_transaction_graph(
            combined
        )

    def _calculate_network_signal(
        self,
        transaction: dict,
    ) -> tuple[int, int, float]:
        """
        Calculate network intelligence using actual
        historical relationships.
        """

        account_id = str(
            transaction["account_id"]
        )

        history = load_network_history()

        if history.empty:

            historical_graph = build_transaction_graph(
                pd.DataFrame(
                    columns=[
                        "account_id",
                        "device_id",
                        "ip_address",
                        "merchant_id",
                    ]
                )
            )

        else:

            historical_graph = build_transaction_graph(
                history[
                    [
                        "account_id",
                        "device_id",
                        "ip_address",
                        "merchant_id",
                    ]
                ]
            )

        previous_degree = account_network_degree(
            historical_graph,
            account_id,
        )

        current_graph = self._build_current_graph(
            transaction
        )

        current_degree = account_network_degree(
            current_graph,
            account_id,
        )

        network_score = (
            calculate_network_signal_from_degree(
                current_degree
            )
        )

        return (
            int(previous_degree),
            int(current_degree),
            float(network_score),
        )

    # ========================================================
    # FRAUD-RING INTELLIGENCE
    # ========================================================

    def _calculate_fraud_ring_signal(
        self,
        transaction: dict,
    ) -> tuple[float, list[dict]]:
        """
        Calculate coordinated fraud-ring risk for the
        current account.

        Returns:
            fraud_ring_score
            connected_accounts
        """

        graph = self._build_current_graph(
            transaction
        )

        account_id = str(
            transaction["account_id"]
        )

        connected_accounts = (
            find_connected_accounts(
                graph,
                account_id,
            )
        )

        fraud_ring_score = (
            calculate_fraud_ring_score(
                graph,
                account_id,
            )
        )

        return (
            float(fraud_ring_score),
            connected_accounts,
        )

    # ========================================================
    # MAIN PROCESSOR
    # ========================================================

    def process(
        self,
        transaction: dict,
        save_history: bool = True,
    ) -> dict:
        """
        Process one transaction through the complete
        Z-Sentinel intelligence pipeline.
        """

        # ----------------------------------------------------
        # 1. ML fraud probability
        # ----------------------------------------------------

        prediction = predict_transaction(
            transaction=transaction,
            model=self.model_name,
            existing_model=self.fraud_model,
        )

        ml_probability = float(
            prediction["ml_probability"]
        )

        prediction_model = prediction.get(
            "model",
            self.model_name,
        )

        prediction_source = prediction.get(
            "prediction_source",
            self.model_name,
        )

        # ----------------------------------------------------
        # 2. Behavioral anomaly
        # ----------------------------------------------------

        anomaly = anomaly_score(
            self.anomaly_model,
            transaction,
        )

        # ----------------------------------------------------
        # 3. Network intelligence
        # ----------------------------------------------------

        (
            previous_degree,
            current_degree,
            network,
        ) = self._calculate_network_signal(
            transaction
        )

        # ----------------------------------------------------
        # 4. Coordinated fraud-ring intelligence
        # ----------------------------------------------------

        (
            fraud_ring_score,
            connected_accounts,
        ) = self._calculate_fraud_ring_signal(
            transaction
        )

        # ----------------------------------------------------
        # 5. Weighted risk engine
        # ----------------------------------------------------

        risk_result = evaluate_risk(
            transaction,
            ml_probability,
            anomaly,
            network,
            fraud_ring_score,
            current_degree,
            connected_accounts,
        )

        # ----------------------------------------------------
        # 6. Decision policy
        #
        # The risk engine produces the base decision.
        # The decision engine applies high-confidence
        # ML safety policies without changing the
        # underlying weighted risk calculation.
        # ----------------------------------------------------

        base_decision = risk_result["decision"]

        final_decision = apply_decision_policy(
            base_decision=base_decision,
            ml_probability=ml_probability,
        )

        # Preserve both decisions for transparency.
        risk_result["base_decision"] = base_decision
        risk_result["decision"] = final_decision

        # ----------------------------------------------------
        # 7. Persist transaction
        # ----------------------------------------------------

        if save_history:

            save_network_transaction(
                transaction
            )

        # ----------------------------------------------------
        # 8. Fraud-ring status
        # ----------------------------------------------------

        fraud_ring_detected = (
            len(connected_accounts) >= 2
        )

        # ----------------------------------------------------
        # 9. Return complete intelligence
        # ----------------------------------------------------

        return {
            "transaction":
                transaction,

            "ml_probability":
                float(
                    ml_probability
                ),

            "prediction_model":
                prediction_model,

            "prediction_source":
                prediction_source,

            "model_name":
                self.model_name,

            "anomaly_score":
                float(
                    anomaly
                ),

            "previous_network_degree":
                int(
                    previous_degree
                ),

            "network_degree":
                int(
                    current_degree
                ),

            "network_score":
                float(
                    network
                ),

            "fraud_ring_score":
                float(
                    fraud_ring_score
                ),

            "fraud_ring_detected":
                bool(
                    fraud_ring_detected
                ),

            "connected_accounts":
                connected_accounts,

            "risk_score":
                float(
                    risk_result[
                        "risk_score"
                    ]
                ),

            "decision":
                final_decision,

            "base_decision":
                base_decision,

            "reasons":
                risk_result.get(
                    "reasons",
                    [],
                ),

            "signals":
                risk_result.get(
                    "signals",
                    {},
                ),

            "risk_result":
                risk_result,
        }