from flask import Flask, request, jsonify
from transit_checker import calculate_aspects, find_transit_windows, get_sign_info
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
    zodiac = request.args.get("zodiac", "tropical").lower()

    try:
        year, month, day = map(int, date_str.split("-"))
        jd = swe.julday(year, month, day)
    except:
        return jsonify({"error": "Invalid or missing date. Use format: YYYY-MM-DD"}), 400

    if zodiac == "sidereal":
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        flag = swe.FLG_SIDEREAL
    else:
        flag = 0

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
        "Lilith": swe.MEAN_APOG
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
                "retrograde": retrograde,
                "sign": get_sign_info(longitude)
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
        orb = float(data.get("orb", 2.0))

        if not natal_chart or not transits:
            return jsonify({
                "error": "Missing required fields: 'natal_chart' and/or 'transits'"
            }), 400

        results = calculate_aspects(transits, natal_chart, orb)
        return jsonify({"aspects": results})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/transit-windows', methods=['POST'])
def transit_windows():
    try:
        data = request.get_json()

        transit_planet = data.get("transit_planet")
        natal_planet = data.get("natal_planet")
        natal_deg = float(data.get("natal_degree"))
        aspect_angle = float(data.get("aspect_angle"))
        orb = float(data.get("orb", 2.5))
        start_date = data.get("start_date")
        end_date = data.get("end_date")

        if not all([transit_planet, natal_planet, natal_deg, aspect_angle, start_date, end_date]):
            return jsonify({"error": "Missing one or more required fields"}), 400

        result = find_transit_windows(
            transit_planet=transit_planet,
            natal_planet=natal_planet,
            natal_deg=natal_deg,
            aspect_angle=aspect_angle,
            orb=orb,
            start_date=start_date,
            end_date=end_date
        )

        return jsonify(result or {"message": "No aspect found in that window"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/transit-windows/batch', methods=['POST'])
def batch_transit_windows():
    try:
        data = request.get_json()

        natal_chart = data.get("natal_chart")
        start_date = data.get("start_date")
        end_date = data.get("end_date")
        orb = float(data.get("orb", 2.5))
        transit_planets = data.get("transit_planets", ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn"])

        aspects = {
            "Conjunction": 0,
            "Sextile": 60,
            "Square": 90,
            "Trine": 120,
            "Opposition": 180
        }

        if not natal_chart or not start_date or not end_date:
            return jsonify({"error": "Missing required fields: 'natal_chart', 'start_date', or 'end_date'"}), 400

        results = []

        for t_planet in transit_planets:
            for n_planet, n_deg in natal_chart.items():
                for aspect_name, aspect_angle in aspects.items():
                    window = find_transit_windows(
                        transit_planet=t_planet,
                        natal_planet=n_planet,
                        natal_deg=n_deg,
                        aspect_angle=aspect_angle,
                        orb=orb,
                        start_date=start_date,
                        end_date=end_date
                    )
                    if window:
                        window["aspect"] = aspect_name
                        results.append(window)

        return jsonify({"results": results})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
