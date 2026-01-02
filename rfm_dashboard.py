# =========================================
# RFM ANALYSIS + DASHBOARD VISUAL
# =========================================

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import timedelta
import os

# =========================================
# 1. LOAD DATA
# =========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(BASE_DIR, "bank data.xlsx")

df = pd.read_excel(file_path)

# =========================================
# 2. DATA CLEANING
# =========================================
# Pastikan nama kolom sesuai
df = df.rename(columns={
    'CustomerID': 'CustomerID',
    'TransactionDate': 'TransactionDate',
    'Amount': 'Amount'
})

# Konversi tanggal
df['TransactionDate'] = pd.to_datetime(df['TransactionDate'], errors='coerce')

# Hapus data kosong
df = df.dropna(subset=['CustomerID', 'TransactionDate', 'Amount'])

print("Jumlah data bersih:", len(df))

# =========================================
# 3. HITUNG RFM
# =========================================
snapshot_date = df['TransactionDate'].max() + timedelta(days=1)

rfm = df.groupby('CustomerID').agg({
    'TransactionDate': lambda x: (snapshot_date - x.max()).days,
    'CustomerID': 'count',
    'Amount': 'sum'
})

rfm.columns = ['Recency', 'Frequency', 'Monetary']

# =========================================
# 4. RFM SCORING
# =========================================
rfm['R_Score'] = pd.qcut(
    rfm['Recency'], 5, labels=[5,4,3,2,1], duplicates='drop'
)

rfm['F_Score'] = pd.qcut(
    rfm['Frequency'].rank(method='first'), 5, labels=[1,2,3,4,5], duplicates='drop'
)

rfm['M_Score'] = pd.qcut(
    rfm['Monetary'], 5, labels=[1,2,3,4,5], duplicates='drop'
)

rfm['RFM_Score'] = (
    rfm['R_Score'].astype(str) +
    rfm['F_Score'].astype(str) +
    rfm['M_Score'].astype(str)
)

# =========================================
# 5. SEGMENTASI PELANGGAN
# =========================================
def rfm_segment(row):
    if row['R_Score'] == '5' and row['F_Score'] == '5':
        return 'Champions'
    elif row['R_Score'] >= '4' and row['F_Score'] >= '4':
        return 'Loyal Customers'
    elif row['R_Score'] >= '4':
        return 'Potential Loyalist'
    elif row['R_Score'] <= '2' and row['F_Score'] >= '4':
        return 'At Risk'
    else:
        return 'Others'

rfm['Segment'] = rfm.apply(rfm_segment, axis=1)

print("\nContoh hasil RFM:")
print(rfm.head())

# =========================================
# 6. DASHBOARD VISUAL
# =========================================
sns.set(style="whitegrid")

# A. Distribusi Segmentasi
plt.figure(figsize=(8,5))
sns.countplot(data=rfm, x='Segment')
plt.title("Distribusi Segmen Pelanggan")
plt.xticks(rotation=30)
plt.tight_layout()
plt.show()

# B. Recency vs Frequency
plt.figure(figsize=(8,6))
sns.scatterplot(
    data=rfm,
    x='Recency',
    y='Frequency',
    hue='Segment'
)
plt.title("Recency vs Frequency")
plt.tight_layout()
plt.show()

# C. Monetary per Segment
plt.figure(figsize=(8,5))
sns.boxplot(
    data=rfm,
    x='Segment',
    y='Monetary'
)
plt.title("Monetary Value per Segment")
plt.xticks(rotation=30)
plt.tight_layout()
plt.show()

# D. Korelasi RFM
plt.figure(figsize=(6,5))
sns.heatmap(
    rfm[['Recency','Frequency','Monetary']].corr(),
    annot=True,
    cmap='coolwarm'
)
plt.title("Korelasi RFM")
plt.tight_layout()
plt.show()

# =========================================
# 7. EXPORT HASIL (OPSIONAL)
# =========================================
output_path = os.path.join(BASE_DIR, "hasil_rfm.xlsx")
rfm.to_excel(output_path)

print("\n✅ Analisis RFM selesai")
print("📁 File hasil:", output_path)
