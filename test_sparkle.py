import asyncio
from bleak import BleakClient
import sqlite3
import csv
import time
import os

from bleak import BleakScanner
from bleak.backends.scanner import AdvertisementData


DEVICE_NAME = "CIRCUITPY8167"  # matches what your CPB advertises
UART_RX_CHAR_UUID = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"
UART_SERVICE_UUID = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"


# BLE: Send a color command
def send_sparkle(color):
    asyncio.run(_send_color(color))

async def _send_color(color):
    print(f"[BLE] Scanning for device named '{DEVICE_NAME}' with UART service...")

    target = None

    def detection_callback(device, adv_data: AdvertisementData):
        nonlocal target
        name_match = device.name and DEVICE_NAME in device.name
        uuid_match = UART_SERVICE_UUID.lower() in [uuid.lower() for uuid in adv_data.service_uuids]
        if name_match and uuid_match:
            target = device

    scanner = BleakScanner(detection_callback)
    await scanner.start()
    await asyncio.sleep(6.0)
    await scanner.stop()

    if not target:
        print(f"[BLE] Error: '{DEVICE_NAME}' with UART service not found.")
        return

    try:
        async with BleakClient(target) as client:
            if await client.is_connected():
                msg = color.upper().encode("utf-8")
                await client.write_gatt_char(UART_RX_CHAR_UUID, msg)
                print(f"[BLE] Sent color: {color}")
            else:
                print("[BLE] Could not connect to device")
    except Exception as e:
        print(f"[BLE] Error: {e}")


# CSV: Load Husky ID → Color map
def load_husky_map():
    base_path = os.path.dirname(__file__)
    csv_path = os.path.join(base_path, "..", "archive", "husky_map.csv")
    id_to_color = {}
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            id_to_color[int(row['ID'])] = row['Color'].upper()
    return id_to_color

# DB Watcher: Live sparkle history
def start_color_tracker():
    base_path = os.path.dirname(__file__)
    db_path = os.path.join(base_path, "..", "archive", "how_far_we_come.db")

    print("Starting live sparkle tracker...")
    color_map = load_husky_map()
    last_row_count = 0

    while True:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM responses")
        rows = cursor.fetchall()
        conn.close()

        if len(rows) > last_row_count:
            new_rows = rows[last_row_count:]
            for row in new_rows:
                husky_id = int(row[2])
                color = color_map.get(husky_id, "OFF")
                print(f"New entry detected! ID: {husky_id} → Color: {color}")
                send_sparkle(color)
                time.sleep(2)
            last_row_count = len(rows)

        time.sleep(1)

# Run as standalone script
if __name__ == "__main__":
    send_sparkle("PINK")
