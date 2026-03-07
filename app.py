import streamlit as st
import pandas as pd
import os
import re
from dotenv import load_dotenv
from streamlit_firebase_auth import FirebaseAuth
import pypdf
from docx import Document

# Modularized Imports
from login_page import show_login
from main_rag import run_rag_single
from vector_store import add_documents
from dashboard import show_dashboard

load_dotenv()

# --- 1. INITIALIZATION & STYLING ---
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
    .small-font { font-size: 14px; opacity: 0.8; }
    .stButton>button { border-radius: 8px; }
    .gap-bar { height: 12px; border-radius: 6px; background: #333; margin-top: 5px; }
    .gap-fill { height: 12px; border-radius: 6px; transition: width 0.8s ease-in-out; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONFIGURATION ---
auth = FirebaseAuth({
    "apiKey": os.getenv("FIREBASE_API_KEY"),
    "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN"),
    "projectId": os.getenv("FIREBASE_PROJECT_ID"),
    "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET"),
    "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID"),
    "appId": os.getenv("FIREBASE_APP_ID")
})

user_name = "Rupanjali"

# --- 3. SIDEBAR (KNOWLEDGE BASE MANAGEMENT) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2942/2942789.png", width=60)
    st.title("EduConnect AI")
    st.write(f"User: **{user_name}**")
    
    st.divider()
    st.subheader("Knowledge Base")
    ref_files = st.file_uploader("Upload Policy Docs", accept_multiple_files=True, type=["txt", "pdf", "docx"], label_visibility="collapsed")
    
    if st.button("Index Documents", type="primary", use_container_width=True) and ref_files:
        with st.spinner("Indexing..."):
            for f in ref_files:
                file_path = os.path.join(SAVE_DIR, f.name)
                with open(file_path, "wb") as save_file:
                    save_file.write(f.getbuffer())
                
                text_content = ""
                if f.name.endswith(".pdf"):
                    pdf_reader = pypdf.PdfReader(f)
                    text_content = "\n".join([page.extract_text() for page in pdf_reader.pages])
                elif f.name.endswith(".docx"):
                    doc = Document(f)
                    text_content = "\n".join([para.text for para in doc.paragraphs])
                else:
                    f.seek(0)
                    text_content = f.read().decode("utf-8")
                
                if text_content.strip():
                    chunks = [p for p in text_content.split("\n\n") if p.strip()]
                    add_documents(chunks, f.name)
        st.success("Indexing Complete")

# --- 4. MAIN AUDIT LOGIC (RAG PIPELINE) ---
apply_adaptive_styling()
st.title("Compliance Portal")

if 'rag_results' not in st.session_state:
    st.session_state.rag_results = []

q_file = st.file_uploader("Upload Questionnaire (CSV)", type=["csv"])

if q_file:
    # Save CSV locally [cite: 26, 27, 28, 29, 30]
    csv_path = os.path.join(SAVE_DIR, q_file.name)
    with open(csv_path, "wb") as f_csv:
        f_csv.write(q_file.getbuffer())
    
    q_file.seek(0)
    df_q = pd.read_csv(q_file)
    questions = df_q.iloc[:, 0].dropna().tolist()
    
    if st.button("Start Answering", type="primary"):
        with st.status("Analyzing...", expanded=True) as status:
            temp_results = []
            for i, q in enumerate(questions):
                res = run_rag_single(q)
                ans_text = res.get('Answer', '').lower()
                cit_text = str(res.get('Citation', '')).lower()

                # --- MULTI-METRIC GAP SCORING ---
                grounding_score = 0
                sources = re.findall(r'source:?\s*(\d+)', cit_text)
                
                if sources: grounding_score += 35 # Weighting source presence [cite: 26, 27]
                if len(set(sources)) > 1: grounding_score += 15 # Multiple sources weight
                
                gap_words = ["not found", "not mentioned", "no information", "unavailable", "unable", "omits"]
                if not any(w in ans_text for w in gap_words): grounding_score += 25 # Penalty check [cite: 1, 4, 14]
                
                if len(ans_text) > 80: grounding_score += 25 # Detail depth check
                
                gap_val = 100 - grounding_score
                res['GapPercentage'] = gap_val

                if gap_val <= 20: res['Status'] = "Verified"
                elif gap_val <= 50: res['Status'] = "Partial Info"
                elif gap_val <= 80: res['Status'] = "Significant Gap"
                else: res['Status'] = "Critical Gap"
                    
                temp_results.append(res)
            
            st.session_state.rag_results = temp_results
            status.update(label="Analysis Complete", state="complete")
            # Force rerun to show results immediately
            st.rerun()

# --- 5. RENDER FINDINGS (OUTSIDE THE BUTTON BLOCK) ---
if st.session_state.rag_results:
    st.divider()
    df_results = pd.DataFrame(st.session_state.rag_results)
    
    st.subheader("Audit Distribution")
    dist_cols = st.columns(4)
    categories = [("Verified", "#00c853"), ("Partial Info", "#ffa500"), ("Significant Gap", "#ff6d00"), ("Critical Gap", "#ff4b4b")]
    
    for idx, (label, color) in enumerate(categories):
        count = len(df_results[df_results['Status'] == label]) if 'Status' in df_results.columns else 0
        dist_cols[idx].markdown(f"""
            <div style="text-align:center; padding:10px; border-radius:10px; background:{color}22; border:1px solid {color}">
                <h4 style="margin:0; color:{color}">{count}</h4>
                <p style="margin:0; font-size:12px">{label}</p>
            </div>
        """, unsafe_allow_html=True)

    st.write("")
    show_dashboard(st.session_state.rag_results) 

    st.subheader("Detailed Item Review")
    for i, res in enumerate(st.session_state.rag_results):
        with st.container(border=True):
            h_col, g_col, s_col = st.columns([4, 1, 1])
            h_col.markdown(f"**Item {i+1}:** {res['Question']}")
            
            gap_val = res.get('GapPercentage', 0)
            status_label = res.get('Status', 'Pending')
            color_map = {"Verified": "#00c853", "Partial Info": "#ffa500", "Significant Gap": "#ff6d00", "Critical Gap": "#ff4b4b"}
            current_color = color_map.get(status_label, "#333")
            
            g_col.write(f"**Gap: {gap_val}%**")
            g_col.markdown(f"""
                <div class="gap-bar"><div class="gap-fill" style="width: {gap_val}%; background-color: {current_color};"></div></div>
                """, unsafe_allow_html=True)
            
            if status_label == "Verified": s_col.success(status_label)
            elif status_label == "Partial Info": s_col.warning(status_label)
            else: s_col.error(status_label)
            
            # Use unique keys for text areas
            st.text_area("Response:", value=res.get('Answer', ''), key=f"final_ed_{i}", height=100)
            st.caption(f"Sources: {res.get('Citation', 'None')}")

    csv_data = df_results.to_csv(index=False).encode('utf-8')
    st.download_button("Download Report", data=csv_data, file_name="security_audit.csv", type="primary")