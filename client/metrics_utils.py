# client/metrics_utils.py
import math

def calculate_simulated_psnr(has_key: bool, nal_type_corrupted: bool = False) -> float:
    """
    Simulasi perhitungan PSNR (Peak Signal-to-Noise Ratio).
    Jika kunci valid ada, kualitas sempurna (PSNR > 40 dB atau inf).
    Jika tanpa kunci, ketiadaan jangkar IDR/SPS/PPS merusak matriks spasial (PSNR < 10 dB).
    """
    if has_key:
        return float('inf')  # Sempurna, tidak ada noise
    
    # Tanpa kunci (Kondisi menyerang / unwatchable state)
    if nal_type_corrupted:
        return 6.25  # Sangat rendah, sinyal hancur total akibat kehilangan IDR/SPS/PPS
    return 8.12

def calculate_simulated_ssim(has_key: bool, nal_type_corrupted: bool = False) -> float:
    """
    Simulasi perhitungan SSIM (Structural Similarity Index) berkisar antara 0 hingga 1.
    Jika tanpa kunci, kedekatan struktural hancur mendekati 0.
    """
    if has_key:
        return 1.0  # Identik dengan video asli
        
    if nal_type_corrupted:
        return 0.02  # Struktur gambar rusak total, tidak bisa dikenali oleh mata
    return 0.08