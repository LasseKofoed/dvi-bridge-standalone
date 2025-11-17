# DVI Heatpump Raspberry Pi Installation Guide

## Prerequisites

-   Raspberry Pi OS Lite (64-bit)
-   USB connection to DVI Heatpump
-   MQTT broker (e.g., Home Assistant Mosquitto)

## 1. Install required packages

``` bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y git python3 python3-pip python3-venv
```

## 2. Clone the repository

``` bash
git clone https://github.com/ruteclrp/dvi-bridge-standalone.git
cd dvi-bridge-standalone
```

## 3. Create Python virtual environment

``` bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 4. Configure MQTT environment

Copy `.env.example` and edit:

``` bash
cp .env.example .env
nano .env
```

Example:

    MQTT_HOST=192.168.x.xxx
    MQTT_PORT=1883
    MQTT_USER=
    MQTT_PASS=

## 5. Find DVI USB serial device

``` bash
ls /dev/serial/by-id/
```

Use the full path shown in your system.

## 6. Update serial port in `bridge.py`

Edit the Modbus initialization line:

``` python
instrument = minimalmodbus.Instrument('/dev/serial/by-id/your-device-if00', 0x10)
```

## 7. Test manually

``` bash
source .venv/bin/activate
python bridge.py
```

You should see:

    Connected to MQTT broker

## 8. Install systemd service

``` bash
sudo cp systemd/bridge.service.example /etc/systemd/system/bridge.service
sudo nano /etc/systemd/system/bridge.service
```

Replace contents with:

    [Unit]
    Description=DVI Modbus-MQTT Bridge
    After=network.target
    Wants=network-online.target

    [Service]
    ExecStart=/home/<user>/dvi-bridge-standalone/.venv/bin/python /home/<user>/dvi-bridge-standalone/bridge.py
    WorkingDirectory=/home/<user>/dvi-bridge-standalone
    Restart=always
    EnvironmentFile=/home/<user>/dvi-bridge-standalone/.env
    User=<user>
    Group=<user>

    [Install]
    WantedBy=multi-user.target

Reload and enable:

``` bash
sudo systemctl daemon-reload
sudo systemctl enable bridge.service
sudo systemctl start bridge.service
```

## 9. Verify in Home Assistant

Home Assistant should auto-discover the device under MQTT devices.
