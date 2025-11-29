#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bygger en DVI payload.json ved at kalde de samme get* funktioner som den gamle
functions.py/PostingThread, via modbus_tk på /dev/ttyACM0.
"""

import json
import os
import queue
import threading
import time
import subprocess  # <-- til at kalde dviWebConnector.py
import sys

from settings import master  # modbus_tk.RtuMaster, samme som i functions.py
from functions import WaitingThread, Job2  # genbrug eksisterende logik

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PAYLOAD_PATH = os.path.join(BASE_DIR, "payload.json")


class SingleWaiting(WaitingThread):
    """
    Lille wrapper rundt om WaitingThread der gør det muligt at kalde
    get* metoderne synkront uden tråde/pri queues.
    """

    def __init__(self):
        # Brug samme initialisering som WaitingThread normalt får,
        # men med vores egne køer.
        jobqueue = queue.PriorityQueue()
        sendqueue = queue.Queue()
        netstatus = queue.Queue()
        slavesende = queue.Queue()
        super().__init__(jobqueue, sendqueue, netstatus, slavesende)

    # Vi override run() så den IKKE starter et evigt loop.
    def run(self):
        raise RuntimeError("SingleWaiting.run() should not be used; call methods directly")


def _collect_one(waiter: SingleWaiting, fn_name: str, *args, **kwargs) -> dict:
    """
    Kald en af WaitingThread.get* metoderne og returner dens JSON-dict.
    Ekstra *args/**kwargs sendes videre til metoden (bruges til force=True).
    """
    # Tøm outputkø først
    while not waiter.sendqueue.empty():
        _ = waiter.sendqueue.get()

    # Kald metoden direkte (ingen tråd, ingen prioritetshåndtering)
    getattr(waiter, fn_name)(*args, **kwargs)

    # Hver get* lægger præcis ét JSON-objekt på sendqueue.
    try:
        raw = waiter.sendqueue.get(timeout=20.0)  # lidt længere timeout for systemstatus
    except queue.Empty:
        return {}

    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            return data
        return {}
    except Exception:
        return {}


def build_legacy_payload(waiter: SingleWaiting, first_run: bool) -> dict:
    """
    Bygger en payload som PostingThread ville have gjort.

    first_run=True: kør også getSystemStatusData(force=True).
    first_run=False: spring systemstatus helt over (brug cachet værdi fra første run).
    """
    payload: dict = {}

    # 1) Felter der ikke er så tunge
    for fn_name in [
        "getSensorData",
        "getRelayData",
        "getUserData",
        "getMonteurData",
    ]:
        part = _collect_one(waiter, fn_name)
        if part:
            payload.update(part)
        time.sleep(0.1)

    # 2) Systemstatus kun første gang (force=True)
    if first_run:
        part = _collect_one(waiter, "getSystemStatusData", True)  # force=True
        if part:
            payload.update(part)
        time.sleep(0.1)

    # 3) Resten
    for fn_name in [
        "getSystemTimeData",
        "getSpecialBlocksData",
        "getSystemBlocksData",
    ]:
        part = _collect_one(waiter, fn_name)
        if part:
            payload.update(part)
        time.sleep(0.1)

    return payload


LOOP_INTERVAL = 60  # sekunder mellem hver fuld legacy‑scan


def main() -> int:
    print("Starting legacy DVI payload loop via modbus_tk (like functions.py)...")

    waiter = SingleWaiting()
    first_run = True

    while True:
        try:
            payload = build_legacy_payload(waiter, first_run)
            first_run = False  # efter første succesfulde run laver vi aldrig mere systemstatus
        except Exception as e:
            print(f"❌ Failed to build legacy payload: {e}")
            time.sleep(10)
            continue

        if not payload:
            print("⚠️ Empty payload built; not writing payload.json")
        else:
            try:
                with open(PAYLOAD_PATH, "w", encoding="utf-8") as f:
                    json.dump(payload, f, ensure_ascii=False)
                print(f"💾 Wrote legacy payload to {PAYLOAD_PATH}")
            except Exception as e:
                print(f"⚠️ Could not write {PAYLOAD_PATH}: {e}")
            else:
                # Hvis skrivning lykkedes, kald dviWebConnector.py for at uploade payloaden
                connector = os.path.join(BASE_DIR, "dviWebConnector.py")
                if os.path.isfile(connector):
                    try:
                        subprocess.Popen(
                            [sys.executable, connector],
                            cwd=BASE_DIR,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                        )
                        print("🚀 Spawned dviWebConnector.py to upload payload")
                    except Exception as e:
                        print(f"⚠️ Could not start dviWebConnector.py: {e}")
                else:
                    print("⚠️ dviWebConnector.py not found; cannot upload payload")

        time.sleep(LOOP_INTERVAL)


if __name__ == "__main__":
    raise SystemExit(main())
