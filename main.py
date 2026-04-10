import customtkinter as ctk
import threading
import time
import pygame
import csv
import os
import sys
from datetime import datetime
from timer_logic import PomodoroTimer

# Matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

# Configure CustomTkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class ReportWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Reportes de Trabajo")
        self.geometry("600x450")
        
        # Prevent opening multiple report windows by keeping focus
        self.grab_set()

        self.filter_var = ctk.StringVar(value="Diario")
        self.filter_seg_btn = ctk.CTkSegmentedButton(
            self, 
            values=["Diario", "Semanal", "Mensual"],
            variable=self.filter_var,
            command=self.update_chart
        )
        self.filter_seg_btn.pack(pady=20)
        
        self.chart_frame = ctk.CTkFrame(self)
        self.chart_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        self.figure, self.ax = plt.subplots(figsize=(6, 4))
        # Style chart for dark mode
        self.figure.patch.set_facecolor('#2b2b2b')
        self.ax.set_facecolor('#2b2b2b')
        self.ax.tick_params(colors='white')
        self.ax.yaxis.label.set_color('white')
        self.ax.xaxis.label.set_color('white')
        self.ax.spines['bottom'].set_color('white')
        self.ax.spines['top'].set_color('#2b2b2b')
        self.ax.spines['right'].set_color('#2b2b2b')
        self.ax.spines['left'].set_color('white')
        
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.chart_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        
        self.update_chart(self.filter_var.get())

        # Bind closing to release grab
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self):
        self.grab_release()
        self.destroy()
        
    def parse_data(self):
        data = []
        file_path = "historial_tareas.csv"
        if not os.path.exists(file_path):
            return data
            
        with open(file_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    dt = datetime.strptime(row["Fecha"], "%Y-%m-%d %H:%M:%S")
                    work_mins = int(row["Minutos Trabajo"])
                    data.append({"date": dt, "work_mins": work_mins})
                except Exception:
                    continue
        return data

    def update_chart(self, filter_type):
        data = self.parse_data()
        self.ax.clear()

        # Check if data exists
        if not data:
            self.ax.text(0.5, 0.5, 'No hay datos suficientes', color='white', ha='center')
            self.canvas.draw()
            return

        # Simple aggregation dict
        agg = {}
        for d in data:
            dt = d["date"]
            val = d["work_mins"]
            if filter_type == "Diario":
                key = dt.strftime("%Y-%m-%d")
            elif filter_type == "Semanal":
                key = dt.strftime("%Y-W%W")
            elif filter_type == "Mensual":
                key = dt.strftime("%Y-%m")
            
            agg[key] = agg.get(key, 0) + val

        keys = sorted(agg.keys())
        values = [agg[k] for k in keys]

        if filter_type == "Diario":
            keys = keys[-7:]
            values = values[-7:]
            x_labels = [datetime.strptime(k, "%Y-%m-%d").strftime("%d %b") for k in keys]
        elif filter_type == "Semanal":
            keys = keys[-4:]
            values = values[-4:]
            x_labels = keys
        elif filter_type == "Mensual":
            keys = keys[-12:]
            values = values[-12:]
            x_labels = [datetime.strptime(k, "%Y-%m").strftime("%b '%y") for k in keys]
            
        # Draw bars
        bars = self.ax.bar(x_labels, values, color='#1f538d') # ctk blue-ish
        
        # Add values on top of bars
        for bar in bars:
            height = bar.get_height()
            self.ax.annotate(f'{height}',
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3),  # 3 points vertical offset
                textcoords="offset points",
                ha='center', va='bottom', color='white')

        self.ax.set_ylabel("Minutos de Trabajo")
        self.ax.set_title(f"Tiempo de Enfoque ({filter_type})", color='white')
        self.figure.autofmt_xdate()
        
        self.canvas.draw()


class PomodoroApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Pomodoro-Portable")
        self.geometry("400x580")
        self.resizable(False, False)
        
        self.app_running = True
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Task tracking variables
        self.active_task_name = None
        self.task_work_secs = 0
        self.task_break_secs = 0

        # Initialize Timer
        self.timer = PomodoroTimer(self.update_ui)
        
        # Start background thread for timer to prevent UI freeze
        self.timer_thread = threading.Thread(target=self.run_timer, daemon=True)
        self.timer_thread.start()

        self.setup_ui()

    def setup_ui(self):
        # State display (Work, Break, etc)
        self.state_label = ctk.CTkLabel(self, text="Trabajo", font=ctk.CTkFont(size=24, weight="bold"))
        self.state_label.pack(pady=(20, 5))

        # Main Clock display
        self.clock_label = ctk.CTkLabel(self, text="25:00", font=ctk.CTkFont(size=80, weight="bold"))
        self.clock_label.pack(pady=5)

        # Work Duration Selector
        self.time_selector_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.time_selector_frame.pack(pady=5)
        
        ctk.CTkLabel(self.time_selector_frame, text="Tiempo (min):").pack(side="left", padx=5)
        self.time_var = ctk.StringVar(value="25")
        self.time_dropdown = ctk.CTkOptionMenu(
            self.time_selector_frame, 
            values=["25", "30", "45", "60"], 
            variable=self.time_var,
            command=self.on_time_change
        )
        self.time_dropdown.pack(side="left", padx=5)

        # Controls
        self.buttons_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.buttons_frame.pack(pady=10)

        self.start_btn = ctk.CTkButton(self.buttons_frame, text="Iniciar", command=self.start_timer, width=80)
        self.start_btn.pack(side="left", padx=10)

        self.pause_btn = ctk.CTkButton(self.buttons_frame, text="Pausar", command=self.pause_timer, width=80)
        self.pause_btn.pack(side="left", padx=10)

        self.reset_btn = ctk.CTkButton(self.buttons_frame, text="Reiniciar", command=self.reset_timer, width=80)
        self.reset_btn.pack(side="left", padx=10)

        # --- Task Tracking UI ---
        # Separator line
        self.separator = ctk.CTkFrame(self, height=2)
        self.separator.pack(fill="x", padx=20, pady=10)
        
        self.task_frame = ctk.CTkFrame(self)
        self.task_frame.pack(pady=5, padx=20, fill="x")

        self.task_status_label = ctk.CTkLabel(self.task_frame, text="Sin tarea activa", font=ctk.CTkFont(weight="bold"))
        self.task_status_label.pack(pady=(10, 5))

        self.task_entry = ctk.CTkEntry(self.task_frame, placeholder_text="Nombre de la tarea", width=250)
        self.task_entry.pack(pady=5)

        self.task_buttons_frame = ctk.CTkFrame(self.task_frame, fg_color="transparent")
        self.task_buttons_frame.pack(pady=(5, 5))

        self.action_task_btn = ctk.CTkButton(self.task_buttons_frame, text="Iniciar Tarea", command=self.toggle_task, width=90)
        self.action_task_btn.pack(side="left", padx=5)

        self.edit_task_btn = ctk.CTkButton(self.task_buttons_frame, text="Editar", command=self.edit_task, width=50, state="disabled")
        self.edit_task_btn.pack(side="left", padx=5)

        self.finish_task_btn = ctk.CTkButton(self.task_buttons_frame, text="Finalizar", command=self.finish_task, width=80, state="disabled")
        self.finish_task_btn.pack(side="left", padx=5)

        # Report Button
        self.report_btn = ctk.CTkButton(self.task_frame, text="Ver Reportes (Gráficos)", fg_color="#4158D0", command=self.show_reports)
        self.report_btn.pack(pady=(5, 15))


    def on_time_change(self, value):
        self.timer.set_work_duration(int(value))

    def update_ui(self, remaining_time, state):
        if not getattr(self, 'app_running', True):
            return
            
        # Tracker logic
        if self.active_task_name is not None and self.timer.is_running and not self.timer.is_paused:
            if state == "Work":
                self.task_work_secs += 1
            else:
                self.task_break_secs += 1

        mins, secs = divmod(remaining_time, 60)
        timeformat = '{:02d}:{:02d}'.format(mins, secs)
        
        if remaining_time == 0:
            # Reproducir sonido ring.mp3
            def _play_alarm():
                try:
                    if not pygame.mixer.get_init():
                        pygame.mixer.init()
                    pygame.mixer.music.load("ring.mp3")
                    pygame.mixer.music.play()
                except Exception as e:
                    print(f"Error reproduciendo audio: {e}")
            threading.Thread(target=_play_alarm, daemon=True).start()
            
        # Use after() to schedule UI update on the main thread
        self.after(0, self._apply_ui_update, timeformat, state)

    def _apply_ui_update(self, timeformat, state):
        self.clock_label.configure(text=timeformat)
        
        # Translate internal states to Spanish
        state_translations = {
            "Work": "Trabajo",
            "Short Break": "Descanso Corto",
            "Long Break": "Descanso Largo"
        }
        
        display_state = state_translations.get(state, state)
        self.state_label.configure(text=display_state)
        
        # Color code states
        if state == "Work":
            self.state_label.configure(text_color="white")
        elif state == "Short Break":
            self.state_label.configure(text_color="#ADD8E6") # Light Blue
        elif state == "Long Break":
            self.state_label.configure(text_color="#90EE90") # Light Green
            
        if timeformat == "00:00":
            self.pause_btn.configure(text="Pausar")
            import tkinter.messagebox as messagebox
            messagebox.showinfo("¡Tiempo completado!", f"El ciclo de {display_state} ha terminado.\nInicia manualmente para continuar.")

    # --- Task Logic Methods ---
    def toggle_task(self):
        task_name = self.task_entry.get().strip()
        if not task_name:
            import tkinter.messagebox as messagebox
            messagebox.showwarning("Atención", "Por favor ingresa un nombre para la tarea.")
            return

        self.active_task_name = task_name
        self.task_status_label.configure(text=f"Tarea Activa: {self.active_task_name}", text_color="#ADD8E6")
        self.task_entry.configure(state="disabled")
        
        self.action_task_btn.configure(state="disabled")
        self.edit_task_btn.configure(state="normal")
        self.finish_task_btn.configure(state="normal")

    def edit_task(self):
        self.task_entry.configure(state="normal")
        self.task_entry.focus()
        self.action_task_btn.configure(state="normal", text="Guardar")
        self.edit_task_btn.configure(state="disabled")

    def finish_task(self):
        if not self.active_task_name: return

        # Calculate time
        w_mins = self.task_work_secs // 60
        b_mins = self.task_break_secs // 60

        report_msg = (
            f"Tarea: {self.active_task_name}\n"
            f"Tiempo enfocado: {w_mins} min\n"
            f"Tiempo de descanso: {b_mins} min"
        )
        
        # Save to CSV
        file_path = "historial_tareas.csv"
        file_exists = os.path.isfile(file_path)
        with open(file_path, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["Fecha", "Tarea", "Minutos Trabajo", "Minutos Descanso"])
            writer.writerow([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                self.active_task_name,
                w_mins,
                b_mins
            ])

        # Show popup
        import tkinter.messagebox as messagebox
        messagebox.showinfo("Reporte de Tarea Finalizada", report_msg)

        # Automatic timer reset
        self.reset_timer()

        # Reset task state
        self.active_task_name = None
        self.task_work_secs = 0
        self.task_break_secs = 0
        
        self.task_status_label.configure(text="Sin tarea activa", text_color="white")
        self.task_entry.configure(state="normal")
        self.task_entry.delete(0, 'end')
        
        self.action_task_btn.configure(state="normal", text="Iniciar Tarea")
        self.edit_task_btn.configure(state="disabled")
        self.finish_task_btn.configure(state="disabled")

    def show_reports(self):
        ReportWindow(self)

    def on_closing(self):
        self.app_running = False
        self.quit()
        self.destroy()
        sys.exit(0)

    # --- Timer Thread Controls ---
    def run_timer(self):
        while getattr(self, 'app_running', True):
            self.timer.tick()
            time.sleep(1)

    def start_timer(self):
        self.timer.start()

    def pause_timer(self):
        self.timer.pause()
        if self.timer.is_paused:
            self.pause_btn.configure(text="Reanudar")
        else:
            self.pause_btn.configure(text="Pausar")

    def reset_timer(self):
        self.timer.reset()
        self.pause_btn.configure(text="Pausar")

if __name__ == "__main__":
    app = PomodoroApp()
    app.mainloop()
