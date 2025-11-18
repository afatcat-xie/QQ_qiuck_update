#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# QQ_quick_update_gui.py by afatcat-xie
#
# This script is designed to send random 8-character strings followed by Enter
# into a focused QQ chat window at a specified interval. It supports both
# a graphical user interface (GUI) and a command-line interface (CLI).
#
# Features include:
# - Detection of QQ.exe process.
# - Customizable sending interval and duration.
# - Global hotkeys (Ctrl+Alt+Q to toggle, F8 to stop).
# - Automatic logging of events and errors.
# - Automatic stopping if QQ.exe closes.
# - New: Records and logs the reason for program exit.

import random
import string
import threading
import time as _time
import ctypes
import ctypes.wintypes
import tkinter as tk
from tkinter import ttk, messagebox # Import messagebox for error dialogs
import keyboard
import os
import configparser
import sys
from datetime import datetime
import traceback
import signal # Import signal for CLI mode graceful exit

# ---------- Global variables ----------
running = False
worker_thread = None
time_interval = 1.0          # Default sending interval
qq_exists = False            # Current QQ status
lock = threading.Lock()      # Protect qq_exists read and write
run_duration = None          # Running duration in seconds (None = unlimited)
start_time = None            # Timestamp when worker started

INI_FILE = "qq_quick_update.ini"
LOG_DIR = "logs"
log_fp = None
log_ini = None
log_lock = threading.Lock()

# --- Global hotkey variables ---
TOGGLE_HOTKEY = 'ctrl+alt+q'
STOP_HOTKEY = 'f8'
hotkey_thread = None
gui_window = None # Reference to the main Tkinter window
is_gui_visible = False # Track if GUI is visible

# New global for program exit reason
program_exit_reason = "Program terminated normally." # Default assumed reason for program exit

# ---------- Logging ----------
def _ensure_log_dir():
    """Ensures the log directory exists."""
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

def _open_log_session():
    """Opens a new log file for the current session."""
    global log_fp, log_ini
    session_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_path = os.path.join(LOG_DIR, f"{session_time}.ini")
    try:
        log_fp = open(log_path, "w", encoding="utf-8")
        log_ini = configparser.ConfigParser()
        log_ini.add_section("Log")
        log_ini.set("Log", "session_start", session_time)
        log_ini.set("Log", "entries", "0")
        log_fp.write("# QQ Quick Update Session Log\n")
        log_fp.flush()
    except Exception as e:
        print(f"ERROR: Could not open log file {log_path}: {e}")
        log_fp = None
        log_ini = None


def _log_print(level, msg):
    """Prints a message to console and logs it to the current session file."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {level}: {msg}"
    print(line)  # still to console
    if log_ini and log_fp:
        with log_lock:
            try:
                count = int(log_ini.get("Log", "entries"))
                log_ini.set("Log", f"{count+1}", line)
                log_ini.set("Log", "entries", str(count+1))
                log_fp.write(line + "\n")
                log_fp.flush()
            except Exception:
                pass  # ignore log write errors

def log_info(msg):
    """Logs an informational message."""
    _log_print("INFO", msg)

def log_error(msg):
    """Logs an error message."""
    _log_print("ERROR", msg)

# ---------- INI helper ----------
def load_settings():
    """Loads settings from the INI file."""
    global time_interval, run_duration
    if not os.path.isfile(INI_FILE):
        return
    cfg = configparser.ConfigParser()
    try:
        cfg.read(INI_FILE, encoding="utf-8")
        time_interval = cfg.getfloat("Settings", "interval", fallback=1.0)
        dur = cfg.get("Settings", "duration", fallback="").strip()
        if dur == "":
            run_duration = None
        else:
            run_duration = int(dur) if dur.isdigit() and int(dur) > 0 else None
    except Exception as e:
        log_error(f"Failed to load settings: {e}")

def save_settings():
    """Saves current settings to the INI file."""
    cfg = configparser.ConfigParser()
    cfg["Settings"] = {
        "interval": str(time_interval),
        "duration": str(run_duration) if run_duration is not None else ""
    }
    try:
        with open(INI_FILE, "w", encoding="utf-8") as f:
            cfg.write(f)
        log_info("Settings saved.")
    except Exception as e:
        log_error(f"Failed to save settings: {e}")

# ---------- Win32 detects QQ.exe ----------
TH32CS_SNAPPROCESS = 0x00000002
class PROCESSENTRY32(ctypes.Structure):
    _fields_ = [("dwSize", ctypes.wintypes.DWORD),
                ("cntUsage", ctypes.wintypes.DWORD),
                ("th32ProcessID", ctypes.wintypes.DWORD),
                ("th32DefaultHeapID", ctypes.c_size_t),
                ("th32ModuleID", ctypes.wintypes.DWORD),
                ("cntThreads", ctypes.wintypes.DWORD),
                ("th32ParentProcessID", ctypes.wintypes.DWORD),
                ("pcPriClassBase", ctypes.c_long),
                ("dwFlags", ctypes.wintypes.DWORD),
                ("szExeFile", ctypes.c_char * 260)]

def qq_is_running():
    """Return True if QQ.exe is found in the process snapshot."""
    kernel32 = ctypes.windll.kernel32
    snap = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if snap == -1:
        return False
    entry = PROCESSENTRY32()
    entry.dwSize = ctypes.sizeof(PROCESSENTRY32)
    found = False
    if kernel32.Process32First(snap, ctypes.byref(entry)):
        while True:
            try:
                exe_name = entry.szExeFile.decode('utf-8', errors='ignore')
                if exe_name.lower() == "qq.exe":
                    found = True
                    break
            except Exception:
                pass
            if not kernel32.Process32Next(snap, ctypes.byref(entry)):
                break
    kernel32.CloseHandle(snap)
    return found

# ---------- Background monitoring thread ----------
def monitor_qq():
    """Monitors the presence of QQ.exe and updates GUI."""
    global qq_exists
    while True:
        try:
            current = qq_is_running()
            with lock:
                changed = current != qq_exists
                qq_exists = current
            if changed:
                log_msg = "QQ.exe is now RUNNING." if current else "QQ.exe is NOT running."
                log_info(log_msg)
                # Use root.after to update GUI elements from main thread
                if gui_window:
                    gui_window.after(0, update_buttons, current)
                if not current:                     # QQ just disappeared
                    gui_window.after(0, auto_stop_if_needed)
        except Exception as e:
            log_error(f"Monitor thread error: {e}")
            if gui_window:
                # Schedule stop_script with an error reason if GUI exists
                gui_window.after(0, stop_script_with_reason, f"QQ monitoring thread encountered an error: {e}")
        _time.sleep(1)

def auto_stop_if_needed():
    """If QQ disappears while the script is running, stop it automatically."""
    global running
    if running:
        log_info("QQ.exe lost, stopping script automatically.")
        stop_script_with_reason("QQ process lost, script stopped automatically")

def update_buttons(qq_running):
    """Called in main thread to enable/disable Start button."""
    if qq_running:
        start_btn.config(state='normal')
    else:
        start_btn.config(state='disabled')

# ---------- Basic logic ----------
def random_8():
    """Generates a random 8-character string."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

def worker():
    """The main worker thread that sends random strings."""
    global running, start_time
    start_time = _time.time()
    try:
        while running:
            # --- Check for F8 hotkey to stop ---
            # Note: keyboard.is_pressed can be resource intensive if called too frequently.
            # For this simple script, it's usually acceptable.
            if keyboard.is_pressed(STOP_HOTKEY):
                log_info(f"{STOP_HOTKEY} hotkey pressed, stopping script.")
                # Use root.after for safe stopping from background thread
                if gui_window:
                    gui_window.after(0, stop_script_with_reason, f"Worker thread stopped by hotkey '{STOP_HOTKEY}'")
                break
            # --- End check ---

            keyboard.write(random_8())
            keyboard.send('enter')
            _time.sleep(time_interval)
            # Check duration
            if run_duration is not None:
                elapsed = _time.time() - start_time
                if elapsed >= run_duration:
                    log_info("Duration reached, stopping automatically.")
                    if gui_window:
                        gui_window.after(0, stop_script_with_reason, "Worker thread stopped due to reaching preset duration")
                    break
    except Exception as e:
        log_error(f"Worker thread error: {e}")
        if gui_window:
            gui_window.after(0, stop_script_with_reason, f"Worker thread encountered an error: {e}")

def start_script():
    """Starts the script's main functionality."""
    global running, worker_thread, time_interval, run_duration, start_time
    if running:
        return
    try:
        time_interval = float(interval_entry.get())
    except ValueError:
        time_interval = 1.0

    # Parse duration
    dur_str = duration_entry.get().strip()
    if not dur_str:
        run_duration = None
    else:
        try:
            run_duration = int(dur_str)
            if run_duration <= 0:
                run_duration = None
        except ValueError:
            run_duration = None

    save_settings()  # Save on start
    running = True
    worker_thread = threading.Thread(target=worker, daemon=True)
    worker_thread.start()
    status_label.config(text="Status: Running")
    log_info("Script started.")
    # Ensure GUI window is visible if it was hidden
    if gui_window:
        gui_window.deiconify() # Show the window if it was minimized/hidden
        gui_window.lift() # Bring to front

def stop_script():
    """Stops the worker script without a specific reason, used internally by other stop functions."""
    global running
    if not running:
        return
    running = False
    if worker_thread and worker_thread.is_alive():
        pass # Daemon threads will be terminated when the main thread exits.
    status_label.config(text="Status: Stopped")
    log_info("Script stopped.")

def stop_script_with_reason(reason="Unknown reason"):
    """Stops the script and logs a specific reason."""
    global running
    if not running:
        return
    running = False
    if worker_thread and worker_thread.is_alive():
        pass
    status_label.config(text="Status: Stopped")
    log_info(f"Script stopped. Reason: {reason}")


# ---------- Hotkey handling ----------
def toggle_script():
    """Handles the toggle hotkey (Ctrl+Alt+Q)."""
    global running, gui_window, is_gui_visible

    if running:
        # If running, stop the script
        log_info("Toggle hotkey pressed: Stopping script.")
        stop_script_with_reason(f"Toggle hotkey '{TOGGLE_HOTKEY}' triggered stop")
    else:
        # If not running, try to start it
        log_info("Toggle hotkey pressed: Attempting to start script.")
        # Check if QQ is running before starting
        if qq_is_running():
            start_script()
        else:
            log_info("QQ.exe not detected, cannot start script yet. Please start QQ.")
            # Optionally, show the GUI window if it's hidden, so the user can see the message
            if gui_window and not is_gui_visible:
                gui_window.deiconify()
                gui_window.lift()


def on_hotkey_press(hotkey_name):
    """Callback for hotkey events. hotkey_name is the string representation of the hotkey."""
    log_info(f"Hotkey '{hotkey_name}' pressed.")
    if hotkey_name == TOGGLE_HOTKEY:
        # Use root.after to call GUI-related functions from the main thread
        if gui_window:
            gui_window.after(0, toggle_script)
        else: # CLI mode, directly toggle
            toggle_script()
    elif hotkey_name == STOP_HOTKEY:
        if gui_window:
            gui_window.after(0, stop_script_with_reason, f"Hotkey '{STOP_HOTKEY}' triggered stop")
        else: # CLI mode, directly stop
            stop_script_with_reason(f"Hotkey '{STOP_HOTKEY}' triggered stop")


def run_hotkey_listener():
    """Thread function to listen for hotkeys."""
    global hotkey_thread
    try:
        # Clear any previous hotkeys to ensure only ours are active
        keyboard.unhook_all()
        # Pass the hotkey name string as the argument to on_hotkey_press
        keyboard.add_hotkey(TOGGLE_HOTKEY, on_hotkey_press, args=(TOGGLE_HOTKEY,))
        keyboard.add_hotkey(STOP_HOTKEY, on_hotkey_press, args=(STOP_HOTKEY,))
        log_info(f"Hotkey listener started for '{TOGGLE_HOTKEY}' and '{STOP_HOTKEY}'.")
        # Keep the listener alive. keyboard.wait() blocks until all hotkeys are unhooked.
        keyboard.wait()
        log_info("Hotkey listener finished.")
    except Exception as e:
        log_error(f"Hotkey listener failed: {e}")
        # Attempt to update status label in GUI thread if listener fails
        if gui_window:
            gui_window.after(0, lambda: status_label.config(text="Status: Hotkey Error"))

def show_gui():
    """Shows the Tkinter GUI window."""
    global gui_window, is_gui_visible
    if gui_window:
        gui_window.deiconify()
        gui_window.lift()
        gui_window.attributes('-topmost', True) # Temporarily bring to front
        gui_window.attributes('-topmost', False) # Release
        is_gui_visible = True
        log_info("GUI window shown.")

def hide_gui():
    """Hides the Tkinter GUI window."""
    global gui_window, is_gui_visible
    if gui_window:
        gui_window.withdraw() # Hide the window
        is_gui_visible = False
        log_info("GUI window hidden.")

def perform_cleanup(reason=None):
    """
    Performs all necessary cleanup actions before the program exits.
    Logs the final exit reason.
    """
    global running, program_exit_reason, log_fp, log_ini, gui_window

    if reason:
        program_exit_reason = reason # Update the global exit reason

    # Stop the script if it's still running
    if running:
        stop_script_with_reason("Script automatically stopped before program exit") # This logs script stopped message

    # Log the final program exit reason
    log_info(f"Program final exit reason: {program_exit_reason}")

    # Unhook hotkeys
    try:
        keyboard.unhook_all()
        log_info("All hotkeys unhooked.")
    except Exception as e:
        log_error(f"Failed to unhook hotkeys: {e}")

    # Close log file
    if log_fp:
        with log_lock:
            try:
                log_fp.close()
                # log_info("Log file closed.") # This message won't go to file, but to console
            except Exception as e:
                print(f"ERROR: Could not properly close log file: {e}")
        log_fp = None
        log_ini = None

    # Destroy GUI window if it exists and hasn't been destroyed yet
    if gui_window and gui_window.winfo_exists():
        gui_window.destroy()
        log_info("GUI window destroyed.")

    running = False # Ensure running flag is false

def on_closing():
    """Handles the GUI window close event."""
    log_info("Window closing event triggered.")
    perform_cleanup("GUI window closed by user")
    # root.mainloop() will naturally exit after gui_window.destroy()

def excepthook(exc_type, exc_value, exc_tb):
    """Custom exception hook for logging unhandled exceptions and performing cleanup."""
    global gui_window
    log_error("--- Unhandled Exception ---")
    error_details = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    log_error(error_details)
    log_error("-------------------------")

    reason = f"Program exited due to an unhandled exception: {exc_type.__name__}: {exc_value}"

    # Perform cleanup. If GUI exists, schedule on main thread.
    if gui_window and gui_window.winfo_exists():
        # Display an error message box for GUI users
        try:
            messagebox.showerror("Unhandled Exception", f"An unhandled error occurred:\n\n{exc_value}\n\nSee logs for details.")
        except Exception as msgbox_e:
            log_error(f"Failed to show error messagebox: {msgbox_e}")
        gui_window.after(0, perform_cleanup, reason)
        # Allow Tkinter mainloop to finish naturally after cleanup
    else:
        # CLI mode or early error before GUI init
        perform_cleanup(reason)
        sys.exit(1) # Explicitly exit for CLI or non-GUI related errors

sys.excepthook = excepthook

def _cli_main():
    """Pure command-line entrypoint"""
    import argparse

    parser = argparse.ArgumentParser(description="QQ Quick Update – CLI mode")
    parser.add_argument("--cli", action="store_true", help="Enter command-line mode")
    parser.add_argument("-i", "--interval", type=float, default=1.0,
                        help="Sending interval (seconds, default 1.0)")
    parser.add_argument("-d", "--duration", type=int, default=None,
                        help="Running duration (seconds, leave blank for unlimited)")
    args = parser.parse_args()

    if not args.cli:          # If --cli is not present, enter GUI mode
        return False

    # Below is all CLI logic
    # Handle Ctrl+C gracefully for CLI mode
    def signal_handler(sig, frame):
        global running, program_exit_reason
        log_info("Ctrl+C caught, initiating shutdown.")
        running = False # Set global 'running' flag to False
        program_exit_reason = "CLI mode interrupted by user (Ctrl+C)" # Set exit reason

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


    _ensure_log_dir()
    _open_log_session()
    log_info("Program started in CLI mode.")

    global running, time_interval, run_duration, start_time, program_exit_reason
    time_interval = args.interval
    run_duration = args.duration
    start_time = _time.time()
    running = True
    program_exit_reason = "CLI mode completed and exited normally." # Default CLI exit reason

    # Wait for QQ
    while running and not qq_is_running():
        log_info("QQ.exe not found, waiting \u2026")
        _time.sleep(2)
    if not running: # If Ctrl+C was pressed while waiting for QQ
        perform_cleanup(program_exit_reason) # Use the reason set by signal_handler
        return True # Exit CLI mode

    log_info("QQ.exe detected, starting work.")

    # Start hotkey listener in a separate thread for CLI mode as well
    # It was already started at the top level, but ensure it's running.
    # If hotkey_thread is not alive for some reason, restart.
    global hotkey_thread
    if not hotkey_thread or not hotkey_thread.is_alive():
        hotkey_thread = threading.Thread(target=run_hotkey_listener, daemon=True)
        hotkey_thread.start()


    try:
        while running:
            # Check for F8 hotkey to stop (hotkey_listener handles this, but direct check for quick exit)
            # This check is somewhat redundant if hotkey_listener calls stop_script_with_reason,
            # but serves as a quick exit point for the loop.
            if keyboard.is_pressed(STOP_HOTKEY):
                log_info(f"{STOP_HOTKEY} hotkey pressed, exiting CLI mode.")
                program_exit_reason = f"CLI mode stopped by hotkey '{STOP_HOTKEY}'"
                break

            if not qq_is_running():
                log_info("QQ.exe lost, pausing until it returns \u2026")
                while running and not qq_is_running():
                    _time.sleep(1)
                if not running: # If Ctrl+C was pressed during the wait
                    # program_exit_reason would have been set by signal_handler
                    break
                log_info("QQ.exe re-detected.")

            keyboard.write(random_8())
            keyboard.send('enter')
            _time.sleep(time_interval)

            if run_duration is not None and (_time.time() - start_time) >= run_duration:
                log_info("Duration reached, exiting CLI mode.")
                program_exit_reason = "CLI mode stopped due to reaching preset duration"
                break
    except Exception as e:
        log_error(f"An error occurred during CLI operation: {e}")
        program_exit_reason = f"An error occurred during CLI operation: {e}"
    finally:
        perform_cleanup(program_exit_reason) # Ensure cleanup is done with the final reason
    return True # Indicate that CLI mode handled the program execution

# -------- Actual entrypoint --------
if __name__ == "__main__":
    # --- ASCII Art Welcome Message ---
    # This is a decorative welcome message displayed in the console.
    ascii_art = [
        "     _      _____      _      _____    ____      _      _____ ",
        "    / \    |  ___|    / \    |_   _|  / ___|    / \    |_   _|",
        "   / _ \   | |_      / _ \     | |   | |       / _ \     | |  ",
        "  / ___ \  |  _|    / ___ \    | |   | |___   / ___ \    | |  ",
        " /_/   \_\ |_|     /_/   \_\   |_|    \____| /_/   \_\   |_|  ",
        "                                                              ",
        "https://github.com/afatcat-xie/QQ_qiuck_update",
        "------------------------------------------------",
        "",
    ]
    for line in ascii_art:
        print(line)
    # --- End of ASCII Art ---

    # Start hotkey listener in a separate thread early on.
    # This allows it to capture hotkeys even if CLI mode is not explicitly chosen
    # or if GUI is hidden. This thread is daemon, so it will exit with the main program.
    hotkey_thread = threading.Thread(target=run_hotkey_listener, daemon=True)
    hotkey_thread.start()

    try:
        # Check if CLI mode was requested. If _cli_main returns True, it handled the exit.
        if _cli_main():
            sys.exit(0)

        # Otherwise, proceed to GUI initialization
        _ensure_log_dir()
        _open_log_session()
        log_info("Program started in GUI mode.")

        # --- Tkinter GUI Setup ---
        root = tk.Tk()
        gui_window = root # Assign to global variable for other functions to use
        root.title("QQ Quick Update – by afatcat-xie")
        # root.resizable(False, False) # Keep resizable for potential future improvements

        load_settings()

        ttk.Label(root, text="Interval (seconds)").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        interval_entry = ttk.Entry(root, width=6)
        interval_entry.insert(0, str(time_interval))
        interval_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(root, text="Duration (seconds, leave blank for unlimited)").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        duration_entry = ttk.Entry(root, width=10)
        duration_entry.insert(0, str(run_duration) if run_duration is not None else "")
        duration_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        start_btn = ttk.Button(root, text="Start", width=10, command=start_script, state='disabled')
        start_btn.grid(row=2, column=0, padx=10, pady=10)
        stop_btn = ttk.Button(root, text="Stop", width=10, command=lambda: stop_script_with_reason("GUI Stop button triggered stop"))
        stop_btn.grid(row=2, column=1, padx=10, pady=10)

        status_label = tk.Label(root, text="Status: Stopped", fg="blue")
        status_label.grid(row=3, column=0, columnspan=2, pady=5)

        # Updated Tip message to include hotkey info
        tk.Label(root, text=f"Tip: Focus QQ chat box. Use '{TOGGLE_HOTKEY.replace('+', ' + ')}' to toggle Start/Stop, '{STOP_HOTKEY}' to stop.", font=(None, 9)) \
            .grid(row=4, column=0, columnspan=2, padx=10, pady=5)

        # Start QQ monitoring thread
        threading.Thread(target=monitor_qq, daemon=True).start()

        # Set the closing protocol for the GUI window
        root.protocol("WM_DELETE_WINDOW", on_closing)

        log_info("GUI initialized.")
        root.mainloop() # Start the Tkinter event loop
        # When root.mainloop() finishes (e.g., after on_closing calls gui_window.destroy()),
        # the code continues here. Perform final cleanup if not already done.
        # on_closing already calls perform_cleanup, so this check avoids redundant calls.
        if log_fp: # If log_fp is still open, it means cleanup wasn't handled by on_closing
            perform_cleanup("GUI mode exited naturally")

    except Exception as e:
        # Catch exceptions that occur *before* or *outside* _cli_main or root.mainloop
        # excepthook should generally catch these, but this is a fail-safe.
        log_error(f"Unhandled error in main program block: {e}")
        perform_cleanup(f"Unhandled error in main program block: {e}")
        sys.exit(1) # Ensure exit for unexpected errors
