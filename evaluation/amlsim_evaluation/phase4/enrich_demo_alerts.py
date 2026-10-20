"""
Enrich sample_alerts.json up to 50 alerts across all risk tiers
(Critical, High, Medium, Low) for comprehensive demo testing.
Preserves existing ranks 1-10 exactly.
"""

import json
import os

path = os.path.join(os.path.dirname(__file__), "..", "phase3", "artifacts", "sample_alerts.json")
with open(path, "r", encoding="utf-8") as f:
    existing = json.load(f)

# Define templates for additional alerts
extra_data = [
    # Critical (11-20)
    (11, 'TX_4712410', '2022/09/09 18:05', '80041A990', '80032DB60', 3890.00, 'US Dollar', 'ACH', 0.992, 'Critical', 'Fan-In Aggregation (Mule Funnel)', 1.0, 9, '12 unique senders into node', 'MODEL,BEHAVIORAL,GRAPH'),
    (12, 'TX_4712495', '2022/09/09 18:06', '80045B110', '80032DB60', 5120.50, 'US Dollar', 'Wire', 0.988, 'Critical', 'Fan-In Aggregation (Mule Funnel)', 0.95, 11, 'Rapid aggregation across 15 min', 'MODEL,BEHAVIORAL,GRAPH'),
    (13, 'TX_4712530', '2022/09/09 18:08', '80047C220', '80032DB60', 4750.00, 'US Dollar', 'Wire', 0.985, 'Critical', 'Fan-In Aggregation (Mule Funnel)', 0.95, 8, 'Structured wire transfer batch', 'MODEL,BEHAVIORAL,GRAPH,RULE'),
    (14, 'TX_4712610', '2022/09/09 18:10', '80052D330', '800E29A00', 8900.00, 'US Dollar', 'Wire', 0.981, 'Critical', 'Rapid Movement / Structuring', 0.90, 6, 'Immediate passthrough under 120s', 'MODEL,BEHAVIORAL,GRAPH'),
    (15, 'TX_4712680', '2022/09/09 18:12', '80058E440', '800E29A00', 9200.00, 'US Dollar', 'ACH', 0.978, 'Critical', 'Rapid Movement / Structuring', 0.90, 7, 'Sequential transfer burst', 'MODEL,BEHAVIORAL,GRAPH'),
    (16, 'TX_4712740', '2022/09/09 18:14', '80061F550', '8022DA710', 6400.00, 'US Dollar', 'ACH', 0.974, 'Critical', 'Fan-In Aggregation (Mule Funnel)', 0.85, 8, 'High recipient concentration', 'MODEL,BEHAVIORAL,GRAPH'),
    (17, 'TX_4712810', '2022/09/09 18:15', '80067A660', '8022DA710', 7100.00, 'US Dollar', 'Wire', 0.970, 'Critical', 'Fan-In Aggregation (Mule Funnel)', 0.85, 10, 'Concentrated inward payment volume', 'MODEL,BEHAVIORAL,GRAPH'),
    (18, 'TX_4712890', '2022/09/09 18:17', '80072B770', '802AEBAC0', 12500.00, 'US Dollar', 'Wire', 0.965, 'Critical', 'High-Value Anomaly', 0.90, 4, 'Amount exceeds 99th percentile', 'MODEL,BEHAVIORAL,GRAPH,RULE'),
    (19, 'TX_4712950', '2022/09/09 18:19', '80078C880', '802AEBAC0', 14200.00, 'US Dollar', 'Wire', 0.961, 'Critical', 'High-Value Anomaly', 0.90, 5, 'Peak single-session debit', 'MODEL,BEHAVIORAL,GRAPH,RULE'),
    (20, 'TX_4713020', '2022/09/09 18:20', '80084D990', '80306B530', 8800.00, 'US Dollar', 'ACH', 0.954, 'Critical', 'Fan-Out Disbursement', 0.85, 14, 'Dispersal to 14 receiver nodes', 'MODEL,BEHAVIORAL,GRAPH'),

    # High (21-35)
    (21, 'TX_4713100', '2022/09/09 18:22', '80091A110', '80306B530', 7500.00, 'US Dollar', 'Wire', 0.942, 'High', 'Fan-Out Disbursement', 0.80, 12, 'Smurfing disbursement pattern', 'MODEL,BEHAVIORAL,GRAPH'),
    (22, 'TX_4713180', '2022/09/09 18:23', '80097B220', '80306B530', 6900.00, 'US Dollar', 'ACH', 0.935, 'High', 'Fan-Out Disbursement', 0.80, 11, 'Multiple small disbursements', 'MODEL,BEHAVIORAL,GRAPH'),
    (23, 'TX_4713250', '2022/09/09 18:25', '80102C330', '80032DB60', 3200.00, 'US Dollar', 'ACH', 0.920, 'High', 'Fan-In Aggregation (Mule Funnel)', 0.75, 6, 'Moderate funnel contributor', 'MODEL,BEHAVIORAL,GRAPH'),
    (24, 'TX_4713320', '2022/09/09 18:26', '80108D440', '80032DB60', 2900.00, 'US Dollar', 'ACH', 0.912, 'High', 'Fan-In Aggregation (Mule Funnel)', 0.75, 5, 'Velocity acceleration factor', 'MODEL,BEHAVIORAL,GRAPH'),
    (25, 'TX_4713400', '2022/09/09 18:28', '80115E550', '80150A990', 9800.00, 'US Dollar', 'Wire', 0.895, 'High', 'Rapid Movement / Structuring', 0.75, 4, 'Hop velocity < 180 seconds', 'MODEL,BEHAVIORAL,GRAPH'),
    (26, 'TX_4713480', '2022/09/09 18:29', '80121F660', '80150A990', 9500.00, 'US Dollar', 'Wire', 0.884, 'High', 'Rapid Movement / Structuring', 0.75, 4, 'Just under $10,000 reporting threshold', 'MODEL,BEHAVIORAL,GRAPH,RULE'),
    (27, 'TX_4713550', '2022/09/09 18:31', '80128A770', '80165B110', 6300.00, 'US Dollar', 'ACH', 0.871, 'High', 'High-Value Anomaly', 0.70, 3, 'Elevated volume relative to history', 'MODEL,BEHAVIORAL'),
    (28, 'TX_4713620', '2022/09/09 18:32', '80134B880', '80165B110', 5800.00, 'US Dollar', 'ACH', 0.858, 'High', 'High-Value Anomaly', 0.70, 3, 'Sudden activity burst', 'MODEL,BEHAVIORAL'),
    (29, 'TX_4713700', '2022/09/09 18:34', '80141C990', '80178C220', 8200.00, 'US Dollar', 'Wire', 0.842, 'High', 'Fan-Out Disbursement', 0.70, 8, 'Dispersal to multiple endpoints', 'MODEL,BEHAVIORAL,GRAPH'),
    (30, 'TX_4713780', '2022/09/09 18:35', '80148D010', '80178C220', 7900.00, 'US Dollar', 'Wire', 0.829, 'High', 'Fan-Out Disbursement', 0.70, 7, 'Coordinated batch wires', 'MODEL,BEHAVIORAL,GRAPH'),
    (31, 'TX_4713850', '2022/09/09 18:37', '80155E120', '80189D330', 4900.00, 'US Dollar', 'ACH', 0.812, 'High', 'Fan-In Aggregation (Mule Funnel)', 0.65, 5, 'Inward velocity buildup', 'MODEL,BEHAVIORAL'),
    (32, 'TX_4713920', '2022/09/09 18:38', '80162F230', '80189D330', 5200.00, 'US Dollar', 'ACH', 0.798, 'High', 'Fan-In Aggregation (Mule Funnel)', 0.65, 5, 'Multiple inward sources', 'MODEL,BEHAVIORAL'),
    (33, 'TX_4714000', '2022/09/09 18:40', '80169A340', '80199E440', 6700.00, 'US Dollar', 'Wire', 0.775, 'High', 'Rapid Movement / Structuring', 0.65, 3, 'Consecutive fund relays', 'MODEL,GRAPH'),
    (34, 'TX_4714080', '2022/09/09 18:41', '80176B450', '80199E440', 7100.00, 'US Dollar', 'Wire', 0.753, 'High', 'Rapid Movement / Structuring', 0.65, 3, 'Relay across intermediate account', 'MODEL,GRAPH'),
    (35, 'TX_4714150', '2022/09/09 18:43', '80183C560', '80210F550', 5400.00, 'US Dollar', 'ACH', 0.721, 'High', 'High-Value Anomaly', 0.60, 4, 'Moderate outlier transaction size', 'MODEL,BEHAVIORAL'),

    # Medium (36-45)
    (36, 'TX_4714220', '2022/09/09 18:45', '80190D670', '80222A660', 3600.00, 'US Dollar', 'ACH', 0.684, 'Medium', 'Fan-In Aggregation (Mule Funnel)', 0.50, 4, 'Mild aggregation activity', 'MODEL,BEHAVIORAL'),
    (37, 'TX_4714300', '2022/09/09 18:46', '80197E780', '80222A660', 3100.00, 'US Dollar', 'ACH', 0.652, 'Medium', 'Fan-In Aggregation (Mule Funnel)', 0.50, 3, 'Consistent deposit pattern', 'MODEL'),
    (38, 'TX_4714380', '2022/09/09 18:48', '80204F890', '80235B770', 4200.00, 'US Dollar', 'Wire', 0.619, 'Medium', 'Rapid Movement / Structuring', 0.45, 2, 'Mild velocity increase', 'MODEL,BEHAVIORAL'),
    (39, 'TX_4714450', '2022/09/09 18:49', '80211A900', '80235B770', 3800.00, 'US Dollar', 'Wire', 0.587, 'Medium', 'Rapid Movement / Structuring', 0.45, 2, 'Intermittent wire transfer', 'MODEL'),
    (40, 'TX_4714520', '2022/09/09 18:51', '80218B010', '80248C880', 2500.00, 'US Dollar', 'ACH', 0.554, 'Medium', 'Fan-Out Disbursement', 0.40, 4, 'Dispersal to small merchant pool', 'MODEL,GRAPH'),
    (41, 'TX_4714600', '2022/09/09 18:52', '80225C120', '80248C880', 2700.00, 'US Dollar', 'ACH', 0.521, 'Medium', 'Fan-Out Disbursement', 0.40, 3, 'Routine multi-party payment', 'MODEL'),
    (42, 'TX_4714680', '2022/09/09 18:54', '80232D230', '80259D990', 4800.00, 'US Dollar', 'Wire', 0.493, 'Medium', 'High-Value Anomaly', 0.40, 2, 'Slightly elevated debit amount', 'MODEL,RULE'),
    (43, 'TX_4714750', '2022/09/09 18:55', '80239E340', '80259D990', 3900.00, 'US Dollar', 'Wire', 0.468, 'Medium', 'High-Value Anomaly', 0.35, 2, 'Occasional business invoice payment', 'MODEL'),
    (44, 'TX_4714820', '2022/09/09 18:57', '80246F450', '80268E010', 2200.00, 'US Dollar', 'ACH', 0.441, 'Medium', 'Fan-In Aggregation (Mule Funnel)', 0.35, 3, 'Minor inward volume increase', 'MODEL'),
    (45, 'TX_4714900', '2022/09/09 18:58', '80253A560', '80268E010', 2100.00, 'US Dollar', 'ACH', 0.415, 'Medium', 'Fan-In Aggregation (Mule Funnel)', 0.30, 2, 'Routine peer transfer flow', 'MODEL'),

    # Low (46-50)
    (46, 'TX_4714980', '2022/09/09 19:00', '80260B670', '80279F120', 850.00, 'US Dollar', 'ACH', 0.362, 'Low', 'None', 0.0, 1, 'Standard peer payment', 'MODEL'),
    (47, 'TX_4715050', '2022/09/09 19:02', '80267C780', '80279F120', 620.00, 'US Dollar', 'ACH', 0.285, 'Low', 'None', 0.0, 1, 'Regular grocery purchase', 'MODEL'),
    (48, 'TX_4715120', '2022/09/09 19:03', '80274D890', '80289A230', 1150.00, 'US Dollar', 'Credit Card', 0.210, 'Low', 'None', 0.0, 1, 'Utility bill payment', 'MODEL'),
    (49, 'TX_4715200', '2022/09/09 19:05', '80281E900', '80289A230', 450.00, 'US Dollar', 'Debit Card', 0.145, 'Low', 'None', 0.0, 1, 'Recurring streaming subscription', 'MODEL'),
    (50, 'TX_4715280', '2022/09/09 19:06', '80288F010', '80299B340', 320.00, 'US Dollar', 'Debit Card', 0.082, 'Low', 'None', 0.0, 1, 'Coffee shop purchase', 'MODEL')
]

enriched_list = list(existing)

for rank, tx_id, ts, sender, receiver, amt, curr, pay_fmt, score, tier, typo, sev, receivers_cnt, note, src_str in extra_data:
    src_list = [s.strip() for s in src_str.split(",")]
    signals = []

    if "MODEL" in src_list:
        threshold_val = 0.95 if tier == "Critical" else (0.70 if tier == "High" else 0.40)
        signals.append({
            "signal_name": "Statistical Risk Probability",
            "source": "MODEL",
            "strength": "CRITICAL" if score >= 0.95 else ("HIGH" if score >= 0.70 else ("MEDIUM" if score >= 0.40 else "LOW")),
            "measured_value": round(score, 3),
            "baseline_comparison": f"Operational tier threshold >= {threshold_val}"
        })
    if "BEHAVIORAL" in src_list:
        signals.append({
            "signal_name": "Counterparty Velocity & Fan-Out",
            "source": "BEHAVIORAL",
            "strength": "HIGH" if receivers_cnt > 5 else "MEDIUM",
            "measured_value": f"{receivers_cnt} unique counterparties",
            "baseline_comparison": "Normal account benchmark < 3 counterparties"
        })
    if "GRAPH" in src_list and typo != "None":
        signals.append({
            "signal_name": f"Graph Pattern: {typo}",
            "source": "GRAPH",
            "strength": "CRITICAL" if sev >= 0.85 else "HIGH",
            "measured_value": f"Severity {sev}",
            "baseline_comparison": "Acyclic standard transaction baseline"
        })
    if "RULE" in src_list:
        signals.append({
            "signal_name": "Regulatory Threshold Proximity Rule",
            "source": "RULE",
            "strength": "HIGH",
            "measured_value": f"${amt:,.2f} near $10k reporting limit",
            "baseline_comparison": "BSA CTR threshold at $10,000"
        })

    graph_pats = []
    if typo != "None":
        typo_code = "FAN_IN" if "Fan-In" in typo else ("FAN_OUT" if "Fan-Out" in typo else ("RAPID_MOVEMENT" if "Rapid" in typo else "HIGH_VALUE"))
        graph_pats.append({
            "typology": typo_code,
            "typology_name": typo,
            "severity": sev,
            "explanation": f"{note}. Target node: {receiver}."
        })

    enriched_list.append({
        "transaction_id": tx_id,
        "timestamp": ts,
        "sender_account": sender,
        "receiver_account": receiver,
        "amount": amt,
        "currency": curr,
        "payment_format": pay_fmt,
        "model_risk_score": score,
        "risk_rank": rank,
        "risk_tier": tier,
        "contributing_signals": signals,
        "graph_patterns": graph_pats,
        "human_readable_summary": f"Alert for transaction {tx_id}: Account {sender} transferred ${amt:,.2f} {curr} to {receiver} on {ts}. Priority tier: {tier} (Rank #{rank}) driven by {score*100:.1f}% statistical risk score and {note.lower()}.",
        "provenance_breakdown": {
            "model_signals_count": sum(1 for s in signals if s["source"] == "MODEL"),
            "behavioral_signals_count": sum(1 for s in signals if s["source"] == "BEHAVIORAL"),
            "graph_signals_count": sum(1 for s in signals if s["source"] == "GRAPH"),
            "rule_signals_count": sum(1 for s in signals if s["source"] == "RULE")
        }
    })

with open(path, "w", encoding="utf-8") as f:
    json.dump(enriched_list, f, indent=2)

print(f"Enriched sample_alerts.json successfully! Total alerts now: {len(enriched_list)}")
