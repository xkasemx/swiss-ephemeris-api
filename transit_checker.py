def calculate_aspects(transits, natal_chart, orb_limit=2):
    """
    transits: dict like {'Mars': 220.3, 'Venus': 170.5, ...}
    natal_chart: dict like {'Venus': 221.88, 'Mars': 278.85, ...}
    orb_limit: float (max allowed orb in degrees)

    Returns list of dicts with valid aspects.
    """
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
            angle = min(angle, 360 - angle)  # wrap-around

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
