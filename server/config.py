# config.py

SECRET_KEY = "secure_drm_secret"
ALGORITHM = "HS256"

# Database Kunci Sementara (Simulasi HSM / Key Store)
# Menyimpan pasangan Tuple (Content_ID: {"cek": hex, "base_iv": hex})
key_database = {}