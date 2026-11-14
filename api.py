import socket
import requests
import pandas as pd
import urllib3.util.connection as urllib3_cn

# IPv6 bekleme takılmasını önlemek için doğrudan IPv4 kullan
def _force_ipv4():
    return socket.AF_INET

urllib3_cn.allowed_gai_family = _force_ipv4


def get_neo_data(start_date, end_date, api_key="DEMO_KEY"):
    url = f"https://api.nasa.gov/neo/rest/v1/feed?start_date={start_date}&end_date={end_date}&api_key={api_key}"
    try:
        response = requests.get(url, timeout=(5, 8))
        if response.status_code != 200:
            return None, f"NASA API Hata Kodu: {response.status_code}"

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

                velocity_kms = float(approach.get("relative_velocity", {}).get("kilometers_per_second", 0))
                miss_distance_ld = float(approach.get("miss_distance", {}).get("lunar", 0))
                miss_distance_km = float(approach.get("miss_distance", {}).get("kilometers", 0))

                asteroids.append({
                    "ID": neo.get("id"),
                    "Asteroit Adı": neo.get("name"),
                    "Yaklaşma Tarihi": date_str,
                    "Ortalama Çap (km)": round(avg_diameter_km, 4),
                    "Hız (km/s)": round(velocity_kms, 2),
                    "Mesafe (Ay Mesafesi - LD)": round(miss_distance_ld, 2),
                    "Mesafe (km)": round(miss_distance_km, 0),
                    "Potansiyel Tehlikeli": neo.get("is_potentially_hazardous_asteroid", False)
                })

        return pd.DataFrame(asteroids), None
    except Exception as e:
        return None, f"Bağlantı Hatası: {e}"


def calculate_risk_score(df):
    scored_df = df.copy()

    raw_score = (
        (scored_df["Ortalama Çap (km)"] * 50) + (scored_df["Hız (km/s)"] * 1.5)
    ) / (scored_df["Mesafe (Ay Mesafesi - LD)"] + 0.1)

    hazard_multiplier = scored_df["Potansiyel Tehlikeli"].apply(lambda x: 1.5 if x else 1.0)
    scored_df["Risk Skoru (0-100)"] = (raw_score * hazard_multiplier * 10).clip(upper=100).round(2)

    def seviye_belirle(skor):
        if skor >= 70:
            return "Yüksek Risk"
        elif skor >= 35:
            return "Orta Risk"
        return "Düşük Risk"

    scored_df["Tehlike Seviyesi"] = scored_df["Risk Skoru (0-100)"].apply(seviye_belirle)
    scored_df = scored_df.sort_values(by="Risk Skoru (0-100)", ascending=False).reset_index(drop=True)
    return scored_df