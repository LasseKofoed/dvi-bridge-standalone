# -*- coding: utf-8 -*-
"""
Læser FABNR/pumpid direkte fra DVI'en via modbus_tk (som i det gamle projekt)
og skriver resultaterne til:
  - ./config.cfg  (JSON med feltet "pumpid")
  - ./fabnr.cfg   (ren tekst med pumpid)
  - ./.env        (linje FABNR=<pumpid>)
Kør dette script på en Pi, der er direkte forbundet til DVI'en (uden STM32-bridge).
"""

import json
import os
import sys
import time

import serial
from modbus_tk import modbus_rtu

# ---- Konfiguration ---------------------------------------------------------

# TTY til DVI'en - juster hvis nødvendigt
MODBUS_PORT = "/dev/ttyACM0"  # samme som ModbusPort i settings.py
SLAVE_ADDR = 16
FUNCTION_CODE = 6
FABNR_ADDR = 153  # register 153
QUANTITY = 1

# Filer placeres i samme dir som dette script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.cfg")
FABNR_PATH = os.path.join(BASE_DIR, "fabnr.cfg")
ENV_PATH = os.path.join(BASE_DIR, ".env")

# ---------------------------------------------------------------------------


def open_master():
    ser = serial.Serial(
        port=MODBUS_PORT,
        baudrate=9600,
        bytesize=8,
        parity="N",
        stopbits=1,
        xonxoff=0,
    )
    master = modbus_rtu.RtuMaster(ser, interchar_multiplier=20, interframe_multiplier=40)
    master.set_timeout(2.0)
    return master


def read_fabnr_raw(master):
    """
    Genskaber den gamle modbusopen(16, 6, 153, 1) med data_format="BBBBBB".
    Returnerer en sekvens med mindst 6 elementer, hvor index 3,4,5 er FABNR-bytes.
    """
    out = master.execute(
        SLAVE_ADDR,
        FUNCTION_CODE,
        FABNR_ADDR,
        QUANTITY,
        data_format="BBBBBB",
        expected_length=10,
    )
    return out


def convert_fabnr_to_pumpid(fabnr_seq):
    """
    Samme logik som i functions.checkFirstStart():
      FABNR = modbusopen(16, 6, 153, 1)
      FABconv = ("%0.2X" % (FABNR[3]), "%0.2X" % (FABNR[4]), "%0.2X" % (FABNR[5]))
      ... pad "1".."9" til "01".."09" ...
      FABarray = FABconv2[0] + FABconv2[1] + FABconv2[2]
      FABout = int(FABarray, 16)
    """
    if len(fabnr_seq) < 6:
        raise ValueError("FABNR sequence too short: %r" % (fabnr_seq,))

    b3, b4, b5 = fabnr_seq[3], fabnr_seq[4], fabnr_seq[5]

    def fmt_byte(val):
        s = "%0.2X" % (val,)
        # gammel kode lavede speciel håndtering af "1".."9"
        if s == "1":
            s = "01"
        elif s == "2":
            s = "02"
        elif s == "3":
            s = "03"
        elif s == "4":
            s = "04"
        elif s == "5":
            s = "05"
        elif s == "6":
            s = "06"
        elif s == "7":
            s = "07"
        elif s == "8":
            s = "08"
        elif s == "9":
            s = "09"
        return s

    h3 = fmt_byte(b3)
    h4 = fmt_byte(b4)
    h5 = fmt_byte(b5)
    fab_hex = h3 + h4 + h5
    fabout = int(fab_hex, 16)
    return fabout


def persist_pumpid(pumpid: int):
    # Skriv fabnr.cfg som ren tekst
    with open(FABNR_PATH, "w", encoding="utf-8") as f:
        f.write(str(pumpid) + "\n")
    print(f"💾 Wrote FABNR to {FABNR_PATH}: {pumpid}")

    # Skriv/merge config.cfg som JSON
    cfg = {}
    if os.path.isfile(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg = json.load(f)
        except Exception:
            cfg = {}
    cfg["pumpid"] = pumpid
    if "accesstoken" not in cfg:
        cfg["accesstoken"] = ""
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f)
    print(f"💾 Stored pumpid in {CONFIG_PATH}: {pumpid}")

    # Opdatér .env med FABNR=<pumpid>
    env_lines = []
    if os.path.isfile(ENV_PATH):
        try:
            with open(ENV_PATH, "r", encoding="utf-8") as f:
                env_lines = f.readlines()
        except Exception:
            env_lines = []
    key = "FABNR"
    new_line = f"{key}={pumpid}\n"
    written = False
    out_lines = []
    for line in env_lines:
        if line.strip().startswith(f"{key}="):
            if not written:
                out_lines.append(new_line)
                written = True
        else:
            out_lines.append(line)
    if not written:
        out_lines.append(new_line)
    try:
        with open(ENV_PATH, "w", encoding="utf-8") as f:
            f.writelines(out_lines)
        print(f"💾 Updated {ENV_PATH} with {key}={pumpid}")
    except Exception as e:
        print(f"⚠️ Could not write {ENV_PATH}: {e}")


def main():
    print(f"Connecting to Modbus slave {SLAVE_ADDR} on {MODBUS_PORT} ...")
    try:
        master = open_master()
    except Exception as e:
        print(f"❌ Could not open Modbus master on {MODBUS_PORT}: {e}")
        sys.exit(1)

    try:
        time.sleep(0.5)
        fabnr_raw = read_fabnr_raw(master)
        print(f"✅ Raw FABNR response: {fabnr_raw!r}")
        pumpid = convert_fabnr_to_pumpid(fabnr_raw)
        print(f"🆔 Computed pumpid from FABNR: {pumpid}")
        persist_pumpid(pumpid)
        print("✅ Done.")
    except Exception as e:
        print(f"❌ Failed to read/convert FABNR: {e}")
        sys.exit(1)
    finally:
        try:
            master.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
