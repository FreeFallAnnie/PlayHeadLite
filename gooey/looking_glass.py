import tkinter as tk
from tkinter import simpledialog, ttk
import csv
import sqlite3
import queue
import sounddevice as sd
import sys
import json
import time
import os
from datetime import datetime
from vosk import Model, KaldiRecognizer

# ──────────────────────────────────────
# AUDIO TRANSCRIPTION + CSV LOGGING
# ──────────────────────────────────────
q = queue.Queue()

def callback(indata, frames, time_info, status):
    if status:
        print(status, file=sys.stderr)
    q.put(bytes(indata))

def recognize_from_mic(duration=10):
    model = Model("model")
    rec = KaldiRecognizer(model, 16000)
    full_text = ""

    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                           channels=1, callback=callback):
        print(f"Listening for {duration} seconds...")
        start_time = time.time()
        while time.time() - start_time < duration:
            data = q.get()
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                full_text += result.get("text", "") + " "
        final_result = json.loads(rec.FinalResult())
        full_text += final_result.get("text", "")

    final_text = full_text.strip()
    save_to_csv(final_text)
    return final_text

def save_to_csv(text, filename="everyday.csv"):
    timestamp = datetime.now().isoformat(timespec='seconds')
    with open(filename, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([timestamp, text])

def get_latest_prompt(filename="everyday.csv"):
    try:
        with open(filename, newline='', encoding='utf-8') as f:
            reader = list(csv.reader(f))
            if reader:
                return reader[-1][1]
    except Exception as e:
        print(f"Error reading CSV: {e}")
    return ""

# ──────────────────────────────────────
# GUI CLASS
# ──────────────────────────────────────
class LookingGlass:
    def __init__(self, start_callback):
        self.root = tk.Tk()
        self.root.title("Looking Glass")

        self.tab_control = ttk.Notebook(self.root)
        self.input_tab = tk.Frame(self.tab_control)
        self.history_tab = tk.Frame(self.tab_control)

        self.tab_control.add(self.input_tab, text='Record + Label')
        self.tab_control.add(self.history_tab, text='View History')
        self.tab_control.pack(expand=1, fill="both")

        self.start_callback = start_callback

        self.label = tk.Label(self.input_tab, text="Press Record to begin!", font=("Helvetica", 16))
        self.label.pack(pady=20)

        self.record_btn = tk.Button(self.input_tab, text="🎧 Record Event", command=self.record_and_load)
        self.record_btn.pack(pady=10)

        self.keep_btn = tk.Button(self.input_tab, text="Keep", command=lambda: self.respond('KEEP'), state='disabled')
        self.discard_btn = tk.Button(self.input_tab, text="Discard", command=lambda: self.respond('DISCARD'), state='disabled')
        self.keep_btn.pack(side=tk.LEFT, padx=10, pady=10)
        self.discard_btn.pack(side=tk.RIGHT, padx=10, pady=10)

        self.result = tk.Label(self.input_tab, text="", wraplength=500, justify="left")
        self.result.pack(pady=20)

        self.tree = ttk.Treeview(self.history_tab, columns=("timestamp", "husky_id", "input", "response", "color"), show="headings")
        self.tree.heading("timestamp", text="Timestamp")
        self.tree.heading("husky_id", text="ID")
        self.tree.heading("input", text="Input")
        self.tree.heading("response", text="Response")
        self.tree.heading("color", text="Color")

        self.tree.column("timestamp", width=140)
        self.tree.column("husky_id", width=40)
        self.tree.column("input", width=180)
        self.tree.column("response", width=200)
        self.tree.column("color", width=60)

        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.tree.bind("<Double-1>", self.show_details)

        self.ensure_table_exists()
        self.load_history()
    def show_details(self, event):
        selected_item = self.tree.selection()
        if not selected_item:
            return
        row = self.tree.item(selected_item[0], 'values')
        timestamp, husky_id, user_input, response, color = row

        detail_win = tk.Toplevel(self.root)
        detail_win.title("Full Entry")
        detail_text = f"""Timestamp: {timestamp}
    ID: {husky_id}
    Color: {color}

    Input:
    {user_input}

    Response:
    {response}
    """
        tk.Label(detail_win, text=detail_text, justify="left", anchor="w").pack(padx=10, pady=10)

    def ensure_table_exists(self):
        conn = sqlite3.connect("how_far_we_come.db")
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                husky_id INTEGER,
                user_input TEXT,
                response TEXT,
                color TEXT
            )
        """)
        conn.commit()
        conn.close()

    def record_and_load(self):
        self.label.config(text="Recording for 10 seconds...")
        self.root.update()
        self.user_input = recognize_from_mic()
        self.label.config(text=f"Transcribed: {self.user_input}")
        self.husky_id = simpledialog.askinteger("Husky ID", "Enter HuskyLens ID:")
        self.keep_btn.config(state='normal')
        self.discard_btn.config(state='normal')

    def respond(self, decision):
        response, color = self.start_callback(self.user_input, self.husky_id, decision)
        self.result.config(text=f"{response}\n\n(Color shown: {color})")
        self.keep_btn.config(state='disabled')
        self.discard_btn.config(state='disabled')

        if decision == 'KEEP':
            save_to_db(self.user_input, self.husky_id, response, color)
            self.load_history()

    def load_history(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        conn = sqlite3.connect("how_far_we_come.db")
        cursor = conn.cursor()
        cursor.execute("SELECT timestamp, husky_id, user_input, response, color FROM responses ORDER BY id DESC")
        rows = cursor.fetchall()
        for row in rows:
            self.tree.insert("", tk.END, values=row)
        conn.close()

    def run(self):
        self.root.mainloop()

# ──────────────────────────────────────
# RUN APP
# ──────────────────────────────────────
if __name__ == "__main__":
    app = LookingGlass(ali_start_callback)
    app.run()
