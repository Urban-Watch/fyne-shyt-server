from fastapi import FastAPI, Query
import requests, json, sqlite3, time, logging
from math import pi

app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- External APIs ---
WORLPOP_API = "https://api.worldpop.org/v1/services/stats"
OVERPASS_API = "http://overpass-api.de/api/interpreter"

# --- SQLite Cache ---
DB_FILE = "impact_cache.db"
CACHE_TTL = 24 * 3600  # 1 day

def init_cache():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS cache (
            key TEXT PRIMARY KEY,
            value TEXT,
            timestamp INTEGER
        )
    """)
    conn.commit()
    conn.close()

init_cache()

def get_cache(key: str):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT value, timestamp FROM cache WHERE key=?", (key,))
    row = cur.fetchone()
    conn.close()
    if row:
        value, ts = row
        if time.time() - ts < CACHE_TTL:
            return json.loads(value)
    return None

def set_cache(key: str, value: dict):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("REPLACE INTO cache (key, value, timestamp) VALUES (?,?,?)",
                (key, json.dumps(value), int(time.time())))
    conn.commit()
    conn.close()


def calculate_impact_score(lat: float, lon: float, radius_km: float = 1.0) -> dict:
    """
    Calculate impact score for a location (standalone function)
    """
    # logger.info("=== IMPACT.PY CALCULATE_IMPACT_SCORE STARTED ===")
    # logger.info(f"Input: lat={lat}, lon={lon}, radius_km={radius_km}")

    cache_key = f"{lat}_{lon}_{radius_km}"
    logger.info(f"Cache key: {cache_key}")

    cached = get_cache(cache_key)
    if cached:
        logger.info("Cache hit - returning cached result")
        logger.info(f"Cached result: {cached}")
        return {**cached, "source": "cache"}

    logger.info("Cache miss - calculating live impact score")

    # ---------------------------
    # 1. Population (WorldPop)
    # ---------------------------
    logger.info("Step 1: Calculating population estimate using WorldPop API")
    try:
        geojson = {"type": "Point", "coordinates": [lon, lat]}
        logger.info(f"WorldPop API request: geojson={geojson}")
        pop_resp = requests.get(
            WORLPOP_API,
            params={"dataset": "ppp_2020_1km_Aggregated", "geojson": str(geojson)},
            timeout=15
        )
        pop_data = pop_resp.json()
        population = pop_data.get("data", {}).get("sum", 0)
        # logger.info(f"WorldPop API response: population={population}")

        if not population:  # handle empty
            raise ValueError("Empty WorldPop response")
    except Exception as e:
        population = 1200 * (radius_km ** 2)  # default estimate
        # logger.warning(f"WorldPop API failed ({str(e)}), using default population estimate: {population}")

    # ---------------------------
    # 2. Roads / Vehicles (Overpass OSM)
    # ---------------------------
    logger.info("Step 2: Calculating vehicle estimate using Overpass OSM API")
    try:
        overpass_query = f"""
        [out:json];
        way(around:{int(radius_km*1000)},{lat},{lon})["highway"];
        out geom;
        """
        # logger.info(f"Overpass API query: {overpass_query.strip()}")
        road_resp = requests.get(OVERPASS_API, params={"data": overpass_query}, timeout=30)
        roads = road_resp.json().get("elements", [])
        road_length_m = len(roads) * 200  # heuristic: avg 200m per road segment
        vehicles = road_length_m / 10     # ~10 vehicles per meter of road
        # logger.info(f"Overpass API response: roads={len(roads)}, road_length_m={road_length_m}, vehicles={vehicles}")

        if vehicles <= 0:
            raise ValueError("No road data")
    except Exception as e:
        vehicles = 800 * radius_km  # default vehicle estimate
        logger.warning(f"Overpass API failed ({str(e)}), using default vehicle estimate: {vehicles}")

    # ---------------------------
    # 3. Impact Score
    # ---------------------------
    # logger.info("Step 3: Calculating final impact score")
    area_km2 = pi * (radius_km ** 2)
    # logger.info(f"Area calculation: area_km2={area_km2}")

    MAX_POP_DENSITY = 7000   # per km² (Mumbai-like max)
    MAX_VEH_DENSITY = 2000   # per km² (peak traffic)

    pop_density = population / max(area_km2, 1)
    veh_density = vehicles / max(area_km2, 1)

    # logger.info(f"Density calculations: pop_density={pop_density:.2f}, veh_density={veh_density:.2f}")
    # logger.info(f"Max densities: MAX_POP_DENSITY={MAX_POP_DENSITY}, MAX_VEH_DENSITY={MAX_VEH_DENSITY}")

    # Calculate impact score and convert to integer 1-100 scale
    import math
    impact_score_float = (
        0.6 * min(pop_density / MAX_POP_DENSITY, 1.0) +
        0.4 * min(veh_density / MAX_VEH_DENSITY, 1.0)
    )** 0.5 * 100
    
    # Convert to integer with ceiling to ensure minimum value of 1
    impact_score = max(1, math.ceil(impact_score_float))

    logger.info(f"Impact score calculation: impact_score={impact_score_float:.4f} -> {impact_score} (1-100 scale)")

    result = {
        "lat": lat,
        "lon": lon,
        "radius_km": radius_km,
        "population_estimate": int(population),
        "vehicle_estimate": int(vehicles),
        "impact_score": impact_score,
        "source": "live"
    }

    logger.info(f"Final result: {result}")

    # Save to cache
    set_cache(cache_key, result)
    # logger.info(f"Saved result to cache with key: {cache_key}")

    logger.info("=== IMPACT.PY CALCULATE_IMPACT_SCORE COMPLETED ===")
    return result

@app.get("/impact_score")
def impact_score(
    lat: float = Query(..., description="Latitude of location"),
    lon: float = Query(..., description="Longitude of location"),
    radius_km: float = Query(1.0, description="Radius around point in km")
):
    """FastAPI endpoint wrapper for impact calculation"""
    return calculate_impact_score(lat, lon, radius_km)
