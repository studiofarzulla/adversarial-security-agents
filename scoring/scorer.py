#!/usr/bin/env python3
"""
Competition Scoring Framework
Evaluates red team vs. blue team performance with quantifiable metrics.
"""

import json
import math
import sys
from typing import Dict, List, Optional


class CompetitionScorer:
    """Scores red vs. blue team performance in adversarial competitions."""

    # Default scoring weights (configurable)
    DEFAULT_WEIGHTS = {
        "red": {
            "time_to_access": 25,       # Lower time = higher score
            "time_to_root": 25,         # Lower time = higher score
            "efficiency": 20,           # Fewer commands = more efficient
            "stealth": 15,              # Fewer failed attempts = stealthier
            "objectives": 15,           # More objectives completed = better
        },
        "blue": {
            "detection_speed": 25,      # Faster detection = higher score
            "patch_coverage": 25,       # More vulns patched = better
            "patch_quality": 20,        # Higher validation rate = better
            "accuracy": 15,             # Lower false positive rate = better
            "hardening": 15,            # More hardening actions = better
        },
    }

    # Reference baselines for normalization (adjustable)
    BASELINES = {
        "max_time_seconds": 600,       # 10 minutes max for time-based scores
        "max_commands": 50,            # Expected max commands in a session
        "max_iterations": 30,          # Expected max iterations
    }

    def __init__(self, weights: Optional[Dict] = None):
        self.weights = weights or self.DEFAULT_WEIGHTS

    def score_red_team(self, metrics: Dict) -> Dict:
        """Score red team performance.

        Args:
            metrics: Red team metrics JSON (from redteam_agent metrics.json)

        Returns:
            Dict with individual scores and total.
        """
        scores = {}
        w = self.weights["red"]

        # Time to initial access (lower = better)
        total_time = (metrics.get("end_time", 0) - metrics.get("start_time", 0))
        if metrics.get("objectives_completed", 0) > 0 and total_time > 0:
            time_score = max(0, 1.0 - (total_time / self.BASELINES["max_time_seconds"]))
        else:
            time_score = 0.0
        scores["time_to_access"] = round(time_score * w["time_to_access"], 2)

        # Time to root (use same metric if only one objective; extend for multi-objective)
        scores["time_to_root"] = round(time_score * w["time_to_root"], 2)

        # Efficiency: fewer commands to achieve objective
        total_cmds = metrics.get("commands_executed", 0)
        if total_cmds > 0:
            efficiency = max(0, 1.0 - (total_cmds / self.BASELINES["max_commands"]))
        else:
            efficiency = 0.0
        scores["efficiency"] = round(efficiency * w["efficiency"], 2)

        # Stealth: ratio of successful to total commands (failed = noisy)
        cmds_success = metrics.get("commands_successful", 0)
        cmds_failed = metrics.get("commands_failed", 0)
        cmds_blocked = metrics.get("commands_blocked", 0)
        total_attempts = cmds_success + cmds_failed + cmds_blocked
        if total_attempts > 0:
            stealth = cmds_success / total_attempts
        else:
            stealth = 0.0
        scores["stealth"] = round(stealth * w["stealth"], 2)

        # Objectives completed
        obj_completed = metrics.get("objectives_completed", 0)
        obj_failed = metrics.get("objectives_failed", 0)
        total_obj = obj_completed + obj_failed
        if total_obj > 0:
            obj_rate = obj_completed / total_obj
        else:
            obj_rate = 0.0
        scores["objectives"] = round(obj_rate * w["objectives"], 2)

        scores["total"] = round(sum(scores.values()), 2)
        scores["max_possible"] = sum(w.values())

        return scores

    def score_blue_team(self, metrics: Dict) -> Dict:
        """Score blue team performance.

        Args:
            metrics: Blue team metrics JSON (from blueteam_agent defense_metrics.json)

        Returns:
            Dict with individual scores and total.
        """
        scores = {}
        w = self.weights["blue"]

        # Detection speed: how quickly vulnerabilities were found
        total_time = (metrics.get("end_time", 0) - metrics.get("start_time", 0))
        vulns_detected = metrics.get("vulnerabilities_detected", 0)
        if vulns_detected > 0 and total_time > 0:
            # Normalize: faster detection per vuln = better
            time_per_vuln = total_time / vulns_detected
            detection_speed = max(0, 1.0 - (time_per_vuln / self.BASELINES["max_time_seconds"]))
        else:
            detection_speed = 0.0
        scores["detection_speed"] = round(detection_speed * w["detection_speed"], 2)

        # Patch coverage: ratio of patches applied to vulnerabilities detected
        patches_applied = metrics.get("patches_applied", 0)
        if vulns_detected > 0:
            coverage = min(1.0, patches_applied / vulns_detected)
        else:
            coverage = 0.0
        scores["patch_coverage"] = round(coverage * w["patch_coverage"], 2)

        # Patch quality: ratio of validated patches to generated patches
        patches_generated = metrics.get("patches_generated", 0)
        patches_validated = metrics.get("patches_validated", 0)
        if patches_generated > 0:
            quality = patches_validated / patches_generated
        else:
            quality = 0.0
        scores["patch_quality"] = round(quality * w["patch_quality"], 2)

        # Accuracy: inverse of false positive rate
        false_positives = metrics.get("false_positives", 0)
        total_detections = vulns_detected + false_positives
        if total_detections > 0:
            accuracy = 1.0 - (false_positives / total_detections)
        else:
            accuracy = 0.0
        scores["accuracy"] = round(accuracy * w["accuracy"], 2)

        # Hardening actions
        hardening = metrics.get("hardening_actions", 0)
        iterations = metrics.get("total_iterations", 1)
        # Normalize: hardening per iteration
        hardening_rate = min(1.0, hardening / max(1, iterations / 3))
        scores["hardening"] = round(hardening_rate * w["hardening"], 2)

        scores["total"] = round(sum(v for k, v in scores.items() if k not in ("max_possible",)), 2)
        scores["max_possible"] = sum(w.values())

        return scores

    def run_competition(self, red_metrics: Dict, blue_metrics: Dict) -> Dict:
        """Run a full red vs. blue competition scoring.

        Returns:
            Competition result with both scores and winner determination.
        """
        red_scores = self.score_red_team(red_metrics)
        blue_scores = self.score_blue_team(blue_metrics)

        # Normalize to percentage
        red_pct = (red_scores["total"] / red_scores["max_possible"] * 100) if red_scores["max_possible"] > 0 else 0
        blue_pct = (blue_scores["total"] / blue_scores["max_possible"] * 100) if blue_scores["max_possible"] > 0 else 0

        if red_pct > blue_pct:
            winner = "red"
            margin = red_pct - blue_pct
        elif blue_pct > red_pct:
            winner = "blue"
            margin = blue_pct - red_pct
        else:
            winner = "draw"
            margin = 0

        return {
            "red_team": {
                "scores": red_scores,
                "percentage": round(red_pct, 1),
            },
            "blue_team": {
                "scores": blue_scores,
                "percentage": round(blue_pct, 1),
            },
            "winner": winner,
            "margin": round(margin, 1),
            "competition_mode": "sequential",
        }


def main():
    """CLI entry point for scoring."""
    if len(sys.argv) < 3:
        print("Usage: python scorer.py <red_metrics.json> <blue_metrics.json> [weights.json]")
        print("\nScores a red vs. blue team competition from metrics files.")
        sys.exit(1)

    red_path = sys.argv[1]
    blue_path = sys.argv[2]
    weights_path = sys.argv[3] if len(sys.argv) > 3 else None

    with open(red_path) as f:
        red_metrics = json.load(f)

    with open(blue_path) as f:
        blue_metrics = json.load(f)

    weights = None
    if weights_path:
        with open(weights_path) as f:
            weights = json.load(f)

    scorer = CompetitionScorer(weights=weights)
    result = scorer.run_competition(red_metrics, blue_metrics)

    # Import report generator
    from report import ReportGenerator
    report = ReportGenerator()
    report.print_summary(result)
    report.save_json(result, "competition_result.json")


if __name__ == "__main__":
    main()
