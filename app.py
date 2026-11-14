
import datetime
import streamlit as st
import plotly.express as px
from api import get_neo_data, calculate_risk_score

st.set_page_config(page_title="OrbitalGuard: NEO Risk Simulator", layout="wide")

st.title("🛰️ OrbitalGuard: NEO Risk Simulator")

st.sidebar.header("Gözlem Parametreleri")
secilen_tarih = st.sidebar.date_input(
    "Analiz Tarihi Seçin:",
    value=datetime.date(2026, 11, 14)
)
tarih_str = secilen_tarih.strftime("%Y-%m-%d")

@st.cache_data(ttl=600)
def veriyi_getir(tarih):
    return get_neo_data(tarih, tarih, api_key="nfKCCpwTCJpNDMtfTKm9MF8Ct768M9Hg7RL69NgJ")

with st.spinner("NASA sunucusundan asteroit verileri çekiliyor..."):
    df, hata = veriyi_getir(tarih_str)

if hata:
    st.error(hata)
elif df is not None and not df.empty:
    scored_df = calculate_risk_score(df)

    # Üst özet metrikleri
    col1, col2, col3 = st.columns(3)
    col1.metric("Toplam Tespit Edilen Asteroit", len(scored_df))
    col2.metric("En Yüksek Risk Skoru", f"{scored_df['Risk Skoru (0-100)'].max()} / 100")
    col3.metric("Potansiyel Tehlikeli Sayısı", int(scored_df["Potansiyel Tehlikeli"].sum()))

    # Asteroit veri tablosu
    st.subheader(f"{tarih_str} Tarihli Asteroit Verileri ve Risk Skorları")
    st.dataframe(scored_df, use_container_width=True)

    # İnteraktif Plotly Scatter Plot
    st.subheader("Asteroitin Hızı ve Dünya'ya Mesafesi Grafiği")

    plot_df = scored_df.copy()
    plot_df["Durum"] = plot_df["Potansiyel Tehlikeli"].map({
        True: "Tehlikeli",
        False: "Normal"
    })

    fig = px.scatter(
        plot_df,
        x="Mesafe (Ay Mesafesi - LD)",
        y="Hız (km/s)",
        color="Durum",
        color_discrete_map={
            "Tehlikeli": "#EF4444",
            "Normal": "#3B82F6"
        },
        hover_name="Asteroit Adı",
        hover_data={
            "Durum": True,
            "Ortalama Çap (km)": True,
            "Risk Skoru (0-100)": True,
            "Mesafe (km)": True
        },
        labels={
            "Mesafe (Ay Mesafesi - LD)": "Dünya'ya Mesafe (Ay Mesafesi - LD)",
            "Hız (km/s)": "Bağıl Hız (km/s)"
        }
    )

    fig.update_traces(marker=dict(size=13, line=dict(width=1, color="white")))
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Bu tarih için kayıtlı asteroit verisi bulunamadı.")
    import streamlit as st
from api import get_neo_data, calculate_risk_score, get_summary_metrics
import pandas as pd

# Sayfa yapılandırması
st.set_page_config(page_title="OrbitalGuard", page_icon="🛰️", layout="wide")

# Oturumda (session_state) seçili asteroit hafızası yoksa başlatalım
if "selected_asteroid" not in st.session_state:
    st.session_state.selected_asteroid = None

# ==========================================
# 1. DURUM: ANA LİSTE SAYFASI
# ==========================================
if st.session_state.selected_asteroid is None:
    st.title("🛰️ OrbitalGuard: NEO Risk Simülatörü")
    st.write("NASA CNEOS verileriyle anlık yakınlaşan asteroit takip paneli.")

    # Veriyi çek ve skorla
    df = get_neo_data("2026-11-14", "2026-11-14", api_key="nfKCCpwTCJpNDMtfTKm9MF8Ct768M9Hg7RL69NgJ")
    
    if df is not None and not df.empty:
        scored_df = calculate_risk_score(df)
        
        # Metrik Kartları (Senin yazdığın fonksiyonla)
        total, hazardous, max_risk = get_summary_metrics(scored_df)
        c1, c2, c3 = st.columns(3)
        c1.metric("Toplam Taranan NEO", total)
        c2.metric("Potansiyel Tehlikeli", hazardous)
        c3.metric("En Yüksek Risk Skoru", f"{max_risk}/100")
        
        st.markdown("---")
        st.subheader("📋 Yakınlaşan Asteroitler Listesi")
        
        # Her asteroit için şık bir satır ve "Detaya Git" butonu oluşturalım
        for index, row in scored_df.iterrows():
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            col1.write(f"**{row['Name']}**")
            col2.write(f"Risk Skoru: **{row['Risk_Score']}**")
            col3.write("🚨 Tehlikeli" if row['Hazardous'] else "✅ Güvenli")
            
            # Butona basıldığında bu asteroitin verisini hafızaya at ve sayfayı yenile (rerun)
            if col4.button("İncele ➔", key=f"btn_{row['ID']}"):
                st.session_state.selected_asteroid = row.to_dict()
                st.rerun()
    else:
        st.error("Veri yüklenemedi veya API yanıt vermedi.")

# ==========================================
# 2. DURUM: ÖZEL ASTEROİT DETAY SAYFASI ("YENİ SAYFA")
# ==========================================
else:
    ast = st.session_state.selected_asteroid

    # Geri dön butonu
    if st.button("⬅️ Ana Listeye Geri Dön"):
        st.session_state.selected_asteroid = None
        st.rerun()

    st.title(f"☄️ Asteroit Detay Paneli: {ast['Name']}")
    
    # Üst Kısım: Temsili / Hareketli NASA Uzay Görseli (GIF veya Animasyon Hissi)
    st.image(
        "https://media.giphy.com/media/26ufc8n6KYsFpuzoA/giphy.gif",
        caption="NASA CNEOS - Simüle Edilmiş Yörünge ve Yaklaşma Görselleştirmesi",
        use_container_width=True
    )
    
    st.markdown("---")
    
    # Alt Kısım: Şık Tasarımlı Detay Bilgileri ve Kartlar
    col1, col2, col3 = st.columns(3)
    col1.metric("Orbital Risk Skoru", f"{ast['Risk_Score']} / 100")
    col2.metric("Ortalama Çap", f"{ast['Diameter_Km']} km")
    col3.metric("Göreceli Hız", f"{ast['Speed_Km_s']} km/s")

    st.markdown("### 🔬 Fiziksel ve Yörünge Parametreleri")
    
    # Bilgi kutusu içinde detaylar
    st.info(
        f"**NASA Benzersiz ID:** {ast['ID']} \n\n"
        f"**Dünyaya En Yakın Geçiş Mesafesi:** {ast['Miss_Distance_Km']:,.2f} km \n\n"
        f"**Tehlike Sınıflandırması:** {'🚨 Potansiyel Tehlikeli Nesne (PHA)' if ast['Hazardous'] else '✅ Güvenli Menzil / Tehdit Yok'}"
    )