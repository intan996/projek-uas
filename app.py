import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Dashboard Wisata Bali", layout="wide")

st.title("🌴 Dashboard Tempat Wisata Bali")

# LOAD DATA
df = pd.read_excel("data_bersih_bali.xlsx")

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

df_filtered = df[
    (df["Lokasi"].isin(lokasi)) &
    (df["Penilaian Google Maps"] >= rating_min)
]

# KPI
col1, col2, col3 = st.columns(3)

col1.metric("Total Wisata", len(df_filtered))
col2.metric("Rata-rata Rating", round(df_filtered["Penilaian Google Maps"].mean(), 2))
col3.metric("Jumlah Lokasi", df_filtered["Lokasi"].nunique())

# GRAFIK 1
st.subheader("📊 Jumlah Wisata per Lokasi")

fig1 = px.bar(
    df_filtered.groupby("Lokasi")["Tempat wisata"].count().reset_index(),
    x="Lokasi",
    y="Tempat wisata",
    labels={"Tempat wisata": "Jumlah Wisata"}
)

st.plotly_chart(fig1, use_container_width=True)

# GRAFIK 2
st.subheader("⭐ Distribusi Rating")
fig2 = px.histogram(df_filtered, x="Penilaian Google Maps", nbins=10)
st.plotly_chart(fig2, use_container_width=True)

# TABLE
st.subheader("📄 Data")
st.dataframe(df_filtered)
