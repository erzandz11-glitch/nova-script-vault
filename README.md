# 🌾 OMNI-SCRIPT-HARVESTER // TITAN AUTONOMOUS ENGINE

**OMNI-SCRIPT-HARVESTER** adalah mesin panen massal otomatis untuk mengumpulkan puluhan script bot WhatsApp terbaru dari GitHub API dan YouTube Channels secara cepat, aman, dan tanpa iklan receh. Berkas yang terpanen langsung disimpan di folder karantina, dicatat ke database SQLite anti-duplikat, dan dilaporkan secara real-time ke bot Telegram.

---

## 🚀 Fitur Utama

1. **GitHub Mass Harvester:** Sekali perintah, langsung menyedot 10–50 repositori bot WhatsApp Baileys terbaru yang aktif diperbarui di GitHub tanpa captcha.
2. **YouTube Channel & Video Dumper:** Memindai kata kunci dan channel kreator bot WA populer untuk mengekstrak tautan unduh (MediaFire, Google Drive, GitHub) dari deskripsi dan komentar video.
3. **MediaFire Direct Grabber:** Mengurai halaman unduhan MediaFire dan langsung menyedot berkas `.zip` secara otomatis.
4. **SQLite Deduplicator:** Melacak ID repositori dan ID video yang sudah pernah diunduh agar tidak ada duplikasi data.
5. **Karantina Mandiri (Quarantine Vault):** Mengisolasi berkas ZIP yang baru diunduh di folder aman dan melarang eksekusi kode sebelum diaudit oleh **OMNI-TITAN**.
6. **Integrasi Telegram Real-Time:** Mengirimkan kartu laporan lengkap saat ada script baru yang berhasil terpanen.
7. **Siap Skalabilitas Cloud (VPS / Pterodactyl Multi-Panel):** Dapat dijalankan di laptop ThinkPad lokal saat ini, dan siap dipindahkan ke VPS / Panel Pterodactyl 24 jam nonstop minggu depan.

---

## 📁 Struktur Folder Proyek

```
omni-script-harvester/
├── .env.example              # Template token Telegram & GitHub
├── .env                      # Kredensial privat (aman, masuk .gitignore)
├── config.json               # Konfigurasi query pencarian, limit, & target channel
├── harvester.py              # CLI Master Launcher (Menu interaktif & Argumen CLI)
├── modules/
│   ├── deduplicator.py       # Engine SQLite pelacak riwayat anti-duplikat
│   ├── github_harvester.py   # Mesin pencari & pengunduh massal GitHub API
│   ├── yt_channel_dumper.py  # Mesin pemindai & ekstraktor link video YouTube
│   ├── mediafire_grabber.py  # Pengunduh direct MediaFire otomatis
│   └── omni_titan_auditor.py # Engine audit keamanan backdoor, stealer & stabilitas
├── storage/
│   ├── harvest_history.sqlite# Database riwayat unduhan
│   ├── quarantine_vault/     # Folder karantina penyimpanan berkas .ZIP
│   ├── harvested_manifest.json # Ringkasan metadata publik untuk staging
│   └── audit_report.json     # Laporan audit komprehensif OMNI-TITAN
├── integrations/
│   ├── telegram_bot.py       # Modul pengirim notifikasi kartu ke Telegram
│   └── github_pusher.py      # Modul auto-commit & manifest exporter
├── tests/
│   ├── test_harvester.py     # Suite unit test harvester
│   └── test_omni_titan_auditor.py # Suite unit test keamanan & adversarial auditor
├── START_HARVESTER.bat       # Peluncur satu-klik untuk Windows
└── README.md                 # Dokumentasi operasional lengkap
```

---

## 💻 Cara Menjalankan

### 1. Menjalankan via Menu Interaktif (Mudah)
Cukup klik ganda berkas **`START_HARVESTER.bat`** atau jalankan perintah berikut di PowerShell / Terminal:
```powershell
python harvester.py
```
Pilih opsi menu:
* `1` : Panen Massal dari GitHub API (Rekomendasi Tercepat)
* `2` : Panen Script dari YouTube (Ekstraksi MediaFire / Drive)
* `3` : Panen Lengkap (GitHub + YouTube Sekaligus)
* `4` : Cek Status Vault & Riwayat Karantina
* `5` : Jalankan OMNI-TITAN Security & Stability Audit
* `6` : Keluar

### 2. Menjalankan via Command Line (Otomatis)
* **Panen GitHub saja:**
  ```powershell
  python harvester.py --github
  ```
* **Panen YouTube saja:**
  ```powershell
  python harvester.py --youtube
  ```
* **Panen Semua Sumber Sekaligus:**
  ```powershell
  python harvester.py --all
  ```
* **Lihat Status Database Vault:**
  ```powershell
  python harvester.py --status
  ```

---

## ⚙️ Konfigurasi Notifikasi Telegram (Opsional)
Salin berkas `.env.example` menjadi `.env`, lalu masukkan token Telegram Anda:
```env
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrSTUvwxYZ
TELEGRAM_CHAT_ID=987654321
```

---

## 🧪 Menjalankan Unit Test
Untuk memastikan seluruh modul bekerja 100% tanpa kendala:
```powershell
python -m unittest discover -s tests -p "test_*.py"
```

---

## 🛡️ Alur Kerja Bersama OMNI-TITAN di Antigravity
1. Jalankan `python harvester.py --github` untuk mengumpulkan puluhan script ke folder `storage/quarantine_vault/`.
2. Buka Antigravity.
3. Beri instruksi: *"Tolong audit dan bersihkan script di folder quarantine_vault menggunakan OMNI-TITAN"*.
4. OMNI-TITAN akan membuang backdoor, membuka enkripsi, menguji coba, dan menyiapkan script bersih siap dibagikan ke komunitas!
