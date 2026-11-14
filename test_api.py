import requests

# NASA API Endpoint (CNEOS / Close Approach Data örnek uç noktası)
url = "https://api.nasa.gov/neo/rest/v1/feed?start_date=2026-11-14&end_date=2026-11-14&api_key=DEMO_KEY"

response = requests.get(url)

if response.status_code == 200:
    data = response.json()
    print("BAŞARILI! NASA API'den veri alındı.")
    print("Bugünkü toplam yakınlaşan asteroit sayısı:", data.get("element_count"))
else:
    print("Hata oluştu, kod:", response.status_code)
    print(response.text)