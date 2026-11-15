import datetime
import html
import math
import os
import random

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from api import get_neo_data, calculate_risk_score, nasa_uyari_paketi_olustur

st.set_page_config(page_title="OrbitalGuard: NEO Risk Simulator", page_icon="🛰️", layout="wide")

# ───────────────────────── Palet ─────────────────────────
UZAY, PANEL, CIZGI = "#05080F", "#0B1220", "#1C2A44"
MAVI, KIRMIZI, KEHRIBAR = "#2F7BFF", "#FC3D21", "#F5A623"
METIN, SOLUK = "#E6ECF5", "#8A9AB5"

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&family=Inter:wght@400;500;600&display=swap');
html, body, [class*="css"], .stApp {{ font-family:'Inter',sans-serif; color:{METIN}; }}
h1,h2,h3,h4,[data-testid="stMetricValue"] {{ font-family:'Space Grotesk',sans-serif !important; letter-spacing:-.01em; }}

.stApp {{ background: radial-gradient(ellipse at 20% -10%, #0F1D3A 0%, {UZAY} 55%) fixed; }}
.stApp::before {{
  content:""; position:fixed; inset:0; pointer-events:none; z-index:0; opacity:.55;
  background-image:
    radial-gradient(1px 1px at 20px 30px,#fff,transparent),
    radial-gradient(1px 1px at 90px 120px,#9DB8FF,transparent),
    radial-gradient(1.5px 1.5px at 160px 60px,#fff,transparent),
    radial-gradient(1px 1px at 230px 180px,#C7D7FF,transparent);
  background-size:200px 200px,260px 260px,340px 340px,410px 410px;
  animation: akis 300s linear infinite, parilti 6s ease-in-out infinite alternate;
}}
@keyframes akis {{ to {{ background-position:1200px 800px,-1040px 780px,1360px -680px,-820px -820px; }} }}
@keyframes parilti {{ from {{ opacity:.35; }} to {{ opacity:.7; }} }}
[data-testid="stHeader"] {{ background:transparent; }}
.block-container {{ padding-top:2rem; max-width:1400px; position:relative; z-index:1; }}

[data-testid="stSidebar"] {{ background:linear-gradient(180deg,#08101F,{UZAY}); border-right:1px solid {CIZGI}; }}
[data-testid="stSidebar"] h2 {{ font-size:1.05rem; color:{SOLUK}; font-weight:500; }}

[data-testid="stMetric"] {{
  background:linear-gradient(160deg,{PANEL},#0A1020); border:1px solid {CIZGI};
  border-radius:10px; padding:16px 18px; transition:border-color .25s, box-shadow .25s;
}}
[data-testid="stMetric"]:hover {{ border-color:{MAVI}; box-shadow:0 0 24px rgba(47,123,255,.18); }}
[data-testid="stMetricLabel"] {{ color:{SOLUK}; }}
[data-testid="stMetricValue"] {{ font-size:1.9rem; font-weight:700; }}

[data-testid="stDataFrame"] {{ border:1px solid {CIZGI}; border-radius:10px; overflow:hidden; }}
[data-testid="stExpander"] {{ background:{PANEL}; border:1px solid {CIZGI}; border-radius:10px; }}
.stButton > button {{ background:transparent; color:{METIN}; border:1px solid {MAVI}; border-radius:8px; transition:background .2s, box-shadow .2s; }}
.stButton > button:hover {{ background:rgba(47,123,255,.14); box-shadow:0 0 18px rgba(47,123,255,.35); color:#fff; border-color:{MAVI}; }}
.stButton > button:focus-visible {{ outline:2px solid {MAVI}; outline-offset:2px; }}

/* Plotly Oynat/Duraklat (updatemenu) butonunun tıklandığında beyaza dönmesini engelle */
.js-plotly-plot .updatemenu-button rect {{
  fill: {PANEL} !important;
  stroke: {MAVI} !important;
  stroke-width: 1.2px !important;
}}
.js-plotly-plot .updatemenu-button:hover rect {{
  fill: #152544 !important;
  stroke: #60A5FA !important;
}}
.js-plotly-plot .updatemenu-button text {{
  fill: {METIN} !important;
}}

.hero {{ display:flex; align-items:center; gap:28px; padding:8px 0 22px; border-bottom:1px solid {CIZGI}; margin-bottom:22px; }}
.h-yor {{ position:relative; width:96px; height:96px; flex:none; }}
.h-dunya {{ position:absolute; inset:31px; border-radius:50%;
  background:radial-gradient(circle at 35% 30%,#6AA7FF,#1D4ED8 55%,#0B2A6B); box-shadow:0 0 22px rgba(47,123,255,.65); }}
.h-halka {{ position:absolute; inset:0; border-radius:50%; border:1px dashed rgba(138,154,181,.55); animation:don 18s linear infinite; }}
.h-halka::after {{ content:""; position:absolute; top:-5px; left:calc(50% - 5px); width:10px; height:10px; border-radius:50%;
  background:#CBD5E1; box-shadow:0 0 10px {KIRMIZI}; }}
@keyframes don {{ to {{ transform:rotate(360deg); }} }}
.hero h1 {{ margin:0; font-size:2.3rem; font-weight:700; line-height:1.1; }}
.hero p {{ margin:6px 0 0; color:{SOLUK}; font-size:.98rem; }}
.h-durum {{ margin-left:auto; text-align:right; color:{SOLUK}; font-size:.85rem; }}
.h-durum b {{ display:block; color:{METIN}; font-family:'Space Grotesk',sans-serif; font-size:1.15rem; }}
.canli {{ display:inline-block; width:8px; height:8px; border-radius:50%; background:#22C55E; margin-right:6px; animation:nabiz 2s ease-in-out infinite; }}
@keyframes nabiz {{ 50% {{ opacity:.3; transform:scale(.7); }} }}

.kritik {{ border:1px solid {KIRMIZI}; border-left-width:5px; border-radius:10px; padding:16px 20px; margin:14px 0;
  background:linear-gradient(90deg,rgba(252,61,33,.14),rgba(252,61,33,.03)); animation:kritik 2.4s ease-in-out infinite; }}
.kritik h4 {{ margin:0 0 8px; color:#FF7A66; font-size:1.05rem; }}
.kritik ul {{ margin:0; padding-left:18px; line-height:1.7; }}
@keyframes kritik {{ 50% {{ box-shadow:0 0 26px rgba(252,61,33,.35); }} }}
.guvenli {{ border:1px solid {CIZGI}; border-left:5px solid #22C55E; border-radius:10px; padding:14px 20px; margin:14px 0; background:rgba(34,197,94,.06); }}

.kart {{ --r:{MAVI}; background:linear-gradient(160deg,{PANEL},#0A1020); border:1px solid {CIZGI}; border-top:3px solid var(--r);
  border-radius:10px; padding:16px 18px; margin-bottom:14px; transition:transform .25s, box-shadow .25s; }}
.kart:hover {{ transform:translateY(-3px); box-shadow:0 8px 28px color-mix(in srgb,var(--r) 28%,transparent); }}
.kart .ad {{ font-family:'Space Grotesk',sans-serif; font-weight:700; font-size:1.02rem; }}
.kart .sv {{ color:var(--r); font-size:.85rem; font-weight:600; }}
.kart .cb {{ height:6px; background:#121C30; border-radius:3px; margin:10px 0 12px; overflow:hidden; }}
.kart .cb i {{ display:block; height:100%; background:var(--r); border-radius:3px; animation:dol 1.1s cubic-bezier(.2,.8,.2,1) both; }}
@keyframes dol {{ from {{ width:0; }} }}
.kart dl {{ margin:0; display:grid; grid-template-columns:auto 1fr; gap:4px 14px; font-size:.88rem; }}
.kart dt {{ color:{SOLUK}; }} .kart dd {{ margin:0; text-align:right; }}

.lejant {{ width:100%; border-collapse:collapse; font-size:14px; }}
.lejant td {{ padding:9px 6px; border-bottom:1px solid {CIZGI}; vertical-align:middle; }}
.lejant small {{ color:{SOLUK}; }}

@media (prefers-reduced-motion: reduce) {{
  .stApp::before,.h-halka,.canli,.kritik,.kart .cb i {{ animation:none !important; }}
}}
@media (max-width:720px) {{ .hero {{ flex-wrap:wrap; }} .h-durum {{ margin-left:0; text-align:left; }} }}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# ───────────────────────── Yardımcılar ─────────────────────────
def fallback_asteroit_verisi_olustur(tarih):
    """NASA API HTTP 429 hız sınırına takıldığında yedek telemetri veri seti sağlar."""
    ornekler = [
        ("3542108", "(2026 KV4)", 0.312, 41250.4, 21.85, 1.42, 545848.0, True),
        ("2099942", "99942 Apophis-Ref", 0.370, 68910.2, 18.40, 2.85, 1095540.0, True),
        ("3841920", "(2024 BX1)", 0.085, 835.6, 14.12, 4.60, 1768240.0, False),
        ("5401681", "(2020 QG)", 0.042, 100.8, 12.33, 6.15, 2364060.0, False),
        ("3729411", "(2015 TB145)", 0.625, 332180.0, 29.50, 8.90, 3421160.0, True),
        ("5442109", "(2026 AB2)", 0.140, 3732.1, 16.05, 11.40, 4382160.0, False),
    ]
    return pd.DataFrame([
        {
            "ID": neo_id,
            "Asteroit Adı": ad,
            "Yaklaşma Tarihi": tarih,
            "Ortalama Çap (km)": cap,
            "Tahmini Kütle (Ton)": kutle,
            "Hız (km/s)": hiz,
            "En Yakın Mesafe (LD)": ld,
            "En Yakın Mesafe (km)": km,
            "Potansiyel Tehlikeli": pha,
        }
        for neo_id, ad, cap, kutle, hiz, ld, km, pha in ornekler
    ])


def risk_rengi_getir(skor, seviye=""):
    """Risk skoruna ve seviyesine göre standart renk kodunu döndürür."""
    if float(skor) >= 70 or seviye == "Yüksek Risk":
        return KIRMIZI
    elif float(skor) >= 35 or seviye == "Orta Risk":
        return KEHRIBAR
    return MAVI


def tablo_risk_stili(deger):
    """Tehlike Seviyesi sütununu risk rengine göre boyar."""
    return f"color: {risk_rengi_getir(0, deger)}; font-weight: 700;"


def mesafe_etiketi_olustur(x_pos, y_pos, ld_degeri):
    """Gri çizginin ortasında duran mesafe etiketi."""
    return dict(
        x=x_pos * 0.5, y=y_pos * 0.5, text=f"<b>{ld_degeri:.2f} LD</b>", showarrow=False,
        bgcolor="rgba(11,18,32,0.92)", bordercolor=CIZGI, borderwidth=1, borderpad=3,
        font=dict(color=METIN, size=11, family="Inter"),
    )


def plotly_koyu(fig):
    """Plotly figürünü koyu görev kontrol temasına çevirir."""
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#060A14",
        font=dict(color=METIN, family="Inter, sans-serif"),
        title_font=dict(family="Space Grotesk, sans-serif", size=18),
        hoverlabel=dict(bgcolor=PANEL, bordercolor=CIZGI, font_color=METIN),
    )
    fig.update_xaxes(gridcolor="rgba(28,42,68,.6)", zerolinecolor=CIZGI, linecolor=CIZGI)
    fig.update_yaxes(gridcolor="rgba(28,42,68,.6)", zerolinecolor=CIZGI, linecolor=CIZGI)
    return fig


def yildiz_izi(max_eksen):
    """Harita arka planı için sabit yıldız alanı (her çizimde aynı gökyüzü)."""
    rng = random.Random(7)
    r, n = max_eksen * 1.25, 140
    return go.Scatter(
        x=[rng.uniform(-r, r) for _ in range(n)], y=[rng.uniform(-r, r) for _ in range(n)],
        mode="markers", hoverinfo="skip", showlegend=False,
        marker=dict(size=[rng.choice([1, 1, 2, 3]) for _ in range(n)], color="#9DB8FF", opacity=0.45),
    )


def risk_karti_html(row):
    skor = float(row["Risk Skoru (0-100)"])
    renk = risk_rengi_getir(skor)
    return f"""
    <div class="kart" style="--r:{renk}">
      <div class="ad">{html.escape(str(row['Asteroit Adı']))}</div>
      <div class="sv">{html.escape(str(row['Tehlike Seviyesi']))} · {skor:.1f}/100</div>
      <div class="cb"><i style="width:{min(skor, 100):.0f}%"></i></div>
      <dl>
        <dt>Kütle</dt><dd>{row['Tahmini Kütle (Ton)']:,.1f} ton</dd>
        <dt>Çap</dt><dd>{row['Ortalama Çap (km)']} km</dd>
        <dt>Hız</dt><dd>{row['Hız (km/s)']} km/s</dd>
        <dt>En yakın mesafe</dt><dd>{row['En Yakın Mesafe (LD)']} LD ({row['En Yakın Mesafe (km)']:,.0f} km)</dd>
      </dl>
    </div>"""


# ───────────────────────── Yörünge simülasyonu ─────────────────────────
def dunya_yorunge_simulasyonu(secili_df):
    """Ortada Dünya, tam boy yörüngeler, Pan/Zoom destekli harita ve animasyon."""
    fig = go.Figure()

    ham_mesafeler = [max(float(m), 0.12) for m in secili_df["En Yakın Mesafe (LD)"]]
    min_gecisler = [1.45 + math.sqrt(m) * 1.15 for m in ham_mesafeler]
    ay_yorunge_r = 1.45 + math.sqrt(1.0) * 1.15
    dis_radar_r = max(max(min_gecisler), ay_yorunge_r) * 1.35
    max_eksen = dis_radar_r * 1.18

    fig.add_trace(yildiz_izi(max_eksen))

    tam_aci = [2 * math.pi * k / 120 for k in range(121)]
    fig.add_trace(go.Scatter(
        x=[dis_radar_r * math.cos(t) for t in tam_aci], y=[dis_radar_r * math.sin(t) for t in tam_aci],
        mode="lines", line=dict(color="rgba(148,163,184,0.25)", width=1), hoverinfo="skip", showlegend=False,
    ))
    fig.add_trace(go.Scatter(
        x=[ay_yorunge_r * math.cos(t) for t in tam_aci], y=[ay_yorunge_r * math.sin(t) for t in tam_aci],
        mode="lines", line=dict(color="#EAB308", width=1.8, dash="dash"), name="Ay Yörüngesi (1 LD)",
        hovertemplate="<b>Ay Yörüngesi Referansı (1 LD ≈ 384.400 km)</b><extra></extra>",
    ))
    # Dünya: dış parıltı + atmosfer + gövde
    fig.add_trace(go.Scatter(
        x=[0], y=[0], mode="markers", hoverinfo="skip", showlegend=False,
        marker=dict(size=78, color="rgba(47,123,255,0.07)", line=dict(width=0)),
    ))
    fig.add_trace(go.Scatter(
        x=[0], y=[0], mode="markers", hoverinfo="skip", showlegend=False,
        marker=dict(size=52, color="rgba(47,123,255,0.16)", line=dict(width=1.5, color="rgba(47,123,255,0.4)")),
    ))
    fig.add_trace(go.Scatter(
        x=[0], y=[0], mode="markers+text", name="Dünya",
        marker=dict(size=32, color="#2563EB", line=dict(width=2, color="#60A5FA")),
        text=["Dünya"], textposition="bottom center", textfont=dict(size=13, color=METIN),
        hovertemplate="<b>Dünya (Merkez Referans)</b><extra></extra>",
    ))

    en_dusuk_hiz = max(float(secili_df["Hız (km/s)"].min()), 0.5)
    en_yuksek_hiz = max(float(secili_df["Hız (km/s)"].max()), en_dusuk_hiz)
    hiz_fark_orani = min(en_yuksek_hiz / en_dusuk_hiz, 2.2)
    kare_sayisi = min(max(int(48 * hiz_fark_orani), 48), 100)

    dinamik_nesneler, animasyonlu_iz_indeksleri = [], []
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
        asteroit_boyut = min(max(int(15 + cap_km * 14), 15), 26)

        d_min = min_gecisler[i]
        yaklasma_acisi = (i * (2 * math.pi / max(toplam_secili, 3))) + 0.35

        def konum(s):
            u = s * tam_yol_yarim
            v = d_min + 0.12 * (u ** 2) / max(d_min, 0.9)
            return (u * math.cos(yaklasma_acisi) - v * math.sin(yaklasma_acisi),
                    u * math.sin(yaklasma_acisi) + v * math.cos(yaklasma_acisi))

        pts = [konum(-1.0 + (2.0 * k / 80)) for k in range(81)]
        fig.add_trace(go.Scatter(
            x=[p[0] for p in pts], y=[p[1] for p in pts], mode="lines",
            line=dict(color=yorunge_renk, width=2.0, dash="dot"), opacity=0.68,
            name=f"{ad} Yörüngesi", hoverinfo="skip",
        ))

        goreceli_hiz = max(hiz_kms / en_dusuk_hiz, 1.0)
        kare_x, kare_y, ld_list, km_list = [], [], [], []
        for k in range(kare_sayisi):
            ilerleme = k / (kare_sayisi - 1)
            rx, ry = konum(min(-1.0 + (2.0 * ilerleme * goreceli_hiz), 1.0))
            olcek_orani = math.hypot(rx, ry) / max(d_min, 0.01)
            kare_x.append(rx); kare_y.append(ry)
            ld_list.append(mesafe_ld * olcek_orani); km_list.append(mesafe_km * olcek_orani)
        dinamik_nesneler.append((kare_x, kare_y, ld_list, km_list))

        fig.add_trace(go.Scatter(
            x=[0, kare_x[0]], y=[0, kare_y[0]], mode="lines",
            line=dict(color="#94A3B8", width=1.8, dash="dash"), opacity=0.9,
            hoverinfo="skip", name=f"{ad} Mesafe Çizgisi",
        ))
        animasyonlu_iz_indeksleri.append(len(fig.data) - 1)

        hover_bilgi = (
            f"<b>{ad}</b><br>Durum: {seviye}<br>Hız: {hiz_kms} km/s<br>"
            f"En Yakın Mesafe: {mesafe_ld} LD ({mesafe_km:,.0f} km)<br>Ortalama Çap: {cap_km} km<br>"
            f"Tahmini Kütle: {kutle_ton:,.1f} Ton<br>Risk Skoru: {risk}/100<extra></extra>"
        )
        fig.add_trace(go.Scatter(
            x=[kare_x[0]], y=[kare_y[0]], mode="markers+text",
            marker=dict(size=asteroit_boyut, color="#CBD5E1", line=dict(width=3.5, color=yorunge_renk)),
            text=[ad], textposition="top center", textfont=dict(size=11, color=METIN),
            hovertemplate=hover_bilgi, name=ad,
        ))
        animasyonlu_iz_indeksleri.append(len(fig.data) - 1)

    baslangic_etiketleri = [mesafe_etiketi_olustur(kx[0], ky[0], ll[0]) for kx, ky, ll, _ in dinamik_nesneler]

    kareler = []
    for k in range(kare_sayisi):
        kare_izleri, kare_etiketleri = [], []
        for kx, ky, ll, _ in dinamik_nesneler:
            kare_izleri.append(go.Scatter(x=[0, kx[k]], y=[0, ky[k]], mode="lines"))
            kare_izleri.append(go.Scatter(x=[kx[k]], y=[ky[k]], mode="markers+text"))
            kare_etiketleri.append(mesafe_etiketi_olustur(kx[k], ky[k], ll[k]))
        kareler.append(go.Frame(data=kare_izleri, traces=animasyonlu_iz_indeksleri,
                                layout=dict(annotations=kare_etiketleri), name=f"adim_{k}"))
    fig.frames = kareler

    fig.update_layout(
        title="Dünya Merkezli Asteroit Yakın Geçiş Haritası",
        showlegend=False, dragmode="pan", annotations=baslangic_etiketleri,
        xaxis=dict(range=[-max_eksen * 1.25, max_eksen * 1.25], title="X ekseni (ölçekli Ay mesafesi, LD)", fixedrange=False),
        yaxis=dict(range=[-max_eksen, max_eksen], title="Y ekseni (ölçekli Ay mesafesi, LD)", fixedrange=False),
        height=640, margin=dict(l=30, r=20, t=70, b=40),
        updatemenus=[dict(
            type="buttons", showactive=False, active=-1, x=0.01, y=1.08, xanchor="left", direction="left",
            bgcolor=PANEL, bordercolor=MAVI, font=dict(color=METIN),
            buttons=[dict(
                label="⏯ Oynat / Duraklat", method="animate",
                args=[None, dict(frame=dict(duration=50, redraw=True), fromcurrent=True, mode="immediate")],
                args2=[[None], dict(frame=dict(duration=0, redraw=False), mode="immediate")],
            )],
        )],
        sliders=[dict(
            active=0, yanchor="top", xanchor="left", pad=dict(b=10, t=25), len=0.98, x=0.01,
            bgcolor="#121C30", bordercolor=CIZGI, activebgcolor=MAVI, font=dict(color=SOLUK),
            currentvalue=dict(prefix="Zaman adımı: ", visible=True, font=dict(color=METIN)),
            steps=[dict(method="animate",
                        args=[[f"adim_{k}"], dict(mode="immediate", frame=dict(duration=0, redraw=True))],
                        label=f"{k + 1}") for k in range(kare_sayisi)],
        )],
    )
    return plotly_koyu(fig)


# ───────────────────────── Sayfa ─────────────────────────
if "nasa_uyari_gecmisi" not in st.session_state:
    st.session_state["nasa_uyari_gecmisi"] = {}
if "yuksek_risk_test_aktif" not in st.session_state:
    st.session_state["yuksek_risk_test_aktif"] = False

st.sidebar.header("Gözlem Parametreleri")
secilen_tarih = st.sidebar.date_input("Analiz Tarihi Seçin:", value=datetime.date(2026, 11, 14))
tarih_str = secilen_tarih.strftime("%Y-%m-%d")
risk_esigi = st.sidebar.slider(
    "Minimum Risk Skoru Eşiği:", min_value=0, max_value=100, value=0, step=5,
    help="Seçilen değer ve üzerindeki risk skoruna sahip asteroitleri filtreler.",
)

st.markdown(
    f"""
    <div class="hero">
      <div class="h-yor"><div class="h-halka"></div><div class="h-dunya"></div></div>
      <div>
        <h1>OrbitalGuard</h1>
        <p>Dünya'ya yakın cisimlerin (NEO) yaklaşma ve risk takibi</p>
      </div>
      <div class="h-durum"><span class="canli"></span>NASA NeoWs bağlantısı<b>{tarih_str}</b></div>
    </div>
    """,
    unsafe_allow_html=True,
)


def _api_anahtari():
    try:
        return st.secrets["NASA_API_KEY"]
    except Exception:
        return os.environ.get("NASA_API_KEY", "nfKCCpwTCJpNDMtfTKm9MF8Ct768M9Hg7RL69NgJ")


@st.cache_data(ttl=3600, show_spinner=False)
def _basarili_nasa_verisi_cek(tarih, anahtar):
    """Yalnızca hatasız ve dolu NASA yanıtlarını önbellekte tutar."""
    df_sonuc, hata_mesaji = get_neo_data(tarih, tarih, api_key=anahtar)
    if hata_mesaji or df_sonuc is None or df_sonuc.empty:
        raise ValueError(hata_mesaji or "Bos veri")
    return df_sonuc


if st.sidebar.button("🔄 Canlı Veriyi Yenile", use_container_width=True, help="Önbelleği sıfırlar ve NASA sunucusundan güncel veriyi çeker."):
    _basarili_nasa_verisi_cek.clear()
    st.rerun()


def veriyi_getir(tarih):
    anahtar = _api_anahtari()
    try:
        return _basarili_nasa_verisi_cek(tarih, anahtar), None
    except Exception as exc:
        hata_mesaji = str(exc)
        if "429" in hata_mesaji:
            return fallback_asteroit_verisi_olustur(tarih), "RATE_LIMIT_FALLBACK"
        return None, hata_mesaji


with st.spinner("NASA sunucusundan asteroit verileri çekiliyor..."):
    df, hata = veriyi_getir(tarih_str)

if hata == "RATE_LIMIT_FALLBACK":
    st.warning("⚠️ NASA API hız sınırına (HTTP 429) ulaşıldı. Simülasyon yedek telemetri veri setiyle çalıştırılıyor.")
    hata = None

if hata:
    st.error(hata)
elif df is not None and not df.empty:
    scored_df = calculate_risk_score(df)

    test_aktif = st.session_state["yuksek_risk_test_aktif"]
    if test_aktif:
        test_satiri = pd.DataFrame([{
            "ID": "SIM-70PLUS", "Asteroit Adı": "[TEST] 2026-PDCO-SIM", "Yaklaşma Tarihi": tarih_str,
            "Ortalama Çap (km)": 0.45, "Tahmini Kütle (Ton)": 124040.5, "Hız (km/s)": 26.4,
            "En Yakın Mesafe (LD)": 0.18, "En Yakın Mesafe (km)": 69192.0, "Potansiyel Tehlikeli": True,
            "Risk Skoru (0-100)": 86.4, "Tehlike Seviyesi": "Yüksek Risk",
        }])
        scored_df = (pd.concat([test_satiri, scored_df], ignore_index=True)
                     .sort_values(by="Risk Skoru (0-100)", ascending=False).reset_index(drop=True))

    filtered_df = scored_df[scored_df["Risk Skoru (0-100)"] >= risk_esigi].reset_index(drop=True)

    col1, col2, col3 = st.columns(3)
    col1.metric("Filtrelenen / Toplam Asteroit", f"{len(filtered_df)} / {len(scored_df)}")

    yuksek_riskliler = scored_df[scored_df["Risk Skoru (0-100)"] >= 70].reset_index(drop=True)
    if not yuksek_riskliler.empty:
        kayit_anahtari = f"{tarih_str}_{test_aktif}"
        if kayit_anahtari not in st.session_state["nasa_uyari_gecmisi"]:
            st.session_state["nasa_uyari_gecmisi"][kayit_anahtari] = nasa_uyari_paketi_olustur(
                yuksek_riskliler, tarih_str, test_modu=test_aktif)
            st.toast(f"Risk skoru ≥ 70 olan {len(yuksek_riskliler)} asteroit için NASA PDCO'ya uyarı gönderildi.", icon="🚨")

        aktif_paket = st.session_state["nasa_uyari_gecmisi"][kayit_anahtari]
        hedef_ozetleri = ", ".join(
            f"{r['Asteroit Adı']} (Skor: {r['Risk Skoru (0-100)']})" for _, r in yuksek_riskliler.iterrows())

        st.markdown(
            f"""<div class="kritik"><h4>Kritik uyarı: risk skoru 70 ve üzeri</h4><ul>
            <li><b>Cisimler:</b> {html.escape(hedef_ozetleri)}</li>
            <li><b>Alıcı:</b> NASA Planetary Defense Coordination Office (PDCO)</li>
            <li><b>İletim:</b> Uyarı paketi gönderildi ({html.escape(str(aktif_paket['alert_id']))}, {html.escape(str(aktif_paket['transmitted_at']))})</li>
            </ul></div>""",
            unsafe_allow_html=True,
        )
        b1, b2 = st.columns([3.0, 1.2])
        with b1:
            with st.expander("📡 NASA PDCO'ya iletilen telemetri paketini görüntüle", expanded=False):
                st.json(aktif_paket)
        with b2:
            if test_aktif and st.button("🛑 Test senaryosunu kapat", use_container_width=True, key="close_test_mode"):
                st.session_state["yuksek_risk_test_aktif"] = False
                st.rerun()
    else:
        u1, u2 = st.columns([3.0, 1.2])
        with u1:
            st.markdown(
                '<div class="guvenli"><b>Otomatik uyarı sistemi aktif.</b> Seçilen tarihte risk skoru 70\'i aşan '
                "asteroit yok; düşük ve orta riskli cisimler için uyarı gönderilmez.</div>",
                unsafe_allow_html=True,
            )
        with u2:
            if st.button("🧪 Yüksek risk senaryosunu test et", use_container_width=True, key=f"test_alert_{tarih_str}"):
                st.session_state["yuksek_risk_test_aktif"] = True
                st.rerun()

    if not filtered_df.empty:
        col2.metric("En Yüksek Risk Skoru", f"{filtered_df['Risk Skoru (0-100)'].max()} / 100")
        col3.metric("Potansiyel Tehlikeli Sayısı", int(filtered_df["Potansiyel Tehlikeli"].sum()))

        st.subheader(f"{tarih_str} tarihli asteroit verileri (risk skoru ≥ {risk_esigi})")
        st.caption("Çap ve kütle çubukları gerçek fiziksel büyüklüğe göre ölçeklenir. "
                   "Satırları işaretleyerek haritada oynatabilirsiniz.")

        max_cap = max(float(filtered_df["Ortalama Çap (km)"].max()), 0.001)
        max_kutle = max(float(filtered_df["Tahmini Kütle (Ton)"].max()), 1.0)
        renkli_tablo = filtered_df.style.map(tablo_risk_stili, subset=["Tehlike Seviyesi"])

        tablo_secimi = st.dataframe(
            renkli_tablo, use_container_width=True, on_select="rerun", selection_mode="multi-row",
            column_config={
                "Ortalama Çap (km)": st.column_config.ProgressColumn(
                    "Ortalama Çap (km)", help="Gerçek ortalama çapa göre ölçeklenen çubuk",
                    format="%.4f km", min_value=0, max_value=max_cap),
                "Tahmini Kütle (Ton)": st.column_config.ProgressColumn(
                    "Tahmini Kütle (Ton)", help="2.6 g/cm³ ortalama yoğunlukla hesaplanan kütle",
                    format="%.1f ton", min_value=0, max_value=max_kutle),
                "En Yakın Mesafe (LD)": st.column_config.NumberColumn(
                    "En Yakın Mesafe (LD)", help="En yakın geçişteki Ay mesafesi (1 LD ≈ 384.400 km)", format="%.2f LD"),
                "En Yakın Mesafe (km)": st.column_config.NumberColumn(
                    "En Yakın Mesafe (km)", help="En yakın geçiş mesafesi (km)", format="%.0f km"),
                "Risk Skoru (0-100)": st.column_config.ProgressColumn(
                    "Risk Skoru (0-100)", format="%.2f / 100", min_value=0, max_value=100),
            },
        )
        secilen_satirlar = tablo_secimi.selection.rows

        if secilen_satirlar:
            secili_df = filtered_df.iloc[secilen_satirlar].reset_index(drop=True)
            secim_anahtari = "_".join(map(str, secilen_satirlar))

            sim_col, rehber_col = st.columns([2.7, 1.3], gap="medium")
            with sim_col:
                st.plotly_chart(
                    dunya_yorunge_simulasyonu(secili_df), use_container_width=True,
                    config={"scrollZoom": True, "displayModeBar": True},
                    key=f"dunya_sim_{tarih_str}_{secim_anahtari}",
                )
            with rehber_col:
                st.markdown("#### 🧭 Harita lejantı")

                def satir(sembol, baslik, aciklama):
                    return (f'<tr><td style="text-align:center;width:72px">{sembol}</td>'
                            f"<td><b>{baslik}</b><br><small>{aciklama}</small></td></tr>")

                def daire(bg, kenar, px_):
                    return (f'<span style="display:inline-block;width:{px_}px;height:{px_}px;border-radius:50%;'
                            f'background:{bg};border:2px solid {kenar}"></span>')

                def cizgi(renk, stil):
                    return f'<span style="display:inline-block;width:44px;border-bottom:2.5px {stil} {renk}"></span>'

                st.markdown(
                    '<table class="lejant">'
                    + satir(daire("#2563EB", "#60A5FA", 18), "Dünya", "Merkez referans noktası")
                    + satir(daire("#CBD5E1", "#64748B", 16), "Asteroit", "Büyüklüğü gerçek çapıyla orantılıdır")
                    + satir(cizgi("#94A3B8", "dashed"), "Anlık mesafe çizgisi", "Dünya ile asteroit arası uzaklığı (LD) gösterir")
                    + satir(cizgi("#EAB308", "dashed"), "Ay yörüngesi (1 LD)", "384.400 km mesafe referansı")
                    + satir(cizgi(KIRMIZI, "dotted"), "Yüksek risk yörüngesi", "Risk skoru 70 ve üzeri (NASA uyarılı)")
                    + satir(cizgi(KEHRIBAR, "dotted"), "Orta risk yörüngesi", "Risk skoru 35 – 69 arası")
                    + satir(cizgi(MAVI, "dotted"), "Düşük risk yörüngesi", "Risk skoru 35 altı")
                    + "</table>",
                    unsafe_allow_html=True,
                )
                st.caption("Haritayı sürükleyerek kaydırabilir, tekerlekle yakınlaştırabilirsiniz.")

            st.markdown("#### 📋 Seçili asteroitlerin anlık durum özeti")
            kart_sutunlari = st.columns(min(len(secili_df), 3))
            for idx, row in secili_df.iterrows():
                with kart_sutunlari[idx % 3]:
                    st.markdown(risk_karti_html(row), unsafe_allow_html=True)

        st.subheader("Asteroitin hızı ve Dünya'ya mesafesi")
        fig = px.scatter(
            filtered_df, x="En Yakın Mesafe (LD)", y="Hız (km/s)", color="Tehlike Seviyesi",
            category_orders={"Tehlike Seviyesi": ["Yüksek Risk", "Orta Risk", "Düşük Risk"]},
            color_discrete_map={"Yüksek Risk": KIRMIZI, "Orta Risk": KEHRIBAR, "Düşük Risk": MAVI},
            hover_name="Asteroit Adı",
            hover_data={"Tehlike Seviyesi": True, "Ortalama Çap (km)": True, "Tahmini Kütle (Ton)": True,
                        "Risk Skoru (0-100)": True, "En Yakın Mesafe (km)": True},
            labels={"En Yakın Mesafe (LD)": "En yakın mesafe (Ay mesafesi, LD)", "Hız (km/s)": "Bağıl hız (km/s)"},
        )
        fig.update_layout(dragmode="pan")
        fig.update_traces(marker=dict(size=13, line=dict(width=1, color="#05080F")))
        plotly_koyu(fig)
        st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": True, "displayModeBar": True})

        with st.expander("📖 Grafik kullanım kılavuzu", expanded=False):
            k1, k2 = st.columns(2)
            with k1:
                st.markdown("""
- **Detay inceleme:** Noktaların üzerine gelerek adı, kütleyi, çapı, hızı ve risk skorunu görün.
- **Yakınlaştırma:** Bölgeyi dikdörtgen içine alın ya da fare tekerleğini kullanın.
- **Görünümü sıfırlama:** Grafiğin boş bir yerine çift tıklayın.
""")
            with k2:
                st.markdown("""
- **Risk grubu filtreleme:** Sağ üstteki etiketlere tıklayarak ilgili grubu gizleyin ya da açın.
- **Kaydırma:** Grafiği fareyle tutup sürükleyin.
- **Görsel indirme:** Sağ üstteki kamera simgesiyle PNG olarak indirin.
""")
    else:
        col2.metric("En Yüksek Risk Skoru", "-")
        col3.metric("Potansiyel Tehlikeli Sayısı", 0)
        st.info(f"Seçilen tarihte risk skoru {risk_esigi} ve üzerinde olan asteroit yok. Sol menüden eşiği düşürebilirsin.")
else:
    st.warning("Bu tarih için kayıtlı asteroit verisi bulunamadı.")
