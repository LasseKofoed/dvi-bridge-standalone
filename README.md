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

## C. DVI LV‑X Heatpump Lovelace Card

The **DVI LV‑X Heatpump card** is a custom Lovelace card that shows:

- A schematic diagram of the LV‑X unit (using animated GIF overlays)
- Live temperatures (flow/return, buffer tanks, evaporator, HP/LP, outdoor)
- Status icons for compressor, circulation pump and defrost
- A **mode bar** with:
  - Central heating (CV) mode + night mode indicator (sun/moon/clock)
  - Hot water (VV) mode + schedule indicator
  - AUX / electric heater state indicator
  - Info chip with current EM23 power
- Inline controls to:
  - Turn CV / VV ON or OFF
  - Change CV night mode (Timer / Constant day / Constant night)
  - Change AUX heating mode (Off / Automatic / On)
  - Adjust VV setpoint (+/– 1°C)

### 1. File layout in Home Assistant

On your Home Assistant instance, place the files like this (inside your config directory):

```text
config/
  www/
    dvi-lv-x/
      dvi-lv-x-heatpump-card.js
      dvi.gif
      CV_on.gif
      CVflow_on.gif
      HP_on.gif
      COMP_on.gif
      (any other image assets)
```

> Note: The `/local/` path in Lovelace corresponds to `config/www/` on disk.

### 2. Add the Lovelace resource

Go to **Settings → Dashboards → (three dots) → Resources** and add a new resource:

- **URL:** `/local/dvi-lv-x/dvi-lv-x-heatpump-card.js`
- **Resource type:** `JavaScript Module`

Alternatively, if you manage Lovelace in YAML, add:

```yaml
resources:
  - url: /local/dvi-lv-x/dvi-lv-x-heatpump-card.js
    type: module
```

Restart Home Assistant or reload resources if needed.

### 3. Install and configure `browser_mod` (for popups)

The card can show **nice popups** (entities list) when you click the mode chips at the top. This is done via the [`browser_mod`](https://github.com/thomasloven/hass-browser_mod) integration.

1. Install via HACS:
   - Open **HACS → Integrations → Explore & download repositories**
   - Search for **“browser_mod”**
   - Install and restart Home Assistant
2. Add minimal config in `configuration.yaml` if required:

   ```yaml
   browser_mod:
   ```

3. Clear your browser cache / reload the page.

If `browser_mod` is not installed or not working, the card can still be used, but the popups will not open.

### 4. Example Lovelace card configuration

After the resource is added and the bridge is running, create a new Lovelace card (YAML) and use something like this:

```yaml
type: custom:dvi-lv-x-heatpump-card

cv_mode: select.dvi_lv12_cv_mode
vv_mode: select.dvi_lv12_vv_mode
cv_night: select.dvi_lv12_cv_night
vv_schedule: select.dvi_lv12_vv_schedule
aux_heating: select.dvi_lv12_tv_state
vv_setpoint: number.dvi_lv12_vv_setpoint

outdoor_temp: sensor.dvi_lv12_outdoor
curve_temp: sensor.dvi_lv12_curve_temp
storage_tank_cv: sensor.dvi_lv12_storage_tank_cv
storage_tank_vv: sensor.dvi_lv12_storage_tank_vv

evaporator_temp: sensor.dvi_lv12_evaporator
hp_temp: sensor.dvi_lv12_compressor_hp
lp_temp: sensor.dvi_lv12_compressor_lp
cv_forward_temp: sensor.dvi_lv12_cv_forward
cv_return_temp: sensor.dvi_lv12_cv_return

em23_power: sensor.dvi_lv12_em23_power
em23_energy: sensor.dvi_lv12_em23_energy

comp_icon: binary_sensor.dvi_lv12_soft_starter_compressor
cv_pump_icon: binary_sensor.dvi_lv12_circ_pump_cv
defrost_icon: binary_sensor.dvi_lv12_4_way_valve_defrost

# Popup contents for the four chips in the mode bar:
info_entities:
  - sensor.dvi_lv12_em23_energy
  - sensor.dvi_lv12_comp_hours
  - sensor.dvi_lv12_vv_hours
  - sensor.dvi_lv12_heating_hours

cv_entities:
  - select.dvi_lv12_cv_mode
  - number.dvi_lv12_cv_curve
  - select.dvi_lv12_tv_state
  - select.dvi_lv12_cv_night

vv_entities:
  - number.dvi_lv12_vv_setpoint
  - select.dvi_lv12_vv_mode
  - input_select.varmtvandsur

aux_entities:
  - select.dvi_lv12_tv_state
  - binary_sensor.dvi_lv12_heating_element
```

> Adjust entity IDs to match what your MQTT auto‑discovery created. The ones above follow a typical naming scheme based on the bridge configuration.

### 5. Card behaviour summary

- **Top “mode bar” chips:**
  - **Info** – opens a popup with energy + runtime entities, shows current EM23 power in the chip.
  - **CV** – colour reflects `cv_mode` and `cv_night` (sun / moon / clock).
  - **VV** – colour and small icon reflect `vv_mode` and `vv_schedule`.
  - **AUX** – shows status of the electric heater (dangerous/expensive mode).
- **Diagram overlay:**
  - Compressor + HP animated GIFs when the compressor coil is ON.
  - CV pump + CV flow GIFs when the circulation pump coil is ON.
  - Defrost snowflake icon with orange colour when defrost coil is ON.
  - Temperatures are written directly on the diagram near the physical location.
- **Bottom grid:**
  - Shows key modes and temperatures.
  - Provides direct buttons for:
    - CV mode ON/OFF
    - VV mode ON/OFF
    - CV night mode (Timer / Day / Night)
    - AUX heating mode (Off / Automatic / On)
    - VV setpoint –/+ (updates via the corresponding `number` entity).

---

## D. HACS Distribution (Frontend Card)

This project is prepared for HACS as a **frontend** custom repository. The `hacs.json` file in the root declares:

```json
{
  "name": "LV12 Heatpump Card",
  "content_in_root": true,
  "render_readme": true
}
```

With this structure (bridge + card in one repo):

```text
dvi-bridge-standalone/
  bridge.py
  systemd/
  .env.example
  ...
  dvi-lv-x-heatpump-card.js
  dvi-lv-x/
    dvi.gif
    CV_on.gif
    CVflow_on.gif
    HP_on.gif
    COMP_on.gif
  README.md   (this file)
  hacs.json
```

you can:

1. Publish the repository on GitHub.
2. In Home Assistant → HACS → Frontend → **Custom repositories**, add:
   - **URL:** your GitHub repo URL
   - **Category:** `Lovelace`
3. Install **“LV12 Heatpump Card”** from HACS and HACS will place the JS file under `/www/community/...` for you.

When using HACS, the Lovelace resource URL will typically be something like:

```yaml
- url: /hacsfiles/lv12-heatpump-card/dvi-lv-x-heatpump-card.js
  type: module
```

(The exact path depends on the repository name and HACS slug.)

---

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
