import subprocess
import time
from pathlib import Path
from typing import Optional, List, Dict
from .config import load_settings, SCREENSHOTS_DIR

class ADBManager:
    def __init__(self):
        self.config = load_settings()
        self.adb_path = self.config.get("adb_path", "adb")
        self.cached_device: Optional[str] = None

    def _run_cmd(self, args: List[str], timeout: int = 5) -> subprocess.CompletedProcess:
        adb_bin = self.adb_path
        if not Path(adb_bin).exists():
            import shutil
            which = shutil.which("adb")
            if which:
                adb_bin = which
            else:
                return subprocess.CompletedProcess(args, returncode=1, stdout="", stderr="ADB not found")

        cmd = [adb_bin] + args
        startupinfo = None
        creationflags = 0
        if hasattr(subprocess, 'STARTUPINFO'):
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        if hasattr(subprocess, 'CREATE_NO_WINDOW'):
            creationflags |= subprocess.CREATE_NO_WINDOW
            
        try:
            return subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                startupinfo=startupinfo,
                creationflags=creationflags,
                encoding="utf-8",
                errors="ignore"
            )
        except Exception as e:
            return subprocess.CompletedProcess(cmd, returncode=1, stdout="", stderr=str(e))

    def get_devices(self) -> List[str]:
        try:
            res = self._run_cmd(["devices"])
            lines = res.stdout.strip().splitlines()
            devices = []
            for line in lines[1:]:
                parts = line.strip().split()
                if len(parts) >= 2 and parts[1] == "device":
                    devices.append(parts[0])
            if devices:
                self.cached_device = devices[0]
            else:
                self.cached_device = None
            return devices
        except Exception as e:
            print(f"[ADB] Error listing devices: {e}")
            return []

    def get_target_device(self) -> Optional[str]:
        if self.cached_device:
            return self.cached_device
        devs = self.get_devices()
        return devs[0] if devs else None

    def is_boot_completed(self) -> bool:
        dev = self.get_target_device()
        if not dev:
            return False
        try:
            res = self._run_cmd(["-s", dev, "shell", "getprop", "sys.boot_completed"], timeout=5)
            return res.stdout.strip() == "1"
        except Exception:
            return False

    def get_system_info(self) -> Dict[str, str]:
        dev = self.get_target_device()
        if not dev:
            return {"status": "Disconnected"}
        try:
            version = self._run_cmd(["-s", dev, "shell", "getprop", "ro.build.version.release"]).stdout.strip()
            model = self._run_cmd(["-s", dev, "shell", "getprop", "ro.product.model"]).stdout.strip()
            abis = self._run_cmd(["-s", dev, "shell", "getprop", "ro.product.cpu.abilist"]).stdout.strip()
            api = self._run_cmd(["-s", dev, "shell", "getprop", "ro.build.version.sdk"]).stdout.strip()
            return {
                "status": "Connected",
                "device": dev,
                "android_version": version or "14",
                "api_level": api or "34",
                "model": model or "NovaPlayer Tablet",
                "supported_abis": abis or "x86_64,arm64-v8a"
            }
        except Exception as e:
            return {"status": "Error", "error": str(e)}

    def install_apk(self, apk_path: str) -> Dict[str, any]:
        dev = self.get_target_device()
        if not dev:
            return {"success": False, "message": "No active emulator found."}
        
        apk_file = Path(apk_path)
        if not apk_file.exists():
            return {"success": False, "message": f"File does not exist: {apk_path}"}
        
        try:
            print(f"[ADB] Installing APK: {apk_path} on {dev}...")
            # -r: replace existing application
            # -d: allow version code downgrade
            # -g: grant all runtime permissions
            res = self._run_cmd(["-s", dev, "install", "-r", "-d", "-g", str(apk_file)], timeout=180)
            if "Success" in res.stdout:
                return {"success": True, "message": f"Successfully installed {apk_file.name}!"}
            else:
                msg = res.stdout.strip() or res.stderr.strip()
                return {"success": False, "message": f"Install failed: {msg}"}
        except subprocess.TimeoutExpired:
            return {"success": False, "message": "Installation timed out."}
        except Exception as e:
            return {"success": False, "message": f"Installation error: {str(e)}"}

    def list_installed_apps(self) -> List[str]:
        dev = self.get_target_device()
        if not dev:
            return []
        try:
            res = self._run_cmd(["-s", dev, "shell", "pm", "list", "packages", "-3"])
            lines = res.stdout.strip().splitlines()
            apps = []
            for line in lines:
                if line.startswith("package:"):
                    apps.append(line.replace("package:", "").strip())
            return apps
        except Exception:
            return []

    def launch_app(self, package_name: str) -> bool:
        dev = self.get_target_device()
        if not dev:
            return False
        try:
            res = self._run_cmd(["-s", dev, "shell", "monkey", "-p", package_name, "-c", "android.intent.category.LAUNCHER", "1"])
            return res.returncode == 0
        except Exception:
            return False

    def tap(self, x: int, y: int):
        dev = self.get_target_device()
        if dev:
            self._run_cmd(["-s", dev, "shell", "input", "tap", str(x), str(y)], timeout=2)

    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration_ms: int = 150):
        dev = self.get_target_device()
        if dev:
            self._run_cmd(["-s", dev, "shell", "input", "swipe", str(x1), str(y1), str(x2), str(y2), str(duration_ms)], timeout=2)

    def keyevent(self, keycode: int):
        dev = self.get_target_device()
        if dev:
            self._run_cmd(["-s", dev, "shell", "input", "keyevent", str(keycode)], timeout=2)

    def volume_up(self):
        self.keyevent(24)

    def volume_down(self):
        self.keyevent(25)

    def volume_mute(self):
        self.keyevent(164)

    def rotate_screen(self, orientation: str = "landscape"):
        # 0: landscape, 1: portrait
        dev = self.get_target_device()
        if not dev:
            return
        rot_val = "0" if orientation == "landscape" else "1"
        self._run_cmd(["-s", dev, "shell", "settings", "put", "system", "accelerometer_rotation", "0"])
        self._run_cmd(["-s", dev, "shell", "settings", "put", "system", "user_rotation", rot_val])

    def take_screenshot(self) -> Optional[str]:
        dev = self.get_target_device()
        if not dev:
            return None
        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.png"
        filepath = SCREENSHOTS_DIR / filename
        
        try:
            cmd = [self.adb_path, "-s", dev, "exec-out", "screencap", "-p"]
            startupinfo = None
            if hasattr(subprocess, 'STARTUPINFO'):
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            with open(filepath, "wb") as f:
                res = subprocess.run(cmd, stdout=f, timeout=10, startupinfo=startupinfo)
            if res.returncode == 0 and filepath.stat().st_size > 1000:
                return str(filepath)
            return None
        except Exception as e:
            print(f"[ADB] Screenshot failed: {e}")
            return None

    def apply_device_spoofing(self, profile_key: str = "asus_rog_8", fps: int = 120):
        dev = self.get_target_device()
        if not dev:
            return
        from .config import DEVICE_PROFILES
        p = DEVICE_PROFILES.get(profile_key, DEVICE_PROFILES["asus_rog_8"])
        
        try:
            self._run_cmd(["-s", dev, "shell", "setprop", "ro.product.model", p["model"]])
            self._run_cmd(["-s", dev, "shell", "setprop", "ro.product.manufacturer", p["manufacturer"]])
            self._run_cmd(["-s", dev, "shell", "setprop", "ro.product.brand", p["brand"]])
            self._run_cmd(["-s", dev, "shell", "settings", "put", "system", "min_refresh_rate", f"{fps}.0"])
            self._run_cmd(["-s", dev, "shell", "settings", "put", "system", "peak_refresh_rate", f"{fps}.0"])
            print(f"[ADB] Applied spoofing profile: {p['name']} ({fps} FPS)")
        except Exception as e:
            print(f"[ADB] Error applying spoofing: {e}")

    def go_back(self):
        self.keyevent(4)

    def go_home(self):
        self.keyevent(3)

    def go_recent_apps(self):
        self.keyevent(187)

    def get_current_fps(self) -> int:
        dev = self.get_target_device()
        if not dev:
            return 0
        try:
            res = self._run_cmd(["-s", dev, "shell", "dumpsys", "SurfaceFlinger", "--latency"])
            lines = res.stdout.strip().splitlines()
            if lines and lines[0].isdigit():
                ns = int(lines[0])
                if ns > 0:
                    return int(round(1_000_000_000 / ns))
        except Exception:
            pass
        return 60


