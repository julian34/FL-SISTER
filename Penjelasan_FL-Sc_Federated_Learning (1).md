# Penjelasan Repo FL-Sc: Federated Learning untuk Deteksi Scam

**Repository:** <https://github.com/3k0sakti/FL-Sc>  
**Topik:** Federated Learning, FedAvg, Scam Detection, PyTorch  
**Target pembaca:** Pemula yang ingin memahami alur kerja kode dan konsep dasar Federated Learning

---

## 1. Gambaran Umum

Repo **FL-Sc** adalah proyek Python sederhana untuk mensimulasikan **Federated Learning** pada kasus **deteksi pesan scam**. Proyek ini menggunakan skenario sederhana yang terdiri dari:

- **1 Global Server**
- **2 Client**
- **Model Neural Network sederhana**
- **Algoritma FedAvg** untuk menggabungkan bobot model
- **Dataset sintetis** yang dibuat otomatis oleh program

Tujuan utama repo ini adalah memperlihatkan bagaimana model machine learning dapat dilatih secara terdistribusi tanpa harus mengirimkan data mentah dari client ke server.

Secara sederhana, setiap client melatih model menggunakan datanya sendiri. Setelah proses training lokal selesai, client hanya mengirimkan **bobot model** ke server. Server kemudian menggabungkan bobot dari beberapa client menjadi **model global**.

---

## 2. Konsep Dasar Federated Learning

**Federated Learning** adalah metode pelatihan machine learning di mana data tetap berada di perangkat atau client masing-masing. Server tidak mengumpulkan data mentah, tetapi hanya menerima hasil pembelajaran berupa bobot atau parameter model.

Contoh sederhana:

- Client 1 memiliki data pesan SMS.
- Client 2 memiliki data pesan email.
- Server tidak melihat isi SMS atau email tersebut.
- Client melatih model di tempat masing-masing.
- Server hanya menerima bobot hasil training.
- Server menggabungkan bobot tersebut menjadi model global.

Alurnya dapat digambarkan seperti berikut:

```text
Data Client 1        Data Client 2
     |                    |
Training Lokal       Training Lokal
     |                    |
Bobot Model 1        Bobot Model 2
     \                    /
      \                  /
        Global Server
             |
        Agregasi FedAvg
             |
        Model Global Baru
```

Inti dari Federated Learning adalah **data tetap di client**, sedangkan server hanya mengelola pembaruan model.

---

## 3. Masalah yang Diselesaikan

Repo ini menyimulasikan masalah **klasifikasi pesan scam**. Model bertugas memprediksi apakah suatu pesan termasuk:

| Label | Keterangan |
|---|---|
| 0 | Pesan normal atau legitimate |
| 1 | Pesan scam |

Data yang digunakan bukan berupa teks asli, melainkan fitur numerik sintetis. Artinya, pesan tidak dibaca langsung dalam bentuk kalimat, tetapi sudah diubah menjadi angka-angka yang mewakili karakteristik pesan.

Contoh fitur yang digunakan:

| Fitur | Makna |
|---|---|
| `msg_length` | Panjang pesan |
| `num_links` | Jumlah link dalam pesan |
| `has_phone_num` | Apakah pesan memiliki nomor telepon |
| `money_mention` | Apakah pesan menyebut uang atau hadiah |
| `urgency_words` | Jumlah kata bernada mendesak |
| `all_caps_ratio` | Proporsi huruf kapital |
| `exclamation_count` | Jumlah tanda seru |
| `suspicious_keywords` | Jumlah kata mencurigakan |
| `sender_known` | Apakah pengirim dikenal |
| `reply_requested` | Apakah pesan meminta balasan atau tindakan |

---

## 4. Struktur File Repo

Struktur utama repo dapat dipahami seperti berikut:

```text
FL-Sc/
│
├── data_generator.py
├── fl_client.py
├── fl_server.py
├── main.py
├── model.py
├── requirements.txt
└── data/
```

Penjelasan setiap file:

| File | Fungsi Utama |
|---|---|
| `model.py` | Membuat arsitektur model neural network untuk deteksi scam |
| `data_generator.py` | Membuat dataset sintetis untuk client dan data test |
| `fl_client.py` | Mengatur proses training lokal pada setiap client |
| `fl_server.py` | Mengatur server global dan proses agregasi bobot model |
| `main.py` | Menjalankan seluruh simulasi Federated Learning |
| `requirements.txt` | Berisi daftar library Python yang dibutuhkan |
| `data/` | Folder hasil generate dataset dalam format CSV |

---

## 5. Penjelasan `model.py`

File `model.py` berisi model utama yang digunakan untuk mendeteksi scam. Model ini biasanya diberi nama **ScamDetector**.

Model ini menerima **10 fitur input**, lalu memprosesnya melalui beberapa layer neural network.

Arsitektur sederhananya:

```text
Input 10 fitur
      ↓
Linear Layer 10 → 64
      ↓
ReLU
      ↓
Dropout 0.3
      ↓
Linear Layer 64 → 32
      ↓
ReLU
      ↓
Linear Layer 32 → 1
      ↓
Sigmoid
      ↓
Output probabilitas scam
```

Penjelasan bagian-bagian penting:

| Bagian | Fungsi |
|---|---|
| `Linear` | Menghubungkan input ke neuron pada layer berikutnya |
| `ReLU` | Fungsi aktivasi agar model dapat mempelajari pola non-linear |
| `Dropout` | Mengurangi risiko overfitting saat training |
| `Sigmoid` | Mengubah output menjadi nilai probabilitas antara 0 dan 1 |

Output model adalah angka antara 0 sampai 1. Jika output mendekati 1, pesan dianggap lebih mungkin scam. Jika output mendekati 0, pesan dianggap lebih mungkin normal.

Contoh interpretasi:

```text
Output 0.12 → kemungkinan besar bukan scam
Output 0.87 → kemungkinan besar scam
```

---

## 6. Penjelasan `data_generator.py`

File `data_generator.py` digunakan untuk membuat dataset palsu atau **synthetic dataset**. Dataset ini dibuat otomatis agar pengguna dapat belajar konsep Federated Learning tanpa mencari dataset scam asli.

Program membuat beberapa dataset, yaitu:

| Dataset | Fungsi |
|---|---|
| `client1_data.csv` | Data lokal untuk Client 1 |
| `client2_data.csv` | Data lokal untuk Client 2 |
| `test_data.csv` | Data untuk menguji performa model global |

Data pada client dibuat **non-IID**. Non-IID berarti distribusi data pada setiap client tidak sama.

Contoh:

- Client 1 dapat dianggap memiliki karakteristik pesan SMS.
- Client 2 dapat dianggap memiliki karakteristik pesan email.

Perbedaan ini penting karena dalam Federated Learning nyata, setiap client biasanya memiliki data yang berbeda-beda. Misalnya, data pengguna satu perangkat tidak selalu sama dengan data pengguna perangkat lain.

---

## 7. Penjelasan `fl_client.py`

File `fl_client.py` berisi class yang merepresentasikan client dalam Federated Learning. Client bertugas melakukan training lokal menggunakan data miliknya sendiri.

Tugas utama client:

1. Menerima bobot model global dari server.
2. Memasukkan bobot tersebut ke model lokal.
3. Melatih model menggunakan data lokal.
4. Menghasilkan bobot model baru.
5. Mengirim bobot tersebut kembali ke server.

Alur kerja client:

```text
Terima bobot global dari server
          ↓
Set bobot ke model lokal
          ↓
Training menggunakan data lokal
          ↓
Hitung loss
          ↓
Update bobot model
          ↓
Kirim bobot baru ke server
```

Dalam training lokal, client menggunakan beberapa komponen machine learning:

| Komponen | Fungsi |
|---|---|
| `DataLoader` | Membagi data menjadi batch kecil |
| `BCELoss` | Menghitung kesalahan model untuk klasifikasi biner |
| `Adam` | Optimizer untuk memperbarui bobot model |
| `local_epochs` | Jumlah perulangan training lokal |

**BCELoss** digunakan karena masalahnya adalah klasifikasi biner, yaitu hanya ada dua kelas: scam dan bukan scam.

---

## 8. Penjelasan `fl_server.py`

File `fl_server.py` berisi class server global. Server bertugas menyimpan model global dan menggabungkan bobot dari semua client.

Tugas utama server:

1. Menyimpan model global.
2. Mengirim bobot model global ke client.
3. Menerima bobot hasil training dari client.
4. Menggabungkan bobot client menggunakan FedAvg.
5. Mengevaluasi model global menggunakan data test.

### 8.1 Apa itu FedAvg?

**FedAvg** atau **Federated Averaging** adalah metode untuk menggabungkan bobot model dari beberapa client dengan cara menghitung rata-rata berbobot.

Jika client memiliki jumlah data berbeda, client dengan data lebih banyak dapat memberikan kontribusi lebih besar terhadap model global.

Contoh sederhana:

```text
Client 1 memiliki 600 data
Client 2 memiliki 600 data

Karena jumlah datanya sama,
bobot Client 1 dan Client 2 memiliki kontribusi yang seimbang.
```

Jika jumlah data berbeda:

```text
Client 1 memiliki 800 data
Client 2 memiliki 200 data

Client 1 memberi pengaruh lebih besar
karena jumlah datanya lebih banyak.
```

### 8.2 Evaluasi Model

Server juga mengevaluasi model global menggunakan metrik berikut:

| Metrik | Makna |
|---|---|
| Accuracy | Persentase prediksi yang benar |
| Precision | Ketepatan model saat memprediksi scam |
| Recall | Kemampuan model menemukan pesan scam yang benar-benar scam |
| F1-score | Gabungan precision dan recall |

---

## 9. Penjelasan `main.py`

File `main.py` adalah file utama yang menjalankan seluruh proses simulasi.

Biasanya file ini memiliki konfigurasi seperti:

```python
CONFIG = {
    "n_rounds": 10,
    "local_epochs": 5,
    "learning_rate": 0.01,
    "batch_size": 32,
    "input_dim": 10,
    "samples_per_client": 600,
    "n_test": 300,
}
```

Penjelasan konfigurasi:

| Konfigurasi | Arti |
|---|---|
| `n_rounds` | Jumlah putaran Federated Learning |
| `local_epochs` | Jumlah epoch training lokal pada setiap client |
| `learning_rate` | Kecepatan model belajar |
| `batch_size` | Jumlah data dalam satu batch training |
| `input_dim` | Jumlah fitur input |
| `samples_per_client` | Jumlah data pada setiap client |
| `n_test` | Jumlah data test |

Alur kerja `main.py`:

```text
Mulai
  ↓
Generate dataset sintetis
  ↓
Normalisasi fitur
  ↓
Inisialisasi server
  ↓
Inisialisasi client
  ↓
Mulai round Federated Learning
  ↓
Client training lokal
  ↓
Server agregasi bobot
  ↓
Server evaluasi model global
  ↓
Cetak hasil setiap round
  ↓
Selesai
```

---

## 10. Alur Federated Learning dalam Repo

Secara lengkap, proses Federated Learning pada repo ini dapat dijelaskan sebagai berikut:

### Round 1

1. Server membuat model global awal.
2. Server mengirim bobot model global ke Client 1 dan Client 2.
3. Client 1 melatih model menggunakan data lokalnya.
4. Client 2 melatih model menggunakan data lokalnya.
5. Client 1 dan Client 2 mengirim bobot hasil training ke server.
6. Server menggabungkan bobot menggunakan FedAvg.
7. Server mengevaluasi model global.

### Round Berikutnya

Proses yang sama diulang beberapa kali. Setiap round membuat model global semakin baik karena model terus belajar dari hasil training lokal setiap client.

Diagram sederhana:

```text
Round 1
Server → Client → Training → Server → Agregasi → Evaluasi

Round 2
Server → Client → Training → Server → Agregasi → Evaluasi

Round 3 sampai selesai
Proses yang sama diulang
```

---

## 11. Cara Menjalankan Project

### 11.1 Clone Repository

```bash
git clone https://github.com/3k0sakti/FL-Sc.git
cd FL-Sc
```

### 11.2 Buat Virtual Environment

Untuk Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

Untuk Linux atau macOS:

```bash
python -m venv .venv
source .venv/bin/activate
```

### 11.3 Install Dependency

```bash
pip install -r requirements.txt
```

### 11.4 Jalankan Program

```bash
python main.py
```

Setelah program dijalankan, folder `data/` akan berisi dataset CSV yang dibuat otomatis.

---

## 12. Contoh Output Program

Contoh output yang mungkin muncul:

```text
ROUND 1/10
[Server → Clients] global weights broadcast
[Client 1] local training done loss=...
[Client 2] local training done loss=...
[Clients → Server] uploading weights ...
[Server] global acc=... prec=... rec=... f1=...
```

Penjelasan output:

| Output | Arti |
|---|---|
| `ROUND 1/10` | Program sedang menjalankan round pertama dari total 10 round |
| `global weights broadcast` | Server mengirim bobot global ke client |
| `local training done` | Client selesai melakukan training lokal |
| `loss` | Nilai kesalahan model saat training |
| `uploading weights` | Client mengirim bobot ke server |
| `global acc` | Akurasi model global |
| `prec` | Precision model global |
| `rec` | Recall model global |
| `f1` | F1-score model global |

---

## 13. Kelebihan Repo Ini

Repo ini cocok untuk pemula karena:

- Struktur file sederhana.
- Tidak membutuhkan framework Federated Learning eksternal.
- Menggunakan PyTorch yang umum dipakai dalam machine learning.
- Simulasi dapat dijalankan dalam satu proses Python.
- Cocok untuk memahami konsep FedAvg.
- Tidak perlu dataset eksternal karena data dibuat otomatis.

Repo ini juga bagus sebagai bahan pembelajaran untuk memahami hubungan antara server, client, model lokal, model global, dan agregasi bobot.

---

## 14. Keterbatasan Repo Ini

Meskipun bermanfaat untuk pembelajaran, repo ini masih memiliki beberapa keterbatasan:

1. **Masih berupa simulasi lokal**  
   Semua proses berjalan dalam satu program Python, bukan pada perangkat client dan server sungguhan.

2. **Dataset masih sintetis**  
   Data tidak berasal dari pesan scam nyata, tetapi dibuat secara otomatis oleh program.

3. **Belum menggunakan secure aggregation**  
   Bobot model dikirim langsung ke server tanpa mekanisme agregasi aman berbasis kriptografi.

4. **Belum menggunakan differential privacy**  
   Belum ada mekanisme penambahan noise untuk meningkatkan privasi model.

5. **Preprocessing masih terpusat dalam simulasi**  
   Untuk pembelajaran, normalisasi dilakukan dengan cara yang sederhana. Dalam sistem Federated Learning nyata, preprocessing perlu dirancang agar data client tetap benar-benar terpisah.

---

## 15. Istilah Penting

| Istilah | Penjelasan Sederhana |
|---|---|
| Federated Learning | Teknik melatih model di banyak client tanpa mengumpulkan data mentah ke server |
| Client | Pihak atau perangkat yang memiliki data lokal |
| Server | Pihak pusat yang menggabungkan hasil training dari client |
| Local Training | Proses training model di client |
| Global Model | Model utama yang dimiliki server |
| Local Model | Model yang dilatih pada client |
| Weight / Bobot | Nilai parameter hasil pembelajaran model |
| FedAvg | Algoritma untuk menggabungkan bobot dari beberapa client |
| Epoch | Satu siklus pelatihan terhadap seluruh data training |
| Batch Size | Jumlah data yang diproses dalam satu langkah training |
| Loss | Nilai kesalahan model |
| Accuracy | Persentase prediksi benar |
| Precision | Ketepatan prediksi positif |
| Recall | Kemampuan menemukan data positif yang benar |
| F1-score | Gabungan precision dan recall |

---

## 16. Kesimpulan

Repo **FL-Sc** adalah contoh sederhana untuk memahami Federated Learning menggunakan PyTorch. Proyek ini menyimulasikan sistem deteksi pesan scam dengan dua client dan satu server global.

Konsep paling penting dari repo ini adalah:

```text
Data tetap di client
Client melakukan training lokal
Client mengirim bobot model ke server
Server menggabungkan bobot menggunakan FedAvg
Model global diperbarui setiap round
```

Dengan mempelajari repo ini, pemula dapat memahami dasar-dasar Federated Learning, terutama bagaimana server dan client bekerja sama dalam proses training model tanpa memindahkan data mentah ke server pusat.

---

## 17. Referensi

- Repository FL-Sc: <https://github.com/3k0sakti/FL-Sc>
- File `model.py`: <https://github.com/3k0sakti/FL-Sc/blob/main/model.py>
- File `data_generator.py`: <https://github.com/3k0sakti/FL-Sc/blob/main/data_generator.py>
- File `fl_client.py`: <https://github.com/3k0sakti/FL-Sc/blob/main/fl_client.py>
- File `fl_server.py`: <https://github.com/3k0sakti/FL-Sc/blob/main/fl_server.py>
- File `main.py`: <https://github.com/3k0sakti/FL-Sc/blob/main/main.py>
- File `requirements.txt`: <https://github.com/3k0sakti/FL-Sc/blob/main/requirements.txt>
