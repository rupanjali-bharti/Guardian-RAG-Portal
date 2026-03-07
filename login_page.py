import streamlit as st

def show_login(auth):
    _, col_mid, _ = st.columns([1, 2, 1])
    with col_mid:
        st.write("")
        st.image("https://cdn-icons-png.flaticon.com/512/2942/2942789.png", width=80)
        st.title("EduConnect AI")
        st.subheader("Compliance & Security Portal")
        st.markdown("Sign in or create a new account to access the portal.")
        st.divider()
        
        # This enables the email/password UI with a 'Sign Up' option
        auth.login_form(providers=["password"]) 
        
        st.caption("Authorized Access Only")