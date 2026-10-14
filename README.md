# Video-Square-Battle-2D-Otomatis
# Rencana Proyek: Video Square Battle 2D Otomatis

Dokumen ini menjelaskan rencana pembuatan video pertandingan 2D (gaya "Square League") secara otomatis menggunakan Python, Pygame, dan FFmpeg.

---

## 1. Tujuan

Membuat sistem yang dapat menghasilkan video pertandingan antar kotak (square battle) secara otomatis, dengan hasil berbeda di setiap video, tanpa animasi manual.

## 2. Konsep Dasar

Video dibuat dari simulasi fisika sederhana yang direkam frame demi frame:

1. Program menjalankan simulasi: kotak bergerak, memantul di dinding, bertabrakan, kehilangan HP, dan tereliminasi.
2. Setiap frame digambar ke layar virtual (tanpa membuka jendela).
3. Frame dikirim langsung ke FFmpeg dan dikodekan menjadi file MP4.
4. Posisi awal dan arah gerak diacak, sehingga setiap video memiliki jalan cerita dan pemenang yang berbeda.

## 3. Kebutuhan

| Komponen | Keterangan |
|---|---|
| Python 3.x | Bahasa pemrograman utama |
| Pygame | Menggambar frame (`pip install pygame`) |
| FFmpeg | Mengubah frame menjadi video MP4 (harus terpasang di sistem) |

## 4. Spesifikasi Video

- **Resolusi:** 1080 × 1920 (vertikal, cocok untuk YouTube Shorts)
- **Frame rate:** 60 FPS
- **Durasi maksimum:** 90 detik pertandingan + 2 detik kartu pembuka + 3 detik layar pemenang
- **Peserta:** 6 kotak (Merah, Biru, Hijau, Kuning, Ungu, Oranye)
- **Aturan:** setiap tabrakan mengurangi HP 5–15 poin; kotak dengan HP 0 tereliminasi; kotak terakhir yang bertahan menang. Jika waktu habis, pemenangnya adalah kotak dengan HP tertinggi.

## 5. Struktur Proyek & Cara Menjalankan

### Konsep video

| Konsep (`id`) | File | Mode | Durasi maks | Inti permainan |
|---|---|---|---|---|
| Square Battle (`square_battle`) | `square_battle.py` | `klasik`, `menyusut` | 90 s | 6 kotak bertabrakan dan kehilangan HP; kotak terakhir menang |
| Perang Suit (`perang_suit`) | `rps_war.py` | `seimbang`, `underdog` | 60 s | Batu–Gunting–Kertas; yang kalah berubah jenis; menang jika menguasai arena |
| Sumo Bola (`sumo`) | `sumo.py` | `klasik`, `menyusut` | 60 s | Bola berwajah saling dorong; keluar ring = kalah; duel final memicu *Sudden Death* |
| Perebutan Wilayah (`wilayah`) | `wilayah.py` | `klasik`, `power-up` | 45 s | Kotak mengecat lantai; wilayah terluas menang; bintang power-up memberi cipratan besar |

### File pendukung

| File | Isi |
|---|---|
| `engine.py` | Bagian bersama: kanvas & teks, encoder FFmpeg, penggabungan audio, CLI standar |
| `audio.py` | Sintesis efek suara (tabrakan, eliminasi, power-up, kemenangan) dan musik latar — tanpa file aset |
| `concepts.py` | Daftar konsep; daftarkan konsep baru di sini agar muncul di `batch.py` dan dashboard |
| `production.py` | Penomoran episode, metadata unggahan (judul, deskripsi, tag), daftar video, klasemen |
| `batch.py` | Produksi massal dari baris perintah |
| `dashboard.py`, `dashboard/index.html` | Dashboard web lokal untuk mengelola produksi |

### Menjalankan

```bash
pip install -r requirements.txt

# Dashboard (buka http://127.0.0.1:8000)
python dashboard.py
python dashboard.py --port 9000 --no-browser

# Satu video dari konsep tertentu
python square_battle.py --seed 42 --mode menyusut -o final.mp4
python rps_war.py --mode underdog
python sumo.py --no-audio --max-seconds 20      # uji cepat
python wilayah.py --mode power-up

# Banyak video sekaligus (ke folder output/)
python batch.py -n 10 --konsep sumo             # mode acak, seed acak
python batch.py -n 5 --konsep acak --seed 1000  # konsep acak, bisa dibuat ulang
```

Opsi yang sama untuk setiap file konsep: `-o/--output`, `--seed`, `--mode`, `--no-audio`, `--max-seconds`.
Seed yang sama selalu menghasilkan pertandingan yang sama.

### Dashboard

Dashboard hanya bisa diakses dari komputer ini (`127.0.0.1`). Fiturnya:
- **Buat Video** — pilih konsep, mode (atau acak), jumlah, seed, durasi maksimum, dan audio; video masuk antrean.
- **Antrean** — progres render secara langsung, tombol batal, dan riwayat (render berjalan satu per satu).
- **Galeri** — putar video, filter per konsep, cari pemenang, salin judul/deskripsi + tagar, unduh, render ulang dengan seed yang sama, hapus.
- **Klasemen** — jumlah kemenangan dan rasio menang setiap peserta per konsep.

Setiap video diawali kartu pembuka 2 detik yang memperkenalkan konsep dan mengajak penonton
menebak pemenang. Statistik pertandingan juga disertakan dalam deskripsi unggahan otomatis.

### Hasil di folder `output/`

- `<konsep>_NNN.mp4` — video (nomor episode dihitung per konsep)
- `<konsep>_NNN.json` — seed, mode, pemenang, alasan, urutan eliminasi, statistik, judul, deskripsi, tag
- `manifest.jsonl` — log semua video yang pernah dirender (satu baris per video)

## 6. Tahapan Pengembangan

### Tahap 1 — Prototipe (selesai)
- Simulasi gerak, pantulan dinding, dan tabrakan antar kotak
- Sistem HP, eliminasi, dan penentuan pemenang
- Render otomatis ke MP4 melalui FFmpeg

### Tahap 2 — Produksi Massal (selesai — `batch.py`)
- Panggil `main(f"battle_{i}.mp4")` dalam loop untuk menghasilkan banyak video sekaligus
- Gunakan seed acak berbeda (atau catat seed-nya agar video bisa dibuat ulang)

### Tahap 3 — Audio (selesai — `audio.py`)
- Catat nomor frame setiap tabrakan dan eliminasi
- Tempatkan efek suara pada waktu yang sesuai (frame ÷ FPS = detik)
- Gabungkan efek suara dan musik latar ke video menggunakan FFmpeg
- Efek suara sangat berpengaruh pada kesan "satisfying"

### Tahap 4 — Variasi Konten (sebagian selesai — lihat `IDE_KONTEN.md` untuk ide lain)
- **Mode balapan:** kotak berlomba menuju garis finish dengan rintangan
- **Arena menyusut:** ruang gerak mengecil seiring waktu (selesai — `--mode menyusut`)
- **Power-up:** item penambah kecepatan, perisai, atau penyembuh HP (selesai di `wilayah.py --mode power-up`)
- **Senjata:** kotak dapat menembak atau memiliki kemampuan khusus
- **Format seri/turnamen:** pemenang melaju ke babak berikutnya, membangun cerita antar video

### Tahap 5 — Unggah Otomatis
- Gunakan YouTube Data API v3 untuk mengunggah video
- Isi judul, deskripsi, tag, dan thumbnail secara otomatis (misalnya "Siapa yang Menang? Square Battle #12")
- Atur jadwal tayang agar unggahan konsisten
- Perhatikan batas kuota harian API

## 7. Catatan Penting

YouTube memiliki kebijakan monetisasi terhadap konten yang sangat repetitif atau diproduksi massal tanpa variasi berarti. Jika tujuannya monetisasi, pastikan setiap video memiliki keunikan, misalnya mekanik baru, narasi, karakter dengan identitas sendiri, atau format seri yang berkembang dari waktu ke waktu.

## 8. Langkah Berikutnya

- [x] Jalankan skrip dasar dan uji hasil video
- [ ] Sesuaikan warna, ukuran, kecepatan, dan tampilan
- [x] Tambahkan efek suara otomatis
- [x] Kembangkan minimal satu mode permainan baru
- [ ] Siapkan pipeline unggah otomatis
