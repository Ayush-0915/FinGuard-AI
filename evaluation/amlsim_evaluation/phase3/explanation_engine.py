"""
FinGuard AI — Phase 3: Evidence-Grounded Explanation Engine
Produces transparent, multi-source explanations for individual alerts,
synthesizing machine learning outputs, behavioral aggregates, rule signals, and graph typologies.

Strictly preserves:
- Evidence provenance (MODEL vs BEHAVIORAL vs GRAPH vs RULE)
- Measurable signal strengths without fabricated SHAP explanations
- Plain-English compliance narratives for human financial crime investigators
"""

from typing import List, Dict, Any, Optional

class ExplanationEngine:
    def __init__(self, high_amount_threshold: float = 10000.0, rapid_velocity_sec: float = 300.0):
        self.high_amount_threshold = high_amount_threshold
        self.rapid_velocity_sec = rapid_velocity_sec

    def generate_explanation(
        self,
        transaction: Dict[str, Any],
        features: Optional[Dict[str, Any]] = None,
        model_score: Optional[float] = None,
        risk_rank: Optional[int] = None,
        risk_tier: Optional[str] = None,
        graph_patterns: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Builds a comprehensive, grounded explanation for a prioritized alert.
        """
        tx_id = str(transaction.get("transaction_id", transaction.get("original_row_id", "UNKNOWN")))
        ts = str(transaction.get("timestamp", transaction.get("Timestamp", "N/A")))
        sender = str(transaction.get("sender_account", transaction.get("Account", "N/A")))
        receiver = str(transaction.get("receiver_account", transaction.get("Account.1", "N/A")))
        amount = float(transaction.get("amount", transaction.get("Amount Paid", transaction.get("amount_paid", 0.0))))
        currency = str(transaction.get("currency", transaction.get("Payment Currency", transaction.get("payment_currency", "N/A"))))
        pay_format = str(transaction.get("format", transaction.get("Payment Format", transaction.get("payment_format", "N/A"))))

        score = float(model_score) if model_score is not None else float(transaction.get("model_probability", 0.0))
        tier = risk_tier or transaction.get("risk_tier", "Medium")
        rank = risk_rank or transaction.get("risk_rank", None)

        signals = []
        narrative_points = []

        # 1. Model Contribution
        if score >= 0.95:
            signals.append({
                "signal_name": "Elevated Statistical Risk Score",
                "source": "MODEL",
                "strength": "CRITICAL" if score >= 0.99 else "HIGH",
                "measured_value": round(score, 4),
                "baseline_comparison": "Base population threshold >= 0.95"
            })
            narrative_points.append(f"assigned a {score*100:.1f}% statistical risk score by the LightGBM temporal model")

        # 2. Behavioral Features Contribution (if feature vector is provided)
        if features:
            # Currency mismatch
            curr_match = features.get("currency_match", 1)
            if curr_match == 0:
                signals.append({
                    "signal_name": "Cross-Border Currency Conversion",
                    "source": "BEHAVIORAL",
                    "strength": "HIGH",
                    "measured_value": "Currency Mismatch",
                    "baseline_comparison": "Domestic settlement"
                })
                narrative_points.append("involves an active cross-border currency conversion")

            # High Velocity Burst
            sec_prev = float(features.get("seconds_since_previous", 999999.0))
            if 0 < sec_prev <= self.rapid_velocity_sec:
                signals.append({
                    "signal_name": "Rapid Burst Velocity",
                    "source": "BEHAVIORAL",
                    "strength": "HIGH",
                    "measured_value": f"{round(sec_prev, 1)} seconds since prior transfer",
                    "baseline_comparison": f"Normal spacing > {self.rapid_velocity_sec}s"
                })
                narrative_points.append(f"occurred within {int(sec_prev)}s of the account's previous transfer")

            # Funnel aggregation (many unique senders into receiver)
            rec_unique_senders = int(features.get("receiver_unique_senders", 0))
            if rec_unique_senders >= 5:
                signals.append({
                    "signal_name": "High Counterparty Fan-In",
                    "source": "BEHAVIORAL",
                    "strength": "HIGH",
                    "measured_value": f"{rec_unique_senders} unique senders",
                    "baseline_comparison": "Typical receiver < 3 senders"
                })
                narrative_points.append(f"directs funds into an account collecting from {rec_unique_senders} distinct senders")

            # High Fan-out (sender disbursing to many receivers)
            snd_unique_rec = int(features.get("sender_unique_receivers", 0))
            if snd_unique_rec >= 5:
                signals.append({
                    "signal_name": "High Counterparty Fan-Out",
                    "source": "BEHAVIORAL",
                    "strength": "HIGH",
                    "measured_value": f"{snd_unique_rec} unique receivers",
                    "baseline_comparison": "Typical sender < 3 receivers"
                })
                narrative_points.append(f"originates from a sender disbursing to {snd_unique_rec} distinct recipients")

        # 3. Graph Intelligence Contribution
        applicable_graph_signals = []
        if graph_patterns:
            for p in graph_patterns:
                typology = p.get("typology_name", p.get("typology", "Graph Anomaly"))
                severity = p.get("severity_score", 0.7)
                applicable_graph_signals.append({
                    "typology": p.get("typology"),
                    "typology_name": typology,
                    "severity": severity,
                    "explanation": p.get("investigator_explanation")
                })
                signals.append({
                    "signal_name": f"Graph Pattern: {typology}",
                    "source": "GRAPH",
                    "strength": "CRITICAL" if severity >= 0.85 else "HIGH",
                    "measured_value": f"Severity {severity}",
                    "baseline_comparison": "Acyclic benign flow"
                })
                narrative_points.append(f"exhibits structural graph involvement ({typology.lower()})")

        # 4. Rule Heuristics Contribution
        if amount >= self.high_amount_threshold:
            signals.append({
                "signal_name": "High-Value Transaction Size",
                "source": "RULE",
                "strength": "MEDIUM",
                "measured_value": f"${amount:,.2f}",
                "baseline_comparison": f"Threshold >= ${self.high_amount_threshold:,.2f}"
            })
            narrative_points.append(f"surpasses the ${self.high_amount_threshold:,.2f} high-value monitoring threshold")

        # Construct Plain-English Narrative
        if narrative_points:
            summary = (
                f"Alert for transaction {tx_id}: Account {sender} transferred ${amount:,.2f} {currency} "
                f"to {receiver} on {ts}. This transaction is classified as {tier} priority (Rank #{rank if rank else 'N/A'}) "
                f"because it {', '.join(narrative_points)}."
            )
        else:
            summary = (
                f"Alert for transaction {tx_id}: Account {sender} transferred ${amount:,.2f} {currency} "
                f"to {receiver} on {ts} with a risk score of {score:.4f}."
            )

        return {
            "transaction_id": tx_id,
            "timestamp": ts,
            "sender_account": sender,
            "receiver_account": receiver,
            "amount": amount,
            "currency": currency,
            "payment_format": pay_format,
            "model_risk_score": score,
            "risk_rank": rank,
            "risk_tier": tier,
            "contributing_signals": signals,
            "graph_patterns": applicable_graph_signals,
            "human_readable_summary": summary,
            "provenance_breakdown": {
                "model_signals_count": sum(1 for s in signals if s["source"] == "MODEL"),
                "behavioral_signals_count": sum(1 for s in signals if s["source"] == "BEHAVIORAL"),
                "graph_signals_count": sum(1 for s in signals if s["source"] == "GRAPH"),
                "rule_signals_count": sum(1 for s in signals if s["source"] == "RULE")
            }
        }
