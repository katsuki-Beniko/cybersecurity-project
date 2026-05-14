"""
Smart Factory Floor Monitor — Professional UI Client
HIGH DISTINCTION version

Features:
  - Login screen with role-based access (admin / operator)
  - Tabbed dashboard: Live | Chart | Alerts | Commands | Devices | Audit Log
  - MongoDB persistence for all sensor readings, alerts, commands, devices
  - Isolation Forest anomaly detection + trend prediction + anomaly classification
  - AI risk score 0-10 displayed as colour-coded bar
  - Real-time matplotlib temperature + humidity chart (embedded in GUI)
  - Device heartbeat monitoring — auto-marks devices offline after 60 s
  - Command acknowledgment tracking (PENDING → ACKNOWLEDGED)
  - Simulate Attack button for cybersecurity demonstration
  - Role restrictions: operators cannot send Emergency Cooling

Install: pip install paho-mqtt scikit-learn pymongo matplotlib
"""

import paho.mqtt.client as mqtt
import json
import queue
import threading
from datetime import datetime, timedelta

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox

import numpy as np
from sklearn.ensemble import IsolationForest

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import database as db
import auth
from config import *

# ─── AI ENGINE ────────────────────────────────────────────────────────────────

class AIEngine:
    """
    Combines Isolation Forest (anomaly detection), numpy trend prediction,
    and rule-based anomaly classification into a single risk score 0-10.
    """

    def __init__(self):
        self._model     = None
        self._samples   = []
        self._temps     = []      # last 10 temperatures for trend
        self._total     = 0
        self._fitted    = False
        self._lock      = threading.Lock()

    def process(self, temperature, humidity):
        """
        Returns (is_anomaly, anomaly_score, classification, risk_score, predicted_temp).
        predicted_temp is the extrapolated temperature 30 s from now (None if < 5 samples).
        """
        with self._lock:
            self._samples.append([temperature, humidity])
            self._temps.append(temperature)
            if len(self._temps) > 15:
                self._temps.pop(0)
            self._total += 1

            if self._total >= AI_MIN_SAMPLES:
                if not self._fitted or self._total % AI_REFIT_EVERY == 0:
                    self._fit()

            is_anomaly, score = False, 0.0
            if self._fitted:
                X     = np.array([[temperature, humidity]])
                pred  = self._model.predict(X)[0]
                score = round(float(self._model.score_samples(X)[0]), 4)
                is_anomaly = bool(pred == -1)

            classification  = self._classify(temperature, humidity, is_anomaly, score)
            risk_score      = self._risk(temperature, is_anomaly, score, classification)
            predicted_temp  = self._predict_temp()

            return is_anomaly, score, classification, risk_score, predicted_temp

    def _fit(self):
        X = np.array(self._samples[-300:])
        self._model = IsolationForest(
            n_estimators=100, contamination=CONTAMINATION, random_state=42)
        self._model.fit(X)
        self._fitted = True

    def _classify(self, temp, hum, is_anomaly, score):
        if not is_anomaly:
            return "NORMAL"
        if temp > 75 or temp < 5:
            return "SENSOR_FAULT"
        if hum > 92:
            return "HUMIDITY_SPIKE"
        if temp > TEMP_CRITICAL:
            return "OVERHEATING"
        return "INJECTION_ATTACK"

    def _risk(self, temp, is_anomaly, score, classification):
        risk = 0.0
        # Map anomaly score: lower score = higher risk
        if self._fitted:
            risk += max(0, min(4, (-score) * 8))
        # Temperature contribution
        if temp > TEMP_CRITICAL:
            risk += 2
        elif temp > TEMP_ALERT_THRESHOLD:
            risk += 1
        # Classification penalty
        if classification == "INJECTION_ATTACK":
            risk += 2
        elif classification in ("OVERHEATING", "SENSOR_FAULT"):
            risk += 1
        return round(min(10.0, risk), 1)

    def _predict_temp(self):
        if len(self._temps) < 5:
            return None
        x = np.arange(len(self._temps))
        coeffs = np.polyfit(x, self._temps, 1)
        next_x = len(self._temps) + 5   # 6 readings × 5 s = 30 s ahead
        return round(float(np.polyval(coeffs, next_x)), 2)

    @property
    def sample_count(self):
        return self._total

    @property
    def is_fitted(self):
        return self._fitted


# ─── LOGIN WINDOW ─────────────────────────────────────────────────────────────

class LoginWindow(tk.Tk):

    C_BG    = "#1e1e2e"
    C_PANEL = "#2a2a3e"
    C_ACCENT = "#89b4fa"
    C_TEXT  = "#cdd6f4"
    C_RED   = "#f38ba8"

    def __init__(self):
        super().__init__()
        self.title("Smart Factory Floor — Login")
        self.geometry("400x320")
        self.configure(bg=self.C_BG)
        self.resizable(False, False)
        self.current_user = None
        self._build()

    def _build(self):
        tk.Frame(self, bg=self.C_ACCENT, pady=10).pack(fill=tk.X)
        tk.Label(self.nametowidget("."), text="Smart Factory Floor",
                 font=("Consolas", 14, "bold"),
                 bg=self.C_ACCENT, fg=self.C_BG).place(x=0, y=10, width=400)

        bar = tk.Frame(self, bg=self.C_ACCENT, pady=10)
        bar.pack(fill=tk.X)
        tk.Label(bar, text="Smart Factory Floor",
                 font=("Consolas", 14, "bold"),
                 bg=self.C_ACCENT, fg=self.C_BG).pack()

        panel = tk.Frame(self, bg=self.C_PANEL, padx=30, pady=20)
        panel.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        tk.Label(panel, text="Username", font=("Consolas", 10),
                 bg=self.C_PANEL, fg=self.C_TEXT).grid(row=0, column=0, sticky="w", pady=5)
        self._user_var = tk.StringVar()
        ttk.Entry(panel, textvariable=self._user_var, width=22).grid(row=0, column=1, pady=5, padx=10)

        tk.Label(panel, text="Password", font=("Consolas", 10),
                 bg=self.C_PANEL, fg=self.C_TEXT).grid(row=1, column=0, sticky="w", pady=5)
        self._pass_var = tk.StringVar()
        ttk.Entry(panel, textvariable=self._pass_var, show="*", width=22).grid(row=1, column=1, pady=5, padx=10)

        self._err_var = tk.StringVar()
        tk.Label(panel, textvariable=self._err_var, font=("Consolas", 9),
                 bg=self.C_PANEL, fg=self.C_RED).grid(row=2, columnspan=2, pady=5)

        tk.Button(panel, text="Login",
                  font=("Consolas", 10, "bold"),
                  bg=self.C_ACCENT, fg=self.C_BG, bd=0, padx=20, pady=6,
                  cursor="hand2", command=self._attempt_login).grid(row=3, columnspan=2, pady=10)

        tk.Label(panel, text="admin / admin123   |   operator / operator123",
                 font=("Consolas", 8), bg=self.C_PANEL, fg="#6c7086").grid(row=4, columnspan=2)

        self.bind("<Return>", lambda e: self._attempt_login())

    def _attempt_login(self):
        user = auth.login(self._user_var.get().strip(), self._pass_var.get())
        if user:
            self.current_user = user
            self.destroy()
        else:
            self._err_var.set("Invalid username or password.")


# ─── MAIN DASHBOARD ───────────────────────────────────────────────────────────

class SmartFactoryApp(tk.Tk):

    C_BG      = "#1e1e2e"
    C_PANEL   = "#2a2a3e"
    C_SURFACE = "#11111b"
    C_ACCENT  = "#89b4fa"
    C_TEXT    = "#cdd6f4"
    C_GREEN   = "#a6e3a1"
    C_YELLOW  = "#f9e2af"
    C_RED     = "#f38ba8"
    C_PURPLE  = "#cba6f7"
    C_CYAN    = "#89dceb"

    def __init__(self, current_user):
        super().__init__()
        self._user = current_user
        self.title(f"Smart Factory Floor — {current_user['username']} ({current_user['role'].upper()})")
        self.geometry("1100x750")
        self.configure(bg=self.C_BG)
        self.resizable(True, True)

        self._msg_queue          = queue.Queue()
        self._ai                 = AIEngine()
        self._mqtt_client        = None
        self._msg_count          = 0
        self._anomaly_count      = 0
        self._consecutive_alerts = 0
        self._last_temp          = None
        self._last_hum           = None
        self._cooling_active     = False
        self._d1_last_hb         = None
        self._d2_last_hb         = None

        self._chart_temps  = []
        self._chart_hums   = []
        self._chart_times  = []

        self._build_ui()
        self._connect_mqtt()
        self.after(150, self._poll_queue)
        self.after(5000, self._refresh_devices_tab)
        self.after(10000, self._check_heartbeats)

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        # Title bar
        bar = tk.Frame(self, bg=self.C_ACCENT, pady=6)
        bar.pack(fill=tk.X)
        tk.Label(bar,
                 text=f"Smart Factory Floor Monitor   |   {self._user['username'].upper()}  [{self._user['role']}]",
                 font=("Consolas", 13, "bold"),
                 bg=self.C_ACCENT, fg=self.C_BG).pack(side=tk.LEFT, expand=True)
        tk.Button(bar, text="Logout",
                  font=("Consolas", 9, "bold"),
                  bg=self.C_BG, fg=self.C_ACCENT, bd=0, padx=10, pady=2,
                  cursor="hand2", command=self._logout).pack(side=tk.RIGHT, padx=10)

        # Notebook
        style = ttk.Style()
        style.theme_use("default")
        style.configure("TNotebook",       background=self.C_BG,    borderwidth=0)
        style.configure("TNotebook.Tab",   background=self.C_PANEL, foreground=self.C_TEXT,
                        font=("Consolas", 9, "bold"), padding=[12, 6])
        style.map("TNotebook.Tab",         background=[("selected", self.C_ACCENT)],
                  foreground=[("selected", self.C_BG)])

        self._nb = ttk.Notebook(self)
        self._nb.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        self._tab_live    = tk.Frame(self._nb, bg=self.C_BG)
        self._tab_chart   = tk.Frame(self._nb, bg=self.C_BG)
        self._tab_alerts  = tk.Frame(self._nb, bg=self.C_BG)
        self._tab_cmds    = tk.Frame(self._nb, bg=self.C_BG)
        self._tab_devices = tk.Frame(self._nb, bg=self.C_BG)
        self._tab_audit   = tk.Frame(self._nb, bg=self.C_BG)

        self._nb.add(self._tab_live,    text="  Live  ")
        self._nb.add(self._tab_chart,   text="  Chart  ")
        self._nb.add(self._tab_alerts,  text="  Alerts  ")
        self._nb.add(self._tab_cmds,    text="  Commands  ")
        self._nb.add(self._tab_devices, text="  Devices  ")
        self._nb.add(self._tab_audit,   text="  Audit Log  ")

        self._build_live_tab()
        self._build_chart_tab()
        self._build_alerts_tab()
        self._build_commands_tab()
        self._build_devices_tab()
        self._build_audit_tab()

        # Status bar
        sb = tk.Frame(self, bg=self.C_SURFACE)
        sb.pack(fill=tk.X)
        self._status_var = tk.StringVar(value="Connecting…")
        tk.Label(sb, textvariable=self._status_var,
                 font=("Consolas", 8), bg=self.C_SURFACE, fg=self.C_TEXT,
                 anchor="w").pack(side=tk.LEFT, padx=10, pady=2)

    # ── Live tab ──────────────────────────────────────────────────────────────

    def _build_live_tab(self):
        top = tk.Frame(self._tab_live, bg=self.C_BG)
        top.pack(fill=tk.X, padx=8, pady=6)

        # Sensor readings panel
        sf = self._panel(top, "  Sensor Readings  ")
        sf.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 4))
        self._temp_var = tk.StringVar(value="---.- °C")
        self._hum_var  = tk.StringVar(value="---.- %")
        self._vib_var  = tk.StringVar(value="-.--- mm/s")
        self._row(sf, 0, "Temperature :", self._temp_var, "temp_lbl", self.C_TEXT)
        self._row(sf, 1, "Humidity    :", self._hum_var,  "hum_lbl",  self.C_TEXT)
        self._row(sf, 2, "Vibration   :", self._vib_var,  "vib_lbl",  self.C_TEXT)

        # AI status panel
        af = self._panel(top, "  AI Engine  ")
        af.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4)
        self._ai_var      = tk.StringVar(value="Collecting data…")
        self._class_var   = tk.StringVar(value="---")
        self._risk_var    = tk.StringVar(value="Risk: --/10")
        self._predict_var = tk.StringVar(value="Predicted: ---")
        self._samples_var = tk.StringVar(value=f"0 / {AI_MIN_SAMPLES}  (training)")
        self._row(af, 0, "Status      :", self._ai_var,      "ai_lbl",      self.C_YELLOW)
        self._row(af, 1, "Class       :", self._class_var,   "class_lbl",   self.C_TEXT)
        self._row(af, 2, "Risk Score  :", self._risk_var,    "risk_lbl",    self.C_GREEN)
        self._row(af, 3, "Prediction  :", self._predict_var, "predict_lbl", self.C_CYAN)
        self._row(af, 4, "Samples     :", self._samples_var, "smp_lbl",     self.C_TEXT)

        # Device + cooling panel
        df = self._panel(top, "  Device Status  ")
        df.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(4, 0))
        self._d1_var      = tk.StringVar(value="Waiting…")
        self._d2_var      = tk.StringVar(value="Waiting…")
        self._cooling_var = tk.StringVar(value="OFF")
        self._row(df, 0, "Device 1 :", self._d1_var,      "d1_lbl",      self.C_YELLOW)
        self._row(df, 1, "Device 2 :", self._d2_var,      "d2_lbl",      self.C_YELLOW)
        self._row(df, 2, "Cooling  :", self._cooling_var, "cooling_lbl", self.C_GREEN)

        # Alert log
        lf = self._panel(self._tab_live, "  Live Alert Log  ")
        lf.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 4))
        self._log = scrolledtext.ScrolledText(
            lf, font=("Consolas", 9), bg=self.C_SURFACE, fg=self.C_TEXT,
            state=tk.DISABLED, wrap=tk.WORD, height=12)
        self._log.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self._log.tag_config("anomaly", foreground=self.C_RED)
        self._log.tag_config("alert",   foreground=self.C_YELLOW)
        self._log.tag_config("normal",  foreground=self.C_GREEN)
        self._log.tag_config("info",    foreground=self.C_ACCENT)
        self._log.tag_config("cmd",     foreground=self.C_PURPLE)

        # Command buttons
        cf = self._panel(self._tab_live, "  Quick Commands  ")
        cf.pack(fill=tk.X, padx=8, pady=(0, 6))
        bstyle = dict(font=("Consolas", 9, "bold"), bd=0, padx=12, pady=6, cursor="hand2")
        tk.Button(cf, text="Activate Cooling",   bg=self.C_GREEN,  fg=self.C_BG, command=self._cmd_activate,   **bstyle).pack(side=tk.LEFT, padx=4, pady=6)
        tk.Button(cf, text="Deactivate Cooling", bg=self.C_CYAN,   fg=self.C_BG, command=self._cmd_deactivate, **bstyle).pack(side=tk.LEFT, padx=4, pady=6)
        if self._user["role"] == ROLE_ADMIN:
            tk.Button(cf, text="Emergency Cooling", bg=self.C_RED,    fg=self.C_BG, command=self._cmd_emergency,  **bstyle).pack(side=tk.LEFT, padx=4, pady=6)
        tk.Button(cf, text="D2 Diagnostics",     bg=self.C_YELLOW, fg=self.C_BG, command=self._cmd_diagnostics,**bstyle).pack(side=tk.LEFT, padx=4, pady=6)
        tk.Button(cf, text="Status Check",       bg=self.C_ACCENT, fg=self.C_BG, command=self._cmd_status,     **bstyle).pack(side=tk.LEFT, padx=4, pady=6)
        tk.Button(cf, text="Simulate Attack",    bg="#ff5555",     fg="white",   command=self._cmd_simulate,   **bstyle).pack(side=tk.LEFT, padx=4, pady=6)

    # ── Chart tab ─────────────────────────────────────────────────────────────

    def _build_chart_tab(self):
        self._fig = Figure(figsize=(10, 5), facecolor=self.C_BG)
        self._ax_temp = self._fig.add_subplot(211)
        self._ax_hum  = self._fig.add_subplot(212)
        self._fig.tight_layout(pad=2.5)
        self._canvas = FigureCanvasTkAgg(self._fig, master=self._tab_chart)
        self._canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        tk.Button(self._tab_chart, text="Refresh Chart",
                  font=("Consolas", 9, "bold"), bg=self.C_ACCENT, fg=self.C_BG,
                  bd=0, padx=12, pady=5, cursor="hand2",
                  command=self._refresh_chart).pack(pady=(0, 8))
        self._refresh_chart()

    def _refresh_chart(self):
        temp_data = db.get_chart_data("temperature", 30)
        hum_data  = db.get_chart_data("humidity", 30)

        self._ax_temp.clear()
        self._ax_hum.clear()

        for ax in (self._ax_temp, self._ax_hum):
            ax.set_facecolor(self.C_SURFACE)
            ax.tick_params(colors=self.C_TEXT, labelsize=7)
            for spine in ax.spines.values():
                spine.set_edgecolor(self.C_PANEL)

        if temp_data:
            vals  = [d["value"] for d in temp_data]
            times = [d["timestamp"].strftime("%H:%M:%S") for d in temp_data]
            self._ax_temp.plot(times, vals, color=self.C_RED, linewidth=1.5, marker="o", markersize=3)
            self._ax_temp.axhline(TEMP_ALERT_THRESHOLD, color=self.C_YELLOW, linestyle="--", linewidth=1, label=f"Alert ({TEMP_ALERT_THRESHOLD}°C)")
            self._ax_temp.axhline(TEMP_CRITICAL, color=self.C_RED, linestyle="--", linewidth=1, label=f"Critical ({TEMP_CRITICAL}°C)")
            self._ax_temp.set_title("Temperature (°C)", color=self.C_TEXT, fontsize=9)
            self._ax_temp.legend(fontsize=7, facecolor=self.C_PANEL, labelcolor=self.C_TEXT)
            step = max(1, len(times) // 6)
            self._ax_temp.set_xticks(range(0, len(times), step))
            self._ax_temp.set_xticklabels(times[::step], rotation=30, ha="right", fontsize=7)

        if hum_data:
            vals  = [d["value"] for d in hum_data]
            times = [d["timestamp"].strftime("%H:%M:%S") for d in hum_data]
            self._ax_hum.plot(times, vals, color=self.C_CYAN, linewidth=1.5, marker="o", markersize=3)
            self._ax_hum.set_title("Humidity (%)", color=self.C_TEXT, fontsize=9)
            step = max(1, len(times) // 6)
            self._ax_hum.set_xticks(range(0, len(times), step))
            self._ax_hum.set_xticklabels(times[::step], rotation=30, ha="right", fontsize=7)

        self._fig.tight_layout(pad=2.5)
        self._canvas.draw()
        self.after(15000, self._refresh_chart)

    # ── Alerts tab ────────────────────────────────────────────────────────────

    def _build_alerts_tab(self):
        ctrl = tk.Frame(self._tab_alerts, bg=self.C_BG)
        ctrl.pack(fill=tk.X, padx=8, pady=6)
        tk.Button(ctrl, text="Refresh", font=("Consolas", 9, "bold"),
                  bg=self.C_ACCENT, fg=self.C_BG, bd=0, padx=10, pady=4,
                  cursor="hand2", command=self._refresh_alerts).pack(side=tk.LEFT, padx=4)
        if self._user["role"] == ROLE_ADMIN:
            tk.Button(ctrl, text="Acknowledge Selected", font=("Consolas", 9, "bold"),
                      bg=self.C_GREEN, fg=self.C_BG, bd=0, padx=10, pady=4,
                      cursor="hand2", command=self._acknowledge_alert).pack(side=tk.LEFT, padx=4)

        cols = ("Time", "Device", "Type", "Value", "Severity", "Classification", "Resolved")
        self._alert_tree = ttk.Treeview(self._tab_alerts, columns=cols, show="headings", height=20)
        for col in cols:
            self._alert_tree.heading(col, text=col)
            self._alert_tree.column(col, width=130, anchor="center")
        self._alert_tree.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))
        sb = ttk.Scrollbar(self._tab_alerts, orient=tk.VERTICAL, command=self._alert_tree.yview)
        self._alert_tree.configure(yscrollcommand=sb.set)
        self._refresh_alerts()

    def _refresh_alerts(self):
        for row in self._alert_tree.get_children():
            self._alert_tree.delete(row)
        for a in db.get_alerts(limit=100):
            resolved = "Yes" if a.get("resolved") else "No"
            self._alert_tree.insert("", tk.END, iid=str(a["_id"]), values=(
                a["timestamp"].strftime("%H:%M:%S"),
                a.get("device", ""),
                a.get("alert_type", ""),
                a.get("value", ""),
                a.get("severity", ""),
                a.get("classification", ""),
                resolved,
            ))

    def _acknowledge_alert(self):
        sel = self._alert_tree.selection()
        if not sel:
            messagebox.showinfo("Acknowledge", "Select an alert first.")
            return
        db.resolve_alert(sel[0])
        self._refresh_alerts()
        self._log_line(f"[{_ts()}] Admin acknowledged alert {sel[0][:8]}…", "info")

    # ── Commands tab ──────────────────────────────────────────────────────────

    def _build_commands_tab(self):
        ctrl = tk.Frame(self._tab_cmds, bg=self.C_BG)
        ctrl.pack(fill=tk.X, padx=8, pady=6)

        tk.Label(ctrl, text="Device:", font=("Consolas", 9),
                 bg=self.C_BG, fg=self.C_TEXT).pack(side=tk.LEFT, padx=(4, 2))
        self._cmd_device_var = tk.StringVar(value="Device1")
        ttk.Combobox(ctrl, textvariable=self._cmd_device_var,
                     values=["Device1", "Device2"], width=10, state="readonly").pack(side=tk.LEFT, padx=4)

        tk.Label(ctrl, text="Action:", font=("Consolas", 9),
                 bg=self.C_BG, fg=self.C_TEXT).pack(side=tk.LEFT, padx=(8, 2))
        self._cmd_action_var = tk.StringVar(value="STATUS")
        actions = ["STATUS", "ACTIVATE_COOLING", "DEACTIVATE_COOLING",
                   "EMERGENCY_COOLING", "RUN_DIAGNOSTICS"]
        ttk.Combobox(ctrl, textvariable=self._cmd_action_var,
                     values=actions, width=22, state="readonly").pack(side=tk.LEFT, padx=4)

        tk.Button(ctrl, text="Send Command", font=("Consolas", 9, "bold"),
                  bg=self.C_ACCENT, fg=self.C_BG, bd=0, padx=10, pady=4,
                  cursor="hand2", command=self._send_manual_command).pack(side=tk.LEFT, padx=8)
        tk.Button(ctrl, text="Refresh", font=("Consolas", 9, "bold"),
                  bg=self.C_PANEL, fg=self.C_TEXT, bd=0, padx=10, pady=4,
                  cursor="hand2", command=self._refresh_commands).pack(side=tk.LEFT)

        cols = ("Time", "Device", "Action", "Sent By", "Status", "Acknowledged At")
        self._cmd_tree = ttk.Treeview(self._tab_cmds, columns=cols, show="headings", height=20)
        for col in cols:
            self._cmd_tree.heading(col, text=col)
            self._cmd_tree.column(col, width=150, anchor="center")
        self._cmd_tree.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))
        self._refresh_commands()

    def _refresh_commands(self):
        for row in self._cmd_tree.get_children():
            self._cmd_tree.delete(row)
        for c in db.get_commands(limit=60):
            ack_at = c.get("ack_at")
            ack_str = ack_at.strftime("%H:%M:%S") if ack_at else "---"
            self._cmd_tree.insert("", tk.END, values=(
                c["timestamp"].strftime("%H:%M:%S"),
                c.get("device", ""),
                c.get("action", ""),
                c.get("sent_by", ""),
                c.get("status", ""),
                ack_str,
            ))

    def _send_manual_command(self):
        device = self._cmd_device_var.get()
        action = self._cmd_action_var.get()
        if action == "EMERGENCY_COOLING" and self._user["role"] != ROLE_ADMIN:
            messagebox.showerror("Access Denied", "Only admins can send Emergency Cooling.")
            return
        topic = TOPIC_CMD_D1 if device == "Device1" else TOPIC_CMD_D2
        self._publish_command(topic, device, action)

    # ── Devices tab ───────────────────────────────────────────────────────────

    def _build_devices_tab(self):
        ctrl = tk.Frame(self._tab_devices, bg=self.C_BG)
        ctrl.pack(fill=tk.X, padx=8, pady=6)
        tk.Button(ctrl, text="Refresh", font=("Consolas", 9, "bold"),
                  bg=self.C_ACCENT, fg=self.C_BG, bd=0, padx=10, pady=4,
                  cursor="hand2", command=self._refresh_devices_tab).pack(side=tk.LEFT, padx=(0, 12))

        if self._user["role"] == ROLE_ADMIN:
            bstyle = dict(font=("Consolas", 9, "bold"), bd=0, padx=10, pady=4, cursor="hand2")
            for label, device, action, color in [
                ("Activate Device 1",   "Device1", "ACTIVATE",   self.C_GREEN),
                ("Deactivate Device 1", "Device1", "DEACTIVATE", self.C_YELLOW),
                ("Activate Device 2",   "Device2", "ACTIVATE",   self.C_GREEN),
                ("Deactivate Device 2", "Device2", "DEACTIVATE", self.C_YELLOW),
            ]:
                tk.Button(ctrl, text=label, bg=color, fg=self.C_BG,
                          command=lambda d=device, a=action: self._device_control(d, a),
                          **bstyle).pack(side=tk.LEFT, padx=3)

        cols = ("Device ID", "Name", "Status", "Last Heartbeat")
        self._dev_tree = ttk.Treeview(self._tab_devices, columns=cols, show="headings", height=10)
        for col in cols:
            self._dev_tree.heading(col, text=col)
            self._dev_tree.column(col, width=200, anchor="center")
        self._dev_tree.pack(fill=tk.X, padx=8)
        self._refresh_devices_tab()

    def _refresh_devices_tab(self):
        for row in self._dev_tree.get_children():
            self._dev_tree.delete(row)
        for d in db.get_all_devices():
            hb = d.get("last_heartbeat")
            hb_str = hb.strftime("%H:%M:%S") if hb else "Never"
            self._dev_tree.insert("", tk.END, values=(
                d.get("device_id", ""),
                d.get("name", ""),
                d.get("status", ""),
                hb_str,
            ))
        self.after(10000, self._refresh_devices_tab)

    def _device_control(self, device, action):
        topic = TOPIC_CMD_D1 if device == "Device1" else TOPIC_CMD_D2
        self._publish_command(topic, device, action)
        db_status = "active" if action == "ACTIVATE" else "inactive"
        db.upsert_device(device.lower(), f"{'Sensor' if device == 'Device1' else 'Maintenance'} Node ({device})", db_status)
        color = self.C_GREEN if action == "ACTIVATE" else self.C_YELLOW
        tag   = "info" if action == "ACTIVATE" else "alert"
        self._log_line(f"[{_ts()}] ADMIN → {device}: {action}", tag)
        self._refresh_devices_tab()

    # ── Audit Log tab ─────────────────────────────────────────────────────────

    def _build_audit_tab(self):
        tk.Button(self._tab_audit, text="Refresh Audit Log", font=("Consolas", 9, "bold"),
                  bg=self.C_ACCENT, fg=self.C_BG, bd=0, padx=10, pady=4,
                  cursor="hand2", command=self._refresh_audit).pack(anchor="w", padx=8, pady=6)

        cols = ("Time", "Device", "Sensor", "Value", "Unit", "Anomaly", "Score", "Classification", "Risk")
        self._audit_tree = ttk.Treeview(self._tab_audit, columns=cols, show="headings", height=22)
        for col in cols:
            self._audit_tree.heading(col, text=col)
            self._audit_tree.column(col, width=110, anchor="center")
        self._audit_tree.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))
        sb = ttk.Scrollbar(self._tab_audit, orient=tk.VERTICAL, command=self._audit_tree.yview)
        self._audit_tree.configure(yscrollcommand=sb.set)
        self._refresh_audit()

    def _refresh_audit(self):
        for row in self._audit_tree.get_children():
            self._audit_tree.delete(row)
        for r in db.get_recent_readings(limit=100):
            self._audit_tree.insert("", tk.END, values=(
                r["timestamp"].strftime("%H:%M:%S"),
                r.get("device", ""),
                r.get("sensor", ""),
                r.get("value", ""),
                r.get("unit", ""),
                "YES" if r.get("is_anomaly") else "no",
                r.get("anomaly_score", ""),
                r.get("classification", ""),
                r.get("risk_score", ""),
            ))

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _panel(self, parent, title):
        return tk.LabelFrame(parent, text=title,
                             font=("Consolas", 9, "bold"),
                             bg=self.C_PANEL, fg=self.C_ACCENT, bd=2, relief=tk.GROOVE)

    def _row(self, parent, row, label, var, attr, color):
        tk.Label(parent, text=label, font=("Consolas", 9),
                 bg=self.C_PANEL, fg=self.C_TEXT).grid(row=row, column=0, sticky="w", padx=10, pady=4)
        lbl = tk.Label(parent, textvariable=var, font=("Consolas", 11, "bold"),
                       bg=self.C_PANEL, fg=color)
        lbl.grid(row=row, column=1, sticky="w", padx=8)
        setattr(self, f"_{attr}", lbl)

    def _log_line(self, text, tag="info"):
        self._log.configure(state=tk.NORMAL)
        self._log.insert(tk.END, text + "\n", tag)
        self._log.see(tk.END)
        self._log.configure(state=tk.DISABLED)

    def _refresh_status(self):
        self._status_var.set(
            f"Broker: {BROKER}:{PORT}   User: {self._user['username']} [{self._user['role']}]"
            f"   Messages: {self._msg_count}   Anomalies: {self._anomaly_count}"
            f"   DB: {MONGO_DB}"
        )

    # ── MQTT ─────────────────────────────────────────────────────────────────

    def _connect_mqtt(self):
        self._mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self._mqtt_client.username_pw_set(USERNAME, PASSWORD)
        self._mqtt_client.on_connect = self._on_connect
        self._mqtt_client.on_message = self._on_message
        try:
            self._mqtt_client.connect(BROKER, PORT, keepalive=60)
            self._mqtt_client.loop_start()
        except Exception as exc:
            self._msg_queue.put(("error", str(exc)))

    def _on_connect(self, client, userdata, flags, reason_code, _properties):
        if reason_code == 0:
            client.subscribe(TOPIC_PRIVATE_ALL)
            client.subscribe(TOPIC_PUBLIC_ALL)
            self._msg_queue.put(("connected", None))
            db.upsert_device("monitor", "UI Monitor", "online")
        else:
            self._msg_queue.put(("error", f"MQTT connect failed ({reason_code})"))

    def _on_message(self, client, userdata, msg):
        self._msg_queue.put(("message", msg))

    # ── Queue polling ─────────────────────────────────────────────────────────

    def _poll_queue(self):
        try:
            while True:
                kind, data = self._msg_queue.get_nowait()
                if kind == "connected":
                    self._log_line(f"[{_ts()}] Connected to broker at {BROKER}:{PORT}", "info")
                    self._refresh_status()
                elif kind == "error":
                    self._log_line(f"[{_ts()}] ERROR: {data}", "anomaly")
                elif kind == "message":
                    self._process_message(data)
        except queue.Empty:
            pass
        self.after(150, self._poll_queue)

    # ── Message processing ────────────────────────────────────────────────────

    def _process_message(self, msg):
        topic   = msg.topic
        payload = msg.payload.decode()
        self._msg_count += 1

        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            data = {}

        ts = _ts()

        # Heartbeats
        if topic == TOPIC_D1_HEARTBEAT:
            self._d1_last_hb = datetime.now()
            db.update_heartbeat("device1")
            self._d1_var.set("Online")
            self._d1_lbl.configure(fg=self.C_GREEN)
            return

        if topic == TOPIC_D2_HEARTBEAT:
            self._d2_last_hb = datetime.now()
            db.update_heartbeat("device2")
            self._d2_var.set("Online")
            self._d2_lbl.configure(fg=self.C_GREEN)
            return

        # Command acknowledgments
        if topic == TOPIC_D1_ACK or topic == TOPIC_D2_ACK:
            device = data.get("device", "")
            action = data.get("action", "")
            db.acknowledge_command(device, action)
            self._log_line(f"[{ts}] ACK from {device}: {action} → ACKNOWLEDGED", "cmd")
            self._refresh_commands()
            return

        # Private sensor telemetry (Device 1 telemetry bundle)
        if topic == TOPIC_D1_TELEMETRY:
            temp = data.get("temperature")
            hum  = data.get("humidity")
            vib  = data.get("vibration")
            if temp is not None:
                self._temp_var.set(f"{temp} °C")
                self._temp_lbl.configure(fg=self.C_RED if temp > TEMP_ALERT_THRESHOLD else self.C_GREEN)
                self._last_temp = temp
            if hum is not None:
                self._hum_var.set(f"{hum} %")
                self._last_hum = hum
            if vib is not None:
                self._vib_var.set(f"{vib} mm/s")
            return

        # Individual sensor topics (for AI processing)
        sensor = data.get("sensor", "")
        value  = data.get("value")
        unit   = data.get("unit", "")
        device = data.get("device", "")

        if sensor == "temperature" and value is not None:
            temp = float(value)
            self._last_temp = temp
            self._temp_var.set(f"{temp} °C")
            self._temp_lbl.configure(fg=self.C_RED if temp > TEMP_ALERT_THRESHOLD else self.C_GREEN)
            self._d1_var.set("Online")
            self._d1_lbl.configure(fg=self.C_GREEN)
            self._d1_last_hb = datetime.now()

            if temp <= TEMP_ALERT_THRESHOLD:
                self._consecutive_alerts = 0

            is_anomaly, score, classification, risk_score, predicted = (False, 0.0, "NORMAL", 0.0, None)
            if self._last_hum is not None:
                is_anomaly, score, classification, risk_score, predicted = \
                    self._ai.process(temp, self._last_hum)

            self._update_ai_display(is_anomaly, score, classification, risk_score, predicted)
            db.insert_reading(device, "temperature", temp, "C",
                              is_anomaly, score, classification, risk_score)

            if is_anomaly and classification != "NORMAL":
                self._anomaly_count += 1
                db.insert_alert(device, "ANOMALY", temp, classification, classification)
                self._log_line(
                    f"[{ts}] AI ANOMALY  temp={temp}°C  class={classification}"
                    f"  risk={risk_score}/10  score={score}", "anomaly")
                self._refresh_alerts()

            tag = "anomaly" if is_anomaly else "normal"
            self._log_line(
                f"[{ts}] TEMP={temp}°C  risk={risk_score}/10"
                f"  class={classification}", tag)

            if temp > TEMP_ALERT_THRESHOLD and not self._cooling_active:
                self._auto_activate_cooling()

            self._samples_var.set(
                f"{self._ai.sample_count} / {AI_MIN_SAMPLES}"
                f"  {'(fitted)' if self._ai.is_fitted else '(training)'}"
            )

        elif sensor == "humidity" and value is not None:
            self._last_hum = float(value)
            self._hum_var.set(f"{value} %")
            db.insert_reading(device, "humidity", float(value), "%",
                              False, 0.0, "NORMAL", 0.0)

        elif sensor == "vibration" and value is not None:
            self._vib_var.set(f"{value} mm/s")
            db.insert_reading(device, "vibration", float(value), "mm/s",
                              False, 0.0, "NORMAL", 0.0)

        # Public Topic 1 — temperature alert
        elif data.get("alert") == "HIGH_TEMPERATURE":
            self._consecutive_alerts += 1
            val = data.get("value", "")
            self._log_line(
                f"[{ts}] ALERT: HIGH_TEMPERATURE {val}°C"
                f"  (consecutive={self._consecutive_alerts})", "alert")
            db.insert_alert(device or "Device1", "HIGH_TEMPERATURE", val,
                            "CRITICAL" if self._consecutive_alerts >= AUTO_EMERGENCY_COUNT else "HIGH",
                            "OVERHEATING")
            self._refresh_alerts()
            if self._consecutive_alerts >= AUTO_EMERGENCY_COUNT:
                self._auto_emergency_cooling()

        # Public Topic 2 — maintenance response
        elif data.get("status") and "Device2" in data.get("device", ""):
            self._d2_var.set("Online")
            self._d2_lbl.configure(fg=self.C_GREEN)
            self._d2_last_hb = datetime.now()
            status   = data.get("status", "")
            priority = data.get("priority", "")
            machine  = data.get("machine_id", "")
            tag = "alert" if priority in ("HIGH", "CRITICAL") else "normal"
            self._log_line(
                f"[{ts}] DEVICE2  status={status}"
                f"  priority={priority}  machine={machine}", tag)

            if status in ("COOLING_ACTIVATED", "IMMEDIATE_COOLING_REQUIRED",
                          "EMERGENCY_COOLING_REQUIRED"):
                self._set_cooling(True)

        self._refresh_status()

    # ── AI display ────────────────────────────────────────────────────────────

    def _update_ai_display(self, is_anomaly, score, classification, risk_score, predicted):
        if not self._ai.is_fitted:
            self._ai_var.set("Collecting data…")
            self._ai_lbl.configure(fg=self.C_YELLOW)
        elif is_anomaly:
            self._ai_var.set(f"ANOMALY  (score={score})")
            self._ai_lbl.configure(fg=self.C_RED)
        else:
            self._ai_var.set(f"Normal  (score={score})")
            self._ai_lbl.configure(fg=self.C_GREEN)

        self._class_var.set(classification)
        color_map = {
            "NORMAL": self.C_GREEN, "OVERHEATING": self.C_YELLOW,
            "INJECTION_ATTACK": self.C_RED, "SENSOR_FAULT": self.C_PURPLE,
            "HUMIDITY_SPIKE": self.C_CYAN,
        }
        self._class_lbl.configure(fg=color_map.get(classification, self.C_TEXT))

        self._risk_var.set(f"Risk: {risk_score}/10")
        risk_color = self.C_GREEN if risk_score < 4 else (self.C_YELLOW if risk_score < 7 else self.C_RED)
        self._risk_lbl.configure(fg=risk_color)

        if predicted is not None:
            warn = " ⚠ COOLING RECOMMENDED" if predicted > TEMP_ALERT_THRESHOLD else ""
            self._predict_var.set(f"Predicted: {predicted}°C{warn}")
            self._predict_lbl.configure(
                fg=self.C_YELLOW if predicted > TEMP_ALERT_THRESHOLD else self.C_CYAN)
        else:
            self._predict_var.set("Predicted: collecting…")

    # ── Heartbeat checker ─────────────────────────────────────────────────────

    def _check_heartbeats(self):
        cutoff = datetime.now() - timedelta(seconds=OFFLINE_TIMEOUT)
        if self._d1_last_hb and self._d1_last_hb < cutoff:
            self._d1_var.set("OFFLINE")
            self._d1_lbl.configure(fg=self.C_RED)
            db.set_device_offline("device1")
        if self._d2_last_hb and self._d2_last_hb < cutoff:
            self._d2_var.set("OFFLINE")
            self._d2_lbl.configure(fg=self.C_RED)
            db.set_device_offline("device2")
        self.after(10000, self._check_heartbeats)

    # ── Cooling helpers ───────────────────────────────────────────────────────

    def _set_cooling(self, active, label=None):
        self._cooling_active = active
        text = label if label else ("ON" if active else "OFF")
        self._cooling_var.set(text)
        self._cooling_lbl.configure(fg=self.C_RED if active else self.C_GREEN)

    # ── Auto-commands ─────────────────────────────────────────────────────────

    def _auto_activate_cooling(self):
        self._publish_command(TOPIC_CMD_D1, "Device1", "ACTIVATE_COOLING")
        self._set_cooling(True)
        self._log_line(f"[{_ts()}] AUTO-CMD → Device 1: ACTIVATE_COOLING", "cmd")

    def _auto_emergency_cooling(self):
        self._publish_command(TOPIC_CMD_D1, "Device1", "EMERGENCY_COOLING")
        self._set_cooling(True, "EMERGENCY")
        self._log_line(
            f"[{_ts()}] AUTO-CMD → Device 1: EMERGENCY_COOLING"
            f"  (after {self._consecutive_alerts} consecutive alerts)", "anomaly")

    # ── Button commands ───────────────────────────────────────────────────────

    def _cmd_activate(self):
        self._publish_command(TOPIC_CMD_D1, "Device1", "ACTIVATE_COOLING")
        self._set_cooling(True)
        self._log_line(f"[{_ts()}] MANUAL CMD → Device 1: ACTIVATE_COOLING", "cmd")

    def _cmd_deactivate(self):
        self._publish_command(TOPIC_CMD_D1, "Device1", "DEACTIVATE_COOLING")
        self._set_cooling(False)
        self._consecutive_alerts = 0
        self._log_line(f"[{_ts()}] MANUAL CMD → Device 1: DEACTIVATE_COOLING", "cmd")

    def _cmd_emergency(self):
        self._publish_command(TOPIC_CMD_D1, "Device1", "EMERGENCY_COOLING")
        self._set_cooling(True, "EMERGENCY")
        self._log_line(f"[{_ts()}] MANUAL CMD → Device 1: EMERGENCY_COOLING", "anomaly")

    def _cmd_diagnostics(self):
        self._publish_command(TOPIC_CMD_D2, "Device2", "RUN_DIAGNOSTICS")
        self._log_line(f"[{_ts()}] MANUAL CMD → Device 2: RUN_DIAGNOSTICS", "cmd")

    def _cmd_status(self):
        self._publish_command(TOPIC_CMD_D1, "Device1", "STATUS")
        self._publish_command(TOPIC_CMD_D2, "Device2", "STATUS")
        self._log_line(f"[{_ts()}] MANUAL CMD → Device 1 + 2: STATUS", "cmd")

    def _cmd_simulate(self):
        if not self._mqtt_client:
            return
        fake_temp, fake_hum = 95.0, 3.0
        payload = json.dumps({
            "device": "ATTACKER", "sensor": "temperature",
            "value": fake_temp, "unit": "C",
            "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        })
        self._mqtt_client.publish(f"{STUDENT_ID}/sensors/temperature", payload)
        self._log_line(
            f"[{_ts()}] ATTACK SIMULATED — injected fake reading:"
            f" temp={fake_temp}°C  hum={fake_hum}%", "anomaly")

    def _publish_command(self, topic, device, action):
        if self._mqtt_client:
            payload = json.dumps({
                "action":    action,
                "sent_by":   self._user["username"],
                "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            })
            self._mqtt_client.publish(topic, payload)
            db.insert_command(device, action, self._user["username"])
            self._refresh_commands()

    # ── Shutdown ──────────────────────────────────────────────────────────────

    def _logout(self):
        if self._mqtt_client:
            self._mqtt_client.loop_stop()
            self._mqtt_client.disconnect()
        self.destroy()
        # Show login window again
        login_win = LoginWindow()
        login_win.mainloop()
        if login_win.current_user:
            app = SmartFactoryApp(login_win.current_user)
            app.protocol("WM_DELETE_WINDOW", app.on_closing)
            app.mainloop()

    def on_closing(self):
        if self._mqtt_client:
            self._mqtt_client.loop_stop()
            self._mqtt_client.disconnect()
        self.destroy()


# ─── HELPERS ──────────────────────────────────────────────────────────────────

def _ts():
    return datetime.now().strftime("%H:%M:%S")


# ─── ENTRY POINT ──────────────────────────────────────────────────────────────

def main():
    # Seed default users in MongoDB
    try:
        auth.seed_default_users()
    except Exception as e:
        print(f"[DB] Warning: {e}")

    # Register devices in MongoDB
    try:
        db.upsert_device("device1", "Sensor Node (Device 1)", "offline")
        db.upsert_device("device2", "Maintenance Node (Device 2)", "offline")
    except Exception as e:
        print(f"[DB] Warning: {e}")

    # Login window
    login_win = LoginWindow()
    login_win.mainloop()

    if not login_win.current_user:
        print("Login cancelled.")
        return

    # Main dashboard
    app = SmartFactoryApp(login_win.current_user)
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()


if __name__ == "__main__":
    main()
