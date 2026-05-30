# Panduan Client — FL-SISTER Federated Learning

Dokumen ini menjelaskan cara menjalankan sisi **client** pada proyek FL-SISTER. Fokus utama panduan ini adalah pembuatan data lokal client dan proses pengiriman update model ke server federated learning.

Client bertugas melakukan training lokal menggunakan data masing-masing. Data mentah tidak dikirim ke server. Client hanya mengirim parameter atau bobot model hasil training lokal beserta informasi pendukung seperti `client_id`, `round`, `n_samples`, dan `loss`.

---

## 1. Peran Client dalam Sistem

Dalam arsitektur federated learning, client adalah node yang menyimpan data lokal dan melakukan proses pelatihan model secara mandiri. Server hanya mengatur distribusi model global, menerima update dari client, lalu melakukan agregasi menggunakan pendekatan FedAvg.

Alur kerja client:

```text
Client mengambil model global dari server
        ↓
Client melakukan training lokal
        ↓
Client menghitung loss dan update bobot model
        ↓
Client mengirim update ke server
        ↓
Server menunggu update dari seluruh client
        ↓
Server melakukan agregasi FedAvg
```

Dengan mekanisme ini, data lokal tetap berada di sisi client. Hal ini sesuai dengan prinsip utama federated learning, yaitu pelatihan model dilakukan secara terdistribusi tanpa memusatkan data mentah ke server.

---

## 2. Prasyarat Client

Sebelum menjalankan client, pastikan perangkat client sudah memiliki:

```text
Python 3.9 atau versi lebih baru
Git
Koneksi ke server federated learning
File dataset lokal client
```

Clone repository:

```bash
git clone -b "dev/-Grafana+Prometheus" https://github.com/julian34/FL-SISTER.git
cd FL-SISTER
```

Buat virtual environment:

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

Install dependency:

```bash
pip install -r requirements.txt
```

---

# Bagian 1 — Generator Data Client

## 3. Fungsi Generator Data

File `data_generator.py` digunakan untuk membuat dataset sintetis untuk simulasi deteksi scam. Dataset dibuat dalam bentuk non-IID, artinya distribusi data antar-client tidak sama.

Secara default, generator membuat tiga file:

```text
data/client1_data.csv
data/client2_data.csv
data/test_data.csv
```

Penjelasan file:

| File               | Fungsi                                           |
| ------------------ | ------------------------------------------------ |
| `client1_data.csv` | Data lokal untuk Client 1                        |
| `client2_data.csv` | Data lokal untuk Client 2                        |
| `test_data.csv`    | Data uji global untuk evaluasi server            |
| `label`            | Kolom target klasifikasi, wajib ada pada dataset |

Client 1 dan Client 2 memiliki karakteristik data yang berbeda. Client 1 merepresentasikan pola pesan pendek seperti SMS, sedangkan Client 2 merepresentasikan pola pesan lebih panjang seperti email. Perbedaan distribusi ini digunakan untuk mensimulasikan kondisi federated learning yang lebih realistis.

---

## 4. Menjalankan Generator Data

Jalankan perintah berikut dari root project:

```bash
python data_generator.py
```

Jika berhasil, akan terbentuk folder dan file berikut:

```text
data/
├── client1_data.csv
├── client2_data.csv
└── test_data.csv
```

Untuk memastikan file sudah terbentuk:

### Windows PowerShell

```powershell
dir data
```

### Linux / macOS

```bash
ls data
```

---

## 5. Validasi Dataset Client

Setiap file dataset client harus memiliki kolom fitur dan kolom target `label`.

Contoh struktur dataset:

```text
msg_length,num_links,has_phone_num,money_mention,urgency_words,all_caps_ratio,exclamation_count,suspicious_keywords,sender_known,reply_requested,label
```

Kolom `label` wajib ada karena digunakan sebagai target klasifikasi. Jika kolom `label` tidak tersedia, proses client akan berhenti dan menampilkan error.

Validasi cepat menggunakan Python:

```bash
python -c "import pandas as pd; df=pd.read_csv('data/client1_data.csv'); print(df.head()); print(df.columns)"
```

Untuk Client 2:

```bash
python -c "import pandas as pd; df=pd.read_csv('data/client2_data.csv'); print(df.head()); print(df.columns)"
```

---

## 6. Pembagian Dataset ke Client

Untuk simulasi dua client:

```text
Client 1 menggunakan data/client1_data.csv
Client 2 menggunakan data/client2_data.csv
```

Jika client dijalankan di laptop berbeda, host dapat mengirim file dataset sesuai identitas client. Contoh:

```text
Laptop Client 1 → client1_data.csv
Laptop Client 2 → client2_data.csv
```

Pada skenario federated learning, setiap client sebaiknya hanya memegang data miliknya sendiri.

---

# Bagian 2 — Pengiriman Update ke Server

## 7. Pastikan Server Sudah Aktif

Sebelum client dijalankan, server federated learning harus sudah aktif.

Cek koneksi ke server:

```bash
curl http://localhost:8000/health
```

Jika server berada di laptop lain, gunakan IP server:

```bash
curl http://192.168.1.10:8000/health
```

Jika server menggunakan Ngrok:

```bash
curl https://alamat-ngrok-anda.ngrok-free.app/health
```

Client tidak harus menjalankan Docker. Client cukup menjalankan Python lokal selama dapat mengakses alamat server.

---

## 8. Konfigurasi Environment Variable Client

Client membaca konfigurasi dari environment variable berikut:

| Variable        | Fungsi                              | Contoh                  |
| --------------- | ----------------------------------- | ----------------------- |
| `CLIENT_ID`     | Identitas unik client               | `1`                     |
| `SERVER_URL`    | Alamat server federated learning    | `http://localhost:8000` |
| `DATA_PATH`     | Lokasi file dataset lokal           | `data/client1_data.csv` |
| `LOCAL_EPOCHS`  | Jumlah epoch training lokal         | `5`                     |
| `BATCH_SIZE`    | Ukuran batch training               | `32`                    |
| `LEARNING_RATE` | Nilai learning rate                 | `0.01`                  |
| `POLL_SECONDS`  | Interval client mengecek round baru | `5`                     |

Konfigurasi paling penting adalah:

```text
CLIENT_ID
SERVER_URL
DATA_PATH
```

Setiap client wajib memiliki `CLIENT_ID` yang berbeda.

---

## 9. Menjalankan Client 1

### Windows PowerShell

```powershell
$env:CLIENT_ID="1"
$env:SERVER_URL="http://localhost:8000"
$env:DATA_PATH="data/client1_data.csv"
$env:LOCAL_EPOCHS="5"
$env:BATCH_SIZE="32"
$env:LEARNING_RATE="0.01"
python client_worker.py
```

### Linux / macOS

```bash
export CLIENT_ID=1
export SERVER_URL=http://localhost:8000
export DATA_PATH=data/client1_data.csv
export LOCAL_EPOCHS=5
export BATCH_SIZE=32
export LEARNING_RATE=0.01
python client_worker.py
```

---

## 10. Menjalankan Client 2

### Windows PowerShell

```powershell
$env:CLIENT_ID="2"
$env:SERVER_URL="http://localhost:8000"
$env:DATA_PATH="data/client2_data.csv"
$env:LOCAL_EPOCHS="5"
$env:BATCH_SIZE="32"
$env:LEARNING_RATE="0.01"
python client_worker.py
```

### Linux / macOS

```bash
export CLIENT_ID=2
export SERVER_URL=http://localhost:8000
export DATA_PATH=data/client2_data.csv
export LOCAL_EPOCHS=5
export BATCH_SIZE=32
export LEARNING_RATE=0.01
python client_worker.py
```

---

## 11. Menjalankan Client dari Laptop Berbeda

Jika server berjalan di laptop utama dengan IP:

```text
192.168.1.10
```

Maka client di laptop lain menggunakan:

```powershell
$env:CLIENT_ID="1"
$env:SERVER_URL="http://192.168.1.10:8000"
$env:DATA_PATH="data/client1_data.csv"
python client_worker.py
```

Pastikan firewall laptop server mengizinkan akses ke port `8000`.

---

## 12. Menjalankan Client Menggunakan Ngrok

Jika server diekspos menggunakan Ngrok, contoh URL server:

```text
https://abc123.ngrok-free.app
```

Maka client menggunakan:

```powershell
$env:CLIENT_ID="1"
$env:SERVER_URL="https://abc123.ngrok-free.app"
$env:DATA_PATH="data/client1_data.csv"
python client_worker.py
```

Untuk Client 2:

```powershell
$env:CLIENT_ID="2"
$env:SERVER_URL="https://abc123.ngrok-free.app"
$env:DATA_PATH="data/client2_data.csv"
python client_worker.py
```

Client tidak perlu menjalankan Ngrok. Ngrok cukup dijalankan pada sisi server.

---

## 13. Proses Teknis Pengiriman ke Server

Saat `client_worker.py` berjalan, proses yang dilakukan adalah:

```text
1. Client membaca dataset lokal dari DATA_PATH
2. Client melakukan normalisasi lokal menggunakan StandardScaler
3. Client meminta model global dari SERVER_URL/global-model
4. Client menerima bobot model global
5. Client melakukan training lokal
6. Client menghitung loss
7. Client membuat payload update
8. Client mengirim update ke SERVER_URL/submit-update
9. Client menunggu round berikutnya
```

Payload yang dikirim client ke server berisi:

```json
{
  "client_id": "1",
  "round": 1,
  "n_samples": 600,
  "weights": {},
  "loss": 0.4123
}
```

Keterangan:

| Field       | Fungsi                            |
| ----------- | --------------------------------- |
| `client_id` | Identitas client pengirim         |
| `round`     | Nomor round federated learning    |
| `n_samples` | Jumlah data lokal client          |
| `weights`   | Bobot model hasil training lokal  |
| `loss`      | Nilai loss setelah training lokal |

Data mentah seperti isi CSV tidak dikirim ke server.

---

## 14. Contoh Output Client

Jika client berhasil terhubung ke server, output akan terlihat seperti berikut:

```text
[Client 1] Loading local data: data/client1_data.csv
[Client 1] Connected to server: http://localhost:8000
[Client 1] Local samples: 600
[Client 1] Starting local training for round 1
[Client 1] Round 1 submitted | loss=0.4532 | server={'status': 'waiting'}
```

Jika seluruh client sudah mengirim update, server akan melakukan agregasi dan client masuk ke round berikutnya.

---

## 15. Masalah Umum

### Server belum aktif

Gejala:

```text
Server belum siap / koneksi gagal
```

Solusi:

```text
Pastikan server sudah berjalan.
Pastikan SERVER_URL benar.
Pastikan port 8000 bisa diakses.
```

---

### Dataset tidak ditemukan

Gejala:

```text
FileNotFoundError: data/client1_data.csv
```

Solusi:

```bash
python data_generator.py
```

Lalu cek ulang:

```bash
ls data
```

atau pada Windows:

```powershell
dir data
```

---

### Kolom label tidak ada

Gejala:

```text
Dataset harus memiliki kolom 'label'.
```

Solusi:

```text
Pastikan file CSV memiliki kolom label.
Jangan menghapus kolom label dari dataset client.
Gunakan data hasil generator jika masih dalam tahap simulasi.
```

---

### Round tidak selesai

Penyebab umum:

```text
Jumlah client yang aktif lebih sedikit dari NUM_CLIENTS pada server.
```

Contoh:

```text
Server diset NUM_CLIENTS=2
Tetapi hanya Client 1 yang berjalan
Maka server akan terus menunggu update dari Client 2
```

Solusi:

```text
Jalankan semua client sesuai konfigurasi NUM_CLIENTS.
Pastikan setiap client memakai CLIENT_ID berbeda.
```

---

## 16. Ringkasan Perintah Utama

Generate data:

```bash
python data_generator.py
```

Jalankan Client 1:

```powershell
$env:CLIENT_ID="1"
$env:SERVER_URL="http://localhost:8000"
$env:DATA_PATH="data/client1_data.csv"
python client_worker.py
```

Jalankan Client 2:

```powershell
$env:CLIENT_ID="2"
$env:SERVER_URL="http://localhost:8000"
$env:DATA_PATH="data/client2_data.csv"
python client_worker.py
```

Jika memakai Ngrok:

```powershell
$env:SERVER_URL="https://alamat-ngrok-anda.ngrok-free.app"
```

---

## 17. Kesimpulan

Client pada FL-SISTER dapat berjalan tanpa Docker. Client hanya membutuhkan Python, dependency project, dataset lokal, dan alamat server federated learning. Generator data digunakan untuk membuat dataset lokal client, sedangkan `client_worker.py` digunakan untuk mengambil model global, melakukan training lokal, dan mengirim update model ke server.

Prinsip utama yang harus dijaga adalah setiap client memiliki data lokal sendiri, `CLIENT_ID` berbeda, dan `SERVER_URL` mengarah ke server yang aktif.
