import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Dashboard Wisata Bali", layout="wide")

st.title("🌴 Dashboard Tempat Wisata Bali")

# LOAD DATA
df = pd.read_excel("data_bersih_bali.xlsx")

# SIDEBAR FILTER
st.sidebar.header("Filter Data")

kecamatan = st.sidebar.multiselect(
    "Pilih Kecamatan",
    df["kecamatan"].dropna().unique(),
    default=df["kecamatan"].dropna().unique()
)

rating_min = st.sidebar.slider(
    "Minimal Rating",
    float(df["rating"].min()),
    float(df["rating"].max()),
    float(df["rating"].min())
)

df_filtered = df[
    (df["kecamatan"].isin(kecamatan)) &
    (df["rating"] >= rating_min)
]

# KPI
col1, col2, col3 = st.columns(3)

col1.metric("Total Wisata", len(df_filtered))
col2.metric("Rata-rata Rating", round(df_filtered["rating"].mean(), 2))
col3.metric("Jumlah Kecamatan", df_filtered["kecamatan"].nunique())

# GRAFIK 1
st.subheader("📊 Jumlah Wisata per Kecamatan")

fig1 = px.bar(
    df_filtered.groupby("kecamatan")["nama"].count().reset_index(),
    x="kecamatan",
    y="nama",
    labels={"nama": "Jumlah Wisata"}
)

st.plotly_chart(fig1, use_container_width=True)

# GRAFIK 2
st.subheader("⭐ Distribusi Rating")
fig2 = px.histogram(df_filtered, x="rating", nbins=10)
st.plotly_chart(fig2, use_container_width=True)

# MAP (kalau ada koordinat)
if "latitude" in df.columns and "longitude" in df.columns:
    st.subheader("🗺️ Peta Wisata")

    fig3 = px.scatter_mapbox(
        df_filtered,
        lat="latitude",
        lon="longitude",
        hover_name="nama",
        zoom=10,
        height=500
    )

    fig3.update_layout(mapbox_style="open-street-map")
    st.plotly_chart(fig3, use_container_width=True)

# TABLE
st.subheader("📄 Data")
st.dataframe(df_filtered)