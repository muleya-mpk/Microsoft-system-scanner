"""
SysGuard Desktop — Windows System Maintenance Tool
Requires Python 3.8+ (built-in tkinter, no extra installs needed)
Run: python sysguard_desktop.py   (as Administrator for full functionality)
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import subprocess
import threading
import datetime
import os
import sys
import ctypes

# ── Colour palette ──────────────────────────────────────────────────────────
C = {
    "bg":        "#080c0a",
    "surface":   "#0d1410",
    "surface2":  "#111a14",
    "border":    "#1a2e1e",
    "green":     "#00ff6a",
    "green_dim": "#00c44f",
    "amber":     "#ffb700",
    "red":       "#ff4444",
    "text":      "#c8e8d0",
    "text_dim":  "#4a7a58",
    "white":     "#ffffff",
}

# ── Stage definitions ────────────────────────────────────────────────────────
STAGES = [
    {
        "id":      1,
        "title":   "Disk Drive Status",
        "cmd":     "wmic diskdrive get status",
        "desc":    "Checks hardware-level health of all connected drives.",
        "good":    "All entries should read OK.",
        "warn":    "Any other value may indicate drive problems.",
        "ssd_ok":  True,
    },
    {
        "id":      2,
        "title":   "Filesystem Light Scan",
        "cmd":     "chkdsk C: /scan",
        "desc":    "Non-destructive read-only scan of the C: filesystem.",
        "good":    "No problems found.",
        "warn":    "If errors found, run Deep Repair in Final Actions.",
        "ssd_ok":  True,
    },
    {
        "id":      3,
        "title":   "System File Verification",
        "cmd":     "sfc /scannow",
        "desc":    "Scans & auto-repairs protected Windows system files.",
        "good":    "did not find any integrity violations",
        "warn":    "If repairs fail, run DISM first then re-run SFC.",
        "ssd_ok":  True,
    },
    {
        "id":      4,
        "title":   "Drive Defragmentation",
        "cmd":     "defrag C: /u /v",
        "desc":    "Defragments C: drive. Skip if drive is an SSD.",
        "good":    "Defragmentation complete.",
        "warn":    "SSD users: skip this stage — Windows handles it automatically.",
        "ssd_ok":  False,
    },
    {
        "id":      5,
        "title":   "DISM Image Scan",
        "cmd":     "DISM /Online /Cleanup-Image /ScanHealth",
        "desc":    "Scans the Windows component store for corruption.",
        "good":    "No component store corruption detected.",
        "warn":    "If corruption found, run RestoreHealth in Final Actions.",
        "ssd_ok":  True,
    },
]


# ── Helpers ──────────────────────────────────────────────────────────────────
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False   # Non-Windows (dev/test)


def run_command(cmd, output_widget, on_finish=None):
    """Run a shell command and stream output to a ScrolledText widget."""
    def worker():
        output_widget.config(state="normal")
        output_widget.insert("end", f"\n> {cmd}\n", "cmd")
        output_widget.see("end")
        try:
            proc = subprocess.Popen(
                cmd, shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            for line in proc.stdout:
                output_widget.insert("end", line, "output")
                output_widget.see("end")
            proc.wait()
            rc = proc.returncode
            tag = "ok" if rc == 0 else "err"
            output_widget.insert("end", f"\n[Exit code: {rc}]\n", tag)
        except Exception as e:
            output_widget.insert("end", f"\nError: {e}\n", "err")
        output_widget.insert("end", "─" * 60 + "\n", "dim")
        output_widget.see("end")
        output_widget.config(state="disabled")
        if on_finish:
            output_widget.after(0, on_finish)

    threading.Thread(target=worker, daemon=True).start()


# ── Main Application ─────────────────────────────────────────────────────────
class SysGuardApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SysGuard — Windows System Scanner")
        self.geometry("1060x720")
        self.minsize(820, 560)
        self.configure(bg=C["bg"])
        self.stage_states = {s["id"]: "pending" for s in STAGES}  # pending/running/done/error
        self._build_ui()
        self._check_admin()
        self._start_clock()

    # ── Admin check ──────────────────────────────────────────────────────────
    def _check_admin(self):
        if not is_admin():
            self._log(
                "⚠  NOT running as Administrator. Some commands will fail.\n"
                "   Restart this app via right-click → 'Run as administrator'.\n",
                "warn"
            )
        else:
            self._log("✓  Running as Administrator.\n", "ok")

    # ── Clock ────────────────────────────────────────────────────────────────
    def _start_clock(self):
        def tick():
            now = datetime.datetime.now().strftime("%H:%M:%S")
            self.clock_var.set(now)
            self.after(1000, tick)
        tick()

    # ── UI Build ─────────────────────────────────────────────────────────────
    def _build_ui(self):
        self._configure_styles()

        # ── Top bar ──
        top = tk.Frame(self, bg=C["bg"], pady=10)
        top.pack(fill="x", padx=20)

        tk.Label(top, text="SYS", font=("Courier New", 28, "bold"),
                 bg=C["bg"], fg=C["white"]).pack(side="left")
        tk.Label(top, text="GUARD", font=("Courier New", 28, "bold"),
                 bg=C["bg"], fg=C["green"]).pack(side="left")

        meta = tk.Frame(top, bg=C["bg"])
        meta.pack(side="right")
        self.clock_var = tk.StringVar(value="--:--:--")
        tk.Label(meta, textvariable=self.clock_var,
                 font=("Courier New", 9), bg=C["bg"], fg=C["text_dim"]).pack(anchor="e")
        tk.Label(meta, text="Target: C:\\   |   Windows 10/11",
                 font=("Courier New", 8), bg=C["bg"], fg=C["text_dim"]).pack(anchor="e")

        # Separator
        tk.Frame(self, bg=C["border"], height=1).pack(fill="x", padx=20)

        # Admin banner
        self.admin_banner = tk.Frame(self, bg="#1a1400", padx=12, pady=6)
        self.admin_banner.pack(fill="x", padx=20, pady=(6, 0))
        tk.Label(self.admin_banner,
                 text="⚠  Run as Administrator for full functionality",
                 font=("Courier New", 8), bg="#1a1400", fg=C["amber"]).pack(side="left")

        # ── Main paned layout ──
        paned = tk.PanedWindow(self, orient="horizontal", bg=C["bg"],
                               sashwidth=4, sashrelief="flat",
                               sashpad=0)
        paned.pack(fill="both", expand=True, padx=20, pady=10)

        # Left panel — stages list
        left = tk.Frame(paned, bg=C["bg"], width=300)
        paned.add(left, minsize=240)
        self._build_left_panel(left)

        # Right panel — output + final actions
        right = tk.Frame(paned, bg=C["bg"])
        paned.add(right, minsize=400)
        self._build_right_panel(right)

        # ── Status bar ──
        bar = tk.Frame(self, bg=C["surface2"], padx=12, pady=4)
        bar.pack(fill="x", side="bottom")
        self.status_var = tk.StringVar(value="Ready.")
        tk.Label(bar, textvariable=self.status_var,
                 font=("Courier New", 8), bg=C["surface2"], fg=C["text_dim"]).pack(side="left")
        self.progress_var = tk.StringVar(value="0 / 5")
        tk.Label(bar, textvariable=self.progress_var,
                 font=("Courier New", 8), bg=C["surface2"], fg=C["green"]).pack(side="right")

    def _build_left_panel(self, parent):
        tk.Label(parent,
                 text="SCAN STAGES",
                 font=("Courier New", 8, "bold"),
                 bg=C["bg"], fg=C["text_dim"],
                 anchor="w").pack(fill="x", pady=(0, 6))

        self.stage_frames = {}
        self.stage_btns = {}
        self.stage_labels = {}

        for s in STAGES:
            frame = tk.Frame(parent, bg=C["surface"], bd=0,
                             highlightbackground=C["border"], highlightthickness=1,
                             padx=12, pady=10)
            frame.pack(fill="x", pady=3)

            # Stage number + status badge row
            header = tk.Frame(frame, bg=C["surface"])
            header.pack(fill="x")
            tk.Label(header,
                     text=f"STAGE {s['id']:02d}",
                     font=("Courier New", 7, "bold"),
                     bg=C["surface"], fg=C["text_dim"]).pack(side="left")
            badge = tk.Label(header,
                             text="PENDING",
                             font=("Courier New", 7),
                             bg=C["surface"], fg=C["text_dim"])
            badge.pack(side="right")
            self.stage_labels[s["id"]] = badge

            # Title
            tk.Label(frame,
                     text=s["title"],
                     font=("Courier New", 10, "bold"),
                     bg=C["surface"], fg=C["white"],
                     anchor="w").pack(fill="x", pady=(3, 1))

            # Description
            tk.Label(frame,
                     text=s["desc"],
                     font=("Courier New", 7),
                     bg=C["surface"], fg=C["text_dim"],
                     anchor="w", wraplength=220, justify="left").pack(fill="x")

            # Run button
            btn = tk.Button(frame,
                            text=f"▶  Run Stage {s['id']}",
                            font=("Courier New", 8),
                            bg=C["surface2"], fg=C["green"],
                            activebackground=C["green_dim"], activeforeground=C["bg"],
                            relief="flat", bd=0, padx=8, pady=5, cursor="hand2",
                            highlightbackground=C["border"], highlightthickness=1,
                            command=lambda sid=s["id"]: self._run_stage(sid))
            btn.pack(fill="x", pady=(8, 0))

            self.stage_frames[s["id"]] = frame
            self.stage_btns[s["id"]] = btn

        # Run All button
        tk.Frame(parent, bg=C["bg"], height=8).pack()
        run_all = tk.Button(parent,
                            text="▶▶  RUN ALL STAGES",
                            font=("Courier New", 9, "bold"),
                            bg=C["green_dim"], fg=C["bg"],
                            activebackground=C["green"], activeforeground=C["bg"],
                            relief="flat", bd=0, padx=8, pady=8, cursor="hand2",
                            command=self._run_all)
        run_all.pack(fill="x", pady=2)

        clear_btn = tk.Button(parent,
                              text="⬜  Clear Output",
                              font=("Courier New", 8),
                              bg=C["surface"], fg=C["text_dim"],
                              activebackground=C["surface2"], activeforeground=C["text"],
                              relief="flat", bd=0, padx=8, pady=6, cursor="hand2",
                              highlightbackground=C["border"], highlightthickness=1,
                              command=self._clear_output)
        clear_btn.pack(fill="x", pady=2)

    def _build_right_panel(self, parent):
        # Output area label
        tk.Label(parent,
                 text="COMMAND OUTPUT",
                 font=("Courier New", 8, "bold"),
                 bg=C["bg"], fg=C["text_dim"],
                 anchor="w").pack(fill="x", pady=(0, 4))

        # ScrolledText output
        self.output = scrolledtext.ScrolledText(
            parent,
            font=("Courier New", 9),
            bg=C["surface"], fg=C["text"],
            insertbackground=C["green"],
            selectbackground=C["green_dim"], selectforeground=C["bg"],
            relief="flat", bd=0,
            highlightbackground=C["border"], highlightthickness=1,
            wrap="word",
            state="disabled",
            height=20,
        )
        self.output.pack(fill="both", expand=True)

        # Output text tags
        self.output.tag_config("cmd",    foreground=C["green"],     font=("Courier New", 9, "bold"))
        self.output.tag_config("output", foreground=C["text"])
        self.output.tag_config("ok",     foreground=C["green_dim"])
        self.output.tag_config("warn",   foreground=C["amber"])
        self.output.tag_config("err",    foreground=C["red"])
        self.output.tag_config("dim",    foreground=C["text_dim"])
        self.output.tag_config("header", foreground=C["white"],     font=("Courier New", 10, "bold"))

        # ── Final Actions ──
        tk.Frame(parent, bg=C["border"], height=1).pack(fill="x", pady=(10, 6))
        tk.Label(parent,
                 text="FINAL ACTIONS",
                 font=("Courier New", 8, "bold"),
                 bg=C["bg"], fg=C["text_dim"],
                 anchor="w").pack(fill="x")

        btn_row = tk.Frame(parent, bg=C["bg"])
        btn_row.pack(fill="x", pady=(6, 0))

        def fa_btn(parent, text, color, cmd_str, col):
            f = tk.Frame(parent, bg=C["surface"],
                         highlightbackground=C["border"], highlightthickness=1)
            f.grid(row=0, column=col, sticky="nsew", padx=(0 if col == 0 else 4, 0))
            parent.columnconfigure(col, weight=1)
            tk.Label(f, text=text, font=("Courier New", 8, "bold"),
                     bg=C["surface"], fg=color, wraplength=180,
                     justify="left", anchor="w", padx=8, pady=6).pack(fill="x")
            tk.Button(f, text="▶  Run",
                      font=("Courier New", 8),
                      bg=C["surface2"], fg=color,
                      relief="flat", bd=0, padx=8, pady=5, cursor="hand2",
                      highlightbackground=C["border"], highlightthickness=1,
                      command=lambda c=cmd_str: self._run_custom(c)).pack(
                          fill="x", padx=8, pady=(0, 8))

        fa_btn(btn_row, "Deep Filesystem Repair\nchkdsk C: /f /r",
               C["amber"], "chkdsk C: /f /r", 0)
        fa_btn(btn_row, "DISM Restore Health\nDISM /RestoreHealth",
               C["amber"], "DISM /Online /Cleanup-Image /RestoreHealth", 1)
        fa_btn(btn_row, "Scheduled Restart\nshutdown /r /t 100",
               C["red"],   'shutdown /r /t 100 /c "SysGuard reboot"', 2)
        fa_btn(btn_row, "Abort Restart\nshutdown /a",
               C["green_dim"], "shutdown /a", 3)

    # ── Logic ────────────────────────────────────────────────────────────────
    def _log(self, text, tag="output"):
        self.output.config(state="normal")
        self.output.insert("end", text, tag)
        self.output.see("end")
        self.output.config(state="disabled")

    def _clear_output(self):
        self.output.config(state="normal")
        self.output.delete("1.0", "end")
        self.output.config(state="disabled")

    def _set_stage_state(self, sid, state):
        """state: pending | running | done | error"""
        self.stage_states[sid] = state
        badge = self.stage_labels[sid]
        frame = self.stage_frames[sid]
        btn   = self.stage_btns[sid]
        colors = {
            "pending": (C["text_dim"],  C["border"],  "PENDING"),
            "running": (C["amber"],     "#2a2000",    "RUNNING"),
            "done":    (C["green"],     C["green_dim"],"DONE"),
            "error":   (C["red"],       "#2a0000",    "ERROR"),
        }
        fg, hbg, label = colors.get(state, colors["pending"])
        badge.config(text=label, fg=fg)
        frame.config(highlightbackground=hbg)
        btn.config(state="disabled" if state == "running" else "normal")

        done_count = sum(1 for v in self.stage_states.values() if v == "done")
        self.progress_var.set(f"{done_count} / 5")

    def _run_stage(self, sid):
        stage = next(s for s in STAGES if s["id"] == sid)
        self._set_stage_state(sid, "running")
        self.status_var.set(f"Running Stage {sid}: {stage['title']}...")
        self._log(f"\n{'═'*60}\n  STAGE {sid}: {stage['title'].upper()}\n{'═'*60}\n", "header")
        self._log(f"  {stage['desc']}\n  Good: {stage['good']}\n", "dim")

        def done():
            self._set_stage_state(sid, "done")
            self.status_var.set(f"Stage {sid} complete.")

        run_command(stage["cmd"], self.output, on_finish=done)

    def _run_all(self):
        """Run all stages sequentially."""
        def run_next(idx=0):
            if idx >= len(STAGES):
                self.status_var.set("All stages complete.")
                self._log("\n✓  ALL STAGES COMPLETE\n", "ok")
                return
            sid = STAGES[idx]["id"]
            self._set_stage_state(sid, "running")
            stage = STAGES[idx]
            self.status_var.set(f"Running Stage {sid}: {stage['title']}...")
            self._log(f"\n{'═'*60}\n  STAGE {sid}: {stage['title'].upper()}\n{'═'*60}\n", "header")
            self._log(f"  {stage['desc']}\n", "dim")

            def done():
                self._set_stage_state(sid, "done")
                run_next(idx + 1)

            run_command(stage["cmd"], self.output, on_finish=done)

        self._clear_output()
        run_next()

    def _run_custom(self, cmd):
        self.status_var.set(f"Running: {cmd}")
        self._log(f"\n{'═'*60}\n  FINAL ACTION\n{'═'*60}\n", "header")
        run_command(cmd, self.output,
                    on_finish=lambda: self.status_var.set("Done."))

    def _configure_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")


# ── Entry point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = SysGuardApp()
    app.mainloop()
