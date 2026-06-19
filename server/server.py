# server.py
import os
import jwt
import datetime
from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

# Import komponen internal
from config import SECRET_KEY, ALGORITHM, key_database
from packager import ExperimentPackager

app = FastAPI(title="DRM Centralized License Server")
security = HTTPBearer()

class RegisterAssetRequest(BaseModel):
    content_id: str

def verify_jwt(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Validasi token JWT akses client[cite: 99]."""
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token Tidak Valid/Kedaluwarsa")


@app.post("/api/v1/register-asset")
def register_asset(req: RegisterAssetRequest):
    """Endpoint internal bagi Packager untuk mendaftarkan aset baru."""
    cek, base_iv = ExperimentPackager.generate_keys()
    key_database[req.content_id] = {
        "cek": cek.hex(),
        "base_iv": base_iv.hex()
    }
    return {
        "status": "Success",
        "content_id": req.content_id,
        "base_iv": base_iv.hex()
    }


@app.post("/api/v1/license")
def acquire_license(content_id: str, token_data: dict = Depends(verify_jwt)):
    """Mendistribusikan Content Encryption Key (CEK) ke client player[cite: 100, 105]."""
    if token_data.get("authorized_content_id") != content_id:
        raise HTTPException(status_code=403, detail="Akses Ditolak untuk Content ID ini")
    
    if content_id not in key_database:
        raise HTTPException(status_code=404, detail="Kunci tidak ditemukan")
        
    return {
        "content_id": content_id,
        "cek": key_database[content_id]["cek"]
    }


@app.get("/api/v1/get-token")
def simulate_gateway_issue_token(user_id: str, content_id: str):
    """Simulasi API Gateway menerbitkan token akses jangka pendek (ephemeral)[cite: 93, 96]."""
    expiration = datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
    payload = {
        "sub": user_id,
        "authorized_content_id": content_id,
        "exp": expiration
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return {"token": token}


@app.post("/api/v1/experiment/run-packager")
def run_packager_experiment(content_id: str, video_path: str = "../sample.mp4"):
    if content_id not in key_database:
        raise HTTPException(status_code=404, detail="Daftarkan asset terlebih dahulu")
        
    if not os.path.exists(video_path):
        raise HTTPException(status_code=400, detail=f"Berkas video asli tidak ditemukan di {video_path}")
        
    with open(video_path, "rb") as f:
        full_raw_video = f.read()
        
    cek = bytes.fromhex(key_database[content_id]["cek"])
    base_iv = bytes.fromhex(key_database[content_id]["base_iv"])
    
    # Lakukan parsing bita asli H.264/AVC
    parsed_video = ExperimentPackager.parse_h264_stream(full_raw_video)
    
    # Jalankan pengujian enkripsi sesungguhnya
    _, baseline_metrics = ExperimentPackager.run_baseline_full_encryption(full_raw_video, cek, base_iv)
    _, proposed_metrics = ExperimentPackager.run_proposed_selective_encryption(parsed_video, cek, base_iv)
    
    return {
        "video_source": video_path,
        "experiment_target_size_bytes": len(full_raw_video),
        "baseline_full_crypto": baseline_metrics,
        "proposed_selective_crypto": proposed_metrics
    }