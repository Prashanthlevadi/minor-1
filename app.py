"""
app.py - AI Contradiction Detector Streamlit Application with Premium UI/UX.
"""

import os
import sys
import json
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from dotenv import load_dotenv

# Ensure root directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.pdf_reader import PDFReader, load_document
from src.cleaner import TextCleaner
from src.claims import ClaimExtractor, DocumentClaims
from src.matcher import ClaimMatcher, ClaimPair
from src.comparator import ContradictionComparator, ContradictionSummary
from src.report import ReportGenerator

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="AI Contradiction Detector",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern UI/UX
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }

    /* Main Container Padding */
    .block-container {
        padding-top: 1.8rem;
        padding-bottom: 2rem;
    }

    /* Header Banner */
    .main-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%);
        color: #ffffff;
        padding: 24px 32px;
        border-radius: 16px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.2);
        margin-bottom: 24px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .main-header h1 {
        color: #ffffff !important;
        font-weight: 700;
        font-size: 2.2rem;
        margin: 0 0 6px 0;
        letter-spacing: -0.5px;
    }
    
    .main-header p {
        color: #94a3b8;
        font-size: 1.05rem;
        margin: 0;
    }

    /* Roadmap Stepper */
    .stepper-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        padding: 12px 20px;
        border-radius: 12px;
        margin-bottom: 24px;
    }
    .stepper-step {
        flex: 1;
        text-align: center;
        padding: 8px 12px;
        font-weight: 600;
        font-size: 0.82rem;
        border-radius: 8px;
        color: #64748b;
        background: #ffffff;
        border: 1px solid #cbd5e1;
        margin: 0 4px;
        transition: all 0.2s ease;
    }
    .stepper-step.active {
        background: #2563eb;
        color: #ffffff;
        border-color: #2563eb;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.25);
    }

    /* Metric Card Styling */
    .metric-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.06);
    }
    .metric-val {
        font-size: 2.2rem;
        font-weight: 700;
        line-height: 1.1;
        margin-bottom: 4px;
    }
    .metric-lbl {
        font-size: 0.85rem;
        color: #64748b;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* Severity Badges */
    .badge-high {
        background: #fef2f2;
        color: #dc2626;
        border: 1px solid #fca5a5;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.78rem;
    }
    .badge-medium {
        background: #fffbeb;
        color: #d97706;
        border: 1px solid #fcd34d;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.78rem;
    }
    .badge-low {
        background: #eff6ff;
        color: #2563eb;
        border: 1px solid #93c5fd;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.78rem;
    }
    .badge-consistent {
        background: #ecfdf5;
        color: #16a34a;
        border: 1px solid #86efac;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.78rem;
    }

    /* Card Containers */
    .claim-card {
        background: #ffffff;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        padding: 20px;
        margin-bottom: 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.02);
    }
    
    .conflict-box {
        background: #fff1f2;
        border-left: 4px solid #f43f5e;
        padding: 12px 16px;
        border-radius: 6px;
        margin: 12px 0;
        font-size: 0.9rem;
        color: #9f1239;
    }

    .recommendation-box {
        background: #f0fdf4;
        border-left: 4px solid #22c55e;
        padding: 10px 14px;
        border-radius: 6px;
        margin-top: 10px;
        font-size: 0.88rem;
        color: #14532d;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    base_dir = os.path.join(os.path.dirname(__file__), "data", "samples")
    if "doc_a" not in st.session_state or st.session_state.doc_a is None:
        path_a = os.path.join(base_dir, "sample_contract_v1.pdf")
        if not os.path.exists(path_a):
            path_a = os.path.join(base_dir, "sample_contract_v1.txt")
        st.session_state.doc_a = load_document(path_a, "sample_contract_v1.pdf")

    if "doc_b" not in st.session_state or st.session_state.doc_b is None:
        path_b = os.path.join(base_dir, "sample_contract_v2.pdf")
        if not os.path.exists(path_b):
            path_b = os.path.join(base_dir, "sample_contract_v2.txt")
        st.session_state.doc_b = load_document(path_b, "sample_contract_v2.pdf")

    if "analysis_results" not in st.session_state:
        st.session_state.analysis_results = None


def load_sample_pair(sample_type: str):
    base_dir = os.path.join(os.path.dirname(__file__), "data", "samples")

    if sample_type == "contract":
        path_a = os.path.join(base_dir, "sample_contract_v1.pdf")
        path_b = os.path.join(base_dir, "sample_contract_v2.pdf")
        name_a, name_b = "sample_contract_v1.pdf", "sample_contract_v2.pdf"
    elif sample_type == "policy":
        path_a = os.path.join(base_dir, "sample_policy_2023.pdf")
        path_b = os.path.join(base_dir, "sample_policy_2024.pdf")
        name_a, name_b = "sample_policy_2023.pdf", "sample_policy_2024.pdf"
    else:
        path_a = os.path.join(base_dir, "sample_contract_v1.pdf")
        path_b = os.path.join(base_dir, "sample_contract_v2.pdf")
        name_a, name_b = "sample_contract_v1.pdf", "sample_contract_v2.pdf"

    doc_a = load_document(path_a, name_a)
    doc_b = load_document(path_b, name_b)

    st.session_state.doc_a = doc_a
    st.session_state.doc_b = doc_b
    st.session_state.analysis_results = None
    st.rerun()


def main():
    init_session_state()

    # App Header
    st.markdown("""
    <div class="main-header">
        <h1>🚨 AI Contradiction Detector</h1>
        <p>Automated Factual, Legal & Policy Contradiction Audit Engine powered by LLMs & Pydantic Validation</p>
    </div>
    """, unsafe_allow_html=True)

    # 5-Step Progress Roadmap Stepper
    st.markdown("""
    <div class="stepper-container">
        <div class="stepper-step active">1. UNDERSTAND</div>
        <div class="stepper-step active">2. DESIGN</div>
        <div class="stepper-step active">3. BUILD</div>
        <div class="stepper-step active">4. TEST</div>
        <div class="stepper-step active">5. DEPLOY</div>
    </div>
    """, unsafe_allow_html=True)

    # Sidebar Controls
    with st.sidebar:
        st.header("⚙️ Configuration & Settings")

        provider = st.selectbox(
            "AI Provider Engine",
            ["auto", "gemini", "openai", "heuristic"],
            format_func=lambda x: {
                "auto": "⚡ Auto-Detect (Gemini / OpenAI / NLP)",
                "gemini": "✨ Google Gemini API",
                "openai": "🤖 OpenAI GPT API",
                "heuristic": "🛠️ Offline Rule-Based NLP Engine"
            }.get(x, x),
            help="Select preferred AI analysis backend."
        )

        api_key_input = st.text_input(
            "API Key (Optional)",
            type="password",
            value=os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY") or "",
            help="Enter your Gemini or OpenAI API key. Leave blank to use offline heuristic NLP engine."
        )

        if api_key_input:
            st.success("🔑 API Key configured.")
        else:
            st.info("💡 Running in high-precision Offline NLP mode.")

        st.divider()
        st.subheader("🔍 Matching Thresholds")
        similarity_threshold = st.slider(
            "Min Match Similarity",
            min_value=0.05,
            max_value=0.50,
            value=0.12,
            step=0.01,
            help="Threshold for pairing statements across documents."
        )

        st.divider()
        st.markdown("### 📋 Sample PDF Loader")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("📄 Contract PDFs", use_container_width=True):
                load_sample_pair("contract")
        with c2:
            if st.button("🏢 Policy PDFs", use_container_width=True):
                load_sample_pair("policy")

    # Document Input Section
    st.subheader("📁 Step 1: Supply Documents for Contradiction Analysis")

    # Active Document Banner
    if st.session_state.doc_a and st.session_state.doc_b:
        ac1, ac2 = st.columns(2)
        with ac1:
            st.success(f"🟢 **Document A Active:** `{st.session_state.doc_a.get('filename')}` ({st.session_state.doc_a.get('char_count')} chars)")
        with ac2:
            st.success(f"🟢 **Document B Active:** `{st.session_state.doc_b.get('filename')}` ({st.session_state.doc_b.get('char_count')} chars)")

    input_tabs = st.tabs(["📦 Loaded Sample PDFs", "📤 Upload Custom Files (PDF / TXT)", "✍️ Direct Text Input"])

    with input_tabs[0]:
        if st.session_state.doc_a and st.session_state.doc_b:
            col_s1, col_s2 = st.columns(2)
            with col_s1:
                st.markdown(f"##### Document A Preview: `{st.session_state.doc_a.get('filename')}`")
                st.text_area("Doc A Extracted Text", st.session_state.doc_a.get("full_text", ""), height=160, disabled=True, key="preview_a")
            with col_s2:
                st.markdown(f"##### Document B Preview: `{st.session_state.doc_b.get('filename')}`")
                st.text_area("Doc B Extracted Text", st.session_state.doc_b.get("full_text", ""), height=160, disabled=True, key="preview_b")
        else:
            st.info("Click one of the sample buttons in the sidebar to load test documents.")

    with input_tabs[1]:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("##### Upload Document A (PDF / TXT)")
            file_a = st.file_uploader("Upload PDF or TXT for Document A", type=["pdf", "txt", "md"], key="file_a")
            if file_a:
                st.session_state.doc_a = load_document(file_a.read(), file_a.name)
                st.success(f"Uploaded & Parsed: `{file_a.name}` ({st.session_state.doc_a.get('char_count', 0)} chars)")

        with col2:
            st.markdown("##### Upload Document B (PDF / TXT)")
            file_b = st.file_uploader("Upload PDF or TXT for Document B", type=["pdf", "txt", "md"], key="file_b")
            if file_b:
                st.session_state.doc_b = load_document(file_b.read(), file_b.name)
                st.success(f"Uploaded & Parsed: `{file_b.name}` ({st.session_state.doc_b.get('char_count', 0)} chars)")

    with input_tabs[2]:
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            text_a_input = st.text_area("Paste Document A Content", height=200, key="text_a_input")
            if st.button("Save Document A Text"):
                if text_a_input.strip():
                    st.session_state.doc_a = load_document(text_a_input, "Document_A.txt")
                    st.success("Document A text updated!")
        with col_t2:
            text_b_input = st.text_area("Paste Document B Content", height=200, key="text_b_input")
            if st.button("Save Document B Text"):
                if text_b_input.strip():
                    st.session_state.doc_b = load_document(text_b_input, "Document_B.txt")
                    st.success("Document B text updated!")

    st.divider()

    # Trigger Analysis Button
    run_disabled = not (st.session_state.doc_a and st.session_state.doc_b)

    if st.button("⚡ Run Full AI Contradiction Detector Audit", type="primary", use_container_width=True, disabled=run_disabled):
        with st.spinner("🔍 Processing pipeline: Cleaning text -> Extracting Pydantic Claims -> Aligning Pairs -> Detecting Contradictions..."):

            # Step 1: Preprocessing
            doc_a_clean = TextCleaner.prepare_for_analysis(st.session_state.doc_a)
            doc_b_clean = TextCleaner.prepare_for_analysis(st.session_state.doc_b)

            # Step 2: Claim Extraction
            claims_a = ClaimExtractor.extract_claims(
                text=doc_a_clean["cleaned_text"],
                doc_name=doc_a_clean.get("filename", "Doc A"),
                provider=provider,
                api_key=api_key_input
            )

            claims_b = ClaimExtractor.extract_claims(
                text=doc_b_clean["cleaned_text"],
                doc_name=doc_b_clean.get("filename", "Doc B"),
                provider=provider,
                api_key=api_key_input
            )

            # Step 3: Claim Matching
            pairs = ClaimMatcher.match_claims(claims_a, claims_b, min_threshold=similarity_threshold)

            # Step 4: Contradiction Analysis
            summary = ContradictionComparator.compare_pairs(
                pairs=pairs,
                provider=provider,
                api_key=api_key_input
            )

            # Store in session state
            st.session_state.analysis_results = {
                "doc_a_meta": doc_a_clean,
                "doc_b_meta": doc_b_clean,
                "claims_a": claims_a,
                "claims_b": claims_b,
                "summary": summary
            }

            st.toast("Audit complete! Results loaded below.", icon="✅")

    # Display Analysis Dashboard
    if st.session_state.analysis_results:
        res = st.session_state.analysis_results
        summary: ContradictionSummary = res["summary"]
        claims_a: DocumentClaims = res["claims_a"]
        claims_b: DocumentClaims = res["claims_b"]

        st.subheader("📊 Step 2: Audit Summary & Metrics")

        # Top Executive Metrics Row
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-val" style="color: #2563eb;">{summary.overall_consistency_score}%</div>
                <div class="metric-lbl">Consistency Index</div>
            </div>
            """, unsafe_allow_html=True)
        with m2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-val" style="color: #dc2626;">{summary.high_severity_count}</div>
                <div class="metric-lbl">High Contradictions</div>
            </div>
            """, unsafe_allow_html=True)
        with m3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-val" style="color: #d97706;">{summary.medium_severity_count}</div>
                <div class="metric-lbl">Medium Discrepancies</div>
            </div>
            """, unsafe_allow_html=True)
        with m4:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-val" style="color: #16a34a;">{summary.consistent_count}</div>
                <div class="metric-lbl">Consistent Pairs</div>
            </div>
            """, unsafe_allow_html=True)

        st.write("")

        # Visual Charts Section
        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            st.markdown("##### 🍩 Contradiction Severity Breakdown")
            severity_labels = ["High Contradiction", "Medium Discrepancy", "Low Distinction", "Consistent"]
            severity_counts = [
                summary.high_severity_count,
                summary.medium_severity_count,
                summary.low_severity_count,
                summary.consistent_count
            ]
            fig_donut = go.Figure(data=[go.Pie(
                labels=severity_labels,
                values=severity_counts,
                hole=0.55,
                marker=dict(colors=["#ef4444", "#f59e0b", "#3b82f6", "#10b981"])
            )])
            fig_donut.update_layout(margin=dict(t=20, b=20, l=20, r=20), height=280)
            st.plotly_chart(fig_donut, use_container_width=True)

        with chart_col2:
            st.markdown("##### 🏷️ Contradictions by Category")
            categories = [r.category for r in summary.results]
            cat_counts = {}
            for c in categories:
                cat_counts[c] = cat_counts.get(c, 0) + 1

            cat_keys = list(cat_counts.keys())
            cat_vals = list(cat_counts.values())
            colors = ["#3b82f6", "#8b5cf6", "#ec4899", "#f59e0b", "#10b981", "#6366f1"]

            fig_bar = go.Figure(data=[go.Bar(
                x=cat_keys,
                y=cat_vals,
                marker=dict(color=colors[:len(cat_keys)])
            )])
            fig_bar.update_layout(
                margin=dict(t=20, b=20, l=20, r=20),
                height=280,
                xaxis_title="Category",
                yaxis_title="Count"
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        st.divider()

        # Detailed Explorer Section
        st.subheader("🔍 Step 3: Detailed Side-by-Side Claim Explorer")

        # Filters
        filter_col1, filter_col2, filter_col3 = st.columns([2, 2, 3])
        with filter_col1:
            severity_filter = st.multiselect(
                "Filter by Severity",
                ["HIGH", "MEDIUM", "LOW", "CONSISTENT"],
                default=["HIGH", "MEDIUM", "LOW", "CONSISTENT"]
            )
        with filter_col2:
            all_cats = list(set(r.category for r in summary.results))
            cat_filter = st.multiselect("Filter by Category", all_cats, default=all_cats)
        with filter_col3:
            search_query = st.text_input("🔍 Search within claims or explanations", "")

        # Render Claim Pairs
        filtered_results = [
            r for r in summary.results
            if r.severity in severity_filter and r.category in cat_filter
            and (not search_query or search_query.lower() in r.claim_a.text.lower()
                 or search_query.lower() in r.claim_b.text.lower()
                 or search_query.lower() in r.explanation.lower())
        ]

        st.caption(f"Displaying **{len(filtered_results)}** of {len(summary.results)} total analyzed claim pairs.")

        for idx, r in enumerate(filtered_results, 1):
            badge_class = f"badge-{r.severity.lower()}"
            badge_label = {
                "HIGH": "🔴 HIGH CONTRADICTION",
                "MEDIUM": "🟡 MEDIUM DISCREPANCY",
                "LOW": "🔵 LOW DISTINCTION",
                "CONSISTENT": "🟢 CONSISTENT"
            }.get(r.severity, r.severity)

            with st.container():
                st.markdown(f"""
                <div class="claim-card">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                        <div>
                            <span class="{badge_class}">{badge_label}</span>
                            <span style="font-size:0.85rem; color:#64748b; margin-left:10px;">Category: <strong>{r.category}</strong></span>
                        </div>
                        <span style="font-size:0.82rem; color:#94a3b8;">Pair ID: {r.pair_id} | Confidence: {int(r.confidence*100)}%</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown(f"**📄 Document A ({r.claim_a.source_doc}):**")
                    st.info(f"\"{r.claim_a.text}\"")
                    if r.claim_a.key_entities:
                        st.caption(f"Entities: {', '.join(r.claim_a.key_entities)}")

                with col_b:
                    st.markdown(f"**📄 Document B ({r.claim_b.source_doc}):**")
                    st.info(f"\"{r.claim_b.text}\"")
                    if r.claim_b.key_entities:
                        st.caption(f"Entities: {', '.join(r.claim_b.key_entities)}")

                if r.conflict_detail:
                    st.markdown(f"""
                    <div class="conflict-box">
                        <strong>⚡ Conflict Highlight:</strong> {r.conflict_detail}
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown(f"**💡 Explanation:** {r.explanation}")

                if r.recommendation:
                    st.markdown(f"""
                    <div class="recommendation-box">
                        <strong>🛡️ Action Recommendation:</strong> {r.recommendation}
                    </div>
                    """, unsafe_allow_html=True)

                st.write("")

        st.divider()

        # Step 4: Export Reports
        st.subheader("📥 Step 4: Export Audit Reports")
        ex1, ex2, ex3 = st.columns(3)

        doc_a_name = res["doc_a_meta"].get("filename", "Doc_A")
        doc_b_name = res["doc_b_meta"].get("filename", "Doc_B")

        json_report = ReportGenerator.generate_json_report(res["doc_a_meta"], res["doc_b_meta"], claims_a, claims_b, summary)
        md_report = ReportGenerator.generate_markdown_report(doc_a_name, doc_b_name, summary)
        html_report = ReportGenerator.generate_html_report(doc_a_name, doc_b_name, summary)

        with ex1:
            st.download_button(
                "💾 Download JSON Audit Report",
                data=json_report,
                file_name="contradiction_report.json",
                mime="application/json",
                use_container_width=True
            )
        with ex2:
            st.download_button(
                "📝 Download Markdown Report",
                data=md_report,
                file_name="contradiction_report.md",
                mime="text/markdown",
                use_container_width=True
            )
        with ex3:
            st.download_button(
                "🌐 Download HTML Executive Report",
                data=html_report,
                file_name="contradiction_report.html",
                mime="text/html",
                use_container_width=True
            )


if __name__ == "__main__":
    main()
