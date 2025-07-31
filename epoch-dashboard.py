#!/usr/bin/env python3
# epoch_curses_dashboard.py

import argparse
import curses
import time
import socket
import os
import subprocess
import shutil
import platform
import sys

# ===== Configuration =====
INTERVAL = 10    # seconds until next refresh
TIMEOUT  = 1     # socket timeout in seconds
DEFAULT_LOGFILE = "epoch_dashboard_log.md"
SERVICES = [
    ("Website",        "198.185.159.145",   80),
    ("Auth Server",    "198.244.165.233", 3724),
    ("Kezan (PvE)",    "198.244.165.233", 8085),
    ("Gurubashi (PvP)","198.244.165.233", 8086),
    ("Cloudflare",     "1.1.1.1",         443),
]

# ===== State =====
last_seen = {name: "N/A" for name, _, _ in SERVICES}
prev_status = {name: None for name, _, _ in SERVICES}


def check_service(ip, port):
    """Return True if TCP port is open."""
    try:
        with socket.create_connection((ip, port), timeout=TIMEOUT):
            return True
    except Exception:
        return False


def log_status(service, status, last, logfile):
    """Append a status line to the markdown log."""
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"| {ts} | {service} | {status} | {last} |\n"
    with open(logfile, "a") as f:
        f.write(line)


def send_notification(message, title="Epoch Dashboard"):
    """Cross-platform notification: macOS, Linux, Windows."""
    system = platform.system()
    if system == "Darwin":
        tn = shutil.which("terminal-notifier")
        if tn:
            subprocess.run([tn, "-title", title, "-message", message])
        else:
            script = f'display notification "{message}" with title "{title}"'
            subprocess.run(["osascript", "-e", script])
    elif system == "Linux":
        if shutil.which("notify-send"):
            subprocess.run(["notify-send", title, message])
    elif system == "Windows":
        try:
            from win10toast import ToastNotifier
            toaster = ToastNotifier()
            toaster.show_toast(title, message, duration=5)
        except ImportError:
            pass


def notify_change(service, status):
    send_notification(f"{service} is now {status}")


def notify_start():
    send_notification("Dashboard has started")


def run_once(logfile):
    """Run a single check pass, log all statuses once."""
    new_file = not os.path.isfile(logfile)
    with open(logfile, 'a') as f:
        if new_file:
            f.write("| Time | Service | Status | Last Seen |\n")
            f.write("| ---- | ------- | ------ | --------- |\n")
        for name, ip, port in SERVICES:
            ok = check_service(ip, port)
            status = "Online" if ok else "Offline"
            ts = time.strftime("%Y-%m-%d %H:%M:%S")
            if ok:
                last_seen[name] = ts
            last = last_seen[name]
            f.write(f"| {ts} | {name} | {status} | {last} |\n")
    return


def draw_dashboard(stdscr, logfile):
    curses.curs_set(0)
    stdscr.nodelay(True)
    while True:
        stdscr.erase()
        height, width = stdscr.getmaxyx()
        title = "📡 EPOCH DASHBOARD"
        stdscr.addstr(0, max(0, (width - len(title)) // 2), title, curses.A_BOLD)
        stdscr.addstr(1, 0, time.strftime("Updated: %a %d %b %Y %H:%M:%S"))
        for idx, (name, ip, port) in enumerate(SERVICES, start=3):
            ok = check_service(ip, port)
            status = "Online" if ok else "Offline"
            old = prev_status[name]
            # state change handling
            if old is not None and status != old:
                if ok:
                    last_seen[name] = time.strftime("%Y-%m-%d %H:%M:%S")
                notify_change(name, status)
                log_status(name, status, last_seen[name], logfile)
            elif old is None and ok:
                last_seen[name] = time.strftime("%Y-%m-%d %H:%M:%S")
            prev_status[name] = status
            sym = "✔" if ok else "✖"
            col = curses.color_pair(2) if ok else curses.color_pair(1)
            stdscr.addstr(idx, 2, sym + " ", col)
            stdscr.addstr(idx, 4, f"{name} ({ip}:{port})")
            last = last_seen[name]
            label = "Last seen:"
            x = width - len(label) - 1 - len(last)
            stdscr.addstr(idx, x, f"{label} {last}")
        # countdown
        for rem in range(INTERVAL, 0, -1):
            stdscr.addstr(len(SERVICES) + 4, 0, f"Next refresh in {rem:2d}s... Press 'q' to quit.")
            stdscr.refresh()
            time.sleep(1)
        if stdscr.getch() in (ord('q'), ord('Q')):
            break


def main():
    parser = argparse.ArgumentParser(description="Epoch Dashboard TUI and logger")
    parser.add_argument('--once', action='store_true', help='run one check and exit')
    parser.add_argument('--output', '-o', help='output log file path', default=DEFAULT_LOGFILE)
    args = parser.parse_args()
    if args.once:
        run_once(args.output)
        sys.exit(0)
    notify_start()
    def curses_main(stdscr):
        if curses.has_colors():
            curses.start_color()
            curses.use_default_colors()
            curses.init_pair(1, curses.COLOR_RED, -1)
            curses.init_pair(2, curses.COLOR_GREEN, -1)
        draw_dashboard(stdscr, args.output)
    curses.wrapper(curses_main)

if __name__ == "__main__":
    main()
