"""
Script to safely integrate Phase 4 views into frontend/app.py.
Adds:
- QComboBox to imports
- get_prioritized_alerts, get_alert_explanation, get_graph_typologies, get_investigator_cases, get_case_detail to ApiClient
- Navigation entries for Alert Prioritization (10) and Case Dossiers (11)
- AlertPrioritizationView and CaseDossiersView classes
"""

import os
import shutil

APP_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "frontend", "app.py"))
BACKUP_PATH = APP_PATH + ".bak"

print(f"Target file: {APP_PATH}")

with open(APP_PATH, "r", encoding="utf-8") as f:
    content = f.read()

# Make backup
if not os.path.exists(BACKUP_PATH):
    shutil.copyfile(APP_PATH, BACKUP_PATH)
    print(f"Created backup at {BACKUP_PATH}")

# 1. Update imports
if "QComboBox" not in content:
    content = content.replace(
        "    QDialog, QMessageBox, QCheckBox, QFrame, QScrollArea, QSplitter, QFormLayout, QProgressBar\n)",
        "    QDialog, QMessageBox, QCheckBox, QFrame, QScrollArea, QSplitter, QFormLayout, QProgressBar, QComboBox\n)"
    )
    print("Added QComboBox to imports.")

# 2. Add ApiClient methods
api_methods = '''
    def get_prioritized_alerts(self, budget=500, tier="All"):
        if not self.local_mode:
            try:
                params = {"budget": budget, "tier": tier}
                r = requests.get(f"{self.base_url}/api/v2/alerts/prioritized", params=params, timeout=2.5)
                if r.status_code == 200:
                    return r.json().get("alerts", [])
            except Exception as e:
                print(f"API prioritized alerts error: {e}")
        try:
            root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            fpath = os.path.join(root, "evaluation", "amlsim_evaluation", "phase3", "artifacts", "sample_alerts.json")
            if os.path.exists(fpath):
                with open(fpath, "r", encoding="utf-8") as f:
                    alerts = json.load(f)
                    if tier and tier.lower() != "all":
                        alerts = [a for a in alerts if str(a.get("risk_tier", "")).lower() == tier.lower()]
                    return alerts[:budget]
        except Exception as e:
            print(f"Fallback prioritized alerts error: {e}")
        return []

    def get_alert_explanation(self, tx_id):
        if not self.local_mode:
            try:
                r = requests.get(f"{self.base_url}/api/v2/alerts/{tx_id}/explanation", timeout=2.5)
                if r.status_code == 200:
                    return r.json().get("explanation", {})
            except Exception as e:
                print(f"API alert explanation error: {e}")
        try:
            root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            fpath = os.path.join(root, "evaluation", "amlsim_evaluation", "phase3", "artifacts", "sample_alerts.json")
            if os.path.exists(fpath):
                with open(fpath, "r", encoding="utf-8") as f:
                    for a in json.load(f):
                        if a.get("transaction_id") == tx_id:
                            return a
        except Exception:
            pass
        return {}

    def get_graph_typologies(self):
        if not self.local_mode:
            try:
                r = requests.get(f"{self.base_url}/api/v2/graph/typologies", timeout=2.5)
                if r.status_code == 200:
                    return r.json()
            except Exception as e:
                print(f"API graph typologies error: {e}")
        try:
            root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            fpath = os.path.join(root, "evaluation", "amlsim_evaluation", "phase3", "phase3_results.json")
            if os.path.exists(fpath):
                with open(fpath, "r", encoding="utf-8") as f:
                    d = json.load(f)
                    return {
                        "graph_summary": d.get("graph_intelligence", {}).get("graph_summary", {}),
                        "sample_patterns": d.get("graph_intelligence", {}).get("sample_patterns", [])
                    }
        except Exception:
            pass
        return {"graph_summary": {}, "sample_patterns": []}

    def get_investigator_cases(self, status="All", tier="All"):
        if not self.local_mode:
            try:
                params = {"status": status, "tier": tier}
                r = requests.get(f"{self.base_url}/api/v2/cases", params=params, timeout=2.5)
                if r.status_code == 200:
                    return r.json().get("cases", [])
            except Exception as e:
                print(f"API cases error: {e}")
        cases = []
        try:
            root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            cdir = os.path.join(root, "evaluation", "amlsim_evaluation", "phase3", "artifacts", "cases")
            if os.path.exists(cdir):
                for f in sorted(os.listdir(cdir)):
                    if f.endswith(".json"):
                        with open(os.path.join(cdir, f), "r", encoding="utf-8") as jf:
                            cases.append(json.load(jf))
            if status and status.lower() != "all":
                cases = [c for c in cases if str(c.get("review_status", "")).lower() == status.lower()]
            if tier and tier.lower() != "all":
                cases = [c for c in cases if str(c.get("priority_tier", "")).lower() == tier.lower()]
        except Exception:
            pass
        return cases

    def get_case_detail(self, case_id):
        if not self.local_mode:
            try:
                r = requests.get(f"{self.base_url}/api/v2/cases/{case_id}", timeout=2.5)
                if r.status_code == 200:
                    return r.json().get("case", {})
            except Exception as e:
                print(f"API case detail error: {e}")
        for c in self.get_investigator_cases():
            if c.get("case_id") == case_id:
                return c
        return {}
'''

if "def get_prioritized_alerts" not in content:
    target_str = "    def _initialize_local_mock_db(self):"
    content = content.replace(target_str, api_methods + "\n" + target_str)
    print("Added ApiClient Phase 4 methods.")

# 3. Update sidebar navigation
old_groups = '''        groups = [
            ("OVERVIEW", [("Dashboard", 0)], False),
            ("RISK MONITORING", [("Active Alerts", 1), ("Live Transactions", 2)], True),
            ("INVESTIGATION", [("Accounts", 3), ("Transactions", 4), ("Network Analysis", 5)], True),
            ("ANALYTICS", [("Fraud Analytics", 6), ("Regional Risk", 7), ("Payment Methods", 8)], True)
        ]'''

new_groups = '''        groups = [
            ("OVERVIEW", [("Dashboard", 0)], False),
            ("RISK MONITORING", [("Active Alerts", 1), ("Live Transactions", 2), ("Alert Prioritization", 10)], True),
            ("INVESTIGATION", [("Accounts", 3), ("Transactions", 4), ("Network Analysis", 5), ("Case Dossiers", 11)], True),
            ("ANALYTICS", [("Fraud Analytics", 6), ("Regional Risk", 7), ("Payment Methods", 8)], True)
        ]'''

if old_groups in content:
    content = content.replace(old_groups, new_groups)
    print("Updated sidebar groups with Alert Prioritization (10) and Case Dossiers (11).")

# 4. Update build_content_pages
old_build = '''        self.page_settings = SettingsView(self.api, self)
        self.content_stack.addWidget(self.page_settings)
        
        self.switch_content_page(0)'''

new_build = '''        self.page_settings = SettingsView(self.api, self)
        self.content_stack.addWidget(self.page_settings)
        
        self.page_prioritization = AlertPrioritizationView(self.api, self)
        self.content_stack.addWidget(self.page_prioritization)
        
        self.page_cases = CaseDossiersView(self.api, self)
        self.content_stack.addWidget(self.page_cases)
        
        self.switch_content_page(0)'''

if old_build in content:
    content = content.replace(old_build, new_build)
    print("Added page_prioritization and page_cases to content_stack.")

# 5. Update switch_content_page
old_switch = '''        categories = {
            0: "OVERVIEW", 1: "RISK MONITORING", 2: "RISK MONITORING",
            3: "INVESTIGATION", 4: "INVESTIGATION", 5: "INVESTIGATION",
            6: "ANALYTICS", 7: "ANALYTICS", 8: "ANALYTICS", 9: "SYSTEM"
        }
        titles = {
            0: "Executive Dashboard",
            1: "Real-time High-Risk Alerts",
            2: "Live Transaction Feed Stream",
            3: "Institutional Account Registry",
            4: "Ledger Transaction Search",
            5: "Mule Network Analysis",
            6: "Crime Analytics & Typologies",
            7: "Geographical Regional Risk Map",
            8: "Payment Channel Breakdown",
            9: "System Configuration & Node Health"
        }'''

new_switch = '''        categories = {
            0: "OVERVIEW", 1: "RISK MONITORING", 2: "RISK MONITORING",
            3: "INVESTIGATION", 4: "INVESTIGATION", 5: "INVESTIGATION",
            6: "ANALYTICS", 7: "ANALYTICS", 8: "ANALYTICS", 9: "SYSTEM",
            10: "RISK MONITORING", 11: "INVESTIGATION"
        }
        titles = {
            0: "Executive Dashboard",
            1: "Real-time High-Risk Alerts",
            2: "Live Transaction Feed Stream",
            3: "Institutional Account Registry",
            4: "Ledger Transaction Search",
            5: "Mule Network Analysis",
            6: "Crime Analytics & Typologies",
            7: "Geographical Regional Risk Map",
            8: "Payment Channel Breakdown",
            9: "System Configuration & Node Health",
            10: "Alert Prioritization & Grounded Explanations",
            11: "Case Dossiers & Audit Trails"
        }'''

if old_switch in content:
    content = content.replace(old_switch, new_switch)
    print("Updated switch_content_page categories and titles for 10 and 11.")

# 6. Add view classes
view_classes = '''
# ---------------------------------------------------------
# VIEW 10: ALERT PRIORITIZATION & GROUNDED EXPLANATIONS
# ---------------------------------------------------------
class AlertPrioritizationView(QWidget):
    def __init__(self, api: ApiClient, main_window: MainWindow):
        super().__init__()
        self.api = api
        self.main_window = main_window
        self.current_tier = "All"
        self.current_budget = 500
        self.selected_tx = None
        self.init_ui()
        self.load_data()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(15)

        # 1. Top KPI Row (4 Cards)
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(15)

        # Budget Card
        c1 = QFrame()
        c1.setProperty("class", "Card")
        c1.setStyleSheet("background-color: #FFFFFF; border: 1px solid #E4E7EC; border-radius: 8px;")
        l1 = QVBoxLayout(c1)
        l1.setContentsMargins(15, 12, 15, 12)
        lbl_b_title = QLabel("INVESTIGATION CAPACITY")
        lbl_b_title.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 11px; font-weight: bold;")
        self.cmb_budget = QComboBox()
        self.cmb_budget.addItems(["Top 100", "Top 250", "Top 500", "Top 1000", "Top 2500", "Top 5000"])
        self.cmb_budget.setCurrentIndex(2) # Default Top 500
        self.cmb_budget.currentIndexChanged.connect(self.on_budget_changed)
        self.cmb_budget.setStyleSheet("padding: 4px; font-size: 13px; font-weight: bold;")
        l1.addWidget(lbl_b_title)
        l1.addWidget(self.cmb_budget)
        kpi_row.addWidget(c1)

        # Efficiency Card
        c2 = QFrame()
        c2.setProperty("class", "Card")
        c2.setStyleSheet("background-color: #FFFFFF; border: 1px solid #E4E7EC; border-radius: 8px;")
        l2 = QVBoxLayout(c2)
        l2.setContentsMargins(15, 12, 15, 12)
        lbl_e_title = QLabel("TRIAGE REDUCTION")
        lbl_e_title.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 11px; font-weight: bold;")
        lbl_e_val = QLabel("99.70%")
        lbl_e_val.setStyleSheet(f"color: {COLOR_RISK_LOW}; font-size: 20px; font-weight: bold;")
        lbl_e_sub = QLabel("Volume filtered vs unranked stream")
        lbl_e_sub.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 10px;")
        l2.addWidget(lbl_e_title)
        l2.addWidget(lbl_e_val)
        l2.addWidget(lbl_e_sub)
        kpi_row.addWidget(c2)

        # Distribution Card
        c3 = QFrame()
        c3.setProperty("class", "Card")
        c3.setStyleSheet("background-color: #FFFFFF; border: 1px solid #E4E7EC; border-radius: 8px;")
        l3 = QVBoxLayout(c3)
        l3.setContentsMargins(15, 12, 15, 12)
        lbl_d_title = QLabel("PRIORITY TIERS")
        lbl_d_title.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 11px; font-weight: bold;")
        self.lbl_tier_dist = QLabel("20 Critical · 15 High · 10 Med")
        self.lbl_tier_dist.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 14px; font-weight: bold;")
        lbl_d_sub = QLabel("Threshold calibrated on validation data")
        lbl_d_sub.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 10px;")
        l3.addWidget(lbl_d_title)
        l3.addWidget(self.lbl_tier_dist)
        l3.addWidget(lbl_d_sub)
        kpi_row.addWidget(c3)

        # Baseline Card
        c4 = QFrame()
        c4.setProperty("class", "Card")
        c4.setStyleSheet("background-color: #FFFFFF; border: 1px solid #E4E7EC; border-radius: 8px;")
        l4 = QVBoxLayout(c4)
        l4.setContentsMargins(15, 12, 15, 12)
        lbl_m_title = QLabel("PRIMARY RANKING BASELINE")
        lbl_m_title.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 11px; font-weight: bold;")
        lbl_m_val = QLabel("LightGBM Probability")
        lbl_m_val.setStyleSheet(f"color: {COLOR_PRIMARY_BLUE}; font-size: 14px; font-weight: bold;")
        lbl_m_sub = QLabel("Supported by Graph + Fused Signals")
        lbl_m_sub.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 10px;")
        l4.addWidget(lbl_m_title)
        l4.addWidget(lbl_m_val)
        l4.addWidget(lbl_m_sub)
        kpi_row.addWidget(c4)

        layout.addLayout(kpi_row)

        # 2. Controls & Filter Bar
        ctrl_card = QFrame()
        ctrl_card.setProperty("class", "Card")
        ctrl_card.setStyleSheet("background-color: #FFFFFF; border: 1px solid #E4E7EC; border-radius: 8px; padding: 5px;")
        ctrl_lay = QHBoxLayout(ctrl_card)
        ctrl_lay.setContentsMargins(15, 8, 15, 8)
        ctrl_lay.setSpacing(10)

        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Filter prioritized alerts by Tx ID, Account, Currency...")
        self.txt_search.setStyleSheet("border: 1px solid #E4E7EC; border-radius: 6px; padding: 6px 12px; font-size: 12px;")
        self.txt_search.textChanged.connect(self.apply_client_filter)
        ctrl_lay.addWidget(self.txt_search, 2)

        ctrl_lay.addWidget(QLabel("Tier Filter:"))
        self.tier_buttons = {}
        for t_name in ["All", "Critical", "High", "Medium", "Low"]:
            btn = QPushButton(t_name)
            btn.setCheckable(True)
            btn.setChecked(t_name == "All")
            btn.setStyleSheet("""
                QPushButton {
                    border: 1px solid #E4E7EC;
                    border-radius: 4px;
                    padding: 5px 12px;
                    font-size: 11px;
                    font-weight: bold;
                    background-color: #FFFFFF;
                    color: #667085;
                }
                QPushButton:checked {
                    background-color: #155EEF;
                    color: #FFFFFF;
                    border-color: #155EEF;
                }
            """)
            btn.clicked.connect(lambda checked, t=t_name: self.on_tier_filter_clicked(t))
            ctrl_lay.addWidget(btn)
            self.tier_buttons[t_name] = btn

        ctrl_lay.addStretch()

        btn_refresh = QPushButton("⟳ Refresh")
        btn_refresh.setStyleSheet("background-color: #F8F9FC; border: 1px solid #E4E7EC; border-radius: 4px; padding: 5px 12px; font-size: 11px;")
        btn_refresh.clicked.connect(self.load_data)
        ctrl_lay.addWidget(btn_refresh)

        layout.addWidget(ctrl_card)

        # 3. Main Splitter: Left Table | Right Grounded Explanation Inspector
        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)

        # Left Table Widget
        self.tbl_alerts = QTableWidget()
        self.tbl_alerts.setColumnCount(8)
        self.tbl_alerts.setHorizontalHeaderLabels(["Rank", "Tx ID", "Timestamp", "Counterparties", "Amount", "Model Risk", "Priority Tier", "Action"])
        self.tbl_alerts.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_alerts.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tbl_alerts.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tbl_alerts.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.tbl_alerts.verticalHeader().setVisible(False)
        self.tbl_alerts.itemSelectionChanged.connect(self.on_table_selection_changed)
        splitter.addWidget(self.tbl_alerts)

        # Right Detail Area (Grounded Explanation Card)
        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setStyleSheet("border: none; background: transparent;")

        self.right_container = QFrame()
        self.right_container.setProperty("class", "Card")
        self.right_container.setStyleSheet("background-color: #FFFFFF; border: 1px solid #E4E7EC; border-radius: 8px;")
        self.right_layout = QVBoxLayout(self.right_container)
        self.right_layout.setContentsMargins(20, 20, 20, 20)
        self.right_layout.setSpacing(12)

        # Placeholder inside right container
        self.lbl_detail_placeholder = QLabel("Select an alert from the table to view its evidence-grounded explanation and signal provenance.")
        self.lbl_detail_placeholder.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 13px; font-style: italic;")
        self.lbl_detail_placeholder.setWordWrap(True)
        self.right_layout.addWidget(self.lbl_detail_placeholder)
        self.right_layout.addStretch()

        right_scroll.setWidget(self.right_container)
        splitter.addWidget(right_scroll)

        splitter.setSizes([680, 480])
        layout.addWidget(splitter, 1)

    def on_budget_changed(self, idx):
        budget_map = [100, 250, 500, 1000, 2500, 5000]
        self.current_budget = budget_map[idx]
        self.load_data()

    def on_tier_filter_clicked(self, tier):
        self.current_tier = tier
        for t_name, btn in self.tier_buttons.items():
            btn.setChecked(t_name == tier)
        self.load_data()

    def load_data(self):
        self.all_loaded_alerts = self.api.get_prioritized_alerts(budget=self.current_budget, tier=self.current_tier)
        self.apply_client_filter()

    def apply_client_filter(self):
        query = self.txt_search.text().strip().lower()
        if query:
            filtered = [
                a for a in self.all_loaded_alerts
                if query in a.get("transaction_id", "").lower()
                or query in a.get("sender_account", "").lower()
                or query in a.get("receiver_account", "").lower()
                or query in a.get("currency", "").lower()
            ]
        else:
            filtered = self.all_loaded_alerts

        self.rendered_alerts = filtered
        self.tbl_alerts.setRowCount(len(filtered))

        for row, a in enumerate(filtered):
            rank = a.get("risk_rank", row + 1)
            self.tbl_alerts.setItem(row, 0, QTableWidgetItem(f"#{rank}"))
            self.tbl_alerts.setItem(row, 1, QTableWidgetItem(a.get("transaction_id", "")))
            self.tbl_alerts.setItem(row, 2, QTableWidgetItem(a.get("timestamp", "")))

            counterparties = f"{a.get('sender_account', '')} ➔ {a.get('receiver_account', '')}"
            self.tbl_alerts.setItem(row, 3, QTableWidgetItem(counterparties))

            amt = a.get("amount", 0.0)
            curr = a.get("currency", "USD")
            self.tbl_alerts.setItem(row, 4, QTableWidgetItem(f"${amt:,.2f} {curr}"))

            score = a.get("model_risk_score", 0.0)
            self.tbl_alerts.setItem(row, 5, QTableWidgetItem(f"{score*100:.1f}%"))

            tier = a.get("risk_tier", "Low")
            badge = TableBadgeLabel(tier, tier.lower())
            self.tbl_alerts.setCellWidget(row, 6, badge)

            btn_inspect = QPushButton("Explain")
            btn_inspect.setStyleSheet("background-color: #155EEF; color: #FFFFFF; border-radius: 4px; padding: 3px 8px; font-size: 11px;")
            btn_inspect.clicked.connect(lambda checked, idx=row: self.select_alert_by_row(idx))
            self.tbl_alerts.setCellWidget(row, 7, btn_inspect)

        if filtered:
            self.select_alert_by_row(0)

    def on_table_selection_changed(self):
        rows = self.tbl_alerts.selectionModel().selectedRows()
        if rows:
            self.select_alert_by_row(rows[0].row())

    def select_alert_by_row(self, row_idx):
        if 0 <= row_idx < len(self.rendered_alerts):
            self.render_explanation_detail(self.rendered_alerts[row_idx])

    def render_explanation_detail(self, alert_data):
        # Clear existing layout
        while self.right_layout.count():
            item = self.right_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # Header
        h_row = QHBoxLayout()
        tx_id = alert_data.get("transaction_id", "Unknown")
        lbl_tx = QLabel(f"Alert Dossier: {tx_id}")
        lbl_tx.setStyleSheet("font-size: 16px; font-weight: bold; color: #172B4D;")
        h_row.addWidget(lbl_tx)
        h_row.addStretch()

        tier = alert_data.get("risk_tier", "Low")
        badge = TableBadgeLabel(tier, tier.lower())
        h_row.addWidget(badge)
        self.right_layout.addLayout(h_row)

        # Meta row
        score = alert_data.get("model_risk_score", 0.0)
        rank = alert_data.get("risk_rank", 1)
        amt = alert_data.get("amount", 0.0)
        curr = alert_data.get("currency", "USD")
        lbl_meta = QLabel(f"Rank #{rank} in Capacity Triage · Probability: {score*100:.1f}% · Amount: ${amt:,.2f} {curr}")
        lbl_meta.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 12px; font-weight: bold;")
        self.right_layout.addWidget(lbl_meta)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"color: {COLOR_BORDER}; margin: 4px 0px;")
        self.right_layout.addWidget(sep)

        # Human-Readable Grounded Summary
        lbl_sum_title = QLabel("GROUNDED NARRATIVE EXPLANATION")
        lbl_sum_title.setStyleSheet(f"color: {COLOR_PRIMARY_BLUE}; font-size: 11px; font-weight: bold;")
        self.right_layout.addWidget(lbl_sum_title)

        summary_text = alert_data.get("human_readable_summary", "No narrative available.")
        lbl_summary = QLabel(summary_text)
        lbl_summary.setWordWrap(True)
        lbl_summary.setStyleSheet("font-size: 12px; color: #172B4D; line-height: 18px; background-color: #F8F9FC; border: 1px solid #E4E7EC; border-radius: 6px; padding: 10px;")
        self.right_layout.addWidget(lbl_summary)

        # Multi-Source Signal Breakdown (Provenance Grounded)
        lbl_sig_title = QLabel("CONTRIBUTING SIGNAL PROVENANCE")
        lbl_sig_title.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 12px; font-weight: bold; margin-top: 8px;")
        self.right_layout.addWidget(lbl_sig_title)

        signals = alert_data.get("contributing_signals", [])
        if not signals:
            lbl_no_sig = QLabel("No discrete signals logged.")
            lbl_no_sig.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11px;")
            self.right_layout.addWidget(lbl_no_sig)
        else:
            for s in signals:
                s_box = QFrame()
                s_box.setStyleSheet("background-color: #FFFFFF; border: 1px solid #E4E7EC; border-radius: 6px; padding: 8px;")
                s_box_lay = QVBoxLayout(s_box)
                s_box_lay.setContentsMargins(8, 6, 8, 6)
                s_box_lay.setSpacing(4)

                top_s = QHBoxLayout()
                s_name = s.get("signal_name", "Risk Indicator")
                lbl_sn = QLabel(s_name)
                lbl_sn.setStyleSheet("font-size: 12px; font-weight: bold; color: #172B4D;")
                top_s.addWidget(lbl_sn)
                top_s.addStretch()

                # Source badge
                src = s.get("source", "MODEL")
                src_col = "#155EEF" if src == "MODEL" else ("#7F56D9" if src == "GRAPH" else ("#027A48" if src == "BEHAVIORAL" else "#B54708"))
                lbl_src = QLabel(f"[{src}]")
                lbl_src.setStyleSheet(f"color: {src_col}; font-size: 10px; font-weight: bold;")
                top_s.addWidget(lbl_src)
                s_box_lay.addLayout(top_s)

                meas = s.get("measured_value", "N/A")
                base = s.get("baseline_comparison", "Normal activity")
                lbl_val = QLabel(f"Observed: {meas}  |  Baseline: {base}")
                lbl_val.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 11px;")
                s_box_lay.addWidget(lbl_val)

                self.right_layout.addWidget(s_box)

        # Graph Typologies
        graph_pats = alert_data.get("graph_patterns", [])
        if graph_pats:
            lbl_g_title = QLabel("DETECTED GRAPH TOPOLOGY PATTERNS")
            lbl_g_title.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 12px; font-weight: bold; margin-top: 8px;")
            self.right_layout.addWidget(lbl_g_title)

            for g in graph_pats:
                g_box = QFrame()
                g_box.setStyleSheet("background-color: #FEF6EE; border: 1px solid #F9DBAF; border-radius: 6px; padding: 8px;")
                g_lay = QVBoxLayout(g_box)
                g_lay.setContentsMargins(8, 6, 8, 6)

                t_name = g.get("typology_name", g.get("typology", "Graph Anomaly"))
                lbl_gn = QLabel(f"🕸️ {t_name}")
                lbl_gn.setStyleSheet("font-size: 12px; font-weight: bold; color: #B54708;")
                g_lay.addWidget(lbl_gn)

                expl = g.get("explanation", "Structural topology match in counterparty transaction network.")
                lbl_ge = QLabel(expl)
                lbl_ge.setWordWrap(True)
                lbl_ge.setStyleSheet("font-size: 11px; color: #4E2A09;")
                g_lay.addWidget(lbl_ge)

                self.right_layout.addWidget(g_box)

        # Actions
        self.right_layout.addStretch()
        action_row = QHBoxLayout()
        btn_network = QPushButton("Inspect Mule Network")
        btn_network.setStyleSheet("background-color: #155EEF; color: #FFFFFF; border-radius: 4px; padding: 6px 12px; font-size: 12px; font-weight: bold;")
        receiver_acc = alert_data.get("receiver_account", "")
        btn_network.clicked.connect(lambda: self.main_window.switch_content_page(5))
        action_row.addWidget(btn_network)

        btn_cases = QPushButton("View Case Dossiers")
        btn_cases.setStyleSheet("background-color: #F8F9FC; border: 1px solid #E4E7EC; border-radius: 4px; padding: 6px 12px; font-size: 12px; color: #172B4D;")
        btn_cases.clicked.connect(lambda: self.main_window.switch_content_page(11))
        action_row.addWidget(btn_cases)

        self.right_layout.addLayout(action_row)


# ---------------------------------------------------------
# VIEW 11: CASE DOSSIERS & AUDIT TRAILS
# ---------------------------------------------------------
class CaseDossiersView(QWidget):
    def __init__(self, api: ApiClient, main_window: MainWindow):
        super().__init__()
        self.api = api
        self.main_window = main_window
        self.current_status = "All"
        self.current_tier = "All"
        self.init_ui()
        self.load_data()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(15)

        # Top KPI Cards
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(15)

        cards_data = [
            ("TOTAL CASE DOSSIERS", "5 Active Cases", "Targeted mule funnels", COLOR_PRIMARY_BLUE),
            ("PEAK RISK ENTITY", "80032DB60", "Critical Priority (Rank #1)", COLOR_RISK_CRITICAL),
            ("FLAGGED VOLUME", "$284,500.00", "Multi-party aggregate", COLOR_TEXT_PRIMARY),
            ("LEGAL STATUS", "Investigative Lead", "Requires formal SAR filing", COLOR_RISK_HIGH)
        ]

        for title, val, sub, col in cards_data:
            c = QFrame()
            c.setProperty("class", "Card")
            c.setStyleSheet("background-color: #FFFFFF; border: 1px solid #E4E7EC; border-radius: 8px;")
            l = QVBoxLayout(c)
            l.setContentsMargins(15, 12, 15, 12)
            lbl_t = QLabel(title)
            lbl_t.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 11px; font-weight: bold;")
            lbl_v = QLabel(val)
            lbl_v.setStyleSheet(f"color: {col}; font-size: 18px; font-weight: bold;")
            lbl_s = QLabel(sub)
            lbl_s.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 10px;")
            l.addWidget(lbl_t)
            l.addWidget(lbl_v)
            l.addWidget(lbl_s)
            kpi_row.addWidget(c)

        layout.addLayout(kpi_row)

        # Control Bar
        ctrl_card = QFrame()
        ctrl_card.setProperty("class", "Card")
        ctrl_card.setStyleSheet("background-color: #FFFFFF; border: 1px solid #E4E7EC; border-radius: 8px; padding: 5px;")
        ctrl_lay = QHBoxLayout(ctrl_card)
        ctrl_lay.setContentsMargins(15, 8, 15, 8)
        ctrl_lay.setSpacing(10)

        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Filter case dossiers by Case ID, Entity Account...")
        self.txt_search.setStyleSheet("border: 1px solid #E4E7EC; border-radius: 6px; padding: 6px 12px; font-size: 12px;")
        self.txt_search.textChanged.connect(self.apply_case_filter)
        ctrl_lay.addWidget(self.txt_search, 2)

        ctrl_lay.addWidget(QLabel("Status:"))
        self.status_buttons = {}
        for s_name in ["All", "Open", "Under Review", "Closed"]:
            btn = QPushButton(s_name)
            btn.setCheckable(True)
            btn.setChecked(s_name == "All")
            btn.setStyleSheet("""
                QPushButton {
                    border: 1px solid #E4E7EC;
                    border-radius: 4px;
                    padding: 5px 12px;
                    font-size: 11px;
                    font-weight: bold;
                    background-color: #FFFFFF;
                    color: #667085;
                }
                QPushButton:checked {
                    background-color: #155EEF;
                    color: #FFFFFF;
                    border-color: #155EEF;
                }
            """)
            btn.clicked.connect(lambda checked, s=s_name: self.on_status_clicked(s))
            ctrl_lay.addWidget(btn)
            self.status_buttons[s_name] = btn

        ctrl_lay.addStretch()
        btn_refresh = QPushButton("⟳ Refresh")
        btn_refresh.setStyleSheet("background-color: #F8F9FC; border: 1px solid #E4E7EC; border-radius: 4px; padding: 5px 12px; font-size: 11px;")
        btn_refresh.clicked.connect(self.load_data)
        ctrl_lay.addWidget(btn_refresh)

        layout.addWidget(ctrl_card)

        # Main Splitter
        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)

        # Left Table
        self.tbl_cases = QTableWidget()
        self.tbl_cases.setColumnCount(7)
        self.tbl_cases.setHorizontalHeaderLabels(["Case ID", "Primary Entity", "Priority", "Suspicious Volume", "Alerts", "Connected", "Status"])
        self.tbl_cases.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_cases.verticalHeader().setVisible(False)
        self.tbl_cases.itemSelectionChanged.connect(self.on_case_selection_changed)
        splitter.addWidget(self.tbl_cases)

        # Right Detail Area
        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setStyleSheet("border: none; background: transparent;")

        self.case_container = QFrame()
        self.case_container.setProperty("class", "Card")
        self.case_container.setStyleSheet("background-color: #FFFFFF; border: 1px solid #E4E7EC; border-radius: 8px;")
        self.case_layout = QVBoxLayout(self.case_container)
        self.case_layout.setContentsMargins(20, 20, 20, 20)
        self.case_layout.setSpacing(12)

        self.lbl_case_placeholder = QLabel("Select a case dossier from the table to inspect its chronological audit trail, connected accounts, and compliance summary.")
        self.lbl_case_placeholder.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 13px; font-style: italic;")
        self.lbl_case_placeholder.setWordWrap(True)
        self.case_layout.addWidget(self.lbl_case_placeholder)
        self.case_layout.addStretch()

        right_scroll.setWidget(self.case_container)
        splitter.addWidget(right_scroll)

        splitter.setSizes([620, 540])
        layout.addWidget(splitter, 1)

    def on_status_clicked(self, s):
        self.current_status = s
        for s_name, btn in self.status_buttons.items():
            btn.setChecked(s_name == s)
        self.load_data()

    def load_data(self):
        self.all_cases = self.api.get_investigator_cases(status=self.current_status, tier=self.current_tier)
        self.apply_case_filter()

    def apply_case_filter(self):
        query = self.txt_search.text().strip().lower()
        if query:
            filtered = [
                c for c in self.all_cases
                if query in c.get("case_id", "").lower()
                or query in c.get("primary_account", "").lower()
            ]
        else:
            filtered = self.all_cases

        self.rendered_cases = filtered
        self.tbl_cases.setRowCount(len(filtered))

        for row, c in enumerate(filtered):
            self.tbl_cases.setItem(row, 0, QTableWidgetItem(c.get("case_id", "")))
            self.tbl_cases.setItem(row, 1, QTableWidgetItem(c.get("primary_account", "")))

            tier = c.get("priority_tier", "High")
            self.tbl_cases.setCellWidget(row, 2, TableBadgeLabel(tier, tier.lower()))

            vol = c.get("total_suspicious_volume", 0.0)
            self.tbl_cases.setItem(row, 3, QTableWidgetItem(f"${vol:,.2f}"))

            cnt = c.get("alert_count", 1)
            self.tbl_cases.setItem(row, 4, QTableWidgetItem(str(cnt)))

            conn = c.get("connected_accounts_count", len(c.get("related_accounts", [])))
            self.tbl_cases.setItem(row, 5, QTableWidgetItem(f"{conn} nodes"))

            status = c.get("review_status", "Open")
            self.tbl_cases.setItem(row, 6, QTableWidgetItem(status))

        if filtered:
            self.select_case_by_row(0)

    def on_case_selection_changed(self):
        rows = self.tbl_cases.selectionModel().selectedRows()
        if rows:
            self.select_case_by_row(rows[0].row())

    def select_case_by_row(self, row_idx):
        if 0 <= row_idx < len(self.rendered_cases):
            self.render_case_dossier(self.rendered_cases[row_idx])

    def render_case_dossier(self, case_data):
        while self.case_layout.count():
            item = self.case_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # Header
        h_row = QHBoxLayout()
        case_id = case_data.get("case_id", "Unknown")
        lbl_cid = QLabel(f"Dossier: {case_id}")
        lbl_cid.setStyleSheet("font-size: 16px; font-weight: bold; color: #172B4D;")
        h_row.addWidget(lbl_cid)
        h_row.addStretch()

        tier = case_data.get("priority_tier", "Critical")
        h_row.addWidget(TableBadgeLabel(tier, tier.lower()))
        self.case_layout.addLayout(h_row)

        primary_acc = case_data.get("primary_account", "N/A")
        vol = case_data.get("total_suspicious_volume", 0.0)
        lbl_meta = QLabel(f"Primary Target Node: {primary_acc}  ·  Aggregate Flagged Volume: ${vol:,.2f}")
        lbl_meta.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 12px; font-weight: bold;")
        self.case_layout.addWidget(lbl_meta)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"color: {COLOR_BORDER}; margin: 4px 0px;")
        self.case_layout.addWidget(sep)

        # Investigation Summary
        lbl_s_title = QLabel("CASE INVESTIGATION SUMMARY")
        lbl_s_title.setStyleSheet(f"color: {COLOR_PRIMARY_BLUE}; font-size: 11px; font-weight: bold;")
        self.case_layout.addWidget(lbl_s_title)

        summary_text = case_data.get("investigation_summary", "Automated investigative case summary compiled by FinGuard AI.")
        lbl_sum = QLabel(summary_text)
        lbl_sum.setWordWrap(True)
        lbl_sum.setStyleSheet("font-size: 12px; color: #172B4D; line-height: 18px; background-color: #F8F9FC; border: 1px solid #E4E7EC; border-radius: 6px; padding: 10px;")
        self.case_layout.addWidget(lbl_sum)

        # Activity Timeline
        timeline = case_data.get("activity_timeline", [])
        if timeline:
            lbl_t_title = QLabel("CHRONOLOGICAL ACTIVITY TIMELINE")
            lbl_t_title.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 12px; font-weight: bold; margin-top: 8px;")
            self.case_layout.addWidget(lbl_t_title)

            for step in timeline:
                t_card = QFrame()
                t_card.setStyleSheet("background-color: #FFFFFF; border: 1px solid #E4E7EC; border-radius: 6px; padding: 8px;")
                t_lay = QVBoxLayout(t_card)
                t_lay.setContentsMargins(8, 6, 8, 6)
                t_lay.setSpacing(2)

                top_t = QHBoxLayout()
                lbl_step = QLabel(f"Step {step.get('step', 1)}: {step.get('timestamp', '')}")
                lbl_step.setStyleSheet("font-size: 11px; font-weight: bold; color: #155EEF;")
                top_t.addWidget(lbl_step)
                top_t.addStretch()

                s_amt = step.get("amount", 0.0)
                s_curr = step.get("currency", "USD")
                lbl_amt = QLabel(f"${s_amt:,.2f} {s_curr}")
                lbl_amt.setStyleSheet("font-size: 11px; font-weight: bold; color: #172B4D;")
                top_t.addWidget(lbl_amt)
                t_lay.addLayout(top_t)

                t_summ = step.get("summary", "")
                lbl_tsumm = QLabel(t_summ)
                lbl_tsumm.setWordWrap(True)
                lbl_tsumm.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 11px;")
                t_lay.addWidget(lbl_tsumm)

                self.case_layout.addWidget(t_card)

        # Connected Accounts
        rel_accs = case_data.get("related_accounts", [])
        if rel_accs:
            lbl_r_title = QLabel(f"CONNECTED COUNTERPARTY NODES ({len(rel_accs)})")
            lbl_r_title.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 12px; font-weight: bold; margin-top: 8px;")
            self.case_layout.addWidget(lbl_r_title)

            accs_str = ", ".join(rel_accs)
            lbl_accs = QLabel(accs_str)
            lbl_accs.setWordWrap(True)
            lbl_accs.setStyleSheet("font-family: monospace; font-size: 11px; color: #172B4D; background-color: #F8F9FC; border: 1px solid #E4E7EC; border-radius: 4px; padding: 6px 10px;")
            self.case_layout.addWidget(lbl_accs)

        # Mandatory Compliance Disclaimer
        self.case_layout.addStretch()
        disc_box = QFrame()
        disc_box.setStyleSheet("background-color: #FEF3F2; border: 1px solid #FECDCA; border-radius: 6px; padding: 10px;")
        disc_lay = QVBoxLayout(disc_box)
        disc_lay.setContentsMargins(10, 8, 10, 8)
        disc_lay.setSpacing(4)

        lbl_disc_h = QLabel("⚖️ MANDATORY AML COMPLIANCE NOTICE")
        lbl_disc_h.setStyleSheet("font-size: 11px; font-weight: bold; color: #B42318;")
        disc_lay.addWidget(lbl_disc_h)

        disclaimer_text = case_data.get(
            "compliance_disclaimer",
            "NOTICE: This case file represents an automated investigatory lead generated by FinGuard AI based on statistical anomaly detection and graph topology signals. It is designed to assist compliance analysts and does not constitute a confirmed financial crime, legal determination, or proof of illicit activity."
        )
        lbl_disc_body = QLabel(disclaimer_text)
        lbl_disc_body.setWordWrap(True)
        lbl_disc_body.setStyleSheet("font-size: 10px; color: #7A271A; line-height: 14px;")
        disc_lay.addWidget(lbl_disc_body)

        self.case_layout.addWidget(disc_box)
'''

if "class AlertPrioritizationView" not in content:
    target_main = "def main():"
    content = content.replace(target_main, view_classes + "\n" + target_main)
    print("Added AlertPrioritizationView and CaseDossiersView classes.")

with open(APP_PATH, "w", encoding="utf-8") as f:
    f.write(content)

print("Successfully updated frontend/app.py!")
