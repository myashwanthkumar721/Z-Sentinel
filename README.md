# Z-Sentinel
### Real-Time AI-Powered Fraud Detection and Investigation

Z-Sentinel is an AI-powered fraud detection system designed to analyze transaction behavior, identify anomalies, uncover suspicious account relationships, and produce explainable risk decisions. It combines machine-learning predictions, behavioral analysis, network intelligence, and fraud-ring detection to support real-time transaction screening.

The system classifies transactions into three outcomes:

- **ALLOW** — Lower-risk transactions that can proceed.
- **VERIFY** — Transactions requiring additional verification.
- **HOLD** — Higher-risk transactions requiring further review or intervention.

Z-Sentinel has been tested locally on Windows and deployed and validated in an IBM Z LinuxONE environment.

---

## Table of Contents

1. [Problem Statement](#problem-statement)
2. [Key Features](#key-features)
3. [System Architecture](#system-architecture)
4. [Risk Decision Workflow](#risk-decision-workflow)
5. [Technology Stack](#technology-stack)
6. [IBM LinuxONE Implementation and Validation](#ibm-linuxone-implementation-and-validation)
7. [API Documentation](#api-documentation)
8. [Installation](#installation)
9. [Running the Application](#running-the-application)
10. [Testing](#testing)
11. [Project Structure](#project-structure)
12. [Example API Response](#example-api-response)
13. [Limitations and Future Improvements](#limitations-and-future-improvements)
14. [Security Considerations](#security-considerations)
15. [Intended Beneficiaries](#intended-beneficiaries)
16. [Disclaimer](#disclaimer)

---

## 1. Problem Statement

Digital payments and online financial transactions can be exposed to fraudulent activities, abnormal transaction patterns, coordinated account behavior, and suspicious networks of related accounts.

Traditional rule-based systems can struggle to identify complex patterns that evolve across transaction histories and connected accounts. They may also provide limited explanations for why a transaction was flagged.

Z-Sentinel addresses these challenges by combining multiple risk signals into an explainable transaction analysis workflow. The system evaluates transaction characteristics, behavioral anomalies, network relationships, and model predictions to produce a risk score and a recommended decision.

The project is a prototype intended to demonstrate an approach to fraud detection. Its performance and effectiveness in production financial environments require additional evaluation.

---

## 2. Key Features

### Transaction Risk Scoring
Combines available risk signals to calculate a transaction risk score and determine a recommended action.

### Behavioral Anomaly Detection
Analyzes transaction behavior to identify unusual patterns that may warrant additional investigation.

### Machine-Learning Prediction
Supports model-based fraud prediction through the configured model pipeline.

### Network Intelligence
Examines relationships between accounts and transactions to identify potentially suspicious connected activity.

### Fraud-Ring Analysis
Evaluates coordinated patterns and relationships that may indicate a group of related suspicious accounts.

### Explainable Decisions
Returns risk indicators and explanatory reasons to help users understand why a transaction received a particular decision.

### Streaming and Transaction Processing
Includes components for processing transaction events and demonstrating a transaction analysis workflow.

### API Integration
Provides a FastAPI-based interface for health checks and transaction analysis.

### Dashboard
Includes dashboard implementations for viewing and exploring fraud-detection information.

### IBM Z LinuxONE Validation
The application and automated tests have been executed in a LinuxONE environment using the IBM Z `s390x` architecture.

---

## 3. System Architecture

Z-Sentinel uses a modular architecture to separate API handling, transaction processing, feature analysis, detection, network intelligence, and risk decisions.

### High-Level Workflow

```text
Transaction Input
       |
       v
API and Transaction Processing
       |
       v
Transaction Validation and Features
       |
       +--------------------------+
       |             |            |
       v             v            v
  ML Prediction  Anomaly       Network and
                 Detection     Fraud-Ring Analysis
       |             |            |
       +-------------+------------+
                     |
                     v
              Risk Assessment
                     |
                     v
             Explainable Decision
                     |
          +----------+----------+
          |          |          |
          v          v          v
        ALLOW      VERIFY      HOLD
```

The exact signals available to a decision depend on the active model configuration and the transaction data supplied.

### Main Components

- **API layer:** Accepts requests and returns structured results.
- **Data and feature layer:** Validates transaction information and derives analysis features.
- **Detection layer:** Provides model prediction and anomaly-detection components.
- **Network layer:** Analyzes account relationships and suspicious connected activity.
- **Risk layer:** Combines supported risk indicators into a score and decision.
- **Streaming layer:** Provides transaction event-processing components.
- **Dashboard layer:** Provides interfaces for examining fraud-detection results.

---

## 4. Risk Decision Workflow

Z-Sentinel produces a numerical risk score and maps the result to a recommended action.

The documented decision ranges are:

| Risk Score | Decision | Meaning |
|---|---|---|
| 0–39 | ALLOW | Lower-risk transaction |
| 40–69 | VERIFY | Additional verification recommended |
| 70–100 | HOLD | Further review or intervention recommended |

These ranges describe the project's configured decision policy. They should not be interpreted as calibrated probabilities of fraud.

The analysis may include:

- Model-based prediction.
- Behavioral anomaly indicators.
- Network relationship analysis.
- Fraud-ring indicators.
- Explanatory reasons supporting the decision.

A decision is a screening recommendation, not proof that a transaction is fraudulent.

---

## 5. Technology Stack

The project includes the following technologies and components:

- **Language:** Python.
- **API framework:** FastAPI.
- **Data validation:** Pydantic-based request and response schemas.
- **Machine learning:** Configurable prediction components, including an optional XGBoost-based PaySim model path.
- **Analysis:** Behavioral features, anomaly detection, network analysis, and risk scoring.
- **Testing:** pytest.
- **Dashboard:** Python dashboard implementations.
- **Containerization:** Docker and Docker Compose configuration.
- **Version control:** Git and GitHub.
- **Target platform validation:** IBM Z LinuxONE running Ubuntu on `s390x`.

The optional PaySim/XGBoost model has not been successfully validated on the tested LinuxONE environment; see the platform compatibility note below.

---

## 6. IBM LinuxONE Implementation and Validation

Z-Sentinel was deployed and tested in an IBM Z LinuxONE environment to verify that the application could run on the target architecture.

### Validated Environment

| Component | Verified Result |
|---|---|
| Platform architecture | IBM Z / `s390x` |
| Operating system | Ubuntu 24.04.5 LTS |
| Python version | 3.12.3 |
| API health check | Passed |
| Automated tests | 25 passed |
| Synthetic transaction API demonstration | HTTP 200 |

### Validation Activities

The following activities were completed:

1. Deployed the Z-Sentinel application in the LinuxONE environment.
2. Verified the machine architecture using the system's architecture information.
3. Checked the Python runtime version.
4. Started and accessed the FastAPI application.
5. Confirmed that the health endpoint returned a successful response.
6. Executed the automated test suite, with **25 tests passing**.
7. Submitted a synthetic transaction through the API and received a successful HTTP 200 response.
8. Inspected the resulting risk score, model probability, anomaly score, network score, fraud-ring score, and recommended decision.

### Health Check

The following endpoint was verified:

```text
GET /api/health
```

Successful response:

```json
{
  "status": "ok",
  "service": "Z-Sentinel"
}
```

### Synthetic Transaction Demonstration

A controlled synthetic transaction produced the following example results:

| Output | Example Result |
|---|---|
| Transaction amount | 1,250.50 synthetic currency units |
| Risk score | 46.23 |
| Recommended decision | VERIFY |
| Model probability | Approximately 59.08% |
| Anomaly score | 0.578543 |
| Network score | 0.375 |
| Fraud-ring score | 0.625 |

The example transaction was assigned the `VERIFY` decision. The scores demonstrate the API's output for this specific synthetic input; they do not establish real-world fraud-detection accuracy.

### Accessing the API Documentation

When the application is running locally, open:

```text
http://127.0.0.1:8000/docs
```

Health endpoint:

```text
http://127.0.0.1:8000/api/health
```

The local documentation address is accessible from the machine running the application or through a correctly configured SSH tunnel when the application runs remotely.

### LinuxONE Compatibility Note

The existing demo-model configuration and the application's API and automated test suite were validated in the tested LinuxONE environment.

The optional PaySim/XGBoost model could not be loaded on `s390x` because a compatible XGBoost package was unavailable from the configured package index. Consequently, that optional model configuration remains unvalidated on LinuxONE.

Successful execution of the tested application and test suite does not, by itself, establish production readiness, full compatibility of every optional dependency, or real-world fraud-detection accuracy.

---

## 7. API Documentation

Z-Sentinel exposes API endpoints through FastAPI.

### Health Endpoint

```http
GET /api/health
```

Purpose: Checks the application's health and returns its service status.

### Transaction Analysis Endpoint

```http
POST /api/analyze
```

Purpose: Accepts transaction-analysis input and returns the available risk assessment results.

Use the interactive API documentation at `/docs` to inspect the request schema and submit a request matching the current application implementation.

The precise response fields depend on the configured request schema and analysis pipeline.

---

## 8. Installation

### Prerequisites

- Python version compatible with the pinned project dependencies.
- Git.
- A terminal such as PowerShell or Bash.
- Optional: Docker, if using the project's container configuration.

### Clone the Repository

```bash
git clone https://github.com/myashwanthkumar721/Z-Sentinel.git
cd Z-Sentinel
```

### Create a Virtual Environment

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

On Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Install Dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Dependency availability can vary by operating system and CPU architecture. In particular, the optional PaySim/XGBoost configuration may require additional compatibility work on IBM Z `s390x`.

---

## 9. Running the Application

Start the FastAPI application from the project root using the repository's application entry point:

```bash
uvicorn app:app --host 127.0.0.1 --port 8000
```

If the application is running on a remote LinuxONE host, use an SSH tunnel or an appropriately secured network configuration to access it from your development machine.

Once the application is running, open:

```text
http://127.0.0.1:8000/docs
```

Check the health endpoint:

```bash
curl http://127.0.0.1:8000/api/health
```

Use the actual configured model and request schema when testing transaction analysis.

---

## 10. Testing

The project includes automated tests covering several components, including API behavior, configuration, data processing, detection, network analysis, risk scoring, utilities, and fraud-ring logic.

Run the test suite with:

```bash
python -m pytest -q
```

### Recorded Test Results

| Environment | Result |
|---|---|
| Windows development environment | 25 passed |
| IBM Z LinuxONE environment | 25 passed |

The Windows run also reported two dependency deprecation warnings. Those warnings did not cause the tests to fail.

These results represent the test suite available at the time of validation. Future code or dependency changes should be retested.

---

## 11. Project Structure

```text
Z-Sentinel/
├── api/
│   ├── dependencies.py
│   ├── routes.py
│   └── schemas.py
├── config/
│   ├── model_config.py
│   ├── settings.py
│   └── thresholds.py
├── dashboard/
│   ├── dashboard.py
│   └── live_dashboard.py
├── database/
│   ├── database.py
│   ├── models.py
│   └── repository.py
├── docs/
│   ├── evaluation_report.md
│   └── paysim_model_evaluation.md
├── models/
│   ├── feature_columns.json
│   ├── paysim_feature_columns.json
│   └── paysim_model_metrics.json
├── scripts/
│   ├── generate_demo_data.py
│   ├── preprocess_data.py
│   ├── preprocess_paysim.py
│   ├── train_model.py
│   └── train_paysim_model.py
├── src/
│   ├── anomaly/
│   ├── data/
│   ├── detection/
│   ├── features/
│   ├── network/
│   ├── risk/
│   ├── streaming/
│   └── utils/
├── tests/
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── README.md
└── app.py
```

The structure above highlights the main source directories and entry points; additional implementation and test scripts are present in the repository.

---

## 12. Example API Response

The following values summarize the previously validated synthetic demonstration. They are provided to illustrate the result format, not as a guaranteed response for every request.

```json
{
  "risk_score": 46.23,
  "decision": "VERIFY",
  "ml_probability": 0.5907679695,
  "anomaly_score": 0.578543,
  "network_score": 0.375,
  "fraud_ring_score": 0.625
}
```

The exact JSON structure returned by the running API may include additional fields. Use `/docs` to inspect the current response schema.

---

## 13. Limitations and Future Improvements

### Current Limitations

- The demonstrated transaction results use synthetic data.
- Production fraud-detection accuracy has not been established by the example transaction.
- The optional PaySim/XGBoost model could not be loaded in the tested LinuxONE environment.
- Compatibility of every optional model and dependency has not been established across all CPU architectures.
- Production deployment would require further security, performance, operational, and financial-domain validation.

### Future Improvements

- Resolve and test XGBoost compatibility for IBM Z `s390x`.
- Validate model performance on appropriate held-out datasets.
- Measure false-positive and false-negative rates.
- Evaluate latency and throughput under representative transaction loads.
- Improve monitoring, logging, and model-performance reporting.
- Add controlled deployment and integration tests.
- Evaluate secure authentication, authorization, audit trails, and production data handling.
- Conduct further validation on representative hardware and workloads.

---

## 14. Security Considerations

Z-Sentinel is a prototype and should not be deployed directly into a production financial environment without additional review.

Before production use:

- Protect API endpoints with appropriate authentication and authorization.
- Avoid exposing development servers directly to the public internet.
- Keep credentials, tokens, private keys, and environment-specific secrets out of source control.
- Apply access controls and retention policies to transaction data and logs.
- Use encrypted network communication for remote access.
- Validate inputs and monitor operational failures.
- Assess privacy, regulatory, and financial-sector requirements.

The repository's `.env.example` is intended to document placeholder configuration values. Real credentials must be supplied securely outside version control.

---

## 15. Intended Beneficiaries

Potential beneficiaries include:

- Banks and financial institutions.
- Digital payment providers.
- Fintech platforms.
- Fraud investigation and risk operations teams.
- Developers and researchers exploring explainable fraud-detection architectures.

These are intended use cases; suitability for any particular organization would require evaluation and integration.

---

## 16. Disclaimer

Z-Sentinel is a fraud-detection prototype developed for demonstration, experimentation, and evaluation.

Its risk scores and decisions are analytical outputs, not definitive determinations of fraud. Synthetic demonstration results do not establish production effectiveness or financial loss prevention.

IBM LinuxONE validation demonstrates that the tested application configuration and automated tests ran successfully in the specified environment. It does not imply that all optional model configurations are supported or that the system has been certified for production financial services.

---

## Repository

GitHub: https://github.com/myashwanthkumar721/Z-Sentinel