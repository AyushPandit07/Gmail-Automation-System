import os
import sys
import platform
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
import pandas as pd
from datetime import datetime
from automation import GmailAutomation



DARK_BG = "#0f172a"      # slate-900
CARD_BG = "#111827"      # slate-800
TEXT = "#e5e7eb"         # slate-200
MUTED = "#9ca3af"        # slate-400
ACCENT = "#2563eb"       # blue-600
ACCENT_DARK = "#1d4ed8"  # blue-700
SUCCESS = "#22c55e"      # green-500
WARN = "#f59e0b"         # amber-500
DANGER = "#ef4444"       # red-500"
HEADER_LEFT = "#0ea5e9"  # sky-500
HEADER_RIGHT = "#6366f1" # indigo-500


class GmailBotGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Gmail Automation System")
        self.geometry("900x650")
        self.configure(bg=DARK_BG)

        # Core objects
        self.bot = GmailAutomation()
        self.gmail_user = tk.StringVar()
        self.app_password = tk.StringVar()
        self.excel_path = tk.StringVar()
        self.lead_count_var = tk.StringVar(value="0")

        # ttk theme + styles
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background=DARK_BG)
        style.configure("Card.TFrame", background=CARD_BG)
        style.configure("TLabel", background=DARK_BG, foreground=TEXT, font=("Segoe UI", 10))
        style.configure("Card.TLabel", background=CARD_BG, foreground=TEXT, font=("Segoe UI", 10))
        style.configure("Title.TLabel", background=DARK_BG, foreground=TEXT, font=("Segoe UI", 12, "bold"))
        style.configure("Badge.TLabel", background=SUCCESS, foreground="white", font=("Segoe UI", 10, "bold"))
        style.configure("TEntry", fieldbackground="#0b1220", foreground=TEXT, insertcolor=TEXT, padding=6)
        style.configure("Card.TLabelframe", background=CARD_BG, foreground=MUTED, padding=10)
        style.configure("Card.TLabelframe.Label", background=CARD_BG, foreground="#93c5fd", font=("Segoe UI", 11, "bold"))
        style.configure("Primary.TButton", font=("Segoe UI", 11, "bold"), padding=8)
        style.configure("Danger.TButton", font=("Segoe UI", 11, "bold"), padding=8)
        style.map(
            "Primary.TButton",
            background=[("!disabled", ACCENT), ("active", ACCENT_DARK)],
            foreground=[("!disabled", "white")],
        )
        style.map(
            "Danger.TButton",
            background=[("!disabled", DANGER), ("active", "#b91c1c")],
            foreground=[("!disabled", "white")],
        )
        style.configure("Ghost.TButton", font=("Segoe UI", 10), padding=6)
        style.map(
            "Ghost.TButton",
            background=[("!disabled", CARD_BG), ("active", "#0b1220")],
            foreground=[("!disabled", MUTED)],
            relief=[("!disabled", "flat")]
        )
        style.configure("Link.TButton", font=("Segoe UI", 10, "underline"))
        style.map(
            "Link.TButton",
            background=[("!disabled", CARD_BG), ("active", CARD_BG)],
            foreground=[("!disabled", "#93c5fd")]
        )

        self._build_ui()

    # ---------------- UI BUILD ----------------

    def _build_ui(self):
        # Header banner with gradient
        header = tk.Canvas(self, height=90, highlightthickness=0, bd=0)
        header.pack(fill="x")
        self._draw_horizontal_gradient(header, HEADER_LEFT, HEADER_RIGHT)
        header.create_text(
            20, 45, anchor="w",
            text="📧 Gmail Automation System",
            font=("Segoe UI", 22, "bold"),
            fill="white"
        )

        # Top actions row
        top = ttk.Frame(self)
        top.pack(fill="x", padx=16, pady=(10, 4))

        # Lead badge
        badge_frame = ttk.Frame(top, style="Card.TFrame")
        badge_frame.pack(side="right", padx=6)
        ttk.Label(badge_frame, text="Leads", style="Card.TLabel", foreground=MUTED).grid(row=0, column=0, padx=10, pady=(8, 0), sticky="e")
        self.lead_badge = ttk.Label(
            badge_frame, textvariable=self.lead_count_var, style="Badge.TLabel", anchor="center"
        )
        self.lead_badge.grid(row=1, column=0, padx=10, pady=8, sticky="e")

        # Cards grid
        grid = ttk.Frame(self)
        grid.pack(fill="both", expand=True, padx=16, pady=8)

        # --- Gmail credentials card ---
        creds_card = ttk.Labelframe(grid, text="Gmail Login", style="Card.TLabelframe")
        creds_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=(0, 8))
        ttk.Label(creds_card, text="Gmail Address:", style="Card.TLabel").grid(row=0, column=0, padx=8, pady=8, sticky="w")
        ttk.Entry(creds_card, textvariable=self.gmail_user, width=34).grid(row=0, column=1, padx=8, pady=8, sticky="w")

        ttk.Label(creds_card, text="App Password:", style="Card.TLabel").grid(row=1, column=0, padx=8, pady=8, sticky="w")
        ttk.Entry(creds_card, textvariable=self.app_password, width=34, show="*").grid(row=1, column=1, padx=8, pady=8, sticky="w")

        # Quick links under creds
        links = ttk.Frame(creds_card, style="Card.TFrame")
        links.grid(row=2, column=0, columnspan=2, sticky="w", padx=6, pady=(2, 0))
        ttk.Button(links, text="❔ What’s an App Password?", style="Link.TButton",
                   command=self._explain_app_password).pack(side="left", padx=4)
        ttk.Button(links, text="📝 Open messages.json", style="Link.TButton",
                   command=self._open_messages_json).pack(side="left", padx=8)

        # --- Excel card ---
        excel_card = ttk.Labelframe(grid, text="Leads Excel", style="Card.TLabelframe")
        excel_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=(0, 8))
        self.excel_entry = ttk.Entry(excel_card, textvariable=self.excel_path, width=45)
        self.excel_entry.grid(row=0, column=0, padx=8, pady=8, sticky="w")
        ttk.Button(excel_card, text="📂 Browse", style="Primary.TButton",
                   command=self.browse_excel).grid(row=0, column=1, padx=6, pady=8)
        ttk.Button(excel_card, text="📥 Load", style="Primary.TButton",
                   command=self.load_excel).grid(row=0, column=2, padx=6, pady=8)

        # --- Controls card ---
        ctrl_card = ttk.Labelframe(grid, text="Controls", style="Card.TLabelframe")
        ctrl_card.grid(row=1, column=0, sticky="nsew", padx=(0, 8), pady=(8, 0))
        ttk.Button(ctrl_card, text="▶ Start Automation", style="Primary.TButton",
                   command=self.start_automation).grid(row=0, column=0, padx=8, pady=10, sticky="w")
        ttk.Button(ctrl_card, text="⏹ Stop Automation", style="Danger.TButton",
                   command=self.stop_automation).grid(row=0, column=1, padx=8, pady=10, sticky="w")
        ttk.Button(ctrl_card, text="🧹 Clear Logs", style="Ghost.TButton",
                   command=self.clear_logs).grid(row=0, column=2, padx=8, pady=10, sticky="w")

        # --- Logs card ---
        logs_card = ttk.Labelframe(grid, text="Automation Logs", style="Card.TLabelframe")
        logs_card.grid(row=1, column=1, sticky="nsew", padx=(8, 0), pady=(8, 0))
        self.log_box = ScrolledText(logs_card, height=16, bg="#0b1220", fg=TEXT, insertbackground=TEXT, relief="flat")
        self.log_box.pack(fill="both", expand=True, padx=6, pady=6)
        self._init_log_tags()

        # Grid weights
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)
        grid.rowconfigure(1, weight=1)

        # Status bar
        self.status = tk.Label(self, text="Ready", bg=DARK_BG, fg=MUTED, anchor="w", padx=12)
        self.status.pack(fill="x", side="bottom")

    # --------------- HELPERS ------------------

    def _draw_horizontal_gradient(self, canvas, color1, color2):
        """Draw a simple left→right gradient in the header canvas."""
        width = self.winfo_screenwidth()
        height = 90
        canvas.config(width=width, height=height)
        # Parse hex to rgb
        def hex_to_rgb(h): return tuple(int(h[i:i+2], 16) for i in (1, 3, 5))
        r1, g1, b1 = hex_to_rgb(color1)
        r2, g2, b2 = hex_to_rgb(color2)
        steps = width
        for i in range(steps):
            t = i / max(1, steps - 1)
            r = int(r1 + (r2 - r1) * t)
            g = int(g1 + (g2 - g1) * t)
            b = int(b1 + (b2 - b1) * t)
            canvas.create_line(i, 0, i, height, fill=f"#{r:02x}{g:02x}{b:02x}")

    def _init_log_tags(self):
        self.log_box.tag_config("time", foreground=MUTED)
        self.log_box.tag_config("ok", foreground=SUCCESS)
        self.log_box.tag_config("info", foreground="#93c5fd")    # light blue
        self.log_box.tag_config("warn", foreground=WARN)
        self.log_box.tag_config("err", foreground=DANGER)

    def _tag_for_message(self, msg: str) -> str:
        m = msg.lower()
        if "error" in m or "failed" in m or "invalid" in m:
            return "err"
        if "follow-up" in m or "auto-replied" in m or "sent initial" in m or "loaded" in m:
            return "ok"
        if "started" in m or "stopped" in m or "ready" in m:
            return "info"
        if "warning" in m or "no leads" in m:
            return "warn"
        return "info"

    def _open_messages_json(self):
        """Open messages.json in the default editor."""
        path = os.path.abspath("messages.json")
        if not os.path.exists(path):
            messagebox.showinfo("messages.json", "messages.json not found next to the app.")
            return
        try:
            if platform.system() == "Windows":
                os.startfile(path)            # type: ignore[attr-defined]
            elif platform.system() == "Darwin":
                subprocess.call(["open", path])
            else:
                subprocess.call(["xdg-open", path])
        except Exception as e:
            messagebox.showerror("Open File", f"Couldn't open messages.json:\n{e}")

    def _explain_app_password(self):
        messagebox.showinfo(
            "App Password?",
            "Use a Google App Password, not your normal Gmail password.\n\n"
            "Steps:\n"
            "1) Turn ON 2-Step Verification in Google Account → Security.\n"
            "2) Click App Passwords → choose Mail / Device → generate.\n"
            "3) Paste the 16-character password here."
        )

    # --------------- IO + LOGGING ----------------

    def browse_excel(self):
        path = filedialog.askopenfilename(filetypes=[("Excel Files", "*.xlsx;*.xls")])
        if path:
            self.excel_path.set(path)
            self.status.config(text=f"Selected: {os.path.basename(path)}")

    def load_excel(self):
    # Prevent loading Excel while automation is running
        if self.bot and self.bot.running:
            self.log("⚠️ Cannot load new Excel file during automation. Please stop automation first.", "warn")
            messagebox.showwarning("Warning", "You cannot load a new Excel file during automation.\nStop the automation first.")
            return

        try:
            df = pd.read_excel(self.excel_path.get())
            if not {'Name', 'Email'}.issubset(df.columns):
                messagebox.showerror("Error", "Excel must have 'Name' and 'Email' columns.")
                return
            self.bot.leads = list(zip(df['Name'], df['Email']))
            self.lead_count_var.set(str(len(self.bot.leads)))
            self.log("✅ Loaded leads from Excel.", "ok")
            self.status.config(text=f"Loaded {len(self.bot.leads)} leads.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load Excel: {e}")
            self.log(f"Error loading Excel: {e}", "err")


    def clear_logs(self):
        self.log_box.delete("1.0", "end")
        self.status.config(text="Logs cleared.")

    def log(self, text: str, tag: str | None = None):
        timestamp = datetime.now().strftime("%H:%M:%S")
        the_tag = tag or self._tag_for_message(text)
        self.log_box.insert("end", f"{timestamp}  ", ("time",))
        self.log_box.insert("end", text + "\n", (the_tag,))
        self.log_box.see("end")

    # --------------- AUTOMATION CONTROLS ----------------

    def start_automation(self):
        if not self.bot.leads:
            messagebox.showwarning("No Leads", "Please load leads from Excel first.")
            self.log("No leads loaded.", "warn")
            return
        gmail_user = self.gmail_user.get().strip()
        app_password = self.app_password.get().strip()
        if not gmail_user or not app_password:
            messagebox.showwarning("Missing Data", "Enter Gmail credentials.")
            self.log("Missing Gmail or App Password.", "warn")
            return
        self.bot.start(gmail_user, app_password, self.log)
        self.status.config(text="Running… listening for replies and scheduling follow-ups.")

    def stop_automation(self):
        self.bot.stop()
        self.log("🛑 Automation stopped.", "info")
        self.status.config(text="Stopped.")


if __name__ == "__main__":
    app = GmailBotGUI()
    app.mainloop()
