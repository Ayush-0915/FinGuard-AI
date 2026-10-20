"""
FinGuard AI — Phase 3: Risk Fusion Engine
Combines multi-modal risk signals into an operational priority score:
- Statistical Model Probability (LightGBM)
- Graph Typology Severity (NetworkX)
- Behavioral Anomaly Score (Velocity, fan-in/fan-out deviations)
- Rule-Based Indicators (High value, cross-border conversion)

Strictly preserves:
- Separation of calibrated model probability from fused priority score
- Explicit weight normalization and configurable signal weights
- Robust handling of missing signals without double counting
- Non-probability priority ranking semantics
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional

DEFAULT_FUSION_WEIGHTS = {
    "model": 0.50,
    "graph": 0.25,
    "behavior": 0.15,
    "rule": 0.10
}

class RiskFusionEngine:
    def __init__(self, weights: Optional[Dict[str, float]] = None):
        """
        Initializes the Risk Fusion Engine.
        Weights are automatically normalized to sum to 1.0.
        """
        raw_weights = weights or DEFAULT_FUSION_WEIGHTS.copy()
        total_w = sum(raw_weights.values())
        if total_w <= 0:
            raise ValueError("Sum of fusion weights must be strictly positive.")
        self.weights = {k: v / total_w for k, v in raw_weights.items()}

    def compute_behavioral_score(self, features: Dict[str, Any]) -> float:
        """
        Computes a normalized [0, 1] behavioral anomaly score from point-in-time features.
        """
        if not features:
            return 0.0

        score = 0.0

        # Rapid velocity burst: seconds_since_previous <= 300s
        sec_prev = float(features.get("seconds_since_previous", 999999.0))
        if 0 < sec_prev <= 60.0:
            score += 0.40
        elif 0 < sec_prev <= 300.0:
            score += 0.25
        elif 0 < sec_prev <= 900.0:
            score += 0.10

        # Counterparty diversity: high unique senders or unique receivers
        rec_senders = int(features.get("receiver_unique_senders", 0))
        if rec_senders >= 10:
            score += 0.35
        elif rec_senders >= 5:
            score += 0.20

        snd_receivers = int(features.get("sender_unique_receivers", 0))
        if snd_receivers >= 10:
            score += 0.35
        elif snd_receivers >= 5:
            score += 0.20

        # Account activity count
        snd_cnt = int(features.get("sender_transaction_count", 0))
        if snd_cnt >= 20:
            score += 0.15

        return min(1.0, round(score, 4))

    def compute_rule_score(self, transaction: Dict[str, Any], features: Optional[Dict[str, Any]] = None) -> float:
        """
        Computes a normalized [0, 1] rule-based heuristic score.
        """
        score = 0.0
        amt = float(transaction.get("amount", transaction.get("Amount Paid", transaction.get("amount_paid", 0.0))))

        # High amount rule
        if amt >= 50000.0:
            score += 0.50
        elif amt >= 10000.0:
            score += 0.30

        # Currency mismatch rule
        if features:
            curr_match = features.get("currency_match", 1)
            if curr_match == 0:
                score += 0.30
            # Same bank internal transfer vs cross bank
            same_b = features.get("same_bank", 0)
            if same_b == 0:
                score += 0.10

        # Payment format rule
        fmt = str(transaction.get("payment_format", transaction.get("Payment Format", "")))
        if fmt.lower() in ["wire", "bitcoin", "cash"]:
            score += 0.15

        return min(1.0, round(score, 4))

    def compute_graph_score(self, graph_patterns: Optional[List[Dict[str, Any]]]) -> float:
        """
        Computes a normalized [0, 1] composite graph typology severity score.
        """
        if not graph_patterns:
            return 0.0

        severities = [p.get("severity_score", 0.5) for p in graph_patterns]
        # Diminishing returns combination: 1 - prod(1 - s_i)
        comb = 1.0
        for s in severities:
            comb *= (1.0 - min(0.95, s))
        return min(1.0, round(1.0 - comb, 4))

    def fuse_risk(
        self,
        model_prob: float,
        transaction: Dict[str, Any],
        features: Optional[Dict[str, Any]] = None,
        graph_patterns: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Fuses multi-modal signals into a single priority score.
        
        Returns:
        --------
        dict containing:
        - raw_model_probability: float
        - fused_priority_score: float
        - component_scores: dict
        - active_weights: dict
        """
        s_model = float(np.clip(model_prob, 0.0, 1.0))
        s_behavior = self.compute_behavioral_score(features or {})
        s_graph = self.compute_graph_score(graph_patterns)
        s_rule = self.compute_rule_score(transaction, features)

        scores = {
            "model": s_model,
            "graph": s_graph,
            "behavior": s_behavior,
            "rule": s_rule
        }

        # Dynamic weight normalization: if graph patterns are unavailable (None),
        # renormalize remaining weights so missing signals do not artificially penalize score
        active_w = self.weights.copy()
        if graph_patterns is None:
            # Drop graph from active weights and renormalize
            active_w.pop("graph", None)
            total_active = sum(active_w.values())
            active_w = {k: v / total_active for k, v in active_w.items()}

        fused = sum(active_w[k] * scores[k] for k in active_w)
        fused = float(np.clip(fused, 0.0, 1.0))

        return {
            "raw_model_probability": s_model,
            "fused_priority_score": round(fused, 4),
            "component_scores": {k: round(v, 4) for k, v in scores.items()},
            "active_weights": {k: round(v, 4) for k, v in active_w.items()},
            "disclaimer": "fused_priority_score is an operational triage metric, not a calibrated posterior probability."
        }
