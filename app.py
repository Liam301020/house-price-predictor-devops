# app.py — Streamlit UI + integrated Auth (JWT preferred, API Key fallback)
import os
import requests
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Melbourne House Price Predictor", layout="centered")

# ===== API config =====
API_URL = os.getenv("API_URL", "http://localhost:8001")
API_KEY = os.getenv("API_KEY", "dev-secret")  # fallback when not logged in

# ---------- HTTP helpers ----------
def _auth_headers() -> dict:
    """
    Prefer JWT if available (Authorization: Bearer ...).
    Otherwise fallback to API_KEY (X-API-Key).
    """
    token = st.session_state.get("token")
    if token:
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    return {"X-API-Key": API_KEY, "Content-Type": "application/json"}

def api_login(username: str, password: str) -> dict:
    # FastAPI OAuth2 password flow requires form-data, not JSON
    r = requests.post(
        f"{API_URL}/auth/login",
        data={"username": username, "password": password, "grant_type": "password"},
        timeout=10,
    )
    r.raise_for_status()
    return r.json()  # {"access_token": "...", "token_type": "bearer"}

def api_register(username: str, password: str) -> dict:
    # Endpoint expects JSON according to RegisterIn schema
    r = requests.post(
        f"{API_URL}/auth/register",
        json={"username": username, "password": password},
        timeout=10,
    )
    r.raise_for_status()
    return r.json()

def api_me() -> dict:
    r = requests.get(f"{API_URL}/auth/me", headers=_auth_headers(), timeout=10)
    r.raise_for_status()
    return r.json()

def api_predict(payload: dict) -> dict:
    r = requests.post(f"{API_URL}/api/predict", headers=_auth_headers(), json=payload, timeout=10)
    r.raise_for_status()
    return r.json()

def api_records() -> list[dict]:
    r = requests.get(f"{API_URL}/api/records", headers=_auth_headers(), timeout=10)
    r.raise_for_status()
    return r.json()

def api_delete(record_id: str) -> dict:
    r = requests.delete(f"{API_URL}/api/records/{record_id}", headers=_auth_headers(), timeout=10)
    r.raise_for_status()
    return r.json()

# ====================== UI ======================
st.title("Melbourne House Price Predictor")

# Tabs: Auth + Predict + History
tab_auth, tab_predict, tab_history = st.tabs(["Auth", "Predict", "History"])

# ---- Auth tab ----
with tab_auth:
    st.subheader("Account")
    if st.session_state.get("token"):
        st.success(f"Logged in as: {st.session_state.get('username', 'user')}")
    else:
        st.info("Not logged in. Predict/History will fallback to API Key if backend allows.")

    col_login, col_register = st.columns(2)

    with col_login:
        st.write("### Login")
        login_user = st.text_input("Username", key="login_user")
        login_pw = st.text_input("Password", type="password", key="login_pw")
        if st.button("Sign in"):
            try:
                resp = api_login(login_user, login_pw)
                st.session_state["token"] = resp["access_token"]
                st.session_state["username"] = login_user
                st.success("Login success.")
            except Exception as e:
                st.error(f"Login failed: {e}")

    with col_register:
        st.write("### Register")
        reg_user = st.text_input("New username", key="reg_user")
        reg_pw = st.text_input("New password", type="password", key="reg_pw")
        if st.button("Create account"):
            try:
                api_register(reg_user, reg_pw)
                st.success("Account created. You can now login.")
            except Exception as e:
                st.error(f"Register failed: {e}")

    if st.session_state.get("token") and st.button("Who am I? (/auth/me)"):
        try:
            me = api_me()
            st.json(me)
        except Exception as e:
            st.error(f"Failed to fetch user info: {e}")

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
        postcode = st.text_input("Postcode", "3128")  # keep as string for API
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
            st.error(f"Could not call API: {e}")

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
                st.dataframe(df, use_container_width=True, height=350)

                id_col = "id" if "id" in df.columns else None
                if id_col:
                    sel = st.selectbox("Select Record ID to delete", df[id_col].astype(str).tolist())
                    if st.button("Delete selected"):
                        try:
                            api_delete(sel)
                            st.success("Record deleted.")
                            st.session_state["_reload_hist"] = True
                        except Exception as e:
                            st.error(f"Failed to delete: {e}")
        except Exception as e:
            st.error(f"Error loading history: {e}")