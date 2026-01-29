#!/usr/bin/env python3
"""
Competition Report Generator
Produces formatted text and JSON reports from competition scoring results.
"""

import json
from datetime import datetime
from typing import Dict


class ReportGenerator:
    """Generates formatted competition reports."""

    def print_summary(self, result: Dict):
        """Print a formatted competition summary to stdout."""
        red = result["red_team"]
        blue = result["blue_team"]

        print()
        print("=" * 70)
        print("         ADVERSARIAL SECURITY COMPETITION - RESULTS")
        print("=" * 70)
        print(f"  Mode: {result['competition_mode'].upper()}")
        print(f"  Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
        print()

        # Red team
        print("-" * 70)
        print("  RED TEAM (Offensive)")
        print("-" * 70)
        rs = red["scores"]
        print(f"  Time to Access:    {rs['time_to_access']:6.2f} / {result['red_team']['scores'].get('max_possible', 100) * 0.25:.0f}")
        print(f"  Time to Root:      {rs['time_to_root']:6.2f} / {result['red_team']['scores'].get('max_possible', 100) * 0.25:.0f}")
        print(f"  Efficiency:        {rs['efficiency']:6.2f} / {result['red_team']['scores'].get('max_possible', 100) * 0.20:.0f}")
        print(f"  Stealth:           {rs['stealth']:6.2f} / {result['red_team']['scores'].get('max_possible', 100) * 0.15:.0f}")
        print(f"  Objectives:        {rs['objectives']:6.2f} / {result['red_team']['scores'].get('max_possible', 100) * 0.15:.0f}")
        print(f"  {'-' * 36}")
        print(f"  TOTAL:             {rs['total']:6.2f} / {rs['max_possible']}")
        print(f"  PERCENTAGE:        {red['percentage']:5.1f}%")
        print()

        # Blue team
        print("-" * 70)
        print("  BLUE TEAM (Defensive)")
        print("-" * 70)
        bs = blue["scores"]
        print(f"  Detection Speed:   {bs['detection_speed']:6.2f} / {result['blue_team']['scores'].get('max_possible', 100) * 0.25:.0f}")
        print(f"  Patch Coverage:    {bs['patch_coverage']:6.2f} / {result['blue_team']['scores'].get('max_possible', 100) * 0.25:.0f}")
        print(f"  Patch Quality:     {bs['patch_quality']:6.2f} / {result['blue_team']['scores'].get('max_possible', 100) * 0.20:.0f}")
        print(f"  Accuracy:          {bs['accuracy']:6.2f} / {result['blue_team']['scores'].get('max_possible', 100) * 0.15:.0f}")
        print(f"  Hardening:         {bs['hardening']:6.2f} / {result['blue_team']['scores'].get('max_possible', 100) * 0.15:.0f}")
        print(f"  {'-' * 36}")
        print(f"  TOTAL:             {bs['total']:6.2f} / {bs['max_possible']}")
        print(f"  PERCENTAGE:        {blue['percentage']:5.1f}%")
        print()

        # Winner
        print("=" * 70)
        winner = result["winner"]
        margin = result["margin"]
        if winner == "red":
            print(f"  WINNER: RED TEAM (Offense wins by {margin:.1f}%)")
            print("  The attackers breached defenses faster than the defenders could patch.")
        elif winner == "blue":
            print(f"  WINNER: BLUE TEAM (Defense wins by {margin:.1f}%)")
            print("  The defenders detected and patched vulnerabilities effectively.")
        else:
            print("  RESULT: DRAW")
            print("  Red and blue teams performed equally.")
        print("=" * 70)
        print()

    def save_json(self, result: Dict, filepath: str):
        """Save competition result as JSON."""
        output = {
            "metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "framework_version": "1.0.0",
            },
            "result": result,
        }
        with open(filepath, 'w') as f:
            json.dump(output, f, indent=2)
        print(f"[REPORT] Saved to {filepath}")

    def generate_markdown(self, result: Dict) -> str:
        """Generate a Markdown-formatted report."""
        red = result["red_team"]
        blue = result["blue_team"]
        rs = red["scores"]
        bs = blue["scores"]

        lines = [
            "# Adversarial Security Competition Report",
            "",
            f"**Date**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
            f"**Mode**: {result['competition_mode']}",
            "",
            "## Red Team (Offensive)",
            "",
            "| Metric | Score | Weight |",
            "|--------|------:|-------:|",
            f"| Time to Access | {rs['time_to_access']:.2f} | 25 |",
            f"| Time to Root | {rs['time_to_root']:.2f} | 25 |",
            f"| Efficiency | {rs['efficiency']:.2f} | 20 |",
            f"| Stealth | {rs['stealth']:.2f} | 15 |",
            f"| Objectives | {rs['objectives']:.2f} | 15 |",
            f"| **Total** | **{rs['total']:.2f}** | **{rs['max_possible']}** |",
            f"| **Percentage** | **{red['percentage']:.1f}%** | |",
            "",
            "## Blue Team (Defensive)",
            "",
            "| Metric | Score | Weight |",
            "|--------|------:|-------:|",
            f"| Detection Speed | {bs['detection_speed']:.2f} | 25 |",
            f"| Patch Coverage | {bs['patch_coverage']:.2f} | 25 |",
            f"| Patch Quality | {bs['patch_quality']:.2f} | 20 |",
            f"| Accuracy | {bs['accuracy']:.2f} | 15 |",
            f"| Hardening | {bs['hardening']:.2f} | 15 |",
            f"| **Total** | **{bs['total']:.2f}** | **{bs['max_possible']}** |",
            f"| **Percentage** | **{blue['percentage']:.1f}%** | |",
            "",
            "## Result",
            "",
        ]

        winner = result["winner"]
        margin = result["margin"]
        if winner == "red":
            lines.append(f"**Winner: Red Team** (offense wins by {margin:.1f}%)")
        elif winner == "blue":
            lines.append(f"**Winner: Blue Team** (defense wins by {margin:.1f}%)")
        else:
            lines.append("**Result: Draw**")

        return "\n".join(lines)
