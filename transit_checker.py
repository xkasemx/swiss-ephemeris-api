import swisseph as swe

def calculate_aspects(transits, natal_chart, orb_limit=2):
    aspects = {
        "Conjunction": 0,
        "Sextile": 60,
        "Square": 90,
        "Trine": 120,
        "Opposition": 180
    }

    results = []

    for t_planet, t_deg in transits.items():
        for n_planet, n_deg in natal_chart.items():
            angle = abs(t_deg - n_deg)
            angle = min(angle, 360 - angle)

            for aspect_name, aspect_angle in aspects.items():
                orb = abs(angle - aspect_angle)
                if orb <= orb_limit:
                    results.append({
                        "transit": t_planet,
                        "natal": n_planet,
                        "aspect": aspect_name,
                        "orb": round(orb, 2),
                        "transit_deg": round(t_deg, 2),
                        "natal_deg": round(n_deg, 2)
                    })

    return results

def get_planet_position(planet_name, date_str):
    jd = swe.julday(*map(int, date_str.split("-")))
    planet_ids = {
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
        "North Node": swe.TRUE_NODE,
        "Chiron": swe.CHIRON,
        "Lilith": swe.MEAN_APOG
    }
    if planet_name not in planet_ids:
        raise ValueError(f"Unknown planet: {planet_name}")

    pos, _ = swe.calc_ut(jd, planet_ids[planet_name])
    return pos[0]

def find_transit_windows(transit_planet, natal_planet, natal_deg, aspect_angle, orb, start_date, end_date):
    import datetime
    current_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")
    end_date_obj = datetime.datetime.strptime(end_date, "%Y-%m-%d")
    delta = datetime.timedelta(days=1)

    in_window = False
    window_start = None
    window_end = None
    min_orb = 999
    exact_date = None

    while current_date <= end_date_obj:
        date_str = current_date.strftime("%Y-%m-%d")
        try:
            trans_deg = get_planet_position(transit_planet, date_str)
        except Exception:
            current_date += delta
            continue

        angle = abs(trans_deg - natal_deg)
        angle = min(angle, 360 - angle)
        orb_diff = abs(angle - aspect_angle)

        if orb_diff <= orb:
            if not in_window:
                window_start = date_str
                in_window = True

            if orb_diff < min_orb:
                min_orb = orb_diff
                exact_date = date_str

            window_end = date_str
        elif in_window:
            break

        current_date += delta

    if window_start and exact_date and window_end:
        return {
            "transit": transit_planet,
            "natal": natal_planet,
            "aspect": f"{aspect_angle}°",
            "start": window_start,
            "exact": exact_date,
            "end": window_end,
            "orb_used": orb
        }
    else:
        return None
