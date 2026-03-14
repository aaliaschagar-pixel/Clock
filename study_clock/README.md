# Study Clock (Tkinter)

A fullscreen minimalist productivity clock for study sessions, class presentations, and focus routines.

## Features

- Fullscreen digital clock with date display.
- Stopwatch with millisecond precision and lap list.
- Countdown timer with progress bar and completion alert.
- Pomodoro cycle timer (25/5) with automatic alternation and cycle count.
- Classroom mode with extra-large countdown and final-time warning color.
- Session statistics panel (focus time, Pomodoro cycles, stopwatch duration, completed timers).
- Customization controls (theme, colors, font family/size, background mode, animation toggle).
- Animated gradient background modes (animated, static, night).
- Ambient sound player with loop + volume (requires `pygame`).
- Keyboard shortcuts and smooth visual mode transitions.

## Project structure

```text
study_clock/
├── main.py
├── sounds/
│   ├── rain.mp3
│   ├── cafe.mp3
│   ├── forest.mp3
│   └── white_noise.mp3
├── settings.json
└── README.md
```

> Add your own `.mp3` files inside `sounds/` using the exact names above.

## Requirements

- Python 3.10+
- Tkinter (ships with most Python distributions)
- Optional: `pygame` for ambient audio playback

Install optional dependency:

```bash
pip install pygame
```

## Run

```bash
cd study_clock
python main.py
```

## Keyboard shortcuts

- `F11`: Toggle fullscreen
- `ESC`: Exit fullscreen
- `SPACE`: Start/Pause current timer or stopwatch
- `R`: Reset current timer/stopwatch
- `C`: Clock mode
- `S`: Stopwatch mode
- `T`: Countdown timer mode
- `P`: Pomodoro mode
- `M`: Classroom mode

## Notes

- All timers are non-blocking and use Tkinter's `after()` scheduler.
- UI settings persist in `settings.json`.
- If sound files are missing or `pygame` is unavailable, the app continues running without audio.
