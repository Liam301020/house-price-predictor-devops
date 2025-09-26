# auth_ui.py — Simple JWT login/register for the FastAPI backend
import os
import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8001")

def _save_session(token: str | None, username: str | None):
    st.session_state["token"] = token
    st.session_state["username"] = username

def _auth_headers():
    tok = st.session_state.get("token")
    return {"Authorization": f"Bearer {tok}"} if tok else {}

st.set_page_config(page_title="House Price Predictor — Auth UI", layout="centered")
st.title("Melbourne House Price Predictor — Auth UI")

# ---------- Status ----------
colA, colB = st.columns([1, 1])
with colA:
    if "token" in st.session_state and st.session_state["token"]:
        st.success(f"Logged in as: {st.session_state.get('username', 'user')}")
        if st.button("Log out"):
            _save_session(None, None)
            st.rerun()
    else:
        st.info("Not logged in.")

st.divider()

# ---------- Login ----------
st.subheader("Login")
lcol1, lcol2 = st.columns(2)
with lcol1:
    u = st.text_input("Username", key="login_u")
with lcol2:
    p = st.text_input("Password", type="password", key="login_p")

if st.button("Sign in"):
    try:
        # OAuth2PasswordRequestForm => form-data (NOT JSON)
        r = requests.post(
            f"{API_URL}/auth/login",
            data={"username": u, "password": p},
            timeout=10,
        )
        r.raise_for_status()
        token = r.json()["access_token"]

        # (optional) /auth/me to get username from token
        me = requests.get(f"{API_URL}/auth/me", headers={"Authorization": f"Bearer {token}"}, timeout=10)
        me.raise_for_status()
        username = me.json().get("username", u)

        _save_session(token, username)
        st.success("Login success.")
    except Exception as e:
        st.error(f"Login failed: {e}")

st.divider()

# ---------- Register ----------
st.subheader("Register")
rcol1, rcol2 = st.columns(2)
with rcol1:
    new_u = st.text_input("New username", key="reg_u")
with rcol2:
    new_p = st.text_input("New password", type="password", key="reg_p")

if st.button("Create account"):
    try:
        r = requests.post(
            f"{API_URL}/auth/register",
            json={"username": new_u, "password": new_p},
            timeout=10,
        )
        r.raise_for_status()
        st.success("Account created. You can login now.")
    except Exception as e:
        st.error(f"Register failed: {e}")

st.divider()

# ---------- Check token ----------
if st.session_state.get("token"):
    if st.button("Who am I? (/auth/me)"):
        try:
            r = requests.get(f"{API_URL}/auth/me", headers=_auth_headers(), timeout=10)
            r.raise_for_status()
            st.json(r.json())
        except Exception as e:
            st.error(f"/auth/me failed: {e}")