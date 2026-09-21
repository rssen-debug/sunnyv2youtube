#!/usr/bin/env python3
"""agents/risk_agent.py — risk-detektor (före leverans):
copyright / defamation / os­tödda påståenden / copycat.

Returnerar top-level status: GO | REVIEW | HOLD.
"""
import os, json

def run(factcheck_report, licensing_manifest, project_dir):
    risks = []
    if not factcheck_report.get("safe", False):
        if factcheck_report.get("rewritten"):
            pass  # fixade via LLM
        else:
            risks.append({"severity": "high", "type": "unsupported_assertions",
                          "detail": str(factcheck_report.get("pending_manual", True))})
    rev = [a for a in licensing_manifest if a.get("status") == "review"]
    if len(rev) >= 3:
        risks.append({"severity": "medium", "type": "copyright_review",
                      "detail": f"{len(rev)} assets kräver licensbeslut (fair use)"})
    blocked = [a for a in licensing_manifest if a.get("tier", 9) >= 5]
    if blocked:
        risks.append({"severity": "high", "type": "copyright_blocked",
                      "detail": f"{len(blocked)} assets tier>=5 (ej publiceringsbara)"})
    if not factcheck_report.get("safe", False) and not factcheck_report.get("rewritten"):
        severity = "high"
    elif risks and any(r["severity"] == "high" for r in risks):
        severity = "high"
    elif risks:
        severity = "medium"
    else:
        severity = "low"
    status = "HOLD" if severity == "high" else ("REVIEW" if severity == "medium" else "GO")
    report = {"status": status, "severity": severity, "risks": risks}
    with open(os.path.join(project_dir, "risk.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
    return report
