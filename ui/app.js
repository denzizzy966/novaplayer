let currentStatus = { state: "stopped", ready: false };
let isStartingOrStopping = false;

// Tab Switching
document.querySelectorAll(".nav-tab").forEach(tab => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".nav-tab").forEach(t => t.classList.remove("active"));
    document.querySelectorAll(".tab-pane").forEach(p => p.classList.remove("active"));
    
    tab.classList.add("active");
    const targetId = `tab-${tab.dataset.tab}`;
    const targetPane = document.getElementById(targetId);
    if (targetPane) targetPane.classList.add("active");
  });
});

// Toast notification
function showToast(message, duration = 3000) {
  const toast = document.getElementById("toast");
  toast.textContent = message;
  toast.classList.remove("hidden");
  setTimeout(() => {
    toast.classList.add("hidden");
  }, duration);
}

// Update UI with status
function updateStatusUI(status) {
  currentStatus = status;
  const pill = document.getElementById("statusPill");
  const text = document.getElementById("statusText");
  const btn = document.getElementById("btnLaunch");
  const btnText = document.getElementById("btnLaunchText");
  const fpsPill = document.getElementById("fpsPill");
  const fpsValue = document.getElementById("fpsValue");

  pill.className = "status-pill";

  if (status.state === "stopped") {
    pill.classList.add("status-stopped");
    text.textContent = "Offline";
    btn.className = "btn btn-primary btn-glow";
    btnText.textContent = "Launch Emulator";
    btn.disabled = false;
    if (fpsPill) fpsPill.classList.add("hidden");
  } else if (status.state === "booting") {
    pill.classList.add("status-booting");
    text.textContent = status.details || "Booting Android 14...";
    btn.className = "btn btn-outline";
    btnText.textContent = "Starting Engine...";
    btn.disabled = true;
    if (fpsPill) fpsPill.classList.add("hidden");
  } else if (status.state === "running") {
    pill.classList.add("status-running");
    text.textContent = status.details || "Android 14 Ready";
    btn.className = "btn btn-outline";
    btnText.textContent = "Emulator Running";
    btn.disabled = false;
    if (fpsPill) {
      fpsPill.classList.remove("hidden");
      if (status.fps) fpsValue.textContent = String(status.fps);
    }
  }
}

// Android Navigation Buttons
async function goBack() {
  if (window.pywebview) {
    await window.pywebview.api.go_back();
    showToast("◀️ Back");
  }
}

async function goHome() {
  if (window.pywebview) {
    await window.pywebview.api.go_home();
    showToast("⭕ Home");
  }
}

async function goRecentApps() {
  if (window.pywebview) {
    await window.pywebview.api.go_recent_apps();
    showToast("◽ Recent Apps");
  }
}

// Poll status
async function pollStatus() {
  if (window.pywebview && window.pywebview.api) {
    try {
      const status = await window.pywebview.api.get_status();
      updateStatusUI(status);
      if (status.ready && document.querySelectorAll(".app-card:not(.empty-state)").length === 0) {
        loadInstalledApps();
      }
    } catch (e) {
      console.error("Error polling status:", e);
    }
  }
}

// Toggle emulator start/stop
async function toggleEmulator() {
  if (!window.pywebview) return;
  if (currentStatus.state === "stopped") {
    showToast("Launching Android 14 with Direct GPU Host mode...");
    const res = await window.pywebview.api.start_emulator();
    if (!res.success) {
      showToast(res.message);
    }
  } else {
    showToast("Emulator is already running.");
  }
}

async function stopEmulator() {
  if (!window.pywebview) return;
  showToast("Stopping Android emulator...");
  const res = await window.pywebview.api.stop_emulator();
  showToast(res.message);
  pollStatus();
}

// APK Install
async function triggerApkInstall() {
  if (!window.pywebview) return;
  showToast("Opening APK file selector...");
  const res = await window.pywebview.api.install_apk_dialog();
  if (res) {
    showToast(res.message, 4000);
    if (res.success) {
      setTimeout(loadInstalledApps, 2000);
    }
  }
}

// Installed Apps
async function loadInstalledApps() {
  if (!window.pywebview) return;
  const container = document.getElementById("appsList");
  try {
    const apps = await window.pywebview.api.list_apps();
    if (!apps || apps.length === 0) {
      container.innerHTML = `
        <div class="app-card empty-state">
          <span>No third-party apps installed yet. Click "+ APK" on the sidebar to install games!</span>
        </div>`;
      return;
    }
    
    container.innerHTML = "";
    apps.forEach(pkg => {
      const card = document.createElement("div");
      card.className = "app-card";
      const shortName = pkg.split('.').pop();
      card.innerHTML = `
        <div class="app-icon-dummy">${shortName.substring(0, 2).toUpperCase()}</div>
        <div class="app-name" title="${pkg}">${shortName}</div>
      `;
      card.onclick = async () => {
        showToast(`Launching ${shortName}...`);
        await window.pywebview.api.launch_app(pkg);
      };
      container.appendChild(card);
    });
  } catch (e) {
    console.error("Error loading apps:", e);
  }
}

// Screenshots
async function takeScreenshot() {
  if (!window.pywebview) return;
  showToast("Capturing screen...");
  const res = await window.pywebview.api.take_screenshot();
  if (res.success) {
    showToast(`📸 Screenshot saved: ${res.filename}`);
  } else {
    showToast(`Failed: ${res.message}`);
  }
}

async function openScreenshots() {
  if (!window.pywebview) return;
  await window.pywebview.api.open_screenshots_folder();
}

// Volume & Orientation
async function volumeUp() {
  if (window.pywebview) await window.pywebview.api.volume_up();
}

async function volumeDown() {
  if (window.pywebview) await window.pywebview.api.volume_down();
}

let currentOrientation = "landscape";
async function rotateScreen() {
  if (!window.pywebview) return;
  currentOrientation = currentOrientation === "landscape" ? "portrait" : "landscape";
  showToast(`Rotating screen to ${currentOrientation}...`);
  await window.pywebview.api.rotate_screen(currentOrientation);
}

// Keymapper Profiles
async function loadKeymapProfiles() {
  if (!window.pywebview) return;
  const profiles = await window.pywebview.api.get_keymap_profiles();
  const select = document.getElementById("keymapProfileSelect");
  select.innerHTML = "";
  profiles.forEach(p => {
    const opt = document.createElement("option");
    opt.value = p.file;
    opt.textContent = p.name;
    select.appendChild(opt);
  });
}

async function switchKeymapProfile() {
  const select = document.getElementById("keymapProfileSelect");
  const file = select.value;
  await window.pywebview.api.load_keymap(file);
  showToast(`Loaded keymap: ${file}`);
}

async function toggleKeymapperActive() {
  const chk = document.getElementById("keymapperSwitch");
  await window.pywebview.api.set_keymapper_enabled(chk.checked);
  showToast(chk.checked ? "Keymapper activated" : "Keymapper paused");
}

// Settings
async function loadSettingsUI() {
  if (!window.pywebview) return;
  const cfg = await window.pywebview.api.get_settings();
  if (cfg) {
    document.getElementById("cfgRam").value = String(cfg.ram_mb || 4096);
    document.getElementById("cfgCores").value = String(cfg.cores || 4);
    document.getElementById("cfgRes").value = `${cfg.width || 1600}x${cfg.height || 900}`;
    document.getElementById("cfgGpu").value = cfg.gpu_mode || "host";
    if (document.getElementById("cfgDevice") && cfg.device_profile) {
      document.getElementById("cfgDevice").value = cfg.device_profile;
    }
    if (document.getElementById("cfgFps") && cfg.fps) {
      document.getElementById("cfgFps").value = String(cfg.fps);
    }
    if (document.getElementById("cfgSdk") && cfg.sdk_path) {
      document.getElementById("cfgSdk").value = cfg.sdk_path;
    }
    
    document.getElementById("specRam").textContent = `${cfg.ram_mb || 4096} MB RAM`;
    document.getElementById("specCpu").textContent = `${cfg.cores || 4} Cores`;
    document.getElementById("specRes").textContent = `${cfg.width || 1600}×${cfg.height || 900} Landscape`;
  }
}

async function saveSettings() {
  if (!window.pywebview) return;
  const [w, h] = document.getElementById("cfgRes").value.split("x").map(Number);
  const data = {
    ram_mb: Number(document.getElementById("cfgRam").value),
    cores: Number(document.getElementById("cfgCores").value),
    width: w,
    height: h,
    gpu_mode: document.getElementById("cfgGpu").value,
    device_profile: document.getElementById("cfgDevice").value,
    fps: Number(document.getElementById("cfgFps").value)
  };
  const sdkVal = document.getElementById("cfgSdk").value.trim();
  if (sdkVal) {
    data.sdk_path = sdkVal;
  }
  await window.pywebview.api.save_settings(data);
  showToast("Settings & Device Identity applied!");
  loadSettingsUI();
}

// Init when pywebview is ready
window.addEventListener("pywebviewready", async () => {
  try {
    await pollStatus();
    await loadSettingsUI();
    await loadKeymapProfiles();
  } catch (err) {
    console.error("Init error:", err);
  }
  setInterval(pollStatus, 2500);
});
