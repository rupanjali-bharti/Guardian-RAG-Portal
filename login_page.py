import streamlit as st

def show_login(auth):
    """
    Renders a professional login interface for the EduConnect AI Portal.
    Supports both Google OAuth and Email/Password providers via Firebase.
    """
    # Layout: Centered column for a clean UI
    _, col_mid, _ = st.columns([1, 2, 1])
    
    with col_mid:
        st.write("")
        # Using a professional security/shield icon
        st.image("https://cdn-icons-png.flaticon.com/512/2942/2942789.png", width=80)
        
        st.title("🛡️ EduConnect AI")
        st.subheader("Compliance & Security Portal")
        st.markdown("""
            Welcome to the Guardian RAG Portal. 
            Please sign in with your corporate account to access the automated audit tools.
        """)
        
        st.divider()
        
        auth.login_form(providers=["google", "password"]) 
        
        st.divider()
        st.caption("© 2026 EduConnect AI | Authorized Access Only")
        st.markdown("<p style='font-size: 12px; opacity: 0.6;'>Standard university-grade encryption enabled.</p>", unsafe_allow_html=True)
