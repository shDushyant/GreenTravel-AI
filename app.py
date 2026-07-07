from flask import Flask, render_template, request
import pandas as pd
import joblib
from datetime import datetime

import os


# ==========================================
# Initialize Flask App
# ==========================================

app = Flask(__name__)

# ==========================================
# Load Trained Model
# ==========================================

model = joblib.load("model.pkl")

# ==========================================
# Home Page
# ==========================================

@app.route("/")
def home():
    return render_template("index.html")


# ==========================================
# About Page
# ==========================================

@app.route("/about")
def about():
    return render_template("about.html")


# ==========================================
# Prediction Route
# ==========================================

@app.route("/predict", methods=["POST"])
def predict():

    # ==========================================
    # Read User Inputs
    # ==========================================

    departure_country = request.form["DepartureLocationCountry"]

    departure_city = request.form["DepartureLocationCity"]

    arrival_country = request.form["ArrivalLocationCountry"]

    arrival_city = request.form["ArrivalLocationCity"]

    shipping_desc = request.form["ShippingTypeDescription"]

    purpose = request.form["Purpose"]

    out_policy = request.form["OutOfPolicy"]

    entity = int(request.form["EntitiyCode"])

    business = request.form["BusinessUnit"]

    hotel = int(request.form["HotelNights"])

    net_cost = float(request.form["NetCosts"])


    # ==========================================
    # Shipping Type Mapping
    # ==========================================

    shipping_mapping = {

        "Train": 4,

        "Economy Flight": 10,

        "First Class Flight": 11,

        "Business Class Flight": 12,

        "BMW 3 diesel": 13,

        "Volkswagen Golf diesel": 14,

        "Volkswagen Golf petrol": 15,

        "BMW 3 plugin hybrid": 16,

        "Fiat 500 electric": 17

    }

    shipping_type = shipping_mapping.get(shipping_desc, 4)


    # ==========================================
    # Feature Engineering
    # ==========================================

    # Domestic = 0
    # International = 1

    trip_type = 0

    if departure_country != arrival_country:

        trip_type = 1


    route = departure_city + "_" + arrival_city


    cost_per_night = round(net_cost / (hotel + 1), 2)


    event_count = 0


    # ==========================================
    # Create Input DataFrame
    # ==========================================

    input_df = pd.DataFrame({

        "DepartureLocationCountry":[departure_country],

        "DepartureLocationCity":[departure_city],

        "ArrivalLocationCountry":[arrival_country],

        "ArrivalLocationCity":[arrival_city],

        "ShippingType":[shipping_type],

        "ShippingTypeDescription":[shipping_desc],

        "Purpose":[purpose],

        "OutOfPolicy":[out_policy],

        "EntitiyCode":[entity],

        "BusinessUnit":[business],

        "HotelNights":[hotel],

        "NetCosts":[net_cost],

        "TripType":[trip_type],

        "Route":[route],

        "CostPerNight":[cost_per_night],

        "EventCount":[event_count]

    })


    # ==========================================
    # Model Prediction
    # ==========================================

    probability = model.predict_proba(input_df)[0][1]

    probability_percent = round(probability * 100, 2)
    current_time = datetime.now().strftime("%d-%m-%Y %H:%M")


    # ==========================================
    # Prediction Label
    # ==========================================

    if probability >= 0.5:

        prediction = "🔴 High Carbon Trip"

        recommendation = [

            "Choose Train whenever possible.",

            "Reduce Hotel Nights.",

            "Prefer Economy Travel.",

            "Avoid unnecessary business trips."

        ]

    else:

        prediction = "🟢 Low Carbon Trip"

        recommendation = [

            "Great! This trip is relatively eco-friendly.",

            "Maintain sustainable travel practices."

        ]
        # ==========================================
    # AI Explainability
    # ==========================================

    reasons = []
    suggestions = []

    # ---------- Transport ----------

    if "Business Class" in shipping_desc:

        reasons.append("Business Class flights generally produce higher carbon emissions.")
        suggestions.append("Choose Economy Class whenever possible.")

    elif "First Class" in shipping_desc:

        reasons.append("First Class travel has a higher carbon footprint.")
        suggestions.append("Consider Economy Class for lower emissions.")

    elif "Economy Flight" in shipping_desc:

        reasons.append("Flights generally produce more emissions than rail transport.")
        suggestions.append("Use train travel for shorter routes whenever feasible.")

    elif "Train" in shipping_desc:

        reasons.append("Train travel is among the most eco-friendly transport options.")

    # ---------- Hotel Stay ----------

    if hotel >= 5:

        reasons.append("Longer hotel stays increase the overall carbon footprint.")
        suggestions.append("Reduce hotel nights whenever possible.")

    # ---------- Net Cost ----------

    if net_cost >= 50000:

        reasons.append("High travel expenditure usually indicates a longer or resource-intensive trip.")
        suggestions.append("Plan trips earlier to reduce both costs and emissions.")

    # ---------- International Trip ----------

    if trip_type == 1:

        reasons.append("International travel generally results in higher emissions.")
        suggestions.append("Combine multiple meetings into a single international trip.")

    # ==========================================
    # Risk Level
    # ==========================================

    if probability_percent >= 70:

        risk_level = "High"

    elif probability_percent >= 40:

        risk_level = "Moderate"

    else:

        risk_level = "Low"

    # ==========================================
    # Estimated Carbon Reduction
    # ==========================================

    if risk_level == "High":

        estimated_reduction = "30-40%"

    elif risk_level == "Moderate":

        estimated_reduction = "15-25%"

    else:

        estimated_reduction = "Already Optimized"

    # ==========================================
    # Extra Suggestions
    # ==========================================

    if "High" in prediction:

        suggestions.extend([

            "Use virtual meetings whenever possible.",

            "Prefer rail transport for short-distance travel.",

            "Avoid unnecessary business trips.",

            "Book direct flights to reduce emissions."

        ])

    else:

        suggestions.extend([

            "Continue following sustainable travel practices.",

            "Consider electric vehicles for local transportation.",

            "Keep choosing low-emission travel options."

        ])

    # Remove duplicate suggestions

    suggestions = list(dict.fromkeys(suggestions))

    # ==========================================
    # Render Result Page
    # ==========================================
    history = {

    "Date": current_time,

    "Route": route,

    "Prediction": prediction,

    "Probability": probability_percent

}   
    history_df = pd.DataFrame([history])

    if os.path.exists("history.csv"):

     history_df.to_csv(

        "history.csv",

        mode="a",

        header=False,

        index=False

    )
    else:

     history_df.to_csv(

        "history.csv",

        index=False

    )
    return render_template(

        "result.html",

        prediction=prediction,

        probability=probability_percent,

        recommendations=recommendation,

        reasons=reasons,

        suggestions=suggestions,

        risk_level=risk_level,

        estimated_reduction=estimated_reduction

    )


# ==========================================
# Run Flask App
# ==========================================

@app.route("/dashboard")

def dashboard():

    df = pd.read_csv("history.csv")

    total = len(df)

    high = len(

        df[df["Prediction"].str.contains("High")]

    )

    low = len(

        df[df["Prediction"].str.contains("Low")]

    )

    average = round(

        df["Probability"].mean(),

        2

    )

    recent = df.tail(10)

    return render_template(

        "dashboard.html",

        total=total,

        high=high,

        low=low,

        average=average,

        tables=recent.to_dict(orient="records")

    )
if __name__ == "__main__":

    app.run(debug=True)