# WhatsApp Blast Desktop

A WhatsApp Web automation tool built with Tkinter, SQLite, Selenium, Pandas, and APScheduler. The application follows the `SRS.docx` specification: contact and template management, manual/scheduled blast with delay, plus logging.

## Fitur

- Manajemen kontak (CRUD + import CSV + tagging untuk pencarian/filter).
- Filter kontak & target blast berdasarkan keyword/tag untuk segmentasi cepat.
- Manajemen template pesan dengan syntax template Jinja2 (`{{contact.nama}}`,`{{contact.nomor}}`, `{{today|format_date("%d/%m/%Y")}}`, kondisi, dll).
- Blast manual dengan pemilihan kontak dan delay antar pesan.
- Scheduler (set, auto start, cancel, riwayat).
- Log status per kontak dengan ekspor CSV/PDF dan grafik ringkasan sukses/gagal.
- Proteksi login: pengguna tanpa login hanya melihat kontak terbatas, login memberi akses penuh.

## Persiapan

1. Pastikan Python 3.10+ terpasang.
2. (Opsional) Buat virtualenv: `python -m venv env && env\Scripts\activate`.
3. Instal dependensi:
   ```bash
   pip install -r requirements.txt
   ```
4. Siapkan ChromeDriver yang kompatibel dengan versi Chrome lokal di `data/drivers` atau pastikan driver berada di PATH.

## Menjalankan

```bash
python main.py
```

Pada run pertama, login ke WhatsApp Web di jendela Selenium. Setelah QR code dipindai, sesi disimpan di profil browser default.

### Login Aplikasi

- Gunakan tombol **Login** pada tab Blast untuk memasukkan email/password yang terdaftar (diverifikasi via Google Apps Script).
- Jika belum login, tab Blast hanya menampilkan kontak pertama sebagai contoh sehingga blast bersifat terbatas.
- Setelah login sukses, status di tab Blast menampilkan nama & masa berlaku lisensi dan seluruh kontak siap dipilih.

## Build ke EXE

1. Instal PyInstaller (sekali saja):
   ```bash
   pip install pyinstaller
   ```
2. Jalankan build dari root project:
   ```bash
   pyinstaller --onefile --name wa_blast main.py
   ```
3. File executable berada di folder `dist/wa_blast.exe`. Pastikan folder `data/` ikut disalin jika ingin menggunakan database/drivers bawaan.

## Struktur Basis Data

- `contacts`: daftar kontak (nama, nomor unik, tags koma-separator).
- `templates`: daftar template pesan.
- `schedules`: jadwal blast mendatang.
- `logs`: riwayat pengiriman.

Database SQLite otomatis dibuat di `data/wa_blast.db`. CSV import membutuhkan kolom `number` (opsional `name`).

## Scheduler

Scheduler memakai APScheduler. Saat aplikasi berjalan, semua jadwal berstatus `scheduled` dan waktu > sekarang akan dieksekusi otomatis.

## Catatan

- Penggunaan WhatsApp Web secara otomatis memiliki risiko pemblokiran nomor bila spam berlebihan.
- Gunakan delay >= 2 detik dan batasi maksimal 300 pesan per hari sesuai rekomendasi SRS.
- Lihat panduan lengkap pada `USER_MANUAL.md` atau tab **User Manual** di aplikasi.

## Sintaks Template

Template pesan dirender menggunakan Jinja2. Nilai yang selalu tersedia:

- `contact`: informasi kontak dengan alias `contact.name`, `contact.nama`, `contact.number`, `contact.nomor`.
- `today`: tanggal hari ini (`datetime.date`), gunakan `|format_date("%d/%m/%Y")` untuk format khusus.
- `now`: timestamp saat pesan dikirim.

Contoh isi template:

```
Halo {{ contact.nama }},
Pesanan Anda akan kami kirim {{ today|format_date("%d %B %Y") }}.
{% if contact.nomor.startswith('+62') %}
Terima kasih pelanggan Indonesia!
{% endif %}
```
"# whatsapp-blast" 
