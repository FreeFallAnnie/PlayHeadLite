# main.py

from gooey.looking_glass import LookingGlass
from merge.x_marks import load_XMarks, get_Sparkle
from merge.ali_n import ask_AliN
from gooey.sparkle_sender import send_sparkle
import sqlite3
import datetime

# Load the CSV map from archive
prompt_map = load_XMarks("archive/husky_map.csv")

# Connect to SQLite database
db = sqlite3.connect("archive/how_far_we_come.db")
cursor = db.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS history (
                    timestamp TEXT,
                    user_input TEXT,
                    agent_prompt TEXT,
                    ai_response TEXT,
                    color TEXT
                )''')
db.commit()

# GUI sends input and decision here
def handle_user_choice(user_input, husky_id, decision):
    agent_prompt, color = get_Sparkle(prompt_map, husky_id)
    full_prompt = f"{agent_prompt} User said: {user_input}"
    ai_response = ask_AliN(full_prompt)
    send_sparkle(color)  # BLE color call
    timestamp = datetime.datetime.now().isoformat()
    cursor.execute("INSERT INTO history VALUES (?, ?, ?, ?, ?)",
                   (timestamp, user_input, agent_prompt, ai_response, color))
    db.commit()
    return ai_response, color

# Launch GUI loop
LookingGlass(start_callback=handle_user_choice).run()
