import csv
import os
from huskylib import HuskyLensLibrary

# Paths
HUSKY_CSV = os.path.join(os.path.dirname(__file__), '..', 'archive', 'husky_map.csv')
RETRIEVED_CSV = os.path.join(os.path.dirname(__file__), '..', 'archive', 'husky_retrieved.csv')

# Initialize HuskyLens connection
hl = HuskyLensLibrary("UART", "/dev/serial0")
hl.knock()

# Load Husky Map CSV
def load_husky_map(path=HUSKY_CSV):
    husky_map = {}
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            husky_map[int(row['ID'])] = {
                'prompt': row['Agent_LLM'],
                'color': row['Color'].upper()
            }
    return husky_map

# Save to husky_retrieved.csv
def save_retrieved_id(husky_id, prompt, color, path=RETRIEVED_CSV):
    with open(path, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['ID', 'Prompt', 'Color'])
        writer.writerow([husky_id, prompt, color])

# Get current HuskyLens ID
def get_husky_id():
    hl.request()
    if hl.count() > 0:
        block = hl.blocks()[0]
        return block.ID
    return None

# Get mapped info (prompt + color), asks user to choose method
def get_husky_context():
    husky_map = load_husky_map()

    choice = input("Use HuskyLens? (y/n): ").strip().lower()
    husky_id = None

    if choice == 'y':
        husky_id = get_husky_id()
        if husky_id is None:
            print("❌ No object detected by HuskyLens.")
    else:
        try:
            manual_input = input("Enter HuskyLens ID manually: ").strip()
            husky_id = int(manual_input)
        except ValueError:
            print("Invalid input.")

    if husky_id is not None and husky_id in husky_map:
        prompt = husky_map[husky_id]['prompt']
        color = husky_map[husky_id]['color']
        save_retrieved_id(husky_id, prompt, color)
        return husky_id, husky_map[husky_id]

    return None, {'prompt': "Describe this.", 'color': "BLUE"}
