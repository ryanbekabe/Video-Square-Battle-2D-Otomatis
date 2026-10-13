# Bank Ide Konten — Selain Square Battle

Kumpulan ide untuk mengembangkan kanal video simulasi 2D otomatis. Semua ide di sini memakai fondasi yang sudah ada: simulasi per frame, `seed` agar hasil bisa dibuat ulang, catatan event untuk audio (`audio.py`), dan produksi massal (`batch.py`).

---

## 1. Bentuk & Karakter Lain

Mengganti "kotak" saja sudah bisa memberi nuansa baru, terutama kalau setiap bentuk punya sifat fisika sendiri.

| Bentuk / Karakter | Ciri khas | Catatan teknis |
|---|---|---|
| **Bola (marble)** | Pantulan lebih alami, cocok untuk balapan dan arena bulat | Tabrakan lingkaran: jarak pusat < jumlah jari-jari, pantulan berdasarkan vektor normal |
| **Segitiga / poligon** | Bisa berputar; sudut lancip memberi damage lebih besar | Perlu rotasi dan deteksi tabrakan SAT; bisa juga pakai `pymunk` |
| **Bola yang membesar** | Setiap pantulan dinding membuat bola bertambah besar hingga memenuhi arena | Sangat "satisfying", jalan ceritanya bisa ditebak tapi tetap menegangkan |
| **Wajah / emoji buatan sendiri** | Setiap peserta punya ekspresi (senang, marah, panik saat HP rendah) | Gambar sederhana: dua mata dan mulut yang berubah sesuai HP |
| **Elemen (Api, Air, Tanah, Petir)** | Ada aturan keunggulan antar elemen | Matriks damage, misalnya Air vs Api = 2× |
| **Hewan / makanan** | Lebih mudah disukai anak-anak dan penonton umum | Pakai sprite sederhana atau bentuk geometris yang diberi wajah |
| **Planet / bintang** | Gaya gravitasi; yang besar menarik dan "menelan" yang kecil | Gaya gravitasi N-body, cukup untuk 10–30 objek |

## 2. Mekanik Permainan Baru

### 2.1 Perang Batu–Gunting–Kertas (konversi)
Puluhan ikon batu, gunting, dan kertas bergerak acak. Ketika dua ikon bertabrakan, yang kalah **berubah** menjadi jenis pemenang. Video selesai ketika semua ikon menjadi satu jenis.
- Kenapa menarik: populasi naik turun secara dramatis, sering terjadi comeback.
- Tambahan: grafik populasi kecil di bawah arena.

### 2.2 Lolos dari Cincin Berputar (ring escape)
Bola berada di dalam beberapa cincin bercelah yang berputar. Bola harus menemukan celah untuk keluar dari cincin terluar.
- Variasi: setiap pantulan menambah kecepatan, atau setiap bola yang keluar memunculkan dua bola baru.

### 2.3 Balapan Kelereng
Lintasan berliku dengan rintangan (paku, kincir, jembatan yang runtuh). Peringkat diperbarui secara langsung di samping layar.
- Format liga: poin per balapan dan klasemen antar video.

### 2.4 Sumo / Dorong Keluar Arena
Arena bundar tanpa dinding. Tidak ada HP; peserta yang terdorong keluar dinyatakan kalah.
- Mudah dipahami dalam satu detik pertama, cocok untuk Shorts.

### 2.5 Perebutan Wilayah (cat warna)
Setiap kotak meninggalkan jejak warna di lantai arena. Di akhir video, warna dengan wilayah terluas menang.
- Persentase wilayah setiap warna ditampilkan secara langsung.
- Bisa digabung dengan mode menyusut.

### 2.6 Infeksi / Zombie
Satu peserta "terinfeksi" sejak awal. Setiap sentuhan menularkan infeksi. Pertanyaannya: siapa yang paling lama bertahan?

### 2.7 Senjata yang Naik Level
Setiap peserta membawa senjata (pedang, tombak, perisai, panah). Setiap serangan yang mengenai sasaran membuat senjatanya lebih kuat atau lebih panjang.
- Penonton menebak senjata mana yang terbaik, sehingga muncul diskusi di kolom komentar.

### 2.8 Raja Bukit (king of the hill)
Ada zona kecil di tengah arena. Siapa pun yang berada di dalamnya mendapat poin per detik. Pemenangnya adalah peserta dengan poin terbanyak saat waktu habis.

### 2.9 Evolusi / Seleksi Alam
Setiap peserta punya "gen" (kecepatan, ukuran, daya tahan). Pemenang "berkembang biak" dengan sedikit mutasi untuk generasi berikutnya.
- Cocok sebagai seri: "Generasi 1 → Generasi 50".

## 3. Konsep Cerita & Format Seri

Konten simulasi lebih tahan lama kalau penonton punya alasan untuk **kembali** ke video berikutnya.

### 3.1 Liga Musiman
- Satu musim terdiri dari 10–20 pertandingan, dengan klasemen yang diperbarui di akhir setiap video.
- Ada final musim, juara bertahan, dan "pemain terbaik musim ini".
- Data bisa disimpan di `manifest.jsonl` lalu diolah menjadi klasemen.

### 3.2 Karakter dengan Identitas
- Setiap peserta punya nama, julukan, dan kepribadian, misalnya "Merah si Pemarah" (cepat tetapi rapuh) atau "Biru si Tank" (lambat tetapi tebal).
- Statistik karakter memengaruhi simulasi, sehingga hasilnya tetap acak tetapi punya pola yang bisa diikuti penonton.
- Rivalitas tercatat: "Pertemuan ke-7 Merah vs Biru, skor 4–2."

### 3.3 Turnamen Gugur (bracket)
- 16 peserta, duel satu lawan satu, hingga final.
- Satu video per babak, atau satu video kompilasi panjang untuk YouTube biasa.

### 3.4 Kisah Underdog
- Peserta terlemah (HP atau kecepatan lebih rendah) diberi sorotan khusus.
- Jika menang, tampilkan layar "COMEBACK!" dan statistik peluang menangnya.

### 3.5 Perang Kerajaan
- Setiap warna adalah kerajaan dengan wilayah di peta grid.
- Setiap video adalah satu "pertempuran" yang mengubah peta. Peta terbaru ditampilkan di awal video berikutnya.

### 3.6 Penonton Ikut Menentukan
- Ajak penonton memilih lewat komentar: "Mode apa berikutnya?" atau "Siapa yang dapat power-up?"
- Hasil pilihan diumumkan di video berikutnya, sehingga keterlibatan penonton meningkat.

## 4. Pengemasan Video (berlaku untuk semua ide)

- **Hook 2 detik pertama:** tampilkan "Tebak pemenangnya di komentar!" dan semua peserta.
- **Slow motion** saat eliminasi terakhir atau saat HP pemenang sangat tipis.
- **Kamera dinamis:** zoom ke area dengan aksi paling ramai.
- **Replay** momen terbaik sebelum layar pemenang, memanfaatkan frame yang tercatat di daftar event.
- **Statistik akhir:** jumlah tabrakan, damage terbesar, waktu bertahan terlama.
- **Variasi visual:** tema warna atau latar berbeda per musim agar video tidak terlihat sama.

## 5. Prioritas yang Disarankan

| Ide | Usaha | Bisa memakai kode sekarang | Potensi |
|---|---|---|---|
| Batu–Gunting–Kertas | Rendah | Tinggi (ganti aturan `collide`) | Tinggi |
| Sumo / dorong keluar | Rendah | Tinggi (hapus HP, cek posisi) | Sedang |
| Perebutan wilayah | Sedang | Sedang (tambah layer lantai) | Tinggi |
| Liga musiman + klasemen | Sedang | Tinggi (`batch.py` + manifest) | Tinggi untuk retensi |
| Karakter dengan statistik | Rendah | Tinggi (atribut di `Square`) | Tinggi bila digabung dengan liga |
| Lolos dari cincin berputar | Sedang | Rendah (fisika lingkaran baru) | Tinggi |
| Balapan kelereng | Tinggi | Rendah (lintasan dan fisika baru) | Tinggi |
| Evolusi / seleksi alam | Tinggi | Sedang | Sedang, niche tetapi setia |

Urutan paling efisien: **Batu–Gunting–Kertas → karakter dengan statistik → liga musiman**. Ketiganya bisa memakai mesin yang sudah ada dan bersama-sama membentuk alur cerita lintas video.

## 6. Hal yang Perlu Dihindari

- **Logo klub, merek, atau karakter berhak cipta** (misalnya klub sepak bola atau tokoh kartun). Gunakan karakter buatan sendiri.
- **Bendera negara atau simbol politik** dalam format "perang". Rawan memicu komentar negatif dan pembatasan iklan.
- **Musik berhak cipta.** Tetap gunakan audio sintesis dari `audio.py` atau musik bebas royalti.
- **Video yang terlalu mirip satu sama lain.** Lihat catatan monetisasi di README bagian 7; variasi mekanik dan cerita adalah kuncinya.
