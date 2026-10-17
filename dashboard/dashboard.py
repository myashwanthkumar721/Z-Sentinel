import html
import json
import uuid
from datetime import datetime

import pandas as pd
import requests
import streamlit as st

from config.settings import settings
from database.database import init_db
from database.repository import recent_results
from src.network.graph_builder import build_transaction_graph
from src.network.fraud_rings import (
    calculate_fraud_ring_score,
    find_connected_accounts,
)
from src.network.history import (
    build_historical_network,
    clear_network_history,
    load_network_history,
)
from src.network.network_analysis import (
    account_network_degree,
    calculate_network_signal_from_degree,
)
from src.network.suspicious_networks import (
    account_relationships,
    find_suspicious_accounts,
)

API_URL = "http://127.0.0.1:8000"

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Z-Sentinel | Fraud Intelligence",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================================================
# PREMIUM SOC / FRAUD INTELLIGENCE THEME
# ============================================================

st.markdown(
    r'''
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
    --bg:#050b14;
    --panel:#0a1422;
    --panel2:#0d1a2b;
    --border:rgba(148,163,184,.12);
    --text:#f5f8fc;
    --muted:#8295ad;
    --blue:#48a7ff;
    --cyan:#53d8ff;
    --green:#43dfa0;
    --amber:#ffb15f;
    --red:#ff667d;
}

html, body, [class*="css"] { font-family:Inter,sans-serif; }
.stApp {
    background:
      radial-gradient(circle at 4% -5%,rgba(39,132,255,.18),transparent 27%),
      radial-gradient(circle at 96% 3%,rgba(67,215,255,.11),transparent 25%),
      linear-gradient(145deg,#050b14 0%,#07111f 48%,#050b14 100%);
    color:var(--text);
}
[data-testid="stHeader"] { background:transparent; }
[data-testid="stToolbar"] { visibility:hidden; }
.block-container { max-width:1480px; padding-top:1.25rem; padding-bottom:2.2rem; }

/* ---------- Hero ---------- */
.zs-hero {
    position:relative; overflow:hidden; padding:22px 26px; margin-bottom:14px;
    border:1px solid rgba(72,167,255,.18); border-radius:22px;
    background:linear-gradient(135deg,rgba(13,34,58,.97),rgba(7,17,30,.93));
    box-shadow:0 20px 65px rgba(0,0,0,.28),inset 0 1px 0 rgba(255,255,255,.035);
}
.zs-hero:before { content:""; position:absolute; width:380px;height:380px;right:-150px;top:-210px;border-radius:50%;background:rgba(83,216,255,.07); }
.zs-brand { display:flex;align-items:center;gap:14px;position:relative;z-index:2; }
.zs-shield { width:52px;height:52px;display:grid;place-items:center;border-radius:16px;font-size:27px;background:linear-gradient(145deg,rgba(72,167,255,.24),rgba(83,216,255,.08));border:1px solid rgba(72,167,255,.3);box-shadow:0 10px 30px rgba(35,130,255,.15); }
.zs-title { font-size:31px;font-weight:800;letter-spacing:-1.1px;line-height:1; }
.zs-subtitle { color:var(--muted);font-size:12px;margin-top:6px; }
.zs-live { display:inline-flex;align-items:center;gap:7px;padding:7px 12px;border-radius:999px;background:rgba(67,223,160,.08);border:1px solid rgba(67,223,160,.2);color:#8af0c7;font-size:11px;font-weight:800; }
.zs-dot { width:7px;height:7px;border-radius:50%;background:var(--green);box-shadow:0 0 13px rgba(67,223,160,.9); }

/* ---------- KPI strip ---------- */
.zs-kpis { display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:14px; }
.zs-kpi { min-height:82px;padding:14px 16px;border:1px solid var(--border);border-radius:17px;background:linear-gradient(145deg,rgba(13,27,45,.9),rgba(7,16,28,.82));box-shadow:0 12px 30px rgba(0,0,0,.14); }
.zs-kpi-label { color:#7187a3;font-size:9px;font-weight:800;letter-spacing:1.1px;text-transform:uppercase; }
.zs-kpi-value { margin-top:6px;font-size:21px;font-weight:800;letter-spacing:-.5px; }
.zs-kpi-meta { color:#667b95;font-size:9px;margin-top:3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis; }
.zs-kpi-green { border-color:rgba(67,223,160,.17); }
.zs-kpi-blue { border-color:rgba(72,167,255,.17); }
.zs-kpi-amber { border-color:rgba(255,177,95,.17); }

/* ---------- Panels ---------- */
.zs-panel { border:1px solid var(--border);border-radius:18px;background:linear-gradient(145deg,rgba(13,27,45,.82),rgba(7,16,28,.72));padding:17px 18px;box-shadow:0 15px 42px rgba(0,0,0,.16); }
.zs-panel-title { font-size:15px;font-weight:800;letter-spacing:-.2px; }
.zs-panel-sub { color:#70849d;font-size:10px;margin-top:4px;margin-bottom:13px; }
.zs-label { color:#7187a3;font-size:9px;font-weight:800;letter-spacing:1.1px;text-transform:uppercase;margin-bottom:6px; }

/* ---------- Inputs ---------- */
div[data-baseweb="select"] > div, div[data-baseweb="input"] > div { background:rgba(5,13,23,.82)!important;border-color:rgba(148,163,184,.12)!important;border-radius:10px!important; }
.stNumberInput input, .stTextInput input { color:#f5f8fc!important; }
.stSlider [data-baseweb="slider"] { margin-top:-4px; }
.stButton > button { min-height:45px;border-radius:11px!important;font-weight:800!important;border:1px solid rgba(72,167,255,.28)!important;background:linear-gradient(135deg,#2378df,#269bd5)!important;box-shadow:0 9px 27px rgba(38,155,213,.18)!important; }
.stButton > button:hover { transform:translateY(-1px);box-shadow:0 13px 34px rgba(38,155,213,.27)!important; }

/* ---------- Custom result cards ---------- */
.zs-risk-panel { padding:18px;border-radius:18px;border:1px solid rgba(72,167,255,.15);background:linear-gradient(145deg,rgba(13,31,52,.96),rgba(7,16,28,.9)); }
.zs-risk-top { display:flex;justify-content:space-between;align-items:flex-start;gap:12px; }
.zs-risk-number { font-size:40px;font-weight:800;letter-spacing:-2px;line-height:1; }
.zs-risk-label { color:#70849d;font-size:9px;font-weight:800;letter-spacing:1.1px;text-transform:uppercase;margin-bottom:6px; }
.zs-decision { padding:8px 12px;border-radius:10px;font-size:13px;font-weight:800;white-space:nowrap; }
.zs-allow { color:#8af0c7;background:rgba(67,223,160,.09);border:1px solid rgba(67,223,160,.2); }
.zs-verify { color:#ffc58c;background:rgba(255,177,95,.09);border:1px solid rgba(255,177,95,.2); }
.zs-hold { color:#ff98a6;background:rgba(255,102,125,.09);border:1px solid rgba(255,102,125,.2); }
.zs-risk-meter { height:7px;border-radius:999px;background:#17273a;overflow:hidden;margin:14px 0 7px; }
.zs-risk-fill { height:100%;border-radius:999px;background:linear-gradient(90deg,#43dfa0,#48a7ff,#ffb15f,#ff667d); }
.zs-meter-caption { color:#70849d;font-size:10px; }
.zs-mini-grid { display:grid;grid-template-columns:repeat(2,1fr);gap:8px;margin-top:14px; }
.zs-mini { padding:10px;border:1px solid rgba(148,163,184,.09);border-radius:11px;background:rgba(4,11,19,.36); }
.zs-mini-label { color:#70849d;font-size:9px; }
.zs-mini-value { font-size:16px;font-weight:800;margin-top:3px; }

/* ---------- Decision feed ---------- */
.zs-feed-row { display:grid;grid-template-columns:1.45fr .8fr .55fr .65fr;gap:8px;align-items:center;padding:9px 10px;border-bottom:1px solid rgba(148,163,184,.07);font-size:10px; }
.zs-feed-row:last-child { border-bottom:0; }
.zs-feed-head { color:#7187a3;font-size:8px;font-weight:800;letter-spacing:.9px;text-transform:uppercase; }
.zs-feed-id { color:#dbe7f5;font-weight:700;overflow:hidden;text-overflow:ellipsis;white-space:nowrap; }
.zs-feed-account { color:#8195ad;overflow:hidden;text-overflow:ellipsis;white-space:nowrap; }
.zs-feed-risk { font-weight:800; }
.zs-decision-pill { display:inline-flex;align-items:center;justify-content:center;padding:4px 7px;border-radius:999px;font-size:8px;font-weight:800; }

/* ---------- Investigation ---------- */
.zs-invest-grid { display:grid;grid-template-columns:repeat(4,1fr);gap:9px;margin:10px 0 14px; }
.zs-invest-card { padding:12px;border-radius:13px;border:1px solid rgba(148,163,184,.09);background:rgba(6,14,24,.54); }
.zs-invest-label { color:#7187a3;font-size:8px;text-transform:uppercase;letter-spacing:.9px;font-weight:800; }
.zs-invest-value { font-size:21px;font-weight:800;margin-top:5px; }
.zs-entity { padding:8px 10px;border-radius:9px;background:rgba(72,167,255,.06);border:1px solid rgba(72,167,255,.1);margin-bottom:6px;font-size:10px; }
.zs-entity strong { color:#dce9f7; }

/* ---------- Fraud-ring showcase ---------- */
.zs-ring-hero { padding:18px; border-radius:18px; border:1px solid rgba(83,216,255,.16); background:radial-gradient(circle at 90% 10%,rgba(83,216,255,.10),transparent 30%),linear-gradient(145deg,rgba(10,29,48,.95),rgba(6,15,27,.92)); box-shadow:0 16px 40px rgba(0,0,0,.16); }
.zs-ring-badge { display:inline-flex;align-items:center;gap:7px;padding:6px 10px;border-radius:999px;background:rgba(83,216,255,.08);border:1px solid rgba(83,216,255,.16);color:#8fe8ff;font-size:9px;font-weight:800;letter-spacing:.8px;text-transform:uppercase; }
.zs-ring-title { font-size:20px;font-weight:800;letter-spacing:-.5px;margin-top:10px; }
.zs-ring-sub { color:#7187a3;font-size:10px;line-height:1.6;margin-top:5px; }
.zs-ring-node { padding:12px;border-radius:13px;border:1px solid rgba(83,216,255,.11);background:rgba(4,12,21,.48);text-align:center; }
.zs-ring-node-title { color:#7187a3;font-size:8px;font-weight:800;letter-spacing:.9px;text-transform:uppercase; }
.zs-ring-node-value { color:#e9f5ff;font-size:13px;font-weight:800;margin-top:6px;word-break:break-word; }
.zs-ring-line { height:1px;background:linear-gradient(90deg,transparent,rgba(83,216,255,.28),transparent);margin:12px 0; }
.zs-ring-detected { padding:12px 14px;border-radius:12px;background:rgba(67,223,160,.06);border:1px solid rgba(67,223,160,.18);color:#9af3ce;font-size:10px;font-weight:700; }
.zs-ring-progress { height:8px;border-radius:999px;background:#16283b;overflow:hidden;margin-top:8px; }
.zs-ring-progress > div { height:100%;border-radius:999px;background:linear-gradient(90deg,#48a7ff,#53d8ff,#43dfa0); }

/* ---------- Misc ---------- */
[data-testid="stDataFrame"] { border:1px solid rgba(148,163,184,.09);border-radius:12px;overflow:hidden; }
[data-testid="stAlert"] { border-radius:12px!important; }
[data-testid="stExpander"] { border:1px solid rgba(148,163,184,.09)!important;border-radius:12px!important;background:rgba(8,18,30,.45)!important; }
button[data-baseweb="tab"] { font-size:11px!important;font-weight:800!important;color:#7187a3!important; }
button[data-baseweb="tab"][aria-selected="true"] { color:#f5f8fc!important; }
.zs-footer { text-align:center;color:#536a83;font-size:9px;padding:12px 0 0; }

@media(max-width:900px) {
  .zs-kpis{grid-template-columns:1fr 1fr;}
  .zs-invest-grid{grid-template-columns:1fr 1fr;}
}
</style>
''',
    unsafe_allow_html=True,
)

# ============================================================
# DATABASE + SESSION STATE
# ============================================================

init_db()

if "demo_account_id" not in st.session_state:
    st.session_state.demo_account_id = "ACC-" + uuid.uuid4().hex[:8].upper()

if "last_analysis" not in st.session_state:
    st.session_state.last_analysis = None

if "analysis_count" not in st.session_state:
    st.session_state.analysis_count = 0


def model_label(model_name: str) -> str:
    return "PaySim Fraud Model" if model_name == "paysim" else "Z-Sentinel Existing Model"


def format_reasons(value) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return "; ".join(str(item) for item in value)
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return "; ".join(str(item) for item in parsed)
        except (json.JSONDecodeError, TypeError):
            pass
    return str(value)


def risk_band(score: float) -> str:
    score = float(score)
    if score < 40:
        return "LOW"
    if score < 70:
        return "MEDIUM"
    return "HIGH"


def decision_class(decision: str) -> str:
    value = str(decision).upper().strip()
    if value == "HOLD":
        return "zs-hold"
    if value == "VERIFY":
        return "zs-verify"
    return "zs-allow"


def decision_dot(decision: str) -> str:
    value = str(decision).upper().strip()
    return {"ALLOW": "🟢", "VERIFY": "🟠", "HOLD": "🔴"}.get(value, "⚪")


def format_signal_name(name: str) -> str:
    return str(name).replace("_", " ").title()


def run_coordinated_fraud_demo():
    """Run a three-account coordinated activity scenario through the live API."""
    shared_device = "RING-DASH-DEVICE"
    shared_ip = "10.77.0.1"
    shared_merchant = "RING-DASH-MERCHANT"

    transactions = [
        {"account_id": "RING-DASH-01", "amount": 2450.0, "transactions_last_1h": 12, "failed_attempts": 3, "merchant_risk": 0.85, "ip_risk": 0.80},
        {"account_id": "RING-DASH-02", "amount": 3200.0, "transactions_last_1h": 15, "failed_attempts": 4, "merchant_risk": 0.90, "ip_risk": 0.85},
        {"account_id": "RING-DASH-03", "amount": 4100.0, "transactions_last_1h": 18, "failed_attempts": 5, "merchant_risk": 0.95, "ip_risk": 0.90},
    ]

    results = []
    payloads = []
    for index, item in enumerate(transactions, start=1):
        transaction = {
            "transaction_id": f"RING-DASH-TX-{index:02d}-{uuid.uuid4().hex[:8].upper()}",
            "account_id": item["account_id"],
            "device_id": shared_device,
            "ip_address": shared_ip,
            "merchant_id": shared_merchant,
            "amount": item["amount"],
            "hour": datetime.now().hour,
            "transactions_last_1h": item["transactions_last_1h"],
            "amount_last_1h": item["amount"] * item["transactions_last_1h"],
            "account_age_days": 30 - (index * 5),
            "device_age_days": 1,
            "is_new_device": 1,
            "is_international": 1,
            "failed_attempts": item["failed_attempts"],
            "merchant_risk": item["merchant_risk"],
            "ip_risk": item["ip_risk"],
            "network_degree": 3,
            "step": 0,
            "type": "PAYMENT",
            "oldbalanceOrg": 0.0,
            "newbalanceOrig": 0.0,
            "oldbalanceDest": 0.0,
            "newbalanceDest": 0.0,
        }
        response = requests.post(f"{API_URL}/api/analyze", json={**transaction, "model": "existing"}, timeout=30)
        if response.status_code != 200:
            raise RuntimeError(f"Coordinated demo failed for {transaction['account_id']} (HTTP {response.status_code}): {response.text}")
        payloads.append(transaction)
        results.append(response.json())

    graph = build_historical_network()
    final_account = payloads[-1]["account_id"]

    # Derive the showcase state directly from the completed graph.
    # This avoids depending on optional API response fields for the
    # dashboard presentation while keeping the live API as the
    # source of the actual risk decision.
    final_connected_accounts = find_connected_accounts(
        graph,
        final_account,
    )
    final_ring_score = calculate_fraud_ring_score(
        graph,
        final_account,
    )

    # Calculate the degree immediately before the final account
    # entered the graph, rather than estimating it arithmetically.
    history = load_network_history()

    # Network history can legitimately be empty or come from an
    # older schema that does not contain transaction_id.  The
    # coordinated showcase only needs the history BEFORE the final
    # demo account entered the graph, so use transaction_id when
    # available and fall back to account_id for older history files.
    if history.empty:
        history_before_final = history.copy()
    elif "transaction_id" in history.columns:
        history_before_final = history[
            history["transaction_id"]
            != payloads[-1]["transaction_id"]
        ].copy()
    elif "account_id" in history.columns:
        history_before_final = history[
            history["account_id"]
            != final_account
        ].copy()
    else:
        # No usable identity column is present.  Keep the existing
        # history rather than crashing the dashboard.
        history_before_final = history.copy()

    if history_before_final.empty:
        previous_graph = build_transaction_graph(
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
        previous_graph = build_transaction_graph(
            history_before_final[
                [
                    "account_id",
                    "device_id",
                    "ip_address",
                    "merchant_id",
                ]
            ]
        )

    return {
        "transactions": payloads,
        "results": results,
        "final_relationships": account_relationships(graph, final_account),
        "final_connected_accounts": final_connected_accounts,
        "final_ring_score": final_ring_score,
        "final_degree": account_network_degree(graph, final_account),
        "previous_degree": account_network_degree(previous_graph, final_account),
        "completed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


# ============================================================
# HEADER
# ============================================================

history_count = len(load_network_history())

st.markdown(
    f'''
<div class="zs-hero">
  <div style="display:flex;justify-content:space-between;align-items:center;gap:20px;">
    <div class="zs-brand">
      <div class="zs-shield">🛡️</div>
      <div>
        <div class="zs-title">Z-Sentinel</div>
        <div class="zs-subtitle">AI-assisted real-time fraud detection · explainable risk intelligence</div>
      </div>
    </div>
    <div style="text-align:right;position:relative;z-index:2;">
      <div class="zs-live"><span class="zs-dot"></span> LIVE · API CONNECTED</div>
      <div style="color:#647b96;font-size:9px;margin-top:7px;letter-spacing:.6px;">FRAUD INTELLIGENCE ENGINE · v1.0</div>
    </div>
  </div>
</div>
''',
    unsafe_allow_html=True,
)

st.markdown(
    f'''
<div class="zs-kpis">
  <div class="zs-kpi zs-kpi-green"><div class="zs-kpi-label">Pipeline</div><div class="zs-kpi-value">ONLINE</div><div class="zs-kpi-meta">FastAPI single source of truth</div></div>
  <div class="zs-kpi zs-kpi-blue"><div class="zs-kpi-label">Network History</div><div class="zs-kpi-value">{history_count:,}</div><div class="zs-kpi-meta">Persisted transactions</div></div>
  <div class="zs-kpi zs-kpi-amber"><div class="zs-kpi-label">Active Account</div><div class="zs-kpi-value" style="font-size:17px">{st.session_state.demo_account_id}</div><div class="zs-kpi-meta">Current investigation account</div></div>
  <div class="zs-kpi zs-kpi-blue"><div class="zs-kpi-label">Detection Layer</div><div class="zs-kpi-value">2 MODELS</div><div class="zs-kpi-meta">Existing + PaySim available</div></div>
</div>
''',
    unsafe_allow_html=True,
)

# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.header("⚙️ Detection Status")
    st.success("FastAPI pipeline connected")
    st.caption("API is the single source of truth for ML, anomaly, network, risk and decision results.")
    st.divider()
    st.header("🌐 Network Controls")
    st.code(st.session_state.demo_account_id)
    st.metric("Historical Transactions", history_count)
    if st.button("🗑️ Reset Network History", use_container_width=True):
        clear_network_history()
        st.success("Network history cleared.")
        st.rerun()

# ============================================================
# COMMAND CENTER
# ============================================================

left, right = st.columns([1.03, 0.97], gap="large")

with left:
    st.markdown(
        '''<div class="zs-panel"><div class="zs-panel-title">🔍 Transaction Command Center</div><div class="zs-panel-sub">Configure transaction behavior and submit it to the complete Z-Sentinel detection pipeline.</div></div>''',
        unsafe_allow_html=True,
    )

    model_choice = st.selectbox(
        "Detection Model",
        options=["existing", "paysim"],
        format_func=model_label,
        help="Choose the fraud model used by the FastAPI detection pipeline.",
    )

    if model_choice == "paysim":
        st.info("PaySim mode: provide the transaction features used by the PaySim fraud model.")
        paysim_type = st.selectbox("PaySim transaction type", ["PAYMENT", "TRANSFER", "CASH_OUT", "CASH_IN", "DEBIT"])
        paysim_step = st.number_input("PaySim step", min_value=0, value=1, step=1)
        pc1, pc2 = st.columns(2)
        with pc1:
            paysim_old_balance_org = st.number_input("Sender balance before", min_value=0.0, value=500.0, step=50.0)
            paysim_old_balance_dest = st.number_input("Receiver balance before", min_value=0.0, value=0.0, step=50.0)
        with pc2:
            paysim_new_balance_org = st.number_input("Sender balance after", min_value=0.0, value=250.0, step=50.0)
            paysim_new_balance_dest = st.number_input("Receiver balance after", min_value=0.0, value=250.0, step=50.0)
    else:
        paysim_type = "PAYMENT"
        paysim_step = 0
        paysim_old_balance_org = 0.0
        paysim_new_balance_org = 0.0
        paysim_old_balance_dest = 0.0
        paysim_new_balance_dest = 0.0

    input_a, input_b = st.columns(2)
    with input_a:
        amount = st.number_input("Transaction amount", min_value=0.0, max_value=10_000_000.0, value=250.0, step=50.0)
        velocity = st.number_input("Transactions in last 1 hour", min_value=0, max_value=1000, value=2, step=1)
        failed = st.number_input("Failed attempts", min_value=0, max_value=100, value=0, step=1)
    with input_b:
        merchant_risk = st.slider("Merchant risk", 0.0, 1.0, 0.2, 0.05)
        ip_risk = st.slider("IP risk", 0.0, 1.0, 0.2, 0.05)
        new_device = st.checkbox("New device")
        international = st.checkbox("International transaction")

    analyze_clicked = st.button("🔬 ANALYZE TRANSACTION", type="primary", use_container_width=True)

    st.markdown(
        '''<div class="zs-ring-hero" style="margin-top:12px;">
          <div class="zs-ring-badge">🕸 Coordinated Fraud Showcase</div>
          <div class="zs-ring-title">Trace a coordinated account ring</div>
          <div class="zs-ring-sub">Run three sequential transactions through the live API while they share the same device, IP address and merchant.</div>
        </div>''',
        unsafe_allow_html=True,
    )
    fraud_demo_clicked = st.button("🕸️ RUN COORDINATED FRAUD DEMO", use_container_width=True)

with right:
    latest_state = st.session_state.last_analysis
    if latest_state:
        api_result = latest_state["result"]
        latest_risk = float(api_result["risk_score"])
        latest_decision = str(api_result["decision"]).upper()
        latest_ml = float(api_result["ml_probability"])
        latest_anomaly = float(api_result["anomaly_score"])
        latest_network = float(api_result["network_score"])
        latest_ring = float(api_result["fraud_ring_score"])
        fill = max(0, min(100, latest_risk))
        band = risk_band(latest_risk)
        st.markdown(
            f'''
<div class="zs-risk-panel">
  <div class="zs-label">LIVE RISK MONITOR</div>
  <div class="zs-risk-top">
    <div><div class="zs-risk-number">{latest_risk:.1f}<span style="font-size:16px;color:#7187a3;"> / 100</span></div><div style="color:#7187a3;font-size:10px;margin-top:5px;">CURRENT RISK SCORE · {band} RISK BAND</div></div>
    <div class="zs-decision {decision_class(latest_decision)}">{decision_dot(latest_decision)} {latest_decision}</div>
  </div>
  <div class="zs-risk-meter"><div class="zs-risk-fill" style="width:{fill}%;"></div></div>
  <div class="zs-meter-caption">Risk exposure · {fill:.1f}%</div>
  <div class="zs-mini-grid">
    <div class="zs-mini"><div class="zs-mini-label">ML PROBABILITY</div><div class="zs-mini-value">{latest_ml*100:.1f}%</div></div>
    <div class="zs-mini"><div class="zs-mini-label">ANOMALY</div><div class="zs-mini-value">{latest_anomaly*100:.1f}%</div></div>
    <div class="zs-mini"><div class="zs-mini-label">NETWORK</div><div class="zs-mini-value">{latest_network*100:.1f}%</div></div>
    <div class="zs-mini"><div class="zs-mini-label">FRAUD RING</div><div class="zs-mini-value">{latest_ring*100:.1f}%</div></div>
  </div>
  <div style="margin-top:13px;color:#647b96;font-size:9px;">TX · {latest_state['transaction']['transaction_id']}</div>
</div>
''',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '''<div class="zs-risk-panel" style="min-height:286px;display:flex;flex-direction:column;justify-content:center;">
<div class="zs-label">LIVE RISK MONITOR</div>
<div style="font-size:25px;font-weight:800;margin-top:4px;">Awaiting transaction</div>
<div style="color:#7187a3;font-size:11px;line-height:1.7;margin-top:8px;">Run an analysis to populate the live risk score, model signals, network intelligence and decision state.</div>
<div style="margin-top:18px;color:#43dfa0;font-size:10px;font-weight:800;">● ENGINE READY · API CONNECTED</div>
</div>''',
            unsafe_allow_html=True,
        )

# ============================================================
# COORDINATED FRAUD DEMO EXECUTION
# ============================================================

if fraud_demo_clicked:
    try:
        with st.spinner("Tracing coordinated activity through the live detection pipeline..."):
            demo = run_coordinated_fraud_demo()
        final_transaction = demo["transactions"][-1]
        final_result = demo["results"][-1]
        st.session_state.analysis_count += 3
        st.session_state.last_analysis = {
            "transaction": final_transaction,
            "result": final_result,
            "previous_degree": demo["previous_degree"],
            "current_degree": demo["final_degree"],
            "network_score": float(final_result["network_score"]),
            "relationships": demo["final_relationships"],
            "combined_graph": build_historical_network(),
            "analyzed_at": demo["completed_at"],
            "fraud_demo": True,
            "fraud_demo_results": demo["results"],
            "fraud_demo_transactions": demo["transactions"],
            "fraud_demo_connected_accounts": demo["final_connected_accounts"],
            "fraud_demo_ring_score": demo["final_ring_score"],
        }
        st.rerun()
    except Exception as error:
        st.error("❌ Coordinated fraud showcase failed.")
        st.exception(error)

# ============================================================
# ANALYSIS EXECUTION
# ============================================================

if analyze_clicked:
    try:
        transaction_id = "TX-" + datetime.now().strftime("%Y%m%d%H%M%S") + "-" + uuid.uuid4().hex[:8].upper()
        account_id = st.session_state.demo_account_id
        device_id = "DEV-" + uuid.uuid4().hex[:8].upper()
        merchant_id = "MERCHANT-" + uuid.uuid4().hex[:8].upper()
        ip_address = f"10.0.{uuid.uuid4().int % 254 + 1}.{uuid.uuid4().int % 254 + 1}"

        transaction = {
            "transaction_id": transaction_id,
            "account_id": account_id,
            "device_id": device_id,
            "ip_address": ip_address,
            "merchant_id": merchant_id,
            "amount": float(amount),
            "hour": datetime.now().hour,
            "transactions_last_1h": int(velocity),
            "amount_last_1h": float(amount * max(1, velocity)),
            "account_age_days": 365,
            "device_age_days": 1 if new_device else 365,
            "is_new_device": int(new_device),
            "is_international": int(international),
            "failed_attempts": int(failed),
            "merchant_risk": float(merchant_risk),
            "ip_risk": float(ip_risk),
            "network_degree": 3,
            "step": int(paysim_step),
            "type": paysim_type,
            "oldbalanceOrg": float(paysim_old_balance_org),
            "newbalanceOrig": float(paysim_new_balance_org),
            "oldbalanceDest": float(paysim_old_balance_dest),
            "newbalanceDest": float(paysim_new_balance_dest),
        }

        historical_graph = build_historical_network()
        previous_degree = account_network_degree(historical_graph, account_id)

        current_transaction_df = pd.DataFrame([{
            "account_id": account_id,
            "device_id": device_id,
            "ip_address": ip_address,
            "merchant_id": merchant_id,
        }])

        combined_records = pd.concat(
            [load_network_history(), current_transaction_df],
            ignore_index=True,
        )
        combined_graph = build_transaction_graph(combined_records)
        actual_network_degree = account_network_degree(combined_graph, account_id)
        relationships = account_relationships(combined_graph, account_id)
        local_network_score = calculate_network_signal_from_degree(actual_network_degree)

        response = requests.post(
            f"{API_URL}/api/analyze",
            json={**transaction, "model": model_choice},
            timeout=30,
        )

        if response.status_code != 200:
            if response.status_code == 409:
                raise RuntimeError("This transaction ID already exists. Please run the analysis again.")
            if response.status_code == 422:
                try:
                    detail = response.json().get("detail", "Invalid transaction input.")
                except ValueError:
                    detail = "Invalid transaction input."
                raise RuntimeError(f"API validation failed: {detail}")
            raise RuntimeError(f"API analysis failed (HTTP {response.status_code}): {response.text}")

        api_result = response.json()
        st.session_state.analysis_count += 1
        st.session_state.last_analysis = {
            "transaction": transaction,
            "result": api_result,
            "previous_degree": previous_degree,
            "current_degree": actual_network_degree,
            "network_score": float(api_result["network_score"]),
            "relationships": relationships,
            "combined_graph": combined_graph,
            "analyzed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        st.rerun()

    except Exception as error:
        st.error("❌ Transaction analysis failed.")
        st.exception(error)

# ============================================================
# SECURITY OPERATIONS FEED
# ============================================================

st.markdown(
    '''<div class="zs-panel"><div class="zs-panel-title">📡 Security Operations Feed</div><div class="zs-panel-sub">Recent decisions persisted by the Z-Sentinel database.</div></div>''',
    unsafe_allow_html=True,
)

try:
    rows = recent_results(limit=12)
    if rows:
        feed_html = '<div style="border:1px solid rgba(148,163,184,.09);border-radius:13px;overflow:hidden;background:rgba(5,12,21,.45);">'
        feed_html += '<div class="zs-feed-row zs-feed-head"><div>TRANSACTION</div><div>ACCOUNT</div><div>RISK</div><div>DECISION</div></div>'
        for row in rows:
            decision = str(row.get("decision", "")).upper()
            cls = decision_class(decision)
            risk = float(row.get("risk_score", 0))
            feed_html += f'<div class="zs-feed-row"><div class="zs-feed-id">{row.get("transaction_id", "-")}</div><div class="zs-feed-account">{row.get("account_id", "-")}</div><div class="zs-feed-risk">{risk:.1f}</div><div><span class="zs-decision-pill {cls}">{decision_dot(decision)} {decision}</span></div></div>'
        feed_html += '</div>'
        st.markdown(feed_html, unsafe_allow_html=True)
        st.caption(f"Showing {len(rows)} latest analyzed transactions.")
    else:
        st.info("No analyzed transactions yet.")
except Exception as error:
    st.error("Unable to load recent decisions.")
    st.exception(error)

# ============================================================
# LATEST RESULT + INVESTIGATION
# ============================================================

state = st.session_state.last_analysis

if state:
    transaction = state["transaction"]
    result = state["result"]
    risk = float(result["risk_score"])
    decision = str(result["decision"]).upper()
    ml_probability = float(result["ml_probability"])
    anomaly = float(result["anomaly_score"])
    network = float(result["network_score"])
    ring = float(result["fraud_ring_score"])
    relationships = state.get("relationships", [])

    st.markdown("## 🔎 Investigation Center")
    st.caption("Current transaction intelligence · model evidence · network relationships · explainable decision path")

    summary_a, summary_b, summary_c, summary_d = st.columns(4)
    summary_cards = [
        ("RISK SCORE", f"{risk:.1f}/100", risk_band(risk)),
        ("DECISION", decision, "FINAL ACTION"),
        ("ML PROBABILITY", f"{ml_probability*100:.1f}%", "FRAUD MODEL"),
        ("NETWORK DEGREE", str(state["current_degree"]), "CURRENT GRAPH"),
    ]
    for col, (label, value, meta) in zip([summary_a, summary_b, summary_c, summary_d], summary_cards):
        with col:
            st.markdown(
                f'<div class="zs-invest-card"><div class="zs-invest-label">{label}</div><div class="zs-invest-value">{value}</div><div style="color:#60758f;font-size:8px;margin-top:3px;">{meta}</div></div>',
                unsafe_allow_html=True,
            )

    tabs = st.tabs([
        "🌐 NETWORK INTELLIGENCE",
        "🕸️ FRAUD RING",
        "🧠 RISK SIGNALS",
        "🔬 INVESTIGATION",
        "🧾 TRANSACTION",
        "⚠️ REASONS",
    ])

    with tabs[0]:
        net1, net2, net3, net4 = st.columns(4)
        with net1:
            st.markdown(f'<div class="zs-invest-card"><div class="zs-invest-label">PREVIOUS DEGREE</div><div class="zs-invest-value">{state["previous_degree"]}</div></div>', unsafe_allow_html=True)
        with net2:
            st.markdown(f'<div class="zs-invest-card"><div class="zs-invest-label">CURRENT DEGREE</div><div class="zs-invest-value">{state["current_degree"]}</div></div>', unsafe_allow_html=True)
        with net3:
            st.markdown(f'<div class="zs-invest-card"><div class="zs-invest-label">NETWORK RISK</div><div class="zs-invest-value">{network*100:.1f}%</div></div>', unsafe_allow_html=True)
        with net4:
            st.markdown(f'<div class="zs-invest-card"><div class="zs-invest-label">FRAUD RING</div><div class="zs-invest-value">{ring*100:.1f}%</div></div>', unsafe_allow_html=True)

        if relationships:
            st.markdown('<div class="zs-label" style="margin-top:14px;">CONNECTED ENTITIES</div>', unsafe_allow_html=True)
            entity_cols = st.columns(min(3, max(1, len(relationships))))
            for index, relationship in enumerate(relationships[:3]):
                node = relationship.get("node", "-")
                node_type = relationship.get("node_type", "entity")
                identifier = relationship.get("identifier", node)
                relation = relationship.get("relationship", "connected")
                with entity_cols[index % len(entity_cols)]:
                    st.markdown(f'<div class="zs-entity"><strong>{node_type.upper()}</strong><br>{identifier}<br><span style="color:#60758f;">{relation}</span></div>', unsafe_allow_html=True)
        else:
            st.info("No connected entities found for this account.")

        suspicious = find_suspicious_accounts(state["combined_graph"], minimum_degree=8)
        if suspicious:
            st.warning("Suspicious network relationships are present in the current graph.")
            suspicious_df = pd.DataFrame(suspicious)
            st.dataframe(suspicious_df.head(8), use_container_width=True, hide_index=True)
        else:
            st.success("No high-degree suspicious accounts detected in the current graph.")

    with tabs[1]:
        fraud_demo = bool(state.get("fraud_demo", False))

        # The controlled showcase has its own verified graph-derived
        # values. For ordinary analyses, use the API response fields.
        if fraud_demo:
            connected_accounts = state.get(
                "fraud_demo_connected_accounts",
                [],
            ) or []
            ring_score = float(
                state.get("fraud_demo_ring_score", 0.0)
            )
        else:
            connected_accounts = result.get(
                "connected_accounts",
                [],
            ) or []
            ring_score = float(
                result.get("fraud_ring_score", 0.0)
            )

        ring_detected = bool(
            result.get(
                "fraud_ring_detected",
                len(connected_accounts) >= 2,
            )
        )
        if fraud_demo:
            ring_detected = len(connected_accounts) >= 2

        st.markdown(
            '''<div class="zs-ring-hero">
              <div class="zs-ring-badge">🕸 Network Coordination</div>
              <div class="zs-ring-title">Fraud-ring intelligence</div>
              <div class="zs-ring-sub">The risk engine evaluates coordinated relationships alongside ML, anomaly and network signals.</div>
              <div class="zs-ring-line"></div>
            </div>''',
            unsafe_allow_html=True,
        )
        if fraud_demo:
            st.markdown('<div class="zs-ring-detected">✓ Controlled three-account showcase completed through the live API. Shared device, IP and merchant relationships were accumulated sequentially.</div>', unsafe_allow_html=True)
            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

        ring_a, ring_b, ring_c, ring_d = st.columns(4)
        with ring_a:
            st.markdown(f'<div class="zs-invest-card"><div class="zs-invest-label">RING STATUS</div><div class="zs-invest-value">{"DETECTED" if ring_detected else "MONITOR"}</div></div>', unsafe_allow_html=True)
        with ring_b:
            st.markdown(f'<div class="zs-invest-card"><div class="zs-invest-label">RING SCORE</div><div class="zs-invest-value">{ring_score*100:.1f}%</div></div>', unsafe_allow_html=True)
        with ring_c:
            st.markdown(f'<div class="zs-invest-card"><div class="zs-invest-label">CONNECTED ACCOUNTS</div><div class="zs-invest-value">{len(connected_accounts)}</div></div>', unsafe_allow_html=True)
        with ring_d:
            st.markdown(f'<div class="zs-invest-card"><div class="zs-invest-label">NETWORK DEGREE</div><div class="zs-invest-value">{state["current_degree"]}</div></div>', unsafe_allow_html=True)

        st.markdown(f'<div class="zs-label" style="margin-top:16px;">COORDINATION STRENGTH · {ring_score*100:.1f}%</div><div class="zs-ring-progress"><div style="width:{max(0,min(100,ring_score*100)):.1f}%;"></div></div>', unsafe_allow_html=True)
        if ring_detected:
            st.success("🕸️ Coordinated account activity has reached the configured ring-detection threshold.")
        elif connected_accounts:
            st.warning("Connected accounts are present, but the configured ring threshold has not yet been reached.")
        else:
            st.info("No connected accounts were returned for this transaction.")

        st.markdown('<div class="zs-label" style="margin-top:16px;">CONNECTED ACCOUNTS</div>', unsafe_allow_html=True)
        if connected_accounts:
            for account in connected_accounts:
                account_id = html.escape(str(account.get("account_id", "-")))
                shared = int(account.get("shared_connections", 0))
                st.markdown(f'<div class="zs-entity">🕸️ <strong>{account_id}</strong><br><span style="color:#60758f;">Shared infrastructure connections: {shared}</span></div>', unsafe_allow_html=True)
        else:
            st.info("No connected accounts for the current transaction.")

        st.markdown('<div class="zs-label" style="margin-top:16px;">SHARED INFRASTRUCTURE</div>', unsafe_allow_html=True)
        infrastructure = {}
        for relationship in relationships:
            node_type = str(relationship.get("node_type", "entity")).lower()
            identifier = relationship.get("identifier", relationship.get("node", "-"))
            infrastructure.setdefault(node_type, []).append(str(identifier))
        if infrastructure:
            infra_cols = st.columns(min(3, max(1, len(infrastructure))))
            for index, (node_type, identifiers) in enumerate(infrastructure.items()):
                unique_values = list(dict.fromkeys(identifiers))
                with infra_cols[index % len(infra_cols)]:
                    st.markdown(f'<div class="zs-ring-node"><div class="zs-ring-node-title">{html.escape(node_type)}</div><div class="zs-ring-node-value">{html.escape(", ".join(unique_values[:3]))}</div></div>', unsafe_allow_html=True)
        else:
            st.info("No shared infrastructure detected for the current investigation.")

    with tabs[2]:
        signals = result.get("signals", {})
        signal_rows = []
        for signal_name, signal_value in signals.items():
            numeric = float(signal_value)
            signal_rows.append({"Signal": format_signal_name(signal_name), "Score": f"{numeric*100:.1f}%", "Raw": round(numeric, 4)})
        if signal_rows:
            signal_df = pd.DataFrame(signal_rows)
            st.dataframe(signal_df, use_container_width=True, hide_index=True)

        sig_a, sig_b = st.columns(2)
        with sig_a:
            st.markdown(f'<div class="zs-invest-card"><div class="zs-invest-label">BASE DECISION</div><div class="zs-invest-value" style="font-size:18px;">{result["base_decision"]}</div></div>', unsafe_allow_html=True)
        with sig_b:
            st.markdown(f'<div class="zs-invest-card"><div class="zs-invest-label">FINAL DECISION</div><div class="zs-invest-value" style="font-size:18px;">{decision}</div></div>', unsafe_allow_html=True)
        st.progress(max(0, min(100, int(risk))), text=f"Overall risk · {risk:.1f}/100")

    with tabs[3]:
        investigation = result.get("investigation", {})

        if not investigation:
            st.warning(
                "Investigation evidence is not available for this transaction."
            )
        else:
            st.markdown(
                """<div class="zs-ring-hero">
                  <div class="zs-ring-badge">🔬 Investigation Evidence</div>
                  <div class="zs-ring-title">Why did Z-Sentinel make this decision?</div>
                  <div class="zs-ring-sub">
                    Structured evidence collected from the risk engine,
                    transaction behavior and network intelligence.
                  </div>
                </div>""",
                unsafe_allow_html=True,
            )

            st.markdown(
                '<div class="zs-label" style="margin-top:16px;">RISK CONTRIBUTIONS</div>',
                unsafe_allow_html=True,
            )

            contributions = investigation.get("risk_contributions", {})
            contribution_items = [
                ("ML", contributions.get("ml", 0.0)),
                ("ANOMALY", contributions.get("anomaly", 0.0)),
                ("NETWORK", contributions.get("network", 0.0)),
                ("FRAUD RING", contributions.get("fraud_ring", 0.0)),
                ("VELOCITY", contributions.get("velocity", 0.0)),
                ("DEVICE", contributions.get("device", 0.0)),
            ]

            contribution_cols = st.columns(3)
            for index, (label, value) in enumerate(contribution_items):
                with contribution_cols[index % 3]:
                    st.markdown(
                        f"""<div class="zs-invest-card">
  <div class="zs-invest-label">{label}</div>
  <div class="zs-invest-value">{float(value):.2f}</div>
  <div style="color:#60758f;font-size:8px;margin-top:3px;">RISK POINTS</div>
</div>""",
                        unsafe_allow_html=True,
                    )

            transaction_evidence = investigation.get(
                "transaction_evidence",
                {},
            )

            st.markdown(
                '<div class="zs-label" style="margin-top:16px;">TRANSACTION EVIDENCE</div>',
                unsafe_allow_html=True,
            )

            evidence_rows = [
                {
                    "Evidence": "Transaction Amount",
                    "Value": f'₹{float(transaction_evidence.get("amount", 0)):,.2f}',
                },
                {
                    "Evidence": "Transactions in Last 1h",
                    "Value": str(transaction_evidence.get("transactions_last_1h", 0)),
                },
                {
                    "Evidence": "Failed Attempts",
                    "Value": str(transaction_evidence.get("failed_attempts", 0)),
                },
                {
                    "Evidence": "New Device",
                    "Value": str(transaction_evidence.get("is_new_device", False)),
                },
                {
                    "Evidence": "International",
                    "Value": str(transaction_evidence.get("is_international", False)),
                },
                {
                    "Evidence": "Merchant Risk",
                    "Value": f'{float(transaction_evidence.get("merchant_risk", 0)) * 100:.1f}%',
                },
                {
                    "Evidence": "IP Risk",
                    "Value": f'{float(transaction_evidence.get("ip_risk", 0)) * 100:.1f}%',
                },
            ]

            st.dataframe(
                pd.DataFrame(evidence_rows),
                use_container_width=True,
                hide_index=True,
            )

            network_evidence = investigation.get(
                "network_evidence",
                {},
            )

            st.markdown(
                '<div class="zs-label" style="margin-top:16px;">NETWORK EVIDENCE</div>',
                unsafe_allow_html=True,
            )

            network_a, network_b, network_c, network_d = st.columns(4)

            with network_a:
                st.markdown(
                    f"""<div class="zs-invest-card">
  <div class="zs-invest-label">NETWORK DEGREE</div>
  <div class="zs-invest-value">{network_evidence.get("network_degree", 0)}</div>
</div>""",
                    unsafe_allow_html=True,
                )

            with network_b:
                st.markdown(
                    f"""<div class="zs-invest-card">
  <div class="zs-invest-label">NETWORK SCORE</div>
  <div class="zs-invest-value">{float(network_evidence.get("network_score", 0)) * 100:.1f}%</div>
</div>""",
                    unsafe_allow_html=True,
                )

            with network_c:
                st.markdown(
                    f"""<div class="zs-invest-card">
  <div class="zs-invest-label">RING SCORE</div>
  <div class="zs-invest-value">{float(network_evidence.get("fraud_ring_score", 0)) * 100:.1f}%</div>
</div>""",
                    unsafe_allow_html=True,
                )

            with network_d:
                st.markdown(
                    f"""<div class="zs-invest-card">
  <div class="zs-invest-label">CONNECTED ACCOUNTS</div>
  <div class="zs-invest-value">{network_evidence.get("connected_account_count", 0)}</div>
</div>""",
                    unsafe_allow_html=True,
                )

            connected_accounts = network_evidence.get(
                "connected_accounts",
                [],
            ) or []

            if connected_accounts:
                st.markdown(
                    '<div class="zs-label" style="margin-top:14px;">CONNECTED ACCOUNT INTELLIGENCE</div>',
                    unsafe_allow_html=True,
                )

                for account in connected_accounts:
                    account_id = html.escape(
                        str(account.get("account_id", "-"))
                    )
                    shared = int(
                        account.get("shared_connections", 0)
                    )

                    st.markdown(
                        f"""<div class="zs-entity">
  🕸️ <strong>{account_id}</strong><br>
  <span style="color:#60758f;">
    Shared infrastructure connections: {shared}
  </span>
</div>""",
                        unsafe_allow_html=True,
                    )

            decision_summary = investigation.get(
                "decision_summary",
                "",
            )

            st.markdown(
                '<div class="zs-label" style="margin-top:16px;">DECISION EXPLANATION</div>',
                unsafe_allow_html=True,
            )

            if decision_summary:
                st.info(decision_summary)

            conclusion_a, conclusion_b = st.columns(2)

            with conclusion_a:
                st.markdown(
                    f"""<div class="zs-invest-card">
  <div class="zs-invest-label">FINAL RISK SCORE</div>
  <div class="zs-invest-value">
    {float(investigation.get("risk_score", risk)):.1f}/100
  </div>
</div>""",
                    unsafe_allow_html=True,
                )

            with conclusion_b:
                investigation_decision = str(
                    investigation.get("decision", decision)
                ).upper()

                st.markdown(
                    f"""<div class="zs-invest-card">
  <div class="zs-invest-label">FINAL DECISION</div>
  <div class="zs-invest-value" style="font-size:18px;">
    {investigation_decision}
  </div>
</div>""",
                    unsafe_allow_html=True,
                )

    with tabs[4]:
        d1, d2 = st.columns(2)
        with d1:
            st.markdown(f'<div class="zs-label">TRANSACTION ID</div><div style="font-weight:700;margin-bottom:13px;">{transaction["transaction_id"]}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="zs-label">ACCOUNT ID</div><div style="font-weight:700;margin-bottom:13px;">{transaction["account_id"]}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="zs-label">AMOUNT</div><div style="font-weight:700;margin-bottom:13px;">{transaction["amount"]:,.2f}</div>', unsafe_allow_html=True)
        with d2:
            st.markdown(f'<div class="zs-label">DETECTION MODEL</div><div style="font-weight:700;margin-bottom:13px;">{model_label(result["model_name"])}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="zs-label">PREDICTION MODEL</div><div style="font-weight:700;margin-bottom:13px;">{result["prediction_model"]}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="zs-label">ANALYZED AT</div><div style="font-weight:700;margin-bottom:13px;">{state["analyzed_at"]}</div>', unsafe_allow_html=True)
        with st.expander("View raw transaction + API response"):
            st.json({"transaction": transaction, "result": result})

    with tabs[5]:
        reasons = result.get("reasons", [])
        if reasons:
            for reason in reasons:
                st.markdown(f'<div class="zs-entity">⚠️ <strong>{reason}</strong></div>', unsafe_allow_html=True)
        else:
            st.success("No major risk indicators were returned by the detection pipeline.")

    st.markdown("### 🧾 Investigation Conclusion")
    if decision == "HOLD":
        st.error("Transaction should be held for investigation.")
    elif decision == "VERIFY":
        st.warning("Additional verification is recommended before completion.")
    else:
        st.success("Transaction can proceed under the current risk policy.")

    st.caption(
        f"Detection model: {model_label(result['model_name'])} · Prediction source: {result['prediction_source']} · Session analyses: {st.session_state.analysis_count} · API remains the single source of truth."
    )

# ============================================================
# FOOTER
# ============================================================

st.divider()
st.markdown(
    '<div class="zs-footer">Z-Sentinel · AI-assisted fraud detection · Explainable risk intelligence · Real-time decisioning</div>',
    unsafe_allow_html=True,
)
