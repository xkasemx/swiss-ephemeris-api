import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
from aspects import calculate_aspects  # assumes you have this helper
from transit_checker import get_transit_for_date  # optional helper
import pytz

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# === UTILITY HELPERS ===

def sign_to_offset(sign):
    """Convert zodiac sign name to degree offset."""
    signs = [
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
    ]
    return signs.index(sign) * 30 if sign in signs else 0

def build_aspects_payload(chart_data, transit_data, orb=4):
    """Constructs the full aspects payload from live chart and transit data."""
    # Start with natal planets
    natal_chart = {
        planet: info["degree"]
        for planet, info in chart_data.get("planets", {}).items()
    }

    # Add chart angles
    try:
        angles = chart_data["angles"]
        asc_deg = angles["ASC"]["degree"] + sign_to_offset(angles["ASC"]["sign"])
        mc_deg = angles["MC"]["degree"] + sign_to_offset(angles["MC"]["sign"])
        natal_chart["ASC"] = asc_deg % 360
        natal_chart["DESC"] = (asc_deg + 180) % 360
        natal_chart["MC"] = mc_deg % 360
        natal_chart["IC"] = (mc_deg + 180) % 360
    except Exception as e:
        print(f"⚠️ Could not add angles to natal chart: {e}")

    # Transits
    transits = {
        planet: info["longitude"]
        for planet, info in transit_data.get("positions", {}).items()
    }

    return {
        "natal_chart": natal_chart,
        "transits": transits,
        "orb": orb
    }

# === ROUTES ===

@app.route("/")
def root():
    return jsonify({"message": "🪐 Karma is listening."})


@app.route("/transit", methods=["POST"])
def get_transit():
    try:
        data = request.get_json()
        date = data.get("date")
        zodiac = data.get("zodiac", "tropical")

        if not date:
            return jsonify({"error": "Missing 'date' in request."}), 400

        transit = get_transit_for_date(date=date, zodiac=zodiac)
        return jsonify(transit)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/aspects", methods=["POST"])
def aspects():
    try:
        # Load natal chart (Western only — can extend this if needed)
        chart_path = os.path.join(BASE_DIR, "KTC_guru.json")
        with open(chart_path, "r", encoding="utf-8") as f:
            natal_data = json.load(f)

        # Require transit data to be passed in
        data = request.get_json()
        transit_data = data.get("transit_data")
        if not transit_data:
            return jsonify({"error": "Missing 'transit_data' in request."}), 400

        # Build full aspect payload (with angles, orb = 4)
        payload = build_aspects_payload(natal_data["chart"], transit_data, orb=4)

        # Calculate aspects
        results = calculate_aspects(payload["transits"], payload["natal_chart"], payload["orb"])
        return jsonify({"aspects": results})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
