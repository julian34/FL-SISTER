# FL-Sc — Federated Learning for Scam Detection

> Simulasi **Federated Learning** berbasis **FedAvg** untuk klasifikasi pesan scam menggunakan **1 Global Server** dan **2 Client** — dijalankan dengan Python, FastAPI, PyTorch, Docker, dan Ngrok.

**Sumber asli:** [https://github.com/3k0sakti/FL-Sc](https://github.com/3k0sakti/FL-Sc)

---

## Daftar Isi

1. [Gambaran Umum](#1-gambaran-umum)
2. [Technology Stack](#2-technology-stack)
3. [Arsitektur Sistem](#3-arsitektur-sistem)
4. [Struktur Proyek](#4-struktur-proyek)
5. [Dokumentasi Lengkap](#5-dokumentasi-lengkap)
6. [Quickstart](#6-quickstart)
7. [Endpoint API](#7-endpoint-api)
8. [Lisensi & Atribusi](#8-lisensi--atribusi)

---

## 1. Gambaran Umum

**FL-Sc** adalah implementasi simulasi Federated Learning untuk mendeteksi pesan scam. Model neural network dilatih secara terdistribusi pada setiap client menggunakan data lokal masing-masing. Server hanya menerima bobot model hasil training — **data mentah tidak pernah meninggalkan client**.

Konsep inti:

```
Data tetap di client  →  Client training lokal  →  Kirim bobot ke server
Server agregasi (FedAvg)  →  Model global diperbarui  →  Round berikutnya
```

---

## 2. Technology Stack

| Komponen             | Teknologi                   | Fungsi                                 |
| -------------------- | --------------------------- | -------------------------------------- |
| Programming Language | Python                      | Implementasi model, server, dan client |
| API Framework        | FastAPI                     | Menyediakan endpoint FL server         |
| ML Framework         | PyTorch                     | Pelatihan model neural network         |
| Data Processing      | Pandas, NumPy, Scikit-learn | Preprocessing dan normalisasi data     |
| Containerization     | Docker, Docker Compose      | Menjalankan service secara terisolasi  |
| Monitoring           | Prometheus                  | Mengambil dan menyimpan metrik         |
| Dashboard            | Grafana                     | Visualisasi metrik                     |
| Public Access        | Ngrok                       | Membuka akses server lokal ke internet |

---

## 3. Arsitektur Sistem

```
┌─────────────┐        weights        ┌──────────────────┐
│  Client 1   │ ─────────────────────▶│                  │
│ (SMS-like)  │ ◀─────────────────────│  Global Server   │
└─────────────┘   global model        │  (FedAvg)        │
                                      │                  │
┌─────────────┐        weights        │                  │
│  Client 2   │ ─────────────────────▶│                  │
│(Email-like) │ ◀─────────────────────└──────────────────┘
└─────────────┘   global model
```

> **Privacy guarantee:** data mentah tidak pernah meninggalkan client — hanya bobot model yang dikirim ke server.

---

## 4. Struktur Proyek

```
FL-Sc/
├── model.py                    # ScamDetector neural network (PyTorch)
├── data_generator.py           # Pembuat dataset sintetis non-IID
├── fl_client.py                # FederatedClient — training lokal
├── fl_server.py                # FederatedServer — FedAvg aggregation
├── main.py                     # Orkestrator simulasi FL
├── api.py                      # FastAPI server endpoint
├── server_api.py               # Logika server untuk API
├── fl_runner.py                # Runner FL via API
├── client_worker.py            # Worker proses client
├── model_io.py                 # Utilitas simpan/muat model
├── requirements.txt
├── Dockerfile
├── docker-compose.server.yml   # Compose untuk server FL
├── docker-compose.client.yml   # Compose untuk client FL
├── docker-compose.monitoring.yml # Compose untuk Prometheus & Grafana
├── monitoring/
│   └── prometheus.yml          # Konfigurasi scraping Prometheus
└── data/                       # Di-generate otomatis saat run
    ├── client1_data.csv
    ├── client2_data.csv
    └── test_data.csv
```

---

## 5. Dokumentasi Lengkap

Panduan lengkap tersedia dalam file berikut:

| Dokumen                                    | Deskripsi                                                                         |
| ------------------------------------------ | --------------------------------------------------------------------------------- |
| [CARA_MENJALANKAN.md](CARA_MENJALANKAN.md) | Semua mode menjalankan proyek: CLI, API lokal, Docker, dan multi-node             |
| [PANDUAN_MANUAL.md](PANDUAN_MANUAL.md)     | Panduan langkah demi langkah secara manual dengan penjelasan detail tiap perintah |
| [panduan-ngrok.md](panduan-ngrok.md)       | Konfigurasi Ngrok untuk membuka akses server lokal ke internet (multi-machine FL) |

> Untuk menjalankan proyek pertama kali, disarankan membaca **[CARA_MENJALANKAN.md](CARA_MENJALANKAN.md)** terlebih dahulu.

---

## 6. Quickstart

### Prasyarat

- Python 3.9+
- (Opsional) Docker & Docker Compose
- (Opsional) Ngrok untuk akses publik

### Instalasi

```bash
git clone https://github.com/julian34/FL-SISTER.git
cd FL-Sc

python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux / macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

### Jalankan Simulasi (CLI)

```bash
python main.py
```

### Jalankan sebagai API

```bash
uvicorn api:app --host 0.0.0.0 --port 8000
```

### Jalankan dengan Docker

```bash
docker compose -f docker-compose.server.yml up -d --build
```

Untuk panduan mode lain (multi-node, monitoring, ngrok), lihat [CARA_MENJALANKAN.md](CARA_MENJALANKAN.md).

---

## 7. Endpoint API

| Method | Endpoint       | Deskripsi                     |
| ------ | -------------- | ----------------------------- |
| GET    | `/health`      | Cek status service            |
| POST   | `/train`       | Jalankan federated training   |
| GET    | `/last-result` | Lihat hasil training terakhir |

Contoh trigger training:

```bash
curl -X POST http://127.0.0.1:8000/train \
    -H "Content-Type: application/json" \
    -d '{"n_rounds": 5, "local_epochs": 3}'
```

---

## 8. Lisensi & Atribusi

Proyek ini dikembangkan berdasarkan repo asli:

> **FL-Sc** oleh [3k0sakti](https://github.com/3k0sakti)  
> [https://github.com/3k0sakti/FL-Sc](https://github.com/3k0sakti/FL-Sc)

Langkah cek cepat:

1. Cari IP lokal host (contoh `192.168.1.10`).
2. Pastikan firewall Windows mengizinkan inbound TCP port `8000`.
3. Akses dari perangkat lain: `http://192.168.1.10:8000/health`.

## Algoritma: FedAvg

Setiap **round** mengikuti 4 langkah:

1. Server broadcast bobot global ke semua client
2. Setiap client melatih model di data lokal selama `local_epochs` epoch
3. Client mengirim bobot yang sudah diupdate ke server
4. Server menghitung rata-rata tertimbang:

$$w_{global} = \sum_{k=1}^{K} \frac{n_k}{N} \cdot w_k$$

di mana $n_k$ = jumlah sampel client $k$, $N$ = total sampel seluruh client.

## Model

Feed-forward neural network binary classifier:

```
Input(10) → Linear(64) → ReLU → Dropout(0.3) → Linear(32) → ReLU → Linear(1) → Sigmoid
```

**Loss:** Binary Cross-Entropy | **Optimizer:** Adam

## Dataset (Sintetis, Non-IID)

| Feature               | Deskripsi                             |
| --------------------- | ------------------------------------- |
| `msg_length`          | Panjang karakter pesan                |
| `num_links`           | Jumlah URL dalam pesan                |
| `has_phone_num`       | Mengandung nomor telepon (0/1)        |
| `money_mention`       | Menyebut uang/hadiah/reward (0/1)     |
| `urgency_words`       | Jumlah kata urgensi ("act now", dst.) |
| `all_caps_ratio`      | Proporsi huruf kapital                |
| `exclamation_count`   | Jumlah tanda seru                     |
| `suspicious_keywords` | Jumlah kata mencurigakan              |
| `sender_known`        | Pengirim ada di kontak (0/1)          |
| `reply_requested`     | Meminta balasan/klik (0/1)            |

**Split Non-IID:**

- **Client 1** — distribusi SMS: pesan pendek, banyak nomor telepon, sedikit link
- **Client 2** — distribusi Email: pesan panjang, banyak link, sedikit nomor telepon

Label noise ~8% ditambahkan untuk membuat tugas lebih realistis.

## Konfigurasi

Edit konstanta `CONFIG` di `main.py`:

```python
CONFIG = {
    "n_rounds":           10,   # jumlah round federasi
    "local_epochs":        5,   # epoch training lokal per round
    "learning_rate":    0.01,
    "batch_size":         32,
    "samples_per_client": 600,
    "n_test":            300,
}
```

## Contoh Output

```
  Round   Accuracy  Progress
  ─────  ─────────  ────────────────────────────────
      1     0.8933  ███████████████████████████░░░
      2     0.8867  ███████████████████████████░░░
     ...
     10     0.8733  ██████████████████████████░░░░

  FINAL GLOBAL MODEL
  Accuracy  : 0.8733
  Precision : 0.9027
  Recall    : 0.7907
  F1 Score  : 0.8430
```

## Referensi

- McMahan et al., _Communication-Efficient Learning of Deep Networks from Decentralized Data_ (2017) — makalah asli FedAvg
