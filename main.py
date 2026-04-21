import customtkinter as ctk
import threading
import time
import pygame
import csv
import os
import sys
from datetime import datetime, timedelta
from timer_logic import PomodoroTimer



# Configure CustomTkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class ReportWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Reportes de Trabajo")
        self.geometry("520x580")
        self.configure(fg_color="#0a0a0a")
        
        # Prevent opening multiple report windows by keeping focus
        self.grab_set()
        
        # Configurar colores para estética premium
        self.ACCENT_COLOR = "#8b5cf6" # Un tono morado/purpura agradable #7a2aff
        self.TEXT_GRAY = "#a3a3a3"
        self.GREEN_ARROW = "#22c55e"
        self.RED_ARROW = "#ef4444"

        self.setup_ui()
        self.update_data("Hoy")

        # Bind closing to release grab
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self):
        self.grab_release()
        self.destroy()

    def setup_ui(self):
        # Header "Estadísticas de Enfoque"
        self.header_label = ctk.CTkLabel(self, text="Estadísticas de Enfoque", font=("Arial", 24, "bold"), text_color="white")
        self.header_label.pack(anchor="w", padx=30, pady=(25, 15))
        
        # Tabs
        self.filter_var = ctk.StringVar(value="Hoy")
        self.filter_seg_btn = ctk.CTkSegmentedButton(
            self, 
            values=["Hoy", "7 Días", "28 Días"],
            variable=self.filter_var,
            command=self.update_data,
            selected_color=self.ACCENT_COLOR,
            selected_hover_color="#7c3aed",
            unselected_color="#18181b", # dark background for tabs
            unselected_hover_color="#27272a",
        )
        self.filter_seg_btn.pack(anchor="w", padx=30, pady=(0, 25))
        
        # Stats container
        self.stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.stats_frame.pack(fill="x", padx=30)
        
        self.stats_frame.grid_columnconfigure(0, weight=3)
        self.stats_frame.grid_columnconfigure(1, weight=2)
        self.stats_frame.grid_columnconfigure(2, weight=2)
        self.stats_frame.grid_columnconfigure(3, weight=3)
        
        # Stat: Focus Time
        f1 = ctk.CTkFrame(self.stats_frame, fg_color="transparent")
        f1.grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(f1, text="⚡ TIEMPO ENFOQUE", font=("Arial", 10, "bold"), text_color=self.TEXT_GRAY).pack(anchor="w")
        self.lbl_focus_time = ctk.CTkLabel(f1, text="0h 0m", font=("Arial", 22, "bold"), text_color="white")
        self.lbl_focus_time.pack(anchor="w")
        self.lbl_focus_comp = ctk.CTkLabel(f1, text="-- vs. ayer", font=("Arial", 10), text_color=self.TEXT_GRAY)
        self.lbl_focus_comp.pack(anchor="w")
        
        line1 = ctk.CTkFrame(self.stats_frame, width=1, fg_color="#27272a")
        line1.grid(row=0, column=0, sticky="e", pady=5)
        
        # Stat: Tasks
        f2 = ctk.CTkFrame(self.stats_frame, fg_color="transparent")
        f2.grid(row=0, column=1, padx=15, sticky="w")
        ctk.CTkLabel(f2, text="✅ TAREAS", font=("Arial", 10, "bold"), text_color=self.TEXT_GRAY).pack(anchor="w")
        self.lbl_tasks = ctk.CTkLabel(f2, text="0", font=("Arial", 22, "bold"), text_color="white")
        self.lbl_tasks.pack(anchor="w")
        ctk.CTkLabel(f2, text=" ", font=("Arial", 10)).pack() 
        
        line2 = ctk.CTkFrame(self.stats_frame, width=1, fg_color="#27272a")
        line2.grid(row=0, column=1, sticky="e", pady=5)

        # Stat: Sessions
        f3 = ctk.CTkFrame(self.stats_frame, fg_color="transparent")
        f3.grid(row=0, column=2, padx=15, sticky="w")
        ctk.CTkLabel(f3, text="🎯 SESIONES", font=("Arial", 10, "bold"), text_color=self.TEXT_GRAY).pack(anchor="w")
        self.lbl_sessions = ctk.CTkLabel(f3, text="0", font=("Arial", 22, "bold"), text_color="white")
        self.lbl_sessions.pack(anchor="w")
        ctk.CTkLabel(f3, text=" ", font=("Arial", 10)).pack() 
        
        line3 = ctk.CTkFrame(self.stats_frame, width=1, fg_color="#27272a")
        line3.grid(row=0, column=2, sticky="e", pady=5)

        # Stat: Break Time
        f4 = ctk.CTkFrame(self.stats_frame, fg_color="transparent")
        f4.grid(row=0, column=3, padx=15, sticky="w")
        ctk.CTkLabel(f4, text="☕ DESCANSO", font=("Arial", 10, "bold"), text_color=self.TEXT_GRAY).pack(anchor="w")
        self.lbl_break = ctk.CTkLabel(f4, text="0h 0m", font=("Arial", 22, "bold"), text_color="white")
        self.lbl_break.pack(anchor="w")
        ctk.CTkLabel(f4, text=" ", font=("Arial", 10)).pack() 
        
        # Horizontal Separator
        sep = ctk.CTkFrame(self, height=1, fg_color="#27272a")
        sep.pack(fill="x", padx=30, pady=25)
        
        # Subtitle
        ctk.CTkLabel(self, text="Productividad Reciente", font=("Arial", 16, "bold"), text_color="white").pack(anchor="w", padx=30)
        
        # Canvas for custom bar chart
        self.canvas_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.canvas_frame.pack(fill="both", expand=True, padx=30, pady=(10, 20))
        
        # To handle resize events safely, we bind Configure
        self.canvas = ctk.CTkCanvas(self.canvas_frame, bg="#0a0a0a", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda e: self.draw_chart())
        
        self.current_chart_data = []

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
                    b_mins = int(row["Minutos Descanso"]) if "Minutos Descanso" in row else 0
                    data.append({"date": dt, "work_mins": work_mins, "break_mins": b_mins})
                except Exception:
                    continue
        return data

    def update_data(self, filter_type):
        data = self.parse_data()
        now = datetime.now()
        
        # Helper to truncate time for date comparison
        def day_start(dt): return dt.replace(hour=0, minute=0, second=0, microsecond=0)
        today = day_start(now)
        
        # Filters
        if filter_type == "Hoy":
            current_start = today
            prev_start = today - timedelta(days=1)
            prev_end = today
            chart_days = 7 # We still show 7 days on chart for context
        elif filter_type == "7 Días":
            current_start = today - timedelta(days=6) # 7 days ending today
            prev_start = today - timedelta(days=13)
            prev_end = current_start
            chart_days = 7
        elif filter_type == "28 Días":
            current_start = today - timedelta(days=27)
            prev_start = today - timedelta(days=55)
            prev_end = current_start
            chart_days = 28 # For the chart we will group this differently

        curr_work = curr_tasks = curr_break = 0
        prev_work = 0

        # Aggregation for stats
        for d in data:
            dt = d["date"]
            if dt >= current_start:
                curr_work += d["work_mins"]
                curr_tasks += 1
                curr_break += d["break_mins"]
            elif prev_start <= dt < prev_end:
                prev_work += d["work_mins"]

        # Update Top Stats text
        def format_hm(total_mins):
            h, m = divmod(total_mins, 60)
            if h > 0: return f"{h}h {m}m"
            return f"{m}m"

        self.lbl_focus_time.configure(text=format_hm(curr_work))
        self.lbl_tasks.configure(text=str(curr_tasks))
        self.lbl_sessions.configure(text=str(curr_tasks))
        self.lbl_break.configure(text=format_hm(curr_break))
        
        # Percentage comparison
        if prev_work == 0:
            pct_text = "↑ --% vs previo"
            color = self.TEXT_GRAY
        else:
            diff = curr_work - prev_work
            pct = int((abs(diff) / prev_work) * 100)
            if diff >= 0:
                pct_text = f"↑ {pct}% vs previo"
                color = self.GREEN_ARROW
            else:
                pct_text = f"↓ {pct}% vs previo"
                color = self.RED_ARROW
                
        # Override specific label text if Hoy
        if filter_type == "Hoy":
            pct_text = pct_text.replace("previo", "ayer")
            
        self.lbl_focus_comp.configure(text=pct_text, text_color=color)

        # Build Chart Data
        self.current_chart_data = self.build_chart_data(data, filter_type, today)
        self.draw_chart()

    def build_chart_data(self, data, filter_type, today):
        # We'll create a list of dicts: [{'label': 'Jan 8', 'value': 45}, ...]
        chart_data = []
        if filter_type in ["Hoy", "7 Días"]:
            # Chart shows the last 7 days independently of it being "Hoy" or "7 Días"
            for i in range(6, -1, -1):
                target_day = today - timedelta(days=i)
                label = target_day.strftime("%b %d")
                
                day_work = 0
                for d in data:
                    if d["date"].date() == target_day.date():
                        day_work += d["work_mins"]
                        
                chart_data.append({"label": label, "value": day_work})
        else:
            # 28 days -> split into 4 weeks
            for w in range(3, -1, -1):
                w_start = today - timedelta(days=(w*7) + 6)
                w_end = today - timedelta(days=(w*7))
                
                label = f"{w_start.strftime('%d')}-{w_end.strftime('%d %b')}"
                
                week_work = 0
                for d in data:
                    if w_start.date() <= d["date"].date() <= w_end.date():
                        week_work += d["work_mins"]
                
                chart_data.append({"label": label, "value": week_work})
                
        return chart_data

    def draw_chart(self):
        self.canvas.delete("all")
        if not self.current_chart_data: return
        
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w <= 1 or h <= 1: 
            return # Canvas not initialized yet
            
        padding_top = 35
        padding_bottom = 35
        available_h = h - padding_top - padding_bottom
        
        # Add visual aesthetic adjustments to ensure text fits
        max_val = max([d["value"] for d in self.current_chart_data])
        if max_val == 0: max_val = 1 # avoid div by zero

        n_bars = len(self.current_chart_data)
        bar_width = min(35, w / (n_bars * 1.5))
        
        total_content_width = (n_bars * bar_width) + ((n_bars - 1) * bar_width * 0.8)
        start_x = (w - total_content_width) / 2
        
        def format_hm(total_mins):
            hrs, mins = divmod(total_mins, 60)
            if hrs > 0: return f"{hrs}h {mins}m"
            return f"{mins}m"
        
        for i, item in enumerate(self.current_chart_data):
            x = start_x + (i * bar_width * 1.8)
            val = item["value"]
            
            # Bar height proportional
            bar_height = (val / max_val) * available_h
            if val > 0 and bar_height < 10: bar_height = 10 # Minimum visible bump
            
            # For 0 value, draw a tiny line so it shows as a flat rounded pill
            if val == 0: bar_height = 4
            
            y1 = padding_top + available_h
            y0 = y1 - bar_height
            
            # Dibujar la barra con extremos redondeados (píldoras) usando create_line
            # En tk, create_line puede tener un width muy grueso y capstyle=ROUND
            self.canvas.create_line(x + bar_width/2, y1, x + bar_width/2, y0, 
                                  fill=self.ACCENT_COLOR, width=bar_width, capstyle="round")
                                  
            # Etiqueta inferior (Fecha)
            self.canvas.create_text(x + bar_width/2, y1 + bar_width/2 + 10, 
                                  text=item["label"], fill=self.TEXT_GRAY, font=("Arial", 9))
                                  
            # Valor superior (Tiempo)
            if val > 0:
                self.canvas.create_text(x + bar_width/2, y0 - bar_width/2 - 10, 
                                      text=format_hm(val), fill=self.TEXT_GRAY, font=("Arial", 10))



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
        # Top right/left buttons frame
        self.top_frame = ctk.CTkFrame(self, fg_color="transparent", height=40)
        self.top_frame.pack(fill="x", padx=15, pady=(10, 0))

        self.gear_btn = ctk.CTkButton(self.top_frame, text="⚙️", width=30, height=30, 
                                      corner_radius=15, fg_color="transparent", 
                                      hover_color="#333333", font=("Arial", 20),
                                      command=self.toggle_settings)
        self.gear_btn.pack(side="left")

        # Time selector (hidden by default)
        self.time_selector_frame = ctk.CTkFrame(self, fg_color="transparent")
        
        ctk.CTkLabel(self.time_selector_frame, text="Tiempo (min):").pack(side="left", padx=5)
        self.time_var = ctk.StringVar(value="25")
        self.time_dropdown = ctk.CTkOptionMenu(
            self.time_selector_frame, 
            values=["25", "30", "45", "60"], 
            variable=self.time_var,
            command=self.on_time_change
        )
        self.time_dropdown.pack(side="left", padx=5)

        # Circular Timer Canvas
        bg_color = self._get_appearance_mode() # get current bg color
        if bg_color == "Dark":
            canvas_bg = "#242424" # Default CTk dark background
        else:
            canvas_bg = "#EBEBEB"
            
        self.canvas = ctk.CTkCanvas(self, width=280, height=280, bg=canvas_bg, highlightthickness=0)
        self.canvas.pack(pady=(10, 20))
        
        # Background track
        self.arc_bg = self.canvas.create_oval(20, 20, 260, 260, outline="#333333", width=12)
        
        # Progress track
        self.arc_fg = self.canvas.create_arc(20, 20, 260, 260, start=90, extent=-360, style="arc", outline="#f5680c", width=12)
        
        # Inner text elements
        self.icon_text = self.canvas.create_text(140, 70, text="🍅", font=("Arial", 36))
        self.time_text = self.canvas.create_text(140, 130, text="25:00", font=("Arial", 56, "bold"), fill="white")
        self.status_text = self.canvas.create_text(140, 185, text="FOCUS", font=("Arial", 16, "bold"), fill="#aaaaaa")
        self.play_icon = self.canvas.create_text(140, 230, text="▶", font=("Arial", 30), fill="white")
        
        # Bind play/pause to the icon and the text
        self.canvas.tag_bind(self.play_icon, "<Button-1>", self.on_play_pause_click)
        self.canvas.tag_bind(self.time_text, "<Button-1>", self.on_play_pause_click)

        # Transition button (Pomodoro/Break)
        self.buttons_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.buttons_frame.pack(pady=0)
        self.transition_btn = ctk.CTkButton(self.buttons_frame, text="SKIP", width=140, height=40, corner_radius=20, 
                                            fg_color="#333333", hover_color="#444444", font=("Arial", 14, "bold"),
                                            command=self.skip_state)
        self.transition_btn.pack()

        # Reset button moved to top right
        self.reset_btn = ctk.CTkButton(self.top_frame, text="🔄", width=30, height=30, 
                                      corner_radius=15, fg_color="transparent", 
                                      hover_color="#333333", font=("Arial", 20),
                                      command=self.reset_timer)
        self.reset_btn.pack(side="right")

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


    def _get_appearance_mode(self):
        return ctk.get_appearance_mode()

    def toggle_settings(self):
        if self.time_selector_frame.winfo_ismapped():
            self.time_selector_frame.pack_forget()
        else:
            # Place it right below the top frame
            self.time_selector_frame.pack(after=self.top_frame, pady=5)

    def on_play_pause_click(self, event):
        if self.timer.is_running and not self.timer.is_paused:
            self.pause_timer()
        else:
            self.start_timer()

    def skip_state(self):
        # Manually transition state via timer logic and start automatically
        self.timer.transition_state()
        self.timer.start()

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
        self.canvas.itemconfig(self.time_text, text=timeformat)
        
        # Toggle play/pause icon based on pause state
        if not self.timer.is_running or self.timer.is_paused:
            self.canvas.itemconfig(self.play_icon, text="▶")
        else:
            self.canvas.itemconfig(self.play_icon, text="⏸")
        
        # Calculate progress and colors based on state
        total_time = 0
        if state == "Work":
            total_time = self.timer.work_duration
            color = "#f5680c" # Orange/Red
            icon = "🍅"
            status = "FOCUS"
            skip_text = "BREAK"
        elif state == "Short Break":
            total_time = self.timer.short_break
            color = "#3d85c6" # Blue
            icon = "☕"
            status = "RELAX"
            skip_text = "POMODORO"
        elif state == "Long Break":
            total_time = self.timer.long_break
            color = "#90EE90" # Green for long break
            icon = "☕"
            status = "LONG RELAX"
            skip_text = "POMODORO"
            
        self.canvas.itemconfig(self.icon_text, text=icon)
        self.canvas.itemconfig(self.status_text, text=status)
        self.canvas.itemconfig(self.arc_fg, outline=color)
        self.transition_btn.configure(text=skip_text)
        
        # Arc progress
        if total_time > 0:
            remaining = self.timer.current_time
            progress = remaining / total_time
            # Keep extent bounded
            extent = max(-360.0, min(0.0, -360.0 * progress))
            if extent == 0 and remaining > 0:
                extent = -1 # Small visual safety
            self.canvas.itemconfig(self.arc_fg, extent=extent)
            
        if timeformat == "00:00":
            self.canvas.itemconfig(self.play_icon, text="▶")
            import tkinter.messagebox as messagebox
            display_state = { "Work": "Trabajo", "Short Break": "Descanso Corto", "Long Break": "Descanso Largo" }.get(state, state)
            messagebox.showinfo("¡Tiempo completado!", f"El ciclo de {display_state} ha terminado.\nInicia manualmente para continuar o salta a la siguiente fase.")

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
        mins, secs = divmod(self.timer.current_time, 60)
        self._apply_ui_update(f"{mins:02d}:{secs:02d}", self.timer.current_state)

    def reset_timer(self):
        self.timer.reset()
        mins, secs = divmod(self.timer.current_time, 60)
        self._apply_ui_update(f"{mins:02d}:{secs:02d}", self.timer.current_state)

if __name__ == "__main__":
    app = PomodoroApp()
    app.mainloop()
