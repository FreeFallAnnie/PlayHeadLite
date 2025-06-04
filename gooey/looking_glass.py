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
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'archive', 'how_far_we_come.db')

q = queue.Queue()

def load_husky_map(path=os.path.join(os.path.dirname(__file__), '..', 'archive', 'husky_map.csv')):
    husky_map = {}
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            husky_map[int(row['ID'])] = {
                'prompt': row['Prompt'],
                'color': row['Color'].upper()
            }
    return husky_map

def callback(indata, frames, time_info, status):
    if status:
        print(status, file=sys.stderr)
    q.put(bytes(indata))

def recognize_from_mic(duration=10):
    MODEL_PATH = os.path.join(os.path.dirname(__file__), "model")
    model = Model(MODEL_PATH)
    rec = KaldiRecognizer(model, 16000)
    full_text = ""

    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                           channels=1, callback=callback):
        print(f"I listen better when you wait for 3 seconds and keep the everyday event short and sweet!")
        start_time = time.time()
        while time.time() - start_time < duration:
            data = q.get()
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                full_text += result.get("text", "") + " "
        final_result = json.loads(rec.FinalResult())
        full_text += final_result.get("text", "")

    return full_text.strip()

def save_to_csv(event_text, husky_id):
    timestamp = datetime.now().isoformat(timespec='seconds')
    with open(ARCHIVE_CSV, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([timestamp, husky_id, event_text])
        
def load_csv_history():
    try:
        with open(ARCHIVE_CSV, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader, None)
            return list(reader)[-50:]
    except Exception as e:
        print(f"Error reading history: {e}")
        return []

def load_response_history():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT husky_id, response FROM reflections ORDER BY id DESC LIMIT 50")
        rows = cursor.fetchall()
        conn.close()
        return rows
    except Exception as e:
        print("Error loading responses:", e)
        return []

class LookingGlass:
    def show_popup(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        row = self.tree.item(selected[0], 'values')
        if not row or len(row) < 3:
            return

        timestamp, husky_id, event_text = row

        popup = tk.Toplevel(self.root)
        popup.title("Full Entry")
        popup.geometry("500x400")

        full_text = f"""Timestamp: {timestamp}\nHusky ID: {husky_id}\n\nEvent Text:\n{event_text}"""
        label = tk.Label(popup, text=full_text, justify="left", anchor="w", wraplength=480)
        label.pack(padx=10, pady=10)

    def show_response_popup(self, event):
        selected = self.response_tree.selection()
        if not selected:
            return
        row = self.response_tree.item(selected[0], 'values')
        if not row or len(row) < 1:
            return
    
        response = row[0]
    
        popup = tk.Toplevel(self.root)
        popup.title("WonderSparked Response")
        popup.geometry("400x300")
    
        text_frame = tk.Frame(popup)
        text_frame.pack(fill=tk.BOTH, expand=True)
    
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
        text_widget = tk.Text(text_frame, wrap=tk.WORD, yscrollcommand=scrollbar.set)
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
        content = f"{response}"
        text_widget.insert(tk.END, content)
        text_widget.config(state=tk.DISABLED)
    
        scrollbar.config(command=text_widget.yview)

    def __init__(self, start_callback=None):
        self.start_callback = start_callback
        self.root = tk.Tk()
        self.root.title("Looking Glass")
        self.root.configure(bg="white")
        self.husky_map = load_husky_map()

        self.tab_control = ttk.Notebook(self.root)
        self.input_tab = tk.Frame(self.tab_control)
        self.history_tab = tk.Frame(self.tab_control)
        self.response_tab = tk.Frame(self.tab_control)

        self.input_tab.configure(bg="white")
        self.history_tab.configure(bg="white")
        self.response_tab.configure(bg="white")

        self.tab_control.add(self.input_tab, text='Record')
        self.tab_control.add(self.history_tab, text='your Everyday')
        self.tab_control.add(self.response_tab, text='with Wonder!')
        self.tab_control.pack(expand=1, fill="both")

        self.label = tk.Label(self.input_tab, text="Press Record to begin!", font=("Helvetica", 16), bg="white")
        self.label.pack(pady=20)
        
        self.record_btn = tk.Button(self.input_tab, text="Record an everyday event", command=self.record_audio)
        self.record_btn.pack(pady=10)
        
        button_frame = tk.Frame(self.input_tab, bg="white")
        button_frame.pack(pady=10)
        
        self.keep_btn = tk.Button(button_frame, text="Keep", command=self.keep_text, state='disabled')
        self.keep_btn.pack(side=tk.LEFT, padx=10)
        
        self.discard_btn = tk.Button(button_frame, text="Discard", command=self.discard_text, state='disabled')
        self.discard_btn.pack(side=tk.LEFT, padx=10)

        self.transcription = tk.Label(self.input_tab, text="", wraplength=500, justify="left", bg="white")
        self.transcription.pack(pady=20)

        self.tree = ttk.Treeview(self.history_tab, columns=("timestamp", "husky_id", "event_text"), show="headings")
        self.tree.heading("timestamp", text="Time to")
        self.tree.heading("husky_id", text="Spark")
        self.tree.heading("event_text", text="the Everyday")
        self.tree.column("timestamp", width=160)
        self.tree.column("husky_id", width=60)
        self.tree.column("event_text", width=400)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.tree.bind("<Double-1>", self.show_popup)

        self.response_tree = ttk.Treeview(self.response_tab, columns=("response",), show="headings")
        self.response_tree.heading("response", text="WonderSparked")
        self.response_tree.column("response", width=500)
        self.response_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.response_tree.bind("<Double-1>", self.show_response_popup)

        for tree in (self.tree, self.response_tree):
            tree.tag_configure("GREEN", background="#b6fcb6")
            tree.tag_configure("PURPLE", background="#e0b3ff")
            tree.tag_configure("BLUE", background="#add8e6")
            tree.tag_configure("YELLOW", background="#fffab3")
            tree.tag_configure("ORANGE", background="#ffd1a4")
            tree.tag_configure("PINK", background="#ffccdc")
            tree.tag_configure("UNKNOWN", background="#eeeeee")

        self.current_text = ""
        self.load_history()
        self.load_response_history()

    def record_audio(self):
        self.label.config(text="I listen better when you wait for 3 seconds and keep the everyday event short and sweet!")
        self.root.update()
        self.current_text = recognize_from_mic()
        self.label.config(text="Finished Recording! Wait a moment before navigating between pages.")
        self.transcription.config(text=self.current_text)
        self.keep_btn.config(state='normal')
        self.discard_btn.config(state='normal')

    def keep_text(self):
        try:
            husky_id = simpledialog.askinteger("Colour your Lens", "Enter ID:")
            if husky_id is None:
                self.label.config(text="Input cancelled.")
                return

            husky_map = load_husky_map()
            mapping = husky_map.get(husky_id, {'prompt': 'Describe this.', 'color': 'BLUE'})
            save_to_csv(self.current_text, husky_id)
            
            if self.start_callback:
                ai_response, color = self.start_callback(self.current_text, husky_id)
                self.label.config(text=(
                    f"WonderSparked!\n"
                    f"{ai_response[:20]}\n"
                    f"Color: {color} \n Explore the other pages to see."
                ))
            else:
                self.label.config(text=f"Saved with ID {husky_id} ({mapping['color']})")
            
            self.transcription.config(text="")
            self.keep_btn.config(state='disabled')
            self.discard_btn.config(state='disabled')
            self.load_history()
            self.load_response_history()

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
        for record in load_csv_history():
            if len(record) >= 3:
                timestamp, husky_id, event_text = record
                try:
                    husky_id_int = int(husky_id)
                    color = self.husky_map.get(husky_id_int, {}).get("color", "UNKNOWN")
                except (ValueError, TypeError):
                    color = "UNKNOWN"
                self.tree.insert("", tk.END, values=(timestamp, husky_id, event_text), tags=(color,))

    def load_response_history(self):
        for row in self.response_tree.get_children():
            self.response_tree.delete(row)
        for record in load_response_history():
            if len(record) >= 2:
                husky_id, response = record
                try:
                    husky_id_int = int(husky_id)
                    color = self.husky_map.get(husky_id_int, {}).get("color", "UNKNOWN")
                except (ValueError, TypeError):
                    color = "UNKNOWN"
                self.response_tree.insert("", tk.END, values=(response,), tags=(color,))


    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = LookingGlass()
    app.run()
