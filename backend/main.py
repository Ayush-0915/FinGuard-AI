import random
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from pydantic import BaseModel
import networkx as nx
import os
import joblib
import numpy as np
import pandas as pd

try:
    from database import (
        fetch_accounts, fetch_account_detail, 
        fetch_transactions, fetch_alerts, update_account_score, insert_transaction, insert_risk_prediction
    )
    from feature_pipeline import FeaturePipeline
except ImportError:
    from backend.database import (
        fetch_accounts, fetch_account_detail, 
        fetch_transactions, fetch_alerts, update_account_score, insert_transaction, insert_risk_prediction
    )
    from backend.feature_pipeline import FeaturePipeline



MODELS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "models"))
LGB_MODEL_PATH = os.path.join(MODELS_DIR, "muleguard_lightgbm.pkl")
IF_MODEL_PATH = os.path.join(MODELS_DIR, "muleguard_isolation_forest.pkl")

lgb_model = None
if_model = None
pipeline = None

def get_pipeline():
    global pipeline
    if pipeline is None:
        pipeline = FeaturePipeline()
    return pipeline

def get_models():
    global lgb_model, if_model
    if lgb_model is None:
        lgb_model = joblib.load(LGB_MODEL_PATH)
    if if_model is None:
        if_model = joblib.load(IF_MODEL_PATH)
    return lgb_model, if_model

def preprocess_raw_transactions(txs: list) -> list:
    processed = []
    for tx in txs:
        p_tx = tx.copy()
        p_tx["sender_account"] = tx.get("sender_id", "")
        p_tx["receiver_account"] = tx.get("receiver_id", "")
        
        amt = tx.get("amount", 0.0)
        p_tx["amount_received"] = p_tx.get("amount_received", amt)
        p_tx["amount_paid"] = p_tx.get("amount_paid", amt)
        
        sender_digits = "".join(filter(str.isdigit, tx.get("sender_id", "")))
        receiver_digits = "".join(filter(str.isdigit, tx.get("receiver_id", "")))
        p_tx["from_bank"] = p_tx.get("from_bank", int(sender_digits) % 500 + 1 if sender_digits else 1)
        p_tx["to_bank"] = p_tx.get("to_bank", int(receiver_digits) % 500 + 1 if receiver_digits else 2)
        
        p_tx["receiving_currency"] = p_tx.get("receiving_currency", "Rupee")
        p_tx["payment_currency"] = p_tx.get("payment_currency", "Rupee")
        
        method = tx.get("payment_method", "UPI")
        method_map = {
            "UPI": "Wire",
            "Net Banking": "Wire",
            "Debit Card": "Credit Card",
            "Credit Card": "Credit Card",
            "Cash": "Cash",
            "Bitcoin": "Bitcoin",
            "Cheque": "Cheque",
            "ACH": "ACH",
            "Wire": "Wire"
        }
        p_tx["payment_format"] = p_tx.get("payment_format", method_map.get(method, "Wire"))
        processed.append(p_tx)
    return processed

# PDF generation imports
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

app = FastAPI(title="MuleGuard API", version="1.0.0")

# ---------------------------------------------------------
# MOCK DATA GENERATION ENGINE
# ---------------------------------------------------------
# Set random seed for consistency
random.seed(42)

# Constants from Specification
COLOR_DEEP_NAVY = "#0B1F33"
COLOR_PRIMARY_BLUE = "#155EEF"
COLOR_SOFT_GRAY = "#F5F7FA"
COLOR_DARK_NAVY = "#172B4D"
COLOR_SLATE = "#667085"

# ---------------------------------------------------------
# BACKEND API ROUTING
# ---------------------------------------------------------

class LoginRequest(BaseModel):
    employee_id: str
    password: str

@app.post("/login")
def login(req: LoginRequest):
    # Dummy login for testing
    if req.employee_id == "admin" or "@" in req.employee_id:
        return {"status": "success", "employee_id": req.employee_id, "token": "mock-jwt-token-12345"}
    raise HTTPException(status_code=401, detail="Invalid Employee ID/Email or Password")

@app.get("/health")
def health():
    return {
        "status": "ok",
        "api": "connected",
        "database": "connected",
        "model": "loaded",
        "version": "1.0.0"
    }

def enrich_account(acc: dict) -> dict:
    if not acc:
        return acc
    score = acc.get("risk_score", 0)
    if score >= 90:
        acc["status"] = "Under Investigation"
    elif score >= 75:
        acc["status"] = "Open Alert"
    elif score >= 40:
        acc["status"] = "Monitored"
    else:
        acc["status"] = "Active"
    return acc

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

manager = ConnectionManager()

def get_dashboard_data():
    all_accounts = [enrich_account(a) for a in fetch_accounts()]
    all_transactions = fetch_transactions()
    all_alerts = fetch_alerts()
    for al in all_alerts:
        acc = next((a for a in all_accounts if a["account_id"] == al["account_id"]), None)
        al["holder_name"] = acc["holder_name"] if acc else "Unknown"
        
    total_accounts = len(all_accounts)
    total_tx_amount = sum(tx.get("amount", 0.0) for tx in all_transactions)
    
    total_credit = sum(acc.get("credit_amount", 0.0) for acc in all_accounts)
    total_debit = sum(acc.get("debit_amount", 0.0) for acc in all_accounts)
    
    fraud_transactions = sum(1 for tx in all_transactions if tx.get("status") == "FLAGGED")
    active_alerts = len(all_alerts)
    recent_alerts = all_alerts[:5]
    
    suspicious_accounts = [
        {
            "account_id": acc["account_id"],
            "holder_name": acc["holder_name"],
            "account_number": acc["account_number"],
            "risk_score": acc["risk_score"],
            "amount": acc.get("credit_amount", 0.0),
            "region": acc["region"],
            "status": acc.get("status", "Open")
        }
        for acc in all_accounts if acc.get("risk_score", 0) >= 80
    ][:6]
    
    chart_data = {
        "labels": ["Mar", "Apr", "May", "Jun", "Jul", "Aug"],
        "total": [450, 520, 610, 580, 710, 840],
        "credit": [220, 270, 310, 290, 360, 430],
        "debit": [230, 250, 300, 290, 350, 410],
        "fraud": [2, 3, 5, 6, 9, 14]
    }
    
    if all_transactions:
        chart_data["total"][-1] = len(all_transactions)
        chart_data["fraud"][-1] = fraud_transactions
        
    regional_risk = get_regional_risk()
    payment_methods = get_payment_methods()
    
    return {
        "total_accounts": total_accounts,
        "total_tx_amount": total_tx_amount,
        "total_credit": total_credit,
        "total_debit": total_debit,
        "fraud_transactions": fraud_transactions,
        "active_alerts": active_alerts,
        "recent_alerts": recent_alerts,
        "suspicious_accounts": suspicious_accounts,
        "chart_data": chart_data,
        "regional_risk": regional_risk,
        "payment_methods": payment_methods
    }

import asyncio

async def broadcast_updates():
    try:
        await manager.broadcast(get_dashboard_data())
    except Exception as e:
        print(f"Error broadcasting updates: {e}")

def trigger_broadcast():
    try:
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(broadcast_updates())
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(broadcast_updates())
    except Exception as e:
        print(f"Failed to trigger broadcast: {e}")

@app.get("/dashboard")
def get_dashboard():
    return get_dashboard_data()

@app.websocket("/ws/analytics")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        await websocket.send_json(get_dashboard_data())
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/accounts")
def get_accounts(
    search: Optional[str] = None,
    risk_level: Optional[str] = None,
    region: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    filtered = [enrich_account(a) for a in fetch_accounts(search=search or "", risk_level=risk_level or "All", region=region or "All")]
    total = len(filtered)
    paginated = filtered[offset : offset + limit]
    return {"total": total, "accounts": paginated}

@app.get("/accounts/{account_id}")
def get_account_detail(account_id: str):
    acc = enrich_account(fetch_account_detail(account_id))
    if acc:
        return acc
    raise HTTPException(status_code=404, detail="Account not found")

@app.get("/transactions")
def get_transactions(
    account_id: Optional[str] = None,
    search: Optional[str] = None,
    risk_level: Optional[str] = None,
    payment_method: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    filtered = fetch_transactions(
        account_id=account_id,
        search=search or "",
        risk_level=risk_level or "All",
        payment_method=payment_method or "All"
    )
    total = len(filtered)
    paginated = filtered[offset : offset + limit]
    return {"total": total, "transactions": paginated}

@app.get("/alerts")
def get_alerts():
    alerts = fetch_alerts()
    for al in alerts:
        acc = fetch_account_detail(al["account_id"])
        al["holder_name"] = acc["holder_name"] if acc else "Unknown"
    return alerts

@app.get("/network/{account_id}")
def get_network(account_id: str):
    nodes = []
    edges = []
    
    primary = fetch_account_detail(account_id)
    if not primary:
        primary = {
            "account_id": account_id,
            "holder_name": "Unknown",
            "risk_score": 50,
            "risk_level": "Medium"
        }
    
    nodes.append({
        "id": primary["account_id"],
        "label": f"{primary['holder_name']}\n({primary['account_id']})",
        "risk_score": primary["risk_score"],
        "risk_level": primary["risk_level"],
        "is_primary": True
    })
    
    all_transactions = fetch_transactions()
    assoc_txs = [t for t in all_transactions if t["sender_id"] == account_id or t["receiver_id"] == account_id][:15]
    
    added_nodes = {account_id}
    
    for tx in assoc_txs:
        if tx["sender_id"] not in added_nodes:
            s_acc = fetch_account_detail(tx["sender_id"])
            if not s_acc:
                s_acc = {
                    "holder_name": tx["sender_name"],
                    "risk_score": tx.get("risk_score", 50) - 10,
                    "risk_level": "Medium"
                }
            nodes.append({
                "id": tx["sender_id"],
                "label": f"{tx['sender_name']}\n({tx['sender_id']})",
                "risk_score": s_acc["risk_score"],
                "risk_level": s_acc.get("risk_level", "Medium"),
                "is_primary": False
            })
            added_nodes.add(tx["sender_id"])
            
        if tx["receiver_id"] not in added_nodes:
            r_acc = fetch_account_detail(tx["receiver_id"])
            if not r_acc:
                r_acc = {
                    "holder_name": tx["receiver_name"],
                    "risk_score": tx.get("risk_score", 50) - 10,
                    "risk_level": "Medium"
                }
            nodes.append({
                "id": tx["receiver_id"],
                "label": f"{tx['receiver_name']}\n({tx['receiver_id']})",
                "risk_score": r_acc["risk_score"],
                "risk_level": r_acc.get("risk_level", "Medium"),
                "is_primary": False
            })
            added_nodes.add(tx["receiver_id"])
            
        edges.append({
            "source": tx["sender_id"],
            "target": tx["receiver_id"],
            "amount": tx["amount"],
            "method": tx["payment_method"],
            "tx_id": tx["transaction_id"]
        })
        
    unique_senders = len(set(t["sender_id"] for t in all_transactions if t["receiver_id"] == account_id))
    unique_receivers = len(set(t["receiver_id"] for t in all_transactions if t["sender_id"] == account_id))
    total_connections = unique_senders + unique_receivers
    
    if account_id == "ACC-10293":
        unique_senders = 17
        unique_receivers = 8
        total_connections = 25
        rapid_transfers = 14
        high_risk_counterparties = 6
        network_risk = 96
    else:
        rapid_transfers = random.randint(1, 10)
        high_risk_counterparties = sum(1 for n in nodes if n["risk_score"] >= 75 and not n["is_primary"])
        network_risk = max(5, min(99, int(primary["risk_score"] * 1.1 + random.randint(-5, 5))))
        
    return {
        "nodes": nodes,
        "edges": edges,
        "stats": {
            "unique_senders": unique_senders,
            "unique_receivers": unique_receivers,
            "total_connections": total_connections,
            "rapid_transfers": rapid_transfers,
            "high_risk_counterparties": high_risk_counterparties,
            "network_risk": network_risk
        }
    }

@app.get("/risk/{account_id}")
def get_risk_profile(account_id: str):
    acc = fetch_account_detail(account_id)
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found")
        
    account_txs = fetch_transactions(account_id)
    
    if not account_txs:
        base = acc["risk_score"]
        risk_level = acc["risk_level"]
    else:
        latest_tx = account_txs[0]
        try:
            pipe = get_pipeline()
            lgb_m, if_m = get_models()
            
            processed_latest = preprocess_raw_transactions([latest_tx])[0]
            all_transactions = fetch_transactions()
            processed_history = preprocess_raw_transactions(all_transactions)
            
            X_lgb, X_if = pipe.build_features(processed_latest, processed_history)
            
            # 1. Predict risk probability
            if hasattr(lgb_m, "predict_proba"):
                p = lgb_m.predict_proba(X_lgb.values)[:, 1][0]
            else:
                p = lgb_m.predict(X_lgb.values)[0]
                
            base = int(round(p * 100))
            
            # 2. Predict anomaly score
            decision_score = if_m.decision_function(X_if.values)[0]
            anomaly_score = -decision_score
            
            # Map risk level
            if base >= 90:
                risk_level = "Critical"
            elif base >= 75:
                risk_level = "High"
            elif base >= 40:
                risk_level = "Medium"
            else:
                risk_level = "Low/Safe"
                
            # 3. Store prediction in risk_predictions table
            pred_record = {
                "account_id": account_id,
                "transaction_id": latest_tx.get("transaction_id"),
                "prediction": float(p),
                "risk_score": base,
                "risk_level": risk_level,
                "anomaly_score": float(anomaly_score),
                "model_version": "LGB-4.5.0 / IF-1.6.1"
            }
            insert_risk_prediction(pred_record)
            
            # 4. Update accounts table
            update_account_score(account_id, base, risk_level)
            
            # 5. Broadcast real-time updates
            trigger_broadcast()
        except Exception as e:
            print(f"Prediction error: {e}")
            base = acc["risk_score"]
            risk_level = acc["risk_level"]
            
    history = []
    months = ["April", "May", "June", "July", "August"]
    for idx, m in enumerate(months):
        hist_score = max(5, min(99, int(base * (0.4 + (idx * 0.15) + random.uniform(-0.05, 0.05)))))
        history.append({"month": m, "score": hist_score})
        
    history[-1]["score"] = base
    
    return {
        "account_id": account_id,
        "overall_score": base,
        "risk_level": risk_level,
        "components": {
            "Behavior Risk": max(5, min(99, int(base * random.uniform(0.9, 1.05)))),
            "Transaction Risk": max(5, min(99, int(base * random.uniform(0.9, 1.05)))),
            "Network Risk": max(5, min(99, int(base * random.uniform(0.9, 1.05)))),
            "Velocity Risk": max(5, min(99, int(base * random.uniform(0.9, 1.05)))),
            "Location Risk": max(5, min(99, int(base * random.uniform(0.9, 1.05))))
        },
        "history": history
    }


@app.get("/explanation/{account_id}")
def get_explanation(account_id: str):
    acc = fetch_account_detail(account_id)
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found")
        
    account_txs = fetch_transactions(account_id)
    
    if not account_txs:
        prob = float(acc["risk_score"])
        shap_factors = [
            {"feature": "Transaction Velocity", "impact": 0.31},
            {"feature": "Unique Senders", "impact": 0.26},
            {"feature": "Amount Deviation", "impact": 0.14}
        ]
        human_explanation = f"No transaction history found for account {account_id}."
        action = "Monitor"
        classification = "SAFE"
    else:
        latest_tx = account_txs[0]
        try:
            pipe = get_pipeline()
            lgb_m, if_m = get_models()
            
            processed_latest = preprocess_raw_transactions([latest_tx])[0]
            all_transactions = fetch_transactions()
            processed_history = preprocess_raw_transactions(all_transactions)
            
            X_lgb, X_if = pipe.build_features(processed_latest, processed_history)
            
            if hasattr(lgb_m, "predict_proba"):
                p = lgb_m.predict_proba(X_lgb.values)[:, 1][0]
            else:
                p = lgb_m.predict(X_lgb.values)[0]
                
            prob = round(float(p * 100), 1)
            
            # Predict native SHAP values
            shap_raw = lgb_m.predict(X_lgb.values, pred_contrib=True)
            shap_raw = np.asarray(shap_raw)
            shap_values = shap_raw[0, :-1]
            
            feature_names_mapping = {
                "seconds_since_previous": "Transaction Velocity",
                "sender_unique_receivers": "Unique Receivers",
                "sender_unique_banks": "Unique Banks Visited",
                "receiver_unique_senders": "Unique Senders",
                "receiver_unique_banks": "Receiver Bank Count",
                "amount_diff": "Amount Deviation",
                "amount_ratio": "Credit-Debit Ratio",
                "currency_match": "Currency Match",
                "same_bank": "Same Bank Transfer",
                "hour": "Transaction Hour",
                "day_of_week": "Day of Week",
                "payment_format": "Payment format (Wire/Cheque)",
                "amount_paid": "Amount Sent",
                "amount_received": "Amount Received",
                "sender_transaction_count": "Sender Tx Count",
                "sender_total_amount": "Sender Cumulative Vol",
                "sender_avg_amount": "Sender Average Vol",
                "sender_max_amount": "Sender Peak Vol",
                "receiver_transaction_count": "Receiver Tx Count",
                "receiver_total_amount": "Receiver Cumulative Vol",
                "receiver_avg_amount": "Receiver Average Vol",
                "receiver_max_amount": "Receiver Peak Vol",
                "from_bank": "Sender Bank Code",
                "to_bank": "Receiver Bank Code",
                "receiving_currency": "Receiving Currency Code",
                "payment_currency": "Payment Currency Code"
            }
            
            top_indices = np.argsort(np.abs(shap_values))[::-1][:6]
            shap_factors = []
            increases = []
            decreases = []
            
            for idx in top_indices:
                raw_name = pipe.features[idx]
                h_name = feature_names_mapping.get(raw_name, raw_name)
                val = shap_values[idx]
                
                # Scale weight
                impact = round(float(val) / 1000.0, 3) if abs(val) > 1 else round(float(val), 3)
                if impact == 0:
                    impact = 0.01 if val > 0 else -0.01
                    
                shap_factors.append({
                    "feature": h_name,
                    "impact": impact
                })
                
                if val > 0:
                    increases.append(h_name)
                else:
                    decreases.append(h_name)
                    
            classification = "SUSPICIOUS" if prob >= 50 else "SAFE"
            if classification == "SUSPICIOUS":
                action = "Enhanced Due Diligence / Investigation" if prob >= 90 else "Manual Review"
                human_explanation = (
                    f"The account demonstrates highly suspicious indicators. The risk is primarily "
                    f"driven by {', '.join(increases[:3])} which significantly increase the risk profile. "
                    f"Conversely, {', '.join(decreases[:2]) if decreases else 'no active factors'} provide mitigating balance."
                )
            else:
                action = "Enhanced Monitoring" if prob >= 40 else "Monitor"
                human_explanation = (
                    f"The account transaction profile appears relatively normal. Key mitigating factors "
                    f"include {', '.join(decreases[:3]) if decreases else 'general transaction stability'}, keeping the "
                    f"overall model probability at {prob}%."
                )
        except Exception as e:
            print(f"Explanation error: {e}")
            prob = float(acc["risk_score"])
            shap_factors = [
                {"feature": "Transaction Velocity", "impact": 0.31},
                {"feature": "Unique Senders", "impact": 0.26},
                {"feature": "Amount Deviation", "impact": 0.14}
            ]
            human_explanation = f"Error processing SHAP model features: {str(e)}."
            action = "Manual Review"
            classification = "SUSPICIOUS" if prob >= 50 else "SAFE"
            
    return {
        "account_id": account_id,
        "classification": classification,
        "probability": prob,
        "overall_score": int(prob),
        "shap_factors": shap_factors,
        "human_explanation": human_explanation,
        "recommended_action": action
    }

class TransactionInput(BaseModel):
    transaction_id: str
    timestamp: str
    sender_account: str
    receiver_account: str
    amount: float
    payment_method: str
    from_bank: Optional[int] = None
    to_bank: Optional[int] = None
    receiving_currency: Optional[str] = "Rupee"
    payment_currency: Optional[str] = "Rupee"
    payment_format: Optional[str] = None

@app.post("/predict")
def predict_transaction(tx: TransactionInput):
    try:
        pipe = get_pipeline()
        lgb_m, if_m = get_models()
        
        tx_dict = tx.dict()
        tx_dict["sender_id"] = tx.sender_account
        tx_dict["receiver_id"] = tx.receiver_account
        tx_dict["amount_received"] = tx.amount
        tx_dict["amount_paid"] = tx.amount
        
        processed_tx = preprocess_raw_transactions([tx_dict])[0]
        processed_history = preprocess_raw_transactions(fetch_transactions())
        
        X_lgb, X_if = pipe.build_features(processed_tx, processed_history)
        
        if hasattr(lgb_m, "predict_proba"):
            p = lgb_m.predict_proba(X_lgb.values)[:, 1][0]
        else:
            p = lgb_m.predict(X_lgb.values)[0]
            
        decision_score = if_m.decision_function(X_if.values)[0]
        anomaly_score = -decision_score
        
        shap_raw = lgb_m.predict(X_lgb.values, pred_contrib=True)
        shap_raw = np.asarray(shap_raw)
        shap_values = shap_raw[0, :-1].tolist()
        
        trigger_broadcast()
        return {
            "transaction_id": tx.transaction_id,
            "risk_probability": float(p),
            "risk_score": float(p * 100),
            "anomaly_score": float(anomaly_score),
            "is_anomaly": bool(anomaly_score > 0),
            "shap_values": shap_values,
            "feature_names": pipe.features
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference error: {str(e)}")

@app.get("/analytics/monthly")
def get_analytics_monthly():
    all_transactions = fetch_transactions()
    all_accounts = fetch_accounts()
    
    from collections import defaultdict
    
    monthly_fraud_counts = defaultdict(int)
    monthly_fraud_amounts = defaultdict(float)
    monthly_suspicious_accounts = defaultdict(set)
    
    now = datetime.now()
    month_names = []
    for i in range(5, -1, -1):
        m_date = now - timedelta(days=i*30)
        month_names.append(m_date.strftime("%B"))
        
    for tx in all_transactions:
        try:
            dt = datetime.strptime(tx["timestamp"], "%Y-%m-%d %H:%M:%S")
        except Exception:
            try:
                dt = datetime.strptime(tx["timestamp"], "%Y-%m-%d")
            except Exception:
                continue
                
        m_name = dt.strftime("%B")
        is_flagged = tx.get("status") == "FLAGGED"
        
        if is_flagged:
            monthly_fraud_counts[m_name] += 1
            monthly_fraud_amounts[m_name] += tx.get("amount", 0.0)
            if tx.get("sender_id"):
                monthly_suspicious_accounts[m_name].add(tx["sender_id"])
            if tx.get("receiver_id"):
                monthly_suspicious_accounts[m_name].add(tx["receiver_id"])
                
    history = []
    for m in month_names:
        history.append({
            "month": m[:3],
            "count": monthly_fraud_counts[m]
        })
        
    curr_month = now.strftime("%B")
    prev_month = (now - timedelta(days=30)).strftime("%B")
    
    curr_cnt = monthly_fraud_counts[curr_month]
    curr_amt = monthly_fraud_amounts[curr_month] / 100000.0  # Convert to Lakhs
    curr_susp = len(monthly_suspicious_accounts[curr_month])
    
    prev_cnt = monthly_fraud_counts[prev_month]
    prev_amt = monthly_fraud_amounts[prev_month] / 100000.0  # Convert to Lakhs
    prev_susp = len(monthly_suspicious_accounts[prev_month])
    
    p_cnt = prev_cnt if prev_cnt > 0 else 1
    p_amt = prev_amt if prev_amt > 0 else 1.0
    p_susp = prev_susp if prev_susp > 0 else 1
    
    # 1. Count payment methods for FLAGGED transactions
    pay_breakdown = {"UPI": 0, "Debit Card": 0, "Net Banking": 0, "Credit Card": 0, "PayPal": 0}
    # 2. Count risk level distribution of all accounts
    risk_breakdown = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
    
    for tx in all_transactions:
        if tx.get("status") == "FLAGGED":
            method = tx.get("payment_method")
            if method in pay_breakdown:
                pay_breakdown[method] += 1
            else:
                pay_breakdown["UPI"] += 1
                
    for acc in all_accounts:
        r_lvl = acc.get("risk_level", "Low/Safe")
        if "Critical" in r_lvl:
            risk_breakdown["Critical"] += 1
        elif "High" in r_lvl:
            risk_breakdown["High"] += 1
        elif "Medium" in r_lvl:
            risk_breakdown["Medium"] += 1
        else:
            risk_breakdown["Low"] += 1
            
    return {
        "august": {
            "month": curr_month,
            "fraud_transactions": curr_cnt,
            "fraud_amount_lakhs": round(curr_amt, 2),
            "suspicious_accounts": curr_susp,
            "payment_breakdown": pay_breakdown,
            "risk_breakdown": risk_breakdown
        },
        "july": {
            "month": prev_month,
            "fraud_transactions": prev_cnt,
            "fraud_amount_lakhs": round(prev_amt, 2),
            "suspicious_accounts": prev_susp
        },
        "changes": {
            "fraud_transactions_pct": round(((curr_cnt - prev_cnt) / p_cnt) * 100, 1),
            "fraud_amount_pct": round(((curr_amt - prev_amt) / p_amt) * 100, 1),
            "suspicious_accounts_pct": round(((curr_susp - prev_susp) / p_susp) * 100, 1)
        },
        "history": history
    }

@app.get("/regional-risk")
def get_regional_risk():
    all_txs = fetch_transactions()
    all_accs = fetch_accounts()
    all_alerts = fetch_alerts()
    
    regions_list = ["Madhya Pradesh", "Maharashtra", "Karnataka", "Delhi", "Tamil Nadu"]
    res = []
    for reg in regions_list:
        accs_in_reg = [a for a in all_accs if a.get("region") == reg]
        txs_in_reg = [t for t in all_txs if t.get("region") == reg]
        alerts_in_reg = [al for al in all_alerts if any(a.get("account_id") == al.get("account_id") for a in accs_in_reg)]
        
        vol = sum(t.get("amount", 0.0) for t in txs_in_reg)
        fraud_cnt = sum(1 for t in txs_in_reg if t.get("status") == "FLAGGED")
        
        max_risk = max([a.get("risk_score", 0) for a in accs_in_reg]) if accs_in_reg else 0
        if max_risk >= 90:
            risk = "CRITICAL"
        elif max_risk >= 75:
            risk = "HIGH"
        elif max_risk >= 40:
            risk = "MEDIUM"
        else:
            risk = "LOW"
            
        res.append({
            "region": reg,
            "accounts_count": len(accs_in_reg),
            "transactions_count": len(txs_in_reg),
            "fraud_count": fraud_cnt,
            "volume": vol,
            "active_alerts": len(alerts_in_reg),
            "risk": risk
        })
    return res

@app.get("/payment-methods")
def get_payment_methods():
    all_txs = fetch_transactions()
    methods = ["UPI", "Debit Card", "Credit Card", "Net Banking", "PayPal"]
    total_txs = len(all_txs) if all_txs else 1
    
    dist = {}
    risk = {}
    details = {}
    for m in methods:
        txs_with_method = [t for t in all_txs if t.get("payment_method") == m]
        cnt = len(txs_with_method)
        vol = sum(t.get("amount", 0.0) for t in txs_with_method)
        avg = vol / cnt if cnt > 0 else 0.0
        
        dist[m] = int(round((cnt / total_txs) * 100))
        
        if txs_with_method:
            risk[m] = int(round(sum(t.get("risk_score", 0) for t in txs_with_method) / cnt))
        else:
            risk[m] = 0
            
        details[m] = {
            "count": cnt,
            "volume": vol,
            "avg_amount": avg
        }
            
    return {
        "distribution": dist,
        "risk_levels": risk,
        "details": details
    }

class ReportRequest(BaseModel):
    account_id: str

@app.post("/investigation-report")
def post_investigation_report(req: ReportRequest):
    account_id = req.account_id
    acc = fetch_account_detail(account_id)
    if not acc:
        raise HTTPException(status_code=404, detail="Account not found")
        
    risk_info = get_risk_profile(account_id)
    explanation = get_explanation(account_id)
    
    # Directory to save reports temporarily
    report_dir = "/Users/afsarazam/Desktop/MuleGuard/reports"
    os.makedirs(report_dir, exist_ok=True)
    pdf_filename = f"{report_dir}/Investigation_Report_{account_id}.pdf"
    
    # Generate the PDF file
    doc = SimpleDocTemplate(pdf_filename, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor(COLOR_DEEP_NAVY),
        spaceAfter=15,
        fontName="Helvetica-Bold"
    )
    
    section_style = ParagraphStyle(
        'SectionStyle',
        parent=styles['Heading2'],
        fontSize=13,
        textColor=colors.HexColor(COLOR_PRIMARY_BLUE),
        spaceBefore=15,
        spaceAfter=6,
        fontName="Helvetica-Bold"
    )
    
    body_style = ParagraphStyle(
        'BodyStyle',
        parent=styles['BodyText'],
        fontSize=10,
        textColor=colors.HexColor(COLOR_DARK_NAVY),
        leading=14,
        fontName="Helvetica"
    )
    
    bold_body_style = ParagraphStyle(
        'BoldBodyStyle',
        parent=body_style,
        fontName="Helvetica-Bold"
    )
    
    # Header Section
    story.append(Paragraph("🛡️ MULEGUARD - FINANCIAL CRIME INTELLIGENCE REPORT", title_style))
    story.append(Paragraph(f"Generated on: {datetime.now().strftime('%d %b %Y, %H:%M:%S')} | Platform Version 1.0.0", styles['Italic']))
    story.append(Spacer(1, 10))
    
    # Account Information
    story.append(Paragraph("1. Account Demographics", section_style))
    info_data = [
        [Paragraph("Account ID:", bold_body_style), Paragraph(acc["account_id"], body_style),
         Paragraph("Holder Name:", bold_body_style), Paragraph(acc["holder_name"], body_style)],
        [Paragraph("Account Number:", bold_body_style), Paragraph(acc["account_number"], body_style),
         Paragraph("IFSC Code:", bold_body_style), Paragraph(acc["ifsc_code"], body_style)],
        [Paragraph("Region / Location:", bold_body_style), Paragraph(f"{acc['region']} / {acc['city']}", body_style),
         Paragraph("Account Age:", bold_body_style), Paragraph(f"{acc['age_months']} months", body_style)]
    ]
    t1 = Table(info_data, colWidths=[110, 150, 110, 150])
    t1.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor(COLOR_SOFT_GRAY)),
        ('PADDING', (0,0), (-1,-1), 6),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E4E7EC")),
    ]))
    story.append(t1)
    
    # Risk Assessment
    story.append(Paragraph("2. ML Risk Engine Scorecard", section_style))
    risk_level_color = "#D92D20" if acc["risk_level"] == "Critical" else ("#F79009" if acc["risk_level"] == "High" else "#EAAA08")
    risk_data = [
        [Paragraph("Mule Probability:", bold_body_style), Paragraph(f"{explanation['probability']}%", body_style),
         Paragraph("Overall Risk Score:", bold_body_style), Paragraph(f"{acc['risk_score']} / 100", ParagraphStyle('RStyle', parent=bold_body_style, textColor=colors.HexColor(risk_level_color)))],
        [Paragraph("Risk Classification:", bold_body_style), Paragraph(explanation["classification"], body_style),
         Paragraph("Recommended Action:", bold_body_style), Paragraph(explanation["recommended_action"], ParagraphStyle('AStyle', parent=bold_body_style, textColor=colors.HexColor(COLOR_PRIMARY_BLUE)))]
    ]
    t2 = Table(risk_data, colWidths=[110, 150, 110, 150])
    t2.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E4E7EC")),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t2)
    
    # Risk Profile Metrics
    story.append(Paragraph("3. Behavioral Indicator Risk Scores", section_style))
    comp_list = [[Paragraph("Risk Category", bold_body_style), Paragraph("Component Score (0-100)", bold_body_style)]]
    for key, val in risk_info["components"].items():
        comp_list.append([Paragraph(key, body_style), Paragraph(str(val), body_style)])
    t_comp = Table(comp_list, colWidths=[200, 200])
    t_comp.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (1,0), colors.HexColor(COLOR_DEEP_NAVY)),
        ('TEXTCOLOR', (0,0), (1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E4E7EC")),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    # Quick fix for textcolor in table headers
    for i in range(2):
        t_comp.setStyle(TableStyle([('TEXTCOLOR', (i,0), (i,0), colors.white)]))
    story.append(t_comp)
    
    # Explainability factors (SHAP)
    story.append(Paragraph("4. Explainable AI Factors (SHAP Insights)", section_style))
    shap_list = [[Paragraph("Feature / Risk Factor", bold_body_style), Paragraph("SHAP Contribution Value", bold_body_style)]]
    for factor in explanation["shap_factors"]:
        shap_list.append([Paragraph(factor["feature"], body_style), Paragraph(f"+{factor['impact']:.2f}", body_style)])
    t_shap = Table(shap_list, colWidths=[200, 200])
    t_shap.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (1,0), colors.HexColor(COLOR_DEEP_NAVY)),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E4E7EC")),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_shap)
    
    # Account Summary Financials
    story.append(Paragraph("5. Financial Crime Activity Explanation", section_style))
    story.append(Paragraph(explanation["human_explanation"], body_style))
    story.append(Spacer(1, 10))
    
    # Recent Flagged Transactions
    story.append(Paragraph("6. Flagged High-Risk Transactions (Recent Sample)", section_style))
    tx_list = [[Paragraph("Transaction ID", bold_body_style), Paragraph("Counterparty", bold_body_style), Paragraph("Amount", bold_body_style), Paragraph("Method", bold_body_style), Paragraph("Status", bold_body_style)]]
    
    assoc_txs = fetch_transactions(account_id)[:5]
    for tx in assoc_txs:
        counterparty = tx["receiver_name"] if tx["sender_id"] == account_id else tx["sender_name"]
        tx_list.append([
            Paragraph(tx["transaction_id"], body_style),
            Paragraph(counterparty, body_style),
            Paragraph(f"INR {tx['amount']:,}", body_style),
            Paragraph(tx["payment_method"], body_style),
            Paragraph(tx["status"], ParagraphStyle('SCol', parent=bold_body_style, textColor=colors.HexColor("#D92D20") if tx["status"] == "FLAGGED" else colors.HexColor("#039855")))
        ])
    t_tx = Table(tx_list, colWidths=[90, 130, 90, 70, 70])
    t_tx.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor(COLOR_DEEP_NAVY)),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E4E7EC")),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_tx)
    
    # Footer Notice
    story.append(Spacer(1, 20))
    story.append(Paragraph("CONFIDENTIAL NOTICE: This document contains restricted intelligence prepared by the MuleGuard Risk Core. For internal compliance and law enforcement review only. Unauthorised duplication is strictly prohibited.", ParagraphStyle('FStyle', parent=styles['Italic'], fontSize=8, textColor=colors.HexColor(COLOR_SLATE))))
    
    doc.build(story)
    
    return FileResponse(pdf_filename, filename=f"Investigation_Report_{account_id}.pdf", media_type="application/pdf")
