import os
import json
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext


class MessageObject:
    def __init__(self, ID, Timestamp, Contents):
        self.ID = ID
        # Convert Discord timestamp to Python datetime
        # Handles "Z" suffix for UTC
        Timestamp = Timestamp.replace("Z", "+00:00")
        self.Timestamp = datetime.fromisoformat(Timestamp)
        self.Contents = Contents


class DiscordSummarizerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Discord Data Summarizer")

        # Main frame
        frame = tk.Frame(root, padx=10, pady=10)
        frame.pack(fill="both", expand=True)

        # Path selection
        self.path_label = tk.Label(frame, text="No folder selected")
        self.path_label.pack(anchor="w")

        self.select_btn = tk.Button(frame, text="Select Discord Data Folder", command=self.select_folder)
        self.select_btn.pack(pady=5)

        # Debug toggle
        self.debug_var = tk.IntVar()
        self.debug_check = tk.Checkbutton(frame, text="Show extra debug info", variable=self.debug_var)
        self.debug_check.pack(anchor="w", pady=5)

        # Run button
        self.run_btn = tk.Button(frame, text="Process", command=self.process)
        self.run_btn.pack(pady=10)

        # Output text window (scrollable)
        self.output = scrolledtext.ScrolledText(frame, height=25, width=90)
        self.output.pack(pady=10)

        self.dir_path = None


    def log(self, text):
        self.output.insert("end", text + "\n")
        self.output.see("end")

    def select_folder(self):
        self.dir_path = filedialog.askdirectory()
        if self.dir_path:
            self.path_label.config(text=self.dir_path)

    def process(self):
        if not self.dir_path:
            messagebox.showerror("Error", "Please select a folder first.")
            return

        index_path = os.path.join(self.dir_path, "messages", "index.json")
        if not os.path.isfile(index_path):
            messagebox.showerror("Error", "Folder does not contain messages/index.json\nThis is not a valid Discord data export.")
            return

        show_debug = bool(self.debug_var.get())

        self.output.delete("1.0", "end")
        self.log("Processing messages...\nThis may take a while.\n")

        try:
            self.do_summarization(self.dir_path, show_debug)
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred:\n{e}")

    def do_summarization(self, dir_path, show_extra_debug):
        years = [2025, 2024, 2023, 2022, 2021, 2020]

        # Counters
        year_counts = {y: 0 for y in years}
        per_channel = {y: {} for y in years}

        # Load channel map
        with open(os.path.join(dir_path, "messages", "index.json"), "r", encoding="utf-8") as f:
            channel_map = json.load(f)

        msg_root = os.path.join(dir_path, "messages")

        for folder in os.listdir(msg_root):
            full_path = os.path.join(msg_root, folder)

            if not os.path.isdir(full_path):
                continue
            if folder == "index.json":
                continue
            if not folder.startswith("_"):
                continue
            
            # Extract channel ID
            try:
                channel_id = int(folder[1:])
            except:
                continue

            for y in years:
                per_channel[y][channel_id] = 0

            if show_extra_debug:
                channel_name = channel_map.get(str(channel_id), "(unknown)")
                self.log(f"{channel_id}: {channel_name}")

            messages_path = os.path.join(full_path, "messages.json")
            if not os.path.isfile(messages_path):
                continue

            with open(messages_path, "r", encoding="utf-8") as f:
                raw = json.load(f)

            messages = [
                MessageObject(
                    x.get("ID", 0),
                    x.get("Timestamp", "1970-01-01T00:00:00"),
                    x.get("Contents", "")
                ) for x in raw
            ]

            # Count per year
            for msg in messages:
                y = msg.Timestamp.year
                if y in year_counts:
                    year_counts[y] += 1
                    per_channel[y][channel_id] += 1

        # Print results
        self.log("\nSummary:\n")

        for y in years:
            self.log(f"{y}: {year_counts[y]} messages")

        self.log("\nMost active channels by year:\n")

        for y in years:
            sorted_items = sorted(per_channel[y].items(), key=lambda x: x[1], reverse=True)
            self.log(f"Top channels in {y}:")
            for cid, _ in sorted_items[:5]:
                name = channel_map.get(str(cid), "(unknown)")
                self.log(f"    {name}")
            self.log("")

        self.log("\nFinished.\n")


if __name__ == "__main__":
    root = tk.Tk()
    app = DiscordSummarizerGUI(root)
    root.mainloop()