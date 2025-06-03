# main.py

from dotenv import load_dotenv
load_dotenv()

from gooey.looking_glass import LookingGlass
from merge.x_marks import load_XMarks, get_Sparkle
from merge.ali_n import ask_AliN, save_to_db
#from gooey.sparkle_sender import send_sparkle
import sqlite3
import datetime
import os

# Load context map
prompt_map = load_XMarks(os.path.join("archive", "husky_map.csv"))

# Set up SQLite DB
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent
db_path = BASE_DIR / "archive" / "how_far_we_come.db"
db = sqlite3.connect(db_path)
cursor = db.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS history (
    timestamp TEXT,
    user_input TEXT,
    agent_prompt TEXT,
    ai_response TEXT,
    color TEXT
)''')
db.commit()

# This function is called ONLY when "Keep" is pressed
def handle_user_choice(user_input, husky_id):
    # Step 1: Get mapped context prompt + color
    agent_prompt, color = get_Sparkle(prompt_map, husky_id)

    # Step 2: Call LLM
    x_prompt = "Spark wonder in this event - keep it short."
    full_prompt, ai_response = ask_AliN(x_prompt, agent_prompt, user_input)

    # Step 3: Send color to LED via Bluefruit
    #send_sparkle(color)
    
    # Step 3: Save to reflections table (for third tab)
    save_to_db(db_path, user_input, husky_id, full_prompt, ai_response)
    
    # Step 4: Save to database
    timestamp = datetime.datetime.now().isoformat()
    cursor.execute("INSERT INTO history VALUES (?, ?, ?, ?, ?)",
                   (timestamp, user_input, agent_prompt, ai_response, color))
    db.commit()

    # Step 5: Return to GUI (to display)
    return ai_response, color

# Start GUI loop with callback for keep button
if __name__ == "__main__":
    LookingGlass(start_callback=handle_user_choice).run()

