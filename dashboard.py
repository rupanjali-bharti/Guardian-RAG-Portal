import streamlit as st
import pandas as pd

def show_dashboard(results):
    """Renders a professional executive summary with visual analytics"""
    if not results:
        return

    # 1. Data Aggregation
    total_items = len(results)
    verified = sum(1 for r in results if r.get('Confidence') == "High")
    gaps = total_items - verified
    compliance_score = int((verified / total_items) * 100) if total_items > 0 else 0

    st.header("📊 Executive Audit Dashboard")
    
    # 2. KPI Metrics
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Compliance Score", f"{compliance_score}%")
    m2.metric("Total Scope", f"{total_items} Items")
    m3.metric("Verified", verified)
    m4.metric("Gaps Found", gaps, delta=f"-{gaps}" if gaps > 0 else "0", delta_color="inverse")

    # 3. Visual Confidence Distribution
    st.write("")
    chart_col, info_col = st.columns([2, 1])
    
    with chart_col:
        st.subheader("🛡️ Confidence Distribution")
        chart_data = pd.DataFrame({
            'Status': ['Verified (High)', 'Gaps (Low)'],
            'Count': [verified, gaps]
        }).set_index('Status')
        # Dynamic coloring based on score
        chart_color = ["#28a745", "#dc3545"] 
        st.bar_chart(chart_data)

    with info_col:
        st.subheader("💡 Audit Status")
        if compliance_score < 70:
            st.error("Critical documentation gaps identified. Manual review required.")
        elif compliance_score < 100:
            st.warning("Audit nearly complete. Verify remaining 'Low Confidence' items.")
        else:
            st.success("Full policy alignment achieved. Ready for certification.")