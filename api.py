import datetime
import math
import socket
import requests
import pandas as pd
import urllib3.util.connection as urllib3_cn

# Force direct IPv4 connection to prevent IPv6 hanging issues
def _force_ipv4():
    return socket.AF_INET

urllib3_cn.allowed_gai_family = _force_ipv4


def get_neo_data(start_date, end_date, api_key="DEMO_KEY"):
    """
    Fetches near-Earth asteroid data from the NASA NEO API for the specified date range 
    and returns a processed Pandas DataFrame.
    """
    url = f"https://api.nasa.gov/neo/rest/v1/feed?start_date={start_date}&end_date={end_date}&api_key={api_key}"
    
    try:
        response = requests.get(url, timeout=(5, 8))
        if response.status_code != 200:
            return None, f"NASA API Error Code: {response.status_code}"

        data = response.json()
        near_earth_objects = data.get("near_earth_objects", {})

        asteroids = []
        for date_str, neo_list in near_earth_objects.items():
            for neo in neo_list:
                approaches = neo.get("close_approach_data") or [{}]
                approach = approaches[0]

                diameter = neo.get("estimated_diameter", {}).get("kilometers", {})
                min_d = float(diameter.get("estimated_diameter_min", 0))
                max_d = float(diameter.get("estimated_diameter_max", 0))
                avg_diameter_km = (min_d + max_d) / 2

                # Mass calculation using spherical asteroid model and average rock density (2.6 g/cm³ = 2600 kg/m³)
                radius_m = (avg_diameter_km * 1000) / 2
                volume_m3 = (4 / 3) * math.pi * (radius_m ** 3)
                mass_tons = (volume_m3 * 2600) / 1000

                velocity_kms = float(approach.get("relative_velocity", {}).get("kilometers_per_second", 0))
                miss_distance_ld = float(approach.get("miss_distance", {}).get("lunar", 0))
                miss_distance_km = float(approach.get("miss_distance", {}).get("kilometers", 0))

                asteroids.append({
                    "ID": neo.get("id"),
                    "Asteroid Name": neo.get("name"),
                    "Approach Date": date_str,
                    "Average Diameter (km)": round(avg_diameter_km, 4),
                    "Estimated Mass (Tons)": round(mass_tons, 1),
                    "Velocity (km/s)": round(velocity_kms, 2),
                    "Closest Approach (LD)": round(miss_distance_ld, 2),
                    "Closest Approach (km)": round(miss_distance_km, 0),
                    "Potentially Hazardous": neo.get("is_potentially_hazardous_asteroid", False)
                })

        return pd.DataFrame(asteroids), None
    except Exception as e:
        return None, f"Connection Error: {e}"


def calculate_risk_score(df):
    """
    Calculates orbital risk scores and threat levels for asteroids.
    """
    scored_df = df.copy()

    # Backwards compatibility check for cached data
    if "Estimated Mass (Tons)" not in scored_df.columns:
        radius_m = (scored_df["Average Diameter (km)"] * 1000) / 2
        scored_df["Estimated Mass (Tons)"] = (((4 / 3) * math.pi * (radius_m ** 3) * 2600) / 1000).round(1)

    if "Closest Approach (LD)" not in scored_df.columns and "Mesafe (Ay Mesafesi - LD)" in scored_df.columns:
        scored_df["Closest Approach (LD)"] = scored_df["Mesafe (Ay Mesafesi - LD)"]
        scored_df = scored_df.drop(columns=["Mesafe (Ay Mesafesi - LD)"])

    if "Closest Approach (km)" not in scored_df.columns and "Mesafe (km)" in scored_df.columns:
        scored_df["Closest Approach (km)"] = scored_df["Mesafe (km)"]
        scored_df = scored_df.drop(columns=["Mesafe (km)"])

    raw_score = (
        (scored_df["Average Diameter (km)"] * 50) + (scored_df["Velocity (km/s)"] * 1.5)
    ) / (scored_df["Closest Approach (LD)"] + 0.1)

    hazard_multiplier = scored_df["Potentially Hazardous"].apply(lambda x: 1.5 if x else 1.0)
    scored_df["Risk Score (0-100)"] = (raw_score * hazard_multiplier * 10).clip(upper=100).round(2)

    def determine_threat_level(score):
        if score >= 70:
            return "High Risk"
        elif score >= 35:
            return "Medium Risk"
        return "Low Risk"

    scored_df["Threat Level"] = scored_df["Risk Score (0-100)"].apply(determine_threat_level)
    scored_df = scored_df.sort_values(by="Risk Score (0-100)", ascending=False).reset_index(drop=True)
    return scored_df


def nasa_alert_package_generator(high_risk_df, date_str, test_mode=False):
    """Generates a NASA PDCO telemetry alert package for asteroids hitting the high-risk threshold (70+)."""
    transmission_time = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    targets = []
    for _, row in high_risk_df.iterrows():
        targets.append({
            "neo_id": str(row["ID"]),
            "name": row["Asteroid Name"],
            "risk_score": float(row["Risk Score (0-100)"]),
            "threat_level": row["Threat Level"],
            "estimated_diameter_km": float(row["Average Diameter (km)"]),
            "estimated_mass_tons": float(row["Estimated Mass (Tons)"]),
            "relative_velocity_kms": float(row["Velocity (km/s)"]),
            "closest_approach_ld": float(row["Closest Approach (LD)"]),
            "closest_approach_km": float(row["Closest Approach (km)"])
        })

    return {
        "alert_id": f"NASA-PDCO-{date_str.replace('-', '')}-{'TEST' if test_mode else 'AUTO'}",
        "status": "TRANSMITTED",
        "mode": "SIMULATION_TEST" if test_mode else "AUTOMATIC_THRESHOLD_TRIGGER",
        "recipient": "NASA Planetary Defense Coordination Office (PDCO)",
        "trigger_rule": "Risk Score >= 70 (High Risk Threshold)",
        "observation_date": date_str,
        "transmitted_at": transmission_time,
        "high_risk_object_count": len(targets),
        "targets": targets
    }


# Test block
if __name__ == "__main__":
    print("Testing NASA API...")
    test_df, err = get_neo_data("2026-11-14", "2026-11-14", api_key="nfKCCpwTCJpNDMtfTKm9MF8Ct768M9Hg7RL69NgJ")
    if test_df is not None:
        scored_df = calculate_risk_score(test_df)
        print(scored_df.head())
    else:
        print(err)