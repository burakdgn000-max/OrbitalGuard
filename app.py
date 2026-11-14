import datetime
import math
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from api import get_neo_data, calculate_risk_score, nasa_uyari_paketi_olustur

st.set_page_config(page_title="OrbitalGuard: NEO Risk Simulator", layout="wide")


def risk_rengi_getir(skor, seviye=""):
    """Risk skoruna ve seviyesine göre standart renk kodunu döndürür."""
    if float(skor) >= 70 or seviye == "Yüksek Risk":
        return "#EF4444"  # Kırmızı: Yüksek Risk
    elif float(skor) >= 35 or seviye == "Orta Risk":
        return "#F59E0B"  # Turuncu: Orta Risk
    return "#3B82F6"      # Mavi: Düşük Risk


def tablo_risk_stili(deger):
    """Ana tablodaki Tehlike Seviyesi sütununu risk rengine göre boyar."""
    if deger == "Yüksek Risk":
        return "color: #EF4444; font-weight: 700;"
    elif deger == "Orta Risk":
        return "color: #F59E0B; font-weight: 700;"
    return "color: #3B82F6; font-weight: 700;"


def mesafe_etiketi_olustur(x_pos, y_pos, ld_degeri):
    """Gri çizginin tam ortasında duran okunaklı mesafe etiketini üretir."""
    return dict(
        x=x_pos * 0.5,
        y=y_pos * 0.5,
        text=f"<b>{ld_degeri:.2f} LD</b>",
        showarrow=False,
        bgcolor="rgba(255, 255, 255, 0.92)",
        bordercolor="#94A3B8",
        borderwidth=1,
        borderpad=3,
        font=dict(color="#334155", size=11, family="Arial"),
    )


def dunya_yorunge_simulasyonu(secili_df):
    """Ortada mavi Dünya, tam boy yörüngeler, Pan/Zoom destekli harita ve kaldığı yerden devam eden animasyon çizer."""
    fig = go.Figure()

    # En yakın geçiş mesafelerini ölçekle (Dünya merkezde her zaman net kalsın)
    ham_mesafeler = [max(float(m), 0.12) for m in secili_df["En Yakın Mesafe (LD)"]]
    min_gecisler = [1.45 + math.sqrt(m) * 1.15 for m in ham_mesafeler]
    ay_yorunge_r = 1.45 + math.sqrt(1.0) * 1.15  # 1 LD Ay yörüngesi referans çemberi
    dis_radar_r = max(max(min_gecisler), ay_yorunge_r) * 1.35
    max_eksen = dis_radar_r * 1.18

    # Harita detayları: Dış radar mesafe halkası
    tam_aci = [2 * math.pi * k / 120 for k in range(121)]
    fig.add_trace(
        go.Scatter(
            x=[dis_radar_r * math.cos(t) for t in tam_aci],
            y=[dis_radar_r * math.sin(t) for t in tam_aci],
            mode="lines",
            line=dict(color="rgba(148, 163, 184, 0.25)", width=1),
            hoverinfo="skip",
            showlegend=False,
        )
    )

    # Ay Yörüngesi (1 LD) kesikli referans çemberi
    fig.add_trace(
        go.Scatter(
            x=[ay_yorunge_r * math.cos(t) for t in tam_aci],
            y=[ay_yorunge_r * math.sin(t) for t in tam_aci],
            mode="lines",
            line=dict(color="#EAB308", width=1.8, dash="dash"),
            name="Ay Yörüngesi (1 LD)",
            hovertemplate="<b>Ay Yörüngesi Referansı (1 LD ≈ 384.400 km)</b><extra></extra>",
        )
    )

    # Dünya atmosfer halesi (yuvarlak)
    fig.add_trace(
        go.Scatter(
            x=[0],
            y=[0],
            mode="markers",
            marker=dict(
                size=52,
                symbol="circle",
                color="rgba(37, 99, 235, 0.16)",
                line=dict(width=1.5, color="rgba(37, 99, 235, 0.35)"),
            ),
            hoverinfo="skip",
            showlegend=False,
        )
    )

    # Merkezdeki Tam Görünür Mavi Dünya (yuvarlak)
    fig.add_trace(
        go.Scatter(
            x=[0],
            y=[0],
            mode="markers+text",
            marker=dict(
                size=32,
                symbol="circle",
                color="#2563EB",
                line=dict(width=2, color="#1D4ED8"),
            ),
            text=["Dünya"],
            textposition="bottom center",
            textfont=dict(size=13, family="Arial Black"),
            hovertemplate="<b>Dünya (Merkez Referans)</b><extra></extra>",
            name="Dünya",
        )
    )

    # Simülasyon süresi en yavaş asteroide göre belirlenir (tüm asteroitler yörüngesini tamamlar)
    en_dusuk_hiz = max(float(secili_df["Hız (km/s)"].min()), 0.5)
    en_yuksek_hiz = max(float(secili_df["Hız (km/s)"].max()), en_dusuk_hiz)
    hiz_fark_orani = min(en_yuksek_hiz / en_dusuk_hiz, 2.2)
    kare_sayisi = min(max(int(48 * hiz_fark_orani), 48), 100)

    dinamik_nesneler = []
    animasyonlu_iz_indeksleri = []
    toplam_secili = len(secili_df)
    tam_yol_yarim = dis_radar_r * 1.05

    for i, (_, ast) in enumerate(secili_df.iterrows()):
        ad = ast["Asteroit Adı"]
        hiz_kms = float(ast["Hız (km/s)"])
        mesafe_ld = float(ast["En Yakın Mesafe (LD)"])
        mesafe_km = float(ast["En Yakın Mesafe (km)"])
        cap_km = float(ast["Ortalama Çap (km)"])
        kutle_ton = float(ast["Tahmini Kütle (Ton)"])
        risk = float(ast["Risk Skoru (0-100)"])
        seviye = ast["Tehlike Seviyesi"]

        yorunge_renk = risk_rengi_getir(risk, seviye)

        # Asteroit çapına göre yuvarlak boyutunu ölçekle (15 px - 26 px arası)
        asteroit_boyut = min(max(int(15 + cap_km * 14), 15), 26)

        d_min = min_gecisler[i]
        yaklasma_acisi = (i * (2 * math.pi / max(toplam_secili, 3))) + 0.35

        # 1) Tam boy kavisli yakın geçiş yörünge hattı
        rota_adimlari = [-1.0 + (2.0 * k / 80) for k in range(81)]
        orb_x, orb_y = [], []
        for s in rota_adimlari:
            u = s * tam_yol_yarim
            v = d_min + 0.12 * (u ** 2) / max(d_min, 0.9)
            rx = u * math.cos(yaklasma_acisi) - v * math.sin(yaklasma_acisi)
            ry = u * math.sin(yaklasma_acisi) + v * math.cos(yaklasma_acisi)
            orb_x.append(rx)
            orb_y.append(ry)

        fig.add_trace(
            go.Scatter(
                x=orb_x,
                y=orb_y,
                mode="lines",
                line=dict(color=yorunge_renk, width=2.0, dash="dot"),
                opacity=0.68,
                name=f"{ad} Yörüngesi",
                hoverinfo="skip",
            )
        )

        # 2) Animasyon kareleri: En yavaş asteroit son karede bitirir, hızlı olanlar erken bitirip uçta bekler
        goreceli_hiz = max(hiz_kms / en_dusuk_hiz, 1.0)
        kare_x, kare_y, anlik_ld_listesi, anlik_km_listesi = [], [], [], []
        for k in range(kare_sayisi):
            ilerleme = k / (kare_sayisi - 1)
            s = min(-1.0 + (2.0 * ilerleme * goreceli_hiz), 1.0)
            u = s * tam_yol_yarim
            v = d_min + 0.12 * (u ** 2) / max(d_min, 0.9)
            rx = u * math.cos(yaklasma_acisi) - v * math.sin(yaklasma_acisi)
            ry = u * math.sin(yaklasma_acisi) + v * math.cos(yaklasma_acisi)

            gorsel_uzaklik = math.hypot(rx, ry)
            olcek_orani = gorsel_uzaklik / max(d_min, 0.01)
            anlik_ld = mesafe_ld * olcek_orani
            anlik_km = mesafe_km * olcek_orani

            kare_x.append(rx)
            kare_y.append(ry)
            anlik_ld_listesi.append(anlik_ld)
            anlik_km_listesi.append(anlik_km)

        dinamik_nesneler.append((kare_x, kare_y, anlik_ld_listesi, anlik_km_listesi))

        # Dünya (0, 0) ile Asteroit arasındaki GRİ mesafe ölçüm çizgisi
        fig.add_trace(
            go.Scatter(
                x=[0, kare_x[0]],
                y=[0, kare_y[0]],
                mode="lines",
                line=dict(color="#94A3B8", width=1.8, dash="dash"),
                opacity=0.9,
                hoverinfo="skip",
                name=f"{ad} Mesafe Çizgisi",
            )
        )
        animasyonlu_iz_indeksleri.append(len(fig.data) - 1)

        # Açık gri YUVARLAK asteroit + risk renginde kalın dış çerçeve
        hover_bilgi = (
            f"<b>{ad}</b><br>"
            f"Durum: {seviye}<br>"
            f"Hız: {hiz_kms} km/s<br>"
            f"En Yakın Mesafe: {mesafe_ld} LD ({mesafe_km:,.0f} km)<br>"
            f"Ortalama Çap: {cap_km} km<br>"
            f"Tahmini Kütle: {kutle_ton:,.1f} Ton<br>"
            f"Risk Skoru: {risk}/100<extra></extra>"
        )

        fig.add_trace(
            go.Scatter(
                x=[kare_x[0]],
                y=[kare_y[0]],
                mode="markers+text",
                marker=dict(
                    size=asteroit_boyut,
                    symbol="circle",
                    color="#CBD5E1",
                    line=dict(width=3.5, color=yorunge_renk),
                ),
                text=[ad],
                textposition="top center",
                textfont=dict(size=11),
                hovertemplate=hover_bilgi,
                name=ad,
            )
        )
        animasyonlu_iz_indeksleri.append(len(fig.data) - 1)

    # Başlangıç anındaki (k=0) gri çizgi üzeri mesafe etiketleri
    baslangic_etiketleri = [
        mesafe_etiketi_olustur(kx[0], ky[0], ld_list[0])
        for kx, ky, ld_list, _ in dinamik_nesneler
    ]

    # Animasyon kareleri (Hem çizgi, hem asteroit, hem de gri çizgi üzerindeki etiket kutusu güncellenir)
    kareler = []
    for k in range(kare_sayisi):
        kare_izleri = []
        kare_etiketleri = []
        for kx, ky, ld_list, _ in dinamik_nesneler:
            kare_izleri.append(go.Scatter(x=[0, kx[k]], y=[0, ky[k]], mode="lines"))
            kare_izleri.append(go.Scatter(x=[kx[k]], y=[ky[k]], mode="markers+text"))
            kare_etiketleri.append(mesafe_etiketi_olustur(kx[k], ky[k], ld_list[k]))

        kareler.append(
            go.Frame(
                data=kare_izleri,
                traces=animasyonlu_iz_indeksleri,
                layout=dict(annotations=kare_etiketleri),
                name=f"adim_{k}",
            )
        )
    fig.frames = kareler

    fig.update_layout(
        title="🌍 Dünya Merkezli Asteroit Yakın Geçiş Haritası",
        showlegend=False,
        dragmode="pan",
        annotations=baslangic_etiketleri,
        xaxis=dict(
            range=[-max_eksen * 1.25, max_eksen * 1.25],
            title="Uzaklık Ekseni X (Ölçekli Ay Mesafesi - LD)",
            zeroline=True,
            zerolinecolor="rgba(148, 163, 184, 0.25)",
            fixedrange=False,
        ),
        yaxis=dict(
            range=[-max_eksen, max_eksen],
            title="Uzaklık Ekseni Y (Ölçekli Ay Mesafesi - LD)",
            zeroline=True,
            zerolinecolor="rgba(148, 163, 184, 0.25)",
            fixedrange=False,
        ),
        height=640,
        margin=dict(l=30, r=20, t=70, b=40),
        updatemenus=[
            dict(
                type="buttons",
                showactive=True,
                x=0.01,
                y=1.08,
                xanchor="left",
                direction="left",
                buttons=[
                    dict(
                        label="⏯ Oynat / Duraklat",
                        method="animate",
                        args=[
                            None,
                            dict(
                                frame=dict(duration=50, redraw=True),
                                fromcurrent=True,
                                mode="immediate",
                            ),
                        ],
                        args2=[
                            [None],
                            dict(
                                frame=dict(duration=0, redraw=False),
                                mode="immediate",
                            ),
                        ],
                    ),
                ],
            )
        ],
        sliders=[
            dict(
                active=0,
                yanchor="top",
                xanchor="left",
                currentvalue=dict(prefix="Zaman Adımı: ", visible=True),
                pad=dict(b=10, t=25),
                len=0.98,
                x=0.01,
                steps=[
                    dict(
                        method="animate",
                        args=[
                            [f"adim_{k}"],
                            dict(mode="immediate", frame=dict(duration=0, redraw=True)),
                        ],
                        label=f"{k + 1}",
                    )
                    for k in range(kare_sayisi)
                ],
            )
        ],
    )
    return fig


st.title("🛰️ OrbitalGuard: NEO Risk Simulator")

if "nasa_uyari_gecmisi" not in st.session_state:
    st.session_state["nasa_uyari_gecmisi"] = {}
if "yuksek_risk_test_aktif" not in st.session_state:
    st.session_state["yuksek_risk_test_aktif"] = False

# Sol Yan Menü (Sidebar)
st.sidebar.header("Gözlem Parametreleri")
secilen_tarih = st.sidebar.date_input(
    "Analiz Tarihi Seçin:",
    value=datetime.date(2026, 11, 14)
)
tarih_str = secilen_tarih.strftime("%Y-%m-%d")

risk_esigi = st.sidebar.slider(
    "Minimum Risk Skoru Eşiği:",
    min_value=0,
    max_value=100,
    value=0,
    step=5,
    help="Seçilen değer ve üzerindeki risk skoruna sahip asteroitleri filtreler."
)


@st.cache_data(ttl=600)
def veriyi_getir(tarih):
    return get_neo_data(tarih, tarih, api_key="nfKCCpwTCJpNDMtfTKm9MF8Ct768M9Hg7RL69NgJ")


with st.spinner("NASA sunucusundan asteroit verileri çekiliyor..."):
    df, hata = veriyi_getir(tarih_str)

if hata:
    st.error(hata)
elif df is not None and not df.empty:
    scored_df = calculate_risk_score(df)

    # Test modu açıksa gerçek düşük riskli asteroitlere dokunmadan 86.4 skorlu simülasyon cismi ekle
    test_aktif = st.session_state["yuksek_risk_test_aktif"]
    if test_aktif:
        test_satiri = pd.DataFrame([{
            "ID": "SIM-70PLUS",
            "Asteroit Adı": "[TEST] 2026-PDCO-SIM",
            "Yaklaşma Tarihi": tarih_str,
            "Ortalama Çap (km)": 0.45,
            "Tahmini Kütle (Ton)": 124040.5,
            "Hız (km/s)": 26.4,
            "En Yakın Mesafe (LD)": 0.18,
            "En Yakın Mesafe (km)": 69192.0,
            "Potansiyel Tehlikeli": True,
            "Risk Skoru (0-100)": 86.4,
            "Tehlike Seviyesi": "Yüksek Risk",
        }])
        scored_df = (
            pd.concat([test_satiri, scored_df], ignore_index=True)
            .sort_values(by="Risk Skoru (0-100)", ascending=False)
            .reset_index(drop=True)
        )

    filtered_df = scored_df[scored_df["Risk Skoru (0-100)"] >= risk_esigi].reset_index(drop=True)

    # Üst özet metrikleri
    col1, col2, col3 = st.columns(3)
    col1.metric("Filtrelenen / Toplam Asteroit", f"{len(filtered_df)} / {len(scored_df)}")

    # Yüksek Risk Sınırı (Risk Skoru >= 70) Otomatik NASA Uyarı Sistemi
    yuksek_riskliler = scored_df[scored_df["Risk Skoru (0-100)"] >= 70].reset_index(drop=True)
    if not yuksek_riskliler.empty:
        kayit_anahtari = f"{tarih_str}_{test_aktif}"
        if kayit_anahtari not in st.session_state["nasa_uyari_gecmisi"]:
            uyari_paketi = nasa_uyari_paketi_olustur(yuksek_riskliler, tarih_str, test_modu=test_aktif)
            st.session_state["nasa_uyari_gecmisi"][kayit_anahtari] = uyari_paketi
            st.toast(
                f"🚨 KRİTİK UYARI: Risk skoru ≥ 70 olan {len(yuksek_riskliler)} asteroit için NASA PDCO'ya uyarı gönderildi!",
                icon="🚨",
            )

        aktif_paket = st.session_state["nasa_uyari_gecmisi"][kayit_anahtari]
        hedef_ozetleri = ", ".join(
            f"{r['Asteroit Adı']} (Skor: {r['Risk Skoru (0-100)']})"
            for _, r in yuksek_riskliler.iterrows()
        )

        st.error(
            f"🚨 **NASA OTOMATİK ERKEN UYARI TETİKLENDİ (Eşik: Risk Skoru ≥ 70)**\n\n"
            f"* **70 Sınırını Aşan Yüksek Riskli Cisim:** {hedef_ozetleri}\n"
            f"* **Alıcı Birim:** NASA Planetary Defense Coordination Office (PDCO)\n"
            f"* **İletim Durumu:** ✅ Otomatik uyarı paketi gönderildi (`{aktif_paket['alert_id']}` — {aktif_paket['transmitted_at']})"
        )

        buton_col1, buton_col2 = st.columns([3.0, 1.2])
        with buton_col1:
            with st.expander("📡 NASA PDCO'ya İletilen Telemetri Uyarı Paketini Görüntüle", expanded=False):
                st.json(aktif_paket)
        with buton_col2:
            if test_aktif:
                if st.button("🛑 Test Senaryosunu Kapat", use_container_width=True, key="close_test_mode"):
                    st.session_state["yuksek_risk_test_aktif"] = False
                    st.rerun()
    else:
        uyari_col1, uyari_col2 = st.columns([3.0, 1.2])
        with uyari_col1:
            st.success(
                "🛡️ **NASA Otomatik Uyarı Sistemi Aktif (Eşik: Risk Skoru ≥ 70):** "
                "Seçilen tarihte 70 sınırını aşan asteroit bulunmuyor; düşük/orta riskli cisimlere uyarı gönderilmez."
            )
        with uyari_col2:
            if st.button("🧪 Yüksek Risk Senaryosu Test Et", use_container_width=True, key=f"test_alert_{tarih_str}"):
                st.session_state["yuksek_risk_test_aktif"] = True
                st.rerun()

    if not filtered_df.empty:
        col2.metric("En Yüksek Risk Skoru", f"{filtered_df['Risk Skoru (0-100)'].max()} / 100")
        col3.metric("Potansiyel Tehlikeli Sayısı", int(filtered_df["Potansiyel Tehlikeli"].sum()))

        # Asteroit veri tablosu
        st.subheader(f"{tarih_str} Tarihli Asteroit Verileri (Risk Skoru ≥ {risk_esigi})")
        st.caption(
            "💡 Tablodaki **Ortalama Çap** ve **Tahmini Kütle** çubukları asteroitlerin gerçek fiziksel büyüklüğüne göre ölçeklendirilmiştir. "
            "Satır kutucuklarını işaretleyerek haritada oynatabilirsiniz."
        )

        max_cap = max(float(filtered_df["Ortalama Çap (km)"].max()), 0.001)
        max_kutle = max(float(filtered_df["Tahmini Kütle (Ton)"].max()), 1.0)
        renkli_tablo = filtered_df.style.map(tablo_risk_stili, subset=["Tehlike Seviyesi"])

        tablo_secimi = st.dataframe(
            renkli_tablo,
            use_container_width=True,
            on_select="rerun",
            selection_mode="multi-row",
            column_config={
                "Ortalama Çap (km)": st.column_config.ProgressColumn(
                    "Ortalama Çap (km)",
                    help="Gerçek ortalama çapa göre ölçeklendirilmiş büyüklük çubuğu",
                    format="%.4f km",
                    min_value=0,
                    max_value=max_cap,
                ),
                "Tahmini Kütle (Ton)": st.column_config.ProgressColumn(
                    "Tahmini Kütle (Ton)",
                    help="2.6 g/cm³ ortalama yoğunluk ile hesaplanan ve gerçek kütleye göre ölçeklenen değer",
                    format="%.1f ton",
                    min_value=0,
                    max_value=max_kutle,
                ),
                "En Yakın Mesafe (LD)": st.column_config.NumberColumn(
                    "En Yakın Mesafe (LD)",
                    help="Asteroitin Dünya'ya en çok yaklaştığı andaki Ay Mesafesi (1 LD ≈ 384.400 km)",
                    format="%.2f LD",
                ),
                "En Yakın Mesafe (km)": st.column_config.NumberColumn(
                    "En Yakın Mesafe (km)",
                    help="Asteroitin Dünya'ya en yakın geçiş mesafesi (kilometre)",
                    format="%.0f km",
                ),
                "Risk Skoru (0-100)": st.column_config.ProgressColumn(
                    "Risk Skoru (0-100)",
                    format="%.2f / 100",
                    min_value=0,
                    max_value=100,
                ),
            },
        )
        secilen_satirlar = tablo_secimi.selection.rows

        # Sol tarafta harita simülasyonu, sağ tarafta Harita Lejantı
        if secilen_satirlar:
            secili_asteroitler_df = filtered_df.iloc[secilen_satirlar].reset_index(drop=True)
            secim_anahtari = "_".join(map(str, secilen_satirlar))

            sim_col, rehber_col = st.columns([2.7, 1.3], gap="medium")
            with sim_col:
                sim_fig = dunya_yorunge_simulasyonu(secili_asteroitler_df)
                st.plotly_chart(
                    sim_fig,
                    use_container_width=True,
                    config={"scrollZoom": True, "displayModeBar": True},
                    key=f"dunya_sim_{tarih_str}_{secim_anahtari}",
                )

            with rehber_col:
                st.markdown("#### 🧭 Harita Lejantı")
                st.markdown(
                    """
                    <table style="width:100%; border-collapse:collapse; font-size:14px;">
                      <thead>
                        <tr style="border-bottom:1px solid rgba(148,163,184,0.35); text-align:left;">
                          <th style="padding:8px 6px; width:72px;">Örnek</th>
                          <th style="padding:8px 6px;">Haritadaki Anlamı</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr style="border-bottom:1px solid rgba(148,163,184,0.2);">
                          <td style="padding:10px 6px; text-align:center;">
                            <span style="display:inline-block; width:18px; height:18px; border-radius:50%; background:#2563EB; border:2px solid #1D4ED8;"></span>
                          </td>
                          <td style="padding:10px 6px;"><b>Dünya</b><br><span style="font-size:12px; opacity:0.8;">Merkez referans noktası</span></td>
                        </tr>
                        <tr style="border-bottom:1px solid rgba(148,163,184,0.2);">
                          <td style="padding:10px 6px; text-align:center;">
                            <span style="display:inline-block; width:16px; height:16px; border-radius:50%; background:#CBD5E1; border:2px solid #64748B;"></span>
                          </td>
                          <td style="padding:10px 6px;"><b>Asteroit</b><br><span style="font-size:12px; opacity:0.8;">Büyüklüğü gerçek çapıyla orantılıdır</span></td>
                        </tr>
                        <tr style="border-bottom:1px solid rgba(148,163,184,0.2);">
                          <td style="padding:10px 6px; text-align:center;">
                            <span style="display:inline-block; width:44px; border-bottom:2.5px dashed #94A3B8; vertical-align:middle;"></span>
                          </td>
                          <td style="padding:10px 6px;"><b>Anlık Mesafe Çizgisi</b><br><span style="font-size:12px; opacity:0.8;">Dünya ile asteroit arası uzaklığı (LD) gösterir</span></td>
                        </tr>
                        <tr style="border-bottom:1px solid rgba(148,163,184,0.2);">
                          <td style="padding:10px 6px; text-align:center;">
                            <span style="display:inline-block; width:44px; border-bottom:2.5px dashed #EAB308; vertical-align:middle;"></span>
                          </td>
                          <td style="padding:10px 6px;"><b>Ay Yörüngesi (1 LD)</b><br><span style="font-size:12px; opacity:0.8;">384.400 km mesafe referansı</span></td>
                        </tr>
                        <tr style="border-bottom:1px solid rgba(148,163,184,0.2);">
                          <td style="padding:10px 6px; text-align:center;">
                            <span style="display:inline-block; width:44px; border-bottom:2.5px dotted #EF4444; vertical-align:middle;"></span>
                          </td>
                          <td style="padding:10px 6px;"><b>Yüksek Risk Yörüngesi</b><br><span style="font-size:12px; opacity:0.8;">Risk skoru 70 ve üzeri (NASA Uyarılı)</span></td>
                        </tr>
                        <tr style="border-bottom:1px solid rgba(148,163,184,0.2);">
                          <td style="padding:10px 6px; text-align:center;">
                            <span style="display:inline-block; width:44px; border-bottom:2.5px dotted #F59E0B; vertical-align:middle;"></span>
                          </td>
                          <td style="padding:10px 6px;"><b>Orta Risk Yörüngesi</b><br><span style="font-size:12px; opacity:0.8;">Risk skoru 35 – 69 arası rota</span></td>
                        </tr>
                        <tr>
                          <td style="padding:10px 6px; text-align:center;">
                            <span style="display:inline-block; width:44px; border-bottom:2.5px dotted #3B82F6; vertical-align:middle;"></span>
                          </td>
                          <td style="padding:10px 6px;"><b>Düşük Risk Yörüngesi</b><br><span style="font-size:12px; opacity:0.8;">Risk skoru 35 altı güvenli rota</span></td>
                        </tr>
                      </tbody>
                    </table>
                    """,
                    unsafe_allow_html=True,
                )
                st.caption("💡 Haritayı fareyle tutup sürükleyebilir (Pan) ve tekerlekle yakınlaştırabilirsiniz.")

            st.markdown("#### 📋 Seçili Asteroitlerin Anlık Durum Özeti")
            kart_sutunlari = st.columns(min(len(secili_asteroitler_df), 3))
            for idx, row in secili_asteroitler_df.iterrows():
                with kart_sutunlari[idx % 3]:
                    skor_degeri = float(row["Risk Skoru (0-100)"])
                    kart_metni = (
                        f"**{row['Asteroit Adı']}** — {row['Tehlike Seviyesi']} ({row['Risk Skoru (0-100)']}/100)\n\n"
                        f"* **Tahmini Kütle:** {row['Tahmini Kütle (Ton)']:,.1f} Ton\n"
                        f"* **Ortalama Çap:** {row['Ortalama Çap (km)']} km\n"
                        f"* **Hız:** {row['Hız (km/s)']} km/s\n"
                        f"* **En Yakın Mesafe:** {row['En Yakın Mesafe (LD)']} LD ({row['En Yakın Mesafe (km)']:,.0f} km)"
                    )
                    if skor_degeri >= 70:
                        st.error(f"🔴 {kart_metni}")
                    elif skor_degeri >= 35:
                        st.warning(f"🟠 {kart_metni}")
                    else:
                        st.info(f"🔵 {kart_metni}")

        # Hız ve Mesafe Dağılım Grafiği
        st.subheader("Asteroitin Hızı ve Dünya'ya Mesafesi Grafiği")

        fig = px.scatter(
            filtered_df,
            x="En Yakın Mesafe (LD)",
            y="Hız (km/s)",
            color="Tehlike Seviyesi",
            category_orders={"Tehlike Seviyesi": ["Yüksek Risk", "Orta Risk", "Düşük Risk"]},
            color_discrete_map={
                "Yüksek Risk": "#EF4444",
                "Orta Risk": "#F59E0B",
                "Düşük Risk": "#3B82F6"
            },
            hover_name="Asteroit Adı",
            hover_data={
                "Tehlike Seviyesi": True,
                "Ortalama Çap (km)": True,
                "Tahmini Kütle (Ton)": True,
                "Risk Skoru (0-100)": True,
                "En Yakın Mesafe (km)": True
            },
            labels={
                "En Yakın Mesafe (LD)": "En Yakın Mesafe (Ay Mesafesi - LD)",
                "Hız (km/s)": "Bağıl Hız (km/s)"
            }
        )

        fig.update_layout(dragmode="pan")
        fig.update_traces(marker=dict(size=13, line=dict(width=1, color="white")))
        st.plotly_chart(
            fig,
            use_container_width=True,
            config={"scrollZoom": True, "displayModeBar": True},
        )

        # Grafik Kullanım Kılavuzu
        with st.expander("📖 Grafik Kullanım Kılavuzu", expanded=True):
            k1, k2 = st.columns(2)
            with k1:
                st.markdown("""
                * **Detay İnceleme:** Noktaların üzerine fareyle gelerek asteroitin adını, kütlesini, çapını, hızını ve risk skorunu görüntüleyin.
                * **Yakınlaştırma (Zoom):** İncelemek istediğiniz bölgeyi fareyle dikdörtgen içine alarak yakınlaştırın veya fare tekerleğini kullanın.
                * **Görünümü Sıfırlama:** Yakınlaştırma sonrası grafiğin boş bir yerine **çift tıklayarak** ilk görünüme dönün.
                """)
            with k2:
                st.markdown("""
                * **Risk Grubu Filtreleme:** Sağ üstteki **Yüksek Risk** (kırmızı), **Orta Risk** (turuncu) veya **Düşük Risk** (mavi) etiketlerine tıklayarak ilgili grubu gizleyip açın.
                * **Kaydırma (Pan):** Grafik üzerinde doğrudan fareyle tutup sürükleyerek (veya sağ üst el aracını seçerek) grafiği her yöne kaydırın.
                * **Görsel İndirme:** Grafiğin sağ üst köşesindeki **kamera simgesine** tıklayarak analizi PNG olarak indirin.
                """)
    else:
        col2.metric("En Yüksek Risk Skoru", "-")
        col3.metric("Potansiyel Tehlikeli Sayısı", 0)
        st.info(f"Seçilen tarihte risk skoru {risk_esigi} ve üzerinde olan asteroit bulunamadı. Sol menüden eşik değerini düşürebilirsin.")
else:
    st.warning("Bu tarih için kayıtlı asteroit verisi bulunamadı.")