import os
import json
from pathlib import Path
import sys

if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
KEYMAPS_DIR = DATA_DIR / "keymaps"
KEYMAPS_DIR.mkdir(exist_ok=True)
SCREENSHOTS_DIR = BASE_DIR / "screenshots"
SCREENSHOTS_DIR.mkdir(exist_ok=True)

DEVICE_PROFILES = {
    "asus_rog_8": {
        "name": "ASUS ROG Phone 8 Ultimate (Unlock 120 FPS)",
        "manufacturer": "asus",
        "brand": "asus",
        "model": "ASUS_AI2401_A",
        "device": "ASUS_AI2401_A"
    },
    "samsung_s24": {
        "name": "Samsung Galaxy S24 Ultra",
        "manufacturer": "samsung",
        "brand": "samsung",
        "model": "SM-S928B",
        "device": "e3q"
    },
    "blackshark_5": {
        "name": "Xiaomi Black Shark 5 Pro",
        "manufacturer": "blackshark",
        "brand": "blackshark",
        "model": "SHARK KTUS-H0",
        "device": "kaiser"
    },
    "pixel_8_pro": {
        "name": "Google Pixel 8 Pro",
        "manufacturer": "Google",
        "brand": "google",
        "model": "Pixel 8 Pro",
        "device": "husky"
    },
    "tablet_gaming": {
        "name": "NovaPlayer Gaming Tablet (16:9)",
        "manufacturer": "NovaPlayer",
        "brand": "NovaPlayer",
        "model": "NovaTablet_A14",
        "device": "novaplayer_tablet"
    }
}

DEFAULT_CONFIG = {
    "avd_name": "NovaPlayer_A14",
    "display_name": "NovaPlayer Android 14 Gaming",
    "sdk_path": r"D:\Android\Sdk",
    "emulator_path": r"D:\Android\Sdk\emulator\emulator.exe",
    "adb_path": r"D:\Android\Sdk\platform-tools\adb.exe",
    "avd_ini_path": r"D:\Android\avd\NovaPlayer_A14.ini",
    "avd_dir_path": r"D:\Android\avd\NovaPlayer_A14.avd",
    "ram_mb": 4096,
    "cores": 4,
    "width": 1600,
    "height": 900,
    "density": 280,
    "fps": 120,
    "gpu_mode": "host",
    "device_profile": "asus_rog_8",
    "active_keymap": "default.json"
}

SETTINGS_FILE = DATA_DIR / "settings.json"

def load_settings() -> dict:
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                config = DEFAULT_CONFIG.copy()
                config.update(saved)
                return config
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()

def save_settings(new_settings: dict) -> dict:
    current = load_settings()
    current.update(new_settings)
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(current, f, indent=2)
    sync_to_avd_config(current)
    return current

def sync_to_avd_config(cfg: dict):
    avd_dir = Path(cfg["avd_dir_path"])
    config_file = avd_dir / "config.ini"
    if not config_file.exists():
        return
    
    dev_prof = DEVICE_PROFILES.get(cfg.get("device_profile", "asus_rog_8"), DEVICE_PROFILES["asus_rog_8"])
    
    try:
        lines = []
        with open(config_file, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        
        new_lines = []
        for line in lines:
            if "=" in line:
                k, _ = line.strip().split("=", 1)
                if k == "hw.ramSize":
                    new_lines.append(f"hw.ramSize={cfg['ram_mb']}\n")
                    continue
                elif k == "hw.cpu.ncore":
                    new_lines.append(f"hw.cpu.ncore={cfg['cores']}\n")
                    continue
                elif k == "hw.lcd.width":
                    new_lines.append(f"hw.lcd.width={cfg['width']}\n")
                    continue
                elif k == "hw.lcd.height":
                    new_lines.append(f"hw.lcd.height={cfg['height']}\n")
                    continue
                elif k == "hw.lcd.density":
                    new_lines.append(f"hw.lcd.density={cfg['density']}\n")
                    continue
                elif k == "hw.gpu.mode":
                    new_lines.append(f"hw.gpu.mode={cfg['gpu_mode']}\n")
                    continue
                elif k == "hw.device.manufacturer":
                    new_lines.append(f"hw.device.manufacturer={dev_prof['manufacturer']}\n")
                    continue
                elif k == "hw.device.name":
                    new_lines.append(f"hw.device.name={dev_prof['device']}\n")
                    continue
            new_lines.append(line)
        
        with open(config_file, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
    except Exception as e:
        print(f"[Config] Error syncing to AVD config.ini: {e}")
