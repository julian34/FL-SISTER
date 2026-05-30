# Panduan Menjalankan Server FL

Dokumen ini menjelaskan cara menjalankan **FL Server** beserta layanan monitoring (Prometheus & Grafana) menggunakan Docker Compose.

---

## Prasyarat

- Docker Desktop sudah terinstall dan berjalan
- Port **8000**, **9090**, dan **3000** tidak sedang dipakai

---

## Menjalankan Server (Docker Compose)

Jalankan perintah berikut dari direktori root proyek:

```bash
docker compose -f docker-compose.monitoring.yml up -d --build
```

Perintah ini akan menjalankan tiga container sekaligus:

| Container       | Port   | Keterangan                     |
| --------------- | ------ | ------------------------------ |
| `fl-scam-api`   | `8000` | FL Server (FastAPI)            |
| `fl-prometheus` | `9090` | Prometheus (metrics scraping)  |
| `fl-grafana`    | `3000` | Grafana (monitoring dashboard) |

---

## Konfigurasi Server

Variabel lingkungan server diatur di `docker-compose.monitoring.yml`:

| Variabel             | Default              | Keterangan                                    |
| -------------------- | -------------------- | --------------------------------------------- |
| `NUM_CLIENTS`        | `2`                  | Jumlah client yang harus bergabung tiap round |
| `N_ROUNDS`           | `10`                 | Total round federated learning                |
| `INPUT_DIM`          | `10`                 | Dimensi input model                           |
| `PRETRAIN_EPOCHS`    | `50`                 | Epoch pre-training model global di server     |
| `PRETRAIN_DATA_PATH` | `data/test_data.csv` | Path data untuk pre-training                  |

Contoh mengubah konfigurasi di `docker-compose.monitoring.yml`:

```yaml
services:
  fl-scam-api:
    environment:
      NUM_CLIENTS: 3 # tunggu 3 client per round
      N_ROUNDS: 20 # jalankan 20 round
      INPUT_DIM: 10
      PRETRAIN_EPOCHS: 100
```

---

## Endpoint API Server

Dokumentasi interaktif tersedia di: `http://localhost:8000/docs`

| Method | Path             | Keterangan                                            |
| ------ | ---------------- | ----------------------------------------------------- |
| GET    | `/`              | Info server (status, round saat ini)                  |
| GET    | `/status`        | Status round aktif & jumlah update terkumpul          |
| GET    | `/global-model`  | Ambil bobot model global (dipakai oleh client)        |
| POST   | `/submit-update` | Client mengirim update bobot lokal ke server          |
| POST   | `/reset`         | Reset server ke awal (round 0, muat `global_init.pt`) |
| GET    | `/metrics`       | Metrics Prometheus                                    |

### Cek Status Server

```powershell
# PowerShell
Invoke-RestMethod -Uri http://localhost:8000/status

# curl
curl http://localhost:8000/status
```

### Reset Training

```powershell
# PowerShell
Invoke-RestMethod -Method Post -Uri http://localhost:8000/reset

# curl
curl -X POST http://localhost:8000/reset
```

---

## Monitoring

### Prometheus

Buka: `http://localhost:9090`

Metrics yang tersedia:

| Metric                   | Tipe    | Keterangan                               |
| ------------------------ | ------- | ---------------------------------------- |
| `fl_client_update_total` | Counter | Total update yang dikirim tiap client    |
| `fl_client_loss`         | Gauge   | Loss terakhir tiap client                |
| `fl_collected_updates`   | Gauge   | Jumlah update terkumpul pada round aktif |
| `fl_completed_round`     | Gauge   | Round yang sudah selesai di-aggregate    |

### Grafana

Buka: `http://localhost:3000`  
Login default: `admin` / `admin`

Dashboard **FL Sister** sudah di-provisioning secara otomatis dan langsung tersedia setelah container berjalan.

---

## Checkpoint Model

Server menyimpan checkpoint model secara otomatis ke folder `checkpoints/`:

| File                  | Keterangan                              |
| --------------------- | --------------------------------------- |
| `global_init.pt`      | Model setelah pre-training awal         |
| `global_round_<N>.pt` | Model global setelah round ke-N selesai |

---

## Menghentikan Server

```bash
docker compose -f docker-compose.monitoring.yml down
```

Untuk menghapus volume/data container juga:

```bash
docker compose -f docker-compose.monitoring.yml down -v
```

---

## Melihat Log Server

```bash
# Semua service
docker compose -f docker-compose.monitoring.yml logs -f

# Server saja
docker logs -f fl-scam-api
```
