from src.predict import predict_price, load_model

def test_model_loads():
    model = load_model()
    assert model is not None

def test_predict_price():
    sample = {
        "suburb": "Box Hill",
        "property_type": "House",
        "bedrooms": 3,
        "bathrooms": 2,
        "parking_spaces": 1,
        "land_size": 450.0,
        "building_size": 120.0,
        "postcode": 3128,
    }
    result = predict_price(sample)
    assert isinstance(result, float)