# WhatsApp Blast Desktop

A WhatsApp Web automation tool built with Tkinter, SQLite, Selenium, Pandas, and APScheduler. The application follows the `SRS.docx` specification: contact and template management, manual/scheduled blast with delay, plus logging.

## Fitur

- Manajemen kontak (CRUD + import CSV).
- Manajemen template pesan dengan placeholder `{{nama}}`, `{{nomor}}`, dan `{{tanggal}}`.
- Blast manual dengan pemilihan kontak dan delay antar pesan.
- Scheduler (set, auto start, cancel, riwayat).
- Log status per kontak.

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

- `contacts`: daftar kontak (nama, nomor unik).
- `templates`: daftar template pesan.
- `schedules`: jadwal blast mendatang.
- `logs`: riwayat pengiriman.

Database SQLite otomatis dibuat di `data/wa_blast.db`. CSV import membutuhkan kolom `number` (opsional `name`).

## Scheduler

Scheduler memakai APScheduler. Saat aplikasi berjalan, semua jadwal berstatus `scheduled` dan waktu > sekarang akan dieksekusi otomatis.

## Catatan

- Penggunaan WhatsApp Web secara otomatis memiliki risiko pemblokiran nomor bila spam berlebihan.
- Gunakan delay >= 2 detik dan batasi maksimal 300 pesan per hari sesuai rekomendasi SRS.
"# whatsapp-blast" 
