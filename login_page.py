import streamlit as st
from streamlit_firebase_auth import FirebaseAuth

def show_login(auth):
    # Centered layout for a professional look
    _, col_mid, _ = st.columns([1, 2, 1])
    with col_mid:
        st.write("")
        st.image("https://cdn-icons-png.flaticon.com/512/2942/2942789.png", width=80)
        st.title("EduConnect AI")
        st.subheader("Compliance & Security Portal")
        st.markdown("Please sign in to access the automated questionnaire tool.")
        st.divider()
        
        # Built-in Firebase Login/Signup form
        auth.login_form()
        
        st.caption("© 2026 EduConnect AI | Authorized Access Only")