# NEXT STEPS — dijalankan di laptop build (Gemini)

File ini adalah instruksi untuk sesi berikutnya di laptop yang punya Python dan dipakai
untuk mem-build `NovaPlayer.exe`. Setelah semua langkah selesai dan exe baru sudah
di-push, file ini boleh dihapus.

## Konteks singkat (apa yang sudah diperbaiki di commit ini)

1. **`app.py`** — kegagalan "Launch Emulator" sekarang ditulis ke `novaplayer.log`
   (`[Emulator] Launch failed: ...`) dan dikirim ke UI lewat field `error` di `get_status()`.
   Sebelumnya hasil `EmulatorManager.start()` dibuang, jadi user tidak pernah tahu kenapa
   emulator tidak muncul.
2. **`ui/app.js`** — `pollStatus()` menampilkan `status.error` sebagai toast 10 detik,
   satu kali per kejadian (variabel `lastShownError`).
3. Commit sebelumnya (`60e83d1`) sudah memperbaiki freeze "Not Responding":
   atribut `window/adb/emulator/keymapper` di `EmuApi` dibuat privat (`_window`, dst.)
   supaya pywebview tidak menelusuri `Window.dom.*` di UI thread; impor `Path` di
   `core/emulator.py`; dan `adb start-server` dipanggil dengan handle NUL di `core/adb.py`.

`NovaPlayer.exe` di repo **belum** memuat perubahan nomor 1 dan 2. Itu tugas laptop ini.

## Langkah yang harus dilakukan

### 1. Pull dan pastikan dependency

```powershell
git pull origin main
python -m pip install -r requirements.txt pyinstaller
```

### 2. Uji dari source dulu (wajib sebelum build)

```powershell
python app.py
```

Yang harus terlihat:
- Window terbuka dan **tidak** "Not Responding".
- Klik **Launch Emulator**. Jika laptop ini tidak punya system image / AVD, dalam ±2 detik
  harus muncul toast kuning berisi alasannya (contoh: `No Android system images found in ...`)
  dan baris `[Emulator] Launch failed: ...` di `novaplayer.log`.
- Jika tidak ada toast dan log tetap kosong, perbaikan belum jalan — periksa ulang
  `start_emulator()` di `app.py` dan `pollStatus()` di `ui/app.js` sebelum lanjut.

### 3. Build ulang exe

Pakai perintah build yang sama seperti build sebelumnya jika masih ada. Jika tidak ada,
gunakan ini (onefile, tanpa console, ikon, folder `ui` ikut dibundel, semua DLL pywebview
dan WebView2 ikut):

```powershell
pyinstaller --noconfirm --clean --onefile --noconsole `
  --name NovaPlayer --icon icon.ico `
  --add-data "ui;ui" `
  --collect-all webview `
  --hidden-import pynput.keyboard._win32 --hidden-import pynput.mouse._win32 `
  app.py
```

Lalu salin hasilnya ke root repo (menimpa exe lama):

```powershell
Copy-Item dist\NovaPlayer.exe .\NovaPlayer.exe -Force
```

Catatan: `data/` dan `screenshots/` sengaja **tidak** dibundel. Aplikasi membacanya dari
folder tempat exe berada (lihat `BASE_DIR` di `core/config.py`), jadi exe harus tetap
berada di root repo bersama folder `data/keymaps`.

### 4. Uji exe hasil build

```powershell
.\NovaPlayer.exe
```

Ulangi pengecekan yang sama seperti langkah 2 (tidak freeze, toast error muncul saat
Launch gagal, log terisi). Setelah selesai, tutup aplikasinya.

### 5. Commit dan push exe baru

```powershell
git add NovaPlayer.exe
git commit -m "build: recompile NovaPlayer.exe with launch-error reporting"
git push origin main
```

Jangan ikutkan `data/settings.json` (berisi path spesifik PC) dan `novaplayer.log`.

## Prompt siap tempel untuk Gemini

> Baca file `NEXT_STEPS.md` di root repo ini dan kerjakan langkah 1 sampai 5 secara
> berurutan. Jangan ubah logika di `app.py`, `core/`, atau `ui/` kecuali langkah 2
> membuktikan perbaikan belum jalan. Setelah setiap langkah, laporkan hasil nyatanya
> (output perintah, isi `novaplayer.log`, dan apakah toast error muncul). Jika build
> gagal, tampilkan error PyInstaller lengkap sebelum mencoba solusi lain. Terakhir,
> commit hanya `NovaPlayer.exe` dan push ke `origin/main`.

## Catatan untuk PC gaming (bukan laptop build)

Di PC yang menjalankan emulator, penyebab emulator tidak muncul adalah **bukan** path SDK:
- Folder `system-images` tidak ada di `%LOCALAPPDATA%\Android\Sdk` → install lewat
  Android Studio → SDK Manager → SDK Platforms → Android 14 (API 34) →
  **Google Play Intel x86_64 Atom System Image** (centang *Show Package Details*).
- `emulator -accel-check` melapor hypervisor driver belum terpasang → di tab SDK Tools
  centang **Android Emulator hypervisor driver (installer)**, atau aktifkan
  **Windows Hypervisor Platform** di "Turn Windows features on or off" lalu restart.
