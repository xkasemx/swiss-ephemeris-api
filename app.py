from flask import Flask, request, jsonify
from transit_checker import calculate_aspects
import swisseph as swe
import datetime
import os

app = Flask(__name__)

# Setup Swiss Ephemeris absolute path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EPHE_PATH = os.path.join(BASE_DIR, "swisseph_data")
print("Setting ephemeris path to:", EPHE_PATH)
print("Files in ephemeris dir:", os.listdir(EPHE_PATH))
swe.set_ephe_path(EPHE_PATH)

@app.route("/transit", methods=["GET"])
def transit():
    date_str = request.args.get("date", "")
    zodiac = request.args.get("zodiac", "tropical").lower()  # "tropical" or "sidereal"

    try:
        year, month, day = map(int, date_str.split("-"))
        jd = swe.julday(year, month, day)
    except:
        return jsonify({"error": "Invalid or missing date. Use format: YYYY-MM-DD"}), 400

    if zodiac == "sidereal":
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        flag = swe.FLG_SIDEREAL
    else:
        flag = 0  # tropical is default

    # Define planetary constants
    planets = {
        "Sun": swe.SUN,
        "Moon": swe.MOON,
        "Mercury": swe.MERCURY,
        "Venus": swe.VENUS,
        "Mars": swe.MARS,
        "Jupiter": swe.JUPITER,
        "Saturn": swe.SATURN,
        "Uranus": swe.URANUS,
        "Neptune": swe.NEPTUNE,
        "Pluto": swe.PLUTO,
        "True Node": swe.TRUE_NODE,
        "Chiron": swe.CHIRON,
        "Lilith": swe.MEAN_APOG  # Black Moon Lilith
    }

    output = {}

    for name, const in planets.items():
        try:
            pos, _ = swe.calc_ut(jd, const, flag | swe.FLG_SPEED)
            longitude = round(pos[0], 4)
            speed = round(pos[3], 4)
            retrograde = speed < 0

            output[name] = {
                "longitude": longitude,
                "speed": speed,
                "retrograde": retrograde
            }
        except Exception as e:
            output[name] = {"error": str(e)}

    return jsonify({
        "date": date_str,
        "zodiac": zodiac,
        "positions": output
    })

@app.route("/")
def root():
    return "✅ Swiss Ephemeris API is live!"

@app.route('/aspects', methods=['POST'])
def aspects():
    try:
        data = request.get_json()

        natal_chart = data.get("natal_chart")
        transits = data.get("transits")
        orb = float(data.get("orb", 2.0))  # Default orb is 2.0 degrees

        if not natal_chart or not transits:
            return jsonify({
                "error": "Missing required fields: 'natal_chart' and/or 'transits'"
            }), 400

        results = calculate_aspects(transits, natal_chart, orb)
        return jsonify({"aspects": results})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

