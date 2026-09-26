import os
import json
import shutil
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

def auto_detect_sdk() -> str:
    candidates = [
        os.environ.get("ANDROID_HOME"),
        os.environ.get("ANDROID_SDK_ROOT"),
        str(Path.home() / "AppData" / "Local" / "Android" / "Sdk"),
        r"D:\Android\Sdk",
        r"C:\Android\Sdk",
    ]
    which_adb = shutil.which("adb")
    if which_adb:
        candidates.insert(0, str(Path(which_adb).resolve().parent.parent))
    
    for c in candidates:
        if c and Path(c).exists():
            return str(Path(c).resolve())
    return str(Path.home() / "AppData" / "Local" / "Android" / "Sdk")

def auto_detect_avd_dir() -> str:
    candidates = [
        os.environ.get("ANDROID_AVD_HOME"),
        str(Path.home() / ".android" / "avd"),
        r"D:\Android\avd",
        r"C:\Android\avd",
    ]
    for c in candidates:
        if c and Path(c).exists():
            return str(Path(c).resolve())
    default_dir = Path.home() / ".android" / "avd"
    default_dir.mkdir(parents=True, exist_ok=True)
    return str(default_dir.resolve())

def find_system_image(sdk_path: str):
    sys_dir = Path(sdk_path) / "system-images"
    if not sys_dir.exists():
        return None
    # Prefer android-34 x86_64, then any x86_64 image
    candidates = []
    for p in sys_dir.glob("*/*/*"):
        if (p / "system.img").exists():
            candidates.append(p)
    if not candidates:
        return None
    # Sort candidates preferring newer android and x86_64
    candidates.sort(key=lambda x: ("android-34" in str(x), "x86_64" in str(x)), reverse=True)
    chosen = candidates[0]
    try:
        rel = str(chosen.relative_to(sdk_path)) + "\\"
    except Exception:
        rel = str(chosen)
    return {"path": chosen, "rel": rel}

def ensure_avd_ready(cfg: dict) -> dict:
    avd_name = cfg.get("avd_name", "NovaPlayer_A14")
    avd_dir_path = Path(cfg["avd_dir_path"])
    avd_dir_path.mkdir(parents=True, exist_ok=True)
    
    ini_file = avd_dir_path / f"{avd_name}.ini"
    target_avd_dir = avd_dir_path / f"{avd_name}.avd"
    
    # If already exists and valid, we are good
    if ini_file.exists() and (target_avd_dir / "config.ini").exists():
        return {"success": True, "avd_name": avd_name}
    
    # Otherwise auto-create the AVD configuration
    sdk_path = cfg["sdk_path"]
    img_info = find_system_image(sdk_path)
    if not img_info:
        # Check if ANY other AVD exists
        existing_inis = list(avd_dir_path.glob("*.ini"))
        if existing_inis:
            fallback_name = existing_inis[0].stem
            print(f"[Config] Falling back to existing AVD: {fallback_name}")
            return {"success": True, "avd_name": fallback_name}
        return {
            "success": False,
            "message": f"No Android system images found in {sdk_path}\\system-images. Please install an Android image via Android Studio."
        }
    
    try:
        target_avd_dir.mkdir(parents=True, exist_ok=True)
        ini_content = f"avd.ini.encoding=UTF-8\npath={target_avd_dir}\ntarget=android-34\n"
        ini_file.write_text(ini_content, encoding="utf-8")
        
        # Copy initial image files if present
        img_dir = img_info["path"]
        for f in ["userdata.img", "encryptionkey.img"]:
            src = img_dir / f
            dst = target_avd_dir / f
            if src.exists() and not dst.exists():
                shutil.copy2(src, dst)
        
        dev_prof = DEVICE_PROFILES.get(cfg.get("device_profile", "asus_rog_8"), DEVICE_PROFILES["asus_rog_8"])
        config_content = f"""AvdId={avd_name}
PlayStore.enabled=true
abi.type=x86_64
avd.ini.displayname=NovaPlayer Android 14 Gaming
avd.ini.encoding=UTF-8
disk.dataPartition.size=12G
fastboot.forceColdBoot=no
fastboot.forceFastBoot=yes
hw.accelerometer=yes
hw.arc=false
hw.audioInput=yes
hw.battery=yes
hw.camera.back=none
hw.camera.front=none
hw.cpu.arch=x86_64
hw.cpu.ncore={cfg.get('cores', 4)}
hw.dPad=no
hw.device.hash2=MD5:gaming_tablet_nova
hw.device.manufacturer={dev_prof['manufacturer']}
hw.device.name={dev_prof['device']}
hw.gps=yes
hw.gpu.enabled=yes
hw.gpu.mode={cfg.get('gpu_mode', 'host')}
hw.gyroscope=yes
hw.initialOrientation=landscape
hw.keyboard=yes
hw.lcd.density={cfg.get('density', 280)}
hw.lcd.height={cfg.get('height', 900)}
hw.lcd.width={cfg.get('width', 1600)}
hw.mainKeys=no
hw.ramSize={cfg.get('ram_mb', 4096)}
hw.sdCard=yes
hw.sensors.light=yes
hw.sensors.magnetic_field=yes
hw.sensors.orientation=yes
hw.sensors.pressure=yes
hw.sensors.proximity=yes
hw.trackBall=no
image.sysdir.1={img_info['rel']}
runtime.network.latency=none
runtime.network.speed=full
sdcard.size=2048M
showDeviceFrame=no
skin.dynamic=yes
skin.name={cfg.get('width', 1600)}x{cfg.get('height', 900)}
tag.display=Google Play
tag.displaynames=Google Play
tag.id=google_apis_playstore
tag.ids=google_apis_playstore
target=android-34
vm.heapSize=512
"""
        (target_avd_dir / "config.ini").write_text(config_content, encoding="utf-8")
        print(f"[Config] Successfully initialized {avd_name} in {avd_dir_path}")
        return {"success": True, "avd_name": avd_name}
    except Exception as e:
        print(f"[Config] Error creating AVD: {e}")
        return {"success": False, "message": str(e)}

_sdk_path = auto_detect_sdk()
_avd_dir = auto_detect_avd_dir()

DEFAULT_CONFIG = {
    "avd_name": "NovaPlayer_A14",
    "display_name": "NovaPlayer Android 14 Gaming",
    "sdk_path": _sdk_path,
    "emulator_path": str(Path(_sdk_path) / "emulator" / "emulator.exe"),
    "adb_path": str(Path(_sdk_path) / "platform-tools" / "adb.exe"),
    "avd_ini_path": str(Path(_avd_dir) / "NovaPlayer_A14.ini"),
    "avd_dir_path": _avd_dir,
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
    config = DEFAULT_CONFIG.copy()
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
                config.update(saved)
        except Exception:
            pass
            
    # Verify/re-verify paths exist, fallback to auto-detect if saved paths are invalid on another PC
    if not Path(config["sdk_path"]).exists():
        new_sdk = auto_detect_sdk()
        config["sdk_path"] = new_sdk
        config["emulator_path"] = str(Path(new_sdk) / "emulator" / "emulator.exe")
        config["adb_path"] = str(Path(new_sdk) / "platform-tools" / "adb.exe")
        
    if not Path(config["avd_dir_path"]).exists():
        new_avd = auto_detect_avd_dir()
        config["avd_dir_path"] = new_avd
        config["avd_ini_path"] = str(Path(new_avd) / f"{config['avd_name']}.ini")
        
    return config

def save_settings(new_settings: dict) -> dict:
    current = load_settings()
    current.update(new_settings)
    
    # Update derived paths if sdk_path changed
    if "sdk_path" in new_settings:
        current["emulator_path"] = str(Path(new_settings["sdk_path"]) / "emulator" / "emulator.exe")
        current["adb_path"] = str(Path(new_settings["sdk_path"]) / "platform-tools" / "adb.exe")
        
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(current, f, indent=2)
    sync_to_avd_config(current)
    return current

def sync_to_avd_config(cfg: dict):
    avd_dir = Path(cfg["avd_dir_path"])
    config_file = avd_dir / f"{cfg.get('avd_name', 'NovaPlayer_A14')}.avd" / "config.ini"
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
