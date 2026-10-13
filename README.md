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
- **Durasi maksimum:** 90 detik pertandingan + 3 detik layar pemenang
- **Peserta:** 6 kotak (Merah, Biru, Hijau, Kuning, Ungu, Oranye)
- **Aturan:** setiap tabrakan mengurangi HP 5–15 poin; kotak dengan HP 0 tereliminasi; kotak terakhir yang bertahan menang. Jika waktu habis, pemenangnya adalah kotak dengan HP tertinggi.

## 5. Struktur Proyek & Cara Menjalankan

| File | Isi |
|---|---|
| `square_battle.py` | Simulasi, render frame (Pygame), dan encode MP4 (FFmpeg). Bisa dijalankan sendiri. |
| `audio.py` | Sintesis efek suara (tabrakan, eliminasi, kemenangan) dan musik latar — tanpa file aset. |
| `batch.py` | Produksi massal: banyak video sekaligus + metadata JSON (judul, deskripsi, tag) untuk unggahan. |

```bash
pip install -r requirements.txt

# Satu video
python square_battle.py                              # -> battle.mp4
python square_battle.py --seed 42 --mode menyusut -o final.mp4
python square_battle.py --no-audio --max-seconds 20  # uji cepat

# Banyak video sekaligus (ke folder output/)
python batch.py -n 10                 # mode acak, seed acak
python batch.py -n 5 --seed 1000 --mode klasik --start 13
```

Opsi `square_battle.py`:

| Opsi | Keterangan |
|---|---|
| `-o, --output` | Nama file hasil (default `battle.mp4`) |
| `--seed` | Seed acak; seed yang sama selalu menghasilkan pertandingan yang sama |
| `--mode` | `klasik` atau `menyusut` (arena mengecil mulai detik 10 hingga detik 60) |
| `--no-audio` | Render tanpa suara |
| `--max-seconds` | Batas durasi pertandingan (default 90) |

Hasil `batch.py` di folder `output/`:
- `battle_NNN.mp4` — video
- `battle_NNN.json` — seed, mode, pemenang, urutan eliminasi, judul, deskripsi, dan tag
- `manifest.jsonl` — ringkasan semua video yang pernah dirender (satu baris per video)

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

### Tahap 4 — Variasi Konten
- **Mode balapan:** kotak berlomba menuju garis finish dengan rintangan
- **Arena menyusut:** ruang gerak mengecil seiring waktu (selesai — `--mode menyusut`)
- **Power-up:** item penambah kecepatan, perisai, atau penyembuh HP
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
