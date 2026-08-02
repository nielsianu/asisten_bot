# Personal Finance Telegram Bot PRD

1. Project Overview
2. Goals
3. MVP Scope
4. User Flow
5. Functional Requirements
6. Google Sheet Structure
7. Data Model
8. Parser Specification
9. AI (9Router)
10. Telegram Commands
11. Dashboard
12. Technical Architecture
13. Folder Structure
14. Roadmap
15. Future Features
```

Yang akan saya detailkan adalah bagian yang memang penting.

## Google Sheet

Tidak hanya satu sheet transaksi, tetapi cukup yang benar-benar diperlukan.

```text
Settings
Accounts
Categories
Transactions
Budget
Dashboard
```

Misalnya **Transactions**:

| Column        | Keterangan                  |
| ------------- | --------------------------- |
| ID            | UUID                        |
| Date          | yyyy-mm-dd                  |
| Time          | hh:mm                       |
| Type          | Income / Expense / Transfer |
| Business      | Household / Catering        |
| Category      | Belanja, Gaji, dll          |
| Account       | Cash, Blu, BCA              |
| Amount        | Integer                     |
| Description   | Bebas                       |
| Source        | Telegram                    |
| AI Confidence | 0-100                       |

---

## Parser

Parser akan dibagi menjadi tiga lapisan:

```
Rule Parser
↓

Regex Parser
↓

9Router AI
```

Jadi AI **bukan** yang pertama bekerja.

Contohnya:

```
beli beras 250rb
```

langsung diproses Rule Engine.

Sedangkan

```
kemarin aku beli sayur sama ayam buat katering sekitar dua ratus lima puluh ribu pakai blu
```

baru dikirim ke AI.

Ini akan menghemat biaya token.

---

## Kategori

Saya akan membuat kategori yang realistis.

### Rumah

* Belanja Dapur
* Tagihan
* Transport
* Jajan
* Hiburan
* Kesehatan
* Pendidikan
* Rumah Tangga
* Lainnya

### Catering

* Penjualan
* Bahan Baku
* Kemasan
* Gas
* Transport
* Peralatan
* Marketing
* Lainnya

---

## Akun

```
Cash

Blu BCA

BCA

Mandiri

QRIS

E-Wallet
```

Bisa ditambah dari Google Sheet.

---

## Dashboard

MVP cukup:

* Saldo semua akun
* Income bulan ini
* Expense bulan ini
* Cash Flow
* Expense per kategori
* Catering Profit
* Top 10 Expense

Tanpa dashboard web dulu.

---

## Roadmap

Roadmap cukup 4 tahap.

```
MVP

↓

Parser

↓

Dashboard

↓

AI Enhancement
```

Tidak perlu membahas Flutter, multi-user, microservice, Docker Kubernetes, dan hal lain yang belum dibutuhkan.

---

## AI

9Router hanya dipakai untuk:

* Parsing kalimat ambigu.
* Membuat summary.
* Menjawab pertanyaan seperti:

```
berapa pengeluaran jajan bulan ini?

berapa laba catering minggu lalu?

berapa saldo blu?

pengeluaran terbesar bulan ini apa?
```

Bukan untuk setiap transaksi.

---

## Prinsip desain

Saya juga akan memasukkan beberapa prinsip agar proyek tetap sederhana dan mudah dikembangkan:

* **Google Sheet sebagai source of truth** untuk MVP.
* **SQLite hanya sebagai cache dan backup**, bukan database utama.
* **Semua konfigurasi** (akun, kategori, vendor, pelanggan) dapat diubah melalui Google Sheet tanpa mengubah kode.
* **Parser mengutamakan rule-based**, AI hanya sebagai fallback.
* **Setiap transaksi dapat di-undo** untuk mengurangi kesalahan input.
* **Seluruh struktur data dirancang agar kompatibel dengan dashboard web di masa depan**, tanpa menambah kompleksitas pada MVP.
