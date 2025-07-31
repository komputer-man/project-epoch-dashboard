# Epoch Dashboard

A minimal terminal-based monitor that checks TCP ports for configured services and displays their status and last-seen timestamps. State changes are logged in Markdown and trigger desktop notifications.

## Screenshot

<!-- Replace with your screenshot -->
![Dashboard Screenshot](https://raw.githubusercontent.com/komputer-man/project-epoch-dashboard/refs/heads/main/dashboard.png)

## Features

- Periodic port availability checks
- In-place updates of status and last seen time
- Desktop notifications on state changes (macOS, Linux, Windows)
- Markdown log of all state changes

## Requirements

- **Python 3.6+**
- **Windows only**:
  ```bash
  pip install windows-curses win10toast
  ```
- **macOS**:
  - `osascript` (built-in)
  - _Optional_: `terminal-notifier` (`brew install terminal-notifier`)
- **Linux**:
  ```bash
  sudo apt install libnotify-bin
  ```

## Usage

1. Clone or download this repository.
2. Install any Windows requirements if needed.
3. Run the dashboard:
   ```bash
   python epoch_curses_dashboard.py
   ```
4. Press `q` to quit.

## Configuration

Edit the top of `epoch_curses_dashboard.py` to adjust:

```python
INTERVAL = 10    # refresh interval in seconds
TIMEOUT  = 1     # socket timeout in seconds
SERVICES = [
    ("Auth Server", "198.244.165.233", 3724),
    ("Kezan (PvE)", "198.244.165.233", 8085),
    ("Gurubashi (PvP)", "198.244.165.233", 8086),
    ("Cloudflare", "1.1.1.1", 443),
]
```

---

<!-- Add any further notes or links below -->

