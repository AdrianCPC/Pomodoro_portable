import time

class PomodoroTimer:
    def __init__(self, callback):
        self.callback = callback # Function to update UI thread safely
        self.is_running = False
        self.is_paused = False
        self.work_duration = 25 * 60
        self.short_break = 5 * 60
        self.long_break = 15 * 60
        self.current_time = self.work_duration
        self.work_sessions_completed = 0
        self.current_state = "Work" # Work, Short Break, Long Break

    def set_work_duration(self, work_min):
        self.work_duration = work_min * 60
        if not self.is_running and self.current_state == "Work":
            self.current_time = self.work_duration
            self.callback(self.current_time, self.current_state)

    def start(self):
        if self.current_time == 0:
            self.transition_state()
        if not self.is_running:
            self.is_running = True
        self.is_paused = False

    def pause(self):
        if self.is_running:
            self.is_paused = not self.is_paused

    def reset(self):
        self.is_running = False
        self.is_paused = False
        self.current_state = "Work"
        self.work_sessions_completed = 0
        self.current_time = self.work_duration
        self.callback(self.current_time, self.current_state)

    def tick(self):
        if self.is_running and not self.is_paused:
            if self.current_time > 0:
                self.current_time -= 1
                self.callback(self.current_time, self.current_state)
                # Auto pause when time is up
                if self.current_time == 0:
                    self.is_paused = True

    def transition_state(self):
        if self.current_state == "Work":
            self.work_sessions_completed += 1
            if self.work_sessions_completed % 4 == 0:
                self.current_state = "Long Break"
                self.current_time = self.long_break
            else:
                self.current_state = "Short Break"
                self.current_time = self.short_break
        else:
            self.current_state = "Work"
            self.current_time = self.work_duration
            
        self.callback(self.current_time, self.current_state)
