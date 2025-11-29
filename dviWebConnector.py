#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Simple web connector that replaces the old functions.py HTTP logic.

Behaviour:
- On startup: waits until PumpID is present in config.cfg (JSON file).
- When PumpID exists: ensures accesstoken by calling DVI webservice.
- When both PumpID and accesstoken exist: loops and periodically reads
  a payload JSON file (payload.json) written by bridge.py and posts it
  to the backend.

This module is deliberately standalone: it does not talk Modbus
itself, it only handles HTTP and config files.
"""

import json
import os
import sys
import time
from typing import Any, Dict, Optional

import requests
from dotenv import load_dotenv  # <-- add import

# Indlæs .env i projektmappen, så SEND_TO_DVI osv. virker
load_dotenv()

# --- Configuration ---------------------------------------------------------

# Use same URLs as legacy settings.py
WEBSERVICE_URL = "https://ws.dvienergi.com/ws-dvi.php"
# Secondary URL kept for completeness, but currently unused
WEBSERVICE_URL2 = "http://awseb-e-t-awsebloa-17kvf6oxolgul-616217914.eu-central-1.elb.amazonaws.com/includes/webservice/ws-dvi.php"  # noqa: E501

# Paths: mirror legacy behaviour but allow override via env vars
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_PATH = os.getenv("DVI_CONFIG_FILE", os.path.join(BASE_DIR, "config.cfg"))
FABNR_PATH = os.getenv("DVI_FABNR_FILE", os.path.join(BASE_DIR, "fabnr.cfg"))

# File that bridge.py is expected to keep updated with latest payload
PAYLOAD_PATH = os.getenv("DVI_PAYLOAD_FILE", os.path.join(BASE_DIR, "payload.json"))

# Post interval in seconds (legacy was ~60s)
POST_INTERVAL = float(os.getenv("DVI_POST_INTERVAL", "60"))

# Delay between config checks when waiting for pumpid
PUMPID_POLL_INTERVAL = float(os.getenv("DVI_PUMPID_POLL_INTERVAL", "20"))

# Number of consecutive Access == "Denied" responses before resetting token
MAX_DENIED = int(os.getenv("DVI_MAX_DENIED", "10"))

# Control whether payloads are actually sent to DVI backend.
# Default is False (only log payloads).
SEND_TO_DVI_ENV = os.getenv("SEND_TO_DVI", "false").strip().lower()
SEND_TO_DVI = SEND_TO_DVI_ENV in {"1", "true", "yes"}

# --- Helpers --------------------------------------------------------------


def _log(msg: str) -> None:
    ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    print(f"[{ts}] [dviWebConnector] {msg}", flush=True)


def load_config() -> Optional[Dict[str, Any]]:
    """Load JSON config from CONFIG_PATH.

    Expected format: {"pumpid": <int>, "accesstoken": "...", ...}
    Returns None if file missing or invalid.
    """
    if not os.path.isfile(CONFIG_PATH):
        return None
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return None
        return data
    except Exception as e:  # pragma: no cover - defensive
        _log(f"Failed to read config.cfg: {e}")
        return None


def save_config(cfg: Dict[str, Any]) -> None:
    """Write JSON config back to CONFIG_PATH in a safe way."""
    tmp_path = CONFIG_PATH + ".tmp"
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False)
        os.replace(tmp_path, CONFIG_PATH)
        _log("Updated config.cfg")
    except Exception as e:  # pragma: no cover - defensive
        _log(f"Failed to write config.cfg: {e}")


def load_pumpid_from_fabnr() -> Optional[int]:
    """Fallback: read numeric PumpID from fabnr.cfg (plain text)."""
    if not os.path.isfile(FABNR_PATH):
        return None
    try:
        with open(FABNR_PATH, "r", encoding="utf-8") as f:
            raw = f.read().strip()
        if not raw:
            return None
        return int(raw)
    except Exception as e:  # pragma: no cover - defensive
        _log(f"Failed to read fabnr.cfg: {e}")
        return None


def wait_for_pumpid() -> int:
    """Block until we have a pumpid in config or fabnr.cfg.

    This mirrors the behaviour you described: keep checking every 20s
    until PumpID is present.
    """
    while True:
        cfg = load_config() or {}
        pumpid = cfg.get("pumpid")
        if pumpid is None:
            # Try fabnr.cfg as fallback
            pumpid = load_pumpid_from_fabnr()
            if pumpid is not None:
                cfg["pumpid"] = pumpid
                # Ensure accesstoken key exists (may be empty)
                cfg.setdefault("accesstoken", "")
                save_config(cfg)
        if pumpid is not None:
            _log(f"Using PumpID: {pumpid}")
            return int(pumpid)

        _log("No PumpID in config.cfg or fabnr.cfg yet; waiting...")
        time.sleep(PUMPID_POLL_INTERVAL)


def ensure_accesstoken(pumpid: int) -> str:
    """Return accesstoken from config.cfg if present.

    Vi antager at DVI allerede har et gyldigt token liggende for denne pumpid,
    og at token er synkroniseret med deres backend. Vi forsøger IKKE at lave et
    nyt token her – det sker kun hvis backend senere svarer Access == "Denied".
    """
    cfg = load_config() or {}
    token = cfg.get("accesstoken") or ""
    if token:
        _log("Using existing accesstoken from config.cfg")
        return token

    _log("No accesstoken in config.cfg; assuming DVI backend either has none yet or will reject until created.")
    # Return tom streng – payload‑loop vil så ikke kunne poste før vi har et token.
    return ""


def obtain_new_token_from_dvi(pumpid: int) -> Optional[str]:
    """Aktiv token-refresh, KUN kaldt når DVI har sagt Access == 'Denied' for payloads.

    Matcher den oprindelige logik: POST {"pumpid": <id>, "accesstoken": ""} og forvent
    at backend svarer med nyt accesstoken, hvis de har slettet/opdateret det.
    """
    payload = {"pumpid": pumpid, "accesstoken": ""}
    debug_body = json.dumps(payload)
    _log(f"[TOKEN-REFRESH] POST {WEBSERVICE_URL}")
    _log(f"[TOKEN-REFRESH] Request body: {debug_body}")
    try:
        resp = requests.post(
            WEBSERVICE_URL,
            headers={"Content-Type": "application/json"},
            data=debug_body,
            timeout=30.0,
        )
    except Exception as e:
        _log(f"[TOKEN-REFRESH] Error contacting webservice: {e}")
        return None

    _log(f"[TOKEN-REFRESH] Status: {resp.status_code}")
    _log(f"[TOKEN-REFRESH] Raw response text: {resp.text!r}")

    if resp.status_code != 200:
        return None

    try:
        data = resp.json()
    except Exception as e:
        _log(f"[TOKEN-REFRESH] Failed to decode JSON: {e}")
        return None

    _log(f"[TOKEN-REFRESH] Decoded JSON response: {data}")

    if data.get("Access") == "Denied":
        _log("[TOKEN-REFRESH] Access still Denied; backend har ikke (endnu) et token til denne pumpid.")
        return None

    token = data.get("accesstoken") or data.get("AccessToken")
    if not token:
        _log("[TOKEN-REFRESH] Response mangler accesstoken/AccessToken.")
        return None

    cfg = load_config() or {}
    cfg["pumpid"] = pumpid
    cfg["accesstoken"] = token
    save_config(cfg)
    _log("[TOKEN-REFRESH] Stored new accesstoken from DVI")
    return token


def load_payload() -> Optional[Dict[str, Any]]:
    """Load the current payload from PAYLOAD_PATH.

    Expected format: a JSON object with all the measurement fields
    (sensordata, relaydata, etc.) as produced by bridge.py.
    Returns None if file is missing/invalid.
    """
    if not os.path.isfile(PAYLOAD_PATH):
        return None
    try:
        with open(PAYLOAD_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            _log("payload.json is not a JSON object; ignoring")
            return None
        return data
    except Exception as e:  # pragma: no cover - defensive
        _log(f"Failed to read payload.json: {e}")
        return None


def post_payload(session: requests.Session, pumpid: int, token: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Send payload to DVI backend and return decoded JSON response.

    If SEND_TO_DVI is False, only log the payload that would have been sent.
    """
    body = dict(payload)  # shallow copy so we can inject auth fields
    # Ensure auth fields are present at top level
    body.setdefault("pumpid", pumpid)
    body.setdefault("accesstoken", token)

    if not SEND_TO_DVI:
        pretty = json.dumps(body, ensure_ascii=False, indent=2)
        _log("SEND_TO_DVI is False or not set; would have posted this payload:")
        print(pretty, flush=True)
        return None

    if not token:
        _log("[PAYLOAD] No accesstoken available; skipping POST and waiting for valid token.")
        return None

    debug_body = json.dumps(body)
    _log(f"[PAYLOAD] POST {WEBSERVICE_URL}")
    _log(f"[PAYLOAD] Request body: {debug_body[:2000]}")  # truncate to avoid huge logs

    try:
        session.headers.update({"Content-Type": "application/json"})
        resp = session.post(WEBSERVICE_URL, data=debug_body, timeout=30.0)
    except Exception as e:
        _log(f"[PAYLOAD] Error posting payload: {e}")
        return None

    _log(f"[PAYLOAD] Status: {resp.status_code}")
    _log(f"[PAYLOAD] Raw response text: {resp.text!r}")

    if resp.status_code != 200:
        _log(f"Payload post returned status {resp.status_code}")
        return None

    try:
        data = resp.json()
    except Exception as e:  # pragma: no cover - defensive
        _log(f"[PAYLOAD] Failed to decode payload response as JSON: {e}")
        return None

    _log(f"[PAYLOAD] Decoded JSON response: {data}")
    return data


def main() -> int:
    _log("Starting dviWebConnector")

    pumpid = wait_for_pumpid()
    _log(f"Config pumpid is {pumpid}. Will use existing accesstoken if present.")
    token = ensure_accesstoken(pumpid)

    denied_count = 0
    session = requests.Session()

    # Simple periodic loop
    next_post = time.time() + 3  # mimic small initial delay

    while True:
        now = time.time()
        if now < next_post:
            time.sleep(max(0.5, next_post - now))
            continue

        payload = load_payload()
        if payload is None:
            _log("No payload.json available; skipping this cycle")
            next_post = time.time() + POST_INTERVAL
            continue

        _log("Posting payload to DVI backend")
        resp = post_payload(session, pumpid, token, payload)

        if resp is None:
            # Network or decoding issue – do not increment denied counter,
            # but schedule next try.
            next_post = time.time() + POST_INTERVAL
            continue

        # Check Access flag
        access = resp.get("Access")
        if access == "Denied":
            denied_count += 1
            _log(f"Access Denied from server (#{denied_count})")
            _log("This indicates that the currently stored accesstoken is no longer valid at DVI.")
            if denied_count >= MAX_DENIED:
                _log("Too many Access Denied responses; clearing local accesstoken and asking DVI for a new one.")
                cfg = load_config() or {"pumpid": pumpid}
                cfg["pumpid"] = pumpid
                cfg["accesstoken"] = ""
                save_config(cfg)
                denied_count = 0

                # Forsøg at få et nyt token fra DVI – matcher 'enhed skiftet / gammel brændt af'-scenariet
                new_token = obtain_new_token_from_dvi(pumpid)
                if new_token:
                    token = new_token
                else:
                    _log("[TOKEN-REFRESH] Could not obtain new accesstoken; will keep running and retry later.")
        else:
            if denied_count:
                _log("Server Access no longer Denied; resetting counter")
            denied_count = 0

        # Placeholders for future handling of server commands ("up", "login", etc.)
        if "up" in resp:
            _log("Received 'up' structure from server (ignored for now)")
        if "login" in resp:
            _log(f"Server login flag: {resp.get('login')}")

        next_post = time.time() + POST_INTERVAL

    # Unreachable
    # return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        _log("Shutting down on KeyboardInterrupt")
        sys.exit(0)
