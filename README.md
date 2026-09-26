# ⚡ NovaPlayer — Next-Gen Android 14 Gaming Emulator Suite

**NovaPlayer** adalah emulator Android khusus PC gaming yang dibangun di atas fondasi **AOSP Android 14 (API 34 - x86_64)**, Google Play Services resmi, dan akselerasi grafis GPU host langsung (*Direct Host GPU Acceleration*).

---

## 🎮 Dukungan GPU RTX & Hardware Acceleration

NovaPlayer dirancang untuk memaksimalkan kartu grafis modern seperti **NVIDIA GeForce RTX (RTX 3060, 3070, 4060, 4070, dst.)**:
* **Direct Host GPU Rendering:** Emulator langsung menggunakan driver Vulkan 1.4 dan OpenGL ES 3.2 dari kartu grafis host tanpa software emulation overhead.
* **Unlock High Refresh Rate (90 / 120 / 144 FPS):** Mendukung refresh rate tinggi untuk game kompetitif (Free Fire, Mobile Legends, PUBG Mobile, CODM).
* **WHPX (Windows Hypervisor Platform):** Virtualisasi hardware tingkat kernel Windows 10 & 11 untuk performa CPU tanpa lag.

---

## 📱 Device Model Identity (Spoofing Game FPS)

Banyak game Android membatasi opsi grafik (seperti 90 FPS atau 120 FPS) jika mendeteksi perangkat PC/tablet biasa. NovaPlayer memiliki fitur **Device Identity Spoofing**:
1. **ASUS ROG Phone 8 Ultimate (`ASUS_AI2401_A`):** Membuka pengaturan grafis Ultra & 120 FPS di hampir semua game mobile.
2. **Samsung Galaxy S24 Ultra (`SM-S928B`):** Standar flagship global paling stabil.
3. **Xiaomi Black Shark 5 Pro (`SHARK KTUS-H0`):** Profil gaming phone alternatif.
4. **Google Pixel 8 Pro (`Pixel 8 Pro`):** Profil murni Google AOSP.
5. **NovaPlayer Gaming Tablet (16:9):** Mode tablet lanskap standar.

---

## 🛠️ Fitur-Fitur Utama

1. **Dashboard & Controller:**
   * One-click start & stop Android 14 gaming instance.
   * Status monitor waktu nyata (*Offline / Booting / Ready*).
   * Peluncur cepat aplikasi/game yang terpasang.
2. **Keymapping Engine (Mirip BlueStacks / LDPlayer):**
   * **WASD D-Pad:** Gerakan analog menggunakan tombol W, A, S, D.
   * **Action Keys:** Tombol `Space` (Lompat), `Q`, `E`, `R` (Skill), `F` (Interaksi/Loot).
   * **Active Window-Aware:** Hanya membaca tombol saat jendela emulator difokuskan.
3. **Gaming Toolbar:**
   * 📦 **Install APK:** Pasang file APK langsung dengan satu klik.
   * 📸 **Screenshot:** Tangkap layar resolusi tinggi ke folder `screenshots/`.
   * 🔄 **Rotasi Layar:** Berpindah seketika antara Lanskap Tablet dan Portret Ponsel.
   * 🔊 **Audio Volume Controls:** Pengatur volume sistem cepat.
4. **Hardware Customization:**
   * Atur alokasi RAM (2GB s.d. 8GB).
   * Atur jumlah core CPU (2 s.d. 8 Core).
   * Resolusi Layar (720p, 900p, 1080p).
   * Pilihan Engine Grafis (Direct Host GPU, DirectX/ANGLE, Software).

---

## 🚀 Cara Menjalankan

### Cara 1: Menggunakan Executable (1-Klik Tanpa Perlu Install Python)
1. Jika baru pertama kali di PC baru, Anda dapat menjalankan **`setup_dependencies.bat`** untuk memastikan sistem Windows Anda memiliki WebView2 Runtime dan Android SDK.
2. Klik dua kali pada file **`NovaPlayer.exe`**.
*(Catatan: Anda **TIDAK PERLU** menginstall Python atau package PIP karena seluruh runtime Python sudah terkompilasi mandiri di dalam `NovaPlayer.exe`)*.

### Cara 2: Menjalankan dari Source Code (Python)
Jika ingin menjalankan dari source code:
```powershell
# Jalankan setup untuk auto-install dependensi Python & cek sistem
.\setup_dependencies.bat

# Jalankan menggunakan batch script
.\start.bat

# Atau via python langsung
python app.py
```

---

## 💻 Menjalankan di PC Lain (Misal PC dengan GPU RTX)

1. Pastikan fitur **Windows Hypervisor Platform** aktif di Windows:
   * Buka *Turn Windows features on or off* -> Centang **Windows Hypervisor Platform** & **Virtual Machine Platform**.
2. **Microsoft Edge WebView2 Runtime**:
   * Windows 11 sudah menyediakannya secara default.
   * Pada Windows 10 jika belum ada, `setup_dependencies.bat` akan otomatis mengunduh dan memasangnya agar antarmuka UI tidak *freeze/not responding*.
3. **Android SDK & System Image Android 14**:
   * Pastikan terpasang Android emulator & system image Android 14 (`system-images;android-34;google_apis_playstore;x86_64`) via Android Studio atau SDK CLI.
   * Path SDK bisa diatur langsung melalui tab **Settings** di antarmuka NovaPlayer jika berada di folder non-standar.
4. Clone atau update repositori ini:
   ```bash
   git clone https://github.com/denzizzy966/novaplayer.git
   cd novaplayer
   ```
5. Buka **`NovaPlayer.exe`** dan klik **"Launch Emulator"**.
