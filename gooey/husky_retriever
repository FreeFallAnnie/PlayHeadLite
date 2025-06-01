import csv
from huskylib import HuskyLensLibrary
import os

# Initialize HuskyLens connection
hl = HuskyLensLibrary("UART", "/dev/serial0") 
hl.knock()

# Load Husky Map CSV
def load_husky_map(path=os.path.join(os.path.dirname(__file__), '..', 'archive', 'husky_map.csv')):
    husky_map = {}
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            husky_map[int(row['ID'])] = {
                'prompt': row['Agent_LLM'],
                'color': row['Color'].upper()
            }
    return husky_map

# Get current HuskyLens ID
def get_husky_id():
    hl.request()
    if hl.count() > 0:
        block = hl.blocks()[0]
        return block.ID
    return None

# Get mapped info (prompt + color)
def get_husky_context():
    husky_map = load_husky_map()
    husky_id = get_husky_id()
    if husky_id is not None and husky_id in husky_map:
        return husky_id, husky_map[husky_id]
    return None, {'prompt': "Describe this.", 'color': "BLUE"}
