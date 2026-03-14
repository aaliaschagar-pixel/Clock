import json
import os
import time
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

try:
    import pygame
except Exception:  # pygame is optional
    pygame = None


class SettingsManager:
    """Loads and saves user preferences to a JSON file."""

    DEFAULTS = {
        "background_color": "#0d1117",
        "text_color": "#e6edf3",
        "accent_color": "#58a6ff",
        "font_size": 92,
        "font_family": "Helvetica",
        "theme": "dark",
        "background_mode": "animated_gradient",
        "gradient_animation": True,
        "sound_volume": 0.5,
    }

    def __init__(self, path):
        self.path = path
        self.settings = self.load()

    def load(self):
        if not os.path.exists(self.path):
            return self.DEFAULTS.copy()
        try:
            with open(self.path, "r", encoding="utf-8") as file:
                data = json.load(file)
        except (json.JSONDecodeError, OSError):
            data = {}
        merged = self.DEFAULTS.copy()
        merged.update(data)
        return merged

    def save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as file:
            json.dump(self.settings, file, indent=2)


class SoundPlayer:
    """Optional looping ambient sound player using pygame."""

    def __init__(self, sounds_dir, settings_manager):
        self.sounds_dir = sounds_dir
        self.settings_manager = settings_manager
        self.current_track = None
        self.initialized = False

        if pygame:
            try:
                pygame.mixer.init()
                pygame.mixer.music.set_volume(self.settings_manager.settings["sound_volume"])
                self.initialized = True
            except Exception:
                self.initialized = False

    def play(self, filename):
        if not self.initialized:
            return False
        full_path = os.path.join(self.sounds_dir, filename)
        if not os.path.exists(full_path):
            return False
        try:
            pygame.mixer.music.load(full_path)
            pygame.mixer.music.play(loops=-1)
            self.current_track = filename
            return True
        except Exception:
            return False

    def pause(self):
        if self.initialized:
            pygame.mixer.music.pause()

    def resume(self):
        if self.initialized:
            pygame.mixer.music.unpause()

    def stop(self):
        if self.initialized:
            pygame.mixer.music.stop()
            self.current_track = None

    def set_volume(self, volume):
        self.settings_manager.settings["sound_volume"] = volume
        if self.initialized:
            pygame.mixer.music.set_volume(volume)


class GradientBackground:
    """Draws animated gradients or static background fills on a canvas."""

    NIGHT_COLORS = ["#0f172a", "#1e293b", "#334155", "#0b1120"]

    def __init__(self, canvas):
        self.canvas = canvas
        self.t = 0
        self.running = True

    @staticmethod
    def _hex_to_rgb(value):
        value = value.lstrip("#")
        return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))

    @staticmethod
    def _rgb_to_hex(rgb):
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"

    def _blend(self, c1, c2, ratio):
        r1, g1, b1 = self._hex_to_rgb(c1)
        r2, g2, b2 = self._hex_to_rgb(c2)
        mixed = (
            int(r1 + (r2 - r1) * ratio),
            int(g1 + (g2 - g1) * ratio),
            int(b1 + (b2 - b1) * ratio),
        )
        return self._rgb_to_hex(mixed)

    def draw(self, width, height, mode, base_color="#111111", animate=True):
        self.canvas.delete("bg")
        if mode == "static":
            self.canvas.create_rectangle(0, 0, width, height, fill=base_color, outline="", tags="bg")
            return

        if mode == "night":
            colors = self.NIGHT_COLORS
        else:
            colors = ["#111827", "#1d4ed8", "#0ea5e9", "#1e1b4b"]

        shift = (self.t % 200) / 200 if animate else 0.35
        steps = max(20, height // 6)
        for i in range(steps):
            ratio = i / max(1, steps - 1)
            color_a = self._blend(colors[0], colors[1], (ratio + shift) % 1)
            color_b = self._blend(colors[2], colors[3], (ratio * 0.8 + shift) % 1)
            color = self._blend(color_a, color_b, 0.5)
            y0 = int((height / steps) * i)
            y1 = int((height / steps) * (i + 1)) + 1
            self.canvas.create_rectangle(0, y0, width, y1, fill=color, outline="", tags="bg")
        self.t += 2


class Stopwatch:
    def __init__(self, app):
        self.app = app
        self.running = False
        self.start_time = None
        self.elapsed_before_pause = 0.0
        self.laps = []

    def start_pause(self):
        if self.running:
            self.elapsed_before_pause += time.time() - self.start_time
            self.running = False
        else:
            self.start_time = time.time()
            self.running = True

    def reset(self):
        self.running = False
        self.start_time = None
        self.elapsed_before_pause = 0.0
        self.laps.clear()

    def add_lap(self):
        elapsed = self.current_seconds()
        self.laps.append(elapsed)

    def current_seconds(self):
        if self.running:
            return self.elapsed_before_pause + (time.time() - self.start_time)
        return self.elapsed_before_pause

    @staticmethod
    def format_seconds(seconds):
        millis = int((seconds - int(seconds)) * 100)
        total = int(seconds)
        hrs = total // 3600
        mins = (total % 3600) // 60
        secs = total % 60
        return f"{hrs:02}:{mins:02}:{secs:02}.{millis:02}"


class CountdownTimer:
    def __init__(self, app):
        self.app = app
        self.running = False
        self.total_seconds = 0
        self.remaining = 0
        self.last_tick = None

    def start(self, total_seconds):
        if total_seconds <= 0:
            return
        self.total_seconds = total_seconds
        self.remaining = float(total_seconds)
        self.running = True
        self.last_tick = time.time()

    def pause_resume(self):
        if not self.total_seconds:
            return
        self.running = not self.running
        self.last_tick = time.time()

    def reset(self):
        self.running = False
        self.total_seconds = 0
        self.remaining = 0
        self.last_tick = None

    def update(self):
        if not self.running:
            return False
        now = time.time()
        if self.last_tick is None:
            self.last_tick = now
        delta = now - self.last_tick
        self.last_tick = now
        self.remaining = max(0.0, self.remaining - delta)
        finished = self.remaining <= 0
        if finished:
            self.running = False
        return finished

    @staticmethod
    def format_seconds(seconds):
        total = max(0, int(round(seconds)))
        mins = total // 60
        secs = total % 60
        return f"{mins:02}:{secs:02}"

    def progress(self):
        if self.total_seconds <= 0:
            return 0
        return 1 - (self.remaining / self.total_seconds)


class PomodoroTimer:
    def __init__(self, app, study_minutes=25, break_minutes=5):
        self.app = app
        self.study_seconds = study_minutes * 60
        self.break_seconds = break_minutes * 60
        self.running = False
        self.in_study = True
        self.remaining = float(self.study_seconds)
        self.last_tick = None
        self.completed_cycles = 0

    def start_pause(self):
        self.running = not self.running
        self.last_tick = time.time()

    def reset(self):
        self.running = False
        self.in_study = True
        self.remaining = float(self.study_seconds)
        self.last_tick = None
        self.completed_cycles = 0

    def current_total(self):
        return self.study_seconds if self.in_study else self.break_seconds

    def update(self):
        if not self.running:
            return None
        now = time.time()
        if self.last_tick is None:
            self.last_tick = now
        delta = now - self.last_tick
        self.last_tick = now
        self.remaining = max(0.0, self.remaining - delta)
        if self.remaining > 0:
            return None

        just_finished = "study" if self.in_study else "break"
        if self.in_study:
            self.completed_cycles += 1
            self.app.stats["pomodoro_cycles"] += 1
            self.app.stats["total_focus_seconds"] += self.study_seconds
            self.in_study = False
            self.remaining = float(self.break_seconds)
        else:
            self.in_study = True
            self.remaining = float(self.study_seconds)
        return just_finished

    def progress(self):
        total = self.current_total()
        if total <= 0:
            return 0
        return 1 - (self.remaining / total)


class ClockApp:
    MODES = ["CLOCK", "STOPWATCH", "TIMER", "POMODORO", "STATS", "CLASSROOM"]

    def __init__(self, root):
        self.root = root
        self.root.title("Study Productivity Clock")
        self.root.attributes("-fullscreen", True)

        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.settings_manager = SettingsManager(os.path.join(base_dir, "settings.json"))
        self.sound_player = SoundPlayer(os.path.join(base_dir, "sounds"), self.settings_manager)

        self.settings = self.settings_manager.settings
        self.stats = {
            "total_focus_seconds": 0,
            "pomodoro_cycles": 0,
            "stopwatch_seconds": 0,
            "timers_completed": 0,
        }
        self.mode = "CLOCK"

        self.stopwatch = Stopwatch(self)
        self.countdown = CountdownTimer(self)
        self.pomodoro = PomodoroTimer(self)
        self.classroom = CountdownTimer(self)

        self.build_ui()
        self.bind_shortcuts()
        self.animate_transition_ready = True
        self.tick()

    def build_ui(self):
        self.canvas = tk.Canvas(self.root, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda _event: self.redraw_background())
        self.gradient = GradientBackground(self.canvas)

        self.main_container = tk.Frame(self.canvas, bg=self.settings["background_color"])
        self.canvas_window = self.canvas.create_window(0, 0, anchor="nw", window=self.main_container)

        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)

        self.display_label = tk.Label(
            self.main_container,
            text="",
            font=(self.settings["font_family"], self.settings["font_size"], "bold"),
            fg=self.settings["text_color"],
            bg=self.settings["background_color"],
        )
        self.display_label.grid(row=0, column=0, sticky="nsew", pady=(40, 10))

        self.sub_label = tk.Label(
            self.main_container,
            text="",
            font=(self.settings["font_family"], 28),
            fg=self.settings["accent_color"],
            bg=self.settings["background_color"],
        )
        self.sub_label.grid(row=1, column=0)

        self.progress = ttk.Progressbar(self.main_container, mode="determinate", maximum=100, length=700)
        self.progress.grid(row=2, column=0, pady=10)

        self.dynamic_panel = tk.Frame(self.main_container, bg=self.settings["background_color"])
        self.dynamic_panel.grid(row=3, column=0, pady=12)

        self.bottom_bar = tk.Frame(self.main_container, bg=self.settings["background_color"])
        self.bottom_bar.grid(row=4, column=0, pady=(20, 30))

        for mode in self.MODES:
            button = tk.Button(
                self.bottom_bar,
                text=mode,
                command=lambda m=mode: self.switch_mode(m),
                bg=self.settings["accent_color"],
                fg="#ffffff",
                relief="flat",
                padx=14,
                pady=8,
                font=(self.settings["font_family"], 12, "bold"),
            )
            button.pack(side="left", padx=5)

        self.build_settings_panel()
        self.build_sound_panel()
        self.switch_mode("CLOCK", animate=False)
        self.update_layout()

    def update_layout(self):
        width = self.root.winfo_width() or self.root.winfo_screenwidth()
        height = self.root.winfo_height() or self.root.winfo_screenheight()
        self.canvas.coords(self.canvas_window, width / 2, height / 2)
        self.canvas.itemconfig(self.canvas_window, anchor="center")
        self.redraw_background()

    def redraw_background(self):
        width = self.root.winfo_width() or self.root.winfo_screenwidth()
        height = self.root.winfo_height() or self.root.winfo_screenheight()
        self.canvas.config(width=width, height=height)
        self.gradient.draw(
            width,
            height,
            mode=self.settings.get("background_mode", "animated_gradient"),
            base_color=self.settings["background_color"],
            animate=self.settings.get("gradient_animation", True),
        )
        self.canvas.tag_lower("bg")

    def bind_shortcuts(self):
        self.root.bind("<F11>", lambda _e: self.toggle_fullscreen())
        self.root.bind("<Escape>", lambda _e: self.root.attributes("-fullscreen", False))
        self.root.bind("<space>", lambda _e: self.context_start_pause())
        self.root.bind("r", lambda _e: self.context_reset())
        self.root.bind("c", lambda _e: self.switch_mode("CLOCK"))
        self.root.bind("s", lambda _e: self.switch_mode("STOPWATCH"))
        self.root.bind("t", lambda _e: self.switch_mode("TIMER"))
        self.root.bind("p", lambda _e: self.switch_mode("POMODORO"))
        self.root.bind("m", lambda _e: self.switch_mode("CLASSROOM"))

    def toggle_fullscreen(self):
        current = self.root.attributes("-fullscreen")
        self.root.attributes("-fullscreen", not current)

    def context_start_pause(self):
        if self.mode == "STOPWATCH":
            self.stopwatch.start_pause()
        elif self.mode == "TIMER":
            if self.countdown.total_seconds <= 0:
                self.start_timer_from_inputs()
            else:
                self.countdown.pause_resume()
        elif self.mode == "POMODORO":
            self.pomodoro.start_pause()
        elif self.mode == "CLASSROOM":
            if self.classroom.total_seconds <= 0:
                self.start_classroom_from_input()
            else:
                self.classroom.pause_resume()

    def context_reset(self):
        if self.mode == "STOPWATCH":
            self.stopwatch.reset()
            self.lap_list.delete(0, "end")
        elif self.mode == "TIMER":
            self.countdown.reset()
        elif self.mode == "POMODORO":
            self.pomodoro.reset()
        elif self.mode == "CLASSROOM":
            self.classroom.reset()

    def clear_dynamic_panel(self):
        for child in self.dynamic_panel.winfo_children():
            child.destroy()

    def switch_mode(self, mode, animate=True):
        self.mode = mode
        if animate and self.animate_transition_ready:
            self.fade_transition()
        self.clear_dynamic_panel()

        self.progress.grid_remove()
        self.sub_label.config(text="")

        if mode == "STOPWATCH":
            self.build_stopwatch_panel()
        elif mode == "TIMER":
            self.build_timer_panel()
            self.progress.grid()
        elif mode == "POMODORO":
            self.build_pomodoro_panel()
            self.progress.grid()
        elif mode == "STATS":
            self.build_stats_panel()
        elif mode == "CLASSROOM":
            self.build_classroom_panel()
            self.progress.grid()
        self.update_style()

    def fade_transition(self):
        # Keep transition short so timer updates remain responsive.
        for alpha in (1.0, 0.92, 0.84, 0.76):
            self.root.attributes("-alpha", alpha)
            self.root.update_idletasks()
            self.root.after(12)
        for alpha in (0.84, 0.92, 1.0):
            self.root.attributes("-alpha", alpha)
            self.root.update_idletasks()
            self.root.after(12)

    def build_stopwatch_panel(self):
        controls = tk.Frame(self.dynamic_panel, bg=self.settings["background_color"])
        controls.pack()
        self.make_button(controls, "Start/Pause", self.stopwatch.start_pause).pack(side="left", padx=5)
        self.make_button(controls, "Reset", lambda: [self.stopwatch.reset(), self.lap_list.delete(0, "end")]).pack(side="left", padx=5)
        self.make_button(controls, "Lap", self.add_lap).pack(side="left", padx=5)

        self.lap_list = tk.Listbox(
            self.dynamic_panel,
            width=42,
            height=7,
            bg=self.settings["background_color"],
            fg=self.settings["text_color"],
            highlightthickness=1,
            selectbackground=self.settings["accent_color"],
            font=(self.settings["font_family"], 12),
        )
        self.lap_list.pack(pady=10)

    def build_timer_panel(self):
        input_row = tk.Frame(self.dynamic_panel, bg=self.settings["background_color"])
        input_row.pack(pady=4)

        self.timer_min = tk.StringVar(value="10")
        self.timer_sec = tk.StringVar(value="00")

        self.make_entry(input_row, self.timer_min, "MM").pack(side="left", padx=5)
        self.make_entry(input_row, self.timer_sec, "SS").pack(side="left", padx=5)

        controls = tk.Frame(self.dynamic_panel, bg=self.settings["background_color"])
        controls.pack(pady=8)
        self.make_button(controls, "Start", self.start_timer_from_inputs).pack(side="left", padx=5)
        self.make_button(controls, "Pause/Resume", self.countdown.pause_resume).pack(side="left", padx=5)
        self.make_button(controls, "Reset", self.countdown.reset).pack(side="left", padx=5)

    def build_pomodoro_panel(self):
        controls = tk.Frame(self.dynamic_panel, bg=self.settings["background_color"])
        controls.pack(pady=4)
        self.make_button(controls, "Start/Pause", self.pomodoro.start_pause).pack(side="left", padx=5)
        self.make_button(controls, "Reset", self.pomodoro.reset).pack(side="left", padx=5)

    def build_stats_panel(self):
        panel = tk.Frame(self.dynamic_panel, bg=self.settings["background_color"])
        panel.pack(pady=6)
        stats_text = (
            f"Total Focus Time: {self.format_hms(self.stats['total_focus_seconds'])}\n"
            f"Pomodoro Cycles: {self.stats['pomodoro_cycles']}\n"
            f"Stopwatch Time: {self.format_hms(int(self.stats['stopwatch_seconds']))}\n"
            f"Timer Sessions Completed: {self.stats['timers_completed']}"
        )
        label = tk.Label(
            panel,
            text=stats_text,
            justify="left",
            fg=self.settings["text_color"],
            bg=self.settings["background_color"],
            font=(self.settings["font_family"], 24),
        )
        label.pack()

    def build_classroom_panel(self):
        row = tk.Frame(self.dynamic_panel, bg=self.settings["background_color"])
        row.pack()
        self.classroom_min = tk.StringVar(value="60")
        self.make_entry(row, self.classroom_min, "Exam Minutes").pack(side="left", padx=5)
        self.make_button(row, "Set & Start", self.start_classroom_from_input).pack(side="left", padx=5)
        self.make_button(row, "Pause/Resume", self.classroom.pause_resume).pack(side="left", padx=5)
        self.make_button(row, "Reset", self.classroom.reset).pack(side="left", padx=5)

    def build_settings_panel(self):
        frame = tk.Frame(self.main_container, bg=self.settings["background_color"])
        frame.grid(row=5, column=0, pady=(0, 10))

        tk.Label(frame, text="Theme:", bg=self.settings["background_color"], fg=self.settings["text_color"]).pack(side="left")
        theme_var = tk.StringVar(value=self.settings["theme"])
        theme_menu = ttk.Combobox(frame, width=8, textvariable=theme_var, values=["dark", "light"], state="readonly")
        theme_menu.pack(side="left", padx=4)

        tk.Label(frame, text="Font:", bg=self.settings["background_color"], fg=self.settings["text_color"]).pack(side="left")
        self.font_var = tk.StringVar(value=self.settings["font_family"])
        font_menu = ttk.Combobox(
            frame,
            width=14,
            textvariable=self.font_var,
            values=["Helvetica", "Arial", "Times", "Courier", "Calibri"],
            state="readonly",
        )
        font_menu.pack(side="left", padx=4)

        tk.Label(frame, text="Size:", bg=self.settings["background_color"], fg=self.settings["text_color"]).pack(side="left")
        size_var = tk.IntVar(value=self.settings["font_size"])
        tk.Scale(
            frame,
            from_=48,
            to=160,
            orient="horizontal",
            variable=size_var,
            length=180,
            bg=self.settings["background_color"],
            fg=self.settings["text_color"],
            highlightthickness=0,
            command=lambda _e: self.change_setting("font_size", size_var.get()),
        ).pack(side="left", padx=4)

        bg_mode_var = tk.StringVar(value=self.settings.get("background_mode", "animated_gradient"))
        bg_modes = ["animated_gradient", "static", "night"]
        ttk.Combobox(frame, width=16, textvariable=bg_mode_var, values=bg_modes, state="readonly").pack(side="left", padx=4)

        animation_var = tk.BooleanVar(value=self.settings.get("gradient_animation", True))
        tk.Checkbutton(
            frame,
            text="Animate",
            variable=animation_var,
            bg=self.settings["background_color"],
            fg=self.settings["text_color"],
            selectcolor=self.settings["background_color"],
            command=lambda: self.change_setting("gradient_animation", animation_var.get()),
        ).pack(side="left", padx=4)

        self.make_button(frame, "Apply Theme", lambda: self.apply_theme(theme_var.get())).pack(side="left", padx=4)
        self.make_button(frame, "Apply Font", lambda: self.change_setting("font_family", self.font_var.get())).pack(side="left", padx=4)
        self.make_button(frame, "BG Mode", lambda: self.change_setting("background_mode", bg_mode_var.get())).pack(side="left", padx=4)

    def build_sound_panel(self):
        frame = tk.Frame(self.main_container, bg=self.settings["background_color"])
        frame.grid(row=6, column=0, pady=(0, 18))
        tk.Label(frame, text="Ambient:", bg=self.settings["background_color"], fg=self.settings["text_color"]).pack(side="left")

        self.sound_choice = tk.StringVar(value="rain.mp3")
        ttk.Combobox(
            frame,
            width=16,
            textvariable=self.sound_choice,
            values=["rain.mp3", "cafe.mp3", "forest.mp3", "white_noise.mp3"],
            state="readonly",
        ).pack(side="left", padx=4)

        self.make_button(frame, "Play", lambda: self.handle_sound_play()).pack(side="left", padx=4)
        self.make_button(frame, "Pause", self.sound_player.pause).pack(side="left", padx=4)
        self.make_button(frame, "Stop", self.sound_player.stop).pack(side="left", padx=4)

        volume_var = tk.DoubleVar(value=self.settings.get("sound_volume", 0.5))
        tk.Scale(
            frame,
            from_=0,
            to=1,
            resolution=0.05,
            orient="horizontal",
            variable=volume_var,
            length=180,
            bg=self.settings["background_color"],
            fg=self.settings["text_color"],
            highlightthickness=0,
            command=lambda _e: self.change_volume(volume_var.get()),
        ).pack(side="left", padx=4)

    def handle_sound_play(self):
        success = self.sound_player.play(self.sound_choice.get())
        if not success:
            messagebox.showinfo(
                "Ambient Audio",
                "Unable to play sound. Install pygame and add files in study_clock/sounds/",
            )

    def make_button(self, parent, text, command):
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=self.settings["accent_color"],
            fg="#ffffff",
            relief="flat",
            padx=10,
            pady=6,
            font=(self.settings["font_family"], 11, "bold"),
        )

    def make_entry(self, parent, textvariable, hint):
        entry = tk.Entry(
            parent,
            textvariable=textvariable,
            justify="center",
            width=8,
            font=(self.settings["font_family"], 14),
            bg=self.settings["background_color"],
            fg=self.settings["text_color"],
            insertbackground=self.settings["text_color"],
            relief="solid",
            highlightbackground=self.settings["accent_color"],
            highlightcolor=self.settings["accent_color"],
            highlightthickness=1,
        )
        entry.insert(0, textvariable.get() or hint)
        return entry

    def add_lap(self):
        self.stopwatch.add_lap()
        index = len(self.stopwatch.laps)
        current = self.stopwatch.laps[-1]
        self.lap_list.insert("end", f"Lap {index:02} - {self.stopwatch.format_seconds(current)}")

    def start_timer_from_inputs(self):
        try:
            minutes = int(self.timer_min.get())
            seconds = int(self.timer_sec.get())
            total = minutes * 60 + seconds
            self.countdown.start(total)
        except (TypeError, ValueError):
            messagebox.showerror("Invalid Time", "Enter whole numbers for minutes and seconds.")

    def start_classroom_from_input(self):
        try:
            minutes = int(self.classroom_min.get())
            self.classroom.start(minutes * 60)
        except (TypeError, ValueError):
            messagebox.showerror("Invalid Duration", "Enter classroom duration in minutes.")

    def apply_theme(self, theme):
        if theme == "light":
            self.change_setting("background_color", "#f4f7fb")
            self.change_setting("text_color", "#1f2937")
            self.change_setting("accent_color", "#2563eb")
        else:
            self.change_setting("background_color", "#0d1117")
            self.change_setting("text_color", "#e6edf3")
            self.change_setting("accent_color", "#58a6ff")
        self.change_setting("theme", theme)

    def change_volume(self, value):
        self.sound_player.set_volume(float(value))
        self.settings_manager.save()

    def change_setting(self, key, value):
        self.settings[key] = value
        self.update_style()
        self.settings_manager.save()

    def update_style(self):
        self.main_container.config(bg=self.settings["background_color"])
        self.display_label.config(
            bg=self.settings["background_color"],
            fg=self.settings["text_color"],
            font=(self.settings["font_family"], self.settings["font_size"], "bold"),
        )
        self.sub_label.config(
            bg=self.settings["background_color"],
            fg=self.settings["accent_color"],
            font=(self.settings["font_family"], 28),
        )
        for section in (self.dynamic_panel, self.bottom_bar):
            section.config(bg=self.settings["background_color"])
            for child in section.winfo_children():
                if isinstance(child, tk.Button):
                    child.config(bg=self.settings["accent_color"], font=(self.settings["font_family"], 12, "bold"))
                else:
                    try:
                        child.config(bg=self.settings["background_color"], fg=self.settings["text_color"])
                    except tk.TclError:
                        pass
        self.redraw_background()

    @staticmethod
    def format_hms(total_seconds):
        total = int(total_seconds)
        hrs = total // 3600
        mins = (total % 3600) // 60
        secs = total % 60
        return f"{hrs:02}:{mins:02}:{secs:02}"

    def tick(self):
        self.update_layout()
        self.update_mode_display()
        self.root.after(50, self.tick)

    def update_mode_display(self):
        if self.mode == "CLOCK":
            self.display_label.config(text=datetime.now().strftime("%H:%M:%S"))
            self.sub_label.config(text=datetime.now().strftime("%A, %d %B %Y"))

        elif self.mode == "STOPWATCH":
            self.display_label.config(text=self.stopwatch.format_seconds(self.stopwatch.current_seconds()))
            self.stats["stopwatch_seconds"] = self.stopwatch.current_seconds()

        elif self.mode == "TIMER":
            finished = self.countdown.update()
            self.display_label.config(text=self.countdown.format_seconds(self.countdown.remaining))
            self.progress["value"] = self.countdown.progress() * 100
            self.sub_label.config(text="Countdown Timer")
            if finished:
                self.stats["timers_completed"] += 1
                self.sound_player.play("white_noise.mp3")
                messagebox.showinfo("Timer Complete", "Great work! Countdown finished.")
                self.sound_player.stop()

        elif self.mode == "POMODORO":
            finished_segment = self.pomodoro.update()
            segment = "Study" if self.pomodoro.in_study else "Break"
            self.display_label.config(text=CountdownTimer.format_seconds(self.pomodoro.remaining))
            self.sub_label.config(text=f"{segment} Session | Cycles: {self.pomodoro.completed_cycles}")
            self.progress["value"] = self.pomodoro.progress() * 100
            if finished_segment == "study":
                messagebox.showinfo("Pomodoro", "Study block complete! Take a short break.")
            elif finished_segment == "break":
                messagebox.showinfo("Pomodoro", "Break over. Start your next focus cycle!")

        elif self.mode == "STATS":
            self.display_label.config(text="Session Statistics")
            self.build_stats_panel()

        elif self.mode == "CLASSROOM":
            self.classroom.update()
            remain = self.classroom.remaining
            self.display_label.config(
                text=CountdownTimer.format_seconds(remain),
                font=(self.settings["font_family"], max(120, self.settings["font_size"] + 40), "bold"),
            )
            self.sub_label.config(text="Classroom Presentation Timer")
            self.progress["value"] = self.classroom.progress() * 100
            if remain <= 300 and self.classroom.total_seconds > 0:  # last 5 minutes warning
                self.display_label.config(fg="#ef4444")
            else:
                self.display_label.config(fg=self.settings["text_color"])


if __name__ == "__main__":
    app_root = tk.Tk()
    app = ClockApp(app_root)
    app_root.mainloop()
