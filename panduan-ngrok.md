# Panduan Konfigurasi Ngrok

**Federated Learning for Scam Detection — Akses Publik via Tunnel**

---

## Daftar Isi

1. [Pendahuluan](#1-pendahuluan)
2. [Prasyarat](#2-prasyarat)
3. [Instalasi Ngrok di Windows](#3-instalasi-ngrok-di-windows)
4. [Daftar Akun & Setup Authtoken](#4-daftar-akun--setup-authtoken)
5. [Tunnel untuk API Lokal — `api.py` (Port 8000)](#5-tunnel-untuk-api-lokal--apipy-port-8000)
6. [Membaca Output Terminal Ngrok](#6-membaca-output-terminal-ngrok)
7. [Menggunakan URL Publik](#7-menggunakan-url-publik)
8. [Konfigurasi `ngrok.yml`](#8-konfigurasi-ngrokyml)
9. [Tunnel untuk FL Server — `server_api.py` (Port 8001)](#9-tunnel-untuk-fl-server--server_apipy-port-8001)
10. [Ngrok Web Inspector (localhost:4040)](#10-ngrok-web-inspector-localhost4040)
11. [Troubleshooting](#11-troubleshooting)
12. [Catatan Keamanan](#12-catatan-keamanan)

---

## 1. Pendahuluan

Ngrok adalah tool yang membuat **tunnel terenkripsi** antara internet publik dan server yang berjalan di mesin lokal. Dalam project FL-Sc ini, ngrok berguna untuk:

- Mengekspos `api.py` (port 8000) ke internet agar client atau penguji bisa memanggil endpoint `/train` dari luar jaringan lokal.
- Mengekspos `server_api.py` (port 8001) ke internet agar **FL Client** yang berjalan di mesin berbeda bisa berkomunikasi dengan FL Server tanpa perlu berada di jaringan yang sama.

```
┌──────────────────────────────────────────────────────────────┐
│                         Internet                             │
│                                                              │
│   Client / Penguji ──▶  https://xxxx.ngrok-free.app         │
└──────────────────────────────────┬───────────────────────────┘
                                   │  Ngrok Tunnel (TLS)
                    ┌──────────────▼──────────────┐
                    │      Mesin Lokal (Windows)   │
                    │                              │
                    │   ngrok ──▶ localhost:8000   │
                    │              (api.py)        │
                    └──────────────────────────────┘
```

> **Akun gratis sudah cukup** untuk keperluan development dan demo. Batasan utama akun gratis: 1 tunnel aktif, URL berubah setiap restart, session maksimum 2 jam.

---

## 2. Prasyarat

Sebelum menggunakan ngrok, pastikan kondisi berikut terpenuhi:

| Item | Cara Cek |
|------|----------|
| Virtual environment aktif | Prompt terminal diawali `(.venv)` |
| API server bisa berjalan lokal | `curl http://localhost:8000/health` mengembalikan `{"status":"ok"}` |
| Koneksi internet aktif | — |
| Akun ngrok sudah dibuat | [dashboard.ngrok.com](https://dashboard.ngrok.com) |

---

## 3. Instalasi Ngrok di Windows

### Opsi A — Winget (Direkomendasikan)

Buka PowerShell sebagai biasa (tidak perlu Administrator):

```powershell
winget install ngrok.ngrok
```

Verifikasi instalasi:

```powershell
ngrok version
```

Output yang diharapkan:
```
ngrok version 3.x.x
```

---

### Opsi B — Download Manual

1. Buka [https://ngrok.com/download](https://ngrok.com/download) dan unduh file ZIP untuk Windows (64-bit).
2. Extract file `ngrok.exe` ke folder, misalnya `C:\Tools\ngrok\`.
3. Tambahkan folder tersebut ke PATH:

```powershell
# Tambah ke PATH sesi saat ini (sementara)
$env:PATH += ";C:\Tools\ngrok"

# Tambah ke PATH permanen (User)
[Environment]::SetEnvironmentVariable(
    "PATH",
    [Environment]::GetEnvironmentVariable("PATH", "User") + ";C:\Tools\ngrok",
    "User"
)
```

4. Tutup dan buka ulang terminal, lalu verifikasi:

```powershell
ngrok version
```

---

## 4. Daftar Akun & Setup Authtoken

Ngrok v3 **wajib** menggunakan authtoken. Tanpa authtoken, tunnel tidak akan bisa dibuka.

### Langkah 1 — Daftar akun gratis

Buka [https://dashboard.ngrok.com/signup](https://dashboard.ngrok.com/signup) dan daftar menggunakan email atau akun GitHub/Google.

### Langkah 2 — Salin Authtoken

Setelah login, buka menu **Your Authtoken** di dashboard, atau langsung ke:
[https://dashboard.ngrok.com/get-started/your-authtoken](https://dashboard.ngrok.com/get-started/your-authtoken)

Salin token yang ditampilkan (format: `2xxx...xxxxxxxxxxx_xxxxxxxxxxxxxxxxxxxxxxxxxx`).

### Langkah 3 — Konfigurasi token di mesin lokal

```powershell
ngrok config add-authtoken <TOKEN_ANDA_DI_SINI>
```

Contoh:
```powershell
ngrok config add-authtoken 2abc123defghijklmnopqrstuvwxyz_ABCDEFGHIJKLMNOPQRSTUVWXYZ123
```

Output sukses:
```
Authtoken saved to configuration file: C:\Users\jardm\AppData\Local/ngrok/ngrok.yml
```

> Token disimpan di file `ngrok.yml` lokal — **jangan commit file ini ke repository**.

---

## 5. Tunnel untuk API Lokal — `api.py` (Port 8000)

### Langkah 1 — Jalankan API server (Terminal 1)

Pastikan virtual environment aktif, lalu jalankan server:

```powershell
uvicorn api:app --host 0.0.0.0 --port 8000
```

Biarkan terminal ini tetap berjalan.

### Langkah 2 — Buka tunnel ngrok (Terminal 2)

Buka terminal baru, aktifkan venv jika perlu, lalu:

```powershell
ngrok http 8000
```

### Langkah 3 — Salin URL publik dari output

Lihat bagian [Membaca Output Terminal Ngrok](#6-membaca-output-terminal-ngrok) untuk penjelasan output.

---

## 6. Membaca Output Terminal Ngrok

Setelah menjalankan `ngrok http 8000`, output akan terlihat seperti ini:

```
ngrok                                                           (Ctrl+C to quit)

Session Status                online
Account                       nama@email.com (Plan: Free)
Update                        update available (version 3.x.x, Ctrl-U to update)
Version                       3.x.x
Region                        Asia Pacific (ap)
Latency                       45ms
Web Interface                 http://127.0.0.1:4040
Forwarding                    https://abcd-123-45-67-89.ngrok-free.app -> http://localhost:8000

Connections                   ttl     opn     rt1     rt5     p50     p90
                              0       0       0.00    0.00    0.00    0.00
```

| Baris | Penjelasan |
|-------|-----------|
| `Session Status` | `online` berarti tunnel aktif dan bisa digunakan |
| `Account` | Email akun ngrok yang digunakan |
| `Region` | Lokasi server ngrok terdekat (otomatis dipilih, atau bisa dikonfigurasi) |
| `Latency` | Round-trip time ke server ngrok — indikasi kecepatan tunnel |
| `Web Interface` | Alamat lokal untuk membuka Ngrok Web Inspector di browser |
| `Forwarding` | **URL publik** yang diteruskan ke `localhost:8000` — ini yang dibagikan |
| `Connections` | Statistik request yang masuk melalui tunnel |

> **Catat URL Forwarding** — URL tersebut berubah setiap kali ngrok di-restart (pada akun gratis).

---

## 7. Menggunakan URL Publik

Ganti `https://abcd-123-45-67-89.ngrok-free.app` dengan URL aktual dari output ngrok Anda.

### Cek status server

```powershell
curl https://abcd-123-45-67-89.ngrok-free.app/health
```

Respons:
```json
{"status": "ok"}
```

### Trigger federated training

```powershell
curl -X POST https://abcd-123-45-67-89.ngrok-free.app/train `
     -H "Content-Type: application/json" `
     -d '{"n_rounds": 5, "local_epochs": 3}'
```

Respons:
```json
{
  "message": "training completed",
  "config": { "n_rounds": 5, "local_epochs": 3, ... },
  "final": { "accuracy": 0.94, ... },
  "best": { "round": 4, ... },
  "rounds": 5
}
```

### Lihat hasil training terakhir

```powershell
curl https://abcd-123-45-67-89.ngrok-free.app/last-result
```

### Akses dokumentasi API (Swagger UI)

Buka di browser:
```
https://abcd-123-45-67-89.ngrok-free.app/docs
```

> **Catatan:** Browser mungkin menampilkan halaman peringatan ngrok saat pertama kali membuka URL. Klik **"Visit Site"** untuk melanjutkan.

---

## 8. Konfigurasi `ngrok.yml`

File konfigurasi ngrok berada di:

```
C:\Users\jardm\AppData\Local\ngrok\ngrok.yml
```

Untuk membukanya langsung:

```powershell
notepad "$env:LOCALAPPDATA\ngrok\ngrok.yml"
```

### Contoh konfigurasi dasar

```yaml
version: "3"
authtoken: <TOKEN_ANDA>

tunnels:
  fl-api:
    proto: http
    addr: 8000
    inspect: true

  fl-server:
    proto: http
    addr: 8001
    inspect: true
```

Jalankan semua tunnel sekaligus dengan:

```powershell
ngrok start --all
```

### Konfigurasi lengkap dengan region dan Basic Auth

```yaml
version: "3"
authtoken: <TOKEN_ANDA>

region: ap   # ap = Asia Pacific, us = US, eu = Europe

tunnels:
  fl-api:
    proto: http
    addr: 8000
    inspect: true
    # Proteksi endpoint dengan username:password
    basic_auth:
      - "admin:password_rahasia"

  fl-server:
    proto: http
    addr: 8001
    inspect: true
    basic_auth:
      - "fl_client:password_client"
```

> Setelah menambahkan `basic_auth`, setiap request ke URL publik wajib menyertakan header Authorization. Lihat [Catatan Keamanan](#12-catatan-keamanan) untuk detail penggunaannya.

### Jalankan tunnel spesifik berdasarkan nama

```powershell
# Hanya tunnel fl-api
ngrok start fl-api

# Hanya tunnel fl-server
ngrok start fl-server

# Semua tunnel sekaligus
ngrok start --all
```

---

## 9. Tunnel untuk FL Server — `server_api.py` (Port 8001)

Skenario ini digunakan ketika **FL Server** berjalan di satu mesin, dan **FL Client** berjalan di mesin yang berbeda (berbeda jaringan/lokasi).

### Di mesin Server

**Terminal 1** — Jalankan FL Server:

```powershell
uvicorn server_api:app --host 0.0.0.0 --port 8001
```

**Terminal 2** — Buka tunnel ke port 8001:

```powershell
ngrok http 8001
```

Catat URL forwarding, misalnya:
```
https://efgh-456-78-90-12.ngrok-free.app -> http://localhost:8001
```

### Di mesin Client

FL Client perlu mengetahui URL server. Sesuaikan variabel lingkungan atau konfigurasi client untuk mengarah ke URL ngrok server:

```powershell
# Set environment variable sebelum menjalankan client
$env:FL_SERVER_URL = "https://efgh-456-78-90-12.ngrok-free.app"
python client_worker.py
```

### Cek status FL Server via URL publik

```powershell
curl https://efgh-456-78-90-12.ngrok-free.app/status
```

Respons:
```json
{
  "completed": false,
  "current_round": 2,
  ...
}
```

---

## 10. Ngrok Web Inspector (`localhost:4040`)

Selama tunnel aktif, ngrok menyediakan antarmuka web lokal untuk memonitor dan men-debug semua request yang masuk.

### Cara membuka

Buka browser dan navigasi ke:
```
http://localhost:4040
```

### Fitur Web Inspector

| Fitur | Kegunaan |
|-------|----------|
| **Requests** | Daftar semua HTTP request yang masuk melalui tunnel beserta timestamp |
| **Request Detail** | Lihat header, body request, dan response secara lengkap |
| **Replay** | Kirim ulang request yang sama tanpa perlu mengulangi dari client |
| **Status** | Informasi tunnel aktif dan statistik koneksi |

### Contoh penggunaan Replay

1. Buka `http://localhost:4040` di browser
2. Klik salah satu request di daftar (misalnya `POST /train`)
3. Klik tombol **Replay** untuk mengirim ulang request yang sama ke server lokal
4. Berguna untuk menguji perubahan kode tanpa harus memanggil API dari luar

---

## 11. Troubleshooting

### Tunnel tidak bisa dibuka: `authtoken not configured`

```
ERROR:  authtoken not configured, run: ngrok config add-authtoken <token>
```

**Solusi:**
```powershell
ngrok config add-authtoken <TOKEN_DARI_DASHBOARD>
```

---

### Session expired / tunnel terputus otomatis

Akun gratis membatasi durasi session. Jika tunnel terputus:

```
Session Expired: The ngrok session expired. Restart ngrok or upgrade your account.
```

**Solusi:** Jalankan ulang ngrok. URL publik akan berubah.

```powershell
ngrok http 8000
```

---

### Error `ERR_NGROK_108`: Too many connections

```
ERR_NGROK_108: Your account is limited to X simultaneous ngrok agent sessions.
```

**Solusi:** Akun gratis hanya mendukung 1 tunnel aktif. Tutup terminal ngrok lain yang mungkin masih berjalan, lalu coba lagi.

---

### Error `429 Too Many Requests`

Akun gratis membatasi jumlah request per menit. Jika terlalu banyak request masuk:

**Solusi jangka pendek:** Tunggu beberapa saat sebelum mencoba lagi.  
**Solusi jangka panjang:** Upgrade ke akun berbayar atau gunakan ngrok hanya saat diperlukan.

---

### Port sudah digunakan: `bind: address already in use`

```
ERROR: bind: address already in use (:8000)
```

**Solusi:** Cari proses yang menggunakan port tersebut dan matikan:

```powershell
# Cari proses di port 8000
netstat -ano | Select-String ":8000"

# Matikan proses berdasarkan PID (ganti 12345 dengan PID aktual)
Stop-Process -Id 12345 -Force
```

---

### Browser menampilkan halaman peringatan ngrok

Ngrok menampilkan halaman interstitial saat URL pertama kali dibuka di browser. Ini normal.

**Solusi untuk akses API (non-browser):** Tambahkan header berikut ke request:

```powershell
curl https://abcd-xxx.ngrok-free.app/health `
     -H "ngrok-skip-browser-warning: true"
```

---

### API mengembalikan HTML ngrok, bukan JSON

Tanda bahwa request browser memicu halaman peringatan ngrok.

**Solusi:** Selalu sertakan header `ngrok-skip-browser-warning: true` pada request curl atau HTTP client:

```powershell
curl -X POST https://abcd-xxx.ngrok-free.app/train `
     -H "Content-Type: application/json" `
     -H "ngrok-skip-browser-warning: true" `
     -d '{"n_rounds": 3}'
```

---

## 12. Catatan Keamanan

> Ngrok memberikan akses **publik ke server lokal**. Perhatikan hal-hal berikut:

### Jangan share URL ngrok sembarangan

URL ngrok yang aktif memberi akses penuh ke endpoint API Anda — termasuk `/train` yang menjalankan proses komputasi berat. Bagikan hanya kepada orang yang berwenang.

### Gunakan Basic Auth untuk melindungi endpoint

Tambahkan `basic_auth` di `ngrok.yml` (lihat [Bagian 8](#8-konfigurasi-ngrokyml)) agar hanya user dengan kredensial yang bisa mengakses. Contoh penggunaan dengan curl:

```powershell
curl -X POST https://abcd-xxx.ngrok-free.app/train `
     -u "admin:password_rahasia" `
     -H "Content-Type: application/json" `
     -d '{"n_rounds": 5}'
```

### Hentikan tunnel jika tidak digunakan

Tekan `Ctrl+C` di terminal ngrok jika sudah selesai menggunakannya. Jangan biarkan tunnel berjalan tanpa pengawasan.

### Jangan commit authtoken atau ngrok.yml ke repository

File `ngrok.yml` berisi authtoken yang bersifat rahasia. Tambahkan ke `.gitignore`:

```powershell
Add-Content .gitignore "`nngrok.yml"
```

---

## Referensi Cepat

| Perintah | Fungsi |
|----------|--------|
| `ngrok version` | Cek versi ngrok |
| `ngrok config add-authtoken <TOKEN>` | Simpan authtoken |
| `ngrok http 8000` | Buka tunnel ke port 8000 |
| `ngrok http 8001` | Buka tunnel ke port 8001 (FL Server) |
| `ngrok start --all` | Jalankan semua tunnel di `ngrok.yml` |
| `ngrok start fl-api` | Jalankan tunnel bernama `fl-api` dari `ngrok.yml` |
| `Ctrl+C` | Hentikan tunnel |

| URL | Fungsi |
|-----|--------|
| `http://localhost:4040` | Ngrok Web Inspector (debug request) |
| `https://dashboard.ngrok.com` | Dashboard akun ngrok |
| `https://dashboard.ngrok.com/get-started/your-authtoken` | Salin authtoken |
