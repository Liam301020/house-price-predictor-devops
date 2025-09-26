# app.py — Streamlit UI with STRICT JWT authentication (no API key fallback)
import os
import requests
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Melbourne House Price Predictor", layout="centered")

# ===== Config =====
API_URL = os.getenv("API_URL", "http://localhost:8001")
TIMEOUT = 12  # seconds

# ---------- HTTP helpers ----------
def _auth_headers() -> dict:
    """
    STRICT mode: require JWT. If token is missing, we stop earlier in the UI.
    """
    token = st.session_state.get("token")
    if not token:
        raise RuntimeError("Missing token. Please login first.")
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

def api_login(username: str, password: str) -> dict:
    # OAuth2 password flow requires form-data
    r = requests.post(
        f"{API_URL}/auth/login",
        data={"username": username, "password": password, "grant_type": "password"},
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    return r.json()  # {"access_token": "...", "token_type": "bearer"}

def api_register(username: str, password: str) -> dict:
    r = requests.post(
        f"{API_URL}/auth/register",
        json={"username": username, "password": password},
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    return r.json()

def api_me() -> dict:
    r = requests.get(f"{API_URL}/auth/me", headers=_auth_headers(), timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()

def api_predict(payload: dict) -> dict:
    r = requests.post(f"{API_URL}/api/predict", headers=_auth_headers(), json=payload, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()

def api_records() -> list[dict]:
    r = requests.get(f"{API_URL}/api/records", headers=_auth_headers(), timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()

def api_delete(record_id: str) -> dict:
    r = requests.delete(f"{API_URL}/api/records/{record_id}", headers=_auth_headers(), timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()

# ---------- Auth block (shown when not logged in) ----------
def render_auth():
    st.subheader("Account")

    # Login / Register columns
    col_login, col_register = st.columns(2)

    with col_login:
        st.write("### Login")
        u = st.text_input("Username", key="login_user")
        p = st.text_input("Password", type="password", key="login_pw")
        if st.button("Sign in", use_container_width=True):
            try:
                resp = api_login(u, p)
                st.session_state["token"] = resp["access_token"]
                st.session_state["username"] = u
                st.success("Login success.")
                st.rerun()  # reload UI -> show tabs
            except Exception as e:
                st.error(f"Login failed: {e}")

    with col_register:
        st.write("### Register")
        ru = st.text_input("New username", key="reg_user")
        rp = st.text_input("New password", type="password", key="reg_pw")
        if st.button("Create account", use_container_width=True):
            try:
                api_register(ru, rp)
                st.success("Account created. Please login.")
            except Exception as e:
                st.error(f"Register failed: {e}")

# ====================== UI ======================
st.title("Melbourne House Price Predictor")

# Require login before showing feature tabs
if not st.session_state.get("token"):
    st.info("Please sign in to use Predict and History.")
    render_auth()
    st.stop()

# Logged-in header + logout
top_c1, top_c2 = st.columns([3, 1])
with top_c1:
    st.success(f"Logged in as: {st.session_state.get('username', 'user')}")
with top_c2:
    if st.button("Log out"):
        for k in ("token", "username", "_reload_hist"):
            st.session_state.pop(k, None)
        st.experimental_rerun()

# Feature tabs
tab_predict, tab_history = st.tabs(["Predict", "History"])

# ---- Predict tab ----
with tab_predict:
    col1, col2 = st.columns(2)
    with col1:
        suburb = st.text_input("Suburb", "Box Hill")
        property_type = st.selectbox("Property Type", ["House", "Apartment", "Unit"])
        bedrooms = st.number_input("Bedrooms", min_value=0, value=3, step=1)
        bathrooms = st.number_input("Bathrooms", min_value=0, value=2, step=1)
        parking_spaces = st.number_input("Parking Spaces", min_value=0, value=1, step=1)
    with col2:
        land_size = st.number_input("Land Size (sqm)", min_value=0.0, value=450.0, step=10.0)
        building_size = st.number_input("Building Size (sqm)", min_value=0.0, value=120.0, step=5.0)
        # keep postcode as string to match API schema
        postcode = st.text_input("Postcode", "3128")
        schools_nearby = st.number_input("Schools Nearby", min_value=0, value=0, step=1)

    if st.button("Predict Price", use_container_width=True):
        payload = {
            "suburb": suburb,
            "property_type": property_type,
            "bedrooms": int(bedrooms),
            "bathrooms": int(bathrooms),
            "parking": int(parking_spaces),
            "land_size": float(land_size),
            "building_size": float(building_size),
            "postcode": postcode,
            "schools_nearby": int(schools_nearby),
        }
        try:
            resp = api_predict(payload)
            price = resp.get("price")
            rec_id = resp.get("id", "n/a")
            st.success(f"Estimated Price: AUD {price:,.0f}")
            st.caption(f"Record ID: {rec_id}")
        except Exception as e:
            st.error(f"API error: {e}")

# ---- History tab ----
with tab_history:
    if st.button("Refresh history"):
        st.session_state["_reload_hist"] = True

    if st.session_state.get("_reload_hist", True):
        try:
            data = api_records()
            if not data:
                st.info("No records found.")
            else:
                df = pd.DataFrame(data)
                if "created_at" in df.columns:
                    df = df.sort_values("created_at", ascending=False)
                st.dataframe(df, use_container_width=True, height=360)

                if "id" in df.columns and len(df):
                    sel = st.selectbox("Select Record ID to delete", df["id"].astype(str).tolist())
                    if st.button("Delete selected"):
                        try:
                            api_delete(sel)
                            st.success("Record deleted.")
                            st.session_state["_reload_hist"] = True
                        except Exception as e:
                            st.error(f"Delete failed: {e}")
        except Exception as e:
            st.error(f"Failed to load history: {e}")