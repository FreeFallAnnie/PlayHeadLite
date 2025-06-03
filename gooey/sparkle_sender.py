# sparkle_sender.py
# BLE functionality removed — send_sparkle is now a stub

import time
import csv
import os
import sqlite3

# Stub function to preserve compatibility
def send_sparkle(color):
    print(f"[DISABLED BLE] Would send color: {color}")

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

# DB Watcher: Stubbed sparkle history for testing
def start_color_tracker():
    base_path = os.path.dirname(__file__)
    db_path = os.path.join(base_path, "..", "archive", "how_far_we_come.db")

    print("🧪 Starting sparkle tracker (BLE disabled)")
    color_map = load_husky_map()
    last_row_count = 0

    while True:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM reflections")
        rows = cursor.fetchall()
        conn.close()

        if len(rows) > last_row_count:
            new_rows = rows[last_row_count:]
            for row in new_rows:
                husky_id = int(row[2])
                color = color_map.get(husky_id, "OFF")
                print(f"[SPARKLE] ID: {husky_id} → Color: {color} (simulated)")
                send_sparkle(color)
                time.sleep(2)
            last_row_count = len(rows)

        time.sleep(1)

# Run as standalone script (for testing)
if __name__ == "__main__":
    start_color_tracker()
