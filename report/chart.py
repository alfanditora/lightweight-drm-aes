import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Memuat data eksperimen dari CSV
csv_path = 'report\metrics_summary_report.csv'
df = pd.read_csv(csv_path)

# Merapikan label nama video agar pendek di sumbu X
df['Short Name'] = df['Video Name'].apply(lambda x: x.split('~')[-1].replace('.mp4', '').capitalize())

x_labels = df['Short Name'].tolist()
x_indexes = np.arange(len(x_labels))
bar_width = 0.35

# -------------------------------------------------------------------------
# FIGURE 1: Decryption Latency vs File Size
# -------------------------------------------------------------------------
plt.figure(figsize=(7, 5))
plt.bar(x_indexes - bar_width/2, df['Baseline Dec Time (s)'], width=bar_width, label='Baseline (Full)', color='#e3342f')
plt.bar(x_indexes + bar_width/2, df['Proposed Dec Time (s)'], width=bar_width, label='Proposed (Selective)', color='#38c172')
plt.title('Client Decryption Latency Comparison', fontsize=12, fontweight='bold')
plt.xlabel('Video Asset Scale')
plt.ylabel('Decryption Time (seconds)')
plt.xticks(x_indexes, x_labels)
plt.legend()
plt.grid(axis='y', linestyle='--', alpha=0.6)
plt.tight_layout()
plt.savefig('decryption_latency.png', dpi=300)
plt.close()

# -------------------------------------------------------------------------
# FIGURE 2: Throughput vs File Size
# -------------------------------------------------------------------------
plt.figure(figsize=(7, 5))
plt.bar(x_indexes - bar_width/2, df['Baseline Throughput (Mbps)'], width=bar_width, label='Baseline (Full)', color='#e3342f')
plt.bar(x_indexes + bar_width/2, df['Proposed Throughput (Mbps)'], width=bar_width, label='Proposed (Selective)', color='#38c172')
plt.title('Data Decryption Throughput Rate', fontsize=12, fontweight='bold')
plt.xlabel('Video Asset Scale')
plt.ylabel('Throughput (Mbps)')
plt.xticks(x_indexes, x_labels)
plt.legend()
plt.grid(axis='y', linestyle='--', alpha=0.6)
plt.tight_layout()
plt.savefig('throughput_rate.png', dpi=300)
plt.close()

# -------------------------------------------------------------------------
# FIGURE 3: Visual Degradation (PSNR / SSIM) under Unauthorized Attempt
# -------------------------------------------------------------------------
# Skenario: Authorized vs Unauthorized
scenarios = ['Authorized\n(Valid CEK)', 'Unauthorized\n(No CEK)']
psnr_values = [45.0, 6.25]  # 45 dB diplot sebagai perwakilan inf agar grafik dapat dirender visual

fig, ax1 = plt.subplots(figsize=(7, 5))

# Plot bar untuk PSNR (Sumbu Y kiri)
color = '#4f46e5'
ax1.set_xlabel('Scenario Profile')
ax1.set_ylabel('PSNR (dB)', color=color, fontweight='bold')
bars = ax1.bar(scenarios, psnr_values, color=color, alpha=0.6, width=0.4, label='PSNR (dB)')
ax1.tick_params(axis='y', labelcolor=color)
ax1.set_ylim(0, 50)

# Tambahkan label teks khusus untuk nilai "Infinity" di bar Authorized
ax1.text(0, 46, r'$\infty$ (Perfect)', ha='center', va='bottom', color=color, fontweight='bold')
ax1.text(1, 7.25, '6.25 dB', ha='center', va='bottom', color=color, fontweight='bold')

# Buat sumbu Y kedua di sebelah kanan untuk SSIM
ax2 = ax1.twinx()
color = '#f59e0b'
ax2.set_ylabel('SSIM Value', color=color, fontweight='bold')
# Plot line untuk SSIM (Sumbu Y kanan)
ax2.plot(scenarios, [1.00, 0.02], color=color, marker='o', linewidth=2.5, markersize=8, label='SSIM')
ax2.tick_params(axis='y', labelcolor=color)
ax2.set_ylim(0, 1.1)

# Tambahkan teks nilai SSIM di titik marker
ax2.text(0, 0.92, '1.00', ha='center', va='bottom', color=color, fontweight='bold')
ax2.text(1, 0.06, '0.02', ha='center', va='top', color=color, fontweight='bold')

plt.title('Perceptual Quality Visual Degradation Profile', fontsize=12, fontweight='bold')
plt.tight_layout()
plt.savefig('visual_degradation.png', dpi=300)
plt.close()

print("[Success] Tiga berkas gambar terpisah berhasil diekspor.")