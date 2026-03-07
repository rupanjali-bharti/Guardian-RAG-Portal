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

        # Login and Signup buttons for Firebase email/password authentication
        login_tab, signup_tab = st.tabs(["Login", "Sign Up"])
        with login_tab:
            st.write("Login with your email and password.")
            auth.login_form(providers=["password"])
        with signup_tab:
            st.write("Create a new account.")
            auth.signup_form(providers=["password"])

        st.caption("Authorized Access Only")