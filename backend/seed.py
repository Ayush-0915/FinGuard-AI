"""
MuleGuard Supabase Seeding and Migration Tool

This script assists in setting up the Supabase PostgreSQL database tables and 
seeding them with the synthetic mock data required for MuleGuard.

INSTRUCTIONS:
1. Copy the SQL DDL block below and execute it in your Supabase Project "SQL Editor".
2. Create your `backend/.env` file with SUPABASE_URL and SUPABASE_KEY.
3. Run this script to populate the tables:
   ./venv/bin/python backend/seed.py
"""

import os
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv(os.path.expanduser("~/.env"))
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")



# SQL DDL Script for copy-paste inside Supabase SQL Editor
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

def generate_and_seed_data(client: Client):
    print("Starting data generation and database seeding...")
    
    # Check tables status by fetching first row
    try:
        client.table("accounts").select("account_id").limit(1).execute()
        print("✓ Database tables verified.")
    except Exception as e:
        print("\n[ERROR] Verified connection failed or tables do not exist in Supabase.")
        print("Please execute the DDL queries inside your Supabase project SQL Editor first!")
        print("-" * 50)
        print(SQL_DDL)
        print("-" * 50)
        return

    # Delete existing entries to prevent primary key duplicates on re-runs
    print("Clearing existing Supabase data (clean seed)...")
    try:
        client.table("alerts").delete().neq("alert_id", "").execute()
        client.table("transactions").delete().neq("transaction_id", "").execute()
        try:
            client.table("investigations").delete().neq("investigation_id", "").execute()
        except Exception:
            pass
        client.table("accounts").delete().neq("account_id", "").execute()
        print("✓ Staging tables cleared.")
    except Exception as e:
        print(f"Staging tables clear error: {e}")

    # Seed list definitions
    names = [
        "Aarav Sharma", "Ananya Iyer", "Rohan Gupta", "Priya Nair", "Vikram Patel",
        "Neha Deshmukh", "Rahul Verma", "Sneha Rao", "Aditya Joshi", "Kavita Reddy",
        "Siddharth Sen", "Meera Pillai", "Arjun Bhat", "Divya Malhotra", "Karan Johar",
        "Diya Mishra", "Vijay Mallya", "Rajesh Khanna", "Amitabh Bachchan", "Shah Rukh"
    ]
    
    regions = [
        ("Madhya Pradesh", "Indore"), ("Maharashtra", "Mumbai"), ("Karnataka", "Bengaluru"),
        ("Delhi", "New Delhi"), ("Tamil Nadu", "Chennai"), ("West Bengal", "Kolkata"),
        ("Gujarat", "Ahmedabad"), ("Telangana", "Hyderabad"), ("Rajasthan", "Jaipur")
    ]
    
    payment_methods = ["UPI", "Net Banking", "Debit Card", "Credit Card", "Cash"]
    
    accounts = []
    
    # 1. Target Account Profiles
    target_id = "ACC-10293"
    accounts.append({
        "account_id": target_id,
        "holder_name": "Aarav Sharma",
        "account_number": "XXXX XXXX 1092",
        "ifsc_code": "MULE0010293",
        "region": "Madhya Pradesh",
        "city": "Indore",
        "age_months": 24,
        "risk_score": 94,
        "risk_level": "Critical",
        "credit_amount": 142500.00,
        "debit_amount": 139000.00,
        "payment_methods": ["UPI", "Net Banking", "Debit Card"]
    })
    
    accounts.append({
        "account_id": "ACC-4412",
        "holder_name": "Rohan Deshmukh",
        "account_number": "XXXX XXXX 8832",
        "ifsc_code": "MULE0044120",
        "region": "Maharashtra",
        "city": "Mumbai",
        "age_months": 36,
        "risk_score": 75,
        "risk_level": "High",
        "credit_amount": 92000.00,
        "debit_amount": 89000.00,
        "payment_methods": ["UPI", "Net Banking"]
    })
    
    # Generate 100 other accounts
    for i in range(100):
        acc_id = f"ACC-{100 + i}"
        reg, city = random.choice(regions)
        r_score = random.randint(5, 78)
        
        if r_score >= 75:
            r_lvl = "High"
        elif r_score >= 40:
            r_lvl = "Medium"
        else:
            r_lvl = "Low/Safe"
            
        accounts.append({
            "account_id": acc_id,
            "holder_name": f"{random.choice(names)} {random.choice(['Singh', 'Kumar', 'Sharma', 'Patel', 'Iyer', 'Deshmukh'])}",
            "account_number": f"XXXX XXXX {random.randint(1000, 9999)}",
            "ifsc_code": f"SBIN00{random.randint(10000, 99999)}",
            "region": reg,
            "city": city,
            "age_months": random.randint(1, 120),
            "risk_score": r_score,
            "risk_level": r_lvl,
            "credit_amount": round(random.uniform(500, 50000), 2),
            "debit_amount": round(random.uniform(500, 50000), 2),
            "payment_methods": random.sample(payment_methods, k=random.randint(1, 3))
        })
        
    print(f"Inserting {len(accounts)} account records...")
    client.table("accounts").insert(accounts).execute()
    print("✓ Accounts seeded.")
    
    # 2. Seed Alerts
    alerts = []
    alert_types = ["Rapid Fund Movement", "Unusual Velocity", "High Amount Deviation", "Structured Transactions", "Mule Account Activity Pattern"]
    
    # Alert for target Aarav Sharma
    alerts.append({
        "alert_id": "AL-10492",
        "account_id": target_id,
        "alert_type": "Mule Account Activity Pattern",
        "risk_score": 94,
        "risk_level": "Critical",
        "amount": 95000.0,
        "detected_time": (datetime.now() - timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S"),
        "status": "Open"
    })
    
    high_risk_accs = [a for a in accounts if a["risk_score"] >= 70 and a["account_id"] != target_id]
    for idx, acc in enumerate(high_risk_accs[:8]):
        alerts.append({
            "alert_id": f"AL-{10493 + idx}",
            "account_id": acc["account_id"],
            "alert_type": random.choice(alert_types),
            "risk_score": acc["risk_score"],
            "risk_level": acc["risk_level"],
            "amount": round(random.uniform(1000, 50000), 2),
            "detected_time": (datetime.now() - timedelta(minutes=random.randint(10, 1440))).strftime("%Y-%m-%d %H:%M:%S"),
            "status": "Open"
        })
        
    print(f"Inserting {len(alerts)} alerts...")
    client.table("alerts").insert(alerts).execute()
    print("✓ Alerts seeded.")
    
    # 3. Seed Transactions
    transactions = []
    
    # Aarav Sharma critical transaction
    transactions.append({
        "transaction_id": "TX-82921",
        "timestamp": (datetime.now() - timedelta(minutes=2)).strftime("%Y-%m-%d %H:%M:%S"),
        "sender_id": "ACC-4412",
        "sender_name": "Rohan Deshmukh",
        "receiver_id": target_id,
        "receiver_name": "Aarav Sharma",
        "amount": 8500.0,
        "transaction_type": "Credit",
        "payment_method": "UPI",
        "region": "Madhya Pradesh",
        "city": "Indore",
        "risk_score": 94,
        "risk_level": "Critical",
        "status": "FLAGGED",
        "reasons": ["Unusual amount", "New beneficiary", "High transaction velocity", "Suspicious network relationship", "Unusual time"],
        "from_bank": 44,
        "to_bank": 11,
        "receiving_currency": "Rupee",
        "payment_currency": "Rupee",
        "payment_format": "Wire"
    })
    
    # Generate 1500 historical transactions
    acc_map = {a["account_id"]: a for a in accounts}
    acc_ids = list(acc_map.keys())
    
    # Currency encodings helper
    format_map = {
        "UPI": "Wire", "Net Banking": "Wire",
        "Debit Card": "Credit Card", "Credit Card": "Credit Card",
        "Cash": "Cash"
    }
    
    for i in range(1500):
        s_id = random.choice(acc_ids)
        r_id = random.choice(acc_ids)
        while r_id == s_id:
            r_id = random.choice(acc_ids)
            
        sender = acc_map[s_id]
        receiver = acc_map[r_id]
        amt = round(random.uniform(50, 15000), 2)
        tx_type = random.choice(["Credit", "Debit"])
        method = random.choice(sender["payment_methods"])
        
        risk = max(sender["risk_score"], receiver["risk_score"]) - random.randint(0, 15)
        risk = max(5, min(99, risk))
        
        if risk >= 85:
            risk_lvl = "Critical"
            status = "FLAGGED"
            reasons = random.sample(["Unusual amount", "High velocity", "Suspicious sender", "Regional Anomaly"], k=random.randint(1, 2))
        else:
            risk_lvl = "Low/Safe" if risk < 40 else "Medium"
            status = "APPROVED"
            reasons = []
            
        # Parse bank codes
        sender_digits = "".join(filter(str.isdigit, s_id))
        receiver_digits = "".join(filter(str.isdigit, r_id))
        f_bank = int(sender_digits) % 500 + 1 if sender_digits else 1
        t_bank = int(receiver_digits) % 500 + 1 if receiver_digits else 2
        
        transactions.append({
            "transaction_id": f"TX-{82922 + i}",
            "timestamp": (datetime.now() - timedelta(days=random.randint(0, 180), hours=random.randint(0, 23), minutes=random.randint(0, 59))).strftime("%Y-%m-%d %H:%M:%S"),
            "sender_id": s_id,
            "sender_name": sender["holder_name"],
            "receiver_id": r_id,
            "receiver_name": receiver["holder_name"],
            "amount": amt,
            "transaction_type": tx_type,
            "payment_method": method,
            "region": sender["region"],
            "city": sender["city"],
            "risk_score": risk,
            "risk_level": risk_lvl,
            "status": status,
            "reasons": reasons,
            "from_bank": f_bank,
            "to_bank": t_bank,
            "receiving_currency": "Rupee",
            "payment_currency": "Rupee",
            "payment_format": format_map.get(method, "Wire")
        })
        
    # Sort chronological
    transactions.sort(key=lambda x: x["timestamp"])
    
    # Batch insertion in chunks to prevent Supabase payload size limits
    chunk_size = 300
    print(f"Inserting {len(transactions)} transaction records in batches...")
    for j in range(0, len(transactions), chunk_size):
        chunk = transactions[j : j + chunk_size]
        client.table("transactions").insert(chunk).execute()
        print(f" ✓ Batch {j//chunk_size + 1} ({len(chunk)} rows) inserted.")
        
    # 4. Seed Investigations
    investigations = [
        {
            "investigation_id": "INV-10492",
            "account_id": "ACC-10293",
            "status": "Under Investigation",
            "notes": "High velocity structured transaction pattern detected on UPI. Regional anomaly match in Madhya Pradesh.",
            "created_at": (datetime.now() - timedelta(hours=12)).strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": (datetime.now() - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")
        },
        {
            "investigation_id": "INV-10493",
            "account_id": "ACC-4412",
            "status": "Open",
            "notes": "Sender associated with flagged transactions. Ongoing review of transaction velocities.",
            "created_at": (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
        }
    ]
    try:
        print(f"Inserting {len(investigations)} investigations...")
        client.table("investigations").insert(investigations).execute()
        print("✓ Investigations seeded.")
    except Exception as e:
        print(f"Investigations seed error: {e}")
        
    print("==================================================")
    print("DATABASE SEEDING COMPLETED SUCCESSFULLY!")
    print("==================================================")

if __name__ == "__main__":
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("[ERROR] SUPABASE_URL and SUPABASE_KEY must be set in your backend/.env file.")
    else:
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        generate_and_seed_data(client)
