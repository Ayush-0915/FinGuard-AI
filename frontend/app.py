import sys
import os
import random
import requests
import json
import websocket
from datetime import datetime, timedelta

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QPushButton, QLineEdit, QTableWidget,
    QTableWidgetItem, QHeaderView, QStackedWidget, QTabWidget,
    QDialog, QMessageBox, QCheckBox, QFrame, QScrollArea, QSplitter, QFormLayout, QProgressBar
)
from PySide6.QtCore import Qt, QTimer, QSize, Signal, Slot, QThread
from PySide6.QtGui import QFont, QColor, QPainter, QBrush, QPen, QPainterPath, QPixmap, QIcon

# Matplotlib & NetworkX Imports
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.patches import Circle
import networkx as nx

def format_money(val_in_inr):
    # Format value dynamically in Lakhs (L) or Crores (Cr)
    if val_in_inr >= 10000000:
        return f"₹{val_in_inr / 10000000:.2f} Cr"
    elif val_in_inr >= 100000:
        return f"₹{val_in_inr / 100000:.2f} L"
    elif val_in_inr >= 1000:
        return f"₹{val_in_inr / 1000:.1f} K"
    else:
        return f"₹{val_in_inr:,.2f}"

# ---------------------------------------------------------
# CONSTANTS & DESIGN SYSTEM (SECTIONS 1, 2 & BEHANCE COLOR COMBO)
# ---------------------------------------------------------
COLOR_SIDEBAR_BG = "#FFFFFF"      # Clean White Sidebar
COLOR_PRIMARY_BLUE = "#155EEF"    # Professional Blue
COLOR_BG = "#F3F5F9"              # Soft Gray-Blue Background (Behance style)
COLOR_CARD_BG = "#FFFFFF"         # White Card Backgrounds
COLOR_TEXT_PRIMARY = "#172B4D"    # Dark Navy Text
COLOR_TEXT_SECONDARY = "#667085"  # Slate Text
COLOR_TEXT_MUTED = "#98A2B3"      # Gray Muted Text
COLOR_BORDER = "#E4E7EC"          # Light Border

# Risk colors
COLOR_RISK_CRITICAL = "#D92D20"   # Red
COLOR_RISK_HIGH = "#F79009"       # Orange
COLOR_RISK_MEDIUM = "#EAAA08"     # Amber
COLOR_RISK_LOW = "#039855"        # Green

FONT_FAMILY = "Inter"

GLOBAL_STYLE = f"""
QMainWindow {{
    background-color: {COLOR_BG};
}}

QWidget {{
    font-family: "{FONT_FAMILY}", "Segoe UI", sans-serif;
    color: {COLOR_TEXT_PRIMARY};
}}

QLabel {{
    font-size: 14px;
}}

/* Sidebar Elements (Behance Style) */
#SidebarFrame {{
    background-color: {COLOR_SIDEBAR_BG};
    border-right: 1px solid {COLOR_BORDER};
}}

#SidebarHeader {{
    padding: 25px 20px;
    border-bottom: 1px solid {COLOR_BORDER};
}}

#SidebarTitle {{
    color: {COLOR_TEXT_PRIMARY};
    font-size: 18px;
    font-weight: bold;
}}

#SidebarSubtitle {{
    color: {COLOR_TEXT_SECONDARY};
    font-size: 11px;
}}

#SidebarSectionLabel {{
    color: {COLOR_TEXT_MUTED};
    font-size: 11px;
    font-weight: bold;
    padding-left: 20px;
    margin-top: 15px;
    margin-bottom: 5px;
}}

QPushButton[class="SidebarSectionHeader"] {{
    background-color: transparent;
    color: {COLOR_TEXT_MUTED};
    border: none;
    text-align: left;
    padding: 15px 20px 5px 15px;
    font-size: 11px;
    font-weight: bold;
}}

QPushButton[class="SidebarSectionHeader"]:hover {{
    color: {COLOR_PRIMARY_BLUE};
}}

QPushButton[class="SidebarButton"] {{
    background-color: transparent;
    color: {COLOR_TEXT_SECONDARY};
    border: none;
    text-align: left;
    padding: 10px 20px;
    font-size: 13px;
    border-left: 3px solid transparent;
}}

QPushButton[class="SidebarButton"]:hover {{
    background-color: #F8F9FC;
    color: {COLOR_PRIMARY_BLUE};
}}

QPushButton[class="SidebarButton"]:checked {{
    background-color: #F0F4FE;
    color: {COLOR_PRIMARY_BLUE};
    font-weight: bold;
    border-left: 3px solid {COLOR_PRIMARY_BLUE};
}}

/* Top Header Bar */
#HeaderFrame {{
    background-color: #FFFFFF;
    border-bottom: 1px solid {COLOR_BORDER};
    padding: 15px 30px;
}}

#HeaderTitle {{
    font-size: 20px;
    font-weight: bold;
    color: {COLOR_TEXT_PRIMARY};
}}

#HeaderSubtitle {{
    font-size: 12px;
    color: {COLOR_TEXT_SECONDARY};
}}

/* Card Frames */
QFrame[class="Card"] {{
    background-color: #FFFFFF;
    border: 1px solid {COLOR_BORDER};
    border-radius: 8px;
}}

/* Tables */
QTableWidget {{
    background-color: #FFFFFF;
    border: 1px solid {COLOR_BORDER};
    gridline-color: {COLOR_BORDER};
    font-size: 13px;
    selection-background-color: #F2F4FE;
    selection-color: {COLOR_TEXT_PRIMARY};
}}

QHeaderView::section {{
    background-color: #F8F9FC;
    color: {COLOR_TEXT_SECONDARY};
    padding: 10px;
    font-weight: bold;
    font-size: 12px;
    border: none;
    border-bottom: 1px solid {COLOR_BORDER};
}}

/* Inputs */
QLineEdit {{
    border: 1px solid {COLOR_BORDER};
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 13px;
    background-color: #FFFFFF;
}}

QLineEdit:focus {{
    border: 1px solid {COLOR_PRIMARY_BLUE};
}}

/* Buttons */
QPushButton[class="PrimaryButton"] {{
    background-color: {COLOR_PRIMARY_BLUE};
    color: #FFFFFF;
    font-weight: bold;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-size: 13px;
}}

QPushButton[class="PrimaryButton"]:hover {{
    background-color: #104EC6;
}}

QPushButton[class="SecondaryButton"] {{
    background-color: #FFFFFF;
    color: {COLOR_TEXT_PRIMARY};
    border: 1px solid {COLOR_BORDER};
    border-radius: 6px;
    padding: 8px 16px;
    font-size: 13px;
}}

QPushButton[class="SecondaryButton"]:hover {{
    background-color: #F8F9FC;
}}

/* Dynamic Tab Bar Styles */
QTabBar::tab {{
    background-color: transparent;
    color: {COLOR_TEXT_SECONDARY};
    padding: 10px 20px;
    font-size: 13px;
    font-weight: bold;
    border: none;
    border-bottom: 2px solid transparent;
}}

QTabBar::tab:hover {{
    color: {COLOR_PRIMARY_BLUE};
}}

QTabBar::tab:selected {{
    color: {COLOR_PRIMARY_BLUE};
    border-bottom: 2px solid {COLOR_PRIMARY_BLUE};
}}

QTabWidget::pane {{
    border: 1px solid {COLOR_BORDER};
    background-color: #FFFFFF;
    border-radius: 8px;
}}

/* Footer Status Bar */
#FooterFrame {{
    background-color: #FFFFFF;
    border-top: 1px solid {COLOR_BORDER};
    padding: 6px 30px;
}}
"""

class AnalyticsWebSocketThread(QThread):
    data_received = Signal(dict)
    
    def __init__(self, ws_url="ws://127.0.0.1:8000/ws/analytics"):
        super().__init__()
        self.ws_url = ws_url
        self.running = True
        self.ws = None
        
    def run(self):
        while self.running:
            try:
                self.ws = websocket.WebSocketApp(
                    self.ws_url,
                    on_message=self.on_message,
                    on_error=self.on_error,
                    on_close=self.on_close
                )
                self.ws.run_forever()
            except Exception as e:
                print(f"WS thread connection error: {e}")
            self.msleep(3000) # retry after 3 seconds if disconnected
            
    def on_message(self, ws, message):
        try:
            data = json.loads(message)
            self.data_received.emit(data)
        except Exception as e:
            print(f"Error parsing WS message: {e}")
            
    def on_error(self, ws, error):
        print(f"WS error: {error}")
        
    def on_close(self, ws, close_status_code, close_msg):
        print("WS connection closed")
        
    def stop(self):
        self.running = False
        if self.ws:
            self.ws.close()

# ---------------------------------------------------------
# SANDBOX RESILIENT API CLIENT (FORCED LOCAL BY DEFAULT)
# ---------------------------------------------------------
class ApiClient:
    def __init__(self, base_url=None):
        if base_url is None:
            base_url = os.getenv("MULEGUARD_API_URL")
        if base_url is None:
            try:
                if os.path.exists("config.json"):
                    with open("config.json", "r") as f:
                        cfg = json.load(f)
                        base_url = cfg.get("api_url")
            except Exception:
                pass
        if base_url is None:
            base_url = "http://127.0.0.1:8000"
        self.base_url = base_url.rstrip("/")
        self.is_connected = False
        self.local_mode = True # Default local sandbox
        self.cached_dashboard = None
        self.cached_regional = None
        self.cached_payment_methods = None
        self.cached_analytics_monthly = None
        
        self.local_accounts = {}
        self.local_transactions = []
        self.local_alerts = []
        self._initialize_local_mock_db()
        self.check_health()
        
    def check_health(self):
        try:
            r = requests.get(f"{self.base_url}/health", timeout=0.5)
            if r.status_code == 200:
                self.is_connected = True
                self.local_mode = False
                return r.json()
        except Exception:
            pass
        self.is_connected = False
        self.local_mode = True
        return {
            "status": "warning",
            "api": "offline (sandbox)",
            "database": "offline",
            "model": "loaded (local)"
        }
        
    def login(self, emp_id, password):
        if not self.local_mode:
            try:
                r = requests.post(f"{self.base_url}/login", json={"employee_id": emp_id, "password": password}, timeout=2.0)
                if r.status_code == 200:
                    return r.json()
            except Exception as e:
                print(f"API login error: {e}")
        # Fallback
        if emp_id == "admin" or "@" in emp_id:
            return {"status": "success", "employee_id": emp_id, "token": "local-token-1234"}
        return None
        
    def get_dashboard(self):
        if self.cached_dashboard:
            return self.cached_dashboard
        if not self.local_mode:
            try:
                r = requests.get(f"{self.base_url}/dashboard", timeout=2.0)
                if r.status_code == 200:
                    return r.json()
            except Exception as e:
                print(f"API dashboard error: {e}")
                
        # Fallback
        fraud_cnt = sum(1 for tx in self.local_transactions if tx["status"] == "FLAGGED")
        total_credit = sum(a["credit_amount"] for a in self.local_accounts.values())
        total_debit = sum(a["debit_amount"] for a in self.local_accounts.values())
        recent_alerts = self.local_alerts[:5]
        susp_accounts = [a for a in self.local_accounts.values() if a["risk_score"] >= 80][:6]
        return {
            "total_accounts": len(self.local_accounts),
            "total_tx_amount": sum(tx["amount"] for tx in self.local_transactions),
            "total_credit": total_credit,
            "total_debit": total_debit,
            "fraud_transactions": fraud_cnt,
            "active_alerts": len(self.local_alerts),
            "recent_alerts": recent_alerts,
            "suspicious_accounts": susp_accounts,
            "chart_data": {
                "labels": ["Mar", "Apr", "May", "Jun", "Jul", "Aug"],
                "total": [450, 520, 610, 580, 710, 840],
                "credit": [220, 270, 310, 290, 360, 430],
                "debit": [230, 250, 300, 290, 350, 410],
                "fraud": [2, 3, 5, 6, 9, 14]
            }
        }
        
    def get_accounts(self, search="", risk_level="All", region="All"):
        if not self.local_mode:
            try:
                params = {"search": search, "risk_level": risk_level, "region": region}
                r = requests.get(f"{self.base_url}/accounts", params=params, timeout=2.0)
                if r.status_code == 200:
                    return r.json()
            except Exception as e:
                print(f"API accounts error: {e}")
                
        # Fallback
        filtered = list(self.local_accounts.values())
        if search:
            s_lower = search.lower()
            filtered = [
                a for a in filtered
                if s_lower in a["account_id"].lower()
                or s_lower in a["holder_name"].lower()
                or s_lower in a["account_number"].lower()
            ]
        if risk_level and risk_level != "All":
            filtered = [a for a in filtered if a["risk_level"].lower() == risk_level.lower()]
        if region and region != "All":
            filtered = [a for a in filtered if a["region"].lower() == region.lower()]
            
        filtered.sort(key=lambda x: x["risk_score"], reverse=True)
        return {"total": len(filtered), "accounts": filtered}
        
    def get_account_detail(self, acc_id):
        if not self.local_mode:
            try:
                r = requests.get(f"{self.base_url}/accounts/{acc_id}", timeout=2.0)
                if r.status_code == 200:
                    return r.json()
            except Exception as e:
                print(f"API account detail error: {e}")
        # Fallback
        return self.local_accounts.get(acc_id)
        
    def get_transactions(self, account_id=None, search="", risk_level="All", payment_method="All"):
        if not self.local_mode:
            try:
                params = {"account_id": account_id, "search": search, "risk_level": risk_level, "payment_method": payment_method}
                r = requests.get(f"{self.base_url}/transactions", params=params, timeout=2.0)
                if r.status_code == 200:
                    return r.json()
            except Exception as e:
                print(f"API transactions error: {e}")
                
        # Fallback
        filtered = self.local_transactions
        if account_id:
            filtered = [t for t in filtered if t["sender_id"] == account_id or t["receiver_id"] == account_id]
        if search:
            s_lower = search.lower()
            filtered = [
                t for t in filtered
                if s_lower in t["transaction_id"].lower() or s_lower in t["sender_name"].lower() or s_lower in t["receiver_name"].lower()
            ]
        if risk_level and risk_level != "All":
            filtered = [t for t in filtered if t["risk_level"].lower() == risk_level.lower()]
        if payment_method and payment_method != "All":
            filtered = [t for t in filtered if t["payment_method"].lower() == payment_method.lower()]
            
        return {"total": len(filtered), "transactions": filtered}
        
    def get_alerts(self):
        if not self.local_mode:
            try:
                r = requests.get(f"{self.base_url}/alerts", timeout=2.0)
                if r.status_code == 200:
                    return r.json()
            except Exception as e:
                print(f"API alerts error: {e}")
        # Fallback
        return self.local_alerts
        
    def get_network(self, acc_id):
        if not self.local_mode:
            try:
                r = requests.get(f"{self.base_url}/network/{acc_id}", timeout=2.0)
                if r.status_code == 200:
                    return r.json()
            except Exception as e:
                print(f"API network error: {e}")
                
        # Fallback
        primary = self.local_accounts.get(acc_id, {"account_id": acc_id, "holder_name": "Unknown", "risk_score": 50, "risk_level": "Medium"})
        nodes = [{
            "id": primary["account_id"],
            "label": f"{primary['holder_name']}\n({primary['account_id']})",
            "risk_score": primary["risk_score"],
            "risk_level": primary["risk_level"],
            "is_primary": True
        }]
        
        opponents = [
            {"id": "ACC-201", "name": "External Sender A", "amt": 45000, "is_sender": True, "method": "UPI", "risk": 82},
            {"id": "ACC-305", "name": "External Sender B", "amt": 12000, "is_sender": True, "method": "Net Banking", "risk": 60},
            {"id": "ACC-901", "name": "External Receiver A", "amt": 55000, "is_sender": False, "method": "UPI", "risk": 90},
            {"id": "ACC-405", "name": "External Receiver B", "amt": 28000, "is_sender": False, "method": "UPI", "risk": 88}
        ]
        
        edges = []
        for op in opponents:
            nodes.append({
                "id": op["id"],
                "label": f"{op['name']}\n({op['id']})",
                "risk_score": op["risk"],
                "risk_level": "High" if op["risk"] >= 75 else "Medium",
                "is_primary": False
            })
            if op["is_sender"]:
                edges.append({"source": op["id"], "target": acc_id, "amount": op["amt"], "method": op["method"]})
            else:
                edges.append({"source": acc_id, "target": op["id"], "amount": op["amt"], "method": op["method"]})
                
        return {
            "nodes": nodes,
            "edges": edges,
            "stats": {
                "unique_senders": 17 if acc_id == "ACC-10293" else 3,
                "unique_receivers": 8 if acc_id == "ACC-10293" else 2,
                "total_connections": 25 if acc_id == "ACC-10293" else 5,
                "rapid_transfers": 14 if acc_id == "ACC-10293" else 2,
                "high_risk_counterparties": 6 if acc_id == "ACC-10293" else 1,
                "network_risk": 96 if acc_id == "ACC-10293" else 65
            }
        }
        
    def get_risk(self, acc_id):
        if not self.local_mode:
            try:
                r = requests.get(f"{self.base_url}/risk/{acc_id}", timeout=2.0)
                if r.status_code == 200:
                    return r.json()
            except Exception as e:
                print(f"API risk error: {e}")
                
        # Fallback
        return {
            "account_id": acc_id,
            "overall_score": 94 if acc_id == "ACC-10293" else 45,
            "risk_level": "Critical" if acc_id == "ACC-10293" else "Medium",
            "components": {
                "Behavior Risk": 92 if acc_id == "ACC-10293" else 40,
                "Transaction Risk": 89 if acc_id == "ACC-10293" else 52,
                "Network Risk": 96 if acc_id == "ACC-10293" else 35,
                "Velocity Risk": 94 if acc_id == "ACC-10293" else 48,
                "Location Risk": 78 if acc_id == "ACC-10293" else 60
            },
            "history": [
                {"month": "April", "score": 41},
                {"month": "May", "score": 48},
                {"month": "June", "score": 57},
                {"month": "July", "score": 76},
                {"month": "August", "score": 94 if acc_id == "ACC-10293" else 45}
            ]
        }
        
    def get_explanation(self, acc_id):
        if not self.local_mode:
            try:
                r = requests.get(f"{self.base_url}/explanation/{acc_id}", timeout=2.0)
                if r.status_code == 200:
                    return r.json()
            except Exception as e:
                print(f"API explanation error: {e}")
                
        # Fallback
        return {
            "account_id": acc_id,
            "classification": "SUSPICIOUS" if acc_id == "ACC-10293" else "SAFE",
            "probability": 94.2 if acc_id == "ACC-10293" else 15.0,
            "overall_score": 94 if acc_id == "ACC-10293" else 45,
            "shap_factors": [
                {"feature": "Transaction Velocity", "impact": 0.31},
                {"feature": "Unique Senders", "impact": 0.26},
                {"feature": "Rapid Fund Movement", "impact": 0.22},
                {"feature": "Network Connectivity", "impact": 0.18},
                {"feature": "Amount Deviation", "impact": 0.14},
                {"feature": "New Beneficiaries", "impact": 0.11}
            ],
            "human_explanation": "The account demonstrates a high-volume pass-through pattern. It receives funds from multiple unrelated accounts and transfers a significant portion of those funds within a short period. The account's transaction velocity and network connectivity are substantially higher than its normal behavioral profile.",
            "recommended_action": "Enhanced Due Diligence / Investigation" if acc_id == "ACC-10293" else "Monitor"
        }
        
    def get_analytics_monthly(self):
        if self.cached_analytics_monthly:
            return self.cached_analytics_monthly
        if not self.local_mode:
            try:
                r = requests.get(f"{self.base_url}/analytics/monthly", timeout=2.0)
                if r.status_code == 200:
                    return r.json()
            except Exception as e:
                print(f"API analytics error: {e}")
                
        # Fallback
        return {
            "august": {"month": "August 2026", "fraud_transactions": 14, "fraud_amount_lakhs": 8.7, "suspicious_accounts": 6},
            "july": {"month": "July 2026", "fraud_transactions": 9, "fraud_amount_lakhs": 4.2, "suspicious_accounts": 3},
            "changes": {"fraud_transactions_pct": 55.6, "fraud_amount_pct": 107.1, "suspicious_accounts_pct": 100.0},
            "history": [
                {"month": "March", "count": 2}, {"month": "April", "count": 3}, {"month": "May", "count": 5},
                {"month": "June", "count": 6}, {"month": "July", "count": 9}, {"month": "August", "count": 14}
            ]
        }
        
    def get_regional_risk(self):
        if self.cached_regional:
            return self.cached_regional
        if not self.local_mode:
            try:
                r = requests.get(f"{self.base_url}/regional-risk", timeout=2.0)
                if r.status_code == 200:
                    return r.json()
            except Exception as e:
                print(f"API regional risk error: {e}")
        # Fallback
        return [
            {"region": "Madhya Pradesh", "accounts_count": 1842, "transactions_count": 18421, "fraud_count": 42, "volume": 1240000.0, "active_alerts": 8, "risk": "HIGH"},
            {"region": "Maharashtra", "accounts_count": 2984, "transactions_count": 28401, "fraud_count": 51, "volume": 3450000.0, "active_alerts": 12, "risk": "CRITICAL"},
            {"region": "Karnataka", "accounts_count": 2105, "transactions_count": 21840, "fraud_count": 24, "volume": 2100000.0, "active_alerts": 4, "risk": "MEDIUM"},
            {"region": "Delhi", "accounts_count": 1948, "transactions_count": 19280, "fraud_count": 18, "volume": 1850000.0, "active_alerts": 2, "risk": "MEDIUM"},
            {"region": "Tamil Nadu", "accounts_count": 1542, "transactions_count": 14920, "fraud_count": 12, "volume": 1150000.0, "active_alerts": 1, "risk": "LOW"},
        ]
        
    def get_payment_methods(self):
        if self.cached_payment_methods:
            return self.cached_payment_methods
        if not self.local_mode:
            try:
                r = requests.get(f"{self.base_url}/payment-methods", timeout=2.0)
                if r.status_code == 200:
                    return r.json()
            except Exception as e:
                print(f"API payment methods error: {e}")
        # Fallback
        return {
            "distribution": {"UPI": 62, "Debit Card": 24, "Credit Card": 9, "Net Banking": 5, "PayPal": 0},
            "risk_levels": {"UPI": 84, "Debit Card": 45, "Credit Card": 30, "Net Banking": 52, "PayPal": 10}
        }
        
    def export_pdf_report(self, acc_id, output_path):
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            
            acc = self.get_account_detail(acc_id)
            explanation = self.get_explanation(acc_id)
            
            doc = SimpleDocTemplate(output_path, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
            story = []
            styles = getSampleStyleSheet()
            
            title_style = ParagraphStyle('T', fontSize=18, textColor=colors.HexColor("#0B1F33"), fontName="Helvetica-Bold", spaceAfter=15)
            section_style = ParagraphStyle('S', fontSize=12, textColor=colors.HexColor(COLOR_PRIMARY_BLUE), fontName="Helvetica-Bold", spaceBefore=10, spaceAfter=5)
            body_style = ParagraphStyle('B', fontSize=9, textColor=colors.HexColor(COLOR_TEXT_PRIMARY), fontName="Helvetica")
            bold_style = ParagraphStyle('Bld', fontSize=9, textColor=colors.HexColor(COLOR_TEXT_PRIMARY), fontName="Helvetica-Bold")
            
            story.append(Paragraph("MULEGUARD - FINANCIAL CRIME OFFLINE REPORT", title_style))
            story.append(Paragraph(f"Account ID: {acc['account_id']} | Holder: {acc['holder_name']}", section_style))
            
            table_data = [
                [Paragraph("Property", bold_style), Paragraph("Value", bold_style)],
                [Paragraph("Masked Card/Acc Number:", body_style), Paragraph(acc["account_number"], body_style)],
                [Paragraph("IFSC Code:", body_style), Paragraph(acc["ifsc_code"], body_style)],
                [Paragraph("Region / Location:", body_style), Paragraph(acc["region"], body_style)],
                [Paragraph("Account Age:", body_style), Paragraph(f"{acc['age_months']} months", body_style)],
                [Paragraph("Risk Score:", bold_style), Paragraph(f"{acc['risk_score']}/100", bold_style)],
                [Paragraph("Mule Probability:", bold_style), Paragraph(f"{explanation['probability']}%", body_style)],
                [Paragraph("Recommended Action:", bold_style), Paragraph(explanation["recommended_action"], bold_style)]
            ]
            t = Table(table_data, colWidths=[180, 300])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0B1F33")),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor(COLOR_BORDER)),
                ('PADDING', (0,0), (-1,-1), 6),
            ]))
            story.append(t)
            story.append(Spacer(1, 10))
            story.append(Paragraph("Explanation", section_style))
            story.append(Paragraph(explanation["human_explanation"], body_style))
            doc.build(story)
            return True
        except Exception as e:
            print("Offline PDF Error:", e)
            return False
            
    def update_account(self, acc_id, name, acc_number, ifsc_code, region, risk_score):
        if acc_id in self.local_accounts:
            acc = self.local_accounts[acc_id]
            acc["holder_name"] = name
            acc["account_number"] = acc_number
            acc["ifsc_code"] = ifsc_code
            parts = region.split("/")
            acc["region"] = parts[0].strip()
            if len(parts) > 1:
                acc["city"] = parts[1].strip()
            try:
                score = int(risk_score)
                acc["risk_score"] = score
                if score >= 90:
                    acc["risk_level"] = "Critical"
                elif score >= 75:
                    acc["risk_level"] = "High"
                elif score >= 50:
                    acc["risk_level"] = "Medium"
                else:
                    acc["risk_level"] = "Safe"
            except ValueError:
                pass
            return True
        return False

    def _initialize_local_mock_db(self):
        target_id = "ACC-10293"
        self.local_accounts[target_id] = {
            "account_id": target_id,
            "holder_name": "Aarav Sharma",
            "account_number": "XXXX XXXX 1029",
            "ifsc_code": "XXXX0001234",
            "region": "Madhya Pradesh",
            "city": "Indore",
            "age_months": 8,
            "credit_amount": 1840000.0,
            "debit_amount": 1790000.0,
            "risk_score": 94,
            "risk_level": "Critical",
            "status": "Under Investigation",
            "payment_methods": ["UPI", "Debit Card", "Credit Card", "Net Banking"],
            "avg_transaction": 12500.0,
            "max_transaction": 85000.0,
            "min_transaction": 150.0,
            "daily_volume": 12
        }
        
        self.local_accounts["ACC-4412"] = {
            "account_id": "ACC-4412",
            "holder_name": "Rohan Deshmukh",
            "account_number": "XXXX XXXX 4412",
            "ifsc_code": "XXXX0009876",
            "region": "Maharashtra",
            "city": "Mumbai",
            "age_months": 24,
            "credit_amount": 4500000.0,
            "debit_amount": 4200000.0,
            "risk_score": 35,
            "risk_level": "Low/Safe",
            "status": "Active",
            "payment_methods": ["UPI", "Net Banking"],
            "avg_transaction": 22000.0,
            "max_transaction": 120000.0,
            "min_transaction": 100.0,
            "daily_volume": 4
        }
        
        for i in range(10000, 10015):
            acc_id = f"ACC-{i}"
            if acc_id in self.local_accounts: continue
            risk = random.randint(10, 89)
            lvl = "High" if risk >= 75 else ("Medium" if risk >= 40 else "Low/Safe")
            self.local_accounts[acc_id] = {
                "account_id": acc_id,
                "holder_name": f"Compliance Test Account {i-9999}",
                "account_number": f"XXXX XXXX {random.randint(1000,9999)}",
                "ifsc_code": f"XXXX000{random.randint(1000,9999)}",
                "region": "Maharashtra",
                "city": "Mumbai",
                "age_months": random.randint(3, 48),
                "credit_amount": round(random.uniform(50000, 800000), 2),
                "debit_amount": round(random.uniform(50000, 800000), 2),
                "risk_score": risk,
                "risk_level": lvl,
                "status": "Active",
                "payment_methods": ["UPI", "Debit Card"],
                "avg_transaction": 4500.0,
                "max_transaction": 45000.0,
                "min_transaction": 20.0,
                "daily_volume": 3
            }
            
        self.local_alerts.append({
            "alert_id": "AL-10492",
            "account_id": target_id,
            "holder_name": "Aarav Sharma",
            "alert_type": "Rapid Fund Movement",
            "risk_score": 94,
            "risk_level": "Critical",
            "amount": 85000.0,
            "detected_time": "2 min ago",
            "status": "Open"
        })
        for i in range(1, 8):
            self.local_alerts.append({
                "alert_id": f"AL-{10492 + i}",
                "account_id": f"ACC-{10000 + i}",
                "holder_name": self.local_accounts[f"ACC-{10000+i}"]["holder_name"],
                "alert_type": random.choice(["Suspicious Counterparty", "Unusual Velocity", "Circular Transaction"]),
                "risk_score": self.local_accounts[f"ACC-{10000+i}"]["risk_score"],
                "risk_level": self.local_accounts[f"ACC-{10000+i}"]["risk_level"],
                "amount": round(random.uniform(10000, 150000), 2),
                "detected_time": f"{i * 5} min ago",
                "status": "Open"
            })
            
        self.local_transactions.append({
            "transaction_id": "TX-82921",
            "timestamp": "22 Aug 2026, 10:42",
            "sender_id": "ACC-4412",
            "sender_name": "Rohan Deshmukh",
            "receiver_id": target_id,
            "receiver_name": "Aarav Sharma",
            "amount": 85000.0,
            "transaction_type": "Credit",
            "payment_method": "UPI",
            "region": "Madhya Pradesh",
            "city": "Indore",
            "risk_score": 94,
            "risk_level": "Critical",
            "status": "FLAGGED",
            "reasons": ["Unusual amount", "New beneficiary", "High transaction velocity", "Suspicious network relationship"]
        })
        
        for i in range(30):
            self.local_transactions.append({
                "transaction_id": f"TX-82922-{i}",
                "timestamp": (datetime.now() - timedelta(hours=i)).strftime("%d %b %Y, %H:%M"),
                "sender_id": "ACC-10001",
                "sender_name": "Test Sender",
                "receiver_id": target_id if i % 4 == 0 else "ACC-10002",
                "receiver_name": "Aarav Sharma" if i % 4 == 0 else "Test Receiver",
                "amount": round(random.uniform(1000, 95000), 2),
                "transaction_type": "Credit" if i % 2 == 0 else "Debit",
                "payment_method": "UPI",
                "region": "Madhya Pradesh",
                "city": "Indore",
                "risk_score": random.randint(20, 85),
                "risk_level": "Medium",
                "status": "APPROVED",
                "reasons": []
            })


# ---------------------------------------------------------
# MATPLOTLIB WIDGETS
# ---------------------------------------------------------
class MChartCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi, facecolor='#FFFFFF')
        self.ax = self.fig.add_subplot(111)
        self.fig.subplots_adjust(left=0.08, right=0.95, top=0.9, bottom=0.15)
        super().__init__(self.fig)
        self.setParent(parent)
        
    def clear(self):
        self.ax.clear()
        
    def format_ax(self, title):
        self.ax.set_title(title, fontsize=10, color=COLOR_TEXT_PRIMARY, weight='bold', pad=8)
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.ax.spines['left'].set_color(COLOR_BORDER)
        self.ax.spines['bottom'].set_color(COLOR_BORDER)
        self.ax.tick_params(colors=COLOR_TEXT_SECONDARY, labelsize=8)
        self.ax.grid(True, linestyle='--', alpha=0.5, color=COLOR_BORDER)


# ---------------------------------------------------------
# HELPER CUSTOM ROW BADGES FOR BEHANCE TABLES
# ---------------------------------------------------------
class TableBadgeLabel(QLabel):
    def __init__(self, text, style_type="safe", parent=None):
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignCenter)
        
        # Colors based on type
        if style_type == "critical":
            bg_col = "#FEE4E2"
            text_col = COLOR_RISK_CRITICAL
        elif style_type == "high":
            bg_col = "#FEF0C7"
            text_col = COLOR_RISK_HIGH
        elif style_type == "medium":
            bg_col = "#FFFAEB"
            text_col = COLOR_RISK_MEDIUM
        else: # safe / executed
            bg_col = "#D1FADF"
            text_col = COLOR_RISK_LOW
            
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {bg_col};
                color: {text_col};
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 11px;
                font-weight: bold;
            }}
        """)


# ---------------------------------------------------------
# CUSTOM DIALOGS
# ---------------------------------------------------------
class LogoutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Confirm Logout")
        self.setFixedSize(320, 160)
        self.setStyleSheet(GLOBAL_STYLE)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        lbl = QLabel("Are you sure you want to logout?")
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet(f"font-size: 15px; color: {COLOR_TEXT_PRIMARY}; font-weight: bold;")
        layout.addWidget(lbl)
        
        layout.addSpacing(15)
        
        btn_layout = QHBoxLayout()
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setProperty("class", "SecondaryButton")
        self.btn_cancel.clicked.connect(self.reject)
        
        self.btn_logout = QPushButton("Logout")
        self.btn_logout.setProperty("class", "PrimaryButton")
        self.btn_logout.setStyleSheet(f"background-color: {COLOR_RISK_CRITICAL}; color: #FFFFFF;")
        self.btn_logout.clicked.connect(self.accept)
        
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_logout)
        layout.addLayout(btn_layout)


# ---------------------------------------------------------
# LOGIN VIEW (SECTIONS 4 & 5)
# ---------------------------------------------------------
# ---------------------------------------------------------
# SHIELD LOGO CUSTOM WIDGET (MATCHING UPLOADED PHOTO)
# ---------------------------------------------------------
class ShieldLogoWidget(QWidget):
    def __init__(self, size=40, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w = self.width()
        h = self.height()
        
        # Shield Path Outline
        path = QPainterPath()
        path.moveTo(w/2, 2)
        path.lineTo(w - 2, h/4)
        path.lineTo(w - 2, h*2/3)
        path.quadTo(w - 2, h - 2, w/2, h - 2)
        path.quadTo(2, h - 2, 2, h*2/3)
        path.lineTo(2, h/4)
        path.closeSubpath()
        
        # Fill Split Background
        painter.save()
        painter.setClipPath(path)
        painter.fillRect(0, 0, w/2, h, QColor("#1E3A8A")) # Deep Blue
        painter.fillRect(w/2, 0, w/2, h, QColor("#D92D20")) # Red
        painter.restore()
        
        # White Frame Outline
        painter.setPen(QPen(QColor("#FFFFFF"), 2.2))
        painter.drawPath(path)
        
        # Draw padlock shape
        painter.setPen(QPen(QColor("#FFFFFF"), 1.5))
        painter.setBrush(QBrush(QColor("#FFFFFF")))
        
        # Lock Shackle arch
        painter.drawArc(w*5/16, h*1/4, w*6/16, h*5/16, 0, 180*16)
        # Lock body square
        painter.drawRoundedRect(w*5/16 + 2, h*1/2 - 2, w*6/16 - 4, h*1/4, 2, 2)


# ---------------------------------------------------------
# COMPOSITE QLINEEDIT WITH BUILT-IN ICON AND ACTION BUTTON
# ---------------------------------------------------------
class IconLineEdit(QLineEdit):
    def __init__(self, icon_char, is_password=False, parent=None):
        super().__init__(parent)
        self.icon_char = icon_char
        self.is_password = is_password
        
        # Space on left for icon, right for password eye
        left_margin = 35
        right_margin = 35 if self.is_password else 10
        self.setTextMargins(left_margin, 0, right_margin, 0)
        
        # Icon label inside QLineEdit
        self.lbl_icon = QLabel(icon_char, self)
        self.lbl_icon.setStyleSheet("color: #667085; font-size: 14px; background: transparent; border: none; padding: 0px;")
        self.lbl_icon.setAlignment(Qt.AlignCenter)
        self.lbl_icon.setFixedSize(30, 30)
        
        if self.is_password:
            self.setEchoMode(QLineEdit.Password)
            self.btn_eye = QPushButton("👁️", self)
            self.btn_eye.setCursor(Qt.PointingHandCursor)
            self.btn_eye.setStyleSheet("QPushButton { border: none; background: transparent; color: #667085; font-size: 13px; padding: 0px; }")
            self.btn_eye.setFixedSize(30, 30)
            self.btn_eye.clicked.connect(self.toggle_eye)
        else:
            self.btn_eye = None
            
        # Clean styling
        self.setStyleSheet("""
            QLineEdit {
                border: 1px solid #D0D5DD;
                border-radius: 6px;
                padding: 8px 10px;
                font-size: 13px;
                color: #172B4D;
                background-color: #FFFFFF;
            }
            QLineEdit:focus {
                border: 1px solid #155EEF;
            }
        """)
        
    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Vertically center the icon label
        self.lbl_icon.move(8, (self.height() - self.lbl_icon.height()) // 2)
        if self.btn_eye:
            # Vertically center the eye button
            self.btn_eye.move(self.width() - self.btn_eye.width() - 8, (self.height() - self.btn_eye.height()) // 2)
            
    def toggle_eye(self):
        if self.echoMode() == QLineEdit.Password:
            self.setEchoMode(QLineEdit.Normal)
            self.btn_eye.setText("🔒")
        else:
            self.setEchoMode(QLineEdit.Password)
            self.btn_eye.setText("👁️")


# ---------------------------------------------------------
# NEW SPLIT SCREEN LOGIN VIEW
# ---------------------------------------------------------
class LoginView(QWidget):
    login_success = Signal(str)
    
    def __init__(self, api_client: ApiClient, parent=None):
        super().__init__(parent)
        self.api = api_client
        self.init_ui()
        
    def init_ui(self):
        # Master Horizontal Split
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # ---------------------------------------------------------
        # LEFT COLUMN (DEEP NAVY BRAND PANEL)
        # ---------------------------------------------------------
        left_banner = QFrame()
        left_banner.setStyleSheet("QFrame { background-color: #030F26; border: none; }")
        left_layout = QVBoxLayout(left_banner)
        left_layout.setContentsMargins(60, 60, 60, 60)
        left_layout.setSpacing(0)
        
        # App Title Row
        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)
        title_row.setSpacing(12)
        title_row.setAlignment(Qt.AlignVCenter)
        
        self.logo_label = QLabel()
        logo_path = os.path.join(os.path.dirname(__file__), "logo.png")
        pixmap = QPixmap(logo_path)
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(QSize(44, 44), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.logo_label.setPixmap(scaled_pixmap)
        else:
            self.logo_label.setText("🛡️")
            self.logo_label.setStyleSheet("font-size: 24px; color: white;")
        title_row.addWidget(self.logo_label)
        
        logo_text_v = QVBoxLayout()
        logo_text_v.setContentsMargins(0, 0, 0, 0)
        logo_text_v.setSpacing(0)
        
        lbl_appname = QLabel("MuleGuard")
        lbl_appname.setStyleSheet("color: #FFFFFF; font-size: 22px; font-weight: bold; font-family: 'Inter'; padding: 0px;")
        lbl_appdesc = QLabel("Financial Crime Intelligence")
        lbl_appdesc.setStyleSheet("color: #98A2B3; font-size: 11px; padding: 0px;")
        
        logo_text_v.addWidget(lbl_appname)
        logo_text_v.addWidget(lbl_appdesc)
        title_row.addLayout(logo_text_v)
        title_row.addStretch()
        left_layout.addLayout(title_row)
        
        left_layout.addSpacing(50)
        
        # Headline
        lbl_headline = QLabel("Detect. Analyze.<br><font color='#155EEF'>Prevent</font> Financial Crime.")
        lbl_headline.setStyleSheet("color: #FFFFFF; font-size: 32px; font-weight: bold; line-height: 42px; font-family: 'Inter'; padding: 0px;")
        left_layout.addWidget(lbl_headline)
        
        left_layout.addSpacing(12)
        
        # Separator Line
        sep_line = QFrame()
        sep_line.setFixedWidth(50)
        sep_line.setFixedHeight(3)
        sep_line.setStyleSheet("background-color: #155EEF; border: none;")
        left_layout.addWidget(sep_line)
        
        left_layout.addSpacing(16)
        
        # Headline Subtext
        lbl_subtext = QLabel(
            "MuleGuard helps financial institutions identify mule accounts, detect suspicious "
            "transactions, and prevent fraudulent activities with advanced network intelligence."
        )
        lbl_subtext.setWordWrap(True)
        lbl_subtext.setStyleSheet("color: #98A2B3; font-size: 13px; line-height: 20px; padding: 0px;")
        left_layout.addWidget(lbl_subtext)
        
        left_layout.addSpacing(35)
        
        # Grid of capabilities
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(24)
        
        caps = [
            ("🛡️", "AI-Powered Detection", "Advanced ML models", 0, 0),
            ("🌐", "Network Intelligence", "Transaction relationship mapping", 0, 1),
            ("📈", "Real-time Monitoring", "Live alerts and tracking", 1, 0),
            ("📄", "Comprehensive Reports", "Detailed investigation reports", 1, 1)
        ]
        
        for icon, title, desc, r, c in caps:
            cap_box = QFrame()
            cap_box.setStyleSheet("background: transparent; border: none;")
            h_cap = QHBoxLayout(cap_box)
            h_cap.setContentsMargins(0, 0, 0, 0)
            h_cap.setSpacing(12)
            h_cap.setAlignment(Qt.AlignVCenter)
            
            # Circle Icon Frame
            circle = QLabel(icon)
            circle.setAlignment(Qt.AlignCenter)
            circle.setFixedSize(36, 36)
            circle.setStyleSheet("background-color: #0B1F33; border: 1px solid #1C3550; border-radius: 18px; font-size: 16px;")
            h_cap.addWidget(circle)
            
            text_v = QVBoxLayout()
            text_v.setContentsMargins(0, 0, 0, 0)
            text_v.setSpacing(2)
            
            lbl_cap_t = QLabel(title)
            lbl_cap_t.setStyleSheet("color: #FFFFFF; font-weight: bold; font-size: 12px; padding: 0px;")
            lbl_cap_d = QLabel(desc)
            lbl_cap_d.setStyleSheet("color: #98A2B3; font-size: 11px; padding: 0px;")
            
            text_v.addWidget(lbl_cap_t)
            text_v.addWidget(lbl_cap_d)
            h_cap.addLayout(text_v)
            
            grid.addWidget(cap_box, r, c)
            
        left_layout.addLayout(grid)
        left_layout.addStretch()
        
        # ---------------------------------------------------------
        # RIGHT COLUMN (SOFT GRAY PANEL WITH CARD)
        # ---------------------------------------------------------
        right_panel = QWidget()
        right_panel.setStyleSheet("background-color: #F8F9FC; border: none;")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(40, 40, 40, 40)
        right_layout.setSpacing(0)
        
        # System Status Row
        status_row = QHBoxLayout()
        status_row.setContentsMargins(0, 0, 0, 0)
        status_row.addStretch()
        lbl_status = QLabel("● System Status: <font color='#039855'>Online</font>")
        lbl_status.setStyleSheet("color: #667085; font-size: 12px; font-weight: bold;")
        status_row.addWidget(lbl_status)
        right_layout.addLayout(status_row)
        
        right_layout.addStretch()
        
        # Form Card Frame
        form_card = QFrame()
        form_card.setObjectName("FormCard")
        form_card.setFixedSize(400, 490)
        form_card.setStyleSheet("QFrame#FormCard { background-color: #FFFFFF; border: 1px solid #E4E7EC; border-radius: 8px; }")
        
        f_layout = QVBoxLayout(form_card)
        f_layout.setContentsMargins(35, 30, 35, 30)
        f_layout.setSpacing(0)
        
        # Header Badge Logo & Text
        header_v = QVBoxLayout()
        header_v.setContentsMargins(0, 0, 0, 0)
        header_v.setAlignment(Qt.AlignCenter)
        header_v.setSpacing(8)
        
        form_logo = QLabel()
        logo_path = os.path.join(os.path.dirname(__file__), "logo.png")
        pixmap = QPixmap(logo_path)
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(QSize(36, 36), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            form_logo.setPixmap(scaled_pixmap)
        else:
            form_logo.setText("🛡️")
            form_logo.setStyleSheet("font-size: 24px;")
        header_v.addWidget(form_logo, 0, Qt.AlignCenter)
        
        lbl_welcome = QLabel("Welcome Back")
        lbl_welcome.setStyleSheet("font-size: 20px; font-weight: bold; color: #172B4D;")
        lbl_welcome.setAlignment(Qt.AlignCenter)
        header_v.addWidget(lbl_welcome)
        
        lbl_signin_sub = QLabel("Sign in to your Analyst Portal")
        lbl_signin_sub.setStyleSheet("font-size: 12px; color: #667085;")
        lbl_signin_sub.setAlignment(Qt.AlignCenter)
        header_v.addWidget(lbl_signin_sub)
        
        f_layout.addLayout(header_v)
        f_layout.addSpacing(20)
        
        # Username Input Section
        emp_v = QVBoxLayout()
        emp_v.setContentsMargins(0, 0, 0, 0)
        emp_v.setSpacing(6)
        
        lbl_emp_title = QLabel("Employee ID / Email")
        lbl_emp_title.setStyleSheet("font-weight: bold; font-size: 11px; color: #172B4D;")
        
        self.txt_emp = IconLineEdit("✉️")
        self.txt_emp.setText("afsarazam404@gmail.com")
        
        emp_v.addWidget(lbl_emp_title)
        emp_v.addWidget(self.txt_emp)
        f_layout.addLayout(emp_v)
        
        f_layout.addSpacing(14)
        
        # Password Input Section
        pwd_v = QVBoxLayout()
        pwd_v.setContentsMargins(0, 0, 0, 0)
        pwd_v.setSpacing(6)
        
        lbl_pwd_title = QLabel("Password")
        lbl_pwd_title.setStyleSheet("font-weight: bold; font-size: 11px; color: #172B4D;")
        
        self.txt_pwd = IconLineEdit("🔒", is_password=True)
        self.txt_pwd.setText("mockaccesskey")
        
        pwd_v.addWidget(lbl_pwd_title)
        pwd_v.addWidget(self.txt_pwd)
        f_layout.addLayout(pwd_v)
        
        f_layout.addSpacing(12)
        
        # Checkboxes
        opt_layout = QHBoxLayout()
        opt_layout.setContentsMargins(0, 0, 0, 0)
        
        self.chk_show = QCheckBox("Show Password")
        self.chk_show.setStyleSheet("color: #667085; font-size: 11px;")
        self.chk_show.stateChanged.connect(self.toggle_password_visible)
        
        self.chk_rem = QCheckBox("Remember this device")
        self.chk_rem.setChecked(True)
        self.chk_rem.setStyleSheet("color: #667085; font-size: 11px;")
        
        opt_layout.addWidget(self.chk_show)
        opt_layout.addStretch()
        opt_layout.addWidget(self.chk_rem)
        f_layout.addLayout(opt_layout)
        
        # Error text
        self.lbl_error = QLabel("")
        self.lbl_error.setStyleSheet("color: #D92D20; font-size: 11px; font-weight: bold; min-height: 16px;")
        self.lbl_error.setAlignment(Qt.AlignCenter)
        f_layout.addWidget(self.lbl_error)
        
        f_layout.addSpacing(4)
        
        # Sign In Button (Strict Vibrant Blue Style)
        self.btn_signin = QPushButton("🔒   Sign In")
        self.btn_signin.setCursor(Qt.PointingHandCursor)
        self.btn_signin.setStyleSheet("""
            QPushButton {
                background-color: #155EEF;
                color: #FFFFFF;
                font-weight: bold;
                border: none;
                border-radius: 6px;
                height: 40px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #104EC6;
            }
            QPushButton:pressed {
                background-color: #0640B0;
            }
        """)
        self.btn_signin.clicked.connect(self.handle_signin)
        f_layout.addWidget(self.btn_signin)
        
        f_layout.addSpacing(12)
        
        # Separator line "or"
        sep_layout = QHBoxLayout()
        sep_layout.setContentsMargins(0, 0, 0, 0)
        l_line = QFrame()
        l_line.setFrameShape(QFrame.HLine)
        l_line.setStyleSheet("color: #E4E7EC; border: none; background-color: #E4E7EC; height: 1px;")
        r_line = QFrame()
        r_line.setFrameShape(QFrame.HLine)
        r_line.setStyleSheet("color: #E4E7EC; border: none; background-color: #E4E7EC; height: 1px;")
        lbl_or = QLabel("or")
        lbl_or.setStyleSheet("color: #98A2B3; font-size: 11px;")
        sep_layout.addWidget(l_line, 1)
        sep_layout.addWidget(lbl_or, 0, Qt.AlignCenter)
        sep_layout.addWidget(r_line, 1)
        f_layout.addLayout(sep_layout)
        
        f_layout.addSpacing(12)
        
        # SSO button
        self.btn_sso = QPushButton("🛡️  Sign in with SSO")
        self.btn_sso.setCursor(Qt.PointingHandCursor)
        self.btn_sso.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                color: #172B4D;
                border: 1px solid #D0D5DD;
                border-radius: 6px;
                height: 38px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F8F9FC;
            }
        """)
        f_layout.addWidget(self.btn_sso)
        
        f_layout.addSpacing(12)
        
        # Forgot password Link
        self.btn_forgot = QPushButton("Forgot Password?")
        self.btn_forgot.setStyleSheet("color: #155EEF; font-size: 11px; font-weight: bold; background: transparent; border: none;")
        self.btn_forgot.clicked.connect(self.handle_forgot)
        f_layout.addWidget(self.btn_forgot)
        
        right_layout.addWidget(form_card, 0, Qt.AlignCenter)
        right_layout.addStretch()
        
        # Footer
        footer_v = QVBoxLayout()
        footer_v.setSpacing(2)
        lbl_f1 = QLabel("Secure Analyst Portal | MuleGuard v1.0.0")
        lbl_f1.setStyleSheet("color: #667085; font-size: 11px;")
        lbl_f1.setAlignment(Qt.AlignCenter)
        lbl_f2 = QLabel("© 2026 MuleGuard. All rights reserved.")
        lbl_f2.setStyleSheet("color: #98A2B3; font-size: 11px;")
        lbl_f2.setAlignment(Qt.AlignCenter)
        footer_v.addWidget(lbl_f1)
        footer_v.addWidget(lbl_f2)
        right_layout.addLayout(footer_v)
        
        # Assemble Split Screen
        main_layout.addWidget(left_banner, 4)
        main_layout.addWidget(right_panel, 5)
        
    def toggle_password_visible(self, state):
        if state == 2:
            self.txt_pwd.setEchoMode(QLineEdit.Normal)
        else:
            self.txt_pwd.setEchoMode(QLineEdit.Password)
            
    def handle_signin(self):
        emp_id = self.txt_emp.text().strip()
        pwd = self.txt_pwd.text().strip()
        
        if not emp_id or not pwd:
            self.lbl_error.setText("Please fill out all fields.")
            return
            
        res = self.api.login(emp_id, pwd)
        if res:
            self.lbl_error.setText("")
            self.login_success.emit(emp_id)
        else:
            self.lbl_error.setText("Invalid credentials. Try admin/admin")
            
    def handle_forgot(self):
        d = QDialog(self)
        d.setWindowTitle("Reset Password")
        d.setFixedSize(360, 240)
        d.setStyleSheet(GLOBAL_STYLE)
        
        layout = QVBoxLayout(d)
        layout.setContentsMargins(20, 20, 20, 20)
        
        lbl_title = QLabel("Password Recovery Flow")
        lbl_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(lbl_title)
        
        txt_email = QLineEdit()
        txt_email.setPlaceholderText("Enter Email / Employee ID")
        layout.addWidget(txt_email)
        
        lbl_status = QLabel("")
        lbl_status.setStyleSheet("color: #155EEF; font-size: 12px;")
        layout.addWidget(lbl_status)
        
        btn = QPushButton("Send Reset Link")
        btn.setProperty("class", "PrimaryButton")
        
        def run_flow():
            if not txt_email.text().strip():
                lbl_status.setText("Email is required.")
                return
            lbl_status.setText("Verification recovery link dispatched.")
            QTimer.singleShot(2000, lambda: d.accept())
            
        btn.clicked.connect(run_flow)
        layout.addWidget(btn)
        d.exec()




# ---------------------------------------------------------
# MAIN APPLICATION WINDOW SHELL (BEHANCE BREADCRUMB STYLE)
# ---------------------------------------------------------
class MainWindow(QMainWindow):
    def __init__(self, api_client: ApiClient):
        super().__init__()
        self.api = api_client
        self.current_user = "Analyst"
        
        self.setWindowTitle("MuleGuard")
        logo_path = os.path.join(os.path.dirname(__file__), "logo.png")
        self.setWindowIcon(QIcon(logo_path))
        self.setMinimumSize(1280, 720)
        self.resize(1440, 900)
        
        self.central_widget = QStackedWidget()
        self.setCentralWidget(self.central_widget)
        
        # Login page is index 0
        self.login_view = LoginView(self.api)
        self.login_view.login_success.connect(self.on_login_success)
        self.central_widget.addWidget(self.login_view)
        
        # Shell view container is index 1
        self.shell_view = QWidget()
        self.shell_layout = QHBoxLayout(self.shell_view)
        self.shell_layout.setContentsMargins(0, 0, 0, 0)
        self.shell_layout.setSpacing(0)
        
        self.create_sidebar()
        
        self.main_body = QWidget()
        self.main_body_layout = QVBoxLayout(self.main_body)
        self.main_body_layout.setContentsMargins(0, 0, 0, 0)
        self.main_body_layout.setSpacing(0)
        
        self.create_header()
        
        # Content stack
        self.content_stack = QStackedWidget()
        self.main_body_layout.addWidget(self.content_stack)
        
        self.create_footer()
        
        self.shell_layout.addWidget(self.sidebar_frame)
        self.shell_layout.addWidget(self.main_body)
        self.central_widget.addWidget(self.shell_view)
        
        self.build_content_pages()
        
    def create_sidebar(self):
        self.sidebar_frame = QFrame()
        self.sidebar_frame.setObjectName("SidebarFrame")
        self.sidebar_frame.setFixedWidth(240)
        
        layout = QVBoxLayout(self.sidebar_frame)
        layout.setContentsMargins(0, 0, 0, 10)
        layout.setSpacing(0)
        
        # Logo block
        header = QWidget()
        header.setObjectName("SidebarHeader")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(20, 25, 20, 25)
        h_layout.setSpacing(12)
        h_layout.setAlignment(Qt.AlignVCenter)
        
        logo_label = QLabel()
        logo_path = os.path.join(os.path.dirname(__file__), "logo.png")
        pixmap = QPixmap(logo_path)
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(QSize(36, 36), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(scaled_pixmap)
        else:
            logo_label.setText("🛡️")
            logo_label.setStyleSheet("font-size: 24px;")
            
        title = QLabel("MuleGuard")
        title.setObjectName("SidebarTitle")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #172B4D; padding: 0px;")
        
        h_layout.addWidget(logo_label)
        h_layout.addWidget(title)
        h_layout.addStretch()
        layout.addWidget(header)
        
        self.nav_buttons = {}
        
        # Navigation items grouped
        groups = [
            ("OVERVIEW", [("Dashboard", 0)], False),
            ("RISK MONITORING", [("Active Alerts", 1), ("Live Transactions", 2)], True),
            ("INVESTIGATION", [("Accounts", 3), ("Transactions", 4), ("Network Analysis", 5)], True),
            ("ANALYTICS", [("Fraud Analytics", 6), ("Regional Risk", 7), ("Payment Methods", 8)], True)
        ]
        
        self.group_widgets = {}
        self.group_headers = {}
        
        for group_title, items, is_collapsible in groups:
            if is_collapsible:
                header_btn = QPushButton(f"▶  {group_title}")
                header_btn.setCursor(Qt.PointingHandCursor)
                header_btn.setProperty("class", "SidebarSectionHeader")
                header_btn.clicked.connect(lambda checked, gt=group_title: self.toggle_sidebar_group(gt))
                layout.addWidget(header_btn)
                self.group_headers[group_title] = header_btn
                self.group_widgets[group_title] = []
            else:
                lbl = QLabel(group_title)
                lbl.setObjectName("SidebarSectionLabel")
                layout.addWidget(lbl)
                
            for item_name, idx in items:
                btn = QPushButton(f"  {item_name}")
                btn.setCheckable(True)
                btn.setProperty("class", "SidebarButton")
                btn.clicked.connect(lambda checked, i=idx: self.switch_content_page(i))
                layout.addWidget(btn)
                self.nav_buttons[idx] = btn
                
                if is_collapsible:
                    self.group_widgets[group_title].append(btn)
                    btn.setVisible(False)
                
        layout.addStretch()
        
        btn_settings = QPushButton("  Settings")
        btn_settings.setCheckable(True)
        btn_settings.setProperty("class", "SidebarButton")
        btn_settings.clicked.connect(lambda: self.switch_content_page(9))
        layout.addWidget(btn_settings)
        self.nav_buttons[9] = btn_settings
        
        btn_logout = QPushButton("  Logout")
        btn_logout.setProperty("class", "SidebarButton")
        btn_logout.setStyleSheet(f"color: {COLOR_RISK_CRITICAL};")
        btn_logout.clicked.connect(self.handle_logout)
        layout.addWidget(btn_logout)
        
    def toggle_sidebar_group(self, group_title):
        header_btn = self.group_headers.get(group_title)
        sub_buttons = self.group_widgets.get(group_title, [])
        if not header_btn or not sub_buttons:
            return
            
        is_visible = sub_buttons[0].isVisible()
        new_visible = not is_visible
        
        for btn in sub_buttons:
            btn.setVisible(new_visible)
            
        caret = "▼" if new_visible else "▶"
        header_btn.setText(f"{caret}  {group_title}")
        
    def expand_sidebar_group(self, group_title):
        header_btn = self.group_headers.get(group_title)
        sub_buttons = self.group_widgets.get(group_title, [])
        if header_btn and sub_buttons:
            for btn in sub_buttons:
                btn.setVisible(True)
            header_btn.setText(f"▼  {group_title}")
        
    def create_header(self):
        self.header_frame = QFrame()
        self.header_frame.setObjectName("HeaderFrame")
        layout = QHBoxLayout(self.header_frame)
        layout.setContentsMargins(30, 15, 30, 15)
        layout.setSpacing(0)
        
        # Circular Back Button (hidden by default on Dashboard)
        self.btn_back = QPushButton("←")
        self.btn_back.setCursor(Qt.PointingHandCursor)
        self.btn_back.setFixedSize(32, 32)
        self.btn_back.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                border: 1px solid #E4E7EC;
                border-radius: 16px;
                color: #172B4D;
                font-size: 16px;
                font-weight: bold;
                margin-right: 15px;
            }
            QPushButton:hover {
                background-color: #F8F9FC;
                border: 1px solid #B2DDFF;
                color: #155EEF;
            }
        """)
        self.btn_back.clicked.connect(self.go_back_to_dashboard)
        layout.addWidget(self.btn_back)
        
        # Category label + Title (Behance breadcrumb style)
        left_layout = QVBoxLayout()
        self.lbl_breadcrumbs = QLabel("OVERVIEW")
        self.lbl_breadcrumbs.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 11px; font-weight: bold; text-transform: uppercase;")
        
        self.lbl_title = QLabel("Dashboard")
        self.lbl_title.setObjectName("HeaderTitle")
        
        left_layout.addWidget(self.lbl_breadcrumbs)
        left_layout.addWidget(self.lbl_title)
        
        # Shared Header Logo - Shows logo in every tab next to breadcrumbs
        self.header_logo = QLabel()
        logo_path = os.path.join(os.path.dirname(__file__), "logo.png")
        pixmap = QPixmap(logo_path)
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(QSize(28, 28), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.header_logo.setPixmap(scaled_pixmap)
        else:
            self.header_logo.setText("🛡️")
            self.header_logo.setStyleSheet("font-size: 18px;")
            
        title_h = QHBoxLayout()
        title_h.setSpacing(10)
        title_h.addWidget(self.header_logo)
        title_h.addLayout(left_layout)
        
        layout.addLayout(title_h)
        
        layout.addStretch()
        
        # Search Box
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Search Account / Transaction...")
        self.txt_search.setFixedWidth(280)
        self.txt_search.returnPressed.connect(self.handle_header_search)
        layout.addWidget(self.txt_search)
        
        # User metadata & Icons
        icon_layout = QHBoxLayout()
        icon_layout.setSpacing(15)
        
        # Bell notification icon mockup
        lbl_bell = QLabel("🔔")
        lbl_bell.setStyleSheet("font-size: 16px; color: #667085; background-color: #F8F9FC; border-radius: 15px; padding: 4px;")
        
        # Settings cog mockup
        lbl_cog = QLabel("⚙️")
        lbl_cog.setStyleSheet("font-size: 16px; color: #667085; background-color: #F8F9FC; border-radius: 15px; padding: 4px;")
        
        # Avatar mockup
        lbl_avatar = QLabel("AM")
        lbl_avatar.setAlignment(Qt.AlignCenter)
        lbl_avatar.setFixedSize(30, 30)
        lbl_avatar.setStyleSheet("background-color: #155EEF; color: #FFFFFF; font-weight: bold; border-radius: 15px; font-size: 11px;")
        
        icon_layout.addWidget(lbl_bell)
        icon_layout.addWidget(lbl_cog)
        icon_layout.addWidget(lbl_avatar)
        layout.addLayout(icon_layout)
        
    def create_footer(self):
        self.footer_frame = QFrame()
        self.footer_frame.setObjectName("FooterFrame")
        self.footer_frame.setFixedHeight(35)
        
        layout = QHBoxLayout(self.footer_frame)
        layout.setContentsMargins(30, 0, 30, 0)
        
        self.status_labels = {}
        states = ["AI Engine", "API Link", "Database", "Model Engine"]
        
        for state in states:
            lbl = QLabel(f"● {state}: Loaded")
            lbl.setStyleSheet(f"color: {COLOR_RISK_LOW}; font-size: 11px; font-weight: bold; margin-right: 20px;")
            if state == "API Link" or state == "Database":
                lbl.setText(f"● {state}: Sandbox (Offline)")
                lbl.setStyleSheet(f"color: {COLOR_RISK_HIGH}; font-size: 11px; font-weight: bold; margin-right: 20px;")
            layout.addWidget(lbl)
            self.status_labels[state] = lbl
            
        layout.addStretch()
        lbl_ver = QLabel("MuleGuard Desktop Terminal v1.0.0 (Secure Mode)")
        lbl_ver.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11px;")
        layout.addWidget(lbl_ver)
        
    def build_content_pages(self):
        self.page_dashboard = DashboardView(self.api, self)
        self.content_stack.addWidget(self.page_dashboard)
        
        self.page_alerts = ActiveAlertsView(self.api, self)
        self.content_stack.addWidget(self.page_alerts)
        
        self.page_livetx = LiveTransactionsView(self.api, self)
        self.content_stack.addWidget(self.page_livetx)
        
        self.page_accounts = AccountsView(self.api, self)
        self.content_stack.addWidget(self.page_accounts)
        
        self.page_transactions = TransactionsView(self.api, self)
        self.content_stack.addWidget(self.page_transactions)
        
        self.page_network = NetworkAnalysisView(self.api, self)
        self.content_stack.addWidget(self.page_network)
        
        self.page_fraud_anal = FraudAnalyticsView(self.api, self)
        self.content_stack.addWidget(self.page_fraud_anal)
        
        self.page_regional = RegionalRiskView(self.api, self)
        self.content_stack.addWidget(self.page_regional)
        
        self.page_methods = PaymentMethodsView(self.api, self)
        self.content_stack.addWidget(self.page_methods)
        
        self.page_settings = SettingsView(self.api, self)
        self.content_stack.addWidget(self.page_settings)
        
        self.switch_content_page(0)
        
    def switch_content_page(self, index):
        self.content_stack.setCurrentIndex(index)
        
        for idx, btn in self.nav_buttons.items():
            btn.setChecked(idx == index)
            
        categories = {
            0: "OVERVIEW", 1: "RISK MONITORING", 2: "RISK MONITORING",
            3: "INVESTIGATION", 4: "INVESTIGATION", 5: "INVESTIGATION",
            6: "ANALYTICS", 7: "ANALYTICS", 8: "ANALYTICS",
            9: "SYSTEM SETTINGS"
        }
        self.lbl_breadcrumbs.setText(categories.get(index, "MULEGUARD"))
        
        # Expand sidebar group if active page is switched programmatically
        active_category = categories.get(index)
        if active_category and hasattr(self, "expand_sidebar_group"):
            self.expand_sidebar_group(active_category)
        
        titles = {
            0: "Dashboard",
            1: "Active Alerts Queue",
            2: "Live Transactions Monitor",
            3: "Accounts Directory",
            4: "Transactions Ledger",
            5: "Account Investigation Console",
            6: "Fraud Analytics",
            7: "Regional Risk Intelligence",
            8: "Payment Methods Analysis",
            9: "Settings"
        }
        self.lbl_title.setText(titles.get(index, "Dashboard"))
        
        # Toggle back button visibility (hide on Dashboard, show elsewhere)
        if hasattr(self, "btn_back"):
            self.btn_back.setVisible(index != 0)
            
        # Check API health to recover from local fallback mode if backend starts late
        if self.api.local_mode:
            self.api.check_health()
            
        current_widget = self.content_stack.currentWidget()
        if hasattr(current_widget, "load_data"):
            current_widget.load_data()
            
    def go_back_to_dashboard(self):
        self.switch_content_page(0)
            
    def investigate_account(self, account_id):
        self.page_network.set_account(account_id)
        self.switch_content_page(5)
        
    def handle_header_search(self):
        query = self.txt_search.text().strip()
        if not query: return
        
        # Check details directly
        acc = self.api.get_account_detail(query)
        if acc:
            self.investigate_account(query)
            self.txt_search.clear()
        else:
            res = self.api.get_accounts(search=query)
            if res["accounts"]:
                self.investigate_account(res["accounts"][0]["account_id"])
                self.txt_search.clear()
            else:
                QMessageBox.warning(self, "No Matches", f"No accounts found matching ID '{query}'")
                
    def on_login_success(self, emp_id):
        self.current_user = emp_id
        self.central_widget.setCurrentIndex(1)
        self.switch_content_page(0)
        
        # Start background WebSocket thread
        if not hasattr(self, "ws_thread") or not self.ws_thread.isRunning():
            self.ws_thread = AnalyticsWebSocketThread()
            self.ws_thread.data_received.connect(self.on_websocket_data_received)
            self.ws_thread.start()
        
    def handle_logout(self):
        dialog = LogoutDialog(self)
        if dialog.exec():
            self.login_view.txt_emp.clear()
            self.login_view.txt_pwd.clear()
            self.login_view.lbl_error.setText("")
            self.central_widget.setCurrentIndex(0)
            if hasattr(self, "ws_thread"):
                self.ws_thread.stop()
                self.ws_thread.wait()
                
    @Slot(dict)
    def on_websocket_data_received(self, data):
        self.api.cached_dashboard = data
        self.api.cached_regional = data.get("regional_risk")
        self.api.cached_payment_methods = data.get("payment_methods")
        
        # Always update dashboard in the background so it is up-to-date
        try:
            self.page_dashboard.update_with_stream_data(data)
        except Exception as e:
            print(f"Error updating dashboard stream data: {e}")
            
        current_widget = self.content_stack.currentWidget()
        if current_widget == self.page_regional:
            try:
                self.page_regional.load_data()
            except Exception as e:
                print(f"Error updating regional risk data: {e}")
        elif current_widget == self.page_methods:
            try:
                p_methods = data.get("payment_methods", {})
                dist = p_methods.get("distribution", {})
                risks = p_methods.get("risk_levels", {})
                
                total_txs = data.get("total_accounts", 100) * 15
                self.page_methods.sim_upi_txs = int(total_txs * dist.get("UPI", 62) / 100)
                self.page_methods.sim_debit_txs = int(total_txs * dist.get("Debit Card", 24) / 100)
                self.page_methods.sim_credit_txs = int(total_txs * dist.get("Credit Card", 9) / 100)
                self.page_methods.sim_net_txs = int(total_txs * dist.get("Net Banking", 5) / 100)
                self.page_methods.sim_paypal_txs = int(total_txs * dist.get("PayPal", 0) / 100)
                
                self.page_methods.sim_upi_risk = risks.get("UPI", 28)
                self.page_methods.sim_debit_risk = risks.get("Debit Card", 24)
                self.page_methods.sim_credit_risk = risks.get("Credit Card", 35)
                self.page_methods.sim_net_risk = risks.get("Net Banking", 45)
                self.page_methods.sim_paypal_risk = risks.get("PayPal", 10)
                
                self.page_methods.load_data()
            except Exception as e:
                print(f"Error updating payment methods data: {e}")

    def closeEvent(self, event):
        if hasattr(self, "ws_thread"):
            self.ws_thread.stop()
            self.ws_thread.wait()
        event.accept()


# ---------------------------------------------------------
# VIEW 0: MAIN DASHBOARD VIEW
# ---------------------------------------------------------
class DashboardView(QWidget):
    def __init__(self, api: ApiClient, main_window: MainWindow):
        super().__init__()
        self.api = api
        self.main_window = main_window
        self.num_total_accounts = 12450
        self.num_total_tx_amount = 84.6*10000000
        self.num_total_credit = 42.8*10000000
        self.num_total_debit = 41.8*10000000
        self.num_fraud_transactions = 137
        self.num_active_alerts = 24
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(20)
        
        # KPI grid matching section 8
        self.kpi_grid = QGridLayout()
        self.kpi_grid.setSpacing(20)
        
        kpis = [
            ("Total Accounts", "12,450", 0, 0),
            ("Total Transaction Amount", "₹84.6 Cr", 0, 1),
            ("Total Credit", "₹42.8 Cr", 0, 2),
            ("Total Debit", "₹41.8 Cr", 1, 0),
            ("Fraud Transactions", "137", 1, 1),
            ("Active Alerts", "24", 1, 2)
        ]
        
        self.card_widgets = {}
        for title, val, r, c in kpis:
            card = QFrame()
            card.setProperty("class", "Card")
            c_layout = QVBoxLayout(card)
            c_layout.setContentsMargins(20, 20, 20, 20)
            
            lbl_t = QLabel(title)
            lbl_t.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 12px; font-weight: bold; text-transform: uppercase;")
            
            lbl_v = QLabel(val)
            lbl_v.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 24px; font-weight: bold; margin-top: 5px;")
            
            c_layout.addWidget(lbl_t)
            c_layout.addWidget(lbl_v)
            self.kpi_grid.addWidget(card, r, c)
            self.card_widgets[title] = lbl_v
            
        layout.addLayout(self.kpi_grid)
        
        # Splitter matching layout rules
        splitter = QSplitter(Qt.Vertical)
        splitter.setStyleSheet("QSplitter::handle { background-color: #E4E7EC; height: 1px; }")
        
        # Daily Transaction Trend Card
        chart_card = QFrame()
        chart_card.setProperty("class", "Card")
        chart_layout = QVBoxLayout(chart_card)
        chart_layout.setContentsMargins(20, 20, 20, 20)
        
        ctrls = QHBoxLayout()
        lbl_c_title = QLabel("Transaction Activity Analysis")
        lbl_c_title.setStyleSheet("font-size: 14px; font-weight: bold;")
        ctrls.addWidget(lbl_c_title)
        ctrls.addStretch()
        
        self.chart_filter = "30 Days"
        for t in ["24 Hours", "7 Days", "30 Days", "6 Months"]:
            btn = QPushButton(t)
            btn.setProperty("class", "SecondaryButton")
            btn.setFixedHeight(24)
            btn.setStyleSheet("font-size: 11px; padding: 2px 10px;")
            btn.clicked.connect(lambda checked, time=t: self.update_chart_filter(time))
            ctrls.addWidget(btn)
            
        chart_layout.addLayout(ctrls)
        self.canvas = MChartCanvas(self, width=8, height=3)
        chart_layout.addWidget(self.canvas)
        splitter.addWidget(chart_card)
        
        # Bottom side panels
        bottom_widget = QWidget()
        bottom_layout = QHBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(20)
        
        # Active Alert Table Summary
        alerts_card = QFrame()
        alerts_card.setProperty("class", "Card")
        alerts_v = QVBoxLayout(alerts_card)
        alerts_v.setContentsMargins(20, 20, 20, 20)
        
        lbl_al_t = QLabel("🚨 ACTIVE ALERTS OVERVIEW")
        lbl_al_t.setStyleSheet("font-size: 13px; font-weight: bold; color: #172B4D;")
        alerts_v.addWidget(lbl_al_t)
        
        self.tbl_alerts = QTableWidget()
        self.tbl_alerts.setColumnCount(6)
        self.tbl_alerts.setHorizontalHeaderLabels(["ID", "Account", "Type", "Risk", "Amount", "Action"])
        self.tbl_alerts.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_alerts.verticalHeader().setVisible(False)
        alerts_v.addWidget(self.tbl_alerts)
        bottom_layout.addWidget(alerts_card, 1)
        
        # High Risk Suspicious Accounts table
        accounts_card = QFrame()
        accounts_card.setProperty("class", "Card")
        accs_v = QVBoxLayout(accounts_card)
        accs_v.setContentsMargins(20, 20, 20, 20)
        
        lbl_ac_t = QLabel("👤 FLAG REGISTRY (SUSPICIOUS ACCOUNTS)")
        lbl_ac_t.setStyleSheet("font-size: 13px; font-weight: bold; color: #172B4D;")
        accs_v.addWidget(lbl_ac_t)
        
        self.tbl_accounts = QTableWidget()
        self.tbl_accounts.setColumnCount(5)
        self.tbl_accounts.setHorizontalHeaderLabels(["ID", "Holder", "Risk Score", "Region", "Status"])
        self.tbl_accounts.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_accounts.verticalHeader().setVisible(False)
        self.tbl_accounts.cellDoubleClicked.connect(self.on_account_double_click)
        accs_v.addWidget(self.tbl_accounts)
        bottom_layout.addWidget(accounts_card, 1)
        
        splitter.addWidget(bottom_widget)
        layout.addWidget(splitter)
        
    def load_data(self):
        data = self.api.get_dashboard()
        
        self.num_total_accounts = data.get('total_accounts', 12450)
        self.num_total_tx_amount = data.get('total_tx_amount', 84.6*10000000)
        self.num_total_credit = data.get('total_credit', 42.8*10000000)
        self.num_total_debit = data.get('total_debit', 41.8*10000000)
        self.num_fraud_transactions = data.get('fraud_transactions', 137)
        self.num_active_alerts = data.get('active_alerts', 24)
        
        self.card_widgets["Total Accounts"].setText(f"{self.num_total_accounts:,}")
        self.card_widgets["Total Transaction Amount"].setText(format_money(self.num_total_tx_amount))
        self.card_widgets["Total Credit"].setText(format_money(self.num_total_credit))
        self.card_widgets["Total Debit"].setText(format_money(self.num_total_debit))
        self.card_widgets["Fraud Transactions"].setText(str(self.num_fraud_transactions))
        self.card_widgets["Active Alerts"].setText(str(self.num_active_alerts))
        
        self.render_activity_chart(data["chart_data"])
        
        # Fill alerts
        alerts = data.get("recent_alerts", [])
        self.tbl_alerts.setRowCount(len(alerts))
        for row, al in enumerate(alerts):
            self.tbl_alerts.setItem(row, 0, QTableWidgetItem(al["alert_id"]))
            self.tbl_alerts.setItem(row, 1, QTableWidgetItem(al["account_id"]))
            self.tbl_alerts.setItem(row, 2, QTableWidgetItem(al["alert_type"]))
            
            # Badge cell for Risk
            badge = TableBadgeLabel(f"{al['risk_score']} {al['risk_level']}", al["risk_level"].lower())
            self.tbl_alerts.setCellWidget(row, 3, badge)
            
            self.tbl_alerts.setItem(row, 4, QTableWidgetItem(f"₹{al['amount']:,}"))
            
            btn = QPushButton("Investigate")
            btn.setProperty("class", "PrimaryButton")
            btn.setStyleSheet("padding: 2px 6px; font-size: 11px;")
            btn.clicked.connect(lambda checked, acc_id=al["account_id"]: self.main_window.investigate_account(acc_id))
            self.tbl_alerts.setCellWidget(row, 5, btn)
            
        # Fill accounts
        accs = data.get("suspicious_accounts", [])
        self.tbl_accounts.setRowCount(len(accs))
        for row, acc in enumerate(accs):
            self.tbl_accounts.setItem(row, 0, QTableWidgetItem(acc["account_id"]))
            self.tbl_accounts.setItem(row, 1, QTableWidgetItem(acc["holder_name"]))
            
            badge = TableBadgeLabel(str(acc["risk_score"]), "critical" if acc["risk_score"]>=90 else "high")
            self.tbl_accounts.setCellWidget(row, 2, badge)
            
            self.tbl_accounts.setItem(row, 3, QTableWidgetItem(acc["region"]))
            self.tbl_accounts.setItem(row, 4, QTableWidgetItem(acc["status"]))
            
    def update_with_stream_data(self, data):
        self.num_total_accounts = data.get('total_accounts', 12450)
        self.num_total_tx_amount = data.get('total_tx_amount', 84.6*10000000)
        self.num_total_credit = data.get('total_credit', 42.8*10000000)
        self.num_total_debit = data.get('total_debit', 41.8*10000000)
        self.num_fraud_transactions = data.get('fraud_transactions', 137)
        self.num_active_alerts = data.get('active_alerts', 24)
        
        self.card_widgets["Total Accounts"].setText(f"{self.num_total_accounts:,}")
        self.card_widgets["Total Transaction Amount"].setText(format_money(self.num_total_tx_amount))
        self.card_widgets["Total Credit"].setText(format_money(self.num_total_credit))
        self.card_widgets["Total Debit"].setText(format_money(self.num_total_debit))
        self.card_widgets["Fraud Transactions"].setText(str(self.num_fraud_transactions))
        self.card_widgets["Active Alerts"].setText(str(self.num_active_alerts))
        
        self.render_activity_chart(data["chart_data"])
        
        # Fill alerts
        alerts = data.get("recent_alerts", [])
        self.tbl_alerts.setRowCount(len(alerts))
        for row, al in enumerate(alerts):
            self.tbl_alerts.setItem(row, 0, QTableWidgetItem(al["alert_id"]))
            self.tbl_alerts.setItem(row, 1, QTableWidgetItem(al["account_id"]))
            self.tbl_alerts.setItem(row, 2, QTableWidgetItem(al["alert_type"]))
            badge = TableBadgeLabel(f"{al['risk_score']} {al['risk_level']}", al["risk_level"].lower())
            self.tbl_alerts.setCellWidget(row, 3, badge)
            self.tbl_alerts.setItem(row, 4, QTableWidgetItem(f"₹{al['amount']:,}"))
            
            btn = QPushButton("Investigate")
            btn.setProperty("class", "PrimaryButton")
            btn.setStyleSheet("padding: 2px 6px; font-size: 11px;")
            btn.clicked.connect(lambda checked, acc_id=al["account_id"]: self.main_window.investigate_account(acc_id))
            self.tbl_alerts.setCellWidget(row, 5, btn)
            
        # Fill accounts
        accs = data.get("suspicious_accounts", [])
        self.tbl_accounts.setRowCount(len(accs))
        for row, acc in enumerate(accs):
            self.tbl_accounts.setItem(row, 0, QTableWidgetItem(acc["account_id"]))
            self.tbl_accounts.setItem(row, 1, QTableWidgetItem(acc["holder_name"]))
            badge = TableBadgeLabel(str(acc["risk_score"]), "critical" if acc["risk_score"]>=90 else "high")
            self.tbl_accounts.setCellWidget(row, 2, badge)
            self.tbl_accounts.setItem(row, 3, QTableWidgetItem(acc["region"]))
            self.tbl_accounts.setItem(row, 4, QTableWidgetItem(acc["status"]))
            
    def add_live_transaction(self, tx):
        amt = tx["amount"]
        score = tx["risk_score"]
        lvl = tx["risk_level"]
        acc_id = tx["receiver_id"]
        
        self.num_total_tx_amount += amt
        self.num_total_credit += amt
        self.num_total_debit += amt
        
        if score >= 75:
            self.num_fraud_transactions += 1
            self.num_active_alerts += 1
            
            # Add alert to recent alerts table
            alert_id = f"AL-{random.randint(20000, 29999)}"
            self.tbl_alerts.insertRow(0)
            self.tbl_alerts.setItem(0, 0, QTableWidgetItem(alert_id))
            self.tbl_alerts.setItem(0, 1, QTableWidgetItem(acc_id))
            self.tbl_alerts.setItem(0, 2, QTableWidgetItem("Suspicious Activity"))
            
            badge = TableBadgeLabel(f"{score} {lvl}", lvl.lower())
            self.tbl_alerts.setCellWidget(0, 3, badge)
            self.tbl_alerts.setItem(0, 4, QTableWidgetItem(f"₹{int(amt):,}"))
            
            btn = QPushButton("Investigate")
            btn.setProperty("class", "PrimaryButton")
            btn.setStyleSheet("padding: 2px 6px; font-size: 11px;")
            btn.clicked.connect(lambda checked, aid=acc_id: self.main_window.investigate_account(aid))
            self.tbl_alerts.setCellWidget(0, 5, btn)
            
            if self.tbl_alerts.rowCount() > 5:
                self.tbl_alerts.removeRow(self.tbl_alerts.rowCount() - 1)
                
        # Update labels
        self.card_widgets["Total Transaction Amount"].setText(format_money(self.num_total_tx_amount))
        self.card_widgets["Total Credit"].setText(format_money(self.num_total_credit))
        self.card_widgets["Total Debit"].setText(format_money(self.num_total_debit))
        self.card_widgets["Fraud Transactions"].setText(str(self.num_fraud_transactions))
        self.card_widgets["Active Alerts"].setText(str(self.num_active_alerts))
            
    def update_chart_filter(self, filter_name):
        self.chart_filter = filter_name
        self.load_data()
        
    def render_activity_chart(self, chart_data):
        self.canvas.clear()
        
        # Remove any extra axes (like twinx) from the figure to prevent overlapping text on redraw
        for extra_ax in list(self.canvas.fig.axes):
            if extra_ax is not self.canvas.ax:
                self.canvas.fig.delaxes(extra_ax)
                
        # Adjust margins to leave space for right-hand Y labels
        self.canvas.fig.subplots_adjust(left=0.08, right=0.90, top=0.88, bottom=0.15)
        
        labels = chart_data["labels"]
        total = chart_data["total"]
        credit = chart_data["credit"]
        debit = chart_data["debit"]
        fraud = chart_data["fraud"]
        
        factor = 1.0
        if self.chart_filter == "24 Hours": factor = 0.05
        elif self.chart_filter == "7 Days": factor = 0.25
        elif self.chart_filter == "6 Months": factor = 1.2
        
        total = [t * factor for t in total]
        credit = [c * factor for c in credit]
        debit = [d * factor for d in debit]
        
        ax = self.canvas.ax
        ax.plot(labels, total, label='Total Volume', color=COLOR_PRIMARY_BLUE, linewidth=2, marker='o')
        ax.plot(labels, credit, label='Credit', color=COLOR_RISK_LOW, linewidth=1.5, linestyle='--')
        ax.plot(labels, debit, label='Debit', color=COLOR_TEXT_SECONDARY, linewidth=1.5, linestyle=':')
        
        # Twin Y for fraud
        ax2 = ax.twinx()
        ax2.bar(labels, fraud, label='Triggered Fraud Cases', color=COLOR_RISK_CRITICAL, alpha=0.2, width=0.4)
        ax2.spines['top'].set_visible(False)
        ax2.spines['left'].set_visible(False)
        ax2.spines['right'].set_color(COLOR_BORDER)
        ax2.tick_params(colors=COLOR_RISK_CRITICAL, labelsize=8)
        
        self.canvas.format_ax(f"Transaction Activity Volume Trends ({self.chart_filter})")
        
        lines, labels_leg = ax.get_legend_handles_labels()
        lines2, labels_leg2 = ax2.get_legend_handles_labels()
        ax.legend(lines + lines2, labels_leg + labels_leg2, loc='upper left', frameon=True, facecolor='#FFFFFF', edgecolor=COLOR_BORDER, fontsize=8)
        
        self.canvas.draw()
        
    def on_account_double_click(self, row, col):
        acc_id = self.tbl_accounts.item(row, 0).text()
        self.main_window.investigate_account(acc_id)


# ---------------------------------------------------------
# VIEW 1: ACTIVE ALERTS
# ---------------------------------------------------------
class ActiveAlertsView(QWidget):
    def __init__(self, api: ApiClient, main_window: MainWindow):
        super().__init__()
        self.api = api
        self.main_window = main_window
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(20)
        
        f_card = QFrame()
        f_card.setProperty("class", "Card")
        f_layout = QHBoxLayout(f_card)
        f_layout.setContentsMargins(15, 10, 15, 10)
        
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Filter alerts by ID, Account ID, Holder Name...")
        self.txt_search.textChanged.connect(self.load_data)
        f_layout.addWidget(self.txt_search)
        f_layout.addStretch()
        layout.addWidget(f_card)
        
        self.tbl = QTableWidget()
        self.tbl.setColumnCount(9)
        self.tbl.setHorizontalHeaderLabels(["Alert ID", "Account ID", "Holder", "Alert Type", "Risk Score", "Amount", "Detected Time", "Status", "Action"])
        self.tbl.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl.verticalHeader().setVisible(False)
        layout.addWidget(self.tbl)
        
    def load_data(self):
        alerts = self.api.get_alerts()
        query = self.txt_search.text().strip().lower()
        
        if query:
            alerts = [
                a for a in alerts
                if query in a["alert_id"].lower()
                or query in a["account_id"].lower()
                or query in a["holder_name"].lower()
            ]
            
        self.tbl.setRowCount(len(alerts))
        for row, al in enumerate(alerts):
            self.tbl.setItem(row, 0, QTableWidgetItem(al["alert_id"]))
            self.tbl.setItem(row, 1, QTableWidgetItem(al["account_id"]))
            self.tbl.setItem(row, 2, QTableWidgetItem(al["holder_name"]))
            self.tbl.setItem(row, 3, QTableWidgetItem(al["alert_type"]))
            
            badge = TableBadgeLabel(f"{al['risk_score']} {al['risk_level']}", al["risk_level"].lower())
            self.tbl.setCellWidget(row, 4, badge)
            
            self.tbl.setItem(row, 5, QTableWidgetItem(f"₹{al['amount']:,}"))
            self.tbl.setItem(row, 6, QTableWidgetItem(al["detected_time"]))
            self.tbl.setItem(row, 7, QTableWidgetItem(al["status"]))
            
            btn = QPushButton("Investigate")
            btn.setProperty("class", "PrimaryButton")
            btn.setStyleSheet("padding: 2px 6px; font-size: 11px;")
            btn.clicked.connect(lambda checked, acc_id=al["account_id"]: self.main_window.investigate_account(acc_id))
            self.tbl.setCellWidget(row, 8, btn)


# ---------------------------------------------------------
# VIEW 2: LIVE TRANSACTIONS
# ---------------------------------------------------------
class LiveTransactionsView(QWidget):
    def __init__(self, api: ApiClient, main_window: MainWindow):
        super().__init__()
        self.api = api
        self.main_window = main_window
        self.is_monitoring = True
        
        self.init_ui()
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.generate_live_tx)
        self.timer.start(3000)
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(20)
        
        ctrl_card = QFrame()
        ctrl_card.setProperty("class", "Card")
        ctrl_layout = QHBoxLayout(ctrl_card)
        ctrl_layout.setContentsMargins(15, 12, 15, 12)
        
        self.lbl_mon = QLabel("LIVE TRANSACTION MONITOR ● Active")
        self.lbl_mon.setStyleSheet("font-size: 14px; font-weight: bold; color: #039855;")
        ctrl_layout.addWidget(self.lbl_mon)
        ctrl_layout.addStretch()
        
        self.btn_toggle = QPushButton("Pause Monitoring")
        self.btn_toggle.setProperty("class", "SecondaryButton")
        self.btn_toggle.clicked.connect(self.toggle_monitoring)
        ctrl_layout.addWidget(self.btn_toggle)
        
        layout.addWidget(ctrl_card)
        
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("background-color: #0B1F33; border: 1px solid #1C3550; border-radius: 6px;")
        
        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background-color: #0B1F33;")
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setAlignment(Qt.AlignTop)
        self.scroll_layout.setSpacing(10)
        
        self.scroll.setWidget(self.scroll_content)
        layout.addWidget(self.scroll)
        
    def toggle_monitoring(self):
        self.is_monitoring = not self.is_monitoring
        if self.is_monitoring:
            self.lbl_mon.setText("LIVE TRANSACTION MONITOR ● Active")
            self.lbl_mon.setStyleSheet("font-size: 14px; font-weight: bold; color: #039855;")
            self.btn_toggle.setText("Pause Monitoring")
        else:
            self.lbl_mon.setText("LIVE TRANSACTION MONITOR ● Paused")
            self.lbl_mon.setStyleSheet("font-size: 14px; font-weight: bold; color: #D92D20;")
            self.btn_toggle.setText("Resume Monitoring")
            
    def load_data(self):
        pass
        
    def generate_live_tx(self):
        if not self.is_monitoring: return
        
        accounts = []
        try:
            res = self.api.get_accounts(limit=100)
            accounts = res.get("accounts", [])
        except Exception:
            pass
            
        if not accounts:
            accounts = [{"account_id": "ACC-10293", "holder_name": "Aarav Sharma", "risk_score": 94, "risk_level": "Critical"}]
            
        acc = random.choice(accounts)
        acc_id = acc["account_id"]
        
        counterparty = random.choice([a for a in accounts if a["account_id"] != acc_id]) if len(accounts) > 1 else acc
        counterparty_id = counterparty["account_id"]
        
        tx_id = f"TX-{random.randint(90000, 99999)}"
        time_str = datetime.now().strftime("%H:%M:%S")
        
        score = max(acc.get("risk_score", 0), counterparty.get("risk_score", 0))
        score = max(5, min(99, score + random.randint(-10, 5)))
        
        if score >= 75:
            lvl = "CRITICAL" if score >= 90 else "HIGH"
            color = COLOR_RISK_CRITICAL if score >= 90 else COLOR_RISK_HIGH
            amount = f"₹{random.randint(50, 150)*1000:,}"
            method = "UPI"
        else:
            lvl = "LOW" if score < 40 else "MEDIUM"
            color = COLOR_RISK_MEDIUM if score >= 40 else COLOR_RISK_LOW
            amount = f"₹{random.randint(100, 12000):,}"
            method = random.choice(["UPI", "Debit Card", "Net Banking", "Credit Card"])
            
        tx_card = QFrame()
        tx_card.setStyleSheet("QFrame { background-color: #0E2844; border: 1px solid #1A365D; border-radius: 4px; padding: 10px; }")
        t_layout = QHBoxLayout(tx_card)
        
        lbl_time = QLabel(time_str)
        lbl_time.setStyleSheet("color: #98A2B3; font-weight: bold; font-family: monospace;")
        
        lbl_id = QLabel(tx_id)
        lbl_id.setStyleSheet("color: #FFFFFF; font-family: monospace;")
        
        lbl_route = QLabel(f"{counterparty_id} → {acc_id}")
        lbl_route.setStyleSheet("color: #A3B9CC; font-weight: bold;")
        
        lbl_amt = QLabel(amount)
        lbl_amt.setStyleSheet("color: #FFFFFF; font-weight: bold;")
        
        lbl_method = QLabel(method)
        lbl_method.setStyleSheet("color: #98A2B3; font-size: 11px;")
        
        lbl_risk = QLabel(f"Risk Score: {score} [{lvl}]")
        lbl_risk.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 12px;")
        
        btn = QPushButton("Investigate")
        btn.setStyleSheet("QPushButton { background-color: #1C3550; color: #FFFFFF; border: none; border-radius: 3px; padding: 4px 10px; font-size: 11px; } QPushButton:hover { background-color: #155EEF; }")
        btn.clicked.connect(lambda checked, aid=acc_id: self.main_window.investigate_account(aid))
        
        t_layout.addWidget(lbl_time)
        t_layout.addWidget(lbl_id)
        t_layout.addWidget(lbl_route)
        t_layout.addWidget(lbl_amt)
        t_layout.addWidget(lbl_method)
        t_layout.addWidget(lbl_risk)
        t_layout.addWidget(btn)
        
        self.scroll_layout.insertWidget(0, tx_card)
        
        if self.scroll_layout.count() > 30:
            item = self.scroll_layout.takeAt(self.scroll_layout.count() - 1)
            if item.widget():
                item.widget().deleteLater()
                
        # Clean currency formatted amount string (e.g. ₹68,000 -> 68000.0)
        try:
            amount_numeric = float(amount.replace("₹", "").replace(",", ""))
        except ValueError:
            amount_numeric = 0.0
            
        tx_data = {
            "sender_id": counterparty_id,
            "receiver_id": acc_id,
            "amount": amount_numeric,
            "risk_score": score,
            "risk_level": lvl,
            "method": method,
            "time": time_str
        }
        
        # Increment metrics on the main dashboard tab in real-time
        self.main_window.page_dashboard.add_live_transaction(tx_data)


# ---------------------------------------------------------
# VIEW 3: ACCOUNTS LIST GRID
# ---------------------------------------------------------
class AccountsView(QWidget):
    def __init__(self, api: ApiClient, main_window: MainWindow):
        super().__init__()
        self.api = api
        self.main_window = main_window
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(20)
        
        f_card = QFrame()
        f_card.setProperty("class", "Card")
        f_layout = QHBoxLayout(f_card)
        f_layout.setContentsMargins(15, 10, 15, 10)
        
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Search accounts by Holder Name, ID, Card Number...")
        self.txt_search.textChanged.connect(self.load_data)
        f_layout.addWidget(self.txt_search)
        f_layout.addStretch()
        layout.addWidget(f_card)
        
        self.tbl = QTableWidget()
        self.tbl.setColumnCount(10)
        self.tbl.setHorizontalHeaderLabels([
            "Account ID", "Account Holder", "Masked Account", "IFSC Code",
            "Region", "Age", "Credit Balance", "Debit Balance", "Risk Score", "Status"
        ])
        self.tbl.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl.verticalHeader().setVisible(False)
        self.tbl.cellDoubleClicked.connect(self.on_row_double_click)
        layout.addWidget(self.tbl)
        
    def load_data(self):
        query = self.txt_search.text().strip()
        res = self.api.get_accounts(search=query)
        accs = res.get("accounts", [])
        
        self.tbl.setRowCount(len(accs))
        for row, acc in enumerate(accs):
            self.tbl.setItem(row, 0, QTableWidgetItem(acc["account_id"]))
            self.tbl.setItem(row, 1, QTableWidgetItem(acc["holder_name"]))
            self.tbl.setItem(row, 2, QTableWidgetItem(acc["account_number"]))
            self.tbl.setItem(row, 3, QTableWidgetItem(acc["ifsc_code"]))
            self.tbl.setItem(row, 4, QTableWidgetItem(acc["region"]))
            self.tbl.setItem(row, 5, QTableWidgetItem(f"{acc['age_months']} mos"))
            self.tbl.setItem(row, 6, QTableWidgetItem(f"₹{acc['credit_amount']:,}"))
            self.tbl.setItem(row, 7, QTableWidgetItem(f"₹{acc['debit_amount']:,}"))
            
            badge = TableBadgeLabel(str(acc["risk_score"]), acc["risk_level"].lower())
            self.tbl.setCellWidget(row, 8, badge)
            
            self.tbl.setItem(row, 9, QTableWidgetItem(acc["status"]))
            
    def on_row_double_click(self, row, col):
        acc_id = self.tbl.item(row, 0).text()
        self.main_window.investigate_account(acc_id)


# ---------------------------------------------------------
# VIEW 4: TRANSACTIONS LIST GRID
# ---------------------------------------------------------
class TransactionsView(QWidget):
    def __init__(self, api: ApiClient, main_window: MainWindow):
        super().__init__()
        self.api = api
        self.main_window = main_window
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(20)
        
        f_card = QFrame()
        f_card.setProperty("class", "Card")
        f_layout = QHBoxLayout(f_card)
        f_layout.setContentsMargins(15, 10, 15, 10)
        
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Filter transactions by ID, Sender, Receiver Name...")
        self.txt_search.textChanged.connect(self.load_data)
        f_layout.addWidget(self.txt_search)
        f_layout.addStretch()
        layout.addWidget(f_card)
        
        self.tbl = QTableWidget()
        self.tbl.setColumnCount(10)
        self.tbl.setHorizontalHeaderLabels([
            "Transaction ID", "Timestamp", "Sender Party", "Receiver Party",
            "Amount", "Type", "Method", "Region", "Risk Score", "Status"
        ])
        self.tbl.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl.verticalHeader().setVisible(False)
        self.tbl.cellDoubleClicked.connect(self.on_row_double_click)
        layout.addWidget(self.tbl)
        
    def load_data(self):
        query = self.txt_search.text().strip()
        res = self.api.get_transactions(search=query)
        txs = res.get("transactions", [])
        
        self.tbl.setRowCount(len(txs))
        for row, tx in enumerate(txs):
            self.tbl.setItem(row, 0, QTableWidgetItem(tx["transaction_id"]))
            self.tbl.setItem(row, 1, QTableWidgetItem(tx["timestamp"]))
            self.tbl.setItem(row, 2, QTableWidgetItem(f"{tx['sender_name']} ({tx['sender_id']})"))
            self.tbl.setItem(row, 3, QTableWidgetItem(f"{tx['receiver_name']} ({tx['receiver_id']})"))
            
            # Amount column formatted with color
            amt_item = QTableWidgetItem(f"₹{tx['amount']:,}")
            if tx["transaction_type"] == "Credit":
                amt_item.setForeground(QColor(COLOR_RISK_LOW))
            else:
                amt_item.setForeground(QColor(COLOR_RISK_CRITICAL))
            self.tbl.setItem(row, 4, amt_item)
            
            self.tbl.setItem(row, 5, QTableWidgetItem(tx["transaction_type"]))
            self.tbl.setItem(row, 6, QTableWidgetItem(tx["payment_method"]))
            self.tbl.setItem(row, 7, QTableWidgetItem(tx["region"]))
            
            badge = TableBadgeLabel(str(tx["risk_score"]), "critical" if tx["risk_score"]>=80 else "medium")
            self.tbl.setCellWidget(row, 8, badge)
            
            self.tbl.setItem(row, 9, QTableWidgetItem(tx["status"]))
            
    def on_row_double_click(self, row, col):
        # Investigate receiver
        acc_id = self.tbl.item(row, 3).text().split("(")[-1].replace(")", "").strip()
        self.main_window.investigate_account(acc_id)


# ---------------------------------------------------------
# VIEW 5: ACCOUNT INVESTIGATION CONSOLE (BEHANCE TWO COLUMN VIEW)
# ---------------------------------------------------------
class NetworkAnalysisView(QWidget):
    def __init__(self, api: ApiClient, main_window: MainWindow):
        super().__init__()
        self.api = api
        self.main_window = main_window
        self.account_id = "ACC-10293" # Aarav Sharma
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(20)
        
        # Sub title summary row
        self.header_card = QFrame()
        self.header_card.setStyleSheet("background-color: #FFFFFF; border: 1px solid #E4E7EC; border-radius: 6px; padding: 12px;")
        h_layout = QHBoxLayout(self.header_card)
        
        self.lbl_acc_title = QLabel("ACCOUNT DETAILS: ACC-10293 | Aarav Sharma")
        self.lbl_acc_title.setStyleSheet("font-size: 15px; font-weight: bold; color: #172B4D;")
        h_layout.addWidget(self.lbl_acc_title)
        
        h_layout.addStretch()
        
        self.lbl_status = QLabel("● UNDER INVESTIGATION")
        self.lbl_status.setStyleSheet("color: #D92D20; font-weight: bold; font-size: 12px;")
        h_layout.addWidget(self.lbl_status)
        
        layout.addWidget(self.header_card)
        
        # Main Splitter matching Behance layout
        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet("QSplitter::handle { background-color: #E4E7EC; width: 1px; }")
        
        # LEFT COLUMN - ALL ACCOUNTS VERTICAL LIST (Image 3 Left Panel)
        left_panel = QFrame()
        left_panel.setFixedWidth(300)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 10, 0)
        left_layout.setSpacing(10)
        
        lbl_col_title = QLabel("All Accounts List")
        lbl_col_title.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {COLOR_TEXT_SECONDARY}; text-transform: uppercase;")
        left_layout.addWidget(lbl_col_title)
        
        self.scroll_acc = QScrollArea()
        self.scroll_acc.setWidgetResizable(True)
        self.scroll_acc.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_acc.setStyleSheet("background-color: transparent; border: none;")
        
        self.scroll_acc_content = QWidget()
        self.scroll_acc_layout = QVBoxLayout(self.scroll_acc_content)
        self.scroll_acc_layout.setAlignment(Qt.AlignTop)
        self.scroll_acc_layout.setSpacing(8)
        self.scroll_acc_layout.setContentsMargins(0, 0, 0, 0)
        
        self.scroll_acc.setWidget(self.scroll_acc_content)
        left_layout.addWidget(self.scroll_acc)
        
        splitter.addWidget(left_panel)
        
        # RIGHT PANEL - TABS (General Info, Transactions, Network Map, SHAP, PDF Reports)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(10, 0, 0, 0)
        right_layout.setSpacing(0)
        
        self.tabs = QTabWidget()
        logo_path = os.path.join(os.path.dirname(__file__), "logo.png")
        tab_icon = QIcon(logo_path)
        
        # Sub-Tab 1: General Info Card Mockups
        self.tab_info = QWidget()
        self.init_info_tab()
        self.tabs.addTab(self.tab_info, tab_icon, "General Info")
        
        # Sub-Tab 2: Transactions list
        self.tab_tx = QWidget()
        self.init_tx_tab()
        self.tabs.addTab(self.tab_tx, tab_icon, "Transactions")
        
        # Sub-Tab 3: Network Graph Map
        self.tab_net = QWidget()
        self.init_net_tab()
        self.tabs.addTab(self.tab_net, tab_icon, "Network Topology")
        
        # Sub-Tab 4: AI Explanations & SHAP Waterfall
        self.tab_ai = QWidget()
        self.init_ai_tab()
        self.tabs.addTab(self.tab_ai, tab_icon, "Explainable AI (SHAP)")
        
        # Sub-Tab 5: PDF reports Suite
        self.tab_rep = QWidget()
        self.init_rep_tab()
        self.tabs.addTab(self.tab_rep, tab_icon, "Investigation Reports")
        
        right_layout.addWidget(self.tabs)
        splitter.addWidget(right_panel)
        
        layout.addWidget(splitter)
        
    def init_info_tab(self):
        layout = QVBoxLayout(self.tab_info)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Balances Row
        bal_row = QHBoxLayout()
        bal_row.setSpacing(20)
        
        self.card_credit = QFrame()
        self.card_credit.setProperty("class", "Card")
        cc_layout = QVBoxLayout(self.card_credit)
        self.lbl_credit_t = QLabel("TOTAL CREDIT BALANCE")
        self.lbl_credit_t.setStyleSheet("font-size: 11px; font-weight: bold; color: #667085;")
        self.lbl_credit_v = QLabel("₹18.4L Lakhs")
        self.lbl_credit_v.setStyleSheet("font-size: 24px; font-weight: bold; color: #039855;")
        cc_layout.addWidget(self.lbl_credit_t)
        cc_layout.addWidget(self.lbl_credit_v)
        
        self.card_debit = QFrame()
        self.card_debit.setProperty("class", "Card")
        cd_layout = QVBoxLayout(self.card_debit)
        self.lbl_debit_t = QLabel("TOTAL DEBIT FLOWS")
        self.lbl_debit_t.setStyleSheet("font-size: 11px; font-weight: bold; color: #667085;")
        self.lbl_debit_v = QLabel("₹17.9L Lakhs")
        self.lbl_debit_v.setStyleSheet("font-size: 24px; font-weight: bold; color: #D92D20;")
        cd_layout.addWidget(self.lbl_debit_t)
        cd_layout.addWidget(self.lbl_debit_v)
        
        bal_row.addWidget(self.card_credit)
        bal_row.addWidget(self.card_debit)
        layout.addLayout(bal_row)
        
        # Details Fields Card
        fields_card = QFrame()
        fields_card.setProperty("class", "Card")
        f_layout = QVBoxLayout(fields_card)
        f_layout.setContentsMargins(20, 20, 20, 20)
        
        # QHBoxLayout for Title + Edit button
        det_header_row = QHBoxLayout()
        lbl_det_title = QLabel("Account Parameters Details")
        lbl_det_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        det_header_row.addWidget(lbl_det_title)
        det_header_row.addStretch()
        
        self.btn_edit_account = QPushButton("✏️  Edit Account")
        self.btn_edit_account.setCursor(Qt.PointingHandCursor)
        self.btn_edit_account.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                color: #155EEF;
                border: 1px solid #D0D5DD;
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F8F9FC;
                border: 1px solid #B2DDFF;
            }
        """)
        self.btn_edit_account.clicked.connect(self.handle_edit_account)
        det_header_row.addWidget(self.btn_edit_account)
        
        f_layout.addLayout(det_header_row)
        f_layout.addSpacing(10)
        
        grid = QGridLayout()
        grid.setSpacing(15)
        
        labels = ["Account Name", "Account Number", "IFSC Code", "Region / Location", "Account Age", "Vulnerability Status"]
        self.detail_fields = {}
        
        for idx, lbl_text in enumerate(labels):
            row = idx // 2
            col_lbl = (idx % 2) * 2
            col_val = col_lbl + 1
            
            lbl = QLabel(lbl_text)
            lbl.setStyleSheet("color: #667085; font-size: 12px; font-weight: bold;")
            
            val = QLineEdit()
            val.setReadOnly(True)
            val.setStyleSheet("background-color: #F8F9FC; border: 1px solid #E4E7EC; border-radius: 4px; padding: 6px;")
            
            grid.addWidget(lbl, row, col_lbl)
            grid.addWidget(val, row, col_val)
            self.detail_fields[lbl_text] = val
            
        f_layout.addLayout(grid)
        layout.addWidget(fields_card)
        
        # Connected Cards & Methods Distribution Row (Image 3 details)
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(20)
        
        # Connected Cards Mockup QFrame
        cards_mock_frame = QFrame()
        cards_mock_frame.setProperty("class", "Card")
        c_mock_layout = QVBoxLayout(cards_mock_frame)
        c_mock_layout.setContentsMargins(15, 15, 15, 15)
        
        lbl_c_t = QLabel("CONNECTED CARDS")
        lbl_c_t.setStyleSheet("font-size: 12px; font-weight: bold; color: #667085; margin-bottom: 10px;")
        c_mock_layout.addWidget(lbl_c_t)
        
        # Draw styled credit card mockup frame
        self.card_mock = QFrame()
        self.card_mock.setFixedSize(240, 130)
        self.card_mock.setStyleSheet(f"""
            QFrame {{
                background-color: #0B1F33;
                border-radius: 8px;
                border: 1px solid #1C3550;
            }}
        """)
        
        cm_layout = QVBoxLayout(self.card_mock)
        cm_layout.setContentsMargins(15, 15, 15, 15)
        
        lbl_visa = QLabel("VISA")
        lbl_visa.setStyleSheet("color: #FFFFFF; font-weight: bold; font-style: italic; font-size: 14px;")
        
        self.lbl_card_num = QLabel("xxxx xxxx xxxx 1029")
        self.lbl_card_num.setStyleSheet("color: #FFFFFF; font-size: 15px; font-family: monospace; font-weight: bold; margin-top: 10px;")
        
        self.lbl_card_holder = QLabel("AARAV SHARMA")
        self.lbl_card_holder.setStyleSheet("color: #98A2B3; font-size: 10px; font-weight: bold; text-transform: uppercase;")
        
        self.lbl_card_exp = QLabel("EXP: 08/29")
        self.lbl_card_exp.setStyleSheet("color: #98A2B3; font-size: 10px; font-weight: bold;")
        
        cm_layout.addWidget(lbl_visa)
        cm_layout.addWidget(self.lbl_card_num)
        cm_layout.addStretch()
        
        h_info = QHBoxLayout()
        h_info.addWidget(self.lbl_card_holder)
        h_info.addWidget(self.lbl_card_exp)
        cm_layout.addLayout(h_info)
        
        c_mock_layout.addWidget(self.card_mock)
        c_mock_layout.addStretch()
        bottom_row.addWidget(cards_mock_frame, 3)
        
        # Donut methods pie
        pm_frame = QFrame()
        pm_frame.setProperty("class", "Card")
        pm_v = QVBoxLayout(pm_frame)
        pm_v.setContentsMargins(15, 15, 15, 15)
        
        lbl_pm_t = QLabel("PAYMENT DISTRIBUTION SHARE")
        lbl_pm_t.setStyleSheet("font-size: 12px; font-weight: bold; color: #667085;")
        pm_v.addWidget(lbl_pm_t)
        
        self.pm_canvas = MChartCanvas(self, width=4.5, height=2.5)
        pm_v.addWidget(self.pm_canvas)
        bottom_row.addWidget(pm_frame, 5)
        
        layout.addLayout(bottom_row)
        
    def init_tx_tab(self):
        layout = QVBoxLayout(self.tab_tx)
        layout.setContentsMargins(15, 15, 15, 15)
        
        self.tbl_detail_txs = QTableWidget()
        self.tbl_detail_txs.setColumnCount(8)
        self.tbl_detail_txs.setHorizontalHeaderLabels(["ID", "Timestamp", "Opposite Party", "Amount", "Type", "Method", "Risk Score", "Status"])
        self.tbl_detail_txs.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_detail_txs.verticalHeader().setVisible(False)
        layout.addWidget(self.tbl_detail_txs)
        
    def init_net_tab(self):
        layout = QHBoxLayout(self.tab_net)
        layout.setContentsMargins(20, 20, 20, 20)
        
        self.net_canvas = MChartCanvas(self, width=6, height=5)
        layout.addWidget(self.net_canvas, 3)
        
        # Side stats panel
        stats_panel = QFrame()
        stats_panel.setProperty("class", "Card")
        stats_panel.setFixedWidth(200)
        s_layout = QVBoxLayout(stats_panel)
        s_layout.setContentsMargins(15, 15, 15, 15)
        
        lbl_title = QLabel("NET FLOW METRICS")
        lbl_title.setStyleSheet("font-size: 11px; font-weight: bold; color: #667085; text-transform: uppercase;")
        s_layout.addWidget(lbl_title)
        
        self.lbl_n_senders = QLabel("Unique Senders: 17")
        self.lbl_n_receivers = QLabel("Unique Receivers: 8")
        self.lbl_n_conns = QLabel("Total Connections: 25")
        self.lbl_n_rapid = QLabel("Rapid Transfers: 14")
        self.lbl_n_risk = QLabel("Network Risk Score: 96")
        
        for lbl in [self.lbl_n_senders, self.lbl_n_receivers, self.lbl_n_conns, self.lbl_n_rapid, self.lbl_n_risk]:
            lbl.setStyleSheet("color: #172B4D; font-size: 12px; border-bottom: 1px solid #E4E7EC; padding-bottom: 6px; padding-top: 6px;")
            s_layout.addWidget(lbl)
            
        s_layout.addStretch()
        layout.addWidget(stats_panel, 1)
        
    def init_ai_tab(self):
        layout = QVBoxLayout(self.tab_ai)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        charts = QHBoxLayout()
        charts.setSpacing(20)
        
        # Horizontal SHAP waterfall
        shap_frame = QFrame()
        shap_frame.setProperty("class", "Card")
        shap_v = QVBoxLayout(shap_frame)
        shap_v.addWidget(QLabel("Horizontal SHAP Impact factors"))
        self.shap_canvas = MChartCanvas(self, width=4, height=3)
        shap_v.addWidget(self.shap_canvas)
        charts.addWidget(shap_frame)
        
        # Progression line score
        prog_frame = QFrame()
        prog_frame.setProperty("class", "Card")
        prog_v = QVBoxLayout(prog_frame)
        prog_v.addWidget(QLabel("6-Month Risk Progression"))
        self.hist_canvas = MChartCanvas(self, width=4, height=3)
        prog_v.addWidget(self.hist_canvas)
        charts.addWidget(prog_frame)
        
        layout.addLayout(charts)
        
        # AI textual explanation block
        exp_frame = QFrame()
        exp_frame.setProperty("class", "Card")
        exp_frame.setStyleSheet("background-color: #F8F9FC; border: 1px solid #E4E7EC; border-radius: 6px; padding: 15px;")
        exp_layout = QVBoxLayout(exp_frame)
        
        lbl_title = QLabel("🧠 MULEGUARD REASONING EXPLANABILITY REPORT")
        lbl_title.setStyleSheet("font-weight: bold; font-size: 12px; color: #172B4D;")
        exp_layout.addWidget(lbl_title)
        
        self.lbl_explanation = QLabel("")
        self.lbl_explanation.setWordWrap(True)
        self.lbl_explanation.setStyleSheet("font-size: 13px; color: #172B4D; line-height: 18px; margin-top: 8px;")
        exp_layout.addWidget(self.lbl_explanation)
        
        self.lbl_recommended_action = QLabel("")
        self.lbl_recommended_action.setStyleSheet("font-weight: bold; font-size: 13px; color: #D92D20; margin-top: 10px;")
        exp_layout.addWidget(self.lbl_recommended_action)
        
        layout.addWidget(exp_frame)
        
    def init_rep_tab(self):
        layout = QVBoxLayout(self.tab_rep)
        layout.setContentsMargins(20, 20, 20, 20)
        
        preview_card = QFrame()
        preview_card.setProperty("class", "Card")
        p_layout = QVBoxLayout(preview_card)
        p_layout.setContentsMargins(20, 20, 20, 20)
        
        lbl_title = QLabel("Compliance Case Audit Draft Preview")
        lbl_title.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 10px;")
        p_layout.addWidget(lbl_title)
        
        self.lbl_report_preview = QLabel("")
        self.lbl_report_preview.setWordWrap(True)
        self.lbl_report_preview.setStyleSheet("font-size: 12px; font-family: monospace; color: #172B4D; background-color: #F8F9FC; border: 1px solid #E4E7EC; padding: 15px; border-radius: 4px;")
        p_layout.addWidget(self.lbl_report_preview)
        
        p_layout.addSpacing(15)
        
        self.btn_export = QPushButton("Generate & Save Investigation PDF Report")
        self.btn_export.setProperty("class", "PrimaryButton")
        self.btn_export.setFixedHeight(40)
        self.btn_export.clicked.connect(self.handle_export_pdf)
        p_layout.addWidget(self.btn_export)
        
        layout.addWidget(preview_card)
        layout.addStretch()
        
    def set_account(self, account_id):
        self.account_id = account_id
        self.load_data()
        
    def load_data(self):
        # Clear left scroll accounts
        for i in reversed(range(self.scroll_acc_layout.count())):
            widget = self.scroll_acc_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
                
        # Populate accounts list
        res = self.api.get_accounts()
        accs = res.get("accounts", [])
        
        for acc in accs:
            acc_id = acc["account_id"]
            
            card = QFrame()
            # If current active account, highlight select
            if acc_id == self.account_id:
                card.setStyleSheet(f"QFrame {{ background-color: #F0F4FE; border: 1px solid #D0E0FF; border-left: 4px solid {COLOR_PRIMARY_BLUE}; border-radius: 6px; padding: 8px; }}")
            else:
                card.setStyleSheet("QFrame { background-color: #FFFFFF; border: 1px solid #E4E7EC; border-radius: 6px; padding: 8px; } QFrame:hover { background-color: #F8F9FC; }")
                
            c_layout = QVBoxLayout(card)
            c_layout.setContentsMargins(8, 6, 8, 6)
            c_layout.setSpacing(4)
            
            h_row = QHBoxLayout()
            h_row.setContentsMargins(0, 0, 0, 0)
            lbl_name = QLabel(acc["holder_name"])
            lbl_name.setStyleSheet("font-weight: bold; font-size: 13px; color: #172B4D;")
            lbl_name.setWordWrap(True)
            
            risk_badge = QLabel(str(acc["risk_score"]))
            risk_color = COLOR_RISK_CRITICAL if acc["risk_score"]>=90 else (COLOR_RISK_HIGH if acc["risk_score"]>=75 else COLOR_RISK_MEDIUM)
            risk_badge.setStyleSheet(f"color: {risk_color}; font-weight: bold; font-size: 12px;")
            
            h_row.addWidget(lbl_name, 1)
            h_row.addWidget(risk_badge)
            c_layout.addLayout(h_row)
            
            lbl_number = QLabel(acc["account_number"])
            lbl_number.setStyleSheet("color: #667085; font-size: 11px;")
            lbl_number.setWordWrap(True)
            c_layout.addWidget(lbl_number)
            
            lbl_balances = QLabel(f"Cr: ₹{acc['credit_amount'] / 100000:.1f}L  •  Dr: ₹{acc['debit_amount'] / 100000:.1f}L")
            lbl_balances.setStyleSheet("color: #98A2B3; font-size: 11px; margin-top: 2px;")
            lbl_balances.setWordWrap(True)
            c_layout.addWidget(lbl_balances)
            
            # Simple mouse click event routing
            class ClickableFrame(QFrame):
                clicked = Signal(str)
                def mousePressEvent(self, event):
                    self.clicked.emit(self.acc_id)
                    
            card.acc_id = acc_id
            card.mousePressEvent = lambda e, aid=acc_id: self.set_account(aid)
            
            self.scroll_acc_layout.addWidget(card)
            
        # Update current selected account info panel
        acc = self.api.get_account_detail(self.account_id)
        if not acc: return
        
        self.lbl_acc_title.setText(f"ACCOUNT DETAILS: {acc['account_id']} | {acc['holder_name']}")
        self.lbl_status.setText(f"● {acc['status'].upper()}")
        
        self.lbl_credit_v.setText(f"₹{acc['credit_amount']:,}")
        self.lbl_debit_v.setText(f"₹{acc['debit_amount']:,}")
        
        # Connected mockup card values
        self.lbl_card_num.setText(acc["account_number"])
        self.lbl_card_holder.setText(acc["holder_name"].upper())
        
        # Fields mapping
        self.detail_fields["Account Name"].setText(acc["holder_name"])
        self.detail_fields["Account Number"].setText(acc["account_number"])
        self.detail_fields["IFSC Code"].setText(acc["ifsc_code"])
        self.detail_fields["Region / Location"].setText(f"{acc['region']} / {acc['city']}")
        self.detail_fields["Account Age"].setText(f"{acc['age_months']} months")
        self.detail_fields["Vulnerability Status"].setText(acc["status"])
        
        # Donut Chart method
        self.render_donut()
        
        # Sub Tab updates
        self.load_tx_ledger()
        self.load_network_topo()
        self.load_explainability()
        self.load_case_report(acc)
        
    def render_donut(self):
        self.pm_canvas.clear()
        methods = self.api.get_payment_methods()
        dist = methods["distribution"]
        
        labels = list(dist.keys())
        sizes = list(dist.values())
        colors = ["#155EEF", "#32D583", "#F79009", "#F04438", "#9B51E0", "#E4E7EC"]
        
        ax = self.pm_canvas.ax
        ax.clear()
        
        # Adjust layout spacing to squeeze pie left and leave space for the legend on the right
        self.pm_canvas.fig.subplots_adjust(left=0.05, right=0.55, top=0.9, bottom=0.1)
        
        total_val = sum(sizes)
        safe_sizes = sizes if total_val > 0 else [1, 0, 0, 0, 0, 0]
        
        wedges, texts = ax.pie(
            safe_sizes, startangle=90, colors=colors,
            wedgeprops=dict(width=0.25, edgecolor='w')
        )
        
        ax.text(0, 0, "Share %", ha='center', va='center', fontsize=8, weight='bold', color=COLOR_TEXT_PRIMARY)
        
        legend_labels = [f"{labels[i]} ({sizes[i]}%)" for i in range(len(labels))]
        ax.legend(wedges, legend_labels, loc="center left", bbox_to_anchor=(1.05, 0.5), frameon=False, fontsize=8)
        
        ax.axis('equal')
        self.pm_canvas.format_ax("")
        ax.grid(False)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        self.pm_canvas.draw()
        
    def load_tx_ledger(self):
        res = self.api.get_transactions(account_id=self.account_id)
        txs = res.get("transactions", [])
        
        self.tbl_detail_txs.setRowCount(len(txs))
        for row, tx in enumerate(txs):
            self.tbl_detail_txs.setItem(row, 0, QTableWidgetItem(tx["transaction_id"]))
            self.tbl_detail_txs.setItem(row, 1, QTableWidgetItem(tx["timestamp"]))
            
            opp_name = tx["sender_name"] if tx["receiver_id"] == self.account_id else tx["receiver_name"]
            opp_id = tx["sender_id"] if tx["receiver_id"] == self.account_id else tx["receiver_id"]
            self.tbl_detail_txs.setItem(row, 2, QTableWidgetItem(f"{opp_name} ({opp_id})"))
            
            # Amount with colors
            amt_item = QTableWidgetItem(f"₹{tx['amount']:,}")
            if tx["receiver_id"] == self.account_id:
                amt_item.setForeground(QColor(COLOR_RISK_LOW))
            else:
                amt_item.setForeground(QColor(COLOR_RISK_CRITICAL))
            self.tbl_detail_txs.setItem(row, 3, amt_item)
            
            self.tbl_detail_txs.setItem(row, 4, QTableWidgetItem(tx["transaction_type"]))
            self.tbl_detail_txs.setItem(row, 5, QTableWidgetItem(tx["payment_method"]))
            
            badge = TableBadgeLabel(str(tx["risk_score"]), "critical" if tx["risk_score"]>=80 else "medium")
            self.tbl_detail_txs.setCellWidget(row, 6, badge)
            
            self.tbl_detail_txs.setItem(row, 7, QTableWidgetItem(tx["status"]))
            
    def load_network_topo(self):
        self.net_canvas.clear()
        net_data = self.api.get_network(self.account_id)
        stats = net_data["stats"]
        
        self.lbl_n_senders.setText(f"Unique Senders: {stats['unique_senders']}")
        self.lbl_n_receivers.setText(f"Unique Receivers: {stats['unique_receivers']}")
        self.lbl_n_conns.setText(f"Total Connections: {stats['total_connections']}")
        self.lbl_n_rapid.setText(f"Rapid Transfers: {stats['rapid_transfers']}")
        self.lbl_n_risk.setText(f"Network Risk Score: {stats['network_risk']}")
        
        G = nx.DiGraph()
        node_colors = []
        labels = {}
        
        for node in net_data["nodes"]:
            G.add_node(node["id"], risk=node["risk_score"], label=node["label"])
            labels[node["id"]] = node["label"]
            
            if node["is_primary"]:
                node_colors.append(COLOR_PRIMARY_BLUE)
            elif node["risk_score"] >= 90:
                node_colors.append(COLOR_RISK_CRITICAL)
            elif node["risk_score"] >= 75:
                node_colors.append(COLOR_RISK_HIGH)
            elif node["risk_score"] >= 40:
                node_colors.append(COLOR_RISK_MEDIUM)
            else:
                node_colors.append(COLOR_RISK_LOW)
                
        for edge in net_data["edges"]:
            G.add_edge(edge["source"], edge["target"], label=f"₹{edge['amount']/1000:.0f}k")
            
        ax = self.net_canvas.ax
        pos = nx.spring_layout(G, seed=42)
        
        nx.draw_networkx_nodes(G, pos, ax=ax, node_color=node_colors, node_size=800, alpha=0.9)
        nx.draw_networkx_edges(G, pos, ax=ax, width=1.5, edge_color=COLOR_TEXT_MUTED, arrowsize=15, min_source_margin=10, min_target_margin=10)
        nx.draw_networkx_labels(G, pos, labels, ax=ax, font_size=7, font_family='DejaVu Sans', font_color='#0B1F33', font_weight='bold')
        
        edge_labels = nx.get_edge_attributes(G, 'label')
        nx.draw_networkx_edge_labels(G, pos, edge_labels, ax=ax, font_size=7)
        
        self.net_canvas.format_ax(f"Visual Network Topology ({self.account_id})")
        ax.grid(False)
        ax.axis('off')
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        self.net_canvas.draw()
        
    def load_explainability(self):
        self.shap_canvas.clear()
        exp = self.api.get_explanation(self.account_id)
        
        self.lbl_explanation.setText(exp["human_explanation"])
        self.lbl_recommended_action.setText(f"Recommended Compliance Action: {exp['recommended_action']}")
        
        # Update styling colors
        if exp["overall_score"] >= 90:
            self.lbl_recommended_action.setStyleSheet("font-weight: bold; font-size: 13px; color: #D92D20; margin-top: 10px;")
        else:
            self.lbl_recommended_action.setStyleSheet("font-weight: bold; font-size: 13px; color: #EAAA08; margin-top: 10px;")
            
        # Draw horizontal bars
        features = [f["feature"] for f in exp["shap_factors"]]
        impacts = [f["impact"] for f in exp["shap_factors"]]
        
        ax = self.shap_canvas.ax
        y_pos = range(len(features))
        bar_colors = [COLOR_RISK_CRITICAL if x > 0.2 else COLOR_PRIMARY_BLUE for x in impacts]
        
        ax.barh(y_pos, impacts, align='center', color=bar_colors, alpha=0.85, height=0.5)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(features, fontsize=8)
        ax.invert_yaxis()
        
        self.shap_canvas.format_ax("SHAP Impact Factors")
        self.shap_canvas.draw()
        
        # Risk trend line
        self.hist_canvas.clear()
        risk_profile = self.api.get_risk(self.account_id)
        history = risk_profile["history"]
        
        months = [h["month"] for h in history]
        scores = [h["score"] for h in history]
        
        ax_h = self.hist_canvas.ax
        ax_h.plot(months, scores, color=COLOR_RISK_CRITICAL, marker='s', linewidth=2)
        ax_h.set_ylim(0, 105)
        ax_h.axhline(y=75, color=COLOR_RISK_HIGH, linestyle=':', alpha=0.7, label='Suspicion Line')
        ax_h.legend(loc='lower right', fontsize=8)
        
        self.hist_canvas.format_ax("6-Month Risk Progression Score")
        self.hist_canvas.draw()
        
    def load_case_report(self, acc):
        exp = self.api.get_explanation(self.account_id)
        summary = (
            f"MULEGUARD AI COMPLIANCE AUDIT AUDIT DRAFT\n"
            f"================================================\n\n"
            f"Target Account: {acc['account_id']} | Holder: {acc['holder_name']}\n"
            f"Overall Risk Score: {acc['risk_score']} / 100 ({acc['risk_level']})\n"
            f"AI Mule Probability: {exp['probability']}%\n"
            f"Recommended Compliance Action: {exp['recommended_action']}\n\n"
            f"REASONING & FINDINGS EXPLANATION:\n"
            f"{exp['human_explanation']}\n\n"
            f"DEMOGRAPHIC & BALANCES REPORT:\n"
            f"- Masked Bank Card/Acc Num: {acc['account_number']}\n"
            f"- IFSC Code Branch: {acc['ifsc_code']}\n"
            f"- Region: {acc['region']} ({acc['city']})\n"
            f"- Age: {acc['age_months']} months\n"
            f"- Cumulative Inward Flow: ₹{acc['credit_amount']:,}\n"
            f"- Cumulative Outward Flow: ₹{acc['debit_amount']:,}\n"
        )
        self.lbl_report_preview.setText(summary)
        
    def handle_export_pdf(self):
        report_dir = "/Users/afsarazam/Desktop/MuleGuard/reports"
        os.makedirs(report_dir, exist_ok=True)
        pdf_path = f"{report_dir}/Investigation_Report_{self.account_id}.pdf"
        
        self.btn_export.setText("Compiling PDF...")
        self.btn_export.setEnabled(False)
        QApplication.processEvents()
        
        success = self.api.export_pdf_report(self.account_id, pdf_path)
        
        self.btn_export.setText("Generate & Save Investigation PDF Report")
        self.btn_export.setEnabled(True)
        
        if success:
            QMessageBox.information(
                self, "Report Exported",
                f"Compliance Investigation Report has been compiled and saved successfully to:\n\n{pdf_path}"
            )
        else:
            QMessageBox.critical(self, "Export Failed", "Error generated while compiling Report Lab PDF buffer structure.")

    def handle_edit_account(self):
        acc = self.api.get_account_detail(self.account_id)
        if not acc: return
        
        d = QDialog(self)
        d.setWindowTitle("Edit Account Registry Parameters")
        d.setFixedSize(400, 480)
        d.setStyleSheet(GLOBAL_STYLE)
        
        layout = QVBoxLayout(d)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)
        
        lbl_title = QLabel("✏️ Edit Account Parameters")
        lbl_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #172B4D;")
        layout.addWidget(lbl_title)
        
        lbl_sub = QLabel(f"Modifying compliance database records for Registry ID: {acc['account_id']}")
        lbl_sub.setWordWrap(True)
        lbl_sub.setStyleSheet("font-size: 11px; color: #667085;")
        layout.addWidget(lbl_sub)
        
        # Fields layout
        form = QFormLayout()
        form.setSpacing(10)
        
        txt_name = QLineEdit(acc["holder_name"])
        txt_num = QLineEdit(acc["account_number"])
        txt_ifsc = QLineEdit(acc["ifsc_code"])
        txt_region = QLineEdit(f"{acc['region']} / {acc['city']}")
        txt_credit = QLineEdit(str(int(acc["credit_amount"])))
        txt_debit = QLineEdit(str(int(acc["debit_amount"])))
        txt_risk = QLineEdit(str(acc["risk_score"]))
        
        form.addRow("Account Holder Name:", txt_name)
        form.addRow("Account Number:", txt_num)
        form.addRow("IFSC Code:", txt_ifsc)
        form.addRow("Region / City:", txt_region)
        form.addRow("Credit Flow Amount (₹):", txt_credit)
        form.addRow("Debit Flow Amount (₹):", txt_debit)
        form.addRow("AI Risk Score (0-100):", txt_risk)
        layout.addLayout(form)
        
        lbl_status = QLabel("")
        lbl_status.setStyleSheet("color: #D92D20; font-size: 11px; font-weight: bold;")
        layout.addWidget(lbl_status)
        
        # Actions
        btn_lay = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.setProperty("class", "SecondaryButton")
        btn_cancel.clicked.connect(d.reject)
        
        btn_save = QPushButton("Save Parameters")
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.setProperty("class", "PrimaryButton")
        btn_save.setStyleSheet("background-color: #155EEF; color: #FFFFFF;")
        
        def save_changes():
            name = txt_name.text().strip()
            num = txt_num.text().strip()
            ifsc = txt_ifsc.text().strip()
            region = txt_region.text().strip()
            credit_s = txt_credit.text().strip()
            debit_s = txt_debit.text().strip()
            risk_s = txt_risk.text().strip()
            
            if not name or not num or not ifsc or not region or not credit_s or not debit_s or not risk_s:
                lbl_status.setText("All parameter fields are mandatory.")
                return
                
            try:
                credit_val = float(credit_s)
                debit_val = float(debit_s)
                risk_val = int(risk_s)
                if not (0 <= risk_val <= 100):
                    lbl_status.setText("Risk score must be between 0 and 100.")
                    return
            except ValueError:
                lbl_status.setText("Numeric fields must contain valid numbers.")
                return
                
            # Update the DB
            self.api.update_account(self.account_id, name, num, ifsc, region, risk_val)
            # Update credit and debit float balances directly
            self.api.local_accounts[self.account_id]["credit_amount"] = credit_val
            self.api.local_accounts[self.account_id]["debit_amount"] = debit_val
            
            # Reload active console view & sidebar list
            self.load_data()
            if self.main_window:
                if hasattr(self.main_window, "page_dashboard") and hasattr(self.main_window.page_dashboard, "load_data"):
                    self.main_window.page_dashboard.load_data()
                self.main_window.switch_content_page(5)
                
            d.accept()
            
        btn_save.clicked.connect(save_changes)
        btn_lay.addWidget(btn_cancel)
        btn_lay.addWidget(btn_save)
        layout.addLayout(btn_lay)
        
        d.exec()


# ---------------------------------------------------------
# VIEW 6: FRAUD ANALYTICS VIEW
# ---------------------------------------------------------
class FraudAnalyticsView(QWidget):
    def __init__(self, api: ApiClient, main_window: MainWindow):
        super().__init__()
        self.api = api
        self.main_window = main_window
        
        # Default mock simulation data matching the mockup screenshot
        self.sim_total_cases = 14
        self.sim_total_amount = 8.7
        self.sim_suspicious_accounts = 6
        self.sim_avg_fraud_amount = 62143
        self.sim_detection_rate = 92.4
        
        # Payment Methods counts
        self.sim_pay_upi = 7
        self.sim_pay_debit = 4
        self.sim_pay_net = 2
        self.sim_pay_credit = 1
        
        # Risk Levels counts
        self.sim_risk_critical = 6
        self.sim_risk_high = 5
        self.sim_risk_medium = 2
        self.sim_risk_low = 1
        
        # Monthly counts (Mar - Aug)
        self.sim_months = ["Mar", "Apr", "May", "Jun", "Jul", "Aug"]
        self.sim_monthly_cases = [2, 3, 5, 6, 9, 14]
        self.sim_monthly_amounts = [1.2, 1.8, 2.6, 3.2, 4.2, 8.7]
        
        self.init_ui()
        
    def init_ui(self):
        # Use a master layout with scroll area to fit everything comfortably
        master_layout = QVBoxLayout(self)
        master_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background-color: transparent; border: none;")
        
        scroll_content = QWidget()
        scroll_content.setStyleSheet(f"background-color: {COLOR_BG};")
        layout = QVBoxLayout(scroll_content)
        layout.setContentsMargins(30, 20, 30, 25)
        layout.setSpacing(20)
        
        # ---------------------------------------------------------
        # TOP PANEL HEADER (TITLES + CONTROLS)
        # ---------------------------------------------------------
        header_row = QHBoxLayout()
        header_text_v = QVBoxLayout()
        header_text_v.setSpacing(2)
        
        lbl_h_title = QLabel("Fraud Analytics")
        lbl_h_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #172B4D;")
        lbl_h_desc = QLabel("Comprehensive fraud trends, patterns and insights")
        lbl_h_desc.setStyleSheet("font-size: 12px; color: #667085;")
        header_text_v.addWidget(lbl_h_title)
        header_text_v.addWidget(lbl_h_desc)
        header_row.addLayout(header_text_v)
        header_row.addStretch()
        
        # Date & Configure Simulation indicators
        btn_date = QPushButton("📅  01 Mar 2026 - 22 Aug 2026")
        btn_date.setStyleSheet("background-color: #FFFFFF; border: 1px solid #E4E7EC; border-radius: 6px; padding: 6px 12px; font-size: 12px; color: #172B4D;")
        
        self.btn_config_sim = QPushButton("⚙️  Configure Simulation Data")
        self.btn_config_sim.setCursor(Qt.PointingHandCursor)
        self.btn_config_sim.setStyleSheet("background-color: #155EEF; border: 1px solid #155EEF; border-radius: 6px; padding: 6px 12px; font-size: 12px; color: #FFFFFF; font-weight: bold;")
        self.btn_config_sim.clicked.connect(self.handle_config_simulation)
        
        btn_export = QPushButton("📤  Export ˇ")
        btn_export.setStyleSheet("background-color: #FFFFFF; border: 1px solid #E4E7EC; border-radius: 6px; padding: 6px 12px; font-size: 12px; color: #172B4D;")
        
        header_row.addWidget(btn_date)
        header_row.addWidget(self.btn_config_sim)
        header_row.addWidget(btn_export)
        layout.addLayout(header_row)
        
        # ---------------------------------------------------------
        # SECTION 1: TOP STATS GRID (5 CARDS)
        # ---------------------------------------------------------
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(15)
        
        kpi_items = [
            ("Fraud Transactions", "14", "+55.6% vs Last Month", "🔴", "background-color: #FEF3F2; color: #D92D20;"),
            ("Fraud Amount", "₹8.7 L", "+107.1% vs Last Month", "🔴", "background-color: #FEF3F2; color: #D92D20;"),
            ("Suspicious Accounts", "6", "+100% vs Last Month", "🟠", "background-color: #FFFAEB; color: #B54708;"),
            ("Avg. Fraud Amount", "₹62,143", "+32.4% vs Last Month", "🔵", "background-color: #F0F5FF; color: #175CD3;"),
            ("Fraud Detection Rate", "92.4%", "+8.7% vs Last Month", "🟢", "background-color: #ECFDF3; color: #027A48;")
        ]
        
        self.kpi_value_labels = {}
        self.kpi_trend_labels = {}
        
        for name, value, trend, emoji, style in kpi_items:
            card = QFrame()
            card.setProperty("class", "Card")
            card.setStyleSheet("background-color: #FFFFFF; border: 1px solid #E4E7EC; border-radius: 8px;")
            card_lay = QVBoxLayout(card)
            card_lay.setContentsMargins(15, 15, 15, 15)
            card_lay.setSpacing(6)
            
            # Header row: icon + title
            h_lay = QHBoxLayout()
            h_lay.setSpacing(8)
            lbl_icon = QLabel(emoji)
            lbl_icon.setFixedSize(26, 26)
            lbl_icon.setAlignment(Qt.AlignCenter)
            lbl_icon.setStyleSheet(f"border-radius: 13px; font-size: 14px; {style}")
            
            lbl_title = QLabel(name)
            lbl_title.setStyleSheet("font-size: 11px; font-weight: bold; color: #667085;")
            h_lay.addWidget(lbl_icon)
            h_lay.addWidget(lbl_title)
            h_lay.addStretch()
            card_lay.addLayout(h_lay)
            
            # Value
            lbl_val = QLabel(value)
            lbl_val.setStyleSheet("font-size: 22px; font-weight: bold; color: #172B4D;")
            card_lay.addWidget(lbl_val)
            self.kpi_value_labels[name] = lbl_val
            
            # Trend
            lbl_trend = QLabel(trend)
            if "8.7%" in trend: # Green trend
                lbl_trend.setStyleSheet("font-size: 10px; font-weight: bold; color: #027A48;")
            else: # Red/Orange trend
                lbl_trend.setStyleSheet("font-size: 10px; font-weight: bold; color: #B54708;")
            card_lay.addWidget(lbl_trend)
            self.kpi_trend_labels[name] = lbl_trend
            
            kpi_row.addWidget(card)
            
        layout.addLayout(kpi_row)
        
        # ---------------------------------------------------------
        # SECTION 2: CHARTS ROW (3 COLUMNS)
        # ---------------------------------------------------------
        charts_row = QHBoxLayout()
        charts_row.setSpacing(15)
        
        # Bar Chart Card
        bar_card = QFrame()
        bar_card.setProperty("class", "Card")
        bar_card.setStyleSheet("background-color: #FFFFFF; border: 1px solid #E4E7EC; border-radius: 8px;")
        bar_lay = QVBoxLayout(bar_card)
        bar_lay.setContentsMargins(15, 15, 15, 15)
        
        bar_title_h = QHBoxLayout()
        lbl_b_title = QLabel("Triggered Fraud Account Cases Count By Month")
        lbl_b_title.setStyleSheet("font-size: 12px; font-weight: bold; color: #172B4D;")
        lbl_b_opt = QLabel("Last 6 Months ˇ")
        lbl_b_opt.setStyleSheet("font-size: 10px; color: #667085;")
        bar_title_h.addWidget(lbl_b_title)
        bar_title_h.addStretch()
        bar_title_h.addWidget(lbl_b_opt)
        bar_lay.addLayout(bar_title_h)
        
        self.bar_canvas = MChartCanvas(self, width=4, height=3)
        bar_lay.addWidget(self.bar_canvas)
        charts_row.addWidget(bar_card, 4)
        
        # Donut 1 Card (Payment Methods)
        donut1_card = QFrame()
        donut1_card.setProperty("class", "Card")
        donut1_card.setStyleSheet("background-color: #FFFFFF; border: 1px solid #E4E7EC; border-radius: 8px;")
        donut1_lay = QVBoxLayout(donut1_card)
        donut1_lay.setContentsMargins(15, 15, 15, 15)
        
        lbl_d1_title = QLabel("Fraud Overview (Current Month)")
        lbl_d1_title.setStyleSheet("font-size: 12px; font-weight: bold; color: #172B4D;")
        donut1_lay.addWidget(lbl_d1_title)
        
        self.donut1_canvas = MChartCanvas(self, width=3, height=3)
        donut1_lay.addWidget(self.donut1_canvas)
        charts_row.addWidget(donut1_card, 3)
        
        # Donut 2 Card (Risk Levels)
        donut2_card = QFrame()
        donut2_card.setProperty("class", "Card")
        donut2_card.setStyleSheet("background-color: #FFFFFF; border: 1px solid #E4E7EC; border-radius: 8px;")
        donut2_lay = QVBoxLayout(donut2_card)
        donut2_lay.setContentsMargins(15, 15, 15, 15)
        
        lbl_d2_title = QLabel("Fraud by Risk Level (Current Month)")
        lbl_d2_title.setStyleSheet("font-size: 12px; font-weight: bold; color: #172B4D;")
        donut2_lay.addWidget(lbl_d2_title)
        
        self.donut2_canvas = MChartCanvas(self, width=3, height=3)
        donut2_lay.addWidget(self.donut2_canvas)
        charts_row.addWidget(donut2_card, 3)
        
        layout.addLayout(charts_row)
        
        # ---------------------------------------------------------
        # SECTION 3: MOM TABLE, REASONS & LINE CHART ROW (3 COLUMNS)
        # ---------------------------------------------------------
        bottom_grid_row = QHBoxLayout()
        bottom_grid_row.setSpacing(15)
        
        # Table 1: MoM Comparison Card
        mom_card = QFrame()
        mom_card.setProperty("class", "Card")
        mom_card.setStyleSheet("background-color: #FFFFFF; border: 1px solid #E4E7EC; border-radius: 8px;")
        mom_lay = QVBoxLayout(mom_card)
        mom_lay.setContentsMargins(15, 15, 15, 15)
        
        lbl_m_title = QLabel("Month-over-Month Comparison")
        lbl_m_title.setStyleSheet("font-size: 12px; font-weight: bold; color: #172B4D; margin-bottom: 8px;")
        mom_lay.addWidget(lbl_m_title)
        
        self.tbl_mom = QTableWidget()
        self.tbl_mom.setColumnCount(5)
        self.tbl_mom.setRowCount(5)
        self.tbl_mom.setHorizontalHeaderLabels(["Metric", "Aug 2026", "Jul 2026", "Change", "Change %"])
        self.tbl_mom.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_mom.verticalHeader().setVisible(False)
        self.tbl_mom.setStyleSheet("QTableWidget { font-size: 11px; border: none; } QHeaderView::section { font-size: 10px; }")
        mom_lay.addWidget(self.tbl_mom)
        bottom_grid_row.addWidget(mom_card, 4)
        
        # Table 2: Top Reasons Card
        reasons_card = QFrame()
        reasons_card.setProperty("class", "Card")
        reasons_card.setStyleSheet("background-color: #FFFFFF; border: 1px solid #E4E7EC; border-radius: 8px;")
        reasons_lay = QVBoxLayout(reasons_card)
        reasons_lay.setContentsMargins(15, 15, 15, 15)
        
        lbl_r_title = QLabel("Top Fraud Reasons (Current Month)")
        lbl_r_title.setStyleSheet("font-size: 12px; font-weight: bold; color: #172B4D; margin-bottom: 8px;")
        reasons_lay.addWidget(lbl_r_title)
        
        self.tbl_reasons = QTableWidget()
        self.tbl_reasons.setColumnCount(3)
        self.tbl_reasons.setRowCount(5)
        self.tbl_reasons.setHorizontalHeaderLabels(["Reason", "Cases", "%"])
        self.tbl_reasons.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_reasons.verticalHeader().setVisible(False)
        self.tbl_reasons.setStyleSheet("QTableWidget { font-size: 11px; border: none; }")
        reasons_lay.addWidget(self.tbl_reasons)
        bottom_grid_row.addWidget(reasons_card, 3)
        
        # Line Chart Card (Trend Amount)
        trend_card = QFrame()
        trend_card.setProperty("class", "Card")
        trend_card.setStyleSheet("background-color: #FFFFFF; border: 1px solid #E4E7EC; border-radius: 8px;")
        trend_lay = QVBoxLayout(trend_card)
        trend_lay.setContentsMargins(15, 15, 15, 15)
        
        trend_h = QHBoxLayout()
        lbl_tr_title = QLabel("Fraud Trend (Amount)")
        lbl_tr_title.setStyleSheet("font-size: 12px; font-weight: bold; color: #172B4D;")
        lbl_tr_opt = QLabel("Last 6 Months ˇ")
        lbl_tr_opt.setStyleSheet("font-size: 10px; color: #667085;")
        trend_h.addWidget(lbl_tr_title)
        trend_h.addStretch()
        trend_h.addWidget(lbl_tr_opt)
        trend_lay.addLayout(trend_h)
        
        self.trend_canvas = MChartCanvas(self, width=4, height=3)
        trend_lay.addWidget(self.trend_canvas)
        bottom_grid_row.addWidget(trend_card, 3)
        
        layout.addLayout(bottom_grid_row)
        
        # ---------------------------------------------------------
        # SECTION 4: BOTTOM RECENT FRAUD CASES TABLE
        # ---------------------------------------------------------
        recent_card = QFrame()
        recent_card.setProperty("class", "Card")
        recent_card.setStyleSheet("background-color: #FFFFFF; border: 1px solid #E4E7EC; border-radius: 8px;")
        rec_lay = QVBoxLayout(recent_card)
        rec_lay.setContentsMargins(20, 20, 20, 20)
        
        lbl_rec_title = QLabel("Recent Fraud Cases")
        lbl_rec_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #172B4D; margin-bottom: 10px;")
        rec_lay.addWidget(lbl_rec_title)
        
        self.tbl_recent = QTableWidget()
        self.tbl_recent.setColumnCount(9)
        self.tbl_recent.setRowCount(2)
        self.tbl_recent.setHorizontalHeaderLabels([
            "Case ID", "Account ID", "Account Holder", "Amount", "Payment Method", 
            "Risk Level", "Detected On", "Status", "Action"
        ])
        self.tbl_recent.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_recent.verticalHeader().setVisible(False)
        self.tbl_recent.setStyleSheet("QTableWidget { font-size: 12px; border: none; }")
        
        recent_cases = [
            ("FRD-10492", "ACC-10293", "Aarav Sharma", "₹85,000", "UPI", "Critical", "22 Aug 2026, 10:42 AM", "Under Investigation"),
            ("FRD-10488", "ACC-88421", "Rahul Verma", "₹42,500", "UPI", "High", "22 Aug 2026, 09:31 AM", "Under Review")
        ]
        
        for row, case in enumerate(recent_cases):
            self.tbl_recent.setItem(row, 0, QTableWidgetItem(case[0]))
            self.tbl_recent.setItem(row, 1, QTableWidgetItem(case[1]))
            self.tbl_recent.setItem(row, 2, QTableWidgetItem(case[2]))
            self.tbl_recent.setItem(row, 3, QTableWidgetItem(case[3]))
            self.tbl_recent.setItem(row, 4, QTableWidgetItem(case[4]))
            
            # Risk Level Badge
            badge_text = case[5]
            badge_style = "critical" if badge_text.lower() == "critical" else "high"
            self.tbl_recent.setCellWidget(row, 5, TableBadgeLabel(badge_text, badge_style))
            
            self.tbl_recent.setItem(row, 6, QTableWidgetItem(case[6]))
            
            # Status Badge
            status_text = case[7]
            status_style = "warning" if "investigation" in status_text.lower() else "medium"
            self.tbl_recent.setCellWidget(row, 7, TableBadgeLabel(status_text, status_style))
            
            # Action Button
            btn_view = QPushButton("👁️")
            btn_view.setCursor(Qt.PointingHandCursor)
            btn_view.setStyleSheet("background: transparent; border: none; font-size: 14px;")
            acc_id = case[1]
            btn_view.clicked.connect(lambda checked, aid=acc_id: self.main_window.investigate_account(aid))
            self.tbl_recent.setCellWidget(row, 8, btn_view)
            
        rec_lay.addWidget(self.tbl_recent)
        layout.addWidget(recent_card)
        
        # Assemble scroll area
        scroll.setWidget(scroll_content)
        master_layout.addWidget(scroll)
        
    def load_data(self):
        # 1. Fetch monthly analytics details from API
        data = self.api.get_analytics_monthly()
        if data:
            aug = data.get("august", {})
            jul = data.get("july", {})
            changes = data.get("changes", {})
            history = data.get("history", [])
            
            # Map history
            if history:
                self.sim_months = [h["month"] for h in history]
                self.sim_monthly_cases = [h["count"] for h in history]
                self.sim_monthly_amounts = [round(h["count"] * 0.6, 1) for h in history]
            
            self.sim_total_amount = aug.get("fraud_amount_lakhs", 0.0)
            self.sim_suspicious_accounts = aug.get("suspicious_accounts", 0)
            
            # Breakdowns
            p_breakdown = aug.get("payment_breakdown", {})
            self.sim_pay_upi = p_breakdown.get("UPI", 0)
            self.sim_pay_debit = p_breakdown.get("Debit Card", 0)
            self.sim_pay_net = p_breakdown.get("Net Banking", 0)
            self.sim_pay_credit = p_breakdown.get("Credit Card", 0)
            
            r_breakdown = aug.get("risk_breakdown", {})
            self.sim_risk_critical = r_breakdown.get("Critical", 0)
            self.sim_risk_high = r_breakdown.get("High", 0)
            self.sim_risk_medium = r_breakdown.get("Medium", 0)
            self.sim_risk_low = r_breakdown.get("Low", 0)
            
            tot_flagged = aug.get("fraud_transactions", 0)
            self.sim_avg_fraud_amount = int(self.sim_total_amount * 100000 / tot_flagged) if tot_flagged > 0 else 0
            self.sim_detection_rate = 94.5 if tot_flagged > 0 else 0.0
            
        # 0. Update KPI stats labels dynamically from simulated variables
        total_p_cases = self.sim_pay_upi + self.sim_pay_debit + self.sim_pay_net + self.sim_pay_credit
        total_r_cases = self.sim_risk_critical + self.sim_risk_high + self.sim_risk_medium + self.sim_risk_low
        total_cases = total_p_cases
        
        self.kpi_value_labels["Fraud Transactions"].setText(str(total_cases))
        self.kpi_value_labels["Fraud Amount"].setText(f"₹{self.sim_total_amount:.1f} L")
        self.kpi_value_labels["Suspicious Accounts"].setText(str(self.sim_suspicious_accounts))
        self.kpi_value_labels["Avg. Fraud Amount"].setText(f"₹{self.sim_avg_fraud_amount:,}")
        self.kpi_value_labels["Fraud Detection Rate"].setText(f"{self.sim_detection_rate:.1f}%")
        
        # Previous Month Values (July)
        prev_cases = self.sim_monthly_cases[-2] if len(self.sim_monthly_cases) >= 2 else 9
        prev_amt = self.sim_monthly_amounts[-2] if len(self.sim_monthly_amounts) >= 2 else 4.2
        
        diff_cases_pct = ((total_cases - prev_cases) / prev_cases) * 100 if prev_cases else 0
        diff_amt_pct = ((self.sim_total_amount - prev_amt) / prev_amt) * 100 if prev_amt else 0
        
        self.kpi_trend_labels["Fraud Transactions"].setText(f"{'+' if diff_cases_pct>=0 else ''}{diff_cases_pct:.1f}% vs Last Month")
        self.kpi_trend_labels["Fraud Amount"].setText(f"{'+' if diff_amt_pct>=0 else ''}{diff_amt_pct:.1f}% vs Last Month")
        
        # 1. Bar Chart Data Setup
        self.bar_canvas.clear()
        ax_bar = self.bar_canvas.ax
        months = self.sim_months
        cases_count = list(self.sim_monthly_cases)
        if cases_count:
            cases_count[-1] = total_cases
            self.sim_monthly_cases[-1] = total_cases
            
        ax_bar.bar(months, cases_count, color="#155EEF", width=0.4, zorder=3)
        for idx, val in enumerate(cases_count):
            ax_bar.text(idx, val + 0.4, str(val), ha='center', va='bottom', fontsize=8, color="#172B4D", weight='bold')
            
        ax_bar.set_ylabel("Cases", fontsize=8, color="#667085")
        ax_bar.set_ylim(0, max(cases_count) * 1.2 if cases_count else 16)
        self.bar_canvas.format_ax("")
        self.bar_canvas.draw()
        
        # 2. Donut Chart 1 (Payment Methods)
        self.donut1_canvas.clear()
        ax_d1 = self.donut1_canvas.ax
        labels_d1 = ["UPI", "Debit Card", "Net Banking", "Credit Card"]
        sizes_d1 = [self.sim_pay_upi, self.sim_pay_debit, self.sim_pay_net, self.sim_pay_credit]
        colors_d1 = ["#155EEF", "#32D583", "#F79009", "#F04438"]
        
        # Adjust layout spacing to squeeze pie left and leave space for the legend on the right
        self.donut1_canvas.fig.subplots_adjust(left=0.02, right=0.42, top=0.9, bottom=0.1)
        
        safe_sizes_d1 = sizes_d1 if sum(sizes_d1) > 0 else [1, 0, 0, 0]
        wedges1, texts1 = ax_d1.pie(
            safe_sizes_d1, startangle=90, colors=colors_d1, 
            wedgeprops=dict(width=0.25, edgecolor='w')
        )
        ax_d1.text(0, 0, f"{total_cases}\nTotal", ha='center', va='center', fontsize=9, weight='bold', color="#172B4D")
        
        legend_labels = [f"{labels_d1[i]}  {sizes_d1[i]} ({sizes_d1[i]/total_cases*100 if total_cases else 0:.1f}%)" for i in range(len(labels_d1))]
        ax_d1.legend(wedges1, legend_labels, loc="center left", bbox_to_anchor=(1.02, 0.5), frameon=False, fontsize=7)
        ax_d1.axis('equal')
        self.donut1_canvas.draw()
        
        # 3. Donut Chart 2 (Risk Levels)
        self.donut2_canvas.clear()
        ax_d2 = self.donut2_canvas.ax
        labels_d2 = ["Critical", "High", "Medium", "Low"]
        sizes_d2 = [self.sim_risk_critical, self.sim_risk_high, self.sim_risk_medium, self.sim_risk_low]
        colors_d2 = ["#F04438", "#F79009", "#FDB022", "#32D583"]
        
        # Adjust layout spacing to squeeze pie left and leave space for the legend on the right
        self.donut2_canvas.fig.subplots_adjust(left=0.02, right=0.42, top=0.9, bottom=0.1)
        
        safe_sizes_d2 = sizes_d2 if sum(sizes_d2) > 0 else [1, 0, 0, 0]
        wedges2, texts2 = ax_d2.pie(
            safe_sizes_d2, startangle=90, colors=colors_d2, 
            wedgeprops=dict(width=0.25, edgecolor='w')
        )
        ax_d2.text(0, 0, f"{total_r_cases}\nTotal", ha='center', va='center', fontsize=9, weight='bold', color="#172B4D")
        
        legend_labels_d2 = [f"{labels_d2[i]}  {sizes_d2[i]} ({sizes_d2[i]/total_r_cases*100 if total_r_cases else 0:.1f}%)" for i in range(len(labels_d2))]
        ax_d2.legend(wedges2, legend_labels_d2, loc="center left", bbox_to_anchor=(1.02, 0.5), frameon=False, fontsize=7)
        ax_d2.axis('equal')
        self.donut2_canvas.draw()
        
        # 4. Trend Chart (Fraud Amount Lakhs)
        self.trend_canvas.clear()
        ax_tr = self.trend_canvas.ax
        amounts_l = list(self.sim_monthly_amounts)
        if amounts_l:
            amounts_l[-1] = self.sim_total_amount
            self.sim_monthly_amounts[-1] = self.sim_total_amount
            
        ax_tr.plot(months, amounts_l, marker='o', markersize=4, color="#155EEF", linewidth=2, zorder=3)
        ax_tr.fill_between(months, amounts_l, color="#155EEF", alpha=0.1, zorder=2)
        
        for idx, val in enumerate(amounts_l):
            ax_tr.text(idx, val + 0.3, f"{val:.1f}", ha='center', va='bottom', fontsize=8, color="#172B4D", weight='bold')
            
        ax_tr.set_ylabel("Amount (₹ Lakhs)", fontsize=8, color="#667085")
        ax_tr.set_ylim(0, max(amounts_l) * 1.2 if amounts_l else 10.5)
        self.trend_canvas.format_ax("")
        self.trend_canvas.draw()
        
        # 5. Month-over-Month Comparison Grid
        self.tbl_mom.clearContents()
        mom_data = [
            ("Fraud Transactions", str(total_cases), str(prev_cases), f"+{total_cases-prev_cases}" if total_cases>=prev_cases else str(total_cases-prev_cases), f"{'+' if diff_cases_pct>=0 else ''}{diff_cases_pct:.1f}%"),
            ("Fraud Amount", f"₹{self.sim_total_amount:.1f} L", f"₹{prev_amt:.1f} L", f"+₹{self.sim_total_amount-prev_amt:.1f} L" if self.sim_total_amount>=prev_amt else f"-₹{abs(self.sim_total_amount-prev_amt):.1f} L", f"{'+' if diff_amt_pct>=0 else ''}{diff_amt_pct:.1f}%"),
            ("Suspicious Accounts", str(self.sim_suspicious_accounts), "3", f"+{self.sim_suspicious_accounts-3}" if self.sim_suspicious_accounts>=3 else str(self.sim_suspicious_accounts-3), f"{'+' if (self.sim_suspicious_accounts-3)>=0 else ''}{(self.sim_suspicious_accounts-3)/3*100:.1f}%"),
            ("High Risk Accounts", "4", "2", "+2", "+100%"),
            ("Blocked Transactions", "11", "6", "+5", "+83.3%")
        ]
        for row, item in enumerate(mom_data):
            for col, val in enumerate(item):
                cell = QTableWidgetItem(val)
                if col in [3, 4] and "+" in val:
                    cell.setForeground(QColor("#D92D20"))
                    cell.setFont(QFont("Inter", 11, QFont.Bold))
                elif col in [3, 4] and "-" in val:
                    cell.setForeground(QColor("#027A48"))
                    cell.setFont(QFont("Inter", 11, QFont.Bold))
                self.tbl_mom.setItem(row, col, cell)
                
        # 6. Top Reasons Grid
        self.tbl_reasons.clearContents()
        reasons_data = [
            ("Rapid Fund Movement", str(int(total_cases*0.43)), f"{total_cases*0.43/total_cases*100 if total_cases else 0:.1f}%"),
            ("Unusual Transaction Velocity", str(int(total_cases*0.21)), f"{total_cases*0.21/total_cases*100 if total_cases else 0:.1f}%"),
            ("New Beneficiary", str(int(total_cases*0.14)), f"{total_cases*0.14/total_cases*100 if total_cases else 0:.1f}%"),
            ("High Risk Counterparty", str(int(total_cases*0.14)), f"{total_cases*0.14/total_cases*100 if total_cases else 0:.1f}%"),
            ("Location Anomaly", str(int(total_cases*0.07)), f"{total_cases*0.07/total_cases*100 if total_cases else 0:.1f}%")
        ]
        for row, item in enumerate(reasons_data):
            self.tbl_reasons.setItem(row, 0, QTableWidgetItem(item[0]))
            self.tbl_reasons.setItem(row, 1, QTableWidgetItem(item[1]))
            pct_bar = QLabel(item[2])
            pct_bar.setStyleSheet("color: #155EEF; font-weight: bold; font-size: 11px;")
            self.tbl_reasons.setCellWidget(row, 2, pct_bar)
            
    def handle_config_simulation(self):
        d = QDialog(self)
        d.setWindowTitle("Configure Analytics Simulation Parameters")
        d.setFixedSize(500, 560)
        d.setStyleSheet(GLOBAL_STYLE)
        
        layout = QVBoxLayout(d)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)
        
        lbl_title = QLabel("⚙️ Configure Presentation Simulation Data")
        lbl_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #172B4D;")
        layout.addWidget(lbl_title)
        
        lbl_sub = QLabel("Override frontend KPI figures, payments slices, and monthly historical charts in real-time.")
        lbl_sub.setStyleSheet("font-size: 11px; color: #667085;")
        layout.addWidget(lbl_sub)
        
        tab_widget = QTabWidget()
        logo_path = os.path.join(os.path.dirname(__file__), "logo.png")
        tab_icon = QIcon(logo_path)
        
        # Tab 1: KPIs
        tab_kpis = QWidget()
        kpi_lay = QFormLayout(tab_kpis)
        kpi_lay.setSpacing(10)
        
        txt_total_amt = QLineEdit(str(self.sim_total_amount))
        txt_susp_accs = QLineEdit(str(self.sim_suspicious_accounts))
        txt_avg_amt = QLineEdit(str(self.sim_avg_fraud_amount))
        txt_det_rate = QLineEdit(str(self.sim_detection_rate))
        
        kpi_lay.addRow("Simulated Fraud Amount (₹ Lakhs):", txt_total_amt)
        kpi_lay.addRow("Suspicious Accounts Count:", txt_susp_accs)
        kpi_lay.addRow("Average Fraud Ticket (₹):", txt_avg_amt)
        kpi_lay.addRow("Detection Success Rate (%):", txt_det_rate)
        tab_widget.addTab(tab_kpis, tab_icon, "KPI Stats")
        
        # Tab 2: Slices
        tab_slices = QWidget()
        slices_lay = QFormLayout(tab_slices)
        slices_lay.setSpacing(10)
        
        txt_upi = QLineEdit(str(self.sim_pay_upi))
        txt_debit = QLineEdit(str(self.sim_pay_debit))
        txt_net = QLineEdit(str(self.sim_pay_net))
        txt_credit = QLineEdit(str(self.sim_pay_credit))
        
        txt_crit = QLineEdit(str(self.sim_risk_critical))
        txt_high = QLineEdit(str(self.sim_risk_high))
        txt_med = QLineEdit(str(self.sim_risk_medium))
        txt_low = QLineEdit(str(self.sim_risk_low))
        
        slices_lay.addRow("UPI Cases count:", txt_upi)
        slices_lay.addRow("Debit Card Cases count:", txt_debit)
        slices_lay.addRow("Net Banking Cases count:", txt_net)
        slices_lay.addRow("Credit Card Cases count:", txt_credit)
        slices_lay.addRow("Critical Risk Cases count:", txt_crit)
        slices_lay.addRow("High Risk Cases count:", txt_high)
        slices_lay.addRow("Medium Risk Cases count:", txt_med)
        slices_lay.addRow("Low Risk Cases count:", txt_low)
        tab_widget.addTab(tab_slices, tab_icon, "Payment & Risks")
        
        # Tab 3: Monthly History (Mar to Aug)
        tab_history = QWidget()
        hist_lay = QGridLayout(tab_history)
        hist_lay.setSpacing(10)
        
        hist_lay.addWidget(QLabel("Month"), 0, 0)
        hist_lay.addWidget(QLabel("Cases Count"), 0, 1)
        hist_lay.addWidget(QLabel("Fraud Amount (Lakhs)"), 0, 2)
        
        hist_inputs = []
        for idx, m in enumerate(self.sim_months):
            lbl_m = QLabel(m)
            txt_c = QLineEdit(str(self.sim_monthly_cases[idx]))
            txt_a = QLineEdit(str(self.sim_monthly_amounts[idx]))
            
            hist_lay.addWidget(lbl_m, idx+1, 0)
            hist_lay.addWidget(txt_c, idx+1, 1)
            hist_lay.addWidget(txt_a, idx+1, 2)
            
            hist_inputs.append((txt_c, txt_a))
            
        tab_widget.addTab(tab_history, tab_icon, "Monthly Trends")
        
        layout.addWidget(tab_widget)
        
        lbl_err = QLabel("")
        lbl_err.setStyleSheet("color: #D92D20; font-size: 11px; font-weight: bold;")
        layout.addWidget(lbl_err)
        
        # Actions
        btn_lay = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setProperty("class", "SecondaryButton")
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.clicked.connect(d.reject)
        
        btn_save = QPushButton("Apply Simulation Changes")
        btn_save.setProperty("class", "PrimaryButton")
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.setStyleSheet("background-color: #155EEF; color: #FFFFFF;")
        
        def save_sim():
            try:
                # Validation checks
                total_amt_val = float(txt_total_amt.text().strip())
                susp_accs_val = int(txt_susp_accs.text().strip())
                avg_amt_val = float(txt_avg_amt.text().strip())
                det_rate_val = float(txt_det_rate.text().strip())
                
                upi_val = int(txt_upi.text().strip())
                debit_val = int(txt_debit.text().strip())
                net_val = int(txt_net.text().strip())
                credit_val = int(txt_credit.text().strip())
                
                crit_val = int(txt_crit.text().strip())
                high_val = int(txt_high.text().strip())
                med_val = int(txt_med.text().strip())
                low_val = int(txt_low.text().strip())
                
                # Check negative values
                if any(x < 0 for x in [total_amt_val, susp_accs_val, avg_amt_val, det_rate_val, upi_val, debit_val, net_val, credit_val, crit_val, high_val, med_val, low_val]):
                    lbl_err.setText("Metrics cannot contain negative values.")
                    return
                
                # Read monthly list values
                m_cases = []
                m_amounts = []
                for txt_c, txt_a in hist_inputs:
                    c_val = int(txt_c.text().strip())
                    a_val = float(txt_a.text().strip())
                    if c_val < 0 or a_val < 0:
                        lbl_err.setText("Monthly figures cannot contain negative numbers.")
                        return
                    m_cases.append(c_val)
                    m_amounts.append(a_val)
                
                # Set values
                self.sim_total_amount = total_amt_val
                self.sim_suspicious_accounts = susp_accs_val
                self.sim_avg_fraud_amount = avg_amt_val
                self.sim_detection_rate = det_rate_val
                
                self.sim_pay_upi = upi_val
                self.sim_pay_debit = debit_val
                self.sim_pay_net = net_val
                self.sim_pay_credit = credit_val
                
                self.sim_risk_critical = crit_val
                self.sim_risk_high = high_val
                self.sim_risk_medium = med_val
                self.sim_risk_low = low_val
                
                self.sim_monthly_cases = m_cases
                self.sim_monthly_amounts = m_amounts
                
                # Reload view
                self.load_data()
                d.accept()
            except ValueError:
                lbl_err.setText("Please insert valid numbers into the parameter fields.")
                
        btn_save.clicked.connect(save_sim)
        btn_lay.addWidget(btn_cancel)
        btn_lay.addWidget(btn_save)
        layout.addLayout(btn_lay)
        
        d.exec()


# ---------------------------------------------------------
# VIEW 7: REGIONAL RISK VIEW
# ---------------------------------------------------------
class RegionalRiskView(QWidget):
    def __init__(self, api: ApiClient, main_window: MainWindow):
        super().__init__()
        self.api = api
        self.main_window = main_window
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(20)
        
        self.tbl = QTableWidget()
        self.tbl.setColumnCount(7)
        self.tbl.setHorizontalHeaderLabels([
            "Region Location", "Total Registry Accounts", "Transaction Count", "Fraud Count",
            "Total Volume Value", "Active Alerts", "Regional Risk Tier"
        ])
        self.tbl.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl.verticalHeader().setVisible(False)
        layout.addWidget(self.tbl)
        
    def load_data(self):
        regions = self.api.get_regional_risk()
        self.tbl.setRowCount(len(regions))
        for row, reg in enumerate(regions):
            self.tbl.setItem(row, 0, QTableWidgetItem(reg["region"]))
            self.tbl.setItem(row, 1, QTableWidgetItem(f"{reg['accounts_count']:,}"))
            self.tbl.setItem(row, 2, QTableWidgetItem(f"{reg['transactions_count']:,}"))
            self.tbl.setItem(row, 3, QTableWidgetItem(str(reg["fraud_count"])))
            self.tbl.setItem(row, 4, QTableWidgetItem(f"₹{reg['volume'] / 100000:.1f} Lakhs"))
            self.tbl.setItem(row, 5, QTableWidgetItem(str(reg["active_alerts"])))
            
            badge = TableBadgeLabel(reg["risk"], reg["risk"].lower())
            self.tbl.setCellWidget(row, 6, badge)


# ---------------------------------------------------------
# VIEW 8: PAYMENT METHODS VIEW
# ---------------------------------------------------------
class SparklineWidget(QWidget):
    def __init__(self, color="#32D583", parent=None):
        super().__init__(parent)
        self.color = color
        self.setMinimumSize(80, 20)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(QColor(self.color), 1.5)
        painter.setPen(pen)
        
        w = self.width()
        h = self.height()
        
        path = QPainterPath()
        if self.color == "#32D583": # Up trend sparkline
            points = [
                (5, h - 5),
                (w * 0.2, h - 8),
                (w * 0.4, h - 4),
                (w * 0.6, h - 12),
                (w * 0.8, h - 7),
                (w - 5, 5)
            ]
        else: # Down trend sparkline
            points = [
                (5, 5),
                (w * 0.2, 8),
                (w * 0.4, 4),
                (w * 0.6, 12),
                (w * 0.8, 7),
                (w - 5, h - 5)
            ]
        path.moveTo(points[0][0], points[0][1])
        for pt in points[1:]:
            path.lineTo(pt[0], pt[1])
        painter.drawPath(path)


class PaymentMethodsView(QWidget):
    def __init__(self, api: ApiClient, main_window: MainWindow):
        super().__init__()
        self.api = api
        self.main_window = main_window
        
        # Payment Methods Detail Simulation records (Default matching mockup screenshot)
        self.sim_upi_txs = 11418
        self.sim_upi_amt = 52.4
        self.sim_upi_avg = 45912
        self.sim_upi_risk = 28
        self.sim_upi_trend = "#32D583"
        
        self.sim_debit_txs = 4421
        self.sim_debit_amt = 18.6
        self.sim_debit_avg = 42136
        self.sim_debit_risk = 24
        self.sim_debit_trend = "#32D583"
        
        self.sim_credit_txs = 1658
        self.sim_credit_amt = 7.9
        self.sim_credit_avg = 47640
        self.sim_credit_risk = 36
        self.sim_credit_trend = "#F04438"
        
        self.sim_net_txs = 737
        self.sim_net_amt = 4.1
        self.sim_net_avg = 55688
        self.sim_net_risk = 72
        self.sim_net_trend = "#F04438"
        
        self.sim_paypal_txs = 147
        self.sim_paypal_amt = 1.3
        self.sim_paypal_avg = 8844
        self.sim_paypal_risk = 48
        self.sim_paypal_trend = "#32D583"
        
        self.sim_other_txs = 40
        self.sim_other_amt = 0.3
        self.sim_other_avg = 12256
        self.sim_other_risk = 18
        self.sim_other_trend = "#32D583"
        
        self.init_ui()
        
    def init_ui(self):
        master_layout = QVBoxLayout(self)
        master_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background-color: transparent; border: none;")
        
        scroll_content = QWidget()
        scroll_content.setStyleSheet(f"background-color: {COLOR_BG};")
        layout = QVBoxLayout(scroll_content)
        layout.setContentsMargins(30, 20, 30, 25)
        layout.setSpacing(20)
        
        # ---------------------------------------------------------
        # TOP PANEL HEADER (TITLES + CONTROLS)
        # ---------------------------------------------------------
        header_row = QHBoxLayout()
        header_text_v = QVBoxLayout()
        header_text_v.setSpacing(2)
        
        lbl_h_title = QLabel("Payment Methods")
        lbl_h_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #172B4D;")
        lbl_h_desc = QLabel("Transaction analysis by payment method")
        lbl_h_desc.setStyleSheet("font-size: 12px; color: #667085;")
        header_text_v.addWidget(lbl_h_title)
        header_text_v.addWidget(lbl_h_desc)
        header_row.addLayout(header_text_v)
        header_row.addStretch()
        
        # Date & Action buttons
        btn_date = QPushButton("📅  01 Mar 2026 - 22 Aug 2026")
        btn_date.setStyleSheet("background-color: #FFFFFF; border: 1px solid #E4E7EC; border-radius: 6px; padding: 6px 12px; font-size: 12px; color: #172B4D;")
        
        self.btn_config_sim = QPushButton("⚙️  Configure Simulation Data")
        self.btn_config_sim.setCursor(Qt.PointingHandCursor)
        self.btn_config_sim.setStyleSheet("background-color: #155EEF; border: 1px solid #155EEF; border-radius: 6px; padding: 6px 12px; font-size: 12px; color: #FFFFFF; font-weight: bold;")
        self.btn_config_sim.clicked.connect(self.handle_config_simulation)
        
        btn_filter = QPushButton("🎛️  Filter")
        btn_filter.setStyleSheet("background-color: #FFFFFF; border: 1px solid #E4E7EC; border-radius: 6px; padding: 6px 12px; font-size: 12px; color: #172B4D;")
        
        header_row.addWidget(btn_date)
        header_row.addWidget(self.btn_config_sim)
        header_row.addWidget(btn_filter)
        layout.addLayout(header_row)
        
        # ---------------------------------------------------------
        # SECTION 1: TOP STATS GRID (5 CARDS)
        # ---------------------------------------------------------
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(15)
        
        kpi_items = [
            ("Total Transactions", "18,421", "100% of total", "🔄", "background-color: #F0F5FF; color: #175CD3;"),
            ("Total Amount", "₹84.6 Cr", "100% of total", "₹", "background-color: #ECFDF3; color: #027A48;"),
            ("Avg. Transaction Amount", "₹45,942", "Across all methods", "📊", "background-color: #F9F5FF; color: #6941C6;"),
            ("Highest Share", "UPI", "62.0% of total", "⭐", "background-color: #FFFAEB; color: #B54708;"),
            ("Highest Risk Method", "Net Banking", "Risk Score: 72/100", "🛡️", "background-color: #FEF3F2; color: #D92D20;")
        ]
        
        self.kpi_value_labels = {}
        self.kpi_subtext_labels = {}
        
        for name, value, trend, emoji, style in kpi_items:
            card = QFrame()
            card.setProperty("class", "Card")
            card.setStyleSheet("background-color: #FFFFFF; border: 1px solid #E4E7EC; border-radius: 8px;")
            card_lay = QVBoxLayout(card)
            card_lay.setContentsMargins(15, 15, 15, 15)
            card_lay.setSpacing(6)
            
            h_lay = QHBoxLayout()
            h_lay.setSpacing(8)
            lbl_icon = QLabel(emoji)
            lbl_icon.setFixedSize(26, 26)
            lbl_icon.setAlignment(Qt.AlignCenter)
            lbl_icon.setStyleSheet(f"border-radius: 13px; font-size: 14px; {style}")
            
            lbl_title = QLabel(name)
            lbl_title.setStyleSheet("font-size: 11px; font-weight: bold; color: #667085;")
            h_lay.addWidget(lbl_icon)
            h_lay.addWidget(lbl_title)
            h_lay.addStretch()
            card_lay.addLayout(h_lay)
            
            lbl_val = QLabel(value)
            lbl_val.setStyleSheet("font-size: 22px; font-weight: bold; color: #172B4D;")
            card_lay.addWidget(lbl_val)
            self.kpi_value_labels[name] = lbl_val
            
            lbl_trend = QLabel(trend)
            lbl_trend.setStyleSheet("font-size: 10px; color: #667085;")
            card_lay.addWidget(lbl_trend)
            self.kpi_subtext_labels[name] = lbl_trend
            
            kpi_row.addWidget(card)
            
        layout.addLayout(kpi_row)
        
        # ---------------------------------------------------------
        # SECTION 2: CHARTS ROW (3 COLUMNS)
        # ---------------------------------------------------------
        charts_row = QHBoxLayout()
        charts_row.setSpacing(15)
        
        # Donut Chart Card (Share Volume)
        donut_card = QFrame()
        donut_card.setProperty("class", "Card")
        donut_card.setStyleSheet("background-color: #FFFFFF; border: 1px solid #E4E7EC; border-radius: 8px;")
        donut_lay = QVBoxLayout(donut_card)
        donut_lay.setContentsMargins(15, 15, 15, 15)
        
        lbl_d_title = QLabel("Transaction Share by Payment Method")
        lbl_d_title.setStyleSheet("font-size: 12px; font-weight: bold; color: #172B4D;")
        donut_lay.addWidget(lbl_d_title)
        
        self.donut_canvas = MChartCanvas(self, width=4.0, height=3.5)
        donut_lay.addWidget(self.donut_canvas)
        charts_row.addWidget(donut_card, 5)
        
        # Bar Chart 1 (Amount Volume)
        bar1_card = QFrame()
        bar1_card.setProperty("class", "Card")
        bar1_card.setStyleSheet("background-color: #FFFFFF; border: 1px solid #E4E7EC; border-radius: 8px;")
        bar1_lay = QVBoxLayout(bar1_card)
        bar1_lay.setContentsMargins(15, 15, 15, 15)
        
        lbl_b1_title = QLabel("Transaction Amount by Payment Method    (In Crores)")
        lbl_b1_title.setStyleSheet("font-size: 12px; font-weight: bold; color: #172B4D;")
        bar1_lay.addWidget(lbl_b1_title)
        
        self.bar1_canvas = MChartCanvas(self, width=4.0, height=3.5)
        bar1_lay.addWidget(self.bar1_canvas)
        charts_row.addWidget(bar1_card, 4)
        
        # Bar Chart 2 (Average Ticket Size)
        bar2_card = QFrame()
        bar2_card.setProperty("class", "Card")
        bar2_card.setStyleSheet("background-color: #FFFFFF; border: 1px solid #E4E7EC; border-radius: 8px;")
        bar2_lay = QVBoxLayout(bar2_card)
        bar2_lay.setContentsMargins(15, 15, 15, 15)
        
        lbl_b2_title = QLabel("Average Transaction Amount by Method    (In ₹)")
        lbl_b2_title.setStyleSheet("font-size: 12px; font-weight: bold; color: #172B4D;")
        bar2_lay.addWidget(lbl_b2_title)
        
        self.bar2_canvas = MChartCanvas(self, width=4.0, height=3.5)
        bar2_lay.addWidget(self.bar2_canvas)
        charts_row.addWidget(bar2_card, 4)
        
        layout.addLayout(charts_row)
        
        # ---------------------------------------------------------
        # SECTION 3: RISK PROGRESS & DETAILED INSIGHTS TABLE ROW
        # ---------------------------------------------------------
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(15)
        
        # Left Side: Risk progress bars card
        risk_prog_card = QFrame()
        risk_prog_card.setProperty("class", "Card")
        risk_prog_card.setStyleSheet("background-color: #FFFFFF; border: 1px solid #E4E7EC; border-radius: 8px;")
        risk_lay = QVBoxLayout(risk_prog_card)
        risk_lay.setContentsMargins(15, 15, 15, 15)
        
        lbl_rp_title = QLabel("Risk Score by Payment Method")
        lbl_rp_title.setStyleSheet("font-size: 12px; font-weight: bold; color: #172B4D;")
        lbl_rp_sub = QLabel("(Higher score = higher risk)")
        lbl_rp_sub.setStyleSheet("font-size: 10px; color: #667085; margin-bottom: 10px;")
        risk_lay.addWidget(lbl_rp_title)
        risk_lay.addWidget(lbl_rp_sub)
        
        self.risk_progress_container = QVBoxLayout()
        self.risk_progress_container.setSpacing(12)
        risk_lay.addLayout(self.risk_progress_container)
        risk_lay.addStretch()
        bottom_row.addWidget(risk_prog_card, 4)
        
        # Right Side: Table Insights
        tbl_card = QFrame()
        tbl_card.setProperty("class", "Card")
        tbl_card.setStyleSheet("background-color: #FFFFFF; border: 1px solid #E4E7EC; border-radius: 8px;")
        tbl_lay = QVBoxLayout(tbl_card)
        tbl_lay.setContentsMargins(15, 15, 15, 15)
        
        lbl_t_title = QLabel("Payment Method Insights")
        lbl_t_title.setStyleSheet("font-size: 12px; font-weight: bold; color: #172B4D; margin-bottom: 12px;")
        tbl_lay.addWidget(lbl_t_title)
        
        self.tbl_insights = QTableWidget()
        self.tbl_insights.setColumnCount(7)
        self.tbl_insights.setRowCount(6)
        self.tbl_insights.setHorizontalHeaderLabels([
            "Payment Method", "Transactions", "Amount (₹)", "Share (%)", "Avg. Amount (₹)", "Risk Score", "Trend"
        ])
        self.tbl_insights.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_insights.verticalHeader().setVisible(False)
        self.tbl_insights.setStyleSheet("QTableWidget { font-size: 11px; border: none; }")
        
        tbl_lay.addWidget(self.tbl_insights)
        bottom_row.addWidget(tbl_card, 6)
        
        layout.addLayout(bottom_row)
        
        # Bottom Copyright footer info line
        lbl_footer_info = QLabel("All amounts are in INR  |  Data is updated as of 22 Aug 2026, 04:40 PM  |  🔄 Refresh Data")
        lbl_footer_info.setAlignment(Qt.AlignCenter)
        lbl_footer_info.setStyleSheet("font-size: 11px; color: #98A2B3;")
        layout.addWidget(lbl_footer_info)
        
        scroll.setWidget(scroll_content)
        master_layout.addWidget(scroll)
        
    def load_data(self):
        # 1. Fetch real payment methods metrics
        data = self.api.get_payment_methods()
        if data:
            dist = data.get("distribution", {})
            risks = data.get("risk_levels", {})
            details = data.get("details", {})
            
            # Map UPI
            upi_det = details.get("UPI", {})
            self.sim_upi_txs = upi_det.get("count", 0)
            self.sim_upi_amt = upi_det.get("volume", 0.0)
            self.sim_upi_avg = upi_det.get("avg_amount", 0.0)
            self.sim_upi_risk = risks.get("UPI", 0)
            
            # Map Debit Card
            dc_det = details.get("Debit Card", {})
            self.sim_debit_txs = dc_det.get("count", 0)
            self.sim_debit_amt = dc_det.get("volume", 0.0)
            self.sim_debit_avg = dc_det.get("avg_amount", 0.0)
            self.sim_debit_risk = risks.get("Debit Card", 0)
            
            # Map Credit Card
            cc_det = details.get("Credit Card", {})
            self.sim_credit_txs = cc_det.get("count", 0)
            self.sim_credit_amt = cc_det.get("volume", 0.0)
            self.sim_credit_avg = cc_det.get("avg_amount", 0.0)
            self.sim_credit_risk = risks.get("Credit Card", 0)
            
            # Map Net Banking
            nb_det = details.get("Net Banking", {})
            self.sim_net_txs = nb_det.get("count", 0)
            self.sim_net_amt = nb_det.get("volume", 0.0)
            self.sim_net_avg = nb_det.get("avg_amount", 0.0)
            self.sim_net_risk = risks.get("Net Banking", 0)
            
            # Map PayPal
            pp_det = details.get("PayPal", {})
            self.sim_paypal_txs = pp_det.get("count", 0)
            self.sim_paypal_amt = pp_det.get("volume", 0.0)
            self.sim_paypal_avg = pp_det.get("avg_amount", 0.0)
            self.sim_paypal_risk = risks.get("PayPal", 0)
            
            # Map Other
            self.sim_other_txs = 0
            self.sim_other_amt = 0.0
            self.sim_other_avg = 0.0
            self.sim_other_risk = 0
            
        # 0. Recalculate global indicators mathematically
        tx_list = [self.sim_upi_txs, self.sim_debit_txs, self.sim_credit_txs, self.sim_net_txs, self.sim_paypal_txs, self.sim_other_txs]
        amt_list = [self.sim_upi_amt, self.sim_debit_amt, self.sim_credit_amt, self.sim_net_amt, self.sim_paypal_amt, self.sim_other_amt]
        avg_list = [self.sim_upi_avg, self.sim_debit_avg, self.sim_credit_avg, self.sim_net_avg, self.sim_paypal_avg, self.sim_other_avg]
        risk_list = [self.sim_upi_risk, self.sim_debit_risk, self.sim_credit_risk, self.sim_net_risk, self.sim_paypal_risk, self.sim_other_risk]
        
        total_txs = sum(tx_list)
        total_amt = sum(amt_list) # In INR!
        
        # Calculate weighted average transaction ticket
        avg_tx_amt = sum(avg_list) / len(avg_list) if avg_list else 0
        
        # Determine highest share payment channel
        names = ["UPI", "Debit Card", "Credit Card", "Net Banking", "PayPal", "Other"]
        max_idx = tx_list.index(max(tx_list)) if tx_list else 0
        highest_share_name = names[max_idx]
        highest_share_pct = (tx_list[max_idx] / total_txs * 100) if total_txs else 0
        
        # Determine highest risk channel
        max_risk_idx = risk_list.index(max(risk_list)) if risk_list else 0
        highest_risk_name = names[max_risk_idx]
        highest_risk_score = risk_list[max_risk_idx]
        
        self.kpi_value_labels["Total Transactions"].setText(f"{total_txs:,}")
        self.kpi_value_labels["Total Amount"].setText(format_money(total_amt))
        self.kpi_value_labels["Avg. Transaction Amount"].setText(f"₹{int(avg_tx_amt):,}")
        self.kpi_value_labels["Highest Share"].setText(highest_share_name)
        self.kpi_subtext_labels["Highest Share"].setText(f"{highest_share_pct:.1f}% of total")
        self.kpi_value_labels["Highest Risk Method"].setText(highest_risk_name)
        self.kpi_subtext_labels["Highest Risk Method"].setText(f"Risk Score: {highest_risk_score}/100")
        
        # 1. Redraw Donut Chart (Transaction Share)
        self.donut_canvas.clear()
        ax_d = self.donut_canvas.ax
        colors_d = ["#155EEF", "#32D583", "#F79009", "#F04438", "#9B51E0", "#E4E7EC"]
        
        self.donut_canvas.fig.subplots_adjust(left=0.02, right=0.42, top=0.9, bottom=0.1)
        
        safe_tx_list = tx_list if sum(tx_list) > 0 else [1, 0, 0, 0, 0, 0]
        wedges, texts = ax_d.pie(
            safe_tx_list, startangle=90, colors=colors_d,
            wedgeprops=dict(width=0.25, edgecolor='w')
        )
        ax_d.text(0, 0, f"{total_txs:,}\nTotal Tx", ha='center', va='center', fontsize=9, weight='bold', color="#172B4D")
        
        legend_labels = [f"{names[i]}  {tx_list[i]/total_txs*100 if total_txs else 0:.1f}% ({tx_list[i]:,})" for i in range(len(names))]
        ax_d.legend(wedges, legend_labels, loc="center left", bbox_to_anchor=(1.02, 0.5), frameon=False, fontsize=7)
        ax_d.axis('equal')
        self.donut_canvas.draw()
        
        # 2. Redraw Horizontal Bar Chart 1 (Amount Volume in Crores/Lakhs)
        self.bar1_canvas.clear()
        ax_b1 = self.bar1_canvas.ax
        y_pos = range(len(names))
        
        self.bar1_canvas.fig.subplots_adjust(left=0.28, right=0.80, top=0.9, bottom=0.15)
        
        # reverse the lists so highest is plotted at top
        r_names = list(reversed(names))
        r_amt_list = list(reversed(amt_list))
        r_colors = list(reversed(colors_d))
        
        max_val = max(amt_list) if amt_list else 0
        if max_val >= 10000000:
            divisor = 10000000.0
            unit_suffix = "Cr"
        elif max_val >= 100000:
            divisor = 100000.0
            unit_suffix = "L"
        elif max_val >= 1000:
            divisor = 1000.0
            unit_suffix = "K"
        else:
            divisor = 1.0
            unit_suffix = ""
            
        scaled_r_amt_list = [x / divisor for x in r_amt_list]
        
        bars1 = ax_b1.barh(y_pos, scaled_r_amt_list, color=r_colors, height=0.45, zorder=3)
        ax_b1.set_yticks(y_pos)
        ax_b1.set_yticklabels(r_names, fontsize=8, color="#667085")
        
        for bar in bars1:
            width = bar.get_width()
            ax_b1.text(width + (max(scaled_r_amt_list)*0.02 if scaled_r_amt_list else 1.0), 
                       bar.get_y() + bar.get_height()/2, 
                       f"₹{width:.2f} {unit_suffix}" if unit_suffix else f"₹{width:,.0f}", 
                       ha='left', va='center', fontsize=7, color="#172B4D", weight='bold')
            
        ax_b1.set_xlim(0, max(scaled_r_amt_list) * 1.25 if scaled_r_amt_list else 10.0)
        self.bar1_canvas.format_ax("")
        ax_b1.grid(True, linestyle='--', alpha=0.3, color=COLOR_BORDER)
        self.bar1_canvas.draw()
        
        # 3. Redraw Horizontal Bar Chart 2 (Average Transaction Amount in ₹)
        self.bar2_canvas.clear()
        ax_b2 = self.bar2_canvas.ax
        r_avg_list = list(reversed(avg_list))
        
        self.bar2_canvas.fig.subplots_adjust(left=0.28, right=0.80, top=0.9, bottom=0.15)
        
        bars2 = ax_b2.barh(y_pos, r_avg_list, color="#6941C6", height=0.45, zorder=3)
        ax_b2.set_yticks(y_pos)
        ax_b2.set_yticklabels(r_names, fontsize=8, color="#667085")
        
        for bar in bars2:
            width = bar.get_width()
            ax_b2.text(width + 1000, bar.get_y() + bar.get_height()/2, f"₹{int(width):,}", ha='left', va='center', fontsize=7, color="#172B4D", weight='bold')
            
        ax_b2.set_xlim(0, max(avg_list) * 1.25 if avg_list else 60000)
        self.bar2_canvas.format_ax("")
        ax_b2.grid(True, linestyle='--', alpha=0.3, color=COLOR_BORDER)
        self.bar2_canvas.draw()
        
        # 4. Redraw Risk Progress Bar widget indicators on Left column
        # Clear container layouts
        for i in reversed(range(self.risk_progress_container.count())):
            widget = self.risk_progress_container.itemAt(i).widget()
            if widget:
                widget.deleteLater()
                
        # Sort methods by risk score descending
        sorted_pairs = sorted(zip(names, risk_list), key=lambda x: x[1], reverse=True)
        for m_name, score in sorted_pairs:
            row = QHBoxLayout()
            lbl_m = QLabel(m_name)
            lbl_m.setFixedWidth(90)
            lbl_m.setStyleSheet("font-size: 11px; font-weight: bold; color: #172B4D;")
            
            # Draw linear colored indicator line using QProgressBar
            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setValue(score)
            bar.setFixedHeight(8)
            bar.setTextVisible(False)
            
            # Determine color theme
            color_theme = "#D92D20" if score>=70 else ("#F79009" if score>=50 else ("#EAAA08" if score>=30 else "#32D583"))
            bar.setStyleSheet(f"""
                QProgressBar {{
                    border: none;
                    background-color: #F2F4F7;
                    border-radius: 4px;
                }}
                QProgressBar::chunk {{
                    background-color: {color_theme};
                    border-radius: 4px;
                }}
            """)
            
            lbl_score = QLabel(f"{score}/100")
            lbl_score.setFixedWidth(50)
            lbl_score.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            lbl_score.setStyleSheet("font-size: 11px; font-weight: bold; color: #667085;")
            
            row.addWidget(lbl_m)
            row.addWidget(bar)
            row.addWidget(lbl_score)
            
            # Wrap layout inside a QFrame
            row_frame = QWidget()
            row_frame.setLayout(row)
            self.risk_progress_container.addWidget(row_frame)
            
        # 5. Populate Payment Method Insights Table Grid
        self.tbl_insights.clearContents()
        for row, n in enumerate(names):
            txs = tx_list[row]
            amt = amt_list[row]
            share_pct = (txs / total_txs * 100) if total_txs else 0
            avg_val = avg_list[row]
            r_score = risk_list[row]
            trend_col = self.sim_upi_trend if row in [0, 1, 4, 5] else "#F04438"
            
            self.tbl_insights.setItem(row, 0, QTableWidgetItem(n))
            self.tbl_insights.setItem(row, 1, QTableWidgetItem(f"{txs:,}"))
            self.tbl_insights.setItem(row, 2, QTableWidgetItem(f"₹{amt:.1f} Cr"))
            self.tbl_insights.setItem(row, 3, QTableWidgetItem(f"{share_pct:.1f}%"))
            self.tbl_insights.setItem(row, 4, QTableWidgetItem(f"₹{int(avg_val):,}"))
            
            # Risk score badge
            risk_style = "critical" if r_score>=70 else ("high" if r_score>=50 else "safe")
            self.tbl_insights.setCellWidget(row, 5, TableBadgeLabel(f"{r_score}/100", risk_style))
            
            # Trend sparkline drawing
            spark = SparklineWidget(trend_col)
            self.tbl_insights.setCellWidget(row, 6, spark)
            
    def handle_config_simulation(self):
        d = QDialog(self)
        d.setWindowTitle("Configure Payment Simulation Parameters")
        d.setFixedSize(520, 500)
        d.setStyleSheet(GLOBAL_STYLE)
        
        layout = QVBoxLayout(d)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)
        
        lbl_title = QLabel("⚙️ Configure Presentation Payment Data")
        lbl_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #172B4D;")
        layout.addWidget(lbl_title)
        
        lbl_sub = QLabel("Modify volumes, amounts and vulnerability coefficients for payment aggregates in real-time.")
        lbl_sub.setStyleSheet("font-size: 11px; color: #667085;")
        layout.addWidget(lbl_sub)
        
        tab_widget = QTabWidget()
        logo_path = os.path.join(os.path.dirname(__file__), "logo.png")
        tab_icon = QIcon(logo_path)
        
        # Tab 1: High-Volume Channels (UPI, Debit, Credit)
        tab1 = QWidget()
        lay1 = QGridLayout(tab1)
        lay1.setSpacing(10)
        
        lay1.addWidget(QLabel("Channel"), 0, 0)
        lay1.addWidget(QLabel("Transactions"), 0, 1)
        lay1.addWidget(QLabel("Amount (Cr)"), 0, 2)
        lay1.addWidget(QLabel("Risk Score"), 0, 3)
        
        # UPI
        lay1.addWidget(QLabel("UPI:"), 1, 0)
        txt_upi_tx = QLineEdit(str(self.sim_upi_txs))
        txt_upi_am = QLineEdit(str(self.sim_upi_amt))
        txt_upi_ri = QLineEdit(str(self.sim_upi_risk))
        lay1.addWidget(txt_upi_tx, 1, 1)
        lay1.addWidget(txt_upi_am, 1, 2)
        lay1.addWidget(txt_upi_ri, 1, 3)
        
        # Debit Card
        lay1.addWidget(QLabel("Debit Card:"), 2, 0)
        txt_deb_tx = QLineEdit(str(self.sim_debit_txs))
        txt_deb_am = QLineEdit(str(self.sim_debit_amt))
        txt_deb_ri = QLineEdit(str(self.sim_debit_risk))
        lay1.addWidget(txt_deb_tx, 2, 1)
        lay1.addWidget(txt_deb_am, 2, 2)
        lay1.addWidget(txt_deb_ri, 2, 3)
        
        # Credit Card
        lay1.addWidget(QLabel("Credit Card:"), 3, 0)
        txt_cre_tx = QLineEdit(str(self.sim_credit_txs))
        txt_cre_am = QLineEdit(str(self.sim_credit_amt))
        txt_cre_ri = QLineEdit(str(self.sim_credit_risk))
        lay1.addWidget(txt_cre_tx, 3, 1)
        lay1.addWidget(txt_cre_am, 3, 2)
        lay1.addWidget(txt_cre_ri, 3, 3)
        
        tab_widget.addTab(tab1, tab_icon, "Main Channels")
        
        # Tab 2: Other Channels (Net Banking, PayPal, Other)
        tab2 = QWidget()
        lay2 = QGridLayout(tab2)
        lay2.setSpacing(10)
        
        lay2.addWidget(QLabel("Channel"), 0, 0)
        lay2.addWidget(QLabel("Transactions"), 0, 1)
        lay2.addWidget(QLabel("Amount (Cr)"), 0, 2)
        lay2.addWidget(QLabel("Risk Score"), 0, 3)
        
        # Net Banking
        lay2.addWidget(QLabel("Net Banking:"), 1, 0)
        txt_net_tx = QLineEdit(str(self.sim_net_txs))
        txt_net_am = QLineEdit(str(self.sim_net_amt))
        txt_net_ri = QLineEdit(str(self.sim_net_risk))
        lay2.addWidget(txt_net_tx, 1, 1)
        lay2.addWidget(txt_net_am, 1, 2)
        lay2.addWidget(txt_net_ri, 1, 3)
        
        # PayPal
        lay2.addWidget(QLabel("PayPal:"), 2, 0)
        txt_pay_tx = QLineEdit(str(self.sim_paypal_txs))
        txt_pay_am = QLineEdit(str(self.sim_paypal_amt))
        txt_pay_ri = QLineEdit(str(self.sim_paypal_risk))
        lay2.addWidget(txt_pay_tx, 2, 1)
        lay2.addWidget(txt_pay_am, 2, 2)
        lay2.addWidget(txt_pay_ri, 2, 3)
        
        # Other
        lay2.addWidget(QLabel("Other:"), 3, 0)
        txt_oth_tx = QLineEdit(str(self.sim_other_txs))
        txt_oth_am = QLineEdit(str(self.sim_other_amt))
        txt_oth_ri = QLineEdit(str(self.sim_other_risk))
        lay2.addWidget(txt_oth_tx, 3, 1)
        lay2.addWidget(txt_oth_am, 3, 2)
        lay2.addWidget(txt_oth_ri, 3, 3)
        
        tab_widget.addTab(tab2, tab_icon, "Other Channels")
        
        layout.addWidget(tab_widget)
        
        lbl_err = QLabel("")
        lbl_err.setStyleSheet("color: #D92D20; font-size: 11px; font-weight: bold;")
        layout.addWidget(lbl_err)
        
        # Buttons layout
        btn_lay = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setProperty("class", "SecondaryButton")
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.clicked.connect(d.reject)
        
        btn_save = QPushButton("Apply Simulation Changes")
        btn_save.setProperty("class", "PrimaryButton")
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.setStyleSheet("background-color: #155EEF; color: #FFFFFF;")
        
        def save_payment_sim():
            try:
                # Read all inputs
                upi_t = int(txt_upi_tx.text().strip())
                upi_a = float(txt_upi_am.text().strip())
                upi_r = int(txt_upi_ri.text().strip())
                
                deb_t = int(txt_deb_tx.text().strip())
                deb_a = float(txt_deb_am.text().strip())
                deb_r = int(txt_deb_ri.text().strip())
                
                cre_t = int(txt_cre_tx.text().strip())
                cre_a = float(txt_cre_am.text().strip())
                cre_r = int(txt_cre_ri.text().strip())
                
                net_t = int(txt_net_tx.text().strip())
                net_a = float(txt_net_am.text().strip())
                net_r = int(txt_net_ri.text().strip())
                
                pay_t = int(txt_pay_tx.text().strip())
                pay_a = float(txt_pay_am.text().strip())
                pay_r = int(txt_pay_ri.text().strip())
                
                oth_t = int(txt_oth_tx.text().strip())
                oth_a = float(txt_oth_am.text().strip())
                oth_r = int(txt_oth_ri.text().strip())
                
                inputs = [upi_t, upi_a, upi_r, deb_t, deb_a, deb_r, cre_t, cre_a, cre_r, net_t, net_a, net_r, pay_t, pay_a, pay_r, oth_t, oth_a, oth_r]
                if any(x < 0 for x in inputs):
                    lbl_err.setText("Parameters cannot contain negative values.")
                    return
                    
                # Risk score constraint
                if any(x > 100 for x in [upi_r, deb_r, cre_r, net_r, pay_r, oth_r]):
                    lbl_err.setText("Risk scores must be between 0 and 100.")
                    return
                    
                # Update attributes
                self.sim_upi_txs = upi_t
                self.sim_upi_amt = upi_a
                self.sim_upi_risk = upi_r
                
                self.sim_debit_txs = deb_t
                self.sim_debit_amt = deb_a
                self.sim_debit_risk = deb_r
                
                self.sim_credit_txs = cre_t
                self.sim_credit_amt = cre_a
                self.sim_credit_risk = cre_r
                
                self.sim_net_txs = net_t
                self.sim_net_amt = net_a
                self.sim_net_risk = net_r
                
                self.sim_paypal_txs = pay_t
                self.sim_paypal_amt = pay_a
                self.sim_paypal_risk = pay_r
                
                self.sim_other_txs = oth_t
                self.sim_other_amt = oth_a
                self.sim_other_risk = oth_r
                
                # Reload view
                self.load_data()
                d.accept()
            except ValueError:
                lbl_err.setText("Please insert valid numbers into the parameter fields.")
                
        btn_save.clicked.connect(save_payment_sim)
        btn_lay.addWidget(btn_cancel)
        btn_lay.addWidget(btn_save)
        layout.addLayout(btn_lay)
        
        d.exec()


# ---------------------------------------------------------
# VIEW 9: AI RISK ANALYSIS REDIRECT
# ---------------------------------------------------------
class AiRiskAnalysisView(QWidget):
    def __init__(self, api: ApiClient, main_window: MainWindow):
        super().__init__()
        self.api = api
        self.main_window = main_window
        self.account_id = "ACC-10293"
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(20)
        
        card = QFrame()
        card.setProperty("class", "Card")
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(25, 25, 25, 25)
        c_layout.setAlignment(Qt.AlignCenter)
        
        lbl_msg = QLabel("💡 Account Explainable AI (SHAP) View has been integrated directly into the Investigation Console.")
        lbl_msg.setStyleSheet(f"font-size: 15px; font-weight: bold; color: {COLOR_TEXT_PRIMARY};")
        lbl_msg.setAlignment(Qt.AlignCenter)
        c_layout.addWidget(lbl_msg)
        
        btn = QPushButton("Go to Account Investigation Console (ACC-10293)")
        btn.setProperty("class", "PrimaryButton")
        btn.setStyleSheet("margin-top: 15px;")
        btn.clicked.connect(lambda: self.main_window.switch_content_page(5))
        c_layout.addWidget(btn)
        
        layout.addWidget(card)
        layout.addStretch()
        
    def set_account(self, account_id):
        self.account_id = account_id
        
    def load_data(self):
        pass


# ---------------------------------------------------------
# VIEW 10: REPORTS REDIRECT
# ---------------------------------------------------------
class InvestigationReportsView(QWidget):
    def __init__(self, api: ApiClient, main_window: MainWindow):
        super().__init__()
        self.api = api
        self.main_window = main_window
        self.account_id = "ACC-10293"
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(20)
        
        card = QFrame()
        card.setProperty("class", "Card")
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(25, 25, 25, 25)
        c_layout.setAlignment(Qt.AlignCenter)
        
        lbl_msg = QLabel("💡 PDF Export and Reports are accessible inside the Investigation Console under 'Investigation Report Suite'.")
        lbl_msg.setStyleSheet(f"font-size: 15px; font-weight: bold; color: {COLOR_TEXT_PRIMARY};")
        lbl_msg.setAlignment(Qt.AlignCenter)
        c_layout.addWidget(lbl_msg)
        
        btn = QPushButton("Go to Reports Tab (ACC-10293)")
        btn.setProperty("class", "PrimaryButton")
        btn.setStyleSheet("margin-top: 15px;")
        btn.clicked.connect(lambda: self.main_window.switch_content_page(5))
        c_layout.addWidget(btn)
        
        layout.addWidget(card)
        layout.addStretch()
        
    def set_account(self, account_id):
        self.account_id = account_id
        
    def load_data(self):
        pass


# ---------------------------------------------------------
# VIEW 11: SETTINGS VIEW
# ---------------------------------------------------------
class SettingsView(QWidget):
    def __init__(self, api: ApiClient, main_window: MainWindow):
        super().__init__()
        self.api = api
        self.main_window = main_window
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(20)
        
        card = QFrame()
        card.setProperty("class", "Card")
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(25, 25, 25, 25)
        c_layout.setSpacing(12)
        
        lbl_title = QLabel("⚙️ SYSTEM CONFIGURATION CONTROLS")
        lbl_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #172B4D; margin-bottom: 10px;")
        c_layout.addWidget(lbl_title)
        
        self.lbl_profile = QLabel("Profile: Lead Compliance Auditor (Terminal 4)")
        self.lbl_sec = QLabel("Security Status: Enabled (AES-256 local keystore)")
        self.lbl_model = QLabel("Model Engine: XGBoost Classifier + Isolation Forest Outlier Core")
        self.lbl_dataset = QLabel("Dataset Profile: 12,450 accounts in active tracking registry")
        self.lbl_api = QLabel("API Server: http://127.0.0.1:8000")
        self.lbl_db = QLabel("Database Connection: Supabase Connected (Sandbox mode overrides active)")
        self.lbl_ver = QLabel("Application Engine Version: MuleGuard Desktop 1.0.0 Stable")
        
        for lbl in [self.lbl_profile, self.lbl_sec, self.lbl_model, self.lbl_dataset, self.lbl_api, self.lbl_db, self.lbl_ver]:
            lbl.setStyleSheet(f"font-size: 13px; color: {COLOR_TEXT_PRIMARY}; border-bottom: 1px solid {COLOR_BORDER}; padding-bottom: 8px; padding-top: 4px;")
            c_layout.addWidget(lbl)
            
        c_layout.addStretch()
        layout.addWidget(card)
        
    def load_data(self):
        # Update settings labels with actual connection status and counts!
        is_live = not self.api.local_mode
        self.lbl_db.setText(f"Database Connection: Supabase Connected ({'Live Database Mode' if is_live else 'Sandbox mode overrides active'})")
        
        accounts_cnt = 0
        if is_live:
            try:
                res = self.api.get_accounts(limit=1)
                accounts_cnt = res.get("total_count", len(res.get("accounts", [])))
            except Exception:
                pass
        
        if accounts_cnt == 0:
            accounts_cnt = len(self.api.local_accounts) if self.api.local_accounts else 102
            
        self.lbl_dataset.setText(f"Dataset Profile: {accounts_cnt:,} accounts in active tracking registry")


# ---------------------------------------------------------
# APPLICATION ENTRYPOINT
# ---------------------------------------------------------
def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(GLOBAL_STYLE)
    
    api_client = ApiClient()
    
    win = MainWindow(api_client)
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
