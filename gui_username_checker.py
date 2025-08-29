import tkinter as tk
from tkinter import ttk
import requests, random, string, threading, queue, time, os
from datetime import datetime

HEADERS = {"User-Agent": "Mozilla/5.0"}
TIMEOUT = 3

def is_roblox_available(username):
    try:
        res = requests.get("https://auth.roblox.com/v1/usernames/validate",
                           params={"username": username, "birthday": "2000-01-01", "context": "Signup"},
                           headers=HEADERS, timeout=TIMEOUT).json()
        return res.get("code") == 0
    except Exception:
        return None

def is_youtube_available(username):
    try:
        r = requests.get(f"https://www.youtube.com/@{username}", headers=HEADERS, timeout=TIMEOUT)
        return r.status_code == 404
    except Exception:
        return None

def is_twitch_available(username):
    try:
        r = requests.get(f"https://www.twitch.tv/{username}", headers=HEADERS, timeout=TIMEOUT)
        return r.status_code == 404
    except Exception:
        return None

def is_github_available(username):
    try:
        r = requests.get(f"https://github.com/{username}", headers=HEADERS, timeout=TIMEOUT)
        return r.status_code == 404
    except Exception:
        return None

def is_instagram_available(username):
    try:
        r = requests.get(f"https://www.instagram.com/{username}/", headers=HEADERS, timeout=TIMEOUT)
        return r.status_code == 404
    except Exception:
        return None

def is_x_available(username):
    try:
        r = requests.get(f"https://x.com/{username}", headers=HEADERS, timeout=TIMEOUT)
        return r.status_code == 404
    except Exception:
        return None

def is_snapchat_available(username):
    try:
        r = requests.get(f"https://www.snapchat.com/add/{username}", headers=HEADERS, timeout=TIMEOUT)
        return r.status_code == 404
    except Exception:
        return None

def is_steam_available(username):
    try:
        r = requests.get(f"https://steamcommunity.com/id/{username}", headers=HEADERS, timeout=TIMEOUT)
        if r.status_code == 404:
            return True
        return "the specified profile could not be found" in r.text.lower()
    except Exception:
        return None

def is_minecraft_available(username):
    try:
        r = requests.get(f"https://api.mojang.com/users/profiles/minecraft/{username}", headers=HEADERS, timeout=TIMEOUT)
        if r.status_code == 204:
            return True
        if r.status_code == 200:
            return False
        return None
    except Exception:
        return None

PLATFORMS = {
    "Minecraft": is_minecraft_available,
    "Roblox": is_roblox_available,
    "GitHub": is_github_available,
    "YouTube": is_youtube_available,
    "Twitch": is_twitch_available,
    "Instagram": is_instagram_available,
    "X (Twitter)": is_x_available,
    "Snapchat": is_snapchat_available,
    "Steam": is_steam_available,
}

def random_username(length):
    alphabet = string.ascii_lowercase + string.digits
    return ''.join(random.choices(alphabet, k=length))

def get_available_filename():
    base = "available_usernames"
    ext = ".txt"
    counter = 0
    filename = base + ext
    while os.path.exists(filename):
        counter += 1
        filename = f"{base}{counter}{ext}"
    return filename

class Checker(threading.Thread):
    def __init__(self, platform, func, result_q, counter, length):
        super().__init__(daemon=True)
        self.platform, self.func, self.result_q, self.counter = platform, func, result_q, counter
        self.length = length
        self._stop = threading.Event()
        self.filename = get_available_filename()

    def stop(self):
        self._stop.set()

    def run(self):
        while not self._stop.is_set():
            uname = random_username(self.length)
            status = self.func(uname)
            self.result_q.put((uname, status, datetime.now()))
            self.counter["checked"] += 1
            if status is True:
                self.counter["available"] += 1
                with open(self.filename, "a", encoding="utf-8") as f:
                    f.write(f"{self.platform}:{uname}\n")
            time.sleep(0.4)

class App(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=12)
        self.pack(fill="both", expand=True)
        self.master.title("Username Sniper - Created by cyber600T (github.com/cyber600T)")
        self.master.geometry("820x600")

        self.result_q = queue.Queue()
        self.worker, self.running = None, False
        self.counter = {"checked": 0, "available": 0}

        self._build_controls()
        self._build_table()
        self._build_statusbar()

        self.master.protocol("WM_DELETE_WINDOW", self.on_close)
        self.after(80, self.poll_results)

    def _build_controls(self):
        bar = ttk.Frame(self); bar.pack(fill="x", pady=10)
        ttk.Label(bar, text="Platform").grid(row=0, column=0, padx=5)
        self.platform_var = tk.StringVar(value=list(PLATFORMS.keys())[0])
        ttk.Combobox(bar, textvariable=self.platform_var, values=list(PLATFORMS.keys()), state="readonly", width=15).grid(row=0, column=1, padx=5)
        
        ttk.Label(bar, text="Length").grid(row=0, column=2, padx=5)
        self.length_var = tk.IntVar(value=4)
        ttk.Spinbox(bar, from_=3, to=6, textvariable=self.length_var, width=5).grid(row=0, column=3, padx=5)
        
        self.start_btn = ttk.Button(bar, text="Start", command=self.start); self.start_btn.grid(row=0, column=4, padx=8)
        self.stop_btn = ttk.Button(bar, text="Stop", command=self.stop, state="disabled"); self.stop_btn.grid(row=0, column=5, padx=8)

    def _build_table(self):
        columns = ("time", "username", "status")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=20)
        for col, w in zip(columns, (150, 250, 120)):
            self.tree.heading(col, text=col.title())
            self.tree.column(col, width=w)
        self.tree.pack(fill="both", expand=True, pady=10)

    def _build_statusbar(self):
        bar = ttk.Frame(self)
        bar.pack(fill="x", pady=5)
        
        self.status_var = tk.StringVar(value="Checked: 0 | Available: 0")
        self.status_label = ttk.Label(bar, textvariable=self.status_var, anchor="w")
        self.status_label.pack(side="left", fill="x", expand=True)
        
        credit_label = ttk.Label(bar, text="Created by cyber600T", anchor="e")
        credit_label.pack(side="right")

    def start(self):
        if self.running: return
        self.running = True
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        platform = self.platform_var.get()
        length = self.length_var.get()
        func = PLATFORMS[platform]
        self.worker = Checker(platform, func, self.result_q, self.counter, length)
        self.worker.start()

    def stop(self):
        self.running = False
        if self.worker: self.worker.stop()
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")

    def poll_results(self):
        try:
            while True:
                uname, status, ts = self.result_q.get_nowait()
                status_str = "✅" if status is True else "❌" if status is False else "Error"
                self.tree.insert("", "end", values=(ts.strftime("%H:%M:%S"), uname, status_str))
                self.status_var.set(f"Checked: {self.counter['checked']} | Available: {self.counter['available']}")
        except queue.Empty:
            pass
        self.after(100, self.poll_results)

    def on_close(self):
        self.stop()
        self.master.destroy()

def main():
    root = tk.Tk()
    App(root)
    root.mainloop()

if __name__ == "__main__":
    main()
