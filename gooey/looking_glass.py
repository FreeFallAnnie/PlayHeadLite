import tkinter as tk
from tkinter import simpledialog, ttk
import csv
import queue
import sounddevice as sd
import sys
import json
import time
from vosk import Model, KaldiRecognizer
from datetime import datetime
import os

# Set path to model relative to this file
MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'merge', 'model')
ARCHIVE_CSV = os.path.join(os.path.dirname(__file__), '..', 'archive', 'everyday.csv')

q = queue.Queue()

def callback(indata, frames, time_info, status):
    if status:
        print(status, file=sys.stderr)
    q.put(bytes(indata))

def recognize_from_mic(duration=10):
    model = Model(MODEL_PATH)
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

class LookingGlass:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Looking Glass")

        self.label = tk.Label(self.root, text="Press Record to begin!", font=("Helvetica", 16))
        self.label.pack(pady=20)

        self.record_btn = tk.Button(self.root, text="🎧 Record Event", command=self.record_audio)
        self.record_btn.pack(pady=10)

        self.keep_btn = tk.Button(self.root, text="Keep", command=self.keep_text, state='disabled')
        self.discard_btn = tk.Button(self.root, text="Discard", command=self.discard_text, state='disabled')
        self.keep_btn.pack(side=tk.LEFT, padx=10, pady=10)
        self.discard_btn.pack(side=tk.RIGHT, padx=10, pady=10)

        self.transcription = tk.Label(self.root, text="", wraplength=500, justify="left")
        self.transcription.pack(pady=20)

        self.current_text = ""

    def record_audio(self):
        self.label.config(text="Recording for 10 seconds...")
        self.root.update()
        self.current_text = recognize_from_mic()
        self.label.config(text="Finished Recording")
        self.transcription.config(text=self.current_text)
        self.keep_btn.config(state='normal')
        self.discard_btn.config(state='normal')

    def keep_text(self):
        save_to_csv(self.current_text)
        self.label.config(text="Saved to everyday.csv")
        self.transcription.config(text="")
        self.keep_btn.config(state='disabled')
        self.discard_btn.config(state='disabled')

    def discard_text(self):
        self.label.config(text="Input discarded.")
        self.transcription.config(text="")
        self.keep_btn.config(state='disabled')
        self.discard_btn.config(state='disabled')

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = LookingGlass()
    app.run()
