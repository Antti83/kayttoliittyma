import tkinter as tk
from tkinter import ttk, messagebox
import random, math, datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class MotorSimulator:
    def __init__(self):
        self.running = False
        self.time = 0
        self.data = {"temperature": [], "vibration": [], "rpm": [], "oil": [], "voltage": [], "time": []}

    def start(self):
        self.running = True
        self.time = 0
        self.data = {k: [] for k in self.data}

    def stop(self):
        self.running = False

    def generate_data(self):
        self.time += 1
        t = 70 + 15 * math.sin(self.time / 15) + random.uniform(-1, 1)
        vib = 2.0 + 1.5 * math.sin(self.time / 10) + random.uniform(-0.5, 0.5)
        rpm = 1500 + 350 * math.sin(self.time / 5) + random.uniform(-50, 50)
        oil = 3.5 + 0.8 * math.sin(self.time / 20) + random.uniform(-0.2, 0.2)
        volt = 400 + 15 * math.sin(self.time / 30) + random.uniform(-3, 3)

        self.data["time"].append(self.time)
        self.data["temperature"].append(t)
        self.data["vibration"].append(vib)
        self.data["rpm"].append(rpm)
        self.data["oil"].append(oil)
        self.data["voltage"].append(volt)
        return t, vib, rpm, oil, volt


class MotorMonitorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Moottorin kunnon seuranta - Live")
        self.geometry("1050x720")
        self.configure(bg="#1e1e1e")

        self.sim = MotorSimulator()
        self.active_alarms = set()
        self.log_file = "motor_log.txt"
        self.showing_log = False 

        title = tk.Label(self, text="Moottorin kunnon seuranta", font=("Segoe UI", 20, "bold"), bg="#1e1e1e", fg="white")
        title.pack(pady=10)

        btn_frame = tk.Frame(self, bg="#1e1e1e")
        btn_frame.pack()
        self.start_btn = ttk.Button(btn_frame, text="Käynnistä ohjelma", command=self.start_motor)
        self.stop_btn = ttk.Button(btn_frame, text="Pysäytä ohjelma", command=self.stop_motor)
        self.reset_btn = ttk.Button(btn_frame, text="Kuittaa hälytykset", command=self.reset_alarms)
        self.log_btn = ttk.Button(btn_frame, text="Näytä loki", command=self.toggle_log_view)
        self.clear_log_btn = ttk.Button(btn_frame, text="Tyhjennä loki", command=self.clear_log)

        self.start_btn.grid(row=0, column=0, padx=8, pady=5)
        self.stop_btn.grid(row=0, column=1, padx=8, pady=5)
        self.reset_btn.grid(row=0, column=2, padx=8, pady=5)
        self.log_btn.grid(row=0, column=3, padx=8, pady=5)
        self.clear_log_btn.grid(row=0, column=4, padx=8, pady=5)

        meters = tk.Frame(self, bg="#1e1e1e")
        meters.pack(pady=10)
        self.value_labels = {}
        self.status_lights = {}

        sensors = [
            ("Lämpötila", "°C"),
            ("Tärinä", "mm/s RMS"),
            ("Kierrosnopeus", "RPM"),
            ("Öljynpaine", "bar"),
            ("Jännite", "V")
        ]

        for i, (name, unit) in enumerate(sensors):
            frame = tk.Frame(meters, bg="#2e2e2e", bd=1, relief="groove", padx=10, pady=5)
            frame.grid(row=0, column=i, padx=5)

            light = tk.Label(frame, text="●", font=("Segoe UI", 18, "bold"), fg="gray", bg="#2e2e2e")
            light.pack()
            self.status_lights[name] = light

            tk.Label(frame, text=name, bg="#2e2e2e", fg="white", font=("Segoe UI", 10)).pack()
            lbl = tk.Label(frame, text="--", bg="#2e2e2e", fg="lime", font=("Consolas", 14, "bold"))
            lbl.pack()
            tk.Label(frame, text=unit, bg="#2e2e2e", fg="gray").pack()
            self.value_labels[name] = lbl

        
        self.display_frame = tk.Frame(self, bg="#1e1e1e")
        self.display_frame.pack(fill="both", expand=True)

        self.graph_controls = tk.Frame(self.display_frame, bg="#1e1e1e")
        self.graph_controls.pack(pady=5)

        tk.Label(self.graph_controls, text="Näytettävä mittari:", bg="#1e1e1e", fg="white").pack(side="left", padx=5)

        self.metric_buttons = {}
        self.selected_metric = tk.StringVar(value="Tärinä")

        for metric in ["Lämpötila", "Tärinä", "Kierrosnopeus", "Öljynpaine", "Jännite"]:
            btn = tk.Button(
                self.graph_controls,
                text=metric,
                command=lambda m=metric: self.set_metric(m),
                bg="#2e2e2e",
                fg="white",
                relief="ridge",
                padx=8,
                pady=3
            )
            btn.pack(side="left", padx=4)
            self.metric_buttons[metric] = btn

        fig, ax = plt.subplots(figsize=(7, 3), facecolor="#1e1e1e")
        self.ax = ax
        self.fig = fig
        self.canvas = FigureCanvasTkAgg(fig, master=self.display_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        ax.set_facecolor("#1e1e1e")
        ax.tick_params(colors="white")
        ax.spines[:].set_color("white")

        self.log_text = tk.Text(self.display_frame, bg="#2e2e2e", fg="white", wrap="word")
        self.log_text.config(state="disabled")

        self.set_metric("Tärinä")
        self.after(1000, self.update_loop)

    def set_metric(self, metric):
        self.selected_metric.set(metric)
        for name, btn in self.metric_buttons.items():
            if name == metric:
                btn.config(bg="#008000", fg="white")
            else:
                btn.config(bg="#2e2e2e", fg="white")

    def start_motor(self):
        if not self.sim.running:
            self.sim.start()

    def stop_motor(self):
        if self.sim.running:
            self.sim.stop()

    def reset_alarms(self):
        self.active_alarms.clear()
        for light in self.status_lights.values():
            light.config(fg="gray")

    def log_alarm(self, name, value):
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"[{now}] HÄLYTYS: {name} = {value:.2f}\n")

    def toggle_log_view(self):
        if self.showing_log:
            self.log_text.pack_forget()
            self.graph_controls.pack(pady=5)
            self.canvas.get_tk_widget().pack(fill="both", expand=True)
            self.log_btn.config(text="Näytä loki")
            self.showing_log = False
        else:
            try:
                with open(self.log_file, "r", encoding="utf-8") as f:
                    content = f.read()
            except FileNotFoundError:
                content = "Ei lokitietoja saatavilla."

            self.canvas.get_tk_widget().pack_forget()
            self.graph_controls.pack_forget()
            self.log_text.config(state="normal")
            self.log_text.delete("1.0", "end")
            self.log_text.insert("1.0", content)
            self.log_text.config(state="disabled")
            self.log_text.pack(fill="both", expand=True)
            self.log_btn.config(text="Näytä graafi")
            self.showing_log = True

    def clear_log(self):
        if messagebox.askyesno("Vahvista", "Tyhjennetäänkö lokitiedosto?"):
            open(self.log_file, "w", encoding="utf-8").close()
            if self.showing_log:
                self.log_text.config(state="normal")
                self.log_text.delete("1.0", "end")
                self.log_text.config(state="disabled")

    def update_loop(self):
        if self.sim.running:
            t, vib, rpm, oil, volt = self.sim.generate_data()
            values = {"Lämpötila": t, "Tärinä": vib, "Kierrosnopeus": rpm, "Öljynpaine": oil, "Jännite": volt}
            limits = {"Lämpötila": (None, 90), "Tärinä": (None, 3), "Kierrosnopeus": (None, 3000), "Öljynpaine": (1.5, None), "Jännite": (None, 420)}

            for name, val in values.items():
                self.value_labels[name].config(text=f"{val:.1f}")
                low, high = limits[name]
                alarm = (high is not None and val > high) or (low is not None and val < low)
                if alarm:
                    if name not in self.active_alarms:
                        self.active_alarms.add(name)
                        self.log_alarm(name, val)
                    self.status_lights[name].config(fg="red")
                elif name in self.active_alarms:
                    self.status_lights[name].config(fg="red")
                else:
                    self.status_lights[name].config(fg="lime")

            if not self.showing_log:
                metric = self.selected_metric.get()
                key_map = {"Lämpötila": "temperature", "Tärinä": "vibration", "Kierrosnopeus": "rpm", "Öljynpaine": "oil", "Jännite": "voltage"}
                key = key_map[metric]
                ax = self.ax
                ax.clear()
                ax.plot(self.sim.data["time"][-100:], self.sim.data[key][-100:], color="cyan")
                ax.set_facecolor("#1e1e1e")
                ax.tick_params(colors="white")
                ax.spines[:].set_color("white")
                ax.set_xlabel("Aika (s)", color="white")
                ax.set_ylabel(metric, color="white")
                self.canvas.draw()

        self.after(1000, self.update_loop)


if __name__ == "__main__":
    app = MotorMonitorApp()
    app.mainloop()