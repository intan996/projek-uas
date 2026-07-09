import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_folium import st_folium
import folium
import re

# 1. SET KONFIGURASI UTAMA HALAMAN
st.set_page_config(
    page_title="Bali Eco-Tourism Analytics Dashboard", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# 2. INJEKSI CSS UNTUK MENGUNCI TEMA HIJAU ALAM (Sesuai Gambar ke-4)
st.markdown("""
    <style>
        /* Mengunci Background Aplikasi Utama (Gelap Hitam/Hijau Sangat Tua) */
        .stApp {
            background-color: #0f1512 !important;
        }
        
        /* Mengunci Background Sidebar (Hijau Tua) */
        [data-testid="stSidebar"] {
            background-color: #0b1d12 !important;
        }
        
        /* Mengunci Semua Elemen Teks Global Agar Tetap Putih Bersih */
        h1, h2, h3, h4, h5, h6, p, span, label, .stMarkdown, .stCaption {
            color: #ffffff !important;
        }
        
        /* Styling Kartu KPI / Summary Card biar mirip kotak hijau di gambarmu */
        [data-testid="metric-container"] {
            background-color: #143621 !important;
            padding: 15px !important;
            border-radius: 8px !important;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }
        [data-testid="stMetricValue"] div {
            color: #ffffff !important;
            font-weight: 700 !important;
        }
        [data-testid="stMetricLabel"] div {
            color: #b7e4c7 !important;
        }
        
        /* FIX: Memperbaiki Kotak Pencarian Input Text agar tulisan terlihat */
        div[data-baseweb="input"] > div {
            background-color: #1b4332 !important;
            border: 1px solid #52b788 !important;
        }
        input {
            color: #ffffff !important;
            -webkit-text-fill-color: #ffffff !important;
        }
        input::placeholder {
            color: #a3b899 !important;
            -webkit-text-fill-color: #a3b899 !important;
        }
        
        /* Mengamankan Kotak Info Filter di Sidebar */
        .sidebar-card {
            background-color: #143621 !important;
            padding: 15px;
            border-radius: 8px;
            border-left: 5px solid #52b788;
            margin-top: 15px;
        }
        
        /* Custom Subheader UI styling */
        .custom-subheader {
            background-color: #143621;
            padding: 10px 15px;
            border-radius: 6px;
            margin-bottom: 15px;
            border-left: 4px solid #52b788;
        }
        .custom-subheader-text {
            color: #ffffff !important;
            font-weight: 600;
            font-size: 16px;
            margin-left: 8px;
        }

        /* Ngunci tinggi iframe peta Folium agar tidak melar setelah load */
        iframe {
            height: 300px !important;
            max-height: 300px !important;
        }
    </style>
""", unsafe_allow_html=True)

# 3. FUNGSI CACHE LOAD DATA
@st.cache_data
def load_data():
    df = pd.read_excel("data_bersih_bali.xlsx", sheet_name="Bali Popular Destination for To")
    
    df.columns = [str(col).strip().replace('\n', ' ') for col in df.columns]
    
    def cari_kolom(kata_kunci, default_name):
        for col in df.columns:
            if kata_kunci.lower() in col.lower():
                return col
            
        return default_name

    col_tempat = cari_kolom('tempat', 'Tempat wisata')
    col_lokasi = cari_kolom('lokasi', 'Lokasi')
    col_koordinat = cari_kolom('kordinat', 'Kordinat')
    col_rating = cari_kolom('penilaian', 'Penilaian')
    col_ulasan = cari_kolom('ulasan', 'Jumlah Ulasan')
    col_deskripsi = cari_kolom('deskripsi', 'Deskripsi')
    col_harga = cari_kolom('harga', 'Harga Tiket')

    df.attrs['col_tempat'] = col_tempat
    df.attrs['col_lokasi'] = col_lokasi
    df.attrs['col_koordinat'] = col_koordinat
    df.attrs['col_rating'] = col_rating
    df.attrs['col_ulasan'] = col_ulasan
    df.attrs['col_harga'] = col_harga
    df.attrs['col_deskripsi'] = col_deskripsi
    df['Rating_Clean'] = pd.to_numeric(df[col_rating], errors='coerce').fillna(0.0)

    def clean_ulasan_val(val):
        s = str(val).strip().replace(',', '')
        if s.endswith('.0'): s = s[:-2]
        if s in ['-', '', 'nan', 'None']: return 0
        try: return int(float(s))
        except: return 0
    df['Ulasan_Clean'] = df[col_ulasan].apply(clean_ulasan_val)
    
    def clean_harga_val(val):
        s = str(val).strip().replace('Rp', '').replace(' ', '').replace(',', '')
        if s.endswith('.0'): s = s[:-2]
        if s in ['-', '', 'nan', 'None']: return 0
        try: return int(float(s))
        except: return 0
    df['Harga_Clean'] = df[col_harga].apply(clean_harga_val)

    def get_kabupaten(lokasi_str):
        for kab in ["Gianyar", "Badung", "Karangasem", "Tabanan", "Bangli", "Buleleng", "Denpasar", "Klungkung", "Jembrana"]:
            if kab.lower() in str(lokasi_str).lower():
                return "Kota Denpasar" if kab == "Denpasar" else f"Kabupaten {kab}"
        return "Lainnya"

    def get_kecamatan(lokasi_str):
        match = re.search(r"Kec\.\s*([^,]+)", str(lokasi_str))
        return match.group(1).strip() if match else "Umum"

    df['Kabupaten'] = df[col_lokasi].apply(get_kabupaten)
    df['Kecamatan'] = df[col_lokasi].apply(get_kecamatan)

    def parse_lat_lon(coord_str):
        try:
            if pd.isna(coord_str): return -8.4095, 115.1889
            parts = str(coord_str).split(',')
            lat_part, lon_part = parts[0], parts[1]
            
            lat_nums = [float(n) for n in re.findall(r"[-+]?\d*\.\d+|\d+", lat_part)]
            lon_nums = [float(n) for n in re.findall(r"[-+]?\d*\.\d+|\d+", lon_part)]
            
            lat_val = lat_nums[0] + (lat_nums[1]/60.0 if len(lat_nums)>1 else 0) + (lat_nums[2]/3600.0 if len(lat_nums)>2 else 0)
            lon_val = lon_nums[0] + (lon_nums[1]/60.0 if len(lon_nums)>1 else 0) + (lon_nums[2]/3600.0 if len(lon_nums)>2 else 0)
            
            if 'S' in lat_part or 's' in lat_part: lat_val = -lat_val
            return lat_val, lon_val
        except:
            return -8.4095, 115.1889

    coords = df[col_koordinat].apply(parse_lat_lon)
    df['Lat'] = [c[0] for c in coords]
    df['Lon'] = [c[1] for c in coords]
    
    return df

df_base = load_data()

orig_tempat = df_base.attrs['col_tempat']
orig_lokasi = df_base.attrs['col_lokasi']
orig_koordinat = df_base.attrs['col_koordinat']
orig_rating = df_base.attrs['col_rating']
orig_ulasan = df_base.attrs['col_ulasan']
orig_harga = df_base.attrs['col_harga']
orig_deskripsi = df_base.attrs['col_deskripsi']

# 4. BAGIAN SIDEBAR CONTROL PANEL
st.sidebar.title("🎛️ Control Panel")

kab_options = sorted(df_base['Kabupaten'].unique())
pilihan_kab = st.sidebar.multiselect("📍 Pilih Kabupaten / Kota", options=kab_options, default=kab_options)
df_f1 = df_base[df_base['Kabupaten'].isin(pilihan_kab)]

kec_options = sorted(df_f1['Kecamatan'].unique())
pilihan_kec = st.sidebar.multiselect("🧱 Pilih Wilayah Kecamatan", options=kec_options, default=kec_options)
df_f2 = df_f1[df_f1['Kecamatan'].isin(pilihan_kec)]

min_r, max_r = float(df_base['Rating_Clean'].min()), float(df_base['Rating_Clean'].max())
pilihan_rating = st.sidebar.slider("⭐ Batas Rating Destinasi", min_r, max_r, (min_r, max_r), step=0.1)
df_f3 = df_f2[(df_f2['Rating_Clean'] >= pilihan_rating[0]) & (df_f2['Rating_Clean'] <= pilihan_rating[1])]

min_h, max_h = int(df_base['Harga_Clean'].min()), int(df_base['Harga_Clean'].max())
pilihan_harga = st.sidebar.slider("💵 Rentang Tiket Masuk (Rp)", min_h, max_h, (min_h, max_h), step=5000)

df_filtered = df_f3[(df_f3['Harga_Clean'] >= pilihan_harga[0]) & (df_f3['Harga_Clean'] <= pilihan_harga[1])]

st.sidebar.markdown(f"""
    <div class="sidebar-card">
        <p style="margin:0; font-size:12px; font-weight:600; color:#b7e4c7 !important;">💡 Info Filter</p>
        <p style="margin:5px 0 0 0; font-size:13px; line-height:1.4; color:#ffffff !important;">Menampilkan <b>{len(df_filtered)}</b> dari total <b>{len(df_base)}</b> destinasi pariwisata Bali.</p>
    </div>
""", unsafe_allow_html=True)

# 5. HEADER UTAMA DASHBOARD
st.title("🌿 Bali Eco-Tourism Analytics Dashboard")
st.caption("Premium Nature Theme Dashboard")
st.markdown("---")

# 6. PENYUSUNAN 4 KARTU KPI UTAMA
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
with kpi1:
    st.metric("🗺️ Total Destinasi", f"{len(df_filtered)} Tempat")
with kpi2:
    avg_r = df_filtered['Rating_Clean'].mean() if len(df_filtered) > 0 else 0
    st.metric("⭐ Rata-rata Rating", f"{avg_r:.2f} / 5.0")
with kpi3:
    total_u = df_filtered['Ulasan_Clean'].sum() if len(df_filtered) > 0 else 0
    st.metric("💬 Total Ulasan", f"{total_u:,}".replace(',', '.'))
with kpi4:
    avg_h = df_filtered['Harga_Clean'].mean() if len(df_filtered) > 0 else 0
    st.metric("🎟️ Rata-rata Harga Tiket", f"Rp {int(avg_h):,}".replace(',', '.'))

st.markdown("<br>", unsafe_allow_html=True)

# 7. BARIS KEDUA: PETA DAN DIAGRAM PIE
col_map, col_pie = st.columns([1.2, 0.8])

with col_map:
    st.markdown('<div class="custom-subheader"><span class="custom-subheader-text">🗺️ Peta Wisata Alam Interaktif</span></div>', unsafe_allow_html=True)
    pencarian = st.text_input("🔍 Cari & Fokus Nama Tempat Wisata:", placeholder="Ketik nama tempat, misal: Ubud...")
    
    c_lat, c_lon, zoom = -8.4095, 115.1889, 9
    if pencarian and len(df_filtered) > 0:
        match = df_filtered[df_filtered[orig_tempat].str.lower().str.contains(pencarian.lower(), na=False)]
        if not match.empty:
            c_lat, c_lon, zoom = match.iloc[0]['Lat'], match.iloc[0]['Lon'], 13

    m = folium.Map(location=[c_lat, c_lon], zoom_start=zoom, tiles="OpenStreetMap")
    for _, row in df_filtered.iterrows():
        gmaps_link = f"https://www.google.com/maps/search/?api=1&query={row['Lat']},{row['Lon']}"
        map_harga = f"{int(row['Harga_Clean']):,}".replace(',', '.')
        popup_text = f"""
        <div style='font-family: Arial, sans-serif; width: 200px; color:#333333;'>
            <h5 style='margin:0 0 5px 0; color:#1b4332; font-weight:bold;'>{row[orig_tempat]}</h5>
            <b>⭐ Rating:</b> {row['Rating_Clean']}<br>
            <b>🎟️ Tiket:</b> Rp {map_harga}<br>
            <p style='font-size:11px; margin:5px 0;'>{row[orig_deskripsi]}</p>
            <a href='{gmaps_link}' target='_blank' style='display:block; text-align:center; padding:5px; background-color:#2d6a4f; color:white; border-radius:4px; text-decoration:none; font-weight:bold; font-size:11px;'>👉 Buka di Google Maps</a>
        </div>
        """
        folium.Marker(
            location=[row['Lat'], row['Lon']],
            popup=folium.Popup(popup_text, max_width=250),
            tooltip=row[orig_tempat],
            icon=folium.Icon(color='green', icon='leaf')
        ).add_to(m)
    
    st_folium(m, height=300, use_container_width=True, key="map_bali")

with col_pie:
    st.markdown('<div class="custom-subheader"><span class="custom-subheader-text">📊 Distribusi Wilayah Kabupaten</span></div>', unsafe_allow_html=True)
    if len(df_filtered) > 0:
        df_pie = df_filtered['Kabupaten'].value_counts().reset_index()
        # FIX PIE CHART: Menghilangkan hole=0.4 agar jadi bulat penuh dan berwarna-warni
        fig_pie = px.pie(df_pie, values='count', names='Kabupaten')
        fig_pie.update_layout(
            margin=dict(t=20, b=20, l=10, r=10), 
            legend=dict(
                orientation="h", 
                y=-0.15,
                font=dict(color='#ffffff')
            ),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#ffffff')
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("Tidak ada data untuk diagram sebaran.")

st.markdown("<br>", unsafe_allow_html=True)

# 8. BARIS KETIGA: GRAPH BAR TOP 10 DESTINASI & HARGA TIKET
g_col1, g_col2 = st.columns(2)

with g_col1:
    st.markdown('<div class="custom-subheader"><span class="custom-subheader-text">🏆 Top 10 Destinasi Terpopuler</span></div>', unsafe_allow_html=True)
    if len(df_filtered) > 0:
        df_top = df_filtered.sort_values(by=['Rating_Clean', 'Ulasan_Clean'], ascending=[False, False]).head(10)
        fig_top = px.bar(df_top, x='Rating_Clean', y=orig_tempat, orientation='h', color='Rating_Clean', color_continuous_scale='Greens')
        
        # FIX GRAFIK TOP 10: Memotong Sumbu X agar perbedaan bar terlihat jelas
        min_rating_zoom = max(0, df_top['Rating_Clean'].min() - 0.1)
        
        fig_top.update_layout(
            yaxis={'categoryorder':'total ascending'}, 
            coloraxis_showscale=False, 
            height=300, 
            margin=dict(t=10, b=10),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#ffffff', size=11)
        )
        fig_top.update_xaxes(range=[min_rating_zoom, 5.0]) # Memaksa sumbu X dimulai dari angka terendah Top 10
        
        st.plotly_chart(fig_top, use_container_width=True)

with g_col2:
    st.markdown('<div class="custom-subheader"><span class="custom-subheader-text">🎟️ Analisis Harga Tiket Masuk (Top 10)</span></div>', unsafe_allow_html=True)
    if len(df_filtered) > 0:
        df_h_sort = df_filtered.sort_values(by='Harga_Clean', ascending=False).head(10)
        fig_harga = px.bar(df_h_sort, x=orig_tempat, y='Harga_Clean', color_discrete_sequence=['#52b788'])
        fig_harga.update_traces(marker_color='#52b788')
        fig_harga.update_layout(
            height=300, 
            margin=dict(t=10, b=10),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#ffffff')
        )
        st.plotly_chart(fig_harga, use_container_width=True)

# 9. BARIS KEEMPAT: HISTOGRAM DAN SCATTER PLOT CORRELATION
g_col3, g_col4 = st.columns(2)

with g_col3:
    st.markdown('<div class="custom-subheader"><span class="custom-subheader-text">📈 Histogram Sebaran Rating Destinasi</span></div>', unsafe_allow_html=True)
    if len(df_filtered) > 0:
        fig_hist = px.histogram(df_filtered, x='Rating_Clean', nbins=10, color_discrete_sequence=['#74c69d'])
        fig_hist.update_layout(
            height=300, 
            margin=dict(t=10, b=10),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#ffffff')
        )
        st.plotly_chart(fig_hist, use_container_width=True)

with g_col4:
    st.markdown('<div class="custom-subheader"><span class="custom-subheader-text">🎯 Korelasi: Rating vs Volume Ulasan</span></div>', unsafe_allow_html=True)
    if len(df_filtered) > 0:
        # Palet warna hijau kembalikan untuk scatter
        palet_alam = ['#52b788', '#74c69d', '#b7e4c7', '#d8f3dc', '#40916c', '#2d6a4f', '#1b4332']
        fig_scatter = px.scatter(df_filtered, x='Rating_Clean', y='Ulasan_Clean', size='Ulasan_Clean', color='Kabupaten', hover_name=orig_tempat, color_discrete_sequence=palet_alam)
        fig_scatter.update_layout(
            height=300, 
            margin=dict(t=10, b=10),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#ffffff'),
            legend=dict(font=dict(color='#ffffff'))
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

# 10. BARIS TERAKHIR: TABEL DATA UTAMA EXPLORER
st.markdown("---")
st.markdown('<div class="custom-subheader"><span class="custom-subheader-text">🗂️ Explorer Tabel Data Utama</span></div>', unsafe_allow_html=True)

kolom_tampil = [orig_tempat, orig_lokasi, orig_koordinat, orig_rating, orig_ulasan, orig_harga, orig_deskripsi]

df_display = df_filtered[kolom_tampil].copy()
df_display[orig_harga] = df_filtered['Harga_Clean'].apply(lambda x: f"Rp {x:,}".replace(',', '.'))
df_display[orig_ulasan] = df_filtered['Ulasan_Clean'].apply(lambda x: f"{x:,}".replace(',', '.'))
df_display[orig_rating] = df_filtered['Rating_Clean'].apply(lambda x: f"{x:.1f}")

st.dataframe(df_display, use_container_width=True, hide_index=True)