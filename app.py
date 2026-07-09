import streamlit as st
import pandas as pd
import plotly.express as px
import re

def parse_koordinat(s):
    if not isinstance(s, str):
        return None, None
    dec = re.findall(r'(\d+\.?\d*)[°\s]*([NS])[,\s]+(\d+\.?\d*)[°\s]*([EW])', s)
    if dec:
        lat = float(dec[0][0]) * (-1 if dec[0][1] == 'S' else 1)
        lon = float(dec[0][2]) * (-1 if dec[0][3] == 'W' else 1)
        return lat, lon
    dms = re.findall(r'(\d+)[^\d]+(\d+)[^\d]+(\d+\.?\d*)[^\d]*([NS])[,\s]+(\d+)[^\d]+(\d+)[^\d]+(\d+\.?\d*)[^\d]*([EW])', s)
    if dms:
        d = dms[0]
        lat = (float(d[0]) + float(d[1])/60 + float(d[2])/3600) * (-1 if d[3]=='S' else 1)
        lon = (float(d[4]) + float(d[5])/60 + float(d[6])/3600) * (-1 if d[7]=='W' else 1)
        return lat, lon
    dms2 = re.findall(r'(\d+)[^\d]+(\d+)[^\d]*([NS])[,\s]+(\d+)[^\d]+(\d+)[^\d]*([EW])', s)
    if dms2:
        d = dms2[0]
        lat = (float(d[0]) + float(d[1])/60) * (-1 if d[2]=='S' else 1)
        lon = (float(d[3]) + float(d[4])/60) * (-1 if d[5]=='W' else 1)
        return lat, lon
    return None, None

st.set_page_config(page_title="Dashboard Wisata Bali", layout="wide")

st.title("🌴 Dashboard Tempat Wisata Bali")

# LOAD DATA
df = pd.read_excel("data_bersih_bali.xlsx")
df[['lat', 'lon']] = df['Kordinat'].apply(lambda x: pd.Series(parse_koordinat(x)))

# SIDEBAR FILTER
st.sidebar.header("Filter Data")

lokasi = st.sidebar.multiselect(
    "Pilih Lokasi",
    df["Lokasi"].dropna().unique(),
    default=df["Lokasi"].dropna().unique()
)

rating_min = st.sidebar.slider(
    "Minimal Rating",
    float(df["Penilaian Google Maps"].min()),
    float(df["Penilaian Google Maps"].max()),
    float(df["Penilaian Google Maps"].min())
)

harga_max = st.sidebar.slider(
    "Maksimal Harga Tiket (Rp)",
    int(df["Harga Tiket Masuk "].min()),
    int(df["Harga Tiket Masuk "].max()),
    int(df["Harga Tiket Masuk "].max())
)

df_filtered = df[
    (df["Lokasi"].isin(lokasi)) &
    (df["Penilaian Google Maps"] >= rating_min) &
    (df["Harga Tiket Masuk "] <= harga_max)
]

# KPI
col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Wisata", len(df_filtered))
col2.metric("Rata-rata Rating", round(df_filtered["Penilaian Google Maps"].mean(), 2))
col3.metric("Total Ulasan", f"{df_filtered['Jumlah Ulasan Google'].sum():,}")
col4.metric("Rata-rata Harga Tiket", f"Rp {int(df_filtered['Harga Tiket Masuk '].mean()):,}")

st.divider()

# GRAFIK 1 - Jumlah Wisata per Lokasi
st.subheader("📊 Jumlah Wisata per Lokasi")
fig1 = px.bar(
    df_filtered.groupby("Lokasi")["Tempat wisata"].count().reset_index(),
    x="Lokasi",
    y="Tempat wisata",
    labels={"Tempat wisata": "Jumlah Wisata"},
    color="Tempat wisata",
    color_continuous_scale="teal"
)
fig1.update_layout(xaxis_tickangle=-30)
st.plotly_chart(fig1, use_container_width=True)

col_a, col_b = st.columns(2)

# GRAFIK 2 - Distribusi Rating
with col_a:
    st.subheader("⭐ Distribusi Rating")
    fig2 = px.histogram(df_filtered, x="Penilaian Google Maps", nbins=10, color_discrete_sequence=["#f0a500"])
    st.plotly_chart(fig2, use_container_width=True)

# GRAFIK 3 - Top 10 Wisata berdasarkan Ulasan
with col_b:
    st.subheader("🔥 Top 10 Wisata Terpopuler (Ulasan)")
    top10 = df_filtered.nlargest(10, "Jumlah Ulasan Google")[["Tempat wisata", "Jumlah Ulasan Google"]]
    fig3 = px.bar(
        top10,
        x="Jumlah Ulasan Google",
        y="Tempat wisata",
        orientation="h",
        color="Jumlah Ulasan Google",
        color_continuous_scale="blues"
    )
    fig3.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig3, use_container_width=True)

# GRAFIK 4 - Harga Tiket per Tempat Wisata
st.subheader("💰 Harga Tiket Masuk per Tempat Wisata")
fig4 = px.bar(
    df_filtered.sort_values("Harga Tiket Masuk ", ascending=False),
    x="Tempat wisata",
    y="Harga Tiket Masuk ",
    labels={"Harga Tiket Masuk ": "Harga (Rp)"},
    color="Harga Tiket Masuk ",
    color_continuous_scale="reds"
)
fig4.update_layout(xaxis_tickangle=-30)
st.plotly_chart(fig4, use_container_width=True)

# PETA
st.subheader("🗺️ Peta Lokasi Wisata Bali")
df_map = df_filtered.dropna(subset=["lat", "lon"])
fig_map = px.scatter_mapbox(
    df_map,
    lat="lat",
    lon="lon",
    hover_name="Tempat wisata",
    hover_data={"Penilaian Google Maps": True, "Harga Tiket Masuk ": True, "lat": False, "lon": False},
    color="Penilaian Google Maps",
    size="Jumlah Ulasan Google",
    color_continuous_scale="Viridis",
    zoom=9,
    height=500
)
fig_map.update_layout(mapbox_style="open-street-map")
st.plotly_chart(fig_map, use_container_width=True)

# TABLE
st.subheader("📄 Data Lengkap")
st.dataframe(
    df_filtered[["Tempat wisata", "Lokasi", "Penilaian Google Maps", "Jumlah Ulasan Google", "Harga Tiket Masuk ", "Deskripsi"]].reset_index(drop=True),
    use_container_width=True
)
