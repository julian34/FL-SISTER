# Cara Menjalankan Proyek FL-Sc

Terdapat **4 mode** menjalankan proyek ini, pilih sesuai kebutuhan.

---

## Prasyarat

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate

pip install -r requirements.txt
```

---

## Mode 1 — Simulasi Lokal (Paling Sederhana)

Menjalankan seluruh proses FL (server + 2 client) dalam **satu proses Python**, tanpa jaringan.

```bash
python main.py
```

**Yang terjadi:**

- Data sintetis di-generate ke `data/`
- 10 round FedAvg dijalankan secara berurutan
- Akurasi global dicetak di akhir setiap round

**Konfigurasi** dapat diubah langsung di blok `CONFIG` pada [main.py](main.py):

```python
CONFIG = {
    "n_rounds":           10,   # jumlah round federasi
    "local_epochs":      500,   # epoch training lokal per round
    "learning_rate":    0.01,
    "batch_size":         32,
    "samples_per_client": 600,
    "n_test":            300,
}
```

---

## Mode 2 — API Lokal (FastAPI Single-Process)

Menjalankan FL melalui HTTP API tanpa Docker, cocok untuk testing endpoint.

```bash
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

Buka dokumentasi interaktif di browser: `http://127.0.0.1:8000/docs`

### Endpoint

| Method | Path           | Keterangan                    |
| ------ | -------------- | ----------------------------- |
| GET    | `/health`      | Cek service berjalan          |
| POST   | `/train`       | Jalankan training FL          |
| GET    | `/last-result` | Lihat hasil training terakhir |

### Contoh Trigger Training

```bash
# PowerShell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/train `
  -ContentType "application/json" `
  -Body '{"n_rounds": 5, "local_epochs": 3}'

# curl (Linux/macOS/WSL)
curl -X POST http://127.0.0.1:8000/train \
  -H "Content-Type: application/json" \
  -d '{"n_rounds": 5, "local_epochs": 3}'
```

---

## Mode 3 — Terdistribusi (Server + Client Terpisah)

Mensimulasikan skenario nyata di mana server dan setiap client berjalan sebagai **proses terpisah** dan berkomunikasi lewat HTTP.

### Langkah 1 — Generate data terlebih dahulu

```bash
python -c "from data_generator import generate_and_save; generate_and_save(600, 300)"
```

### Langkah 2 — Jalankan Server (terminal pertama)

```bash
uvicorn server_api:app --host 0.0.0.0 --port 8000
```

Variabel environment opsional:

| Variabel      | Default | Keterangan                            |
| ------------- | ------- | ------------------------------------- |
| `NUM_CLIENTS` | `2`     | Jumlah client yang ditunggu per round |
| `N_ROUNDS`    | `10`    | Total round FL                        |
| `INPUT_DIM`   | `10`    | Dimensi input fitur                   |

Contoh dengan env custom:

```bash
# Windows
$env:NUM_CLIENTS="2"; $env:N_ROUNDS="5"; uvicorn server_api:app --host 0.0.0.0 --port 8000

# Linux/macOS
NUM_CLIENTS=2 N_ROUNDS=5 uvicorn server_api:app --host 0.0.0.0 --port 8000
```

### Langkah 3 — Jalankan Client 1 (terminal kedua)

```bash
# Windows
$env:CLIENT_ID="1"; $env:DATA_PATH="data/client1_data.csv"; $env:SERVER_URL="http://localhost:8000"; python client_worker.py

# Linux/macOS
CLIENT_ID=1 DATA_PATH=data/client1_data.csv SERVER_URL=http://localhost:8000 python client_worker.py
```

### Langkah 4 — Jalankan Client 2 (terminal ketiga)

```bash
# Windows
$env:CLIENT_ID="2"; $env:DATA_PATH="data/client2_data.csv"; $env:SERVER_URL="http://localhost:8000"; python client_worker.py

# Linux/macOS
CLIENT_ID=2 DATA_PATH=data/client2_data.csv SERVER_URL=http://localhost:8000 python client_worker.py
```

Server akan otomatis memulai aggregasi FedAvg setelah semua `NUM_CLIENTS` client mengirim update di setiap round.

---

## Mode 4 — Docker Compose

### 4a. Server saja

```bash
docker compose -f docker-compose.server.yml up -d --build
```

### 4b. Server + Monitoring (Prometheus + Grafana)

```bash
docker compose -f docker-compose.monitoring.yml up -d --build
```

| Service    | URL                   |
| ---------- | --------------------- |
| FL API     | http://localhost:8000 |
| Prometheus | http://localhost:9090 |
| Grafana    | http://localhost:3000 |

### 4c. Menjalankan Client via Docker (dalam jaringan yang sama)

Setiap client memiliki file Compose tersendiri. Jalankan di terminal terpisah setelah server berjalan:

```powershell
# Client 1 (terminal kedua)
docker compose -f docker-compose.client1.yml up --build

# Client 2 (terminal ketiga)
docker compose -f docker-compose.client2.yml up --build
```

> Kedua client terhubung ke jaringan Docker internal `fl-sc_fl-monitoring-net` dan menjangkau server melalui nama service `fl-scam-api`.

### 4d. Menjalankan Client dari Luar Jaringan Docker (via URL Publik/Ngrok)

Gunakan file `docker-compose.client-external.yml` untuk client yang berada di **mesin berbeda** atau di luar jaringan Docker. File ini tidak terhubung ke jaringan internal Docker sehingga komunikasi dilakukan melalui koneksi host biasa.

```powershell
# Ganti SERVER_URL dengan URL publik server (ngrok, IP publik, dll.)
$env:CLIENT_ID="3"
$env:SERVER_URL="https://xxxx.ngrok-free.app"
$env:DATA_PATH="data/client1_data.csv"
docker compose -f docker-compose.client-external.yml up --build
```

| Variabel     | Wajib  | Keterangan                                             |
| ------------ | ------ | ------------------------------------------------------ |
| `CLIENT_ID`  | Ya     | ID unik client (default: `3`)                          |
| `SERVER_URL` | **Ya** | URL eksternal server FL (ngrok, IP publik, dll.)       |
| `DATA_PATH`  | Ya     | Path file CSV data lokal (default: `client1_data.csv`) |

### Menghentikan semua container

```powershell
docker compose -f docker-compose.monitoring.yml down
docker compose -f docker-compose.client1.yml down
docker compose -f docker-compose.client2.yml down
docker compose -f docker-compose.client-external.yml down
```

---

## Akses dari Jaringan LAN

Jika server berjalan di PC dengan IP `192.168.1.10`:

1. Pastikan firewall mengizinkan inbound TCP port `8000`
2. Client di perangkat lain gunakan `SERVER_URL=http://192.168.1.10:8000`
3. Cek kesehatan server: `http://192.168.1.10:8000/health`

---

## Mode 5 — Client dari Luar Jaringan Lokal via Ngrok

Skenario ini digunakan ketika **FL Server** ada di satu mesin/jaringan, sementara **FL Client** berada di jaringan yang berbeda (misalnya beda kampus, beda kota, atau via internet). Ngrok membuat tunnel terenkripsi sehingga client bisa mengirim update bobot ke server tanpa VPN.

```
┌─────────────────────────────────────────────────────────────┐
│                          Internet                           │
│                                                             │
│  Client A (jaringan lain) ──▶ https://xxxx.ngrok-free.app  │
│  Client B (jaringan lain) ──▶ https://xxxx.ngrok-free.app  │
└────────────────────────────┬────────────────────────────────┘
                             │  Ngrok Tunnel (TLS)
              ┌──────────────▼──────────────┐
              │       Mesin Server Lokal    │
              │                             │
              │  ngrok ──▶ localhost:8000   │
              │        (server_api.py)      │
              └─────────────────────────────┘
```

### Langkah 1 — Instalasi Ngrok di mesin Server

```powershell
winget install ngrok.ngrok
```

Daftar akun gratis di [dashboard.ngrok.com](https://dashboard.ngrok.com), lalu konfigurasikan authtoken:

```powershell
ngrok config add-authtoken <TOKEN_ANDA>
```

### Langkah 2 — Generate data dan jalankan FL Server

**Terminal 1** — Generate data:

```powershell
python -c "from data_generator import generate_and_save; generate_and_save(600, 300)"
```

**Terminal 2** — Jalankan FL Server:

```powershell
uvicorn server_api:app --host 0.0.0.0 --port 8000
```

### Langkah 3 — Buka tunnel Ngrok ke port 8000

**Terminal 3** — Buka tunnel:

```powershell
ngrok http 8000
```

Catat URL dari baris `Forwarding`, contoh:

```
Forwarding    https://abcd-123-45-67-89.ngrok-free.app -> http://localhost:8000
```

**Verifikasi server bisa diakses dari internet:**

```powershell
curl https://abcd-123-45-67-89.ngrok-free.app/health `
     -H "ngrok-skip-browser-warning: true"
```

Respons yang benar: `{"status":"ok"}`

### Langkah 4 — Jalankan Client di mesin lain (jaringan berbeda)

Pastikan `requirements.txt` sudah terinstall di mesin client. Tidak perlu Docker atau ngrok di sisi client.

**Client 1:**

```powershell
# Windows
$env:CLIENT_ID="1"
$env:SERVER_URL="https://abcd-123-45-67-89.ngrok-free.app"
$env:DATA_PATH="data/client1_data.csv"
python client_worker.py
```

```bash
# Linux/macOS
CLIENT_ID=1 SERVER_URL=https://abcd-123-45-67-89.ngrok-free.app \
  DATA_PATH=data/client1_data.csv python client_worker.py
```

**Client 2 (dari mesin/jaringan lain):**

```powershell
# Windows
$env:CLIENT_ID="2"
$env:SERVER_URL="https://abcd-123-45-67-89.ngrok-free.app"
$env:DATA_PATH="data/client2_data.csv"
python client_worker.py
```

```bash
# Linux/macOS
CLIENT_ID=2 SERVER_URL=https://abcd-123-45-67-89.ngrok-free.app \
  DATA_PATH=data/client2_data.csv python client_worker.py
```

> Ganti `https://abcd-123-45-67-89.ngrok-free.app` dengan URL aktual dari output ngrok Anda. URL berubah setiap kali ngrok di-restart (akun gratis).

### Alur Kerja FL via Ngrok

```
Client                         Ngrok Tunnel                    Server
  │                                │                              │
  │── GET /global-model ──────────▶│──────────────────────────▶  │
  │◀─ {round, weights} ───────────│◀──────────────────────────── │
  │                                │                              │
  │  (training lokal dengan        │                              │
  │   data lokal — data TIDAK      │                              │
  │   keluar dari client)          │                              │
  │                                │                              │
  │── POST /submit-update ────────▶│──────────────────────────▶  │
  │   {weights, n_samples, loss}   │                   (FedAvg)   │
  │◀─ {aggregated} ───────────────│◀──────────────────────────── │
  │                                │                              │
  │  (ulangi sampai semua round    │                              │
  │   selesai)                     │                              │
```

### Catatan Penting

| Hal                     | Keterangan                                                                    |
| ----------------------- | ----------------------------------------------------------------------------- |
| **Data tetap lokal**    | Client hanya mengirim bobot model (`/submit-update`), bukan data training     |
| **URL berubah**         | Akun gratis: URL ngrok berubah tiap restart — beri tahu semua client URL baru |
| **1 tunnel aktif**      | Akun gratis hanya mendukung 1 tunnel sekaligus                                |
| **Batas waktu**         | Session akun gratis maksimal 2 jam; jalankan ulang ngrok jika terputus        |
| **Jangan commit token** | Tambahkan `ngrok.yml` ke `.gitignore`                                         |

### Menambahkan Proteksi Basic Auth (Opsional)

Agar tidak sembarang orang bisa mengirim update ke server, tambahkan autentikasi di `ngrok.yml`:

```yaml
version: "3"
authtoken: <TOKEN_ANDA>

tunnels:
  fl-server:
    proto: http
    addr: 8000
    basic_auth:
      - "fl_client:password_rahasia"
```

Jalankan tunnel dengan nama:

```powershell
ngrok start fl-server
```

Client kemudian perlu memodifikasi `client_worker.py` untuk menyertakan header `Authorization` di setiap request ke server, atau gunakan URL dengan kredensial:

```
SERVER_URL=https://fl_client:password_rahasia@abcd-xxx.ngrok-free.app
```

> Panduan lengkap ngrok tersedia di [panduan-ngrok.md](panduan-ngrok.md).

---

## Ringkasan Perbandingan Mode

| Mode                                   | Proses    | Jaringan        | Cocok untuk                   |
| -------------------------------------- | --------- | --------------- | ----------------------------- |
| `python main.py`                       | 1         | Tidak ada       | Demo cepat, debugging         |
| `uvicorn api:app`                      | 1         | HTTP lokal      | Testing API endpoint          |
| `server_api` + `client_worker`         | 3+        | HTTP lokal/LAN  | Simulasi terdistribusi nyata  |
| Docker Compose (client1/client2)       | Container | Docker bridge   | Demo production, monitoring   |
| Docker Compose (client-external)       | Container | Internet publik | Client di mesin/jaringan lain |
| `server_api` + Ngrok + `client_worker` | 3+        | Internet publik | Client lintas jaringan/lokasi |
