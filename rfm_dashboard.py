# =========================================
# RFM DASHBOARD - STREAMLIT (DEPLOY + UPLOAD)
# =========================================

import pandas as pd
import streamlit as st
import plotly.express as px
from datetime import timedelta
from io import BytesIO
import os

# =========================================
# KONFIGURASI HALAMAN
# =========================================
st.set_page_config(
    page_title="RFM Dashboard",
    layout="wide"
)

st.title("📊 RFM Analysis Dashboard")

# =========================================
# PILIH SUMBER DATA
# =========================================
st.subheader("📂 Sumber Data")
use_upload = st.checkbox("Gunakan file CSV lain (upload)", value=False)

df = None

if use_upload:
    uploaded_file = st.file_uploader(
        "Upload file CSV (delimiter ;)",
        type=["csv"]
    )
    if uploaded_file is None:
        st.stop()

    df = pd.read_csv(
        uploaded_file,
        sep=";",
        encoding="latin1"
    )
    st.success("✅ Data berhasil diupload")

else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(BASE_DIR, "bank data 2.csv")

    if not os.path.exists(file_path):
        st.error("❌ File CSV default tidak ditemukan")
        st.stop()

    df = pd.read_csv(
        file_path,
        sep=";",
        encoding="latin1"
    )
    st.success("✅ Data dibaca dari repository")

# =========================================
# BERSIHKAN KOLOM UNNAMED
# =========================================
df = df.loc[:, ~df.columns.str.contains("^Unnamed")]

st.dataframe(df.head())

# =========================================
# DATA CLEANING
# =========================================
df['TransactionDate'] = pd.to_datetime(
    df['TransactionDate'], errors='coerce'
)

df['Amount'] = (
    df['Amount']
    .astype(str)
    .str.replace('.', '', regex=False)
    .str.replace(',', '.', regex=False)
    .astype(float)
)

df = df.dropna(subset=['CustomerID', 'TransactionDate', 'Amount'])

st.info(f"Jumlah data transaksi bersih: {len(df)}")

# =========================================
# HITUNG RFM
# =========================================
snapshot_date = df['TransactionDate'].max() + timedelta(days=1)

rfm = df.groupby('CustomerID').agg(
    Recency=('TransactionDate', lambda x: (snapshot_date - x.max()).days),
    Frequency=('CustomerID', 'count'),
    Monetary=('Amount', 'sum')
)

# =========================================
# RFM SCORING (ANTI ERROR)
# =========================================
def safe_qcut(series, labels):
    q = min(series.nunique(), len(labels))
    return pd.qcut(
        series.rank(method="first"),
        q=q,
        labels=labels[-q:]
    ).astype(int)

rfm['R_Score'] = safe_qcut(rfm['Recency'], [5,4,3,2,1])
rfm['F_Score'] = safe_qcut(rfm['Frequency'], [1,2,3,4,5])
rfm['M_Score'] = safe_qcut(rfm['Monetary'], [1,2,3,4,5])

rfm['RFM_Score'] = (
    rfm['R_Score'].astype(str) +
    rfm['F_Score'].astype(str) +
    rfm['M_Score'].astype(str)
)

# =========================================
# SEGMENTASI
# =========================================
def rfm_segment(row):
    if row['R_Score'] == 5 and row['F_Score'] == 5:
        return 'Champions'
    elif row['R_Score'] >= 4 and row['F_Score'] >= 4:
        return 'Loyal Customers'
    elif row['R_Score'] >= 4:
        return 'Potential Loyalist'
    elif row['R_Score'] <= 2 and row['F_Score'] >= 4:
        return 'At Risk'
    else:
        return 'Others'

rfm['Segment'] = rfm.apply(rfm_segment, axis=1)

# =========================================
# METRIC
# =========================================
c1, c2, c3 = st.columns(3)
c1.metric("Total Customers", rfm.shape[0])
c2.metric("Total Revenue", f"{rfm['Monetary'].sum():,.0f}")
c3.metric("Rata-rata Recency (hari)", round(rfm['Recency'].mean(), 1))

st.divider()

# =========================================
# VISUALISASI
# =========================================
seg = rfm['Segment'].value_counts().reset_index()
seg.columns = ['Segment', 'Jumlah']

st.plotly_chart(px.bar(seg, x='Segment', y='Jumlah'), use_container_width=True)
st.plotly_chart(
    px.scatter(rfm, x='Recency', y='Frequency', color='Segment',
               hover_data=['Monetary']),
    use_container_width=True
)
st.plotly_chart(
    px.box(rfm, x='Segment', y='Monetary'),
    use_container_width=True
)

# =========================================
# DOWNLOAD
# =========================================
output = BytesIO()
with pd.ExcelWriter(output, engine='openpyxl') as writer:
    rfm.reset_index().to_excel(writer, index=False)

st.download_button(
    "⬇ Download Hasil RFM (Excel)",
    data=output.getvalue(),
    file_name="hasil_rfm.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
