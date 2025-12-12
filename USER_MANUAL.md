# User Manual - WhatsApp Blast Desktop

Panduan ini menjelaskan cara memakai fitur utama aplikasi yang telah terpasang.

## 1. Login WhatsApp Web

- Jalankan aplikasi.
- Jika diminta, pindai QR code WhatsApp Web pada jendela Selenium. Sesi tersimpan otomatis dan hanya perlu diulang saat kadaluarsa.

## 2. Login Aplikasi

- Buka tab **Blast** lalu klik tombol **Login**.
- Masukkan email & password yang terdaftar. Setelah sukses, status akan menunjukkan nama & tanggal expired lisensi.
- Tanpa login, aplikasi hanya menampilkan satu kontak contoh di tab Blast sehingga blast bersifat terbatas.

## 3. Tab Kontak

- Tambah kontak dengan memasukkan **Nama** dan **Nomor** lalu klik **Tambah**.
- Pilih baris kontak untuk mengubah atau menghapusnya.
- Gunakan **Import CSV** (kolom `name`, `number`) untuk menambahkan kontak massal.

## 4. Tab Template

- Buat judul dan isi template menggunakan sintaks Jinja2.
- Variabel: `contact.name`, `contact.nama`, `contact.number`, `contact.nomor`, `today`, `now`.
- Filter: `format_date("%d/%m/%Y")` untuk format tanggal.
- Klik **Preview** guna melihat hasil render terhadap kontak contoh.

## 5. Tab Blast

1. Pilih template.
2. Pilih kontak (jika belum login hanya kontak pertama yang tersedia).
3. Atur **Delay** antar pesan (>=2 detik dianjurkan).
4. Klik **Mulai Blast** untuk mengirim, atau **Stop** untuk membatalkan.
5. Panel status di bagian bawah menampilkan progres pengiriman.

## 6. Tab Scheduler

- Masukkan waktu `YYYY-MM-DD HH:MM`, pilih template, dan delay.
- Klik **Tambah Jadwal** untuk menjadwalkan kampanye.
- Pilih entri jadwal lalu tekan **Cancel Jadwal** untuk membatalkan.

## 7. Tab Log

- Klik **Refresh Log** untuk memuat ulang riwayat pengiriman.
- Gunakan **Export CSV** atau **Export PDF** untuk menyimpan laporan pasca-blast.
- Grafik ringkasan menampilkan jumlah sukses/gagal secara cepat.
- Kolom menampilkan timestamp, nomor, status (`sent`/`failed`), dan pesan status.

## 8. Tab User Manual & About

- Tab **User Manual** menampilkan dokumen ini (tombol **Refresh Manual** untuk memuat ulang).
- Tab **About** berisi ringkasan aplikasi.

## 9. Tips Penggunaan

- Jaga jeda realistis antar pesan dan batasi total blast harian untuk menghindari blokir WhatsApp.
- Manfaatkan preview template sebelum menjalankan kampanye ke banyak kontak.
- Backup berkala database `data/wa_blast.db` untuk keamanan data kontak dan log.
