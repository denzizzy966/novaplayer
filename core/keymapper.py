import json
import threading
import time
import win32gui
from pathlib import Path
from typing import Dict, Optional, Set
from pynput import keyboard
from .config import KEYMAPS_DIR, load_settings
from .adb import ADBManager

class Keymapper:
    def __init__(self, adb_manager: ADBManager):
        self.adb = adb_manager
        self.is_active = False
        self.current_profile: Dict = {}
        self.profile_name = "default.json"
        self.listener: Optional[keyboard.Listener] = None
        
        self.pressed_keys: Set[str] = set()
        self.last_dpad_time = 0
        self.lock = threading.Lock()
        
        self.load_profile(self.profile_name)

    def list_profiles(self) -> list:
        profiles = []
        for p in KEYMAPS_DIR.glob("*.json"):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    profiles.append({
                        "file": p.name,
                        "name": data.get("name", p.stem)
                    })
            except Exception:
                profiles.append({"file": p.name, "name": p.stem})
        return profiles

    def load_profile(self, filename: str) -> bool:
        path = KEYMAPS_DIR / filename
        if not path.exists():
            return False
        try:
            with open(path, "r", encoding="utf-8") as f:
                self.current_profile = json.load(f)
                self.profile_name = filename
                print(f"[Keymapper] Loaded profile: {self.current_profile.get('name')}")
                return True
        except Exception as e:
            print(f"[Keymapper] Error loading profile: {e}")
            return False

    def save_profile(self, filename: str, data: dict) -> bool:
        path = KEYMAPS_DIR / filename
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            self.current_profile = data
            self.profile_name = filename
            return True
        except Exception as e:
            print(f"[Keymapper] Error saving profile: {e}")
            return False

    def is_emulator_focused(self) -> bool:
        try:
            hwnd = win32gui.GetForegroundWindow()
            if not hwnd:
                return False
            title = win32gui.GetWindowText(hwnd)
            return "Android Emulator" in title or "NovaPlayer" in title or "5554" in title
        except Exception:
            return False

    def _normalize_key(self, key) -> Optional[str]:
        if isinstance(key, keyboard.KeyCode):
            return key.char.lower() if key.char else None
        elif isinstance(key, keyboard.Key):
            name = key.name.lower()
            return name
        return None

    def _handle_dpad(self):
        if not self.current_profile.get("dpad", {}).get("enabled", False):
            return
        
        now = time.time()
        # Debounce to prevent flooding adb
        if now - self.last_dpad_time < 0.12:
            return
        self.last_dpad_time = now

        dpad = self.current_profile["dpad"]
        cx = dpad.get("center_x", 260)
        cy = dpad.get("center_y", 680)
        r = dpad.get("radius", 100)

        dx, dy = 0, 0
        if 'w' in self.pressed_keys:
            dy -= 1
        if 's' in self.pressed_keys:
            dy += 1
        if 'a' in self.pressed_keys:
            dx -= 1
        if 'd' in self.pressed_keys:
            dx += 1

        if dx == 0 and dy == 0:
            return

        # Normalize diagonal
        if dx != 0 and dy != 0:
            target_x = int(cx + dx * r * 0.707)
            target_y = int(cy + dy * r * 0.707)
        else:
            target_x = int(cx + dx * r)
            target_y = int(cy + dy * r)

        threading.Thread(target=self.adb.swipe, args=(cx, cy, target_x, target_y, 180), daemon=True).start()

    def _on_press(self, key):
        if not self.is_active or not self.is_emulator_focused():
            return

        k = self._normalize_key(key)
        if not k:
            return

        with self.lock:
            self.pressed_keys.add(k)

        # Check D-Pad
        if k in ('w', 'a', 's', 'd'):
            self._handle_dpad()
            return

        # Check action keys
        keys_map = self.current_profile.get("keys", {})
        if k in keys_map:
            target = keys_map[k]
            x, y = target["x"], target["y"]
            threading.Thread(target=self.adb.tap, args=(x, y), daemon=True).start()

    def _on_release(self, key):
        k = self._normalize_key(key)
        if not k:
            return
        with self.lock:
            self.pressed_keys.discard(k)

    def start(self):
        if self.listener is not None:
            return
        self.is_active = True
        self.listener = keyboard.Listener(on_press=self._on_press, on_release=self._on_release)
        self.listener.start()
        print("[Keymapper] Active keyboard listener started.")

    def stop(self):
        self.is_active = False
        if self.listener:
            self.listener.stop()
            self.listener = None
            print("[Keymapper] Keyboard listener stopped.")

    def set_enabled(self, enabled: bool):
        self.is_active = enabled
