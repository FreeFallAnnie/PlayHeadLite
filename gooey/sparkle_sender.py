import asyncio
from bleak import BleakClient
import sqlite3
import csv
import time
import os

# Replace with your Bluefruit’s MAC address
BLUEFRUIT_MAC_ADDRESS = "AA:BB:CC:DD:EE:FF"
UART_RX_CHAR_UUID = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"

# BLE: Send a color command
def send_sparkle(color):
    asyncio.run(_send_color(color))

async def _send_color(color):
    try:
        async with BleakClient(BLUEFRUIT_MAC_ADDRESS) as client:
            if await client.is_connected():
                msg = color.upper().encode('utf-8')
                await client.write_gatt_char(UART_RX_CHAR_UUID, msg)
                print(f"[BLE] Sent color: {color}")
            else:
                print("[BLE] Could not connect to Bluefruit")
    except Exception as e:
        print(f"[BLE] Error: {e}")

# CSV: Load Husky ID → Color map
def load_husky_map(csv_path="archive/husky_map.csv"):
    id_to_color = {}
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            id_to_color[int(row['ID'])] = row['Color'].upper()
    return id_to_color

# DB Watcher: Live sparkle history
def start_color_tracker(db_path="archive/how_far_we_come.db"):
    print("🌈 Starting live sparkle tracker...")
    color_map = load_husky_map()
    last_row_count = 0

    while True:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM history")
        rows = cursor.fetchall()
        conn.close()

        if len(rows) > last_row_count:
            new_rows = rows[last_row_count:]
            for row in new_rows:
                husky_id = int(row[1])
                color = color_map.get(husky_id, "OFF")
                print(f"✨ New entry detected! ID: {husky_id} → Color: {color}")
                send_sparkle(color)
                time.sleep(2)
            last_row_count = len(rows)

        time.sleep(1)

# Run as standalone script
if __name__ == "__main__":
    start_color_tracker()
