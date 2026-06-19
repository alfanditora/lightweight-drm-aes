# server/packager.py
import os
import time
import psutil
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

class ExperimentPackager:
    @staticmethod
    def generate_keys():
        cek = os.urandom(16)
        base_iv = os.urandom(8)
        return cek, base_iv

    @staticmethod
    def parse_h264_stream(stream_bytes: bytes) -> list:
        """
        Membagi stream bita video H.264 menjadi unit NAL berdasarkan Annex-B Start Code.
        """
        nal_units = []
        i = 0
        length = len(stream_bytes)
        
        # Cari start code pertama
        while i < length - 4:
            if stream_bytes[i:i+3] == b'\x00\x00\x01':
                start_idx = i
                start_code_len = 3
                break
            elif stream_bytes[i:i+4] == b'\x00\x00\x00\x01':
                start_idx = i
                start_code_len = 4
                break
            i += 1
        else:
            # Jika tidak ditemukan start code, anggap sebagai satu kesatuan payload (fallback)
            return [{"type": 1, "payload": stream_bytes, "prefix": b""}]

        # Loop untuk mengisolasi setiap NAL unit
        while start_idx < length:
            i = start_idx + start_code_len
            next_start = length
            next_code_len = 0
            
            # Cari start code berikutnya
            while i < length - 4:
                if stream_bytes[i:i+3] == b'\x00\x00\x01':
                    next_start = i
                    next_code_len = 3
                    break
                elif stream_bytes[i:i+4] == b'\x00\x00\x00\x01':
                    next_start = i
                    next_code_len = 4
                    break
                i += 1
                
            # Ambil bita NAL unit dari start code saat ini sampai start code berikutnya
            nal_data = stream_bytes[start_idx:next_start]
            prefix = stream_bytes[start_idx:start_idx+start_code_len]
            payload = stream_bytes[start_idx+start_code_len:next_start]
            
            if len(payload) > 0:
                # NAL unit header adalah bita pertama setelah start code
                header_byte = payload[0]
                # Mengambil 5-bit tipe NAL (nal_unit_type = header_byte & 0x1F)
                nal_type = header_byte & 0x1F
                
                nal_units.append({
                    "type": nal_type,
                    "payload": payload,
                    "prefix": prefix
                })
                
            start_idx = next_start
            start_code_len = next_code_len
            
        return nal_units

    @staticmethod
    def run_baseline_full_encryption(video_data: bytes, cek: bytes, base_iv: bytes):
        ctr_nonce = base_iv + (0).to_bytes(8, byteorder='big')
        process = psutil.Process(os.getpid())
        start_mem = process.memory_info().rss
        start_cpu = psutil.cpu_percent(interval=None)
        
        start_time = time.perf_counter()
        
        cipher = Cipher(algorithms.AES(cek), modes.CTR(ctr_nonce))
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(video_data) + encryptor.finalize()
        
        end_time = time.perf_counter()
        enc_time = end_time - start_time
        
        return ciphertext, {
            "encryption_time_sec": enc_time,
            "cpu_usage_percent": psutil.cpu_percent(interval=None),
            "memory_usage_mb": max(0.0, (process.memory_info().rss - start_mem) / (1024 * 1024)),
            "throughput_mbps": (len(video_data) * 8 / 1_000_000) / enc_time if enc_time > 0 else 0,
            "file_size_bytes": len(ciphertext),
            "overhead_bytes": 0
        }

    @staticmethod
    def run_proposed_selective_encryption(parsed_nal_units: list, cek: bytes, base_iv: bytes):
        process = psutil.Process(os.getpid())
        start_mem = process.memory_info().rss
        
        start_time = time.perf_counter()
        protected_stream = bytearray()
        
        # Injeksi DRM Metadata Header (24 bita)
        protected_stream.extend(os.urandom(16))  # Content_ID dummy
        protected_stream.extend(base_iv)         # Base IV
        overhead_bytes = len(protected_stream)
        
        raw_total_bytes = 0
        
        for unit in parsed_nal_units:
            nal_type = unit["type"]
            payload = unit["payload"]
            prefix = unit["prefix"]
            raw_total_bytes += (len(prefix) + len(payload))
            
            # Pasang kembali start code-nya dalam bentuk clear text
            protected_stream.extend(prefix)
            
            # Enkripsi Selektif hanya pada IDR (5), SPS (7), PPS (8)
            if nal_type in [5, 7, 8]:
                ctr_nonce = base_iv + nal_type.to_bytes(8, byteorder='big')
                cipher = Cipher(algorithms.AES(cek), modes.CTR(ctr_nonce))
                encryptor = cipher.encryptor()
                encrypted_payload = encryptor.update(payload) + encryptor.finalize()
                protected_stream.extend(encrypted_payload)
            else:
                # Bypass langsung untuk P dan B frame slices
                protected_stream.extend(payload)
                
        end_time = time.perf_counter()
        enc_time = end_time - start_time
        
        return bytes(protected_stream), {
            "encryption_time_sec": enc_time,
            "cpu_usage_percent": psutil.cpu_percent(interval=None),
            "memory_usage_mb": max(0.0, (process.process_info().rss - start_mem) / (1024 * 1024) if hasattr(process, 'process_info') else 0.0),
            "throughput_mbps": (raw_total_bytes * 8 / 1_000_000) / enc_time if enc_time > 0 else 0,
            "file_size_bytes": len(protected_stream),
            "overhead_bytes": overhead_bytes
        }