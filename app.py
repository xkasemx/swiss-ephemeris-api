from flask import Flask, request, jsonify
import swisseph as swe
import datetime

app = Flask(__name__)
swe.set_ephe_path('.')  # Swiss ephemeris files live here

@app.route("/transit", methods=["GET"])
def transit():
    date_str = request.args.get("date", "")
    zodiac = request.args.get("zodiac", "tropical")  # or sidereal

    try:
        year, month, day = map(int, date_str.split("-"))
        jd = swe.julday(year, month, day)
    except:
        return jsonify({"error": "Invalid or missing date format. Use YYYY-MM-DD"}), 400

    if zodiac == "sidereal":
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        flag = swe.FLG_SIDEREAL
    else:
        flag = 0  # tropical

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
        "Lilith": swe.MEAN_APOG  # aka Black Moon Lilith
    }

    output = {}
    for name, const in planets.items():
        try:
            pos, _ = swe.calc_ut(jd, const, flag)
            output[name] = {
                "longitude": round(pos[0], 4),
                "speed": round(pos[3], 4)
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
    return "Swiss Ephemeris API is live!"

# 🔧 THIS MUST BE AT THE END
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

