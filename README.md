# Z-Sentinel

**AI-assisted real-time fraud detection and risk analysis system.**

Z-Sentinel analyzes financial transactions using multiple complementary signals to identify suspicious activity, evaluate risk, detect coordinated fraud networks, and provide explainable investigation evidence.

---

## Problem

Traditional fraud detection systems can struggle when fraudulent behavior evolves across transactions, devices, IP addresses, and accounts.

Z-Sentinel addresses this by combining:

- Supervised fraud detection
- Behavioral anomaly detection
- Network intelligence
- Coordinated fraud-ring detection
- Velocity and device signals
- Explainable risk scoring
- Real-time transaction processing

---

## Core Pipeline

```text
Transaction
    |
    v
Fraud ML
    |
    v
Anomaly Detection
    |
    v
Network Intelligence
    |
    v
Fraud-Ring Analysis
    |
    v
Risk Engine
    |
    v
Explainability / Investigation
    |
    v
ALLOW / VERIFY / HOLD
```

---

## Solution Overview

Z-Sentinel uses a layered fraud-analysis architecture rather than relying on a single model output.

A transaction is analyzed by the fraud model and behavioral anomaly detector. Network intelligence evaluates relationships between accounts, devices, IP addresses, and merchants. Coordinated activity can be identified through fraud-ring analysis.

The resulting signals are combined by the risk engine into a normalized risk score from 0 to 100. The decision policy maps the score to an operational action:

```text
0 - 39    -> ALLOW
40 - 69   -> VERIFY
70 - 100  -> HOLD
```

The system also generates investigation evidence so analysts can understand the signals contributing to a decision.

---

# Key Features

## 1. Supervised Fraud Detection

Z-Sentinel supports multiple model modes:

- Existing demonstration model
- PaySim-trained fraud model

The prediction layer provides a common interface so the rest of the system can work with different model configurations.

## 2. Behavioral Anomaly Detection

Anomaly detection identifies transaction behavior that differs from expected patterns.

This provides a complementary signal to supervised fraud probability.

## 3. Network Intelligence

Z-Sentinel builds a heterogeneous transaction relationship graph involving:

- Accounts
- Devices
- IP addresses
- Merchants

Example:

```text
Account A ---- Device X ---- Account B
     |                         |
     +------ IP Y -------------+
     |
     +------ Merchant Z -------+
```

## 4. Coordinated Fraud-Ring Detection

Accounts become connected when they share infrastructure such as:

- Device
- IP address
- Merchant

The system identifies connected groups and calculates a fraud-ring score.

## 5. Multi-Signal Risk Engine

| Signal | Weight |
|---|---:|
| ML probability | 35% |
| Anomaly score | 15% |
| Network score | 20% |
| Fraud-ring score | 15% |
| Velocity score | 10% |
| Device score | 5% |
| **Total** | **100%** |

Conceptually:

```text
Final Risk
    =
ML contribution
+ Anomaly contribution
+ Network contribution
+ Fraud-ring contribution
+ Velocity contribution
+ Device contribution
```

## 6. Decision Policy

| Risk Score | Decision | Meaning |
|---:|---|---|
| 0–39 | ALLOW | Low combined risk |
| 40–69 | VERIFY | Additional verification required |
| 70–100 | HOLD | High combined risk |

## 7. Explainable Investigation

Investigation evidence includes:

### Risk Contributions
- ML
- Anomaly
- Network
- Fraud Ring
- Velocity
- Device

### Transaction Evidence
- Transaction amount
- Transactions in the last hour
- Failed attempts
- New-device status
- International activity
- Merchant risk
- IP risk

### Network Evidence
- Network degree
- Network score
- Fraud-ring score
- Connected account count
- Connected accounts

### Decision Evidence
- Final risk score
- Final decision
- Human-readable decision summary

## 8. Real-Time Transaction Streaming

Z-Sentinel includes a transaction stream simulator for controlled real-time demonstrations.

---

# Complete Architecture

```text
                    +----------------------+
                    |     Transaction      |
                    +----------+-----------+
                               |
                               v
                    +----------------------+
                    |   Feature / Input    |
                    |      Processing      |
                    +----------+-----------+
                               |
              +----------------+----------------+
              |                                 |
              v                                 v
     +-------------------+             +-------------------+
     |   Fraud ML Model  |             | Anomaly Detection |
     +---------+---------+             +---------+---------+
               |                                 |
               +----------------+----------------+
                                |
                                v
                    +----------------------+
                    | Network Intelligence |
                    +----------+-----------+
                               |
                               v
                    +----------------------+
                    |  Fraud-Ring Analysis |
                    +----------+-----------+
                               |
                               v
                    +----------------------+
                    |     Risk Engine      |
                    +----------+-----------+
                               |
                               v
                    +----------------------+
                    |   Decision Policy    |
                    +----------+-----------+
                               |
                +--------------+--------------+
                |              |              |
                v              v              v
             ALLOW          VERIFY          HOLD
                |              |              |
                +--------------+--------------+
                               |
                               v
                    +----------------------+
                    | Investigation /      |
                    | Explainability       |
                    +----------+-----------+
                               |
                               v
                    +----------------------+
                    | FastAPI + Dashboard  |
                    +----------------------+
```

---

# Network Intelligence Architecture

```text
                  TRANSACTION
                       |
        +--------------+--------------+
        |              |              |
        v              v              v
     ACCOUNT         DEVICE           IP
        |              |              |
        +--------------+--------------+
                       |
                       v
                    MERCHANT
```

Node identities use:

```text
account:<id>
device:<id>
ip:<address>
merchant:<id>
```

Relationships include:

```text
account -- uses_device   -- device
account -- uses_ip       -- ip
account -- uses_merchant -- merchant
```

---

# Fraud-Ring Logic

```text
Account A
    |
    | shared device / IP / merchant
    |
Account B
    |
    | shared infrastructure
    |
Account C
```

The account graph can look like:

```text
        Account A
        /       \
       /         \
Account B ------- Account C
```

The system reports:

- Connected accounts
- Shared connections
- Account count
- Network density
- Fraud-ring score

---

# Technology Stack

- Python
- FastAPI
- Streamlit
- Scikit-learn
- XGBoost
- Pandas
- NumPy
- NetworkX
- SQLAlchemy
- SQLite
- Plotly
- Docker
- Pytest

---

# Project Structure

```text
Z-Sentinel/
|
├── README.md
├── LICENSE
├── .gitignore
├── requirements.txt
├── .env.example
├── docker-compose.yml
├── Dockerfile
├── app.py
|
├── config/
│   ├── __init__.py
│   ├── settings.py
│   ├── thresholds.py
│   └── model_config.py
|
├── data/
│   ├── raw/
│   ├── processed/
│   └── sample/
|
├── models/
|
├── notebooks/
|
├── src/
│   ├── data/
│   ├── features/
│   ├── detection/
│   ├── anomaly/
│   ├── network/
│   ├── risk/
│   ├── streaming/
│   └── utils/
|
├── api/
├── dashboard/
├── database/
├── tests/
├── scripts/
└── docs/
```

---

# Important Components

### Detection

- Fraud model loading
- Prediction
- Model routing
- PaySim prediction
- Prediction adapter

### Anomaly

Behavioral anomaly detection.

### Network

- Historical network data
- Transaction graph construction
- Account relationships
- Fraud-ring detection

### Risk

- Risk calculation
- Risk contributions
- Decision policy
- Explanation generation
- Investigation evidence

### Streaming

- Transaction simulation
- Controlled demo streams
- Real-time processing

### API

FastAPI service and transaction-analysis endpoints.

### Dashboard

Streamlit security-operations style interface.

---

# Local Setup

```powershell
cd C:\movies\Projects\Z-Sentinel
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

---

# Run the API

```powershell
uvicorn app:app --reload
```

API:

```text
http://127.0.0.1:8000
```

Interactive documentation:

```text
http://127.0.0.1:8000/docs
```

Health endpoint:

```text
http://127.0.0.1:8000/api/health
```

---

# Run the Dashboard

Open a second terminal:

```powershell
cd C:\movies\Projects\Z-Sentinel
.\.venv\Scripts\Activate.ps1
streamlit run dashboard\dashboard.py
```

Dashboard sections include:

- Live Risk Monitor
- Network Intelligence
- Fraud Ring
- Risk Signals
- Investigation Center
- Transaction information
- Decision reasons

---

# Run the Streaming Demo

```powershell
python -m src.streaming.runner --demo
python -m src.streaming.runner --help
```

Available options:

```text
--demo
--interval
--max-transactions
```

---

# Run the Fraud-Ring Demonstration

```powershell
python -m scripts.demo_fraud_ring
```

The controlled demonstration validates:

- Shared-device relationships
- Shared-IP relationships
- Shared-merchant relationships
- Connected-account detection
- Fraud-ring scoring
- Coordinated activity detection

---

# Run Tests

```powershell
python -m pytest -q
```

Validated regression result:

```text
25 passed
2 warnings
```

---

# Data Generation and Model Training

```powershell
python -m scripts.generate_demo_data
python -m scripts.train_model
python -m scripts.train_anomaly_model
python -m scripts.train_paysim_model
```

Scripts should be executed from the project root using module mode.

---

# PaySim Dataset Integration

Z-Sentinel was integrated with the PaySim financial transaction dataset.

Dataset characteristics used during development:

```text
Rows: approximately 6.36 million
Fraud transactions: 8,213
Normal transactions: 6,354,407
Fraud rate: approximately 0.1291%
```

PaySim columns include:

```text
step
type
amount
nameOrig
oldbalanceOrg
newbalanceOrig
nameDest
oldbalanceDest
newbalanceDest
isFraud
isFlaggedFraud
```

The dataset was preprocessed into model-ready features.

---

# PaySim Model

The PaySim model uses XGBoost with a chronological held-out evaluation design.

The robustness audit removed these leakage-like features:

```text
sender_zero_balance_after
sender_balance_error
amount_exceeds_sender_balance
sender_balance_change
sender_balance_after
is_flagged_fraud
```

The final audited model retained 15 features.

---

# PaySim Transaction Types

```text
CASH_IN   -> 0
CASH_OUT  -> 1
DEBIT     -> 2
PAYMENT   -> 3
TRANSFER  -> 4
```

---

# Evaluation & Benchmarking

## Existing Demonstration Model

| Metric | Result |
|---|---:|
| Accuracy | 69.60% |
| Precision | 64.82% |
| Recall | 61.14% |
| F1 Score | 62.93% |
| ROC-AUC | 72.12% |

These results describe the demonstration dataset and model configuration.

## PaySim Held-Out Results

| Metric | Result |
|---|---:|
| Accuracy | 99.99% |
| Precision | 97.63% |
| Recall | 99.76% |
| F1 Score | 98.69% |
| ROC-AUC | 1.0000 |
| PR-AUC | 0.9979 |

These results are on held-out PaySim evaluation data and do not guarantee equivalent performance on real-world financial traffic.

## Confusion Matrix

| | Predicted Normal | Predicted Fraud |
|---|---:|---:|
| Actual Normal | 1,268,167 | 103 |
| Actual Fraud | 10 | 4,244 |

---

# PaySim Threshold Analysis

| Threshold | Precision | Recall |
|---:|---:|---:|
| 0.01 | 99.65% | 100.00% |
| 0.05 | 99.84% | 100.00% |
| 0.10 | 99.91% | 100.00% |
| 0.20 | 99.95% | 100.00% |
| 0.30 | 100.00% | 100.00% |
| 0.40 | 100.00% | 100.00% |
| 0.50 | 100.00% | 100.00% |
| 0.60 | approximately 100.00% | 99.98% |
| 0.70 | approximately 100.00% | 99.98% |
| 0.80 | approximately 100.00% | 99.98% |
| 0.90 | approximately 100.00% | 99.95% |
| 0.95 | approximately 100.00% | 99.95% |

Thresholds can be recalibrated for production according to operational requirements and acceptable false-positive/false-negative trade-offs.

---

# Risk Engine

The final risk score combines six normalized signals:

```text
ML probability      -> 35%
Anomaly score       -> 15%
Network score       -> 20%
Fraud-ring score    -> 15%
Velocity score      -> 10%
Device score        ->  5%
                         ---
                        100%
```

The final score is constrained to the 0–100 range.

---

# Investigation & Explainability

```text
Transaction
     |
     +-------------------+
     |                   |
     v                   v
 ML Probability     Anomaly Score
     |                   |
     +---------+---------+
               |
               v
      Network Intelligence
               |
               v
       Fraud-Ring Analysis
               |
               v
        Risk Contributions
               |
               v
          Risk Score
               |
               v
           Decision
               |
               v
      Investigation Evidence
```

Investigation evidence contains:

```text
risk_contributions
transaction_evidence
network_evidence
decision_summary
risk_score
decision
```

---

# Investigation API Validation

A complete end-to-end transaction was successfully processed through the live API.

The validated response included:

```text
HTTP: 200
Decision: VERIFY
Investigation: True
Transaction Evidence: True
Network Evidence: True
```

One controlled verification also confirmed that the individual risk contributions sum to the final risk score.

---

# API

Primary transaction endpoint:

```text
POST /api/analyze
```

Health endpoint:

```text
GET /api/health
```

The analysis response contains transaction information, risk signals, risk score, decision, and investigation evidence.

---

# API Error Handling

The API handles:

- Invalid request values
- Missing model/resource files
- Duplicate transactions
- HTTP exceptions
- Unexpected server-side failures

Typical categories:

```text
200 -> successful analysis
400 -> invalid request
409 -> duplicate transaction
503 -> required model/resource unavailable
500 -> unexpected server-side error
```

---

# Duplicate Protection

Repeated submission of the same transaction identifier can be rejected rather than processed as a new transaction.

Validation performed during development confirmed:

```text
First request   -> HTTP 200
Immediate repeat -> HTTP 409
```

---

# Model Routing

Supported model modes:

```text
existing
paysim
```

The model router selects the requested model while maintaining a common prediction interface.

---

# Real-Time Architecture

```text
Transaction Simulator
        |
        v
Transaction Processor
        |
        +----------------+
        |                |
        v                v
     ML Model       Anomaly Model
        |                |
        +-------+--------+
                |
                v
       Network Analysis
                |
                v
       Risk Engine
                |
                v
        Decision Engine
                |
                v
       Investigation
```

---

# Fraud-Ring Controlled Demonstration

The controlled scenario uses three accounts with shared infrastructure.

```text
RING-DEMO-01
      |
      | shared infrastructure
      v
RING-DEMO-02
      |
      | shared infrastructure
      v
RING-DEMO-03
```

Validated progression:

```text
Transaction 1
Ring score: 0.0000
Connected accounts: []

Transaction 2
Ring score: 0.1250
Connected accounts: first account

Transaction 3
Ring score: 0.2500
Connected accounts: two accounts
Fraud ring detected: True
```

Final controlled group:

```text
3 accounts
Network density: 1.0
```

Fraud-ring acceptance checks passed.

---

# Streaming Validation

The controlled streaming demonstration uses a mixture of normal and suspicious scenarios.

The simulator is intended for demonstration and testing. Scenario generation is not a substitute for production ground truth.

---

# Automated Regression

The complete automated regression suite has been validated:

```text
25 passed
2 warnings
```

Core areas checked include:

- Data processing
- Model prediction
- Anomaly detection
- Network analysis
- Risk engine
- Fraud-ring detection
- API
- Duplicate protection
- Streaming components

---

# Data Handling

The raw PaySim dataset is intentionally not included in the repository.

Large datasets should be downloaded separately and placed in the appropriate data directory according to the project's data-processing workflow.

Do not commit:

- Large raw datasets
- Sensitive financial information
- Private transaction data

---

# Security

Never commit:

- API keys
- Passwords
- Access tokens
- Private credentials
- `.env` files containing secrets
- Sensitive transaction information

Use `.env.example` as the configuration template where applicable.

Before publishing the project, inspect the repository for secrets and large datasets.

---

# Reproducibility

Use module mode from the project root:

```powershell
python -m pytest -q
python -m scripts.generate_demo_data
python -m scripts.train_model
python -m scripts.train_anomaly_model
python -m scripts.demo_fraud_ring
python -m src.streaming.runner --demo
```

---

# Evaluation Report

Detailed evaluation information is available in:

```text
docs/evaluation_report.md
```

The report contains:

- Existing-model benchmark
- PaySim benchmark
- Confusion matrix
- Threshold analysis
- Risk-weight configuration
- Investigation validation
- Fraud-ring validation
- API validation
- Automated regression
- Model coverage
- Limitations
- Reproducibility notes

---

# Demo Checklist

```text
[ ] Activate .venv
[ ] Start FastAPI
[ ] Confirm /api/health
[ ] Start Streamlit dashboard
[ ] Confirm dashboard connection
[ ] Analyze a transaction
[ ] Show risk score
[ ] Show decision
[ ] Show investigation evidence
[ ] Show network intelligence
[ ] Run coordinated fraud-ring demo
[ ] Show connected accounts
[ ] Show fraud-ring score
[ ] Run streaming demonstration
[ ] Confirm tests pass
```

---

# Recommended Demo Sequence

```text
1. Start the FastAPI backend
          |
          v
2. Open the Streamlit dashboard
          |
          v
3. Show system status
          |
          v
4. Analyze a transaction
          |
          v
5. Show ALLOW / VERIFY / HOLD
          |
          v
6. Open Risk Signals
          |
          v
7. Open Investigation Center
          |
          v
8. Show transaction evidence
          |
          v
9. Show network evidence
          |
          v
10. Run coordinated fraud-ring demo
          |
          v
11. Show connected-account intelligence
          |
          v
12. Show final fraud-ring detection
```

---

# Development Status

## Phases 1–16

Completed:

- Core project foundation
- Data pipeline
- Fraud ML
- Anomaly detection
- Network intelligence
- Risk engine
- Decision and explanation system
- Streaming
- FastAPI integration
- Streamlit dashboard
- PaySim integration
- Model routing
- Fraud-ring detection
- Investigation evidence
- Evaluation and benchmarking

## Phase 17

Final local hackathon packaging includes:

- README finalization
- Documentation consistency
- Security/repository cleanup
- Final API/dashboard/streaming validation
- Demo readiness
- Final project completion check

---

# Limitations

Z-Sentinel is a hackathon and research-oriented prototype.

Important limitations:

1. PaySim is a synthetic financial transaction dataset.
2. Benchmark results do not guarantee equivalent performance on live production traffic.
3. Fraud patterns can change over time.
4. Network detection depends on the quality and availability of historical relationship data.
5. Risk thresholds may require recalibration for production.
6. Real-world deployment would require monitoring and retraining policies.
7. Production use would require appropriate security, privacy, compliance, and operational validation.
8. The system is designed to assist fraud investigation and should not replace appropriate human and organizational controls.

---

# Final System Summary

Z-Sentinel combines transaction-level, behavioral, and network-level evidence to support real-time fraud analysis.

```text
+---------------------+
| Transaction Input   |
+----------+----------+
           |
           v
+---------------------+
| Feature Processing  |
+----------+----------+
           |
           +----------------------+
           |                      |
           v                      v
+----------------+       +-------------------+
| Fraud ML       |       | Anomaly Detection |
+--------+-------+       +---------+---------+
         |                         |
         +------------+------------+
                      |
                      v
             +----------------+
             | Network        |
             | Intelligence   |
             +-------+--------+
                     |
                     v
             +----------------+
             | Fraud-Ring     |
             | Detection      |
             +-------+--------+
                     |
                     v
             +----------------+
             | Risk Engine    |
             +-------+--------+
                     |
                     v
             +----------------+
             | Decision       |
             | Policy         |
             +-------+--------+
                     |
             +-------+-------+
             |       |       |
             v       v       v
           ALLOW   VERIFY   HOLD
             |       |       |
             +-------+-------+
                     |
                     v
             +----------------+
             | Investigation  |
             | Evidence       |
             +-------+--------+
                     |
                     v
             +----------------+
             | API / Dashboard|
             +----------------+
```

---

# What Z-Sentinel Demonstrates

```text
Machine Learning
       +
Behavioral Analysis
       +
Graph / Network Intelligence
       +
Fraud-Ring Detection
       +
Risk Scoring
       +
Explainability
       +
Real-Time Processing
```

Instead of producing only a binary fraud prediction, the system produces a risk score, operational decision, and supporting investigation evidence.

---

# Final Technical Summary

```text
Input
  |
  +--> Supervised ML
  |
  +--> Anomaly Detection
  |
  +--> Network Intelligence
  |
  +--> Fraud-Ring Analysis
  |
  +--> Velocity / Device Signals
  |
  v
Risk Engine
  |
  v
0 - 39   -> ALLOW
40 - 69  -> VERIFY
70 - 100 -> HOLD
  |
  v
Investigation Evidence
  |
  v
FastAPI / Streamlit
```

---

# Disclaimer

Z-Sentinel is a hackathon and research-oriented prototype intended to demonstrate AI-assisted fraud detection concepts.

It is not a production financial fraud prevention system and should not be used for real financial decisions without appropriate validation, security review, compliance controls, monitoring, and human oversight.
