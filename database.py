import streamlit as st
from supabase import Client, create_client


def get_supabase_client() -> Client:
    """
    Create one Supabase client for the current Streamlit user session.
    """

    if "supabase_client" not in st.session_state:
        try:
            project_url = st.secrets["supabase"]["url"]
            publishable_key = st.secrets["supabase"]["publishable_key"]
        except KeyError as error:
            raise RuntimeError(
                "Supabase credentials are missing. Add the project URL "
                "and publishable key to .streamlit/secrets.toml."
            ) from error

        if not project_url or not publishable_key:
            raise RuntimeError(
                "The Supabase project URL or publishable key is empty."
            )

        st.session_state.supabase_client = create_client(
            project_url,
            publishable_key,
        )

    return st.session_state.supabase_client


def create_account(email: str, password: str):
    """
    Register a new user with an email address and password.
    """

    email = email.strip().lower()

    if not email:
        raise ValueError("Enter your email address.")

    if len(password) < 6:
        raise ValueError(
            "Your password must contain at least 6 characters."
        )

    try:
        client = get_supabase_client()

        response = client.auth.sign_up(
            {
                "email": email,
                "password": password,
            }
        )

        if response.user is None:
            raise RuntimeError(
                "The account could not be created. Please try again."
            )

        return response

    except ValueError:
        raise

    except Exception as error:
        message = str(error)

        if "already registered" in message.lower():
            raise RuntimeError(
                "An account with this email address already exists."
            ) from error

        raise RuntimeError(
            f"Account creation failed: {message}"
        ) from error


def sign_in(email: str, password: str):
    """
    Sign in an existing user.
    """

    email = email.strip().lower()

    if not email or not password:
        raise ValueError("Enter both your email address and password.")

    try:
        client = get_supabase_client()

        response = client.auth.sign_in_with_password(
            {
                "email": email,
                "password": password,
            }
        )

        if response.user is None or response.session is None:
            raise RuntimeError(
                "Sign-in failed. Check your email and password."
            )

        st.session_state.authenticated = True
        st.session_state.current_user = response.user

        return response

    except ValueError:
        raise

    except Exception as error:
        message = str(error)

        if (
            "invalid login credentials" in message.lower()
            or "email not confirmed" in message.lower()
        ):
            raise RuntimeError(message) from error

        raise RuntimeError(
            f"Sign-in failed: {message}"
        ) from error


def sign_out():
    """
    Sign out the current user and clear their authentication session.
    """

    try:
        client = get_supabase_client()
        client.auth.sign_out()

    except Exception as error:
        raise RuntimeError(
            f"Sign-out failed: {error}"
        ) from error

    finally:
        st.session_state.authenticated = False
        st.session_state.current_user = None
        st.session_state.pop("supabase_client", None)


def get_current_user():
    """
    Return the currently signed-in user.
    """

    if not st.session_state.get("authenticated", False):
        return None

    return st.session_state.get("current_user")


def is_authenticated() -> bool:
    """
    Check whether the current visitor is signed in.
    """

    return (
        st.session_state.get("authenticated", False)
        and st.session_state.get("current_user") is not None
    )


def initialize_authentication():
    """
    Create the authentication session-state values when the app starts.
    """

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if "current_user" not in st.session_state:
        st.session_state.current_user = None