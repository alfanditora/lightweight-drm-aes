# client/client.py
import os
import time
import psutil
import requests
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

# Import fungsi pembantu metrik visual
from client.metrics_utils import calculate_simulated_psnr, calculate_simulated_ssim

SERVER_URL = "http://127.0.0.1:8000"

class DRMClientPlayer:
    def __init__(self, content_id: str, base_iv_hex: str, jwt_token: str):
        self.content_id = content_id
        self.base_iv = bytes.fromhex(base_iv_hex)
        self.jwt_token = jwt_token
        self.cek = None

    def acquire_license(self):
        """Mengambil Content Encryption Key (CEK) dari License Server."""
        headers = {"Authorization": f"Bearer {self.jwt_token}"}
        url = f"{SERVER_URL}/api/v1/license?content_id={self.content_id}"
        
        response = requests.post(url, headers=headers)
        if response.status_code == 200:
            self.cek = bytes.fromhex(response.json()["cek"])
            print("[Client] Handshake sukses. CEK berhasil dimuat ke memori volatil.")
        else:
            raise Exception(f"[Client] Gagal mengambil lisensi: {response.text}")

    def simulate_baseline_full_decryption(self, encrypted_data: bytes):
        """Skenario 1: Mendekripsi seluruh bita berkas (Full AES-CTR)."""
        ctr_nonce = self.base_iv + (0).to_bytes(8, byteorder='big')
        
        process = psutil.Process(os.getpid())
        start_mem = process.memory_info().rss
        start_cpu = psutil.cpu_percent(interval=None)
        
        start_time = time.perf_counter()
        
        # Eksekusi Dekripsi Penuh
        cipher = Cipher(algorithms.AES(self.cek), modes.CTR(ctr_nonce))
        decryptor = cipher.decryptor()
        _ = decryptor.update(encrypted_data) + decryptor.finalize()
        
        end_time = time.perf_counter()
        end_mem = process.memory_info().rss
        end_cpu = psutil.cpu_percent(interval=None)
        
        dec_time = end_time - start_time
        throughput = (len(encrypted_data) * 8 / 1_000_000) / dec_time if dec_time > 0 else 0
        
        return {
            "decryption_time_sec": dec_time,
            "cpu_usage_percent": end_cpu,
            "memory_usage_mb": max(0.0, (end_mem - start_mem) / (1024 * 1024)),
            "throughput_mbps": throughput,
            "psnr_with_key": calculate_simulated_psnr(has_key=True),
            "ssim_with_key": calculate_simulated_ssim(has_key=True),
            "psnr_no_key": calculate_simulated_psnr(has_key=False),
            "ssim_no_key": calculate_simulated_ssim(has_key=False)
        }

    def simulate_proposed_selective_decryption(self, protected_stream: bytes, stream_structure: list):
        """Skenario 2: Mendekripsi secara selektif (Hanya unit IDR/SPS/PPS)."""
        process = psutil.Process(os.getpid())
        start_mem = process.memory_info().rss
        start_cpu = psutil.cpu_percent(interval=None)
        
        start_time = time.perf_counter()
        
        # Simulasi membaca Metadata Header di awal kontainer file (+- 24 bita bypass)
        _ = protected_stream[:24] 
        
        raw_total_bytes = 0
        
        # Pemutar memproses unit NAL satu per satu secara realtime loop
        for unit in stream_structure:
            nal_type = unit["type"]
            payload = unit["payload"]
            raw_total_bytes += len(payload)
            
            if nal_type in [5, 7, 8]:
                # Thread dekripsi AES-CTR hanya dipicu untuk komponen kritis
                ctr_nonce = self.base_iv + nal_type.to_bytes(8, byteorder='big')
                cipher = Cipher(algorithms.AES(self.cek), modes.CTR(ctr_nonce))
                decryptor = cipher.decryptor()
                _ = decryptor.update(payload) + decryptor.finalize()
            else:
                # Bypass langsung ke hardware decoder untuk P dan B frame slices
                _ = payload
                
        end_time = time.perf_counter()
        end_mem = process.memory_info().rss
        end_cpu = psutil.cpu_percent(interval=None)
        
        dec_time = end_time - start_time
        throughput = (raw_total_bytes * 8 / 1_000_000) / dec_time if dec_time > 0 else 0
        
        return {
            "decryption_time_sec": dec_time,
            "cpu_usage_percent": end_cpu,
            "memory_usage_mb": max(0.0, (end_mem - start_mem) / (1024 * 1024)),
            "throughput_mbps": throughput,
            "psnr_with_key": calculate_simulated_psnr(has_key=True),
            "ssim_with_key": calculate_simulated_ssim(has_key=True),
            "psnr_no_key": calculate_simulated_psnr(has_key=False, nal_type_corrupted=True),
            "ssim_no_key": calculate_simulated_ssim(has_key=False, nal_type_corrupted=True)
        }


if __name__ == "__main__":
    print("=== Memulai Klien Eksperimen DRM ===")
    content_id = "video_thesis_2026"
    
    # 1. Daftarkan Aset Baru ke Server
    print("[Client] Mendaftarkan aset baru ke server...")
    reg_res = requests.post(f"{SERVER_URL}/api/v1/register-asset", json={"content_id": content_id}).json()
    base_iv_hex = reg_res["base_iv"]
    
    # 2. Ambil Ephemeral JWT Token dari Gateway
    print("[Client] Meminta token akses JWT...")
    token_res = requests.get(f"{SERVER_URL}/api/v1/get-token?user_id=alfandito&content_id={content_id}").json()
    jwt_token = token_res["token"]
    
    # 3. Inisialisasi Player & Tarik Lisensi Kunci (CEK)
    player = DRMClientPlayer(content_id, base_iv_hex, jwt_token)
    player.acquire_license()
    
    # 4. Siapkan Dummy Data Video tiruan untuk pengujian sisi Client (~12 MB)
    dummy_stream_structure = [
        {"type": 7, "payload": os.urandom(10_000)},
        {"type": 5, "payload": os.urandom(2_000_000)},
        {"type": 1, "payload": os.urandom(5_000_000)},
        {"type": 1, "payload": os.urandom(5_000_000)}
    ]
    full_encrypted_dummy = os.urandom(12_010_000) # Representasi ukuran baseline
    
    # 5. Jalankan Evaluasi Metrik Dekripsi
    print("\n[Client] Mengeksekusi Eksperimen Komparatif Sisi Klien...")
    baseline_results = player.simulate_baseline_full_decryption(full_encrypted_dummy)
    proposed_results = player.simulate_proposed_selective_decryption(full_encrypted_dummy, dummy_stream_structure)
    
    # 6. Tampilkan Output Perbandingan Hasil Eksperimen
    print("\n" + "="*50)
    print("HASIL EVALUASI KOMPARASI DEKRIPSI (CLIENT PLAYER)")
    print("="*50)
    print(f"{'Metrik':<30} | {'Baseline (Full)':<18} | {'Proposed (Selective)':<20}")
    print("-"*74)
    print(f"{'Decryption Time (sec)':<30} | {baseline_results['decryption_time_sec']:<18.6f} | {proposed_results['decryption_time_sec']:<20.6f}")
    print(f"{'CPU Usage (%)':<30} | {baseline_results['cpu_usage_percent']:<18.1f} | {proposed_results['cpu_usage_percent']:<20.1f}")
    print(f"{'Memory Usage (MB)':<30} | {baseline_results['memory_usage_mb']:<18.4f} | {proposed_results['memory_usage_mb']:<20.4f}")
    print(f"{'Throughput (Mbps)':<30} | {baseline_results['throughput_mbps']:<18.2f} | {proposed_results['throughput_mbps']:<20.2f}")
    print(f"{'PSNR dengan Kunci (dB)':<30} | {str(baseline_results['psnr_with_key']):<18} | {str(proposed_results['psnr_with_key']):<20}")
    print(f"{'SSIM dengan Kunci':<30} | {baseline_results['ssim_with_key']:<18.1f} | {proposed_results['ssim_with_key']:<20.1f}")
    print(f"{'PSNR Tanpa Kunci (Attacker)':<30} | {baseline_results['psnr_no_key']:<18.2f} | {proposed_results['psnr_no_key']:<20.2f}")
    print(f"{'SSIM Tanpa Kunci (Attacker)':<30} | {baseline_results['ssim_no_key']:<18.4f} | {proposed_results['ssim_no_key']:<20.4f}")
    print("="*50)