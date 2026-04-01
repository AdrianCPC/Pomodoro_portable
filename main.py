import customtkinter as ctk
import threading
import time
import winsound
from timer_logic import PomodoroTimer

# Configure CustomTkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class PomodoroApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Pomodoro-Portable")
        self.geometry("400x350")
        self.resizable(False, False)

        # Initialize Timer
        self.timer = PomodoroTimer(self.update_ui)
        
        # Start background thread for timer to prevent UI freeze
        self.timer_thread = threading.Thread(target=self.run_timer, daemon=True)
        self.timer_thread.start()

        self.setup_ui()

    def setup_ui(self):
        # State display (Work, Break, etc)
        self.state_label = ctk.CTkLabel(self, text="Trabajo", font=ctk.CTkFont(size=24, weight="bold"))
        self.state_label.pack(pady=(30, 10))

        # Main Clock display
        self.clock_label = ctk.CTkLabel(self, text="25:00", font=ctk.CTkFont(size=80, weight="bold"))
        self.clock_label.pack(pady=10)

        # Work Duration Selector
        self.time_selector_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.time_selector_frame.pack(pady=10)
        
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
        self.buttons_frame.pack(pady=20)

        self.start_btn = ctk.CTkButton(self.buttons_frame, text="Iniciar", command=self.start_timer, width=80)
        self.start_btn.pack(side="left", padx=10)

        self.pause_btn = ctk.CTkButton(self.buttons_frame, text="Pausar", command=self.pause_timer, width=80)
        self.pause_btn.pack(side="left", padx=10)

        self.reset_btn = ctk.CTkButton(self.buttons_frame, text="Reiniciar", command=self.reset_timer, width=80)
        self.reset_btn.pack(side="left", padx=10)

    def on_time_change(self, value):
        self.timer.set_work_duration(int(value))

    def update_ui(self, remaining_time, state):
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
