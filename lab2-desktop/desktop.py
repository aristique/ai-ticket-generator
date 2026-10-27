"""Own and supervise the virtual desktop processes; stop all on container exit."""
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

processes = []


def stop(*_args):
    for process in reversed(processes):
        if process.poll() is None:
            process.terminate()
    for process in processes:
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()
    raise SystemExit(0)


signal.signal(signal.SIGTERM, stop)
signal.signal(signal.SIGINT, stop)
os.environ["DISPLAY"] = ":99"
try:
    processes.append(subprocess.Popen(["Xvfb", ":99", "-screen", "0", "1280x800x24", "-nolisten", "tcp"]))
    for _ in range(100):
        if Path("/tmp/.X11-unix/X99").exists():
            break
        if processes[0].poll() is not None:
            raise RuntimeError("Virtual display failed")
        time.sleep(0.05)
    else:
        raise RuntimeError("Virtual display timeout")
    for command in [
        ["openbox"],
        ["x11vnc", "-display", ":99", "-localhost", "-forever", "-shared",
         "-rfbport", "5900", "-nopw", "-quiet"],
        ["websockify", "--web=/usr/share/novnc", "6080", "127.0.0.1:5900"],
        [sys.executable, "-m", "ui_tickets"],
    ]:
        processes.append(subprocess.Popen(command))
    while all(process.poll() is None for process in processes):
        time.sleep(0.5)
finally:
    stop()
