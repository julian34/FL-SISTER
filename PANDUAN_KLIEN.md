# Panduan Menjalankan Client FL

Dokumen ini menjelaskan cara menjalankan **FL Client** yang akan terhubung ke FL Server dan berpartisipasi dalam proses Federated Learning.

---

## Prasyarat

- Docker Desktop sudah terinstall dan berjalan
- **FL Server sudah berjalan terlebih dahulu** (lihat [PANDUAN_SERVER.md](PANDUAN_SERVER.md))
- Network Docker `fl-sc_fl-monitoring-net` sudah terbentuk (otomatis saat server dijalankan)

---

## Opsi 1 — Jalankan Client 1 & Client 2 (Terpisah)

Dua file Compose sudah disediakan untuk kemudahan:

```bash
# Terminal 1 — Client 1
docker compose -f docker-compose.client1.yml up --build

# Terminal 2 — Client 2
docker compose -f docker-compose.client2.yml up --build
```

Masing-masing client akan otomatis:

1. Memuat data lokal dari folder `data/`
2. Mengambil bobot model global dari server
3. Melatih model secara lokal
4. Mengirim update ke server
5. Mengulang proses sampai semua round selesai

---

## Opsi 2 — Jalankan Client dengan Variabel Kustom

Gunakan `docker-compose.client.yml` dengan menentukan `CLIENT_ID` dan `DATA_PATH` secara manual:

```powershell
# PowerShell — Client 1
$env:CLIENT_ID="1"; $env:DATA_PATH="data/client1_data.csv"
docker compose -f docker-compose.client.yml up --build

# PowerShell — Client 2
$env:CLIENT_ID="2"; $env:DATA_PATH="data/client2_data.csv"
docker compose -f docker-compose.client.yml up --build
```

```bash
# Linux/macOS — Client 1
CLIENT_ID=1 DATA_PATH=data/client1_data.csv docker compose -f docker-compose.client.yml up --build
```

---

## Konfigurasi Client

Variabel lingkungan client diatur di file Compose masing-masing (`docker-compose.client1.yml`, `docker-compose.client2.yml`):

| Variabel        | Default (client1)         | Keterangan                                       |
| --------------- | ------------------------- | ------------------------------------------------ |
| `CLIENT_ID`     | `1`                       | ID unik client (harus berbeda antar client)      |
| `SERVER_URL`    | `http://fl-scam-api:8000` | URL FL Server                                    |
| `DATA_PATH`     | `data/client1_data.csv`   | Path file data CSV lokal                         |
| `LOCAL_EPOCHS`  | `5`                       | Jumlah epoch training lokal per round            |
| `BATCH_SIZE`    | `32`                      | Ukuran batch training                            |
| `LEARNING_RATE` | `0.01`                    | Learning rate optimizer                          |
| `POLL_SECONDS`  | `5`                       | Interval (detik) polling server untuk round baru |

Contoh mengubah konfigurasi di `docker-compose.client1.yml`:

```yaml
services:
  fl-client1:
    environment:
      CLIENT_ID: "1"
      SERVER_URL: http://fl-scam-api:8000
      DATA_PATH: data/client1_data.csv
      LOCAL_EPOCHS: 10 # lebih banyak epoch lokal
      BATCH_SIZE: 64
      LEARNING_RATE: 0.005
      POLL_SECONDS: 3
```

---

## Format Data Client

File CSV harus memiliki kolom `label` sebagai target klasifikasi. Kolom lainnya dianggap sebagai fitur.

```
feature_1,feature_2,...,feature_10,label
0.12,0.45,...,0.33,0
1.02,0.87,...,0.91,1
...
```

- Normalisasi fitur dilakukan **secara lokal** di setiap client (tidak berbagi scaler antar client)
- Jumlah fitur harus sesuai dengan `INPUT_DIM` yang dikonfigurasi di server (default: `10`)

---

## Menghubungkan Client ke Server Eksternal

Jika server berjalan di mesin lain atau melalui ngrok, ubah `SERVER_URL`:

```yaml
# docker-compose.client1.yml
environment:
  SERVER_URL: http://<IP_SERVER>:8000
  # atau via ngrok:
  SERVER_URL: https://xxxx-xx-xx-xx-xx.ngrok-free.app
```

Lihat [panduan-ngrok.md](panduan-ngrok.md) untuk setup tunnel ngrok lebih lanjut.

---

## Melihat Log Client

```bash
# Client 1
docker logs -f fl_client_1

# Client 2
docker logs -f fl_client_2
```

Contoh output normal:

```
[Client 1] Loading local data: data/client1_data.csv
[Client 1] Connected to server: http://fl-scam-api:8000
[Client 1] Local samples: 600
[Client 1] Round 1 — training locally...
[Client 1] Round 1 — submitting update (loss: 0.4231)
[Client 1] Round 2 — training locally...
...
[Client 1] Training completed after round 10.
```

---

## Menghentikan Client

```bash
docker compose -f docker-compose.client1.yml down
docker compose -f docker-compose.client2.yml down
```
