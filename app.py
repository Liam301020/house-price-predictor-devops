import streamlit as st
import pandas as pd
from src.predict import predict_price

st.title("Melbourne House Price Predictor")

# Input form
suburb = st.text_input("Suburb", "Box Hill")
property_type = st.selectbox("Property Type", ["House", "Apartment", "Unit"])
bedrooms = st.number_input("Bedrooms", min_value=1, value=3)
bathrooms = st.number_input("Bathrooms", min_value=1, value=2)
parking_spaces = st.number_input("Parking Spaces", min_value=0, value=1)
land_size = st.number_input("Land Size (sqm)", min_value=50.0, value=450.0)
building_size = st.number_input("Building Size (sqm)", min_value=30.0, value=120.0)
postcode = st.number_input("Postcode", min_value=3000, value=3128)
schools_nearby = st.number_input("Schools Nearby", min_value=0, value=0)  # new field

if st.button("Predict Price"):
    sample = {
        "suburb": suburb,
        "property_type": property_type,
        "bedrooms": bedrooms,
        "bathrooms": bathrooms,
        "parking_spaces": parking_spaces,
        "land_size": land_size,
        "building_size": building_size,
        "postcode": postcode,
        "schools_nearby": schools_nearby,   # include in the sample
    }
    result = predict_price(sample)
    st.success(f"Estimated Price: AUD {result:,.0f}")