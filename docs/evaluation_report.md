# Z-Sentinel — Evaluation & Benchmark Report

## 1. Overview

Z-Sentinel is an AI-assisted real-time fraud detection and risk analysis
system designed to combine multiple signals before making a transaction
decision.

The evaluation covers:

- Supervised fraud detection
- PaySim fraud detection
- Threshold analysis
- Risk scoring
- Network intelligence
- Coordinated fraud-ring detection
- Explainable investigation evidence

The results below are benchmark results from the project's available
datasets and controlled validation scenarios. They should not be interpreted
as guarantees of production or real-world fraud detection performance.

---

## 2. Existing Demo Model

The existing Z-Sentinel demonstration model was evaluated using the project's
demo transaction dataset.

### Metrics

| Metric | Result |
|---|---:|
| Accuracy | 69.60% |
| Precision | 64.82% |
| Recall | 61.14% |
| F1 Score | 62.93% |
| ROC-AUC | 72.12% |

These results represent the existing demonstration dataset and model
configuration.

---

## 3. PaySim Evaluation

Z-Sentinel was additionally evaluated using the PaySim transaction dataset.

The PaySim evaluation used a chronological train/held-out split.

A robustness audit removed features identified as leakage-like before the
final benchmark:

- `sender_zero_balance_after`
- `sender_balance_error`
- `amount_exceeds_sender_balance`
- `sender_balance_change`
- `sender_balance_after`
- `is_flagged_fraud`

The final PaySim model used the retained 15-feature set.

### Held-Out Results

| Metric | Result |
|---|---:|
| Accuracy | 99.99% |
| Precision | 97.63% |
| Recall | 99.76% |
| F1 Score | 98.69% |
| ROC-AUC | 1.0000 |
| PR-AUC | 0.9979 |

### Confusion Matrix

| | Predicted Normal | Predicted Fraud |
|---|---:|---:|
| Actual Normal | 1,268,167 | 103 |
| Actual Fraud | 10 | 4,244 |

These results are specific to the held-out PaySim evaluation data and should
not be generalized directly to real-world production traffic.

---

## 4. Threshold Analysis

The PaySim model was evaluated across multiple probability thresholds.

| Threshold | Precision | Recall |
|---:|---:|---:|
| 0.01 | 99.65% | 100.00% |
| 0.05 | 99.84% | 100.00% |
| 0.10 | 99.91% | 100.00% |
| 0.20 | 99.95% | 100.00% |
| 0.30 | 100.00% | 100.00% |
| 0.40 | 100.00% | 100.00% |
| 0.50 | 100.00% | 100.00% |
| 0.60 | ~100.00% | 99.98% |
| 0.70 | ~100.00% | 99.98% |
| 0.80 | ~100.00% | 99.98% |
| 0.90 | ~100.00% | 99.95% |
| 0.95 | ~100.00% | 99.95% |

The threshold analysis demonstrates how the fraud probability threshold can
be varied depending on the desired precision/recall trade-off.

---

## 5. Multi-Signal Risk Engine

Z-Sentinel does not rely exclusively on the supervised ML probability.

The final risk score combines:

| Signal | Weight |
|---|---:|
| ML probability | 35% |
| Anomaly score | 15% |
| Network score | 20% |
| Fraud-ring score | 15% |
| Velocity score | 10% |
| Device score | 5% |

Total:

**100%**

The resulting risk score is mapped to three operational decision bands:

| Risk Score | Decision |
|---:|---|
| 0–39 | ALLOW |
| 40–69 | VERIFY |
| 70–100 | HOLD |

This enables the system to combine transaction-level and network-level
evidence rather than depending on a single model output.

---

## 6. Investigation Evidence

The investigation pipeline exposes the evidence behind each risk decision.

### Risk Contributions

The API provides the contribution of each major signal:

- ML
- Anomaly
- Network
- Fraud Ring
- Velocity
- Device

### Transaction Evidence

The investigation response can include:

- Transaction amount
- Transactions in the last hour
- Failed attempts
- New-device status
- International transaction status
- Merchant risk
- IP risk

### Network Evidence

The investigation response can include:

- Network degree
- Network score
- Fraud-ring score
- Connected account count
- Connected accounts

This information is surfaced in the dashboard Investigation Center.

---

## 7. Controlled Investigation Validation

An end-to-end investigation request was successfully processed through the
live API.

### Validation Result

```text
HTTP: 200
Decision: VERIFY
Risk Score: 59.01
Investigation: True
Transaction Evidence: True
Network Evidence: True