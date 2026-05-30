# Panduan Server — FL-SISTER Federated Learning

Dokumen ini menjelaskan cara menyiapkan dan menjalankan sisi **server** pada proyek FL-SISTER. Fokus utama panduan ini adalah:

1. Membuat **global weight** awal.
2. Menjalankan **server federated learning**.
3. Menyediakan endpoint agar client dapat mengambil model global dan mengirim update lokal.

Server berperan sebagai pusat koordinasi federated learning. Server tidak menerima data mentah dari client. Server hanya menerima bobot model hasil training lokal, jumlah sampel client, nilai loss, dan metadata round. Setelah semua client mengirim update, server melakukan agregasi menggunakan pendekatan **FedAvg**.

---

## 1. Peran Server dalam Sistem

Server memiliki beberapa fungsi utama:

```text id="8ruoap"
1. Membuat model global awal
2. Menyediakan model global ke client
3. Menerima update bobot model dari client
4. Menunggu update dari seluruh client sesuai NUM_CLIENTS
5. Melakukan agregasi FedAvg
6. Memperbarui bobot global untuk round berikutnya
7. Menyediakan metrik untuk Prometheus dan Grafana
```

Alur kerja server:

```text id="cseuv6"
Server membuat global weight awal
        ↓
Client mengambil global model melalui /global-model
        ↓
Client melakukan training lokal
        ↓
Client mengirim update ke /submit-update
        ↓
Server mengumpulkan update client
        ↓
Jika jumlah update sudah sesuai NUM_CLIENTS
        ↓
Server melakukan agregasi FedAvg
        ↓
Global weight diperbarui
        ↓
Round berikutnya dimulai
```

---

# Bagian 1 — Membuat Global Weight

## 2. Konsep Global Weight

**Global weight** adalah bobot awal model yang disimpan di server dan dikirimkan ke semua client sebelum proses training lokal dimulai. Pada federated learning, semua client harus memulai dari bobot global yang sama agar hasil update dapat diagregasi secara konsisten.

Pada proyek ini, global weight dapat dibuat melalui dua pendekatan:

```text id="7mj8kh"
1. Inisialisasi otomatis dari arsitektur model
2. Pre-training awal menggunakan dataset server
```

Pendekatan pertama membuat bobot model secara acak sesuai arsitektur neural network. Pendekatan kedua melatih model global terlebih dahulu menggunakan dataset awal, misalnya `data/test_data.csv`, lalu menyimpan checkpoint ke folder `checkpoints`.

---

## 3. Dataset untuk Membuat Global Weight

Secara default, server menggunakan file:

```text id="0f98lq"
data/test_data.csv
```

Dataset ini digunakan untuk proses pre-training awal pada server. File tersebut harus memiliki struktur fitur yang sama dengan dataset client dan wajib memiliki kolom target:

```text id="f8e2t5"
label
```

Contoh struktur kolom:

```text id="9800t9"
msg_length,num_links,has_phone_num,money_mention,urgency_words,all_caps_ratio,exclamation_count,suspicious_keywords,sender_known,reply_requested,label
```

Jumlah fitur input default adalah:

```text id="v8v5ng"
INPUT_DIM=10
```

Jika jumlah fitur pada dataset berubah, nilai `INPUT_DIM` juga harus disesuaikan.

---

## 4. Membuat Data Awal

Jika file dataset belum tersedia, jalankan generator data:

```bash id="9yz9dy"
python data_generator.py
```

Atau gunakan fungsi generator secara langsung:

```bash id="cu74dq"
python -c "from data_generator import generate_and_save; generate_and_save(600, 300)"
```

Setelah perintah dijalankan, folder `data` akan berisi:

```text id="bpxuhb"
data/
├── client1_data.csv
├── client2_data.csv
└── test_data.csv
```

File `test_data.csv` digunakan server untuk membuat global weight awal melalui pre-training.

---

## 5. Membuat Global Weight Otomatis Saat Server Startup

Pada proyek ini, pembuatan global weight dilakukan otomatis ketika `server_api.py` dijalankan. Server akan mengecek dua kondisi:

```text id="9cqa6x"
1. PRETRAIN_EPOCHS lebih dari 0
2. File PRETRAIN_DATA_PATH tersedia
```

Jika kedua kondisi terpenuhi, server akan:

```text id="itq10l"
1. Membaca dataset dari PRETRAIN_DATA_PATH
2. Memisahkan fitur dan label
3. Melakukan standardisasi fitur dengan StandardScaler
4. Melakukan pre-training model global
5. Menyimpan bobot awal ke checkpoints/global_init.pt
```

Contoh konfigurasi default:

```text id="bzj7zb"
PRETRAIN_EPOCHS=50
PRETRAIN_DATA_PATH=data/test_data.csv
INPUT_DIM=10
```

---

## 6. Menjalankan Pre-training Global Weight di Windows PowerShell

Gunakan perintah berikut:

```powershell id="0tzv9z"
$env:NUM_CLIENTS="2"
$env:N_ROUNDS="10"
$env:INPUT_DIM="10"
$env:PRETRAIN_EPOCHS="50"
$env:PRETRAIN_DATA_PATH="data/test_data.csv"

uvicorn server_api:app --host 0.0.0.0 --port 8000
```

Jika berhasil, output server akan menampilkan proses seperti:

```text id="80evfg"
[Server] Loading pre-training data from: data/test_data.csv
[Server] Pre-training global model (50 epochs, 300 samples)...
[Server] Pre-training done loss 0.xxxx → 0.xxxx
[Server] Initial checkpoint saved: checkpoints/global_init.pt
```

File hasil global weight awal:

```text id="y1bxli"
checkpoints/global_init.pt
```

---

## 7. Menjalankan Pre-training Global Weight di Linux / macOS

```bash id="b05j7f"
export NUM_CLIENTS=2
export N_ROUNDS=10
export INPUT_DIM=10
export PRETRAIN_EPOCHS=50
export PRETRAIN_DATA_PATH=data/test_data.csv

uvicorn server_api:app --host 0.0.0.0 --port 8000
```

Atau dalam satu baris:

```bash id="wzje5u"
NUM_CLIENTS=2 N_ROUNDS=10 INPUT_DIM=10 PRETRAIN_EPOCHS=50 PRETRAIN_DATA_PATH=data/test_data.csv uvicorn server_api:app --host 0.0.0.0 --port 8000
```

---

## 8. Menjalankan Server Tanpa Pre-training

Jika ingin server langsung memakai bobot awal random dari arsitektur model, matikan pre-training dengan:

```text id="6l5rc4"
PRETRAIN_EPOCHS=0
```

### Windows PowerShell

```powershell id="1jizcf"
$env:NUM_CLIENTS="2"
$env:N_ROUNDS="10"
$env:INPUT_DIM="10"
$env:PRETRAIN_EPOCHS="0"

uvicorn server_api:app --host 0.0.0.0 --port 8000
```

### Linux / macOS

```bash id="lpcqkp"
NUM_CLIENTS=2 N_ROUNDS=10 INPUT_DIM=10 PRETRAIN_EPOCHS=0 uvicorn server_api:app --host 0.0.0.0 --port 8000
```

Mode ini tetap valid untuk simulasi federated learning, tetapi performa awal model biasanya lebih rendah karena server belum memiliki bobot awal yang terlatih.

---

# Bagian 2 — Menjalankan Server

## 9. Instalasi Dependency Server

Buat virtual environment:

### Windows PowerShell

```powershell id="55lold"
python -m venv .venv
.venv\Scripts\activate
```

### Linux / macOS

```bash id="x5efuj"
python3 -m venv .venv
source .venv/bin/activate
```

Install dependency:

```bash id="z7ee1o"
pip install -r requirements.txt
```

Dependency server membutuhkan library untuk FastAPI, Uvicorn, PyTorch, Pandas, Scikit-learn, dan Prometheus metrics.

---

## 10. Konfigurasi Environment Server

Environment variable penting:

| Variable             |              Default | Fungsi                                                     |
| -------------------- | -------------------: | ---------------------------------------------------------- |
| `NUM_CLIENTS`        |                  `2` | Jumlah client yang harus mengirim update pada setiap round |
| `N_ROUNDS`           |                 `10` | Jumlah total round federated learning                      |
| `INPUT_DIM`          |                 `10` | Jumlah fitur input model                                   |
| `PRETRAIN_EPOCHS`    |                 `50` | Jumlah epoch pre-training global weight                    |
| `PRETRAIN_DATA_PATH` | `data/test_data.csv` | Lokasi dataset pre-training server                         |

Konfigurasi minimal untuk dua client:

```text id="zw3ejv"
NUM_CLIENTS=2
N_ROUNDS=10
INPUT_DIM=10
PRETRAIN_EPOCHS=50
PRETRAIN_DATA_PATH=data/test_data.csv
```

Jika jumlah client dinaikkan menjadi 3, maka server harus dijalankan dengan:

```text id="35chn1"
NUM_CLIENTS=3
```

Server akan menunggu 3 update client pada setiap round sebelum melakukan agregasi.

---

## 11. Menjalankan Server Tanpa Docker

### Windows PowerShell

```powershell id="pq8y2k"
$env:NUM_CLIENTS="2"
$env:N_ROUNDS="10"
$env:INPUT_DIM="10"
$env:PRETRAIN_EPOCHS="50"
$env:PRETRAIN_DATA_PATH="data/test_data.csv"

uvicorn server_api:app --host 0.0.0.0 --port 8000
```

### Linux / macOS

```bash id="quew6e"
NUM_CLIENTS=2 N_ROUNDS=10 INPUT_DIM=10 PRETRAIN_EPOCHS=50 PRETRAIN_DATA_PATH=data/test_data.csv uvicorn server_api:app --host 0.0.0.0 --port 8000
```

Server akan berjalan pada:

```text id="8wdya4"
http://localhost:8000
```

Karena menggunakan `--host 0.0.0.0`, server juga dapat diakses dari perangkat lain dalam jaringan yang sama melalui IP laptop server.

---

## 12. Validasi Server Berjalan

Buka browser atau gunakan curl:

```bash id="ck39bx"
curl http://localhost:8000/
```

Contoh respons:

```json id="mbxozl"
{
  "message": "FL Server is running",
  "num_clients": 2,
  "n_rounds": 10,
  "current_completed_round": 0
}
```

Cek status training:

```bash id="3efk18"
curl http://localhost:8000/status
```

Contoh respons awal:

```json id="180qku"
{
  "completed": false,
  "completed_round": 0,
  "next_round": 1,
  "expected_clients": 2,
  "collected_updates": 0
}
```

Cek model global yang akan diambil client:

```bash id="4i731k"
curl http://localhost:8000/global-model
```

Endpoint ini mengembalikan nomor round berikutnya dan bobot global dalam format payload JSON.

---

## 13. Endpoint Server

| Method | Endpoint         | Fungsi                                           |
| ------ | ---------------- | ------------------------------------------------ |
| `GET`  | `/`              | Mengecek server aktif dan konfigurasi dasar      |
| `GET`  | `/status`        | Melihat status round dan jumlah update terkumpul |
| `GET`  | `/global-model`  | Mengirim bobot global ke client                  |
| `POST` | `/submit-update` | Menerima update bobot dari client                |
| `GET`  | `/metrics`       | Menyediakan metrik untuk Prometheus              |

Endpoint `/global-model` digunakan client untuk mengambil bobot global. Endpoint `/submit-update` digunakan client untuk mengirim bobot hasil training lokal.

---

## 14. Format Update dari Client

Client mengirim update ke server dalam format:

```json id="6asqlu"
{
  "client_id": "1",
  "round": 1,
  "n_samples": 600,
  "weights": {},
  "loss": 0.4321
}
```

Penjelasan field:

| Field       | Fungsi                                        |
| ----------- | --------------------------------------------- |
| `client_id` | Identitas client                              |
| `round`     | Round federated learning yang sedang diproses |
| `n_samples` | Jumlah data lokal pada client                 |
| `weights`   | Bobot model hasil training lokal              |
| `loss`      | Nilai loss lokal client                       |

Server menyimpan update berdasarkan round. Jika jumlah update pada round tersebut sudah mencapai `NUM_CLIENTS`, server langsung melakukan agregasi FedAvg.

---

## 15. Menjalankan Server dengan Docker Compose

Jika ingin menjalankan server bersama Prometheus dan Grafana:

```bash id="toh6wp"
docker compose -f docker-compose.monitoring.yml up -d --build
```

Service yang aktif:

```text id="2vs04e"
FL API      : http://localhost:8000
Prometheus : http://localhost:9090
Grafana    : http://localhost:3000
```

Login Grafana default:

```text id="nux92i"
Username: admin
Password: admin
```

Untuk melihat log server:

```bash id="33pljk"
docker logs -f fl-scam-api
```

Untuk menghentikan service:

```bash id="vk5sfl"
docker compose -f docker-compose.monitoring.yml down
```

---

## 16. Menjalankan Server Agar Diakses Client dari Laptop Lain

Cari IP laptop server.

### Windows

```powershell id="g8aawl"
ipconfig
```

Misalnya IP server:

```text id="t0d6be"
192.168.1.10
```

Client lain menggunakan:

```text id="t0p4u5"
SERVER_URL=http://192.168.1.10:8000
```

Pastikan firewall mengizinkan inbound TCP port:

```text id="h6i5sq"
8000
```

Cek dari laptop client:

```bash id="c5eqwf"
curl http://192.168.1.10:8000/
```

Jika respons server muncul, client sudah dapat mengirim update.

---

## 17. Menjalankan Server Melalui Ngrok

Jika client berada di jaringan berbeda, jalankan server lokal terlebih dahulu:

```powershell id="0y8cq4"
uvicorn server_api:app --host 0.0.0.0 --port 8000
```

Lalu jalankan Ngrok:

```bash id="i3qmei"
ngrok http 8000
```

Ngrok akan memberikan URL publik, misalnya:

```text id="tc4kit"
https://abc123.ngrok-free.app
```

Client menggunakan URL tersebut:

```text id="jmbc0m"
SERVER_URL=https://abc123.ngrok-free.app
```

Pada skenario ini, Ngrok hanya dijalankan di sisi server. Client cukup mengarah ke URL publik server.

---

## 18. Monitoring Server

Server menyediakan metrik melalui endpoint:

```text id="6wi3et"
http://localhost:8000/metrics
```

Metrik penting:

| Metrik                   | Fungsi                                              |
| ------------------------ | --------------------------------------------------- |
| `fl_client_update_total` | Menghitung total update dari setiap client          |
| `fl_client_loss`         | Menampilkan loss terakhir setiap client             |
| `fl_collected_updates`   | Jumlah update yang sudah terkumpul pada round aktif |
| `fl_completed_round`     | Round federated learning yang sudah selesai         |

Metrik ini dapat dibaca oleh Prometheus dan divisualisasikan di Grafana.

---

## 19. Masalah Umum pada Server

### Global weight tidak tersimpan

Gejala:

```text id="4675ql"
checkpoints/global_init.pt tidak muncul
```

Kemungkinan penyebab:

```text id="mu5ldr"
1. PRETRAIN_EPOCHS=0
2. File PRETRAIN_DATA_PATH tidak ditemukan
3. Dataset tidak memiliki kolom label
4. Folder checkpoints tidak memiliki izin tulis
```

Solusi:

```bash id="kgk8zb"
python data_generator.py
```

Lalu jalankan ulang server dengan:

```powershell id="1qclyh"
$env:PRETRAIN_EPOCHS="50"
$env:PRETRAIN_DATA_PATH="data/test_data.csv"
uvicorn server_api:app --host 0.0.0.0 --port 8000
```

---

### Server terus menunggu update client

Gejala:

```json id="6df2lh"
{
  "expected_clients": 2,
  "collected_updates": 1
}
```

Penyebab:

```text id="8zz2ul"
Server diset NUM_CLIENTS=2, tetapi baru satu client yang mengirim update.
```

Solusi:

```text id="i3w0yc"
Jalankan semua client sesuai jumlah NUM_CLIENTS.
Pastikan setiap client memiliki CLIENT_ID berbeda.
```

---

### Client tidak dapat terhubung ke server

Kemungkinan penyebab:

```text id="q4gjn0"
1. Server belum berjalan
2. SERVER_URL pada client salah
3. Firewall menutup port 8000
4. Client berada di jaringan berbeda tanpa Ngrok/VPN
```

Solusi:

```bash id="kr1tzx"
curl http://localhost:8000/
```

Jika dari laptop lain:

```bash id="u0h3r2"
curl http://IP_SERVER:8000/
```

---

## 20. Ringkasan Perintah Utama

Generate data:

```bash id="coj2af"
python data_generator.py
```

Jalankan server dengan pre-training:

```powershell id="tso8bn"
$env:NUM_CLIENTS="2"
$env:N_ROUNDS="10"
$env:INPUT_DIM="10"
$env:PRETRAIN_EPOCHS="50"
$env:PRETRAIN_DATA_PATH="data/test_data.csv"
uvicorn server_api:app --host 0.0.0.0 --port 8000
```

Jalankan server tanpa pre-training:

```powershell id="p4jguz"
$env:NUM_CLIENTS="2"
$env:N_ROUNDS="10"
$env:INPUT_DIM="10"
$env:PRETRAIN_EPOCHS="0"
uvicorn server_api:app --host 0.0.0.0 --port 8000
```

Jalankan server + monitoring:

```bash id="rukd7i"
docker compose -f docker-compose.monitoring.yml up -d --build
```

Cek status server:

```bash id="5sawm8"
curl http://localhost:8000/status
```

Cek global model:

```bash id="blzskd"
curl http://localhost:8000/global-model
```

Cek metrik monitoring:

```bash id="3tjmlr"
curl http://localhost:8000/metrics
```

---

## 21. Kesimpulan

Server FL-SISTER berfungsi sebagai pusat koordinasi federated learning. Server membuat global weight awal, mengirimkannya ke client, menerima update lokal dari setiap client, lalu melakukan agregasi FedAvg setelah jumlah update sesuai dengan `NUM_CLIENTS`.

Agar server berjalan stabil, pastikan tiga hal utama:

```text id="sdhvse"
1. Dataset pre-training tersedia jika ingin membuat global weight awal.
2. NUM_CLIENTS sesuai dengan jumlah client yang benar-benar aktif.
3. Port 8000 dapat diakses oleh seluruh client.
```

Jika server dijalankan bersama Prometheus dan Grafana, proses federated learning dapat dipantau melalui metrik client update, loss per client, jumlah update terkumpul, dan round yang sudah selesai.
