import streamlit as st
import pandas as pd

def show_dashboard(results):
    if not results:
        return

    df = pd.DataFrame(results)
    total_items = len(df)
    
    # Calculate Verified based on our new Status tier
    # Verified items are those marked as "Verified"
    verified_count = len(df[df['Status'] == 'Verified'])
    
    # Gaps are everything else (Partial, Significant, Critical)
    gaps_count = total_items - verified_count
    
    # Compliance Score calculation
    compliance_score = round((verified_count / total_items) * 100) if total_items > 0 else 0

    st.markdown("### 📊 Executive Audit Dashboard")
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Compliance Score", f"{compliance_score}%")
    m2.metric("Total Scope", f"{total_items} Items")
    m3.metric("Verified", verified_count)
    m4.metric("Gaps Found", gaps_count, delta=f"-{gaps_count}" if gaps_count > 0 else 0, delta_color="inverse")
    
    st.progress(compliance_score / 100)