# Google Sheets Template Structure (`asisten_bot`)

Dokumen ini berisi spesifikasi lengkap struktur 6 tab Google Sheets yang digunakan oleh **Asisten Keuangan Bot**.

---

## 📋 Daftar Tab (Worksheets)

1. `Settings`
2. `Accounts`
3. `Categories`
4. `Transactions`
5. `Budget`
6. `Dashboard`

---

## 1. Tab `Settings`
Berisi konfigurasi global sistem.

| Key | Value | Description |
|---|---|---|
| Bot Name | Asisten Keuangan Bot | Nama bot |
| Currency | IDR | Mata uang utama |
| Timezone | Asia/Jakarta | Zona waktu transaksi |
| Default Household Account | Cash | Akun default transaksi rumah tangga |
| Default Business Type | Household | Bisnis default (Household / Catering) |
| AI Confidence Threshold | 90 | Threshold auto-confirm transaksi (%) |

---

## 2. Tab `Accounts`
Berisi daftar akun keuangan (Bank, Cash, E-Wallet).

| ID | Account Name | Type | Initial Balance | Current Balance | Notes | Active |
|---|---|---|---|---|---|---|
| ACC-001 | Cash | Cash | 0 | `=Initial Balance` | Uang tunai fisik | TRUE |
| ACC-002 | Blu BCA | Bank | 0 | `=Initial Balance` | Rekening Blu BCA | TRUE |
| ACC-003 | BCA | Bank | 0 | `=Initial Balance` | Rekening Utama BCA | TRUE |
| ACC-004 | Mandiri | Bank | 0 | `=Initial Balance` | Rekening Mandiri | TRUE |
| ACC-005 | QRIS | E-Wallet | 0 | `=Initial Balance` | Saldo QRIS | TRUE |
| ACC-006 | E-Wallet | E-Wallet | 0 | `=Initial Balance` | GoPay/OVO/ShopeePay | TRUE |

---

## 3. Tab `Categories`
Berisi pemetaan kategori pengeluaran dan pemasukan untuk **Household** dan **Catering**.

| ID | Business | Type | Category Name | Keywords | Active |
|---|---|---|---|---|---|
| CAT-001 | Household | Expense | Belanja Dapur | beras, sayur, minyak, bumbu, daging | TRUE |
| CAT-002 | Household | Expense | Tagihan | listrik, air, wifi, pulsa, token | TRUE |
| CAT-003 | Household | Expense | Transport | bensin, parkir, tol, ojol, grab, gojek | TRUE |
| CAT-004 | Household | Expense | Jajan | kopi, cemilan, es krim, boba, jajan | TRUE |
| CAT-005 | Household | Expense | Hiburan | nonton, bioskop, game, netflix, spotify | TRUE |
| CAT-006 | Household | Expense | Kesehatan | obat, dokter, vitamin, apotek | TRUE |
| CAT-007 | Household | Expense | Pendidikan | buku, kursus, spp, sekolah | TRUE |
| CAT-008 | Household | Expense | Rumah Tangga | sabun, detergen, perkakas, perlengkapan | TRUE |
| CAT-009 | Household | Expense | Lainnya | misc, pengeluaran lain | TRUE |
| CAT-010 | Household | Income | Gaji | gaji, payroll, salary | TRUE |
| CAT-011 | Household | Income | Bonus | thr, bonus, insentif | TRUE |
| CAT-012 | Household | Income | Lainnya | pemasukan lain, transferan | TRUE |
| CAT-050 | Catering | Income | Penjualan | pesanan, katering, nasi box, catering | TRUE |
| CAT-051 | Catering | Expense | Bahan Baku | daging katering, bumbu katering, beras katering | TRUE |
| CAT-052 | Catering | Expense | Kemasan | box, mika, plastik, sendok, sterofoam | TRUE |
| CAT-053 | Catering | Expense | Gas | elpiji, gas 3kg, gas 12kg | TRUE |
| CAT-054 | Catering | Expense | Transport | ongkir katering, kurir, antar pesanan | TRUE |
| CAT-055 | Catering | Expense | Peralatan | wajan, panci, pisau, alat masak | TRUE |
| CAT-056 | Catering | Expense | Marketing | brosur, iklan, promosi, ig ads | TRUE |
| CAT-057 | Catering | Expense | Lainnya | biaya operasional katering lain | TRUE |

---

## 4. Tab `Transactions`
Database transaksi pencatatan utama.

| Column | Keterangan | Contoh Data |
|---|---|---|
| **ID** | UUID Transaksi | `TX-8f3a12b4` |
| **Date** | Tanggal (`YYYY-MM-DD`) | `2026-08-02` |
| **Time** | Waktu (`HH:MM`) | `14:30` |
| **Type** | `Expense` / `Income` / `Transfer` | `Expense` |
| **Business** | `Household` / `Catering` | `Household` |
| **Category** | Kategori sesuai tab Categories | `Belanja Dapur` |
| **Account** | Akun sesuai tab Accounts | `Blu BCA` |
| **Amount** | Nominal angka (Integer) | `250000` |
| **Description** | Catatan / Pesan Pengguna | `Beli beras 5kg dan telur` |
| **Source** | Sumber transaksi | `Telegram` |
| **AI Confidence** | Tingkat keyakinan parsing (0-100) | `95` |

---

## 5. Tab `Budget`
Anggaran bulanan per kategori.

| Category | Business | Monthly Budget | Notes |
|---|---|---|---|
| Belanja Dapur | Household | 2000000 | Anggaran belanja bulanan |
| Tagihan | Household | 1000000 | Listrik, Air, Internet |
| Transport | Household | 500000 | Bensin & Transportasi |
| Jajan | Household | 500000 | Batas jajan per bulan |

---

## 6. Tab `Dashboard`
Kilas ringkasan keuangan bulanan & laba rugi usaha katering.

| Row / Label | Formula / Value | Notes |
|---|---|---|
| **Total Income** | `=SUMIFS(Transactions!H:H, Transactions!D:D, "Income")` | Total Pemasukan |
| **Total Expense** | `=SUMIFS(Transactions!H:H, Transactions!D:D, "Expense")` | Total Pengeluaran |
| **Net Cash Flow** | `=B3-B4` | Selisih Income & Expense |
| **Catering Income** | `=SUMIFS(Transactions!H:H, Transactions!E:E, "Catering", Transactions!D:D, "Income")` | Omset Katering |
| **Catering Expense** | `=SUMIFS(Transactions!H:H, Transactions!E:E, "Catering", Transactions!D:D, "Expense")` | Biaya Katering |
| **Catering Net Profit** | `=B8-B9` | Laba Bersih Katering |

---

## ⚡ Cara Menjalankan Auto-Init Script

Jika Anda telah mengisi `GOOGLE_SHEET_ID` di file `.env` dan meletakkan `credentials.json` di root directory, Anda dapat langsung menjalankan script otomatisasi berikut untuk membuat dan mengisi 6 tab di atas secara instan:

```bash
python scripts/init_sheet.py
```
