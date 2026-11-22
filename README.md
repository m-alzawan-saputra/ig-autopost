# ig-autopost

Posting otomatis ke Instagram setiap hari pukul **18.00 WIB** lewat GitHub Actions dan Instagram API resmi. Gratis, tanpa laptop.

## Cara kerja

1. Paket konten dimasukkan ke folder `queue/`, satu folder per postingan.
2. Setiap hari, GitHub Actions mengambil folder paling awal yang tanggalnya sudah tiba, lalu memposting.
3. Folder yang sudah terposting dipindah ke `posted/`.

Format folder antrean:

```
queue/
  2026-11-24/
    01.jpg        ← 1 gambar = post biasa
    caption.txt
  2026-11-25/
    01.jpg        ← 2–10 gambar = carousel (urut sesuai nama file)
    02.jpg
    03.jpg
    caption.txt
```

Gambar wajib **JPG**, ukuran disarankan 1080x1350.

## Pengaturan (sekali saja)

### 1. Buat aplikasi di Meta
1. Buka https://developers.facebook.com → **My Apps** → **Create App**.
2. Pilih use case **Manage messaging & content on Instagram**.
3. Di menu **API setup with Instagram login**, klik **Add account** dan login dengan akun Instagram.
4. Klik **Generate token**. Salin **token** dan **Instagram user ID** yang muncul.

### 2. Simpan ke GitHub
Repo ini → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**:

| Nama | Isi |
|---|---|
| `IG_USER_ID` | Instagram user ID |
| `IG_ACCESS_TOKEN` | token dari langkah 1 |
| `GH_PAT` (opsional) | token GitHub agar perpanjangan token otomatis |

Jangan pernah menulis token di file repo.

### 3. Uji coba
**Actions** → **Posting Instagram** → **Run workflow**. Biarkan "Uji coba saja" tercentang untuk cek tanpa memposting. Hilangkan centangnya untuk posting sungguhan.

## Catatan
- Repo ini harus **public** agar Instagram bisa mengambil gambar dari `raw.githubusercontent.com`. Isinya memang konten yang akan dipublikasikan.
- Token berlaku 60 hari. Workflow **Perpanjang token Instagram** memperpanjangnya tiap tanggal 1 (perlu `GH_PAT`). Tanpa `GH_PAT`, buat token baru di Meta sebelum 60 hari dan perbarui secret-nya.
- Ubah jam posting di `.github/workflows/post.yml` (baris `cron`, waktu UTC; 18.00 WIB = 11.00 UTC).
