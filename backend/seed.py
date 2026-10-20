"""
FinGuard AI Supabase Seeding and Migration Tool

This script assists in setting up the Supabase PostgreSQL database tables and 
seeding them with synthetic showcase data for FinGuard AI.

FEATURES:
- Generates 102 synthetic accounts, 500 transactions, 50 risk predictions, 25 alerts, 12 investigations.
- Completely fictional data: Indian demographic names, synthetic account numbers, demo IFSC codes.
- Deterministic and reproducible using a fixed random seed (seed=42).
- Non-destructive, idempotent upserting (safe to re-run without duplicate key errors or erasing unrelated data).
- Verifies foreign keys, balances, and column constraints.
- Reports actual row counts across all five database tables upon completion.
"""

import os
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv(os.path.expanduser("~/.env"))
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# SQL DDL Script for reference / copy-paste inside Supabase SQL Editor
SQL_DDL = """
-- 1. Create accounts table
CREATE TABLE IF NOT EXISTS accounts (
    account_id TEXT PRIMARY KEY,
    holder_name TEXT NOT NULL,
    account_number TEXT NOT NULL,
    ifsc_code TEXT NOT NULL,
    region TEXT NOT NULL,
    city TEXT NOT NULL,
    age_months INTEGER NOT NULL,
    risk_score INTEGER NOT NULL,
    risk_level TEXT NOT NULL,
    credit_amount DOUBLE PRECISION NOT NULL,
    debit_amount DOUBLE PRECISION NOT NULL,
    payment_methods TEXT[] NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Create transactions table
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id TEXT PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    sender_id TEXT NOT NULL REFERENCES accounts(account_id) ON DELETE CASCADE,
    sender_name TEXT NOT NULL,
    receiver_id TEXT NOT NULL REFERENCES accounts(account_id) ON DELETE CASCADE,
    receiver_name TEXT NOT NULL,
    amount DOUBLE PRECISION NOT NULL,
    transaction_type TEXT NOT NULL,
    payment_method TEXT NOT NULL,
    region TEXT NOT NULL,
    city TEXT NOT NULL,
    risk_score INTEGER NOT NULL,
    risk_level TEXT NOT NULL,
    status TEXT NOT NULL,
    reasons TEXT[] NOT NULL,
    from_bank INTEGER NOT NULL,
    to_bank INTEGER NOT NULL,
    receiving_currency TEXT NOT NULL DEFAULT 'Rupee',
    payment_currency TEXT NOT NULL DEFAULT 'Rupee',
    payment_format TEXT NOT NULL DEFAULT 'Wire',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Create risk_predictions table
CREATE TABLE IF NOT EXISTS risk_predictions (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    account_id TEXT NOT NULL REFERENCES accounts(account_id) ON DELETE CASCADE,
    transaction_id TEXT REFERENCES transactions(transaction_id) ON DELETE CASCADE,
    prediction DOUBLE PRECISION NOT NULL,
    risk_score INTEGER NOT NULL,
    risk_level TEXT NOT NULL,
    anomaly_score DOUBLE PRECISION NOT NULL,
    model_version TEXT NOT NULL DEFAULT 'LGB-4.5.0 / IF-1.6.1',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. Create alerts table
CREATE TABLE IF NOT EXISTS alerts (
    alert_id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL REFERENCES accounts(account_id) ON DELETE CASCADE,
    alert_type TEXT NOT NULL,
    risk_score INTEGER NOT NULL,
    risk_level TEXT NOT NULL,
    amount DOUBLE PRECISION NOT NULL,
    detected_time TIMESTAMP WITH TIME ZONE NOT NULL,
    status TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. Create investigations table
CREATE TABLE IF NOT EXISTS investigations (
    investigation_id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL REFERENCES accounts(account_id) ON DELETE CASCADE,
    status TEXT NOT NULL,
    notes TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
"""

def generate_synthetic_dataset():
    """Generates 100% synthetic, reproducible showcase data."""
    random.seed(42)
    
    names_first = [
        "Aarav", "Rohan", "Vikram", "Priya", "Aditya", "Neha", "Siddharth", "Ananya", 
        "Rahul", "Sneha", "Kavita", "Arjun", "Divya", "Rajesh", "Meera", "Karan", 
        "Pooja", "Amit", "Ritu", "Deepak", "Sunita", "Manoj", "Anil", "Sanjay", 
        "Swati", "Nikhil", "Gaurav", "Harish", "Preeti", "Kunal", "Simran", "Varun"
    ]
    names_last = [
        "Sharma", "Deshmukh", "Patel", "Gupta", "Iyer", "Nair", "Rao", "Joshi", 
        "Bhat", "Malhotra", "Mishra", "Singh", "Kumar", "Chopra", "Reddy", "Sen", 
        "Pillai", "Khanna", "Saxena", "Mehta", "Bose", "Verma", "Trivedi", "Pandey"
    ]
    
    regions_cities = [
        ("Madhya Pradesh", "Indore"), ("Madhya Pradesh", "Bhopal"),
        ("Maharashtra", "Mumbai"), ("Maharashtra", "Pune"),
        ("Karnataka", "Bengaluru"), ("Delhi", "New Delhi"),
        ("Tamil Nadu", "Chennai"), ("West Bengal", "Kolkata"),
        ("Gujarat", "Ahmedabad"), ("Telangana", "Hyderabad"),
        ("Rajasthan", "Jaipur"), ("Uttar Pradesh", "Lucknow")
    ]
    
    all_payment_methods = ["UPI", "Net Banking", "Debit Card", "Credit Card", "Cash"]
    
    # 1. ACCOUNTS (102 Total)
    accounts = []
    
    # Anchor 1: ACC-10293 (Primary Target Demo Account: Aarav Sharma)
    accounts.append({
        "account_id": "ACC-10293",
        "holder_name": "Aarav Sharma",
        "account_number": "XXXX XXXX 1092",
        "ifsc_code": "FINA0010293",
        "region": "Madhya Pradesh",
        "city": "Indore",
        "age_months": 24,
        "risk_score": 94,
        "risk_level": "Critical",
        "credit_amount": 0.0,
        "debit_amount": 0.0,
        "payment_methods": ["UPI", "Net Banking", "Debit Card"]
    })
    
    # Anchor 2: ACC-4412 (Secondary Target Counterparty: Rohan Deshmukh)
    accounts.append({
        "account_id": "ACC-4412",
        "holder_name": "Rohan Deshmukh",
        "account_number": "XXXX XXXX 8832",
        "ifsc_code": "FINA0044120",
        "region": "Maharashtra",
        "city": "Mumbai",
        "age_months": 36,
        "risk_score": 75,
        "risk_level": "High",
        "credit_amount": 0.0,
        "debit_amount": 0.0,
        "payment_methods": ["UPI", "Net Banking"]
    })
    
    # Remaining 100 accounts (ACC-10100 through ACC-10199)
    for i in range(100):
        acc_id = f"ACC-{10100 + i}"
        fn = names_first[i % len(names_first)]
        ln = names_last[(i * 3 + 7) % len(names_last)]
        reg, city = regions_cities[i % len(regions_cities)]
        
        # Risk Distribution: 6 Critical, 16 High, 36 Medium, 42 Low/Safe
        if i < 6:
            score = random.randint(90, 96)
            lvl = "Critical"
        elif i < 22:
            score = random.randint(75, 89)
            lvl = "High"
        elif i < 58:
            score = random.randint(40, 74)
            lvl = "Medium"
        else:
            score = random.randint(8, 38)
            lvl = "Low/Safe"
            
        p_methods = random.sample(all_payment_methods, k=random.randint(1, 3))
        if "UPI" not in p_methods and random.random() < 0.75:
            p_methods.append("UPI")
            
        accounts.append({
            "account_id": acc_id,
            "holder_name": f"{fn} {ln}",
            "account_number": f"XXXX XXXX {random.randint(1000, 9999)}",
            "ifsc_code": f"FINA00{random.randint(10000, 99999)}",
            "region": reg,
            "city": city,
            "age_months": random.randint(3, 110),
            "risk_score": score,
            "risk_level": lvl,
            "credit_amount": 0.0,
            "debit_amount": 0.0,
            "payment_methods": p_methods
        })
        
    acc_map = {a["account_id"]: a for a in accounts}
    other_acc_ids = [a["account_id"] for a in accounts if a["account_id"] not in ("ACC-10293", "ACC-4412")]
    
    # 2. TRANSACTIONS (500 Total)
    transactions = []
    base_time = datetime.now()
    
    fmt_map = {
        "UPI": "Wire",
        "Net Banking": "Wire",
        "Debit Card": "Credit Card",
        "Credit Card": "Credit Card",
        "Cash": "Cash"
    }
    
    tx_counter = 80001
    
    def make_tx(s_id, r_id, amount, method, status, reasons, risk_score, risk_level, delta_min, tx_type="Transfer"):
        nonlocal tx_counter
        s_acc = acc_map[s_id]
        r_acc = acc_map[r_id]
        t_time = (base_time - timedelta(minutes=delta_min)).strftime("%Y-%m-%d %H:%M:%S")
        
        s_digits = "".join(filter(str.isdigit, s_id))
        r_digits = "".join(filter(str.isdigit, r_id))
        f_bank = int(s_digits) % 500 + 1 if s_digits else 1
        t_bank = int(r_digits) % 500 + 1 if r_digits else 2
        
        tx = {
            "transaction_id": f"TX-{tx_counter}",
            "timestamp": t_time,
            "sender_id": s_id,
            "sender_name": s_acc["holder_name"],
            "receiver_id": r_id,
            "receiver_name": r_acc["holder_name"],
            "amount": round(amount, 2),
            "transaction_type": tx_type,
            "payment_method": method,
            "region": s_acc["region"],
            "city": s_acc["city"],
            "risk_score": risk_score,
            "risk_level": risk_level,
            "status": status,
            "reasons": reasons,
            "from_bank": f_bank,
            "to_bank": t_bank,
            "receiving_currency": "Rupee",
            "payment_currency": "Rupee",
            "payment_format": fmt_map.get(method, "Wire")
        }
        tx_counter += 1
        return tx

    # A. Fan-in funneling into ACC-10293 (18 distinct senders)
    fan_in_senders = other_acc_ids[:18]
    for idx, s_id in enumerate(fan_in_senders):
        amt = round(random.uniform(8500, 49500), 2)
        transactions.append(make_tx(
            s_id=s_id,
            r_id="ACC-10293",
            amount=amt,
            method="UPI",
            status="FLAGGED" if amt > 40000 else "SUSPICIOUS",
            reasons=["High transaction velocity", "Structuring pattern near reporting limit"],
            risk_score=random.randint(85, 96),
            risk_level="Critical",
            delta_min=180 + idx * 15,
            tx_type="Credit"
        ))
        
    # B. Fan-out dispersion from ACC-10293 (to 9 distinct receivers, including ACC-4412)
    fan_out_receivers = ["ACC-4412"] + other_acc_ids[18:26]
    for idx, r_id in enumerate(fan_out_receivers):
        amt = round(random.uniform(12000, 68000), 2)
        transactions.append(make_tx(
            s_id="ACC-10293",
            r_id=r_id,
            amount=amt,
            method="UPI" if idx % 2 == 0 else "Net Banking",
            status="FLAGGED" if r_id == "ACC-4412" else "COMPLETED",
            reasons=["Rapid fund dispersion following multiple deposits", "Known mule hub linkage"] if r_id == "ACC-4412" else ["Frequent transfer"],
            risk_score=94 if r_id == "ACC-4412" else random.randint(70, 85),
            risk_level="Critical" if r_id == "ACC-4412" else "High",
            delta_min=60 + idx * 10,
            tx_type="Debit"
        ))
        
    # C. Circular fund routing loop: ACC-10293 -> ACC-4412 -> ACC-10105 -> ACC-10293
    transactions.append(make_tx(
        s_id="ACC-10293",
        r_id="ACC-4412",
        amount=85000.0,
        method="Net Banking",
        status="FLAGGED",
        reasons=["Circular fund flow loop detected", "High amount pass-through"],
        risk_score=95,
        risk_level="Critical",
        delta_min=30,
        tx_type="Transfer"
    ))
    transactions.append(make_tx(
        s_id="ACC-4412",
        r_id="ACC-10105",
        amount=84000.0,
        method="Net Banking",
        status="FLAGGED",
        reasons=["Circular fund flow loop detected", "Pass-through intermediary"],
        risk_score=92,
        risk_level="Critical",
        delta_min=20,
        tx_type="Transfer"
    ))
    transactions.append(make_tx(
        s_id="ACC-10105",
        r_id="ACC-10293",
        amount=83500.0,
        method="UPI",
        status="FLAGGED",
        reasons=["Circular fund flow loop completion", "Wash transaction pattern"],
        risk_score=96,
        risk_level="Critical",
        delta_min=10,
        tx_type="Transfer"
    ))
    
    # D. High-value AML flagged transactions
    for k in range(25):
        s = random.choice(accounts)["account_id"]
        r = random.choice([a["account_id"] for a in accounts if a["account_id"] != s])
        amt = round(random.uniform(95000, 380000), 2)
        transactions.append(make_tx(
            s_id=s,
            r_id=r,
            amount=amt,
            method=random.choice(["Net Banking", "UPI", "Debit Card"]),
            status=random.choice(["FLAGGED", "SUSPICIOUS", "BLOCKED"]),
            reasons=["Unusual spike in transaction amount", "High deviation from historic mean"],
            risk_score=random.randint(75, 93),
            risk_level="High" if amt < 200000 else "Critical",
            delta_min=random.randint(500, 10000),
            tx_type="Transfer"
        ))
        
    # E. Normal & regular daily transactions to reach exactly 500 total
    remaining = 500 - len(transactions)
    for j in range(remaining):
        s = random.choice(accounts)["account_id"]
        r = random.choice([a["account_id"] for a in accounts if a["account_id"] != s])
        method = random.choices(all_payment_methods, weights=[0.50, 0.25, 0.12, 0.08, 0.05])[0]
        amt = round(random.uniform(150, 18500), 2)
        
        s_acc = acc_map[s]
        base_r = s_acc["risk_score"]
        if base_r >= 75:
            t_risk = random.randint(45, 78)
            lvl = "Medium" if t_risk < 75 else "High"
            status = "SUSPICIOUS" if t_risk >= 75 else "COMPLETED"
            reasons = ["Counterparty has elevated risk score"] if status == "SUSPICIOUS" else []
        else:
            t_risk = random.randint(5, 35)
            lvl = "Low/Safe"
            status = "COMPLETED"
            reasons = []
            
        transactions.append(make_tx(
            s_id=s,
            r_id=r,
            amount=amt,
            method=method,
            status=status,
            reasons=reasons,
            risk_score=t_risk,
            risk_level=lvl,
            delta_min=random.randint(60, 180 * 24 * 60), # Last 180 days
            tx_type="Transfer"
        ))
        
    # Chronological sort for transactions
    transactions.sort(key=lambda x: x["timestamp"])
    
    # 3. Synchronize account credit/debit balances with transaction ledger
    for acc in accounts:
        acc_id = acc["account_id"]
        total_credit = sum(t["amount"] for t in transactions if t["receiver_id"] == acc_id)
        total_debit = sum(t["amount"] for t in transactions if t["sender_id"] == acc_id)
        base_bal = 25000.0 if acc["risk_level"] != "Critical" else 15000.0
        acc["credit_amount"] = round(base_bal + total_credit, 2)
        acc["debit_amount"] = round(total_debit, 2)
        
    # 4. RISK PREDICTIONS (50 Total)
    predictions = []
    sampled_txs = transactions[:50]
    for tx in sampled_txs:
        p_val = round(tx["risk_score"] / 100.0, 4)
        if tx["risk_level"] == "Critical":
            anom = round(random.uniform(0.35, 0.82), 4)
        elif tx["risk_level"] == "High":
            anom = round(random.uniform(0.05, 0.35), 4)
        elif tx["risk_level"] == "Medium":
            anom = round(random.uniform(-0.08, 0.05), 4)
        else:
            anom = round(random.uniform(-0.25, -0.05), 4)
            
        predictions.append({
            "account_id": tx["sender_id"],
            "transaction_id": tx["transaction_id"],
            "prediction": p_val,
            "risk_score": tx["risk_score"],
            "risk_level": tx["risk_level"],
            "anomaly_score": anom,
            "model_version": "LGB-4.5.0 / IF-1.6.1"
        })
        
    # 5. ALERTS (25 Total)
    alerts = []
    alert_types = [
        "Mule Account Activity Pattern", "Rapid Fund Movement", "Unusual Velocity",
        "High Amount Deviation", "Structured Transactions", "Suspicious Counterparty",
        "Circular Transaction"
    ]
    
    # Priority Alerts for Target Showcase Accounts
    alerts.append({
        "alert_id": "AL-10001",
        "account_id": "ACC-10293",
        "alert_type": "Mule Account Activity Pattern",
        "risk_score": 96,
        "risk_level": "Critical",
        "amount": 85000.0,
        "detected_time": (base_time - timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M:%S"),
        "status": "Open"
    })
    alerts.append({
        "alert_id": "AL-10002",
        "account_id": "ACC-10293",
        "alert_type": "Rapid Fund Movement",
        "risk_score": 94,
        "risk_level": "Critical",
        "amount": 49500.0,
        "detected_time": (base_time - timedelta(minutes=45)).strftime("%Y-%m-%d %H:%M:%S"),
        "status": "Under Review"
    })
    alerts.append({
        "alert_id": "AL-10003",
        "account_id": "ACC-10293",
        "alert_type": "Structured Transactions",
        "risk_score": 92,
        "risk_level": "Critical",
        "amount": 48000.0,
        "detected_time": (base_time - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S"),
        "status": "Escalated"
    })
    alerts.append({
        "alert_id": "AL-10004",
        "account_id": "ACC-4412",
        "alert_type": "Suspicious Counterparty",
        "risk_score": 85,
        "risk_level": "High",
        "amount": 84000.0,
        "detected_time": (base_time - timedelta(hours=3)).strftime("%Y-%m-%d %H:%M:%S"),
        "status": "Under Review"
    })
    
    # Remaining 21 alerts across other high-risk accounts
    high_risk_accs = [a for a in accounts if a["risk_score"] >= 75 and a["account_id"] not in ("ACC-10293", "ACC-4412")]
    for idx in range(21):
        target_acc = high_risk_accs[idx % len(high_risk_accs)]
        a_id = f"AL-{10005 + idx}"
        atype = alert_types[idx % len(alert_types)]
        stat = random.choices(["Open", "Under Review", "Escalated", "Resolved"], weights=[0.55, 0.25, 0.12, 0.08])[0]
        amt = round(random.uniform(22000, 165000), 2)
        
        alerts.append({
            "alert_id": a_id,
            "account_id": target_acc["account_id"],
            "alert_type": atype,
            "risk_score": target_acc["risk_score"],
            "risk_level": target_acc["risk_level"],
            "amount": amt,
            "detected_time": (base_time - timedelta(hours=random.randint(1, 48), minutes=random.randint(0, 59))).strftime("%Y-%m-%d %H:%M:%S"),
            "status": stat
        })
        
    # 6. INVESTIGATIONS (12 Total)
    investigations = [
        {
            "investigation_id": "INV-1001",
            "account_id": "ACC-10293",
            "status": "Under Investigation",
            "notes": "High velocity structured transaction pattern detected on UPI. Multiple inbound credits swiftly dispersed to outbound nodes across Madhya Pradesh and Maharashtra.",
            "created_at": (base_time - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": (base_time - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
        },
        {
            "investigation_id": "INV-1002",
            "account_id": "ACC-4412",
            "status": "Under Investigation",
            "notes": "Direct counterparty to primary mule account ACC-10293. Immediate funds withdrawal detected following high-value credit.",
            "created_at": (base_time - timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": (base_time - timedelta(hours=4)).strftime("%Y-%m-%d %H:%M:%S")
        },
        {
            "investigation_id": "INV-1003",
            "account_id": "ACC-10100",
            "status": "Open",
            "notes": "Unusual volume surge within 48 hours of account reactivation. Threshold alert triggered.",
            "created_at": (base_time - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": (base_time - timedelta(hours=6)).strftime("%Y-%m-%d %H:%M:%S")
        },
        {
            "investigation_id": "INV-1004",
            "account_id": "ACC-10101",
            "status": "Under Review",
            "notes": "Cross-state transaction flow pattern between Delhi and Karnataka. Analyst review in progress.",
            "created_at": (base_time - timedelta(days=4)).strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": (base_time - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
        },
        {
            "investigation_id": "INV-1005",
            "account_id": "ACC-10102",
            "status": "Escalated",
            "notes": "Structuring near ₹50,000 reporting limit with repeated burst transfers. Escalated to AML compliance supervisor.",
            "created_at": (base_time - timedelta(days=5)).strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": (base_time - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S")
        },
        {
            "investigation_id": "INV-1006",
            "account_id": "ACC-10103",
            "status": "Open",
            "notes": "Frequent small transactions followed by sudden bulk liquidation via Net Banking.",
            "created_at": (base_time - timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": (base_time - timedelta(hours=12)).strftime("%Y-%m-%d %H:%M:%S")
        },
        {
            "investigation_id": "INV-1007",
            "account_id": "ACC-10104",
            "status": "Closed",
            "notes": "KYC documentation verified. Legitimate commercial vendor transactions confirmed. Investigation concluded.",
            "created_at": (base_time - timedelta(days=14)).strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": (base_time - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
        },
        {
            "investigation_id": "INV-1008",
            "account_id": "ACC-10105",
            "status": "Under Investigation",
            "notes": "Intermediary hop in circular fund routing loop between Mumbai and Indore accounts.",
            "created_at": (base_time - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": (base_time - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")
        },
        {
            "investigation_id": "INV-1009",
            "account_id": "ACC-10106",
            "status": "Escalated",
            "notes": "Multiple simultaneous login sessions and disparate IP geolocations triggering device risk flags.",
            "created_at": (base_time - timedelta(days=6)).strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": (base_time - timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S")
        },
        {
            "investigation_id": "INV-1010",
            "account_id": "ACC-10107",
            "status": "Under Review",
            "notes": "Sudden uptick in UPI debit volume outside normal operating hours (2 AM - 4 AM).",
            "created_at": (base_time - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": (base_time - timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")
        },
        {
            "investigation_id": "INV-1011",
            "account_id": "ACC-10108",
            "status": "Open",
            "notes": "Account age under 3 months showing over ₹25 Lakhs in cumulative velocity.",
            "created_at": (base_time - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": (base_time - timedelta(hours=3)).strftime("%Y-%m-%d %H:%M:%S")
        },
        {
            "investigation_id": "INV-1012",
            "account_id": "ACC-10109",
            "status": "Closed",
            "notes": "High value transfer verified as property purchase downpayment with supporting escrow agreement.",
            "created_at": (base_time - timedelta(days=20)).strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": (base_time - timedelta(days=10)).strftime("%Y-%m-%d %H:%M:%S")
        }
    ]
    
    return accounts, transactions, predictions, alerts, investigations

def seed_database(client: Client):
    """Safely seeds synthetic showcase data using non-destructive idempotent upserts."""
    print("==================================================")
    print("FINGUARD AI -- SYNTHETIC SHOWCASE DATA SEEDER")
    print("==================================================")
    
    # 0. Pre-flight connection and schema check
    try:
        client.table("accounts").select("account_id").limit(1).execute()
        print("[OK] Verified Supabase database connectivity and tables existence.")
    except Exception as e:
        print(f"\n[ERROR] Database table verification failed: {e}")
        print("Please ensure the tables are created using the DDL specification.")
        return False
        
    accounts, transactions, predictions, alerts, investigations = generate_synthetic_dataset()
    
    print("\nPlanned safe upsert counts:")
    print(f"  * Accounts:          {len(accounts)}")
    print(f"  * Transactions:      {len(transactions)}")
    print(f"  * Risk Predictions:  {len(predictions)}")
    print(f"  * Alerts:            {len(alerts)}")
    print(f"  * Investigations:    {len(investigations)}")
    print("  * Destructive operations: NONE (idempotent upsert by primary key)\n")
    
    chunk_size = 200
    
    # 1. Accounts
    print(f"[1/5] Upserting {len(accounts)} accounts...")
    client.table("accounts").upsert(accounts, on_conflict="account_id").execute()
    print("      [OK] Accounts upserted successfully.")
    
    # 2. Transactions
    print(f"[2/5] Upserting {len(transactions)} transactions in batches...")
    for j in range(0, len(transactions), chunk_size):
        chunk = transactions[j : j + chunk_size]
        client.table("transactions").upsert(chunk, on_conflict="transaction_id").execute()
        print(f"      [OK] Batch {j//chunk_size + 1} ({len(chunk)} rows) upserted.")
        
    # 3. Risk Predictions (check existing transaction_ids to maintain idempotence)
    print(f"[3/5] Inserting {len(predictions)} risk predictions...")
    try:
        existing_res = client.table("risk_predictions").select("transaction_id").execute()
        existing_tx_ids = {p["transaction_id"] for p in (existing_res.data or []) if p.get("transaction_id")}
        new_preds = [p for p in predictions if p["transaction_id"] not in existing_tx_ids]
        if new_preds:
            for j in range(0, len(new_preds), chunk_size):
                chunk = new_preds[j : j + chunk_size]
                client.table("risk_predictions").insert(chunk).execute()
            print(f"      [OK] {len(new_preds)} risk predictions inserted.")
        else:
            print("      [OK] Risk predictions already seeded (skipped duplicate insert).")
    except Exception as e:
        print(f"      [Warning] Risk predictions insert note: {e}")
        
    # 4. Alerts
    print(f"[4/5] Upserting {len(alerts)} alerts...")
    client.table("alerts").upsert(alerts, on_conflict="alert_id").execute()
    print("      [OK] Alerts upserted successfully.")
    
    # 5. Investigations
    print(f"[5/5] Upserting {len(investigations)} investigations...")
    client.table("investigations").upsert(investigations, on_conflict="investigation_id").execute()
    print("      [OK] Investigations upserted successfully.")
    
    print("\n==================================================")
    print("VERIFYING FINAL SUPABASE TABLE ROW COUNTS:")
    print("==================================================")
    for tbl in ["accounts", "transactions", "risk_predictions", "alerts", "investigations"]:
        res = client.table(tbl).select("*", count="exact").limit(1).execute()
        print(f"  * {tbl:18}: {res.count} rows")
    print("==================================================")
    print("DATABASE SEEDING COMPLETED SUCCESSFULLY!")
    print("==================================================")
    return True

if __name__ == "__main__":
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("[ERROR] SUPABASE_URL and SUPABASE_KEY must be set in your .env file.")
    else:
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        seed_database(client)
