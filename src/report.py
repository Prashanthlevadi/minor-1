"""
report.py - Report generation engine (JSON, Markdown, HTML export formats).
"""

import json
from datetime import datetime
from typing import Dict, Any
from src.comparator import ContradictionSummary
from src.claims import DocumentClaims


class ReportGenerator:
    """
    Generates structured reports for export and display.
    """

    @staticmethod
    def generate_json_report(
        doc_a_meta: Dict[str, Any],
        doc_b_meta: Dict[str, Any],
        claims_a: DocumentClaims,
        claims_b: DocumentClaims,
        summary: ContradictionSummary
    ) -> str:
        """
        Exports full audit report as JSON.
        """
        report_data = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "tool": "AI Contradiction Detector v1.0",
                "document_a": {
                    "filename": doc_a_meta.get("filename", "Doc_A"),
                    "total_claims": claims_a.total_claims,
                    "char_count": doc_a_meta.get("char_count", 0)
                },
                "document_b": {
                    "filename": doc_b_meta.get("filename", "Doc_B"),
                    "total_claims": claims_b.total_claims,
                    "char_count": doc_b_meta.get("char_count", 0)
                }
            },
            "summary": {
                "total_pairs_analyzed": summary.total_pairs_analyzed,
                "contradictions_found": summary.contradictions_found,
                "high_severity_count": summary.high_severity_count,
                "medium_severity_count": summary.medium_severity_count,
                "low_severity_count": summary.low_severity_count,
                "consistent_count": summary.consistent_count,
                "overall_consistency_score": summary.overall_consistency_score
            },
            "contradiction_results": [
                {
                    "pair_id": r.pair_id,
                    "severity": r.severity,
                    "category": r.category,
                    "is_contradiction": r.is_contradiction,
                    "conflict_detail": r.conflict_detail,
                    "claim_a": {
                        "id": r.claim_a.id,
                        "text": r.claim_a.text,
                        "source": r.claim_a.source_doc,
                        "entities": r.claim_a.key_entities
                    },
                    "claim_b": {
                        "id": r.claim_b.id,
                        "text": r.claim_b.text,
                        "source": r.claim_b.source_doc,
                        "entities": r.claim_b.key_entities
                    },
                    "explanation": r.explanation,
                    "recommendation": r.recommendation,
                    "confidence": r.confidence
                }
                for r in summary.results
            ]
        }
        return json.dumps(report_data, indent=2)

    @staticmethod
    def generate_markdown_report(
        doc_a_name: str,
        doc_b_name: str,
        summary: ContradictionSummary
    ) -> str:
        """
        Exports clean Markdown report.
        """
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        md = []
        md.append("# 🚨 AI Contradiction Detector - Audit Report")
        md.append(f"**Generated:** {now}")
        md.append(f"**Documents Compared:** `{doc_a_name}` vs `{doc_b_name}`\n")

        md.append("## 📊 Executive Summary")
        md.append(f"- **Overall Consistency Index:** `{summary.overall_consistency_score}%`")
        md.append(f"- **Total Claim Pairs Analyzed:** `{summary.total_pairs_analyzed}`")
        md.append(f"- **Total Contradictions Detected:** `{summary.contradictions_found}`")
        md.append(f"  - 🔴 **High Severity:** `{summary.high_severity_count}`")
        md.append(f"  - 🟡 **Medium Severity:** `{summary.medium_severity_count}`")
        md.append(f"  - 🔵 **Low Severity:** `{summary.low_severity_count}`")
        md.append(f"  - 🟢 **Consistent:** `{summary.consistent_count}`\n")

        md.append("## 🔍 Detailed Contradiction Breakdown\n")

        if not summary.results:
            md.append("*No claim pairs available for comparison.*")
        else:
            for idx, r in enumerate(summary.results, 1):
                badge = {
                    "HIGH": "🔴 HIGH CONTRADICTION",
                    "MEDIUM": "🟡 MEDIUM DISCREPANCY",
                    "LOW": "🔵 LOW DISTINCTION",
                    "CONSISTENT": "🟢 CONSISTENT"
                }.get(r.severity, r.severity)

                md.append(f"### {idx}. {badge} (Category: {r.category})")
                md.append(f"- **{doc_a_name}:** \"{r.claim_a.text}\"")
                md.append(f"- **{doc_b_name}:** \"{r.claim_b.text}\"")
                if r.conflict_detail:
                    md.append(f"- **Conflict Key:** `{r.conflict_detail}`")
                md.append(f"- **Explanation:** {r.explanation}")
                if r.recommendation:
                    md.append(f"- **Recommendation:** {r.recommendation}")
                md.append(f"- **Confidence Score:** `{int(r.confidence * 100)}%`\n")
                md.append("---")

        return "\n".join(md)

    @staticmethod
    def generate_html_report(
        doc_a_name: str,
        doc_b_name: str,
        summary: ContradictionSummary
    ) -> str:
        """
        Exports a self-contained HTML report with responsive modern CSS styling.
        """
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cards_html = ""
        for r in summary.results:
            color_map = {
                "HIGH": ("#ef4444", "#fef2f2", "#b91c1c"),
                "MEDIUM": ("#f59e0b", "#fffbeb", "#b45309"),
                "LOW": ("#3b82f6", "#eff6ff", "#1d4ed8"),
                "CONSISTENT": ("#10b981", "#ecfdf5", "#047857")
            }
            border_c, bg_c, text_c = color_map.get(r.severity, ("#6b7280", "#f9fafb", "#374151"))

            cards_html += f"""
            <div style="border-left: 5px solid {border_c}; background-color: {bg_c}; padding: 16px; margin-bottom: 16px; border-radius: 8px;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                    <span style="font-weight:bold; color: {text_c}; font-size: 14px;">[{r.severity}] {r.category}</span>
                    <span style="font-size:12px; color:#6b7280;">Confidence: {int(r.confidence*100)}%</span>
                </div>
                <div style="margin-bottom:6px;"><strong>{doc_a_name}:</strong> {r.claim_a.text}</div>
                <div style="margin-bottom:8px;"><strong>{doc_b_name}:</strong> {r.claim_b.text}</div>
                <div style="font-size:13px; color:#374151; background:#ffffff; padding:8px; border-radius:4px; margin-bottom:6px;">
                    <strong>Explanation:</strong> {r.explanation}
                </div>
                {f'<div style="font-size:12px; color:#6b7280;"><strong>Recommendation:</strong> {r.recommendation}</div>' if r.recommendation else ''}
            </div>
            """

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>AI Contradiction Detector Report</title>
            <style>
                body {{ font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; background: #f8fafc; color: #0f172a; padding: 24px; line-height: 1.5; }}
                .container {{ max-width: 900px; margin: 0 auto; background: #ffffff; padding: 32px; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }}
                .header {{ border-bottom: 2px solid #e2e8f0; padding-bottom: 16px; margin-bottom: 24px; }}
                .stats {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 24px; }}
                .stat-card {{ background: #f1f5f9; padding: 12px; border-radius: 8px; text-align: center; }}
                .stat-num {{ font-size: 24px; font-weight: bold; color: #1e293b; }}
                .stat-lbl {{ font-size: 12px; color: #64748b; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1 style="margin:0; color:#0f172a;">AI Contradiction Detector</h1>
                    <p style="margin:4px 0 0 0; color:#64748b;">Report Generated: {now} | Files: {doc_a_name} vs {doc_b_name}</p>
                </div>
                
                <div class="stats">
                    <div class="stat-card">
                        <div class="stat-num" style="color:#0284c7;">{summary.overall_consistency_score}%</div>
                        <div class="stat-lbl">Consistency Index</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-num" style="color:#dc2626;">{summary.high_severity_count}</div>
                        <div class="stat-lbl">High Contradictions</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-num" style="color:#d97706;">{summary.medium_severity_count}</div>
                        <div class="stat-lbl">Medium Discrepancies</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-num" style="color:#16a34a;">{summary.consistent_count}</div>
                        <div class="stat-lbl">Consistent Pairs</div>
                    </div>
                </div>

                <h2>Detailed Comparison Findings</h2>
                {cards_html}
            </div>
        </body>
        </html>
        """
        return html
