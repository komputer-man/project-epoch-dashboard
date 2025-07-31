#!/usr/bin/env python3
# epoch_curses_dashboard.py

import curses
import time
import socket
import os
import subprocess
import shutil
import platform

# ===== Configuration =====
INTERVAL = 10    # seconds until next refresh
TIMEOUT  = 1     # socket timeout in seconds
LOGFILE  = "epoch_dashboard_log.md"
SERVICES = [
    ("Auth Server",    "198.244.165.233", 3724),
    ("Kezan (PvE)",    "198.244.165.233", 8085),
    ("Gurubashi (PvP)","198.244.165.233", 8086),
    ("Cloudflare",     "1.1.1.1",         443),
]

# ===== Initialize last-seen timestamps and status =====
last_seen = {name: "N/A" for name, _, _ in SERVICES}
prev_status = {name: None for name, _, _ in SERVICES}

# ===== Initialize log file =====
if not os.path.isfile(LOGFILE):
    with open(LOGFILE, "w") as f:
        f.write("| Time | Service | Status | Last Seen |\n")
        f.write("| ---- | ------- | ------ | --------- |\n")


def check_service(ip, port):
    """Return True if TCP port is open."""
    try:
        with socket.create_connection((ip, port), timeout=TIMEOUT):
            return True
    except Exception:
        return False


def log_status(service, status, last):
    """Append a status line to the markdown log."""
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"| {ts} | {service} | {status} | {last} |\n"
    with open(LOGFILE, "a") as f:
        f.write(line)


def send_notification(message, title="Epoch Dashboard"):
    """Cross-platform notification: macOS, Linux, Windows."""
    system = platform.system()
    if system == "Darwin":
        # macOS: try terminal-notifier, then osascript
        tn = shutil.which("terminal-notifier")
        if tn:
            subprocess.run([tn, "-title", title, "-message", message])
        else:
            script = f'display notification "{message}" with title "{title}"'
            subprocess.run(["osascript", "-e", script])
    elif system == "Linux":
        # Linux: notify-send
        if shutil.which("notify-send"):
            subprocess.run(["notify-send", title, message])
    elif system == "Windows":
        # Windows: win10toast
        try:
            from win10toast import ToastNotifier
        except ImportError:
            return
        toaster = ToastNotifier()
        toaster.show_toast(title, message, duration=5)


def notify_change(service, status):
    """Send a notification about status change."""
    send_notification(f"{service} is now {status}")


def notify_start():
    """Send a notification indicating the dashboard has started."""
    send_notification("Dashboard has started")


def draw_dashboard(stdscr):
    curses.curs_set(0)              # hide cursor
    stdscr.nodelay(True)            # non-blocking getch

    while True:
        stdscr.erase()
        height, width = stdscr.getmaxyx()

        # Header centered
        title = "📡 EPOCH DASHBOARD"
        stdscr.addstr(0, max(0, (width - len(title)) // 2), title, curses.A_BOLD)
        stdscr.addstr(1, 0, time.strftime("Updated: %a %d %b %Y %H:%M:%S"))

        # Services status and last seen
        for idx, (name, ip, port) in enumerate(SERVICES, start=3):
            ok = check_service(ip, port)
            status_text = "Online" if ok else "Offline"

            old_status = prev_status[name]
            if old_status is not None and status_text != old_status:
                if ok:
                    last_seen[name] = time.strftime("%Y-%m-%d %H:%M:%S")
                notify_change(name, status_text)
                log_status(name, status_text, last_seen[name])
            elif old_status is None and ok:
                last_seen[name] = time.strftime("%Y-%m-%d %H:%M:%S")

            prev_status[name] = status_text

            sym = "✔" if ok else "✖"
            color = curses.color_pair(2) if ok else curses.color_pair(1)

            stdscr.addstr(idx, 2, sym + " ", color)
            stdscr.addstr(idx, 4, f"{name} ({ip}:{port})")

            # draw last seen timestamp at right
            last_str = last_seen[name]
            last_label = "Last seen:"
            label_x = width - len(last_label) - 1 - len(last_str)
            stdscr.addstr(idx, label_x, f"{last_label} {last_str}")

        # Countdown
        for rem in range(INTERVAL, 0, -1):
            stdscr.addstr(len(SERVICES) + 4, 0,
                          f"Next refresh in {rem:2d}s...  Press 'q' to quit.")
            stdscr.refresh()
            time.sleep(1)

        if stdscr.getch() in (ord('q'), ord('Q')):
            break


def main(stdscr):
    if curses.has_colors():
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_RED,    -1)
        curses.init_pair(2, curses.COLOR_GREEN,  -1)
    draw_dashboard(stdscr)


if __name__ == "__main__":
    notify_start()
    # Windows requires `pip install windows-curses` and `pip install win10toast`
    curses.wrapper(main)
