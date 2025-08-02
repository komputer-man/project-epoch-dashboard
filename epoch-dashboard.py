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
import urllib.request

# ===== Configuration =====
INTERVAL = 10    # seconds until next refresh
TIMEOUT  = 1     # socket timeout in seconds
DEFAULT_LOGFILE = "epoch_dashboard_log.md"
SERVICES = [
    ("Website",        "198.185.159.145",   80),
    ("Registration",   "https://account.project-epoch.net", "REG"),  # SPECIAL!
    ("Auth Server",    "198.244.165.233", 3724),
    ("Kezan (PvE)",    "198.244.165.233", 8085),
    ("Gurubashi (PvP)","198.244.165.233", 8086),
    ("Cloudflare",     "1.1.1.1",         443),
]

def check_service(ip, port):
    """Return True if TCP port is open."""
    try:
        with socket.create_connection((ip, port), timeout=TIMEOUT):
            return True
    except Exception:
        return False

def check_registration_open(url):
    """Checks if registration is open by parsing the website."""
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT) as response:
            html = response.read().decode("utf-8", errors="ignore")
            return "Registration to Project Epoch is not currently enabled" not in html
    except Exception:
        return False

def load_statusfile(logfile):
    """Lädt den letzten Status aus der Logdatei (ohne Kopfzeile, eine Zeile pro Service)."""
    status = {}
    if not os.path.isfile(logfile):
        return status
    with open(logfile, "r") as f:
        for line in f:
            parts = [x.strip() for x in line.strip().split('|')[1:-1]]
            if len(parts) == 4:
                _, service, stat, last = parts
                status[service] = [stat, last]
    return status

def save_statusfile(logfile, status):
    """Speichert alle aktuellen Service-Zeilen in die Logdatei (keine Kopfzeile)."""
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(logfile, "w") as f:
        for name, _, _ in SERVICES:
            stat, last = status.get(name, ("Offline", "N/A"))
            f.write(f"| {now} | {name} | {stat} | {last} |\n")

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
    """Run a single check pass, log all statuses once (ohne Kopfzeile, ersetzt Datei)."""
    prev_status = load_statusfile(logfile)
    status = {}
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    for name, ip, port in SERVICES:
        if port == "REG":
            ok = check_registration_open(ip)
            stat = "Online" if ok else "Offline"
        else:
            ok = check_service(ip, port)
            stat = "Online" if ok else "Offline"
        old_last_seen = prev_status.get(name, ["Offline", "N/A"])[1]
        last_seen = now if stat == "Online" else old_last_seen
        status[name] = [stat, last_seen]
    save_statusfile(logfile, status)

def draw_dashboard(stdscr, logfile):
    curses.curs_set(0)
    stdscr.nodelay(True)
    prev_status = load_statusfile(logfile)
    status = prev_status.copy()
    while True:
        now = time.strftime("%Y-%m-%d %H:%M:%S")
        stdscr.erase()
        height, width = stdscr.getmaxyx()
        title = "📡 EPOCH DASHBOARD"
        stdscr.addstr(0, max(0, (width - len(title)) // 2), title, curses.A_BOLD)
        stdscr.addstr(1, 0, time.strftime("Updated: %a %d %b %Y %H:%M:%S"))
        for idx, (name, ip, port) in enumerate(SERVICES, start=3):
            if port == "REG":
                ok = check_registration_open(ip)
                stat = "Online" if ok else "Offline"
            else:
                ok = check_service(ip, port)
                stat = "Online" if ok else "Offline"
            old_stat = prev_status.get(name, ["Offline", "N/A"])[0]
            old_last = prev_status.get(name, ["Offline", "N/A"])[1]
            last_seen = now if stat == "Online" else old_last
            # State change Notification
            if old_stat != stat:
                notify_change(name, stat)
            status[name] = [stat, last_seen]
            sym = "✔" if ok else "✖"
            col = curses.color_pair(2) if ok else curses.color_pair(1)
            stdscr.addstr(idx, 2, sym + " ", col)
            stdscr.addstr(idx, 4, f"{name} ({ip if port != 'REG' else ''}{'' if port == 'REG' else f':{port}'})")
            label = "Last seen:"
            x = width - len(label) - 1 - len(last_seen)
            stdscr.addstr(idx, x, f"{label} {last_seen}")
        # countdown
        for rem in range(INTERVAL, 0, -1):
            stdscr.addstr(len(SERVICES) + 4, 0, f"Next refresh in {rem:2d}s... Press 'q' to quit.")
            stdscr.refresh()
            time.sleep(1)
            if stdscr.getch() in (ord('q'), ord('Q')):
                save_statusfile(logfile, status)
                return
        prev_status = status.copy()
        save_statusfile(logfile, status)

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
