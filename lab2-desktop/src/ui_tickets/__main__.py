from pathlib import Path
import logging
import os
import tkinter as tk
from .gui import App

directory = Path(os.environ.get("DATA_DIR", "/data"))
directory.mkdir(parents=True, exist_ok=True)
logging.basicConfig(filename=directory / "application.log", level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s")
root = tk.Tk()
App(root, directory)
root.mainloop()
