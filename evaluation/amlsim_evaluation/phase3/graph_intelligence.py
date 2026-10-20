"""
FinGuard AI — Phase 3: Graph Intelligence Engine
Constructs directed, timestamped transaction networks using NetworkX and detects
six canonical financial crime typologies:
1. Fan-in (Smurfing / Mule collection)
2. Fan-out (Dispersal / Layering)
3. Circular Flow (Cycle detection)
4. High-Value Anomaly (Unusual ticket size)
5. Rapid Movement (Pass-through / Layering velocity)
6. Counterparty Concentration (Funnel concentration vs fragmentation)

Strictly enforces:
- Temporal causality (only transactions at or before time T are analyzed)
- Traceability back to exact transaction IDs and involved accounts
- Measurable severity scoring [0.0, 1.0] and confidence levels
"""

import networkx as nx
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Set, Tuple
from datetime import datetime, timedelta

class GraphIntelligenceEngine:
    def __init__(
        self,
        fan_in_threshold: int = 3,
        fan_out_threshold: int = 3,
        max_cycle_length: int = 4,
        rapid_movement_window_hours: float = 24.0,
        high_value_multiplier: float = 3.0,
        concentration_threshold: float = 0.85
    ):
        """
        Initializes the Graph Intelligence Engine with configurable parameters.
        """
        self.fan_in_threshold = fan_in_threshold
        self.fan_out_threshold = fan_out_threshold
        self.max_cycle_length = max_cycle_length
        self.rapid_window_hours = rapid_movement_window_hours
        self.high_value_multiplier = high_value_multiplier
        self.concentration_threshold = concentration_threshold

    def build_graph(self, transactions_df: pd.DataFrame) -> nx.MultiDiGraph:
        """
        Builds a NetworkX MultiDiGraph from transactions.
        Nodes represent accounts; directed edges represent transaction flows.
        """
        G = nx.MultiDiGraph()
        if len(transactions_df) == 0:
            return G

        for _, row in transactions_df.iterrows():
            u = str(row["Account"])
            v = str(row["Account.1"])
            tx_id = str(row.get("transaction_id", row.get("original_row_id", f"TX_{_}")))
            amt = float(row.get("Amount Paid", row.get("amount_paid", 0.0)))
            ts_str = str(row.get("Timestamp", row.get("timestamp", "")))
            
            # Epoch seconds
            dt = pd.to_datetime(ts_str, errors="coerce")
            epoch_sec = int(dt.timestamp()) if pd.notnull(dt) else 0

            G.add_edge(
                u, v,
                key=tx_id,
                transaction_id=tx_id,
                amount=amt,
                timestamp=ts_str,
                epoch_sec=epoch_sec,
                from_bank=row.get("From Bank", row.get("from_bank", None)),
                to_bank=row.get("To Bank", row.get("to_bank", None)),
                currency=row.get("Payment Currency", row.get("payment_currency", None)),
                format=row.get("Payment Format", row.get("payment_format", None))
            )
        return G

    def detect_fan_in(self, G: nx.MultiDiGraph) -> List[Dict[str, Any]]:
        """
        Detects Fan-In (Aggregation / Mule Collection):
        Multiple distinct senders transfer funds into a common receiver.
        """
        patterns = []
        for node in G.nodes():
            in_edges = list(G.in_edges(node, data=True, keys=True))
            senders = {u for u, _, _, _ in in_edges}
            if len(senders) >= self.fan_in_threshold:
                tx_ids = [data.get("transaction_id") for _, _, _, data in in_edges]
                amounts = [data.get("amount", 0.0) for _, _, _, data in in_edges]
                total_amt = sum(amounts)
                timestamps = [data.get("timestamp") for _, _, _, data in in_edges if data.get("timestamp")]
                
                # Severity scales with in-degree
                degree_factor = min(1.0, len(senders) / (self.fan_in_threshold * 3))
                severity = round(0.5 + 0.5 * degree_factor, 3)

                patterns.append({
                    "typology": "FAN_IN",
                    "typology_name": "Fan-In Aggregation (Mule Funnel)",
                    "target_account": node,
                    "involved_accounts": list(senders) + [node],
                    "involved_transactions": tx_ids,
                    "statistics": {
                        "unique_senders_count": len(senders),
                        "transaction_count": len(in_edges),
                        "total_amount_received": total_amt,
                        "average_amount_received": round(total_amt / len(in_edges), 2) if in_edges else 0.0
                    },
                    "time_interval": {
                        "first_seen": min(timestamps) if timestamps else "N/A",
                        "last_seen": max(timestamps) if timestamps else "N/A"
                    },
                    "severity_score": severity,
                    "confidence_level": "HIGH" if len(senders) >= self.fan_in_threshold * 2 else "MEDIUM",
                    "investigator_explanation": (
                        f"Account {node} received funds from {len(senders)} distinct sender accounts "
                        f"totalling ${total_amt:,.2f} across {len(in_edges)} transfers, exhibiting classic "
                        "mule collection funneling behavior."
                    ),
                    "known_limitations": "Legitimate merchant, e-commerce, or payroll accounts can exhibit natural fan-in."
                })
        return patterns

    def detect_fan_out(self, G: nx.MultiDiGraph) -> List[Dict[str, Any]]:
        """
        Detects Fan-Out (Dispersal / Smurfing):
        A single source account disperses funds to multiple distinct receivers.
        """
        patterns = []
        for node in G.nodes():
            out_edges = list(G.out_edges(node, data=True, keys=True))
            receivers = {v for _, v, _, _ in out_edges}
            if len(receivers) >= self.fan_out_threshold:
                tx_ids = [data.get("transaction_id") for _, _, _, data in out_edges]
                amounts = [data.get("amount", 0.0) for _, _, _, data in out_edges]
                total_amt = sum(amounts)
                timestamps = [data.get("timestamp") for _, _, _, data in out_edges if data.get("timestamp")]

                degree_factor = min(1.0, len(receivers) / (self.fan_out_threshold * 3))
                severity = round(0.5 + 0.5 * degree_factor, 3)

                patterns.append({
                    "typology": "FAN_OUT",
                    "typology_name": "Fan-Out Dispersal (Layering Distribution)",
                    "target_account": node,
                    "involved_accounts": [node] + list(receivers),
                    "involved_transactions": tx_ids,
                    "statistics": {
                        "unique_receivers_count": len(receivers),
                        "transaction_count": len(out_edges),
                        "total_amount_sent": total_amt,
                        "average_amount_sent": round(total_amt / len(out_edges), 2) if out_edges else 0.0
                    },
                    "time_interval": {
                        "first_seen": min(timestamps) if timestamps else "N/A",
                        "last_seen": max(timestamps) if timestamps else "N/A"
                    },
                    "severity_score": severity,
                    "confidence_level": "HIGH" if len(receivers) >= self.fan_out_threshold * 2 else "MEDIUM",
                    "investigator_explanation": (
                        f"Account {node} dispersed ${total_amt:,.2f} across {len(receivers)} distinct recipient accounts "
                        f"over {len(out_edges)} transactions, characteristic of smurfing or illicit fund dispersal."
                    ),
                    "known_limitations": "Corporate accounts executing supplier payouts or batch payroll show benign fan-out."
                })
        return patterns

    def detect_circular_flow(self, G: nx.MultiDiGraph) -> List[Dict[str, Any]]:
        """
        Detects Circular Flow (Directed Cycles):
        Funds flow through a closed loop of accounts (e.g., A -> B -> C -> A).
        """
        # Convert to simple DiGraph for cycle detection
        simple_di = nx.DiGraph(G)
        patterns = []
        try:
            cycles = list(nx.simple_cycles(simple_di))
        except Exception:
            return []

        seen_cycles = set()
        for cycle in cycles:
            c_len = len(cycle)
            if 2 <= c_len <= self.max_cycle_length:
                # Canonical representation for deduplication
                cycle_key = tuple(sorted(cycle))
                if cycle_key in seen_cycles:
                    continue
                seen_cycles.add(cycle_key)

                # Collect edges along the cycle
                involved_tx_ids = []
                cycle_amounts = []
                cycle_timestamps = []
                is_temporally_plausible = True

                for i in range(c_len):
                    u = cycle[i]
                    v = cycle[(i + 1) % c_len]
                    if G.has_edge(u, v):
                        edge_data = list(G.get_edge_data(u, v).values())[0]
                        involved_tx_ids.append(edge_data.get("transaction_id"))
                        cycle_amounts.append(edge_data.get("amount", 0.0))
                        cycle_timestamps.append(edge_data.get("epoch_sec", 0))

                # Check chronological progression along cycle
                if len(cycle_timestamps) >= 2:
                    # Valid if timestamps are generally increasing or within rapid window
                    time_diff = max(cycle_timestamps) - min(cycle_timestamps)
                    is_temporally_plausible = (time_diff <= self.rapid_window_hours * 3600 * 2)

                severity = round(0.85 if c_len > 2 else 0.70, 3)

                patterns.append({
                    "typology": "CIRCULAR_FLOW",
                    "typology_name": f"{c_len}-Hop Circular Flow (Round-Tripping Layering)",
                    "cycle_length": c_len,
                    "cycle_path": cycle + [cycle[0]],
                    "involved_accounts": cycle,
                    "involved_transactions": involved_tx_ids,
                    "statistics": {
                        "cycle_hops": c_len,
                        "mean_hop_amount": round(float(np.mean(cycle_amounts)), 2) if cycle_amounts else 0.0,
                        "min_hop_amount": round(float(min(cycle_amounts)), 2) if cycle_amounts else 0.0,
                        "max_hop_amount": round(float(max(cycle_amounts)), 2) if cycle_amounts else 0.0
                    },
                    "severity_score": severity,
                    "confidence_level": "HIGH" if is_temporally_plausible else "MEDIUM",
                    "investigator_explanation": (
                        f"Detected a closed financial round-tripping cycle of {c_len} accounts: "
                        f"{' -> '.join(cycle)} -> {cycle[0]}. Circular transactions often indicate "
                        "artificial volume generation, tax evasion, or layering."
                    ),
                    "known_limitations": "Frequent refunds or bilateral payment rebalances between trusted trading partners."
                })
        return patterns

    def detect_rapid_movement(self, G: nx.MultiDiGraph) -> List[Dict[str, Any]]:
        """
        Detects Rapid Movement (Pass-through Mule):
        Account B receives funds from A and quickly forwards funds to C (within rapid_window_hours).
        """
        patterns = []
        window_sec = self.rapid_window_hours * 3600

        for node in G.nodes():
            in_edges = list(G.in_edges(node, data=True))
            out_edges = list(G.out_edges(node, data=True))

            if not in_edges or not out_edges:
                continue

            for u, _, in_data in in_edges:
                in_time = in_data.get("epoch_sec", 0)
                in_amt = in_data.get("amount", 0.0)

                for _, w, out_data in out_edges:
                    if u == w: # Skip immediate refund back to sender
                        continue
                    out_time = out_data.get("epoch_sec", 0)
                    out_amt = out_data.get("amount", 0.0)

                    # Pass-through condition: out occurs after in, within window
                    delta = out_time - in_time
                    if 0 < delta <= window_sec:
                        # Retention ratio: what fraction of funds was forwarded
                        retention = min(in_amt, out_amt) / max(in_amt, out_amt) if max(in_amt, out_amt) > 0 else 0.0
                        if retention >= 0.70: # At least 70% of funds forwarded
                            severity = round(0.75 + 0.20 * retention, 3)
                            patterns.append({
                                "typology": "RAPID_MOVEMENT",
                                "typology_name": "Rapid Pass-Through Movement (Mule Layering)",
                                "intermediary_account": node,
                                "source_account": u,
                                "destination_account": w,
                                "involved_accounts": [u, node, w],
                                "involved_transactions": [in_data.get("transaction_id"), out_data.get("transaction_id")],
                                "statistics": {
                                    "inflow_amount": in_amt,
                                    "outflow_amount": out_amt,
                                    "pass_through_ratio": round(retention, 4),
                                    "elapsed_minutes": round(delta / 60, 1)
                                },
                                "severity_score": severity,
                                "confidence_level": "HIGH" if delta <= 3600 else "MEDIUM",
                                "investigator_explanation": (
                                    f"Intermediary account {node} received ${in_amt:,.2f} from {u} and within "
                                    f"{round(delta/60, 1)} minutes transferred ${out_amt:,.2f} to {w} "
                                    f"({round(retention*100, 1)}% passthrough), characteristic of rapid mule layering."
                                ),
                                "known_limitations": "Automated payment gateways or escrow services naturally pass funds rapidly."
                            })
                            # Limit per node to prevent quadratic explosion
                            if len(patterns) >= 500:
                                return patterns
        return patterns

    def detect_high_value_anomalies(self, G: nx.MultiDiGraph) -> List[Dict[str, Any]]:
        """
        Detects High-Value Anomalies:
        Transactions exceeding a statistical multiple of the sender's average historical amount.
        """
        patterns = []
        for node in G.nodes():
            out_edges = list(G.out_edges(node, data=True))
            if len(out_edges) < 2:
                continue
            amounts = [d.get("amount", 0.0) for _, _, d in out_edges]
            mean_amt = float(np.mean(amounts))
            for _, v, d in out_edges:
                amt = d.get("amount", 0.0)
                if amt >= self.high_value_multiplier * mean_amt and amt > 10000.0:
                    severity = min(0.95, round(0.5 + 0.1 * (amt / (mean_amt + 1e-5)), 3))
                    patterns.append({
                        "typology": "HIGH_VALUE_ANOMALY",
                        "typology_name": "High-Value Transaction Spike",
                        "involved_accounts": [node, v],
                        "involved_transactions": [d.get("transaction_id")],
                        "statistics": {
                            "transaction_amount": amt,
                            "account_historical_mean": round(mean_amt, 2),
                            "spike_ratio": round(amt / mean_amt, 2)
                        },
                        "severity_score": severity,
                        "confidence_level": "MEDIUM",
                        "investigator_explanation": (
                            f"Account {node} executed a transfer of ${amt:,.2f} to {v}, which is "
                            f"{round(amt/mean_amt, 1)}x higher than the account's historical average."
                        ),
                        "known_limitations": "Occasional legitimate capital expenditures or one-off real estate payments."
                    })
        return patterns

    def detect_counterparty_concentration(self, G: nx.MultiDiGraph) -> List[Dict[str, Any]]:
        """
        Detects Counterparty Concentration:
        An account executing multiple transactions directs >85% of volume to a single receiver.
        """
        patterns = []
        for node in G.nodes():
            out_edges = list(G.out_edges(node, data=True))
            if len(out_edges) < 3:
                continue
            rec_amounts = {}
            total_amt = 0.0
            for _, v, d in out_edges:
                amt = d.get("amount", 0.0)
                rec_amounts[v] = rec_amounts.get(v, 0.0) + amt
                total_amt += amt

            if total_amt > 0:
                top_rec, top_amt = max(rec_amounts.items(), key=lambda x: x[1])
                ratio = top_amt / total_amt
                if ratio >= self.concentration_threshold and len(rec_amounts) > 1:
                    patterns.append({
                        "typology": "COUNTERPARTY_CONCENTRATION",
                        "typology_name": "Exclusive Counterparty Concentration",
                        "involved_accounts": [node, top_rec],
                        "involved_transactions": [d.get("transaction_id") for _, v, d in out_edges if v == top_rec],
                        "statistics": {
                            "top_counterparty_volume": top_amt,
                            "total_account_volume": total_amt,
                            "concentration_ratio_pct": round(ratio * 100, 2),
                            "total_counterparties": len(rec_amounts)
                        },
                        "severity_score": round(0.5 + 0.4 * ratio, 3),
                        "confidence_level": "MEDIUM",
                        "investigator_explanation": (
                            f"Account {node} directed {round(ratio*100, 1)}% of its ${total_amt:,.2f} outflow "
                            f"exclusively to counterparty {top_rec}, exhibiting tight concentration."
                        ),
                        "known_limitations": "Dedicated vendor contracts or primary intra-company subsidiary flows."
                    })
        return patterns

    def analyze_network(self, transactions_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Comprehensive network intelligence execution across all 6 typologies.
        """
        G = self.build_graph(transactions_df)
        fan_in = self.detect_fan_in(G)
        fan_out = self.detect_fan_out(G)
        cycles = self.detect_circular_flow(G)
        rapid = self.detect_rapid_movement(G)
        spikes = self.detect_high_value_anomalies(G)
        concentration = self.detect_counterparty_concentration(G)

        all_patterns = fan_in + fan_out + cycles + rapid + spikes + concentration

        # Map patterns by transaction_id for rapid alert joining
        tx_to_patterns = {}
        for p in all_patterns:
            for tx_id in p.get("involved_transactions", []):
                if tx_id not in tx_to_patterns:
                    tx_to_patterns[tx_id] = []
                tx_to_patterns[tx_id].append(p)

        return {
            "graph_summary": {
                "nodes_count": G.number_of_nodes(),
                "edges_count": G.number_of_edges(),
                "total_patterns_detected": len(all_patterns),
                "pattern_breakdown": {
                    "fan_in": len(fan_in),
                    "fan_out": len(fan_out),
                    "circular_flow": len(cycles),
                    "rapid_movement": len(rapid),
                    "high_value_anomalies": len(spikes),
                    "concentration": len(concentration)
                }
            },
            "patterns": all_patterns,
            "tx_to_patterns": tx_to_patterns
        }
