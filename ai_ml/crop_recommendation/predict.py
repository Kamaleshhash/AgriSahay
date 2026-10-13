import joblib
import numpy as np
import pandas as pd
# Load trained model
model = joblib.load("ai_ml/models/crop_recommendation_model.pkl")

# Example farmer input
N = 90
P = 42
K = 43
temperature = 20.8
humidity = 82.0
ph = 6.5
rainfall = 203.0

# Create input
import pandas as pd

input_data = pd.DataFrame([{
    "N": N,
    "P": P,
    "K": K,
    "temperature": temperature,
    "humidity": humidity,
    "ph": ph,
    "rainfall": rainfall
}])

# Predict crop
prediction = model.predict(input_data)

print("Recommended Crop:", prediction[0])