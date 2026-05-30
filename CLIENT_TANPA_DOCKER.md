# Menjalankan Client FL-SISTER Tanpa Docker

Dokumen ini menjelaskan cara menjalankan **client Federated Learning (FL-SISTER)** tanpa Docker. Docker tetap dapat digunakan untuk menjalankan server, Prometheus, dan Grafana, sedangkan client dapat dijalankan langsung menggunakan Python di laptop masing-masing.

---

## 1. Gambaran Umum

Pada sistem FL-SISTER, client bertugas mengambil model global dari server, melakukan pelatihan lokal menggunakan dataset masing-masing, lalu mengirimkan update model kembali ke server.

Alur komunikasi:

```text
Client Python
    ↓
GET /global-model
    ↓
Training lokal
    ↓
POST /submit-update
    ↓
Server melakukan agregasi FedAvg
    ↓
Prometheus membaca /metrics
    ↓
Grafana menampilkan monitoring
```

Client **tidak wajib menggunakan Docker** karena file `client_worker.py` dapat dijalankan langsung menggunakan Python.

---

## 2. Kebutuhan Sistem

Pastikan perangkat client sudah memiliki:

```text
Python 3.10 atau lebih baru
pip
Git
Koneksi internet atau jaringan lokal ke server
Dataset client dalam format CSV
```

Jika menggunakan GPU lokal, pastikan PyTorch sudah sesuai dengan versi CUDA pada laptop.

---

## 3. Clone Repository

```bash
git clone https://github.com/julian34/FL-SISTER.git
cd FL-SISTER
git checkout "dev/-Grafana+Prometheus"
```

Jika branch memiliki karakter khusus dan perintah gagal, gunakan:

```bash
git branch -a
git checkout dev/-Grafana+Prometheus
```

---

## 4. Membuat Virtual Environment

### Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

## 5. Install Dependency

```bash
pip install -r requirements.txt
```

Jika instalasi PyTorch gagal, install PyTorch sesuai perangkat.

### CPU Only

```bash
pip install torch torchvision torchaudio
```

### CUDA

Cek versi CUDA terlebih dahulu:

```bash
nvidia-smi
```

Lalu install PyTorch sesuai versi CUDA dari dokumentasi resmi PyTorch.

Contoh untuk CUDA 12.1:

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

---

## 6. Menyiapkan Dataset Client

Setiap client membutuhkan file CSV masing-masing.

Contoh:

```text
data/client1_data.csv
data/client2_data.csv
data/client3_data.csv
```

Struktur dataset harus memiliki:

```text
fitur_1, fitur_2, fitur_3, ..., label
```

Kolom `label` wajib ada karena digunakan sebagai target klasifikasi.

Contoh sederhana:

```csv
feature_1,feature_2,feature_3,label
0.12,0.34,0.55,0
0.75,0.21,0.48,1
0.44,0.61,0.19,0
```

---

## 7. Menjalankan Server

Server dapat dijalankan dengan Docker atau tanpa Docker.

### Opsi A — Server Menggunakan Docker

```bash
docker compose -f docker-compose.monitoring.yml up -d --build
```

Setelah berjalan, server tersedia di:

```text
http://localhost:8000
```

Cek endpoint metrics:

```text
http://localhost:8000/metrics
```

### Opsi B — Server Tanpa Docker

```bash
uvicorn server_api:app --host 0.0.0.0 --port 8000
```

Jika ingin menentukan jumlah client:

### Windows PowerShell

```powershell
$env:NUM_CLIENTS="2"
$env:N_ROUNDS="10"
uvicorn server_api:app --host 0.0.0.0 --port 8000
```

### Linux / macOS

```bash
export NUM_CLIENTS=2
export N_ROUNDS=10
uvicorn server_api:app --host 0.0.0.0 --port 8000
```

---

## 8. Menjalankan Client Tanpa Docker

### Client 1 — Windows PowerShell

```powershell
$env:CLIENT_ID="1"
$env:SERVER_URL="http://localhost:8000"
$env:DATA_PATH="data/client1_data.csv"
python client_worker.py
```

### Client 2 — Windows PowerShell

Buka terminal PowerShell baru:

```powershell
$env:CLIENT_ID="2"
$env:SERVER_URL="http://localhost:8000"
$env:DATA_PATH="data/client2_data.csv"
python client_worker.py
```

### Client 1 — Linux / macOS

```bash
export CLIENT_ID=1
export SERVER_URL=http://localhost:8000
export DATA_PATH=data/client1_data.csv
python client_worker.py
```

### Client 2 — Linux / macOS

```bash
export CLIENT_ID=2
export SERVER_URL=http://localhost:8000
export DATA_PATH=data/client2_data.csv
python client_worker.py
```

---

## 9. Menjalankan Client dari Laptop Teman

Jika server berjalan di laptop utama dan client dijalankan dari laptop teman, gunakan IP laptop server.

Contoh IP server:

```text
192.168.1.10
```

Maka client menggunakan:

```powershell
$env:CLIENT_ID="1"
$env:SERVER_URL="http://192.168.1.10:8000"
$env:DATA_PATH="data/client1_data.csv"
python client_worker.py
```

Pastikan firewall laptop server mengizinkan akses ke port:

```text
8000
```

---

## 10. Menjalankan Client Menggunakan Ngrok

Jika client berada di jaringan berbeda, server dapat dibuka menggunakan Ngrok.

Di laptop server:

```bash
ngrok http 8000
```

Ngrok akan menghasilkan URL seperti:

```text
https://xxxx-xxxx-xxxx.ngrok-free.app
```

Client menggunakan URL tersebut:

```powershell
$env:CLIENT_ID="1"
$env:SERVER_URL="https://xxxx-xxxx-xxxx.ngrok-free.app"
$env:DATA_PATH="data/client1_data.csv"
python client_worker.py
```

Client tidak perlu menjalankan Ngrok. Ngrok hanya dijalankan pada laptop server.

---

## 11. Menambah Client Baru

Repo default menggunakan 2 client, tetapi dapat dikembangkan menjadi lebih banyak client.

### Ubah jumlah client pada server

Jika menggunakan Docker, ubah `NUM_CLIENTS` pada `docker-compose.monitoring.yml`:

```yaml
environment:
  NUM_CLIENTS: 3
```

Jika menjalankan server manual:

```powershell
$env:NUM_CLIENTS="3"
uvicorn server_api:app --host 0.0.0.0 --port 8000
```

### Tambahkan dataset baru

```text
data/client3_data.csv
```

### Jalankan client ke-3

```powershell
$env:CLIENT_ID="3"
$env:SERVER_URL="http://localhost:8000"
$env:DATA_PATH="data/client3_data.csv"
python client_worker.py
```

---

## 12. Hubungan Client dengan Grafana

Client tidak terhubung langsung ke Grafana.

Alurnya:

```text
Client mengirim update ke FastAPI Server
Server menyimpan metric di endpoint /metrics
Prometheus mengambil metric dari /metrics
Grafana membaca data dari Prometheus
```

Jadi, selama client berhasil mengirim update ke server, Grafana akan menampilkan aktivitas client.

Metric penting yang dapat dipantau:

```text
fl_client_update_total
fl_client_loss
fl_collected_updates
fl_completed_round
```

---

## 13. Validasi

### Cek server

```text
http://localhost:8000
```

### Cek metrics

```text
http://localhost:8000/metrics
```

### Cek Prometheus

```text
http://localhost:9090
```

Query Prometheus:

```promql
fl_completed_round
```

```promql
fl_collected_updates
```

```promql
fl_client_loss
```

```promql
sum by (client_id) (fl_client_update_total)
```

### Cek Grafana

```text
http://localhost:3000
```

Login default:

```text
Username: admin
Password: admin
```

---

## 14. Troubleshooting

### Client gagal connect ke server

Cek nilai `SERVER_URL`.

```powershell
echo $env:SERVER_URL
```

Pastikan server aktif:

```text
http://localhost:8000
```

Jika client dari laptop lain, gunakan IP server, bukan `localhost`.

---

### Dataset tidak ditemukan

Pastikan `DATA_PATH` benar.

```powershell
$env:DATA_PATH="data/client1_data.csv"
```

Cek file:

```powershell
dir data
```

---

### Kolom label tidak ada

Pastikan dataset memiliki kolom:

```text
label
```

Jika tidak ada, sesuaikan nama kolom target di dataset atau ubah kode pembacaan dataset pada `client_worker.py`.

---

### Server menunggu terus dan round tidak selesai

Cek nilai `NUM_CLIENTS`.

Jika server dikonfigurasi:

```text
NUM_CLIENTS=3
```

maka harus ada 3 client yang mengirim update. Jika hanya 2 client aktif, agregasi tidak akan berjalan.

---

### Grafana tidak menampilkan data

Pastikan:

```text
Server aktif
Client sudah mengirim update
Endpoint /metrics berisi data FL
Prometheus target berstatus UP
Grafana datasource mengarah ke Prometheus
```

Cek Prometheus target:

```text
http://localhost:9090/targets
```

---

## 15. Kesimpulan

Client FL-SISTER dapat dijalankan tanpa Docker karena proses training lokal dijalankan langsung melalui `client_worker.py`. Docker hanya diperlukan jika ingin mempermudah deployment server, Prometheus, dan Grafana.

Konfigurasi yang direkomendasikan untuk pengujian kolaboratif:

```text
Server utama    : FastAPI + Prometheus + Grafana
Client 1        : Python lokal
Client 2        : Python lokal
Client tambahan : Python lokal
Komunikasi      : HTTP melalui LAN atau Ngrok
```

Dengan konfigurasi ini, simulasi Federated Learning dapat dilakukan oleh beberapa perangkat tanpa harus mewajibkan setiap client menggunakan Docker.
