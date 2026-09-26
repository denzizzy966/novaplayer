import os
import sys
import threading
import time
from pathlib import Path
import webview

# Handle stdout/stderr for frozen/noconsole mode
if getattr(sys, 'frozen', False) or sys.stdout is None:
    try:
        log_path = Path(sys.executable).parent / "novaplayer.log" if getattr(sys, 'frozen', False) else Path(__file__).parent / "novaplayer.log"
        log_file = open(log_path, "a", encoding="utf-8", buffering=1)
        sys.stdout = log_file
        sys.stderr = log_file
    except Exception:
        sys.stdout = open(os.devnull, "w")
        sys.stderr = open(os.devnull, "w")

from core.config import load_settings, save_settings, SCREENSHOTS_DIR
from core.adb import ADBManager
from core.emulator import EmulatorManager
from core.keymapper import Keymapper

class EmuApi:
    # NOTE: pywebview walks every PUBLIC attribute of this object (recursively) when it
    # injects window.pywebview.api. Any attribute that is not meant to be called from JS
    # (especially the webview Window itself) MUST be prefixed with "_" or pywebview will
    # touch window.dom.* properties on the UI thread and freeze the app ("Not Responding").
    def __init__(self, window=None):
        self._window = window
        self._adb = ADBManager()
        self._emulator = EmulatorManager()
        self._keymapper = Keymapper(self._adb)
        
        # In-memory status cache so UI calls never block or lag
        self._cached_status = {"state": "stopped", "ready": False, "details": "Ready to launch"}
        self._last_error = None  # last emulator launch failure, surfaced to the UI via get_status()
        self._running_monitor = True
        
        # Start background polling thread (runs independently of WinForms UI thread)
        self._monitor_thread = threading.Thread(target=self._status_monitor_loop, daemon=True)
        self._monitor_thread.start()

    def set_window(self, window):
        self._window = window

    def _status_monitor_loop(self):
        while self._running_monitor:
            try:
                st = self._emulator.get_status()
                if st.get("ready", False):
                    st["fps"] = self._adb.get_current_fps()
                if self._last_error and not st.get("ready", False):
                    st["error"] = self._last_error
                self._cached_status = st
                
                # Automatically enable keymapper when emulator is ready
                if st.get("ready", False) and not self._keymapper.is_active:
                    self._keymapper.start()
                elif not st.get("ready", False) and self._keymapper.is_active:
                    self._keymapper.stop()
            except Exception as e:
                print(f"[Monitor] Error: {e}")
            time.sleep(2)

    def go_back(self):
        threading.Thread(target=self._adb.go_back, daemon=True).start()
        return True

    def go_home(self):
        threading.Thread(target=self._adb.go_home, daemon=True).start()
        return True

    def go_recent_apps(self):
        threading.Thread(target=self._adb.go_recent_apps, daemon=True).start()
        return True

    def get_status(self):
        # Instant return from cache (0ms delay)
        return self._cached_status

    def start_emulator(self):
        def worker():
            try:
                res = self._emulator.start()
            except Exception as e:
                res = {"success": False, "message": f"Unexpected error while starting emulator: {e}"}
            if not res.get("success", False):
                msg = res.get("message", "Unknown error")
                print(f"[Emulator] Launch failed: {msg}")
                self._last_error = msg
                self._cached_status = {"state": "stopped", "ready": False, "details": msg, "error": msg}
            else:
                print(f"[Emulator] {res.get('message', 'Launched')}")
        self._last_error = None
        threading.Thread(target=worker, daemon=True).start()
        self._cached_status = {"state": "booting", "ready": False, "details": "Starting engine..."}
        return {"success": True, "message": "Launching emulator engine..."}

    def stop_emulator(self):
        def worker():
            self._emulator.stop()
        threading.Thread(target=worker, daemon=True).start()
        self._cached_status = {"state": "stopped", "ready": False, "details": "Stopping engine..."}
        return {"success": True, "message": "Stopping Android emulator..."}

    def install_apk_dialog(self):
        if not self._window:
            return {"success": False, "message": "Window context not ready."}
        
        try:
            file_types = ('Android Packages (*.apk)', 'All files (*.*)')
            result = self._window.create_file_dialog(webview.OPEN_DIALOG, allow_multiple=False, file_types=file_types)
            if result and len(result) > 0:
                apk_path = result[0]
                return self._adb.install_apk(apk_path)
            return {"success": False, "message": "No file selected."}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def list_apps(self):
        return self._adb.list_installed_apps()

    def launch_app(self, package_name):
        return self._adb.launch_app(package_name)

    def take_screenshot(self):
        file_path = self._adb.take_screenshot()
        if file_path:
            filename = Path(file_path).name
            return {"success": True, "filename": filename, "path": file_path}
        return {"success": False, "message": "Failed to capture screen. Ensure emulator is running."}

    def open_screenshots_folder(self):
        try:
            os.startfile(str(SCREENSHOTS_DIR))
            return True
        except Exception as e:
            print(f"Error opening folder: {e}")
            return False

    def volume_up(self):
        threading.Thread(target=self._adb.volume_up, daemon=True).start()
        return True

    def volume_down(self):
        threading.Thread(target=self._adb.volume_down, daemon=True).start()
        return True

    def rotate_screen(self, orientation):
        threading.Thread(target=self._adb.rotate_screen, args=(orientation,), daemon=True).start()
        return True

    def get_settings(self):
        return load_settings()

    def get_device_profiles(self):
        from core.config import DEVICE_PROFILES
        return [{"id": k, "name": v["name"]} for k, v in DEVICE_PROFILES.items()]

    def save_settings(self, new_settings):
        res = save_settings(new_settings)
        # Apply spoofing immediately if running
        if self._cached_status.get("ready", False):
            threading.Thread(
                target=self._adb.apply_device_spoofing,
                args=(res.get("device_profile", "asus_rog_8"), res.get("fps", 120)),
                daemon=True
            ).start()
        return res

    def get_keymap_profiles(self):
        return self._keymapper.list_profiles()

    def load_keymap(self, filename):
        return self._keymapper.load_profile(filename)

    def set_keymapper_enabled(self, enabled):
        self._keymapper.set_enabled(enabled)
        return True

    def cleanup(self):
        self._running_monitor = False
        self._keymapper.stop()

def check_webview2() -> bool:
    if sys.platform != "win32":
        return True
    try:
        import winreg
        keys = [
            (winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}'),
            (winreg.HKEY_CURRENT_USER, r'Software\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}'),
            (winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}')
        ]
        for root, subkey in keys:
            try:
                with winreg.OpenKey(root, subkey) as k:
                    val, _ = winreg.QueryValueEx(k, 'pv')
                    if val:
                        return True
            except Exception:
                pass
    except Exception:
        pass
    return False

def main():
    if not check_webview2():
        import ctypes
        import webbrowser
        msg = (
            "NovaPlayer requires 'Microsoft Edge WebView2 Runtime' to render the modern gaming interface.\n\n"
            "Without WebView2, Windows falls back to legacy Internet Explorer which causes freezing.\n\n"
            "Would you like to open the official Microsoft download page to install it now?"
        )
        res = ctypes.windll.user32.MessageBoxW(0, msg, "NovaPlayer - Runtime Required", 0x00000004 | 0x00000030)
        if res == 6:
            webbrowser.open("https://go.microsoft.com/fwlink/p/?LinkId=2124703")
        return

    if getattr(sys, 'frozen', False):
        bundle_dir = Path(getattr(sys, '_MEIPASS', Path(sys.executable).parent)).resolve()
        if (bundle_dir / "ui" / "index.html").exists():
            ui_dir = bundle_dir / "ui"
        else:
            ui_dir = Path(sys.executable).resolve().parent / "ui"
    else:
        ui_dir = Path(__file__).resolve().parent / "ui"
        
    html_file = ui_dir / "index.html"
    css_file = ui_dir / "style.css"
    js_file = ui_dir / "app.js"
    
    html_content = html_file.read_text(encoding="utf-8")
    if css_file.exists():
        css_content = css_file.read_text(encoding="utf-8")
        html_content = html_content.replace('<link rel="stylesheet" href="style.css">', f"<style>\n{css_content}\n</style>")
    if js_file.exists():
        js_content = js_file.read_text(encoding="utf-8")
        html_content = html_content.replace('<script src="app.js"></script>', f"<script>\n{js_content}\n</script>")

    api = EmuApi()
    window = webview.create_window(
        title="NovaPlayer - Android 14 Gaming Suite",
        html=html_content,
        js_api=api,
        width=1020,
        height=680,
        resizable=True,
        min_size=(900, 600),
        background_color="#0b0e14"
    )
    api.set_window(window)
    
    try:
        try:
            webview.start(gui='edgechromium', debug=False)
        except Exception:
            webview.start(debug=False)
    finally:
        api.cleanup()

if __name__ == "__main__":
    main()
