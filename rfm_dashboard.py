# =========================================
# RFM DASHBOARD - STREAMLIT (FIXED & STABLE)
# =========================================

import pandas as pd
import streamlit as st
import plotly.express as px
from datetime import timedelta
from io import BytesIO

# =========================================
# KONFIGURASI HALAMAN
# =========================================
st.set_page_config(
    page_title="RFM Dashboard",
    layout="wide"
)

st.title("📊 RFM Analysis Dashboard")

# =========================================
# UPLOAD DATA
# =========================================
uploaded_file = st.file_uploader(
    "📂 Upload file CSV (delimiter ;)",
    type=["csv"]
)

if uploaded_file is None:
    st.warning("Silakan upload file CSV terlebih dahulu")
    st.stop()

df = pd.read_csv(
    uploaded_file,
    sep=";",
    encoding="latin1"
)

st.success("✅ File CSV berhasil dibaca")
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
    q = min(len(series.unique()), len(labels))
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
# SEGMENTASI RFM
# =========================================
def rfm_segment(row):
    if row['RFM_Score'] >= '555':
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
# METRIC RINGKAS
# =========================================
col1, col2, col3 = st.columns(3)

col1.metric("Total Customers", rfm.shape[0])
col2.metric("Total Revenue", f"{rfm['Monetary'].sum():,.0f}")
col3.metric("Rata-rata Recency (hari)", round(rfm['Recency'].mean(), 1))

st.divider()

# =========================================
# VISUALISASI
# =========================================
segment_df = rfm['Segment'].value_counts().reset_index()
segment_df.columns = ['Segment', 'Jumlah']

fig1 = px.bar(
    segment_df,
    x='Segment',
    y='Jumlah',
    title="Distribusi Segmen Pelanggan"
)
st.plotly_chart(fig1, use_container_width=True)

fig2 = px.scatter(
    rfm,
    x='Recency',
    y='Frequency',
    color='Segment',
    hover_data=['Monetary'],
    title="Recency vs Frequency"
)
st.plotly_chart(fig2, use_container_width=True)

fig3 = px.box(
    rfm,
    x='Segment',
    y='Monetary',
    title="Monetary Value per Segment"
)
st.plotly_chart(fig3, use_container_width=True)

# =========================================
# TABEL & DOWNLOAD
# =========================================
st.subheader("📋 Tabel RFM")
st.dataframe(rfm.reset_index())

output = BytesIO()
with pd.ExcelWriter(output, engine='openpyxl') as writer:
    rfm.reset_index().to_excel(writer, index=False, sheet_name='RFM')

st.download_button(
    label="⬇ Download Hasil RFM (Excel)",
    data=output.getvalue(),
    file_name="hasil_rfm.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
