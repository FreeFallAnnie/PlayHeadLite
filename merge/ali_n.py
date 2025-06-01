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

# Define paths
archive_dir = Path("archive")
everyday_csv = archive_dir / "everyday.csv"
husky_csv = archive_dir / "husky_retrieved.csv"
husky_map_csv = archive_dir / "husky_map.csv"
db_path = archive_dir / "how_far_we_come.db"

# Load last user input from everyday.csv
def get_last_input(csv_path):
    try:
        with open(csv_path, newline='', encoding='utf-8') as f:
            rows = list(csv.reader(f))
            if rows:
                return rows[-1][1]  # assuming column 1 is the user input
    except Exception as e:
        print(f"Error reading {csv_path}: {e}")
    return ""

# Load last Husky ID from husky_retrieved.csv
def get_last_husky_id(csv_path):
    try:
        with open(csv_path, newline='', encoding='utf-8') as f:
            rows = list(csv.reader(f))
            if rows:
                return int(rows[-1][1])  # assuming column 1 is the Husky ID
    except Exception as e:
        print(f"Error reading {csv_path}: {e}")
    return -1

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
def ask_AliN(x_prompt, husky_prompt, user_input):
    full_prompt = f"{x_prompt} {husky_prompt} {user_input}"
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
def save_to_db(db_file, user_input, husky_id, full_prompt, response):
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS reflections
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_input TEXT,
                  husky_id INTEGER,
                  full_prompt TEXT,
                  response TEXT)''')
    c.execute("INSERT INTO reflections (user_input, husky_id, full_prompt, response) VALUES (?, ?, ?, ?)",
              (user_input, husky_id, full_prompt, response))
    conn.commit()
    conn.close()

# Run logic (skip OpenAI call if not installed)
user_input = get_last_input(everyday_csv)
husky_id = get_last_husky_id(husky_csv)
husky_map = load_husky_map(husky_map_csv)
x_prompt = "Reflect on this event with insight."
husky_prompt = husky_map.get(husky_id, "Describe this.")

if user_input and husky_id != -1 and openai_available:
    full_prompt, response = ask_AliN(x_prompt, husky_prompt, user_input)
    save_to_db(db_path, user_input, husky_id, full_prompt, response)
    result = {"prompt": full_prompt, "response": response}
else:
    result = {"error": "Missing input, husky ID, or OpenAI not available."}

import ace_tools as tools; tools.display_dataframe_to_user(name="Ali_N Result", dataframe=pd.DataFrame([result]))
