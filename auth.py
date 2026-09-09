import streamlit as st

from database import (
    create_account,
    get_current_user,
    initialize_authentication,
    is_authenticated,
    sign_in,
    sign_out,
)


def show_auth_header():
    """Display the authentication page heading."""

    st.markdown(
        """
        <div class="auth-header">
            <span class="auth-eyebrow">TASKFLOW ACCOUNT</span>
            <h1>Welcome to TaskFlow</h1>
            <p>
                Sign in to manage your tasks, weekly goals,
                schedules, and progress.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_sign_in_form():
    """Display and process the sign-in form."""

    with st.form("sign_in_form", clear_on_submit=False):
        st.subheader("Sign in")

        email = st.text_input(
            "Email address",
            placeholder="name@example.com",
            key="sign_in_email",
        )

        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter your password",
            key="sign_in_password",
        )

        submitted = st.form_submit_button(
            "Sign in",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        try:
            with st.spinner("Signing you in..."):
                sign_in(email, password)

            st.success("You have signed in successfully.")
            st.rerun()

        except (ValueError, RuntimeError) as error:
            st.error(str(error))


def show_registration_form():
    """Display and process the account registration form."""

    with st.form("registration_form", clear_on_submit=False):
        st.subheader("Create an account")

        email = st.text_input(
            "Email address",
            placeholder="name@example.com",
            key="registration_email",
        )

        password = st.text_input(
            "Password",
            type="password",
            placeholder="Create a password",
            help="Use at least 6 characters.",
            key="registration_password",
        )

        confirm_password = st.text_input(
            "Confirm password",
            type="password",
            placeholder="Enter the password again",
            key="confirm_registration_password",
        )

        accepted_terms = st.checkbox(
            "I agree to create a TaskFlow account.",
            key="accept_registration_terms",
        )

        submitted = st.form_submit_button(
            "Create account",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        if password != confirm_password:
            st.error("The passwords do not match.")
            return

        if not accepted_terms:
            st.warning(
                "Confirm that you agree to create an account."
            )
            return

        try:
            with st.spinner("Creating your account..."):
                response = create_account(email, password)

            if response.session is not None:
                st.session_state.authenticated = True
                st.session_state.current_user = response.user

                st.success("Your account has been created.")
                st.rerun()

            else:
                st.success(
                    "Your account has been created. Check your email "
                    "and confirm your address before signing in."
                )

        except (ValueError, RuntimeError) as error:
            st.error(str(error))


def show_authentication_page():
    """
    Display the sign-in and account-registration page.
    """

    initialize_authentication()
    show_auth_header()

    sign_in_tab, registration_tab = st.tabs(
        ["Sign in", "Create account"]
    )

    with sign_in_tab:
        show_sign_in_form()

    with registration_tab:
        show_registration_form()


def require_authentication():
    """
    Stop the rest of the application when the user is not signed in.

    Call this function near the beginning of app.py.
    """

    initialize_authentication()

    if not is_authenticated():
        show_authentication_page()
        st.stop()


def show_account_menu():
    """
    Display the signed-in user's account details and sign-out button.
    """

    user = get_current_user()

    if user is None:
        return

    user_email = getattr(user, "email", "TaskFlow user")

    with st.sidebar:
        st.markdown("### Your account")
        st.caption(user_email)

        if st.button(
            "Sign out",
            key="sign_out_button",
            use_container_width=True,
        ):
            try:
                sign_out()
                st.success("You have been signed out.")
                st.rerun()

            except RuntimeError as error:
                st.error(str(error))
                