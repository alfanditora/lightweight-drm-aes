# client/metrics_utils.py
import math
import cv2
import numpy as np

def calculate_psnr(img1: np.ndarray, img2: np.ndarray) -> float:
    """
    Hitung PSNR (Peak Signal-to-Noise Ratio) berdasarkan rumus matematika.
    """
    mse = np.mean((img1.astype(float) - img2.astype(float)) ** 2)
    if mse == 0:
        return float('inf')
    max_pixel = 255.0
    psnr = 20 * math.log10(max_pixel / math.sqrt(mse))
    return psnr

def calculate_ssim(img1: np.ndarray, img2: np.ndarray) -> float:
    """
    Hitung SSIM (Structural Similarity Index) berdasarkan rumus matematika.
    """
    if len(img1.shape) == 3:
        img1_gray = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY).astype(float)
        img2_gray = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY).astype(float)
    else:
        img1_gray = img1.astype(float)
        img2_gray = img2.astype(float)
        
    x = img1_gray
    y = img2_gray
    
    # Rata-rata
    mu_x = np.mean(x)
    mu_y = np.mean(y)
    
    # Variansi dan Kovariansi
    sigma_x_sq = np.var(x)
    sigma_y_sq = np.var(y)
    sigma_xy = np.mean((x - mu_x) * (y - mu_y))
    
    # Konstanta stabilitas (k1, k2 << 1)
    k1 = 0.01
    k2 = 0.03
    L = 255.0
    c1 = (k1 * L) ** 2
    c2 = (k2 * L) ** 2
    
    # Rumus SSIM
    numerator = (2 * mu_x * mu_y + c1) * (2 * sigma_xy + c2)
    denominator = (mu_x**2 + mu_y**2 + c1) * (sigma_x_sq + sigma_y_sq + c2)
    
    if denominator == 0:
        return 0.0
    return numerator / denominator

def generate_mock_images(has_key: bool, nal_type_corrupted: bool = False):
    """
    Membuat sepasang matriks gambar (original & test) untuk mensimulasikan rumus PSNR/SSIM.
    """
    h, w = 256, 256
    # Buat gradasi diagonal untuk variasi struktur
    x = np.linspace(0, 255, w)
    y = np.linspace(0, 255, h)
    xx, yy = np.meshgrid(x, y)
    img1 = ((xx + yy) / 2).astype(np.uint8)
    
    # Gambar pola lingkaran di tengah
    cv2.circle(img1, (128, 128), 64, 255, -1)
    cv2.circle(img1, (128, 128), 32, 0, -1)
    
    if has_key:
        return img1, img1.copy()
        
    if not nal_type_corrupted:
        # Full Encryption (completely destroyed start codes/container)
        # Menghasilkan citra noise abu-abu acak (TV static)
        np.random.seed(42)
        img2 = np.random.randint(0, 256, (h, w), dtype=np.uint8)
        return img1, img2
    else:
        # Selective Encryption (SPS/PPS/IDR corrupted, P & B frames cleared)
        # Sebagian besar makroblok diacak, sebagian disisakan
        np.random.seed(42)
        img2 = img1.copy()
        block_size = 16
        for r in range(0, h, block_size):
            for c in range(0, w, block_size):
                # Acak 85% dari makroblok gambar
                if np.random.random() < 0.85:
                    img2[r:r+block_size, c:c+block_size] = np.random.randint(0, 256, (block_size, block_size), dtype=np.uint8)
        return img1, img2

def calculate_simulated_psnr(has_key: bool, nal_type_corrupted: bool = False, img1=None, img2=None) -> float:
    if img1 is not None and img2 is not None:
        return calculate_psnr(img1, img2)
    ref, test = generate_mock_images(has_key, nal_type_corrupted)
    return calculate_psnr(ref, test)

def calculate_simulated_ssim(has_key: bool, nal_type_corrupted: bool = False, img1=None, img2=None) -> float:
    if img1 is not None and img2 is not None:
        return calculate_ssim(img1, img2)
    ref, test = generate_mock_images(has_key, nal_type_corrupted)
    return calculate_ssim(ref, test)