import streamlit as st
from streamlit_firebase_auth import FirebaseAuth
import streamlit as st

def show_login(auth):
    _, col_mid, _ = st.columns([1, 2, 1])
    with col_mid:
        st.write("")
        st.image("https://cdn-icons-png.flaticon.com/512/2942/2942789.png", width=80)
        st.title("EduConnect AI")
        st.subheader("Compliance & Security Portal")
        st.markdown("Sign in with your corporate account to continue.")
        st.divider()
        
        # This line forces ONLY Google login
        auth.login_form(providers=["google"]) 
        
        st.caption("© 2026 EduConnect AI | Authorized Access Only")