import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv
from streamlit_firebase_auth import FirebaseAuth

# Modularized Imports - Ensure these files are in your GitHub root
from login_page import show_login
from main_rag import run_rag_single
from vector_store import add_documents
from dashboard import show_dashboard

# Load environment variables for local testing
load_dotenv()

# --- 1. INITIALIZATION & STYLING ---
st.set_page_config(page_title="EduConnect AI | Compliance Portal", page_icon="🛡️", layout="wide")

def apply_adaptive_styling():
    st.markdown("""
    <style>
    [data-testid="stSidebar"] { border-right: 1px solid rgba(128, 128, 128, 0.2) !important; }
    [data-testid="metric-container"] { border: 1px solid rgba(128, 128, 128, 0.2); border-radius: 12px; padding: 15px; }
    .small-font { font-size: 14px; opacity: 0.8; }
    .stButton>button { border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONFIGURATION ---
# (Keeping Auth object for variable stability, but skipping the login gate)
auth = FirebaseAuth({
    "apiKey": os.getenv("FIREBASE_API_KEY"),
    "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN"),
    "projectId": os.getenv("FIREBASE_PROJECT_ID"),
    "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET"),
    "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID"),
    "appId": os.getenv("FIREBASE_APP_ID")
})

# Mock user for the UI since login is currently disabled for reviewer ease
user_name = "Guest Reviewer" 

# --- 3. SIDEBAR (KNOWLEDGE BASE MANAGEMENT) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2942/2942789.png", width=60)
    st.title("EduConnect AI")
    with st.container(border=True):
        st.write(f"👤 **{user_name}**")
        st.caption("Direct Reviewer Access Enabled")

    st.divider()
    st.subheader("📁 Knowledge Base")
    st.markdown("<p class='small-font'>Upload university policies to ground the AI.</p>", unsafe_allow_html=True)
    
    ref_files = st.file_uploader("Upload Policy Docs", accept_multiple_files=True, type=["txt"], label_visibility="collapsed")
    
    if st.button("Index Documents", type="primary", use_container_width=True) and ref_files:
        with st.spinner("Indexing to Vector Store..."):
            for f in ref_files:
                text_content = f.read().decode("utf-8")
                # Paragraph-based chunking for better retrieval
                chunks = [p for p in text_content.split("\n\n") if p.strip()]
                add_documents(chunks, f.name)
        st.success("Indexing Complete!")

# --- 4. MAIN AUDIT LOGIC (RAG PIPELINE) ---
apply_adaptive_styling()
st.title("🛡️ Compliance Portal")
st.markdown("<p class='small-font'>Automated Vendor Security Assessment & Gap Analysis</p>", unsafe_allow_html=True)

if 'rag_results' not in st.session_state:
    st.session_state.rag_results = []

st.write("### 🚀 Step 1: Upload Questionnaire")
q_file = st.file_uploader("Upload Questionnaire (CSV)", type=["csv"], label_visibility="collapsed")

if q_file:
    try:
        df_q = pd.read_csv(q_file)
        questions = df_q.iloc[:, 0].dropna().tolist()
        
        if st.button("🔍 Start Automated Audit", type="primary"):
            with st.status("Analyzing documentation via RAG...", expanded=True) as status:
                temp_results = []
                for i, q in enumerate(questions):
                    res = run_rag_single(q)
                    ans_text = res.get('Answer', '').lower()
                    cit_text = str(res.get('Citation', '')).lower()

                    # ROBUST GAP DETECTION LOGIC
                    gap_keywords = ["not found", "not mentioned", "no information", "does not specify", "unavailable"]
                    has_gap_phrase = any(phrase in ans_text for phrase in gap_keywords)
                    is_missing_citation = cit_text in ["n/a", "none", "", "unknown", "nan"]
                    
                    # Logic: High confidence only if data is present AND cited
                    if has_gap_phrase or is_missing_citation or len(ans_text) < 20:
                        res['Confidence'] = "Low"
                    else:
                        res['Confidence'] = "High"
                        
                    temp_results.append(res)
                
                st.session_state.rag_results = temp_results
                status.update(label="✅ Analysis Complete", state="complete")

    except Exception as e:
        st.error(f"Error processing files: {e}")

# --- 5. RENDER FINDINGS & DASHBOARD ---
if st.session_state.rag_results:
    st.divider()
    # Call to your modular dashboard
    show_dashboard(st.session_state.rag_results) 

    st.write("")
    st.subheader("📝 Detailed Findings & Editor")
    
    updated_data = []
    for i, res in enumerate(st.session_state.rag_results):
        with st.container(border=True):
            h_col, c_col = st.columns([5, 1])
            h_col.markdown(f"**Item {i+1}:** {res['Question']}")
            
            # Dynamic Badge UI
            if res.get('Confidence') == "High":
                c_col.success("VERIFIED")
            else:
                c_col.warning("GAP FOUND")
            
            # Editable response area for final report generation
            ed_ans = st.text_area("Final Response:", value=res.get('Answer', ''), key=f"ed_{i}", height=100)
            st.markdown(f"<p class='small-font'>📍 Source Citation: {res.get('Citation', 'N/A')}</p>", unsafe_allow_html=True)
            
            updated_data.append({
                "Question": res['Question'], "Answer": ed_ans, 
                "Citation": res.get('Citation', 'N/A'), "Confidence": res.get('Confidence')
            })

    # Sync state for export
    st.session_state.rag_results = updated_data 

    st.write("")
    _, col_ex = st.columns([5, 1]) 
    with col_ex:
        csv_data = pd.DataFrame(st.session_state.rag_results).to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Report", data=csv_data, file_name="educonnect_audit.csv", type="primary", use_container_width=True)