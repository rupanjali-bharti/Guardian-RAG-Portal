import streamlit as st
import pandas as pd
import os
import re
from dotenv import load_dotenv
from streamlit_firebase_auth import FirebaseAuth
import pypdf
from docx import Document

# Modularized Imports
from main_rag import run_rag_single
from vector_store import add_documents
from dashboard import show_dashboard

load_dotenv()

st.set_page_config(page_title="EduConnect AI | Compliance Portal", layout="wide")

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SAVE_DIR = os.path.join(CURRENT_DIR, "sample_data")

if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

def apply_adaptive_styling():
    st.markdown("""
    <style>
    [data-testid="stSidebar"] { border-right: 1px solid rgba(128, 128, 128, 0.2) !important; }
    [data-testid="metric-container"] { border: 1px solid rgba(128, 128, 128, 0.2); border-radius: 12px; padding: 15px; }
    .gap-bar { height: 12px; border-radius: 6px; background: #333; margin-top: 5px; }
    .gap-fill { height: 12px; border-radius: 6px; transition: width 0.8s ease-in-out; }
    </style>
    """, unsafe_allow_html=True)

apply_adaptive_styling()
st.title("Compliance Portal")

if 'rag_results' not in st.session_state:
    st.session_state.rag_results = []

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2942/2942789.png", width=60)
    st.title("EduConnect AI")
    st.write("User: **Guest**")
    st.divider()
    ref_files = st.file_uploader("Upload Policy Docs", accept_multiple_files=True, type=["txt", "pdf", "docx"])
    if st.button("Index Documents", type="primary") and ref_files:
        for f in ref_files:
            with open(os.path.join(SAVE_DIR, f.name), "wb") as save_file:
                save_file.write(f.getbuffer())
        st.success("Indexed.")

# --- MAIN LOGIC ---
q_file = st.file_uploader("Upload Questionnaire (CSV)", type=["csv"])

if q_file:
    df_q = pd.read_csv(q_file)
    questions = df_q.iloc[:, 0].dropna().tolist()
    
    if st.button("Start Answering", type="primary"):
        with st.status("Analyzing...", expanded=True) as status:
            temp_results = []
            for i, q in enumerate(questions):
                res = run_rag_single(q)
                ans_text = res.get('Answer', '').lower()
                cit_text = str(res.get('Citation', '')).lower()

                # SCORING LOGIC
                grounding_score = 0
                if any(ext in cit_text for ext in [".txt", ".pdf", ".docx"]): grounding_score += 40
                gap_words = ["not found", "not mentioned", "unavailable", "does not specify"]
                if not any(w in ans_text for w in gap_words): grounding_score += 30
                if len(ans_text) > 80: grounding_score += 30
                
                gap_val = 100 - grounding_score
                res['GapPercentage'] = gap_val

                # STATUS MAPPING
                if gap_val <= 20: res['Status'] = "Verified"
                elif gap_val <= 50: res['Status'] = "Partial Info"
                elif gap_val <= 80: res['Status'] = "Significant Gap"
                else: res['Status'] = "Critical Gap"
                    
                temp_results.append(res)
            
            st.session_state.rag_results = temp_results
            status.update(label="Analysis Complete", state="complete")
            st.rerun()

# --- RENDER RESULTS ---
if st.session_state.rag_results:
    st.divider()
    
    # Passing results to the Executive Dashboard
    show_dashboard(st.session_state.rag_results) 

    st.write("")
    df_res = pd.DataFrame(st.session_state.rag_results)
    
    # Audit Tiles
    t_cols = st.columns(4)
    categories = [("Verified", "#00c853"), ("Partial Info", "#ffa500"), ("Significant Gap", "#ff6d00"), ("Critical Gap", "#ff4b4b")]
    for idx, (label, color) in enumerate(categories):
        count = len(df_res[df_res['Status'] == label])
        t_cols[idx].markdown(f"""
            <div style="text-align:center; padding:10px; border-radius:10px; background:{color}22; border:1px solid {color}">
                <h4 style="margin:0; color:{color}">{count}</h4>
                <p style="margin:0; font-size:12px">{label}</p>
            </div>
        """, unsafe_allow_html=True)

    # Review Items
    st.subheader("Detailed Item Review")
    for i, res in enumerate(st.session_state.rag_results):
        with st.container(border=True):
            c1, c2, c3 = st.columns([4, 1, 1])
            c1.markdown(f"**Item {i+1}:** {res['Question']}")
            gap = res.get('GapPercentage', 0)
            stat = res.get('Status', 'Critical Gap')
            c2.write(f"Gap: {gap}%")
            if stat == "Verified": c3.success(stat)
            else: c3.warning(stat)
            
            # Using unique keys to capture updated values
            st.text_area("Response:", value=res['Answer'], key=f"rev_{i}", height=100)
            st.caption(f"Sources: {res.get('Citation', 'None')}")

    # --- DYNAMIC EXPORT LOGIC ---
    # We collect the current values from the text_area keys to ensure edited text is exported
    final_data_for_export = []
    for i, res in enumerate(st.session_state.rag_results):
        updated_answer = st.session_state.get(f"rev_{i}", res['Answer'])
        final_data_for_export.append({
            "Question": res['Question'],
            "Answer": updated_answer,
            "Citation": res['Citation'],
            "Status": res['Status'],
            "GapPercentage": res['GapPercentage']
        })
    
    st.divider()
    export_df = pd.DataFrame(final_data_for_export)
    csv_data = export_df.to_csv(index=False).encode('utf-8')
    
    # Download button for updated CSV
    st.download_button(
        label="📥 Download Updated Audit Report",
        data=csv_data,
        file_name="educonnect_updated_audit.csv",
        mime="text/csv",
        type="primary",
        use_container_width=True
    )