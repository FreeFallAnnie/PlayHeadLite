import csv
import sqlite3
from pathlib import Path
from dotenv import load_dotenv
import os
import pandas as pd

# Try importing OpenAI, but skip if not installed (for current environment)
try:
    import openai
    openai_available = True
except ImportError:
    openai_available = False

# Load environment variables
load_dotenv()

# If OpenAI is available, initialize client
if openai_available:
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

from pathlib import Path

# Set base directory as the parent of 'merge/'
BASE_DIR = Path(__file__).resolve().parent.parent

archive_dir = BASE_DIR / "archive"
everyday_csv = archive_dir / "everyday.csv"
husky_map_csv = archive_dir / "husky_map.csv"
db_path = archive_dir / "how_far_we_come.db"

# Load last user input from everyday.csv
def get_last_event_and_id(csv_path):
    try:
        with open(csv_path, newline='', encoding='utf-8') as f:
            rows = list(csv.reader(f))
            if rows:
                last_row = rows[-1]
                if len(last_row) >= 3:
                    return last_row[2], int(last_row[1])  # event_text, husky_id
    except Exception as e:
        print(f"Error reading {csv_path}: {e}")
    return "", -1

# Load husky_map from CSV
def load_husky_map(csv_path):
    mapping = {}
    try:
        with open(csv_path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                mapping[int(row['ID'])] = row['Prompt']
    except Exception as e:
        print(f"Error reading {csv_path}: {e}")
    return mapping

# Combine prompts and generate response
def ask_AliN(x_prompt, husky_prompt, event_text):
    full_prompt = f"{x_prompt} {husky_prompt} {event_text}"
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Respond clearly and creatively."},
            {"role": "user", "content": full_prompt}
        ],
        temperature=0.7
    )
    return full_prompt, response.choices[0].message.content.strip()

# Save to SQLite DB
def save_to_db(db_file, event_text, husky_id, full_prompt, response):
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS reflections
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  event_text TEXT,
                  husky_id INTEGER,
                  full_prompt TEXT,
                  response TEXT)''')
    c.execute("INSERT INTO reflections (event_text, husky_id, full_prompt, response) VALUES (?, ?, ?, ?)",
              (event_text, husky_id, full_prompt, response))
    conn.commit()
    conn.close()

# Run logic
event_text, husky_id = get_last_event_and_id(everyday_csv)
husky_map = load_husky_map(husky_map_csv)
x_prompt = "Reflect on this event with insight."
husky_prompt = husky_map.get(husky_id, "Describe this.")

if event_text and husky_id != -1 and openai_available:
    full_prompt, response = ask_AliN(x_prompt, husky_prompt, event_text)
    save_to_db(db_path, event_text, husky_id, full_prompt, response)
    result = {"prompt": full_prompt, "response": response}
else:
    result = {"error": "Missing input, husky ID, or OpenAI not available."}

if "response" in locals():
    print("Saved to how_far_we_come.db:")
    print(f"\nPrompt:\n{full_prompt}\n\nResponse:\n{response}")
else:
    print(result["error"])
