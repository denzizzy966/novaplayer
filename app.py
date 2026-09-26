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
    def __init__(self, window=None):
        self.window = window
        self.adb = ADBManager()
        self.emulator = EmulatorManager()
        self.keymapper = Keymapper(self.adb)
        
        # In-memory status cache so UI calls never block or lag
        self._cached_status = {"state": "stopped", "ready": False, "details": "Ready to launch"}
        self._running_monitor = True
        
        # Start background polling thread (runs independently of WinForms UI thread)
        self._monitor_thread = threading.Thread(target=self._status_monitor_loop, daemon=True)
        self._monitor_thread.start()

    def set_window(self, window):
        self.window = window

    def _status_monitor_loop(self):
        while self._running_monitor:
            try:
                st = self.emulator.get_status()
                if st.get("ready", False):
                    st["fps"] = self.adb.get_current_fps()
                self._cached_status = st
                
                # Automatically enable keymapper when emulator is ready
                if st.get("ready", False) and not self.keymapper.is_active:
                    self.keymapper.start()
                elif not st.get("ready", False) and self.keymapper.is_active:
                    self.keymapper.stop()
            except Exception as e:
                print(f"[Monitor] Error: {e}")
            time.sleep(2)

    def go_back(self):
        threading.Thread(target=self.adb.go_back, daemon=True).start()
        return True

    def go_home(self):
        threading.Thread(target=self.adb.go_home, daemon=True).start()
        return True

    def go_recent_apps(self):
        threading.Thread(target=self.adb.go_recent_apps, daemon=True).start()
        return True

    def get_status(self):
        # Instant return from cache (0ms delay)
        return self._cached_status

    def start_emulator(self):
        def worker():
            self.emulator.start()
        threading.Thread(target=worker, daemon=True).start()
        self._cached_status = {"state": "booting", "ready": False, "details": "Starting engine..."}
        return {"success": True, "message": "Launching emulator engine..."}

    def stop_emulator(self):
        def worker():
            self.emulator.stop()
        threading.Thread(target=worker, daemon=True).start()
        self._cached_status = {"state": "stopped", "ready": False, "details": "Stopping engine..."}
        return {"success": True, "message": "Stopping Android emulator..."}

    def install_apk_dialog(self):
        if not self.window:
            return {"success": False, "message": "Window context not ready."}
        
        try:
            file_types = ('Android Packages (*.apk)', 'All files (*.*)')
            result = self.window.create_file_dialog(webview.OPEN_DIALOG, allow_multiple=False, file_types=file_types)
            if result and len(result) > 0:
                apk_path = result[0]
                return self.adb.install_apk(apk_path)
            return {"success": False, "message": "No file selected."}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def list_apps(self):
        return self.adb.list_installed_apps()

    def launch_app(self, package_name):
        return self.adb.launch_app(package_name)

    def take_screenshot(self):
        file_path = self.adb.take_screenshot()
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
        threading.Thread(target=self.adb.volume_up, daemon=True).start()
        return True

    def volume_down(self):
        threading.Thread(target=self.adb.volume_down, daemon=True).start()
        return True

    def rotate_screen(self, orientation):
        threading.Thread(target=self.adb.rotate_screen, args=(orientation,), daemon=True).start()
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
                target=self.adb.apply_device_spoofing,
                args=(res.get("device_profile", "asus_rog_8"), res.get("fps", 120)),
                daemon=True
            ).start()
        return res

    def get_keymap_profiles(self):
        return self.keymapper.list_profiles()

    def load_keymap(self, filename):
        return self.keymapper.load_profile(filename)

    def set_keymapper_enabled(self, enabled):
        self.keymapper.set_enabled(enabled)
        return True

    def cleanup(self):
        self._running_monitor = False
        self.keymapper.stop()

def main():
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
