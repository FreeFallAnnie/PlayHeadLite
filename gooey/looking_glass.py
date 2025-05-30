import tkinter as tk
from tkinter import simpledialog

class LookingGlass:
    def __init__(self, start_callback):
        self.root = tk.Tk()
        self.root.title("Looking Glass")
        self.start_callback = start_callback

        self.label = tk.Label(self.root, text="Press Start to begin!", font=("Helvetica", 16))
        self.label.pack(pady=20)

        self.start_btn = tk.Button(self.root, text="Start", command=self.collect_input)
        self.start_btn.pack()

        self.keep_btn = tk.Button(self.root, text="Keep", command=lambda: self.respond('KEEP'), state='disabled')
        self.discard_btn = tk.Button(self.root, text="Discard", command=lambda: self.respond('DISCARD'), state='disabled')
        self.keep_btn.pack(side=tk.LEFT, padx=10, pady=10)
        self.discard_btn.pack(side=tk.RIGHT, padx=10, pady=10)

        self.result = tk.Label(self.root, text="", wraplength=500, justify="left")
        self.result.pack(pady=20)

    def collect_input(self):
        self.user_input = simpledialog.askstring("User Input", "What do you want to say?")
        self.husky_id = simpledialog.askinteger("Husky ID", "Enter HuskyLens ID:")
        self.keep_btn.config(state='normal')
        self.discard_btn.config(state='normal')
        self.label.config(text="Choose to keep or discard the response.")

    def respond(self, decision):
        response, color = self.start_callback(self.user_input, self.husky_id, decision)
        self.result.config(text=f"{response}\n\n(Color shown: {color})")
        self.keep_btn.config(state='disabled')
        self.discard_btn.config(state='disabled')

    def run(self):
        self.root.mainloop()
