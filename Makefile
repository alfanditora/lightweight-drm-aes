# Nama berkas: Makefile

# Untuk Windows, path eksekusi venv bawaan uv adalah .venv/Scripts
VENV_BIN = venv\Scripts

.PHONY: help run-server run-client test clean

help:
	@echo "Perintah Makefile (Windows + uv) yang tersedia:"
	@echo "  make run-server  - Menjalankan FastAPI Server via uv .venv"
	@echo "  make run-client  - Menjalankan simulasi DRM Client via uv .venv"
	@echo "  make test        - Otomatisasi penuh: Jalankan server (bg), tes klien, lalu matikan server"
	@echo "  make clean       - Membersihkan berkas cache (__pycache__)"

run-server:
	@echo "--> Menjalankan Uvicorn Server via uv .venv..."
	cd server && ..\$(VENV_BIN)\python.exe -m uvicorn server:app --reload --port 8000

run-cli:
	@echo "--> Menjalankan CustomTkinter DRM Client CLI..."
	$(VENV_BIN)\python.exe -m client.run_experiments_cli

run-gui:
	@echo "--> Menjalankan CustomTkinter DRM Client GUI..."
	$(VENV_BIN)\python.exe -m client.client_gui

test:
	@echo "--> Memulai Otomatisasi Eksperimen DRM (Windows + uv)..."
	@echo "--> Langkah 1: Menjalankan server di latar belakang..."
	# Menggunakan ekstensi .exe untuk kompatibilitas Windows di background process
	cd server && ../$(VENV_BIN)/python.exe -m uvicorn server:app --port 8000 > /dev/null 2>&1 & echo $$! > server.pid
	@echo "--> Menunggu 3 detik agar server siap..."
	sleep 3
	@echo "--> Langkah 2: Menjalankan simulasi Client Player..."
	-cd client && ../$(VENV_BIN)/python.exe client.py
	@echo "--> Langkah 3: Menghentikan server di latar belakang..."
	@if [ -f server/server.pid ]; then \
		pid=$$(cat server/server.pid) && taskkill //F //PID $$pid && rm server/server.pid; \
	fi
	@echo "--> Eksperimen Selesai."

clean:
	@echo "--> Membersihkan __pycache__ dan artifacts..."
	rm -rf server/__pycache__ client/__pycache__
	@if [ -f server/server.pid ]; then rm server/server.pid; fi