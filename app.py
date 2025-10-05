from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
from datetime import date, timedelta
import math
import random
import hashlib

# --- CONFIGURATION ---
NASA_API_KEY = '7navEoAK4Qcg1684pjGePLQ8chu0KI46CXcUaWB9'
NASA_NEO_API_URL = 'https://api.nasa.gov/neo/rest/v1/feed'
NASA_NEO_LOOKUP_URL = 'https://api.nasa.gov/neo/rest/v1/neo/'

# --- FLASK APP INITIALIZATION ---
app = Flask(__name__)
CORS(app)

# --- CONSTANTS ---
ASTEROID_DENSITY_KG_M3 = 2000
JOULES_TO_MEGATONS_TNT = 4.184e15

# --- IMPACT CALCULATIONS ---
def calculate_impact_energy(diameter_meters, velocity_kps):
    velocity_mps = velocity_kps * 1000.0
    radius = diameter_meters / 2.0
    volume = (4.0 / 3.0) * math.pi * (radius ** 3)
    mass_kg = volume * ASTEROID_DENSITY_KG_M3
    kinetic_energy_joules = 0.5 * mass_kg * (velocity_mps ** 2)
    megatons_tnt = kinetic_energy_joules / JOULES_TO_MEGATONS_TNT
    return kinetic_energy_joules, megatons_tnt

def estimate_crater_diameter(energy_in_joules):
    target_density_kg_m3 = 2600
    K1 = 0.1
    crater_diameter_meters = K1 * (energy_in_joules / target_density_kg_m3) ** (1.0 / 3.4)
    return crater_diameter_meters

# --- GENERATE PSEUDO GEO COORDS ---
def generate_fake_coordinates(asteroid_id, miss_distance_km):
    """Generate reproducible pseudo-random lat/lon for each asteroid using a stable hash seed."""
    # asteroid_id may not be numeric; use md5 hash to create an int seed
    if asteroid_id is None:
        seed_int = 0
    else:
        h = hashlib.md5(str(asteroid_id).encode('utf-8')).hexdigest()
        # take first 12 hex chars -> int
        seed_int = int(h[:12], 16)
    # include miss_distance for more variation (safe conversion)
    try:
        md = int(float(miss_distance_km)) if (miss_distance_km is not None) else 0
    except Exception:
        md = 0
    random.seed(seed_int + md)
    lat = random.uniform(-60.0, 60.0)
    lon = random.uniform(-180.0, 180.0)
    return lat, lon

# --- FETCH AND PROCESS DATA ---
def fetch_and_process_feed_data(start_date, end_date):
    params = {'api_key': NASA_API_KEY, 'start_date': start_date, 'end_date': end_date}
    try:
        response = requests.get(NASA_NEO_API_URL, params=params, timeout=15)
        print(f"Requesting URL: {response.url}")
        response.raise_for_status()
        data = response.json()

        raw_neos = []
        neo_map = data.get('near_earth_objects', {})
        for date_key in sorted(neo_map.keys()):
            raw_neos.extend(neo_map[date_key])

        processed_neos = []
        for asteroid in raw_neos:
            if 'estimated_diameter' not in asteroid or not asteroid.get('close_approach_data'):
                continue

            # average diameter in meters
            try:
                diam_min = asteroid['estimated_diameter']['meters']['estimated_diameter_min']
                diam_max = asteroid['estimated_diameter']['meters']['estimated_diameter_max']
                diameter_m = (float(diam_min) + float(diam_max)) / 2.0
            except Exception:
                continue

            cad = asteroid['close_approach_data'][0]

            # velocity parsing (defensive: remove commas)
            try:
                vel_str = cad['relative_velocity'].get('kilometers_per_second', '')
                velocity_kps = float(vel_str.replace(',', ''))
            except Exception:
                velocity_kps = 25.0  # default fallback velocity

            ke_joules, ke_megatons = calculate_impact_energy(diameter_m, velocity_kps)
            crater_m = estimate_crater_diameter(ke_joules)

            # miss distance parsing
            miss_distance_km = None
            try:
                if cad.get('miss_distance') and cad['miss_distance'].get('kilometers') is not None:
                    miss_distance_km = float(cad['miss_distance']['kilometers'].replace(',', ''))
            except Exception:
                miss_distance_km = None

            lat, lon = generate_fake_coordinates(asteroid.get('id'), miss_distance_km)

            processed_neos.append({
                'id': asteroid.get('id'),
                'name': asteroid.get('name'),
                'nasa_jpl_url': asteroid.get('nasa_jpl_url'),
                'is_potentially_hazardous': asteroid.get('is_potentially_hazardous_asteroid', False),
                'diameter_km': diameter_m / 1000.0,
                'close_approach_date': cad.get('close_approach_date_full') or cad.get('close_approach_date'),
                'velocity_kps': velocity_kps,
                'miss_distance_km': miss_distance_km,
                'impact_megatons_tnt': ke_megatons,
                'crater_kilometers': crater_m / 1000.0,
                'lat': lat,
                'lon': lon
            })

        print(f"Successfully fetched and processed {len(processed_neos)} asteroids.")
        return processed_neos

    except requests.exceptions.RequestException as e:
        print('Error fetching NEO feed:', e)
        return None

# --- API ENDPOINTS ---
@app.route('/api/neos')
def get_neos_endpoint():
    start_date_str = request.args.get('start_date', default=date.today().strftime('%Y-%m-%d'))
    # ensure days is integer and within 1..7
    try:
        days_in_range = int(request.args.get('days', 7))
    except Exception:
        days_in_range = 7
    days_in_range = max(1, min(days_in_range, 7))

    start_date_obj = date.fromisoformat(start_date_str)
    # NASA feed is inclusive, so subtract 1 day when building end_date
    end_date_obj = start_date_obj + timedelta(days=(days_in_range - 1))
    end_date_str = end_date_obj.strftime('%Y-%m-%d')

    all_asteroid_data = fetch_and_process_feed_data(start_date=start_date_str, end_date=end_date_str)

    if all_asteroid_data is not None:
        return jsonify(all_asteroid_data)
    else:
        return jsonify({"error": "Failed to fetch data from NASA"}), 500


@app.route('/api/neo/<asteroid_id>')
def get_neo_details(asteroid_id):
    """Get detailed data for a single asteroid"""
    try:
        url = f"{NASA_NEO_LOOKUP_URL}{asteroid_id}"
        response = requests.get(url, params={'api_key': NASA_API_KEY}, timeout=15)
        response.raise_for_status()
        data = response.json()

        details = {
            "discovery_date": data.get("orbital_data", {}).get("first_observation_date", "N/A"),
            "orbit_class": data.get("orbital_data", {}).get("orbit_class", {}).get("orbit_class_type", "N/A")
        }
        return jsonify(details)

    except requests.exceptions.RequestException as e:
        print(f"Error fetching details for asteroid {asteroid_id}: {e}")
        return jsonify({"error": "Failed to fetch asteroid details"}), 500


if __name__ == '__main__':
    print("🚀 Starting Flask backend on http://127.0.0.1:5000 ...")
    # For local development this is fine. If you want other machines to access it, set host='0.0.0.0'
    app.run(debug=True, port=5000)