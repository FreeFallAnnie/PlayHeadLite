import tkinter as tk
from tkinter import ttk
from tkinter import simpledialog
import csv
import queue
import sounddevice as sd
import sys
import json
import time
from vosk import Model, KaldiRecognizer
from datetime import datetime
import os
import sqlite3

ARCHIVE_CSV = os.path.join(os.path.dirname(__file__), '..', 'archive', 'everyday.csv')

q = queue.Queue()
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
        print(f"🎙️ Listening for {duration} seconds...")
        start_time = time.time()
        while time.time() - start_time < duration:
            data = q.get()
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                full_text += result.get("text", "") + " "
        final_result = json.loads(rec.FinalResult())
        full_text += final_result.get("text", "")

    return full_text.strip()

def save_to_csv(text):
    timestamp = datetime.now().isoformat(timespec='seconds')
    with open(ARCHIVE_CSV, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([timestamp, text])

def load_csv_history():
    try:
        with open(ARCHIVE_CSV, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            return list(reader)[-50:]  # limit to last 50 entries
    except Exception as e:
        print(f"Error reading history: {e}")
        return []

class LookingGlass:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Looking Glass")

        self.tab_control = ttk.Notebook(self.root)
        self.input_tab = tk.Frame(self.tab_control)
        self.history_tab = tk.Frame(self.tab_control)

        self.tab_control.add(self.input_tab, text='Record + Label')
        self.tab_control.add(self.history_tab, text='View History')
        self.tab_control.pack(expand=1, fill="both")

        self.label = tk.Label(self.input_tab, text="Press Record to begin!", font=("Helvetica", 16))
        self.label.pack(pady=20)

        self.record_btn = tk.Button(self.input_tab, text="Record an everyday event", command=self.record_audio)
        self.record_btn.pack(pady=10)

        self.keep_btn = tk.Button(self.input_tab, text="Keep", command=self.keep_text, state='disabled')
        self.discard_btn = tk.Button(self.input_tab, text="Discard", command=self.discard_text, state='disabled')
        self.keep_btn.pack(side=tk.LEFT, padx=10, pady=10)
        self.discard_btn.pack(side=tk.RIGHT, padx=10, pady=10)

        self.transcription = tk.Label(self.input_tab, text="", wraplength=500, justify="left")
        self.transcription.pack(pady=20)

        self.tree = ttk.Treeview(self.history_tab, columns=("timestamp", "text"), show="headings")
        self.tree.heading("timestamp", text="Timestamp")
        self.tree.heading("text", text="Transcribed Text")

        self.tree.column("timestamp", width=180)
        self.tree.column("text", width=400)

        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.current_text = ""
        self.load_history()

    def record_audio(self):
        self.label.config(text="Recording for 10 seconds...")
        self.root.update()
        self.current_text = recognize_from_mic()
        self.label.config(text="Finished Recording")
        self.transcription.config(text=self.current_text)
        self.keep_btn.config(state='normal')
        self.discard_btn.config(state='normal')

    def keep_text(self):
        try:
            husky_id = simpledialog.askinteger("Husky ID", "Enter HuskyLens ID:")
            if husky_id is None:
                self.label.config(text="Input cancelled.")
                return
    
            husky_map = load_husky_map()
            mapping = husky_map.get(husky_id, {'prompt': 'Describe this.', 'color': 'BLUE'})
    
            # Combine prompt + transcribed input
            combined_text = f"{mapping['prompt']} {self.current_text}"
    
            # Save only the original input for now (LLM will come later)
            save_to_csv(self.current_text)
    
            self.label.config(text=f"Saved with ID {husky_id} ({mapping['color']})")
            self.transcription.config(text="")
            self.keep_btn.config(state='disabled')
            self.discard_btn.config(state='disabled')
            self.load_history()
        except Exception as e:
            print("Error during keep:", e)
            self.label.config(text="Error while saving.")
            
    def discard_text(self):
        self.label.config(text="Your event has not been kept.")
        self.transcription.config(text="")
        self.keep_btn.config(state='disabled')
        self.discard_btn.config(state='disabled')

    def load_history(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for timestamp, text in load_csv_history():
            self.tree.insert("", tk.END, values=(timestamp, text))

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = LookingGlass()
    app.run()
