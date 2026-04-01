import customtkinter as ctk
import threading
import time
import winsound
import csv
import os
from datetime import datetime
from timer_logic import PomodoroTimer

# Configure CustomTkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class PomodoroApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Pomodoro-Portable")
        self.geometry("400x550")
        self.resizable(False, False)

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
        self.separator.pack(fill="x", padx=20, pady=15)
        
        self.task_frame = ctk.CTkFrame(self)
        self.task_frame.pack(pady=5, padx=20, fill="x")

        self.task_status_label = ctk.CTkLabel(self.task_frame, text="Sin tarea activa", font=ctk.CTkFont(weight="bold"))
        self.task_status_label.pack(pady=(10, 5))

        self.task_entry = ctk.CTkEntry(self.task_frame, placeholder_text="Nombre de la tarea", width=250)
        self.task_entry.pack(pady=5)

        self.task_buttons_frame = ctk.CTkFrame(self.task_frame, fg_color="transparent")
        self.task_buttons_frame.pack(pady=(5, 10))

        self.action_task_btn = ctk.CTkButton(self.task_buttons_frame, text="Iniciar Tarea", command=self.toggle_task, width=100)
        self.action_task_btn.pack(side="left", padx=5)

        self.edit_task_btn = ctk.CTkButton(self.task_buttons_frame, text="Editar", command=self.edit_task, width=60, state="disabled")
        self.edit_task_btn.pack(side="left", padx=5)

        self.finish_task_btn = ctk.CTkButton(self.task_buttons_frame, text="Finalizar", command=self.finish_task, width=80, state="disabled")
        self.finish_task_btn.pack(side="left", padx=5)


    def on_time_change(self, value):
        self.timer.set_work_duration(int(value))

    def update_ui(self, remaining_time, state):
        # Tracker logic
        if self.active_task_name is not None and self.timer.is_running and not self.timer.is_paused:
            if state == "Work":
                self.task_work_secs += 1
            else:
                self.task_break_secs += 1

        mins, secs = divmod(remaining_time, 60)
        timeformat = '{:02d}:{:02d}'.format(mins, secs)
        
        if remaining_time == 0:
            # Alarma: secuencia de 3 pitidos de 500ms (aprox 2 segundos total) a 800Hz
            def _play_alarm():
                for _ in range(3):
                    winsound.Beep(800, 500)
                    time.sleep(0.1)
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
        messagebox.showinfo("Reporte de Tarea", report_msg)

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

    # --- Timer Thread Controls ---
    def run_timer(self):
        while True:
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
