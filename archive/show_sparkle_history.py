import sqlite3
import csv
import time
# from gooey.sparkle_sender import send_sparkle  # 🔇 BLE disabled

# Load Husky ID → Color map
def load_husky_map(csv_path="archive/husky_map.csv"):
    id_to_color = {}
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            id_to_color[int(row['ID'])] = row['Color'].upper()
    return id_to_color

# Read color history from DB
def get_color_history(db_path="archive/how_far_we_come.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM history")
    rows = cursor.fetchall()
    conn.close()

    # Extract Husky ID from second column
    return [int(row[1]) for row in rows]

# Main loop
if __name__ == "__main__":
    color_map = load_husky_map()
    id_history = get_color_history()

    print("🎨 (Simulated) Sending color history to Circuit Playground...")
    for husky_id in id_history:
        color = color_map.get(husky_id, "OFF")
        print(f"🟢 ID: {husky_id} → Color: {color}")
        # send_sparkle(color)  # 🔇 BLE action disabled
        time.sleep(2)  # Pause to simulate timing
