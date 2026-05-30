# Panduan Menjalankan Proyek Secara Manual

**Federated Learning for Scam Detection**

---

## Daftar Isi

1. [Prasyarat](#1-prasyarat)
2. [Persiapan Project](#2-persiapan-project)
3. [Setup Virtual Environment](#3-setup-virtual-environment)
4. [Instalasi Dependensi](#4-instalasi-dependensi)
5. [Mode 1 — Training Federated via CLI](#5-mode-1--training-federated-via-cli)
6. [Mode 2 — Jalankan sebagai API (lokal)](#6-mode-2--jalankan-sebagai-api-lokal)
7. [Pengujian Endpoint API](#7-pengujian-endpoint-api)
8. [Akses dari Jaringan LAN](#8-akses-dari-jaringan-lan)
9. [Akses Publik via Ngrok](#9-akses-publik-via-ngrok)
10. [Konfigurasi Parameter Training](#10-konfigurasi-parameter-training)
11. [Generate Ulang Data](#11-generate-ulang-data)
12. [Troubleshooting](#12-troubleshooting)
13. [Docker — Menjalankan via Container](#13-docker--menjalankan-via-container)
14. [Docker — Menjalankan via Container](#13-docker--menjalankan-via-container)

---

## 1. Prasyarat

Pastikan tools berikut sudah terinstal sebelum memulai:

| Tool               | Versi Minimum | Cek Versi          |
| ------------------ | ------------- | ------------------ |
| Python             | 3.9+          | `python --version` |
| pip                | terbaru       | `pip --version`    |
| ngrok _(opsional)_ | v3+           | `ngrok version`    |

> **Windows:** Pastikan Python sudah ditambahkan ke `PATH` saat instalasi. Jika perintah `python` tidak dikenali, coba `py` sebagai penggantinya.

---

## 2. Persiapan Project

Masuk ke folder project:

```powershell
cd "C:\Users\jardm\Documents\Brawijaya\Berkas Akademik\Semester 1\1. Tugas\sister-kel\FL-Sc"
```

Verifikasi struktur folder sudah lengkap:

```powershell
Get-ChildItem
```

Output yang diharapkan:

```
api.py
data_generator.py
docker-compose.yml
Dockerfile
fl_client.py
fl_runner.py
fl_server.py
main.py
model.py
README.md
requirements.txt
data/
```

### Buat folder checkpoints

Folder ini dibutuhkan server untuk menyimpan checkpoint model dan sebagai volume mount Docker:

```powershell
# Windows (PowerShell)
New-Item -ItemType Directory -Force -Path checkpoints
```

```bash
# Linux / macOS
mkdir -p checkpoints
```

---

## 3. Setup Virtual Environment

### Buat virtual environment baru

```powershell
python -m venv .venv
```

### Aktifkan virtual environment

**Windows (PowerShell):**

```powershell
.venv\Scripts\Activate.ps1
```

> Jika muncul error _"execution of scripts is disabled"_, jalankan dulu:
>
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```
>
> lalu ulangi perintah aktivasi.

**Windows (Command Prompt):**

```cmd
.venv\Scripts\activate.bat
```

**Linux / macOS:**

```bash
source .venv/bin/activate
```

### Verifikasi aktivasi

Setelah berhasil, prompt terminal akan berubah menjadi:

```
(.venv) PS C:\...\FL-Sc>
```

---

## 4. Instalasi Dependensi

```powershell
pip install -r requirements.txt
```

Paket yang akan diinstal:

| Paket          | Kegunaan                            |
| -------------- | ----------------------------------- |
| `torch`        | Neural network (ScamDetector model) |
| `numpy`        | Operasi array numerik               |
| `pandas`       | Baca/tulis data CSV                 |
| `scikit-learn` | Metrik evaluasi (accuracy, F1)      |
| `fastapi`      | HTTP API framework                  |
| `uvicorn`      | ASGI server untuk FastAPI           |

Verifikasi instalasi berhasil:

```powershell
pip show torch fastapi uvicorn
```

---

## 5. Mode 1 — Training Federated via CLI

Mode ini menjalankan seluruh siklus Federated Learning langsung dari terminal tanpa API.

```powershell
python main.py
```

### Yang terjadi secara otomatis:

1. Data sintetis di-generate ke folder `data/` (jika belum ada)
2. Server global dan 2 client diinisialisasi
3. Training berjalan selama **10 round** (FedAvg)
4. Metrik ditampilkan setiap round
5. Hasil round terbaik ditampilkan di akhir

### Contoh output terminal:

```
Generating data for 2 clients...
Data saved to data/

=== Federated Learning: Round 1/10 ===
  Client 1 — loss: 0.6821  acc: 0.5833
  Client 2 — loss: 0.6754  acc: 0.6117
  [Server] Global accuracy: 0.6233  F1: 0.5981

=== Federated Learning: Round 5/10 ===
  Client 1 — loss: 0.4312  acc: 0.8083
  Client 2 — loss: 0.4187  acc: 0.8217
  [Server] Global accuracy: 0.8367  F1: 0.8291

...

=== Training Selesai ===
Best Round : 9
Best Accuracy : 0.8933
Best F1 Score : 0.8871
```

---

## 6. Mode 2 — Jalankan sebagai API (lokal)

Mode ini menjalankan server HTTP sehingga training bisa dipicu via request dari browser atau aplikasi lain.

### Jalankan API server

```powershell
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

| Flag             | Keterangan                                            |
| ---------------- | ----------------------------------------------------- |
| `--host 0.0.0.0` | Terima koneksi dari semua interface (LAN & localhost) |
| `--port 8000`    | Port yang digunakan                                   |
| `--reload`       | Auto-restart saat ada perubahan kode _(development)_  |

### Verifikasi server berjalan

Buka browser dan akses:

```
http://127.0.0.1:8000/docs
```

Halaman **Swagger UI** akan tampil dengan daftar semua endpoint.

---

## 7. Pengujian Endpoint API

### 7.1 Health Check

Verifikasi server hidup:

```powershell
curl http://127.0.0.1:8000/health
```

Respons yang diharapkan:

```json
{ "status": "ok" }
```

### 7.2 Trigger Training

Jalankan federated training dengan konfigurasi default (10 round):

```powershell
curl -X POST http://127.0.0.1:8000/train `
     -H "Content-Type: application/json" `
     -d '{}'
```

Atau dengan konfigurasi kustom:

```powershell
curl -X POST http://127.0.0.1:8000/train `
     -H "Content-Type: application/json" `
     -d '{\"n_rounds\": 5, \"local_epochs\": 3, \"learning_rate\": 0.01}'
```

> **Catatan:** Training berjalan sinkron. Request akan menunggu hingga semua round selesai sebelum respons dikembalikan.

Contoh respons:

```json
{
  "status": "success",
  "best_round": 4,
  "best_accuracy": 0.8867,
  "best_f1": 0.8812,
  "config": {
    "n_rounds": 5,
    "local_epochs": 3,
    "learning_rate": 0.01,
    "batch_size": 32
  },
  "rounds": [...]
}
```

### 7.3 Lihat Hasil Training Terakhir

```powershell
curl http://127.0.0.1:8000/last-result
```

### 7.4 Lihat Daftar Endpoint

```powershell
curl http://127.0.0.1:8000/
```

---

## 8. Akses dari Jaringan LAN

API dapat diakses dari perangkat lain (HP, laptop teman) dalam jaringan WiFi yang sama.

### Langkah 1 — Cari IP lokal komputer host

```powershell
ipconfig
```

Cari baris **IPv4 Address** pada adapter WiFi, contoh: `192.168.1.10`

### Langkah 2 — Izinkan port 8000 di firewall Windows

```powershell
New-NetFirewallRule -DisplayName "FL-Scam API" `
    -Direction Inbound `
    -Protocol TCP `
    -LocalPort 8000 `
    -Action Allow
```

> Perintah ini membutuhkan PowerShell sebagai **Administrator**.

### Langkah 3 — Akses dari perangkat lain

Dari perangkat lain yang terhubung ke WiFi yang sama, buka browser dan akses:

```
http://192.168.1.10:8000/health
```

_(Ganti `192.168.1.10` dengan IP lokal aktual dari Langkah 1)_

---

## 9. Akses Publik via Ngrok

Ngrok membuat tunnel dari internet ke server lokal sehingga API dapat diakses dari luar jaringan.

### Langkah 1 — Pastikan API server sudah berjalan

Di terminal pertama (biarkan tetap berjalan):

```powershell
uvicorn api:app --host 0.0.0.0 --port 8000
```

### Langkah 2 — Buka tunnel ngrok

Di terminal kedua:

```powershell
ngrok http 8000
```

### Langkah 3 — Salin URL publik

Output ngrok akan menampilkan:

```
Session Status   online
Account          your-account@email.com
Forwarding       https://xxxx-xxx-xxx-xxx-xxx.ngrok-free.app -> http://localhost:8000
```

Salin URL `https://xxxx-....ngrok-free.app` — URL ini bisa diakses dari mana saja.

### Langkah 4 — Test endpoint via URL publik

```powershell
curl https://xxxx-xxx-xxx-xxx-xxx.ngrok-free.app/health

curl -X POST https://xxxx-xxx-xxx-xxx-xxx.ngrok-free.app/train `
     -H "Content-Type: application/json" `
     -d '{\"n_rounds\": 3}'
```

> **Catatan:** URL ngrok berubah setiap kali tunnel dibuka ulang (pada akun gratis). URL hanya aktif selama ngrok berjalan.

---

## 10. Konfigurasi Parameter Training

Parameter dapat diubah melalui dua cara:

### Via request body API (`POST /train`)

```json
{
  "n_rounds": 10,
  "local_epochs": 5,
  "learning_rate": 0.01,
  "batch_size": 32,
  "samples_per_client": 600,
  "n_test": 300
}
```

### Via edit `main.py` (untuk Mode CLI)

Buka `main.py` dan ubah dict `CONFIG`:

```python
CONFIG = {
    "n_rounds": 10,          # Jumlah round federated
    "local_epochs": 5,       # Epoch training lokal per client per round
    "learning_rate": 0.01,   # Learning rate optimizer
    "batch_size": 32,        # Ukuran batch training
    "input_dim": 10,         # Dimensi input fitur (jangan diubah)
    "samples_per_client": 600,  # Jumlah sampel per client
    "n_test": 300,           # Jumlah sampel test set
}
```

### Penjelasan parameter

| Parameter            | Default | Keterangan                                                    |
| -------------------- | ------- | ------------------------------------------------------------- |
| `n_rounds`           | `10`    | Semakin banyak round → akurasi lebih tinggi, waktu lebih lama |
| `local_epochs`       | `5`     | Epoch training di masing-masing client sebelum kirim bobot    |
| `learning_rate`      | `0.01`  | Step size optimizer Adam                                      |
| `batch_size`         | `32`    | Jumlah sampel per batch gradient descent                      |
| `samples_per_client` | `600`   | Total data per client (non-IID split)                         |
| `n_test`             | `300`   | Ukuran dataset evaluasi global                                |

---

## 11. Generate Ulang Data

Data dibuat otomatis saat `main.py` pertama kali dijalankan. Untuk me-reset data:

```powershell
# Hapus data lama
Remove-Item -Recurse -Force data\

# Generate ulang
python data_generator.py
```

File yang akan dibuat ulang di folder `data/`:

| File               | Deskripsi                                   |
| ------------------ | ------------------------------------------- |
| `client1_data.csv` | Data SMS-like (~600 baris) untuk Client 1   |
| `client2_data.csv` | Data Email-like (~600 baris) untuk Client 2 |
| `test_data.csv`    | Dataset evaluasi global (~300 baris)        |

---

## 12. Troubleshooting

### Port 8000 sudah digunakan

```
ERROR: [Errno 10048] error while attempting to bind on address ('0.0.0.0', 8000)
```

**Solusi:** Cari dan hentikan proses yang menggunakan port 8000:

```powershell
# Cari PID proses
netstat -ano | findstr :8000

# Hentikan proses (ganti 12345 dengan PID aktual)
Stop-Process -Id 12345 -Force
```

Atau gunakan port lain:

```powershell
uvicorn api:app --host 0.0.0.0 --port 8080
```

---

### Virtual environment tidak aktif

Jika muncul error `ModuleNotFoundError`, pastikan virtual environment sudah aktif (ada `(.venv)` di awal prompt). Jalankan ulang:

```powershell
.venv\Scripts\Activate.ps1
```

---

### Script execution disabled (Windows)

```
.venv\Scripts\Activate.ps1 cannot be loaded because running scripts is disabled
```

**Solusi:**

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

### PyTorch tidak terinstal dengan benar

```
ModuleNotFoundError: No module named 'torch'
```

**Solusi:** Install ulang dengan versi yang sesuai:

```powershell
pip uninstall torch -y
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

---

### Ngrok: tunnel session expired

Ngrok gratis membatasi durasi tunnel. Jika tunnel terputus, jalankan ulang:

```powershell
ngrok http 8000
```

---

## 13. Docker — Menjalankan via Container

Proyek ini menyediakan dua file Docker Compose terpisah:

| File                        | Peran                                         |
| --------------------------- | --------------------------------------------- |
| `docker-compose.server.yml` | Menjalankan FL Server + API (`server_api.py`) |
| `docker-compose.client.yml` | Menjalankan FL Client (`client_worker.py`)    |

---

### 13.1 Build Image

Build image Docker dari `Dockerfile` di root project:

```powershell
docker build -t fl-scam-api .
```

Verifikasi image berhasil dibuat:

```powershell
docker images
```

---

### 13.2 Menjalankan Server

Pastikan folder `checkpoints` sudah ada sebelum menjalankan server (dibutuhkan sebagai volume mount):

```powershell
New-Item -ItemType Directory -Force -Path checkpoints
```

Jalankan FL Server beserta API-nya:

```powershell
docker compose -f docker-compose.server.yml up -d --build
```

| Flag                           | Keterangan                             |
| ------------------------------ | -------------------------------------- |
| `-f docker-compose.server.yml` | Tentukan file compose yang digunakan   |
| `up`                           | Buat dan jalankan container            |
| `-d`                           | Jalankan di background (detached mode) |
| `--build`                      | Rebuild image sebelum menjalankan      |

Cek server berjalan:

```powershell
curl http://127.0.0.1:8000/health
```

---

### 13.3 Menjalankan Client

Setiap client dijalankan dengan variabel environment `CLIENT_ID`, `SERVER_URL`, dan `DATA_PATH`.

**Client 1:**

```powershell
$env:CLIENT_ID = "1"
$env:SERVER_URL = "http://fl-scam-api:8000"
$env:DATA_PATH  = "/app/data/client1_data.csv"
docker compose -f docker-compose.client.yml up -d --build
```

**Client 2** (terminal baru):

```powershell
$env:CLIENT_ID = "2"
$env:SERVER_URL = "http://fl-scam-api:8000"
$env:DATA_PATH  = "/app/data/client2_data.csv"
docker compose -f docker-compose.client.yml up -d --build
```

> **Catatan:** `SERVER_URL` menggunakan nama service `fl-scam-api` (bukan `localhost`) agar komunikasi antar container berjalan melalui jaringan Docker internal.

---

### 13.4 Melihat Status Container

Daftar semua container yang sedang berjalan:

```powershell
docker ps
```

Daftar semua container (termasuk yang sudah berhenti):

```powershell
docker ps -a
```

Contoh output:

```
CONTAINER ID   IMAGE          COMMAND                  STATUS         PORTS                    NAMES
a1b2c3d4e5f6   fl-scam-api    "uvicorn server_api:…"   Up 2 minutes   0.0.0.0:8000->8000/tcp   fl-scam-api
```

---

### 13.5 Melihat Log Container

Log server secara real-time:

```powershell
docker logs -f fl-scam-api
```

Log client tertentu:

```powershell
docker logs -f fl_client_1
docker logs -f fl_client_2
```

Log sejumlah baris terakhir saja:

```powershell
docker logs --tail 50 fl-scam-api
```

---

### 13.6 Menghentikan dan Menghapus Container

Hentikan container server:

```powershell
docker compose -f docker-compose.server.yml down
```

Hentikan container client:

```powershell
docker compose -f docker-compose.client.yml down
```

Hentikan satu container secara manual:

```powershell
docker stop fl-scam-api
docker stop fl_client_1
```

Hapus container yang sudah berhenti:

```powershell
docker rm fl-scam-api
docker rm fl_client_1
```

Hentikan dan hapus sekaligus (termasuk network):

```powershell
docker compose -f docker-compose.server.yml down --remove-orphans
docker compose -f docker-compose.client.yml down --remove-orphans
```

---

### 13.7 Menghapus Image

Hapus image yang tidak diperlukan:

```powershell
docker rmi fl-scam-api
```

Hapus semua image yang tidak digunakan sekaligus (prune):

```powershell
docker image prune -a
```

---

### 13.8 Melihat Penggunaan Resource

Statistik CPU, RAM, dan network container secara live:

```powershell
docker stats
```

Untuk container tertentu saja:

```powershell
docker stats fl-scam-api
```

---

### 13.9 Masuk ke Shell Container (Debugging)

Membuka shell interaktif di dalam container yang sedang berjalan:

```powershell
docker exec -it fl-scam-api /bin/bash
```

Keluar dari shell container:

```bash
exit
```

---

### 13.10 Ringkasan Perintah Docker

| Perintah                                                    | Kegunaan                           |
| ----------------------------------------------------------- | ---------------------------------- |
| `docker build -t fl-scam-api .`                             | Build image dari Dockerfile        |
| `docker compose -f docker-compose.server.yml up -d --build` | Jalankan server di background      |
| `docker compose -f docker-compose.client.yml up -d --build` | Jalankan client di background      |
| `docker ps`                                                 | Lihat container yang berjalan      |
| `docker ps -a`                                              | Lihat semua container              |
| `docker logs -f <nama>`                                     | Ikuti log container secara live    |
| `docker stop <nama>`                                        | Hentikan container                 |
| `docker rm <nama>`                                          | Hapus container                    |
| `docker rmi fl-scam-api`                                    | Hapus image                        |
| `docker stats`                                              | Monitor resource container         |
| `docker exec -it <nama> /bin/bash`                          | Masuk ke shell container           |
| `docker compose … down`                                     | Hentikan & hapus container+network |

---

_Panduan ini mencakup semua langkah untuk menjalankan proyek secara manual maupun via Docker._
