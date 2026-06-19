# Design and Implementation of a Lightweight Digital Rights Management System

Sistem *Digital Rights Management* (DRM) berbasis *Selective Encryption* (SE) sadar codec (*codec-aware*) yang efisien dan berbobot ringan (*lightweight*). Sistem ini mengamankan distribusi video H.264/AVC menggunakan algoritma AES-CTR dengan hanya mengonversi unit NAL struktural kritis (SPS, PPS, dan IDR Frame), sehingga mampu memangkas beban latensi komputasi di sisi klien hingga 93%.

## 🚀 Fitur Utama

* **Token-Based Gateway Auth:** Autentikasi lisensi aman via dynamic JSON Web Token (JWT).
* **Syntax-Aware Encryption:** Enkripsi selektif pada unit NAL 5 (IDR), 7 (SPS), dan 8 (PPS) dengan membiarkan bingkai P/B dalam bentuk plaintext demi performa maksimal.
* **Real-Time Client Decryption:** Dekripsi on-the-fly terintegrasi hardware acceleration via OpenSSL primitives.
* **Comprehensive GUI & CLI:** Antarmuka visual intuitif menggunakan `customtkinter` dan otomasi pengujian sekuensial lewat skrip CLI.

## 🛠️ Prasyarat & Lingkungan Sistem

Proyek ini dikembangkan menggunakan bahasa pemrograman **Python 3.13** dan dioptimalkan untuk lingkungan **Windows** menggunakan manajer dependensi **`uv`**.

Pastikan Anda telah memasang:

1. Python 3.13
2. `uv` (pacakge manager)
3. GnuWin32 atau Git Bash (untuk mengeksekusi utilitas `make` di Windows)

### Pemasangan Dependensi

Inisialisasi lingkungan virtual (`.venv`) dan pasang seluruh pustaka prasyarat melalui perintah:

```bash
uv venv
uv pip install -r requirements.txt
```

## 💻 Panduan Menjalankan Sistem (Otomasi via Makefile)

Gunakan perintah `make` untuk mengontrol siklus hidup server, pengemas video (packager), dan pemutar multimedia (client player).

### 1. Menampilkan Menu Bantuan

Untuk melihat daftar perintah otomasi yang tersedia, jalankan:

```bash
make help
```

### 2. Menjalankan Gateway & License Server

Eksekusi server lisensi berbasis FastAPI pada port 8000:

```bash
make run-server
```

### 3. Menjalankan Client GUI

Untuk membuka aplikasi pemutar video DRM interaktif berbasis antarmuka grafis (CustomTkinter):

```bash
make run-gui
```

### 4. Menjalankan Eksperimen Analisis CLI

Untuk mengeksekusi pengujian performa otomatis sekuensial (`run_experiments_cli.py`) guna mengumpulkan data latensi, throughput, dan utilitas CPU dari berbagai skala aset video:

```bash
make run-cli
```

### 5. Otomatisasi Tes End-to-End (Background Testing)

Perintah ini akan menjalankan server lisensi di latar belakang (background process), melakukan pengetesan loop dekripsi pada klien player, mengumpulkan metrik data, dan secara otomatis mematikan proses server kembali setelah eksperimen selesai:

```bash
make test
```

### 6. Membersihkan Sisa Artefak / Cache

Untuk menghapus berkas cache `__pycache__` dan berkas PID penanda background server:

```bash
make clean
```

## 📊 Hasil Eksperimen Singkat

Berdasarkan analisis performa pada dataset video berukuran hingga 1,1 GB, sistem ini menunjukkan hasil metrik sebagai berikut:

* Latensi Dekripsi Klien: Berkurang dari 0,782 detik menjadi 0,054 detik (Penghematan daya 93.0%).
* Throughput Pemrosesan: Melonjak sebesar 14,38 kali lipat hingga menyentuh kecepatan 172,669.1 Mbps.
* Kondisi Tanpa Lisensi (Serangan): Degradasi visual ekstrem dengan PSNR 8.43 dB dan SSIM 0.1767 yang merusak temporal decoding bita video sehingga konten sama sekali tidak dapat ditonton.

## 📂 Struktur Repositori

```text
├── server/
│   ├── server.py              # FastAPI license server & token verification
│   └── packager.py            # Annex-B bitstream parser & selective encryptor
├── client/
│   ├── client.py              # Core real-time decryption loop pipeline
│   ├── client_gui.py          # CustomTkinter interface rendering stack
│   └── run_experiments_cli.py # Automated benchmark orchestrator script
├── Makefile                   # Windows-optimized uv command automation shortcuts
└── requirements.txt           # Third-party production libraries configuration
```

## 📝 Lisensi & Pernyataan Akademis

Proyek ini disusun sebagai bagian dari luaran tugas eksperimen tugas makalah mata kuliah Kriptografi, Departemen Teknik Informatika, Institut Teknologi Bandung. Seluruh kode sumber bersifat open-source untuk kepentingan riset akademis berkelanjutan.
