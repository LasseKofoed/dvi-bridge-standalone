# DVI LV‑X Heatpump – Bridge & Home Assistant Card

This document describes both:

1. **DVI Modbus‑MQTT bridge** for Raspberry Pi (talks Modbus RTU with the heatpump and publishes data via MQTT with Home Assistant auto‑discovery).
2. **DVI LV‑X Heatpump Lovelace card** – a custom frontend card that visualises the heatpump diagram, modes and temperatures and lets you change key settings directly from Home Assistant.

The repository is designed so both parts can live in the same project (bridge + card) and be distributed via HACS as a frontend card.

---

## A. Raspberry Pi Modbus‑MQTT Bridge

### Prerequisites

- Raspberry Pi OS Lite (64‑bit) – when you install, **set the default username to `dviha`** to match the paths and examples in this guide.
- USB connection to DVI LV‑X heatpump
- MQTT broker (e.g. the Mosquitto broker add‑on in Home Assistant)
- Git + Python 3.9+ on the Pi

### 1. Install required packages on the Pi

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y git python3 python3-pip python3-venv
```

### 2. Clone the repository

```bash
cd /home/dviha
git clone https://github.com/<your-org-or-user>/dvi-bridge-standalone.git
cd dvi-bridge-standalone
```

### 3. Create the Python virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure MQTT environment

Copy the example environment file and edit it with your broker settings:

```bash
cp .env.example .env
nano .env
```

Example `.env`:

```ini
MQTT_HOST=192.168.x.xxx
MQTT_PORT=1883
MQTT_USER=
MQTT_PASS=
```

Leave `MQTT_USER` / `MQTT_PASS` empty if your broker does not require authentication.

### 5. Test the bridge manually

```bash
source .venv/bin/activate
python bridge.py
```

You should see something like:

```text
✅ Connected to MQTT broker
```

If everything is OK, the bridge will start polling the heatpump and publish JSON payloads on the topic:

```text
dvi/measurement
```

Home Assistant will also receive MQTT discovery messages so entities are created automatically.

### 7. Install the systemd service (auto‑start on boot)

Copy the example service file and edit it:

```bash
sudo cp systemd/bridge.service.example /etc/systemd/system/bridge.service
sudo nano /etc/systemd/system/bridge.service
```

Replace the contents with:

```ini
[Unit]
Description=DVI Modbus-MQTT Bridge
After=network.target
Wants=network-online.target

[Service]
ExecStart=/home/dviha/dvi-bridge-standalone/.venv/bin/python /home/dviha/dvi-bridge-standalone/bridge.py
WorkingDirectory=/home/dviha/dvi-bridge-standalone
Restart=always
EnvironmentFile=/home/dviha/dvi-bridge-standalone/.env
User=dviha
Group=dviha

[Install]
WantedBy=multi-user.target
```

If you chose a different username than `dviha` when installing Raspberry Pi OS, remember to update the username in all the paths and examples in this guide.

Reload systemd and enable the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable bridge.service
sudo systemctl start bridge.service
```

You can check the status with:

```bash
sudo systemctl status bridge.service
```

When it is **active (running)** and your USB connection + Modbus wiring are correct, the heatpump data should be visible in Home Assistant via MQTT discovery.

---

## B. Home Assistant MQTT Entities

The bridge publishes a single JSON payload to:

```text
dvi/measurement
```

Example payload:

```json
{
  "coils": {
    "Soft starter Compressor": 1,
    "Circ. pump CV": 1
  },
  "input_registers": {
    "Outdoor": 4.6,
    "Storage tank CV": 36.9,
    "Storage tank VV": 52.9
  },
  "write_registers": {
    "cv_mode": 1,
    "vv_mode": 1,
    "vv_setpoint": 55,
    "curve_temp": 36.7
  }
}
```

On startup the bridge also sends Home Assistant MQTT discovery messages for:

- Temperature sensors
- Binary sensors (coils)
- `number`/`select` entities for writable FC06 registers (modes, setpoints, etc.)

As long as MQTT discovery is enabled in Home Assistant, all entities will appear automatically and are ready to be used by the custom Lovelace card.

---

## C. 

# DVI LV‑X Heatpump Lovelace Card

The **DVI LV‑X Heatpump card** provides a full visual diagram of your LV‑X heatpump, live temperatures, compressor/pump status, mode controls, animated overlays, and popup panels for detailed settings.

It is fully compatible with HACS and includes a visual configuration editor.

---

## 🔧 Install via HACS

### 1. Open HACS  
Home Assistant → **HACS** → *Frontend* → ⋮ (menu) → **Custom repositories**

### 2. Add the repository  
- **URL:**  
  `https://github.com/LasseKofoed/dvi-bridge-standalone`
- **Category:** `Dashboard`

Click **Add**.

### 3. Install the card  
Go to **HACS → Frontend**, find:

**“DVI LV‑X Heatpump Card”**

Click **Download**.  
HACS installs everything automatically into:

```
/config/www/community/dvi-bridge-standalone/
```

### 4. Reload browser  
Press **Ctrl+F5** (or full refresh on mobile) to ensure the new card files load.

---

## 🧩 Adding the card in Lovelace

1. Open any dashboard  
2. Click **Edit dashboard**  
3. Click **Add card**  
4. Select **DVI LV‑X Heatpump Card**

A full configuration UI appears.  
From here you can visually pick all entities discovered via MQTT:

- CV mode  
- VV mode  
- CV night mode  
- VV schedule  
- AUX mode  
- All temperature sensors  
- Pump/compressor/defrost binary sensors  
- Entities shown in the popup panels (Info / CV / VV / AUX)

No YAML needed — unless you prefer YAML manually.

---

## 📘 Requirements

### Optional (recommended)
**browser_mod** (installed from HACS)  
Enables beautiful popup panels when clicking the top mode chips.

Add to configuration if required:

```yaml
browser_mod:
```

---

## 🎨 Features

- Animated LV‑X heating circuit diagram  
- Real‑time temperatures drawn directly in the diagram  
- Live compressor, CV pump and defrost icons  
- Mode bar with:
  - CV mode + sun/moon/clock based on night mode  
  - VV mode + schedule indicator  
  - AUX heating status  
  - Info chip showing EM23 power  
- Popups for Info, CV, VV, AUX  
- Buttons for:
  - CV/VV ON/OFF  
  - CV night mode (Timer / Day / Night)  
  - AUX modes (Off / Auto / On)  
  - VV setpoint ±1°C  
- Fully HACS‑compatible asset loading (JS + images auto‑loaded)

---

## 🛠 Troubleshooting

**Card does not appear in Add Card menu?**  
- Clear cache (Ctrl+F5)  
- Check **Settings → Dashboards → Resources**

**Popups not opening?**  
- Install `browser_mod`  
- Restart Home Assistant

**Entity not found?**  
- Check MQTT entity names: *Settings → Devices & Services → MQTT*

---

## 📄 License
MIT License


## E. Energy Dashboard (optional)

Home Assistant’s **Energy dashboard** can be extended with a sensor that reports the heatpump’s electricity consumption and (optionally) generated heat energy.

With the EM23 meter you already have:

- `sensor.dvi_lv12_em23_power` (instant kW)
- `sensor.dvi_lv12_em23_energy` (total kWh, `state_class: total_increasing`)

To use this in the Energy dashboard:

1. Make sure `sensor.dvi_lv12_em23_energy` has:
   - `device_class: energy`
   - `unit_of_measurement: kWh`
   - `state_class: total_increasing`  
   (the bridge already publishes these via discovery)
2. Go to **Settings → Dashboards → Energy → Electricity grid → Setup** and select `sensor.dvi_lv12_em23_energy` as a consumption source.

If you later add a calculated **heat output** sensor (COP × electric energy), you can add that as a custom energy source as well.

---

## F. Notes & Troubleshooting

- If the card does not load, open the browser console and check for 404 errors on the JS file or images.
- If popups do not appear when clicking the chips:
  - Confirm that `browser_mod` is installed and loaded.
  - Make sure your config includes the `browser_mod:` section (if required by your version).
- If some entities show as `entity not found`, open **Settings → Devices & Services → MQTT** and verify which entity IDs were created, then update the Lovelace YAML accordingly.
- If Modbus values look wrong (e.g. very large numbers instead of negative temperatures), double‑check the Modbus register format and scaling in `bridge.py`.
