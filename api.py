<<<<<<< Updated upstream
import datetime
import math
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

                # Küresel asteroit modeli ve ortalama kayaç yoğunluğu (2.6 g/cm³ = 2600 kg/m³) ile kütle hesabı
                yaricap_m = (avg_diameter_km * 1000) / 2
                hacim_m3 = (4 / 3) * math.pi * (yaricap_m ** 3)
                kutle_ton = (hacim_m3 * 2600) / 1000

                velocity_kms = float(approach.get("relative_velocity", {}).get("kilometers_per_second", 0))
                miss_distance_ld = float(approach.get("miss_distance", {}).get("lunar", 0))
                miss_distance_km = float(approach.get("miss_distance", {}).get("kilometers", 0))

                asteroids.append({
                    "ID": neo.get("id"),
                    "Asteroit Adı": neo.get("name"),
                    "Yaklaşma Tarihi": date_str,
                    "Ortalama Çap (km)": round(avg_diameter_km, 4),
                    "Tahmini Kütle (Ton)": round(kutle_ton, 1),
                    "Hız (km/s)": round(velocity_kms, 2),
                    "En Yakın Mesafe (LD)": round(miss_distance_ld, 2),
                    "En Yakın Mesafe (km)": round(miss_distance_km, 0),
                    "Potansiyel Tehlikeli": neo.get("is_potentially_hazardous_asteroid", False)
                })

        return pd.DataFrame(asteroids), None
    except Exception as e:
        return None, f"Bağlantı Hatası: {e}"


def calculate_risk_score(df):
    scored_df = df.copy()

    # Streamlit önbelleğinden eski veri gelirse yeni sütunları otomatik tamamla
    if "Tahmini Kütle (Ton)" not in scored_df.columns:
        yaricap_m = (scored_df["Ortalama Çap (km)"] * 1000) / 2
        scored_df["Tahmini Kütle (Ton)"] = (((4 / 3) * math.pi * (yaricap_m ** 3) * 2600) / 1000).round(1)

    if "En Yakın Mesafe (LD)" not in scored_df.columns and "Mesafe (Ay Mesafesi - LD)" in scored_df.columns:
        scored_df["En Yakın Mesafe (LD)"] = scored_df["Mesafe (Ay Mesafesi - LD)"]
        scored_df = scored_df.drop(columns=["Mesafe (Ay Mesafesi - LD)"])

    if "En Yakın Mesafe (km)" not in scored_df.columns and "Mesafe (km)" in scored_df.columns:
        scored_df["En Yakın Mesafe (km)"] = scored_df["Mesafe (km)"]
        scored_df = scored_df.drop(columns=["Mesafe (km)"])

    raw_score = (
        (scored_df["Ortalama Çap (km)"] * 50) + (scored_df["Hız (km/s)"] * 1.5)
    ) / (scored_df["En Yakın Mesafe (LD)"] + 0.1)

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


def nasa_uyari_paketi_olustur(yuksek_riskli_df, tarih_str, test_modu=False):
    """Yüksek risk sınırına (70+) giren asteroitler için NASA PDCO telemetri uyarı paketi üretir."""
    gonderim_zamani = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    hedefler = []
    for _, row in yuksek_riskli_df.iterrows():
        hedefler.append({
            "neo_id": str(row["ID"]),
            "name": row["Asteroit Adı"],
            "risk_score": float(row["Risk Skoru (0-100)"]),
            "threat_level": row["Tehlike Seviyesi"],
            "estimated_diameter_km": float(row["Ortalama Çap (km)"]),
            "estimated_mass_tons": float(row["Tahmini Kütle (Ton)"]),
            "relative_velocity_kms": float(row["Hız (km/s)"]),
            "closest_approach_ld": float(row["En Yakın Mesafe (LD)"]),
            "closest_approach_km": float(row["En Yakın Mesafe (km)"])
        })

    return {
        "alert_id": f"NASA-PDCO-{tarih_str.replace('-', '')}-{'TEST' if test_modu else 'AUTO'}",
        "status": "TRANSMITTED",
        "mode": "SIMULATION_TEST" if test_modu else "AUTOMATIC_THRESHOLD_TRIGGER",
        "recipient": "NASA Planetary Defense Coordination Office (PDCO)",
        "trigger_rule": "Risk Skoru >= 70 (Yüksek Risk Sınırı)",
        "observation_date": tarih_str,
        "transmitted_at": gonderim_zamani,
        "high_risk_object_count": len(hedefler),
        "targets": hedefler
    }
=======
import requests
import pandas as pd
import numpy as np

def get_neo_data(start_date, end_date, api_key="DEMO_KEY"):
    """
    NASA NEO API'sinden belirtilen tarih aralığındaki asteroit verilerini çeker 
    ve işlenmiş bir Pandas DataFrame döndürür.
    """
    url = f"https://api.nasa.gov/neo/rest/v1/feed?start_date={start_date}&end_date={end_date}&api_key={api_key}"
    
    try:
        response = requests.get(url)
        if response.status_code != 200:
            print(f"API Hatası: {response.status_code}")
            return None
            
        data = response.json()
        near_earth_objects = data.get("near_earth_objects", {})
        
        asteroids_list = []
        
        # Günlük döngü (NASA API verileri tarihlere göre gruplar)
        for date_key, ast_array in near_earth_objects.items():
            for ast in ast_array:
                name = ast.get("name")
                id_val = ast.get("id")
                is_hazardous = ast.get("is_potentially_hazardous_asteroid", False)
                
                # Çap bilgileri (Kilometre cinsinden ortalama)
                diameter_min = ast.get("estimated_diameter", {}).get("kilometers", {}).get("estimated_diameter_min", 0)
                diameter_max = ast.get("estimated_diameter", {}).get("kilometers", {}).get("estimated_diameter_max", 0)
                avg_diameter = (diameter_min + diameter_max) / 2
                
                # Yaklaşma ve Hız Bilgileri (İlk yaklaşma verisini baz alıyoruz)
                close_approach_data = ast.get("close_approach_data", [])
                if close_approach_data:
                    cad = close_approach_data[0]
                    miss_distance_km = float(cad.get("miss_distance", {}).get("kilometers", 0))
                    speed_km_s = float(cad.get("relative_velocity", {}).get("kilometers_per_second", 0))
                    approach_date = cad.get("calendar_date_full", cad.get("close_approach_date", ""))
                else:
                    miss_distance_km = 0.0
                    speed_km_s = 0.0
                    approach_date = ""

                asteroids_list.append({
                    "ID": id_val,
                    "Name": name,
                    "Hazardous": is_hazardous,
                    "Diameter_Km": round(avg_diameter, 3),
                    "Miss_Distance_Km": round(miss_distance_km, 2),
                    "Speed_Km_s": round(speed_km_s, 2),
                    "Approach_Date": approach_date
                })
                
        df = pd.DataFrame(asteroids_list)
        return df

    except Exception as e:
        print(f"Veri çekilirken hata oluştu: {e}")
        return None

def calculate_risk_score(df):
    """
    Asteroitlerin mesafe ve hızına göre 0-100 arası 'Orbital Risk Skoru' hesaplar.
    """
    if df is None or df.empty:
        return df
        
    max_dist = df["Miss_Distance_Km"].max() if df["Miss_Distance_Km"].max() > 0 else 1
    max_speed = df["Speed_Km_s"].max() if df["Speed_Km_s"].max() > 0 else 1
    
    dist_score = 1 - (df["Miss_Distance_Km"] / max_dist)
    speed_score = df["Speed_Km_s"] / max_speed
    
    hazard_multiplier = df["Hazardous"].astype(int) * 0.4
    
    raw_score = (dist_score * 0.3) + (speed_score * 0.3) + hazard_multiplier
    
    df["Risk_Score"] = (raw_score * 100).round(1)
    df = df.sort_values(by="Risk_Score", ascending=False).reset_index(drop=True)
    return df

def get_summary_metrics(df):
    """
    DataFrame üzerinden jüri için özet metrikleri hesaplar.
    """
    if df is None or df.empty:
        return 0, 0, 0.0
    
    total_count = len(df)
    hazardous_count = int(df["Hazardous"].sum())
    max_risk = float(df["Risk_Score"].max()) if "Risk_Score" in df.columns else 0.0
    
    return total_count, hazardous_count, max_risk

# Test bloğu en alta alındı
if __name__ == "__main__":
    print("NASA API test ediliyor...")
    test_df = get_neo_data("2026-11-14", "2026-11-14", api_key="nfKCCpwTCJpNDMtfTKm9MF8Ct768M9Hg7RL69NgJ")
    if test_df is not None:
        scored_df = calculate_risk_score(test_df)
        print(scored_df.head())
>>>>>>> Stashed changes
