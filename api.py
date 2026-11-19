import datetime
import math
import uuid
import pandas as pd
import requests


def get_neo_data(start_date, end_date, api_key="DEMO_KEY"):
    """NASA NeoWs API üzerinden belirtilen tarih aralığındaki asteroit verilerini çeker."""
    url = "https://api.nasa.gov/neo/rest/v1/feed"
    params = {
        "start_date": start_date,
        "end_date": end_date,
        "api_key": api_key,
    }

    try:
        response = requests.get(url, params=params, timeout=15)
        if response.status_code != 200:
            return None, f"NASA API Hatası (HTTP {response.status_code}): {response.text}"

        data = response.json()
        near_earth_objects = data.get("near_earth_objects", {})

        kayitlar = []
        # Ortalama kondritik asteroit yoğunluğu: 2.6 g/cm³ = 2.6 * 10^9 ton/km³
        yogunluk_ton_km3 = 2.6e9

        for tarih_anahtari, neo_listesi in near_earth_objects.items():
            for neo in neo_listesi:
                neo_id = str(neo.get("id", ""))
                ad = neo.get("name", "Bilinmeyen Cisim")
                pha = bool(neo.get("is_potentially_hazardous_asteroid", False))

                cap_bilgisi = neo.get("estimated_diameter", {}).get("kilometers", {})
                min_cap = float(cap_bilgisi.get("estimated_diameter_min", 0.0))
                max_cap = float(cap_bilgisi.get("estimated_diameter_max", 0.0))
                ort_cap_km = round((min_cap + max_cap) / 2.0, 4)

                # Küre hacim formülü: V = (4/3) * pi * r^3
                yaricap_km = ort_cap_km / 2.0
                hacim_km3 = (4.0 / 3.0) * math.pi * (yaricap_km ** 3)
                tahmini_kutle_ton = round(hacim_km3 * yogunluk_ton_km3, 1)

                yaklasmalar = neo.get("close_approach_data", [])
                if not yaklasmalar:
                    continue

                ilk_yaklasma = yaklasmalar[0]
                yaklasma_tarihi = ilk_yaklasma.get("close_approach_date", tarih_anahtari)
                hiz_kms = round(
                    float(ilk_yaklasma.get("relative_velocity", {}).get("kilometers_per_second", 0.0)),
                    2,
                )
                mesafe_ld = round(
                    float(ilk_yaklasma.get("miss_distance", {}).get("lunar", 0.0)),
                    2,
                )
                mesafe_km = round(
                    float(ilk_yaklasma.get("miss_distance", {}).get("kilometers", 0.0)),
                    0,
                )

                kayitlar.append(
                    {
                        "ID": neo_id,
                        "Asteroit Adı": ad,
                        "Yaklaşma Tarihi": yaklasma_tarihi,
                        "Ortalama Çap (km)": ort_cap_km,
                        "Tahmini Kütle (Ton)": tahmini_kutle_ton,
                        "Hız (km/s)": hiz_kms,
                        "En Yakın Mesafe (LD)": mesafe_ld,
                        "En Yakın Mesafe (km)": mesafe_km,
                        "Potansiyel Tehlikeli": pha,
                    }
                )

        if not kayitlar:
            return pd.DataFrame(), None

        df = pd.DataFrame(kayitlar)
        return df, None

    except requests.exceptions.Timeout:
        return None, "NASA sunucusuna bağlanırken zaman aşımı (Timeout) oluştu. Lütfen tekrar deneyin."
    except requests.exceptions.RequestException as e:
        return None, f"Ağ bağlantı hatası: {e}"
    except Exception as e:
        return None, f"Veri işleme hatası: {e}"


def calculate_risk_score(df):
    """Mesafe, çap, hız ve PHA durumuna göre 0-100 arası çok kriterli risk skoru hesaplar."""
    sonuc_df = df.copy()
    skorlar = []
    seviyeler = []

    for _, row in sonuc_df.iterrows():
        mesafe_ld = max(float(row["En Yakın Mesafe (LD)"]), 0.01)
        cap_km = float(row["Ortalama Çap (km)"])
        hiz_kms = float(row["Hız (km/s)"])
        pha = bool(row["Potansiyel Tehlikeli"])

        # 1. Yakınlık puanı (Maks 40 puan - 1 LD ve altı maksimum tehdit)
        mesafe_puani = min(40.0, (1.0 / (mesafe_ld ** 0.65)) * 22.0)

        # 2. Boyut / Kütle puanı (Maks 30 puan - 1 km çap ve üzeri maksimum)
        cap_puani = min(30.0, (cap_km / 0.8) * 30.0)

        # 3. Kinetik hız puanı (Maks 20 puan - 35 km/s referans)
        hiz_puani = min(20.0, (hiz_kms / 35.0) * 20.0)

        # 4. NASA PHA statü bonusu (10 puan)
        pha_puani = 10.0 if pha else 0.0

        toplam_skor = round(min(100.0, mesafe_puani + cap_puani + hiz_puani + pha_puani), 2)
        skorlar.append(toplam_skor)

        if toplam_skor >= 70.0:
            seviyeler.append("Yüksek Risk")
        elif toplam_skor >= 35.0:
            seviyeler.append("Orta Risk")
        else:
            seviyeler.append("Düşük Risk")

    sonuc_df["Risk Skoru (0-100)"] = skorlar
    sonuc_df["Tehlike Seviyesi"] = seviyeler
    sonuc_df = sonuc_df.sort_values(by="Risk Skoru (0-100)", ascending=False).reset_index(drop=True)
    return sonuc_df


def nasa_uyari_paketi_olustur(yuksek_riskli_df, analiz_tarihi, test_modu=False):
    """Risk skoru 70 ve üzerindeki cisimler için NASA PDCO telemetri uyarı paketi üretir."""
    zaman_damgasi = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    uyari_kodu = f"PDCO-ALT-{uuid.uuid4().hex[:8].upper()}"

    cisimler = []
    for _, row in yuksek_riskli_df.iterrows():
        cisimler.append(
            {
                "neo_id": str(row["ID"]),
                "designation": str(row["Asteroit Adı"]),
                "close_approach_date": str(row["Yaklaşma Tarihi"]),
                "risk_score": float(row["Risk Skoru (0-100)"]),
                "threat_level": str(row["Tehlike Seviyesi"]),
                "miss_distance_ld": float(row["En Yakın Mesafe (LD)"]),
                "miss_distance_km": float(row["En Yakın Mesafe (km)"]),
                "relative_velocity_kms": float(row["Hız (km/s)"]),
                "mean_diameter_km": float(row["Ortalama Çap (km)"]),
                "estimated_mass_tons": float(row["Tahmini Kütle (Ton)"]),
                "potentially_hazardous": bool(row["Potansiyel Tehlikeli"]),
            }
        )

    return {
        "alert_id": uyari_kodu,
        "protocol": "NASA-PDCO-TELEMETRY-v1.2",
        "source_system": "OrbitalGuard NEO Risk Simulator",
        "simulation_test_mode": bool(test_modu),
        "analysis_date": analiz_tarihi,
        "transmitted_at": zaman_damgasi,
        "recipient": "NASA Planetary Defense Coordination Office (PDCO)",
        "alert_threshold": 70.0,
        "detected_high_risk_count": len(cisimler),
        "objects": cisimler,
    }
