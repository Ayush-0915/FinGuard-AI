import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables strictly
backend_env = os.path.join(os.path.dirname(__file__), ".env")
root_env = os.path.join(os.path.dirname(__file__), "..", ".env")

if os.path.exists(backend_env):
    load_dotenv(backend_env)
elif os.path.exists(root_env):
    load_dotenv(root_env)
else:
    load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError(
        "CRITICAL DATABASE ERROR: SUPABASE_URL and SUPABASE_KEY environment variables are missing! "
        "MuleGuard requires a valid Supabase database setup. Mock fallbacks are disabled."
    )

# Create Supabase Client
client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def fetch_accounts(search="", risk_level="All", region="All"):
    query = client.table("accounts").select("*")
    if risk_level and risk_level != "All":
        query = query.eq("risk_level", risk_level)
    if region and region != "All":
        query = query.eq("region", region)
        
    res = query.execute()
    data = res.data
    
    if search:
        s_lower = search.lower()
        data = [
            a for a in data 
            if s_lower in str(a.get("account_id", "")).lower() 
            or s_lower in str(a.get("holder_name", "")).lower()
            or s_lower in str(a.get("account_number", "")).lower()
        ]
    # Return sorted by risk score descending
    return sorted(data, key=lambda x: x.get("risk_score", 0), reverse=True)

def fetch_account_detail(acc_id):
    res = client.table("accounts").select("*").eq("account_id", acc_id).execute()
    if res.data:
        return res.data[0]
    return None

def fetch_transactions(account_id=None, search="", risk_level="All", payment_method="All"):
    query = client.table("transactions").select("*")
    if account_id:
        query = query.or_(f"sender_id.eq.{account_id},receiver_id.eq.{account_id}")
    if risk_level and risk_level != "All":
        query = query.eq("risk_level", risk_level)
    if payment_method and payment_method != "All":
        query = query.eq("payment_method", payment_method)
        
    res = query.execute()
    data = res.data
    
    if search:
        s_lower = search.lower()
        data = [
            t for t in data
            if s_lower in str(t.get("transaction_id", "")).lower()
            or s_lower in str(t.get("sender_name", "")).lower()
            or s_lower in str(t.get("receiver_name", "")).lower()
            or s_lower in str(t.get("sender_id", "")).lower()
            or s_lower in str(t.get("receiver_id", "")).lower()
        ]
    # Return sorted descending by transaction timestamp
    return sorted(data, key=lambda x: x.get("timestamp", ""), reverse=True)

def fetch_alerts():
    res = client.table("alerts").select("*").execute()
    return sorted(res.data, key=lambda x: x.get("detected_time", ""), reverse=True)

def update_account_score(acc_id, new_score, new_risk_level):
    client.table("accounts").update({
        "risk_score": new_score,
        "risk_level": new_risk_level
    }).eq("account_id", acc_id).execute()

def insert_transaction(tx):
    client.table("transactions").insert(tx).execute()

def insert_risk_prediction(pred):
    client.table("risk_predictions").insert(pred).execute()
