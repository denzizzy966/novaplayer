import subprocess
import time
import win32gui
import win32process
from typing import Optional
from .config import load_settings
from .adb import ADBManager

class EmulatorManager:
    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self.adb = ADBManager()
        self.hwnd: Optional[int] = None
        self._cached_sys_info = None

    def start(self) -> dict:
        if self.is_running():
            return {"success": False, "message": "Emulator is already running."}

        cfg = load_settings()
        emulator_exe = cfg.get("emulator_path", r"D:\Android\Sdk\emulator\emulator.exe")
        avd_name = cfg.get("avd_name", "NovaPlayer_A14")
        ram_mb = cfg.get("ram_mb", 4096)
        cores = cfg.get("cores", 4)
        width = cfg.get("width", 1600)
        height = cfg.get("height", 900)
        gpu_mode = cfg.get("gpu_mode", "host")

        cmd = [
            emulator_exe,
            "-avd", avd_name,
            "-gpu", gpu_mode,
            "-memory", str(ram_mb),
            "-cores", str(cores),
            "-skin", f"{width}x{height}",
            "-no-boot-anim",
            "-netdelay", "none",
            "-netspeed", "full"
        ]

        flags = 0
        if hasattr(subprocess, 'DETACHED_PROCESS') and hasattr(subprocess, 'CREATE_NEW_PROCESS_GROUP'):
            flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP

        print(f"[Emulator] Launching with command: {' '.join(cmd)}")
        try:
            self.process = subprocess.Popen(
                cmd,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=flags,
                close_fds=True
            )
            return {"success": True, "message": "Emulator engine launched.", "pid": self.process.pid}
        except Exception as e:
            print(f"[Emulator] Failed to start: {e}")
            return {"success": False, "message": f"Failed to start emulator: {str(e)}"}

    def is_running(self) -> bool:
        if self.process and self.process.poll() is None:
            return True
        # Also check if any emulator devices exist in ADB
        devs = self.adb.get_devices()
        return len(devs) > 0

    def stop(self) -> dict:
        try:
            # First try graceful ADB emu kill
            dev = self.adb.get_target_device()
            if dev:
                self.adb._run_cmd(["-s", dev, "emu", "kill"], timeout=5)
            
            # If process handle exists, terminate
            if self.process and self.process.poll() is None:
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.kill()
            
            # Double check with taskkill for any lingering qemu-system-x86_64
            subprocess.run(["taskkill", "/F", "/IM", "qemu-system-x86_64.exe"], capture_output=True)
            self.process = None
            self.hwnd = None
            return {"success": True, "message": "Emulator stopped successfully."}
        except Exception as e:
            return {"success": False, "message": f"Error stopping emulator: {str(e)}"}

    def get_status(self) -> dict:
        running = self.is_running()
        if not running:
            self._cached_sys_info = None
            return {"state": "stopped", "ready": False, "details": "Emulator is powered off."}
        
        booted = self.adb.is_boot_completed()
        if booted:
            if not self._cached_sys_info:
                self._cached_sys_info = self.adb.get_system_info()
            return {
                "state": "running",
                "ready": True,
                "details": f"Android {self._cached_sys_info.get('android_version', '14')} Ready",
                "info": self._cached_sys_info
            }
        else:
            return {"state": "booting", "ready": False, "details": "Booting Android 14 OS..."}

    def find_window(self) -> Optional[int]:
        found_hwnds = []

        def enum_windows_callback(hwnd, extra):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                # Google QEMU window typically has title: "Android Emulator - NovaPlayer_A14:5554" or "NovaPlayer"
                if "Android Emulator" in title or "NovaPlayer" in title or "5554" in title:
                    found_hwnds.append((hwnd, title))
            return True

        win32gui.EnumWindows(enum_windows_callback, None)
        if found_hwnds:
            self.hwnd = found_hwnds[0][0]
            return self.hwnd
        return None
