import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv
from streamlit_firebase_auth import FirebaseAuth

# Modularized Imports
from login_page import show_login
from main_rag import run_rag_single
from vector_store import add_documents
from dashboard import show_dashboard

# Load environment variables
load_dotenv()

# --- 1. INITIALIZATION ---
st.set_page_config(page_title="EduConnect AI | Compliance Portal", page_icon="🛡️", layout="wide")

def apply_adaptive_styling():
    st.markdown("""
    <style>
    [data-testid="stSidebar"] { border-right: 1px solid rgba(128, 128, 128, 0.2) !important; }
    [data-testid="metric-container"] { border: 1px solid rgba(128, 128, 128, 0.2); border-radius: 12px; padding: 15px; }
    .small-font { font-size: 14px; opacity: 0.8; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. FIREBASE AUTH ---
auth = FirebaseAuth({
    "apiKey": os.getenv("FIREBASE_API_KEY"),
    "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN"),
    "projectId": os.getenv("FIREBASE_PROJECT_ID"),
    "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET"),
    "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID"),
    "appId": os.getenv("FIREBASE_APP_ID")
})

if 'app_init' not in st.session_state:
    try: auth.logout() 
    except: pass
    st.session_state.clear()
    st.session_state['app_init'] = True
    st.rerun()

user = auth.check_session()
if not user:
    apply_adaptive_styling()
    show_login(auth)
    st.stop()

# --- 3. SIDEBAR ---
user_email = user.get('email', 'User')
user_name = user_email.split('@')[0].capitalize() 

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2942/2942789.png", width=60)
    st.title("EduConnect AI")
    with st.container(border=True):
        st.write(f"👤 **{user_name}**")
        if st.button("Log Out", type="secondary", use_container_width=True):
            auth.logout()
            st.session_state.clear()
            st.rerun()

    st.divider()
    st.subheader("📁 Knowledge Base")
    ref_files = st.file_uploader("Upload Policy Docs", accept_multiple_files=True, type=["txt"])
    if st.button("Index Documents", type="primary", use_container_width=True) and ref_files:
        with st.spinner("Indexing..."):
            for f in ref_files:
                text_content = f.read().decode("utf-8")
                chunks = [p for p in text_content.split("\n\n") if p.strip()]
                add_documents(chunks, f.name)
        st.success("Indexing Complete!")

# --- 4. MAIN AUDIT LOGIC ---
apply_adaptive_styling()
st.title("🛡️ Compliance Portal")
st.markdown("<p class='small-font'>Automated Vendor Security Assessment & Gap Analysis</p>", unsafe_allow_html=True)

if 'rag_results' not in st.session_state:
    st.session_state.rag_results = []

q_file = st.file_uploader("Upload Questionnaire (CSV)", type=["csv"], label_visibility="collapsed")

if q_file:
    try:
        df_q = pd.read_csv(q_file)
        questions = df_q.iloc[:, 0].dropna().tolist()
        
        if st.button("🚀 Start Audit", type="primary"):
            with st.status("Analyzing documentation...", expanded=True) as status:
                temp_results = []
                for i, q in enumerate(questions):
                    res = run_rag_single(q)
                    ans_text = res.get('Answer', '').lower()
                    cit_text = str(res.get('Citation', '')).lower()

                    # STRICT GROUNDING CHECK
                    is_gap = any(p in ans_text for p in [
                        "not specified", "not mentioned", "no information", 
                        "not found", "unavailable", "does not specify"
                    ])
                    has_no_cit = cit_text in ["n/a", "none", "", "unknown", "nan"]
                    
                    # Logic: High confidence only if data is present AND cited
                    res['Confidence'] = "Low" if (is_gap or has_no_cit or len(ans_text) < 30) else "High"
                    
                    temp_results.append(res)
                st.session_state.rag_results = temp_results
                status.update(label="✅ Analysis Complete", state="complete")

    except Exception as e:
        st.error(f"Error: {e}")

# --- 5. RENDER FINDINGS ---
if st.session_state.rag_results:
    st.divider()
    show_dashboard(st.session_state.rag_results) # Modular Call

    st.write("")
    st.subheader("📝 Detailed Findings")
    
    updated_data = []
    for i, res in enumerate(st.session_state.rag_results):
        with st.container(border=True):
            h_col, c_col = st.columns([5, 1])
            h_col.markdown(f"**Item {i+1}:** {res['Question']}")
            
            # Badge UI
            if res.get('Confidence') == "High":
                c_col.success("VERIFIED")
            else:
                c_col.warning("GAP FOUND")
            
            # Editable area captures live changes
            ed_ans = st.text_area("Final Response:", value=res.get('Answer', ''), key=f"ed_{i}", height=100)
            st.markdown(f"<p class='small-font'>📍 Reference: {res.get('Citation', 'N/A')}</p>", unsafe_allow_html=True)
            
            updated_data.append({
                "Question": res['Question'], "Answer": ed_ans, 
                "Citation": res.get('Citation', 'N/A'), "Confidence": res.get('Confidence')
            })

    # Final State Sync
    st.session_state.rag_results = updated_data 

    st.write("")
    _, col_ex = st.columns([5, 1]) 
    with col_ex:
        csv_data = pd.DataFrame(st.session_state.rag_results).to_csv(index=False).encode('utf-8')
        st.download_button("📥 Export CSV", data=csv_data, file_name="audit_report.csv", type="primary", use_container_width=True)