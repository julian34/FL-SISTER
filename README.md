# Federated Learning for Scam Detection

Hands-on simulasi **Federated Learning** (FedAvg) untuk klasifikasi pesan scam dengan **1 Global Server** dan **2 Client** — semua berjalan dalam satu proses Python tanpa framework FL eksternal.

## Arsitektur

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

## Struktur Proyek

```
fl-scam/
├── model.py            # ScamDetector neural network
├── data_generator.py   # Pembuat data sintetis, split non-IID ke 2 client
├── fl_client.py        # FederatedClient — training lokal + kirim bobot
├── fl_server.py        # FederatedServer — FedAvg aggregation
├── main.py             # Orkestrator utama
├── requirements.txt
└── data/               # Di-generate otomatis saat run
    ├── client1_data.csv
    ├── client2_data.csv
    └── test_data.csv
```

## Instalasi

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Cara Menjalankan

```bash
python main.py
```

## Menjalankan Sebagai API (lokal)

Project ini sekarang juga menyediakan HTTP API dengan FastAPI.

```bash
uvicorn api:app --host 0.0.0.0 --port 8000
```

Endpoint utama:

- `GET /health` cek service hidup
- `POST /train` jalankan federated training
- `GET /last-result` lihat hasil training terakhir

Contoh trigger training:

```bash
curl -X POST http://127.0.0.1:8000/train \
    -H "Content-Type: application/json" \
    -d '{"n_rounds": 5, "local_epochs": 3}'
```

## Docker Container

Build image:

```bash
docker build -t fl-scam-api .
```

Jalankan container:

```bash
docker run -d --name fl-scam-api -p 8000:8000 fl-scam-api
```

Atau pakai docker compose:

```bash
docker compose up -d --build
```

## Akses dari Jaringan LAN

Karena service di-bind ke `0.0.0.0` dan port di-publish `8000:8000`, API bisa diakses dari perangkat lain dalam LAN:

```bash
http://IP_LOKAL_PC_ANDA:8000/health
```

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
