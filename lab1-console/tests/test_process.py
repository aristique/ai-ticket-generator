"""Exercise the actual application in its own Linux pseudo-terminal."""
import os
import pty
import select
import subprocess
import sys
import time

from openpyxl import load_workbook


class App:
    def __init__(self, path):
        self.master, slave = pty.openpty()
        env = dict(os.environ, JOURNAL_PATH=str(path), TERM="dumb",
                   PROMPT_TOOLKIT_NO_CPR="1")
        self.process = subprocess.Popen([sys.executable, "-m", "tickets"],
                                        stdin=slave, stdout=slave, stderr=slave,
                                        env=env, start_new_session=True)
        os.close(slave)
        self.buffer = b""

    def wait_for(self, text):
        target = text.encode()
        deadline = time.monotonic() + 5
        while target not in self.buffer:
            if time.monotonic() > deadline:
                raise AssertionError(f"Missing {text!r}: {self.buffer.decode(errors='replace')}")
            if select.select([self.master], [], [], 0.1)[0]:
                try:
                    chunk = os.read(self.master, 8192)
                except OSError:
                    chunk = b""
                if not chunk:
                    raise AssertionError(self.buffer.decode(errors="replace"))
                self.buffer += chunk
        prefix, self.buffer = self.buffer.split(target, 1)
        return prefix

    def send(self, value):
        os.write(self.master, value.encode())

    def student(self, last, first):
        self.wait_for("Last name:")
        self.send(last + "\r")
        self.wait_for("First name:")
        self.send(first + "\r")
        self.wait_for("Запись сохранена.")

    def close(self):
        if self.process.poll() is None:
            self.process.kill()
        self.process.wait(timeout=5)
        os.close(self.master)


def read_rows(path):
    book = load_workbook(path)
    try:
        return list(book.active.values)
    finally:
        book.close()


def test_actual_process_restart_and_escape(tmp_path):
    path = tmp_path / "journal.xlsx"
    app = App(path)
    try:
        for i in range(3):
            app.student(f"Иванов{i}", " Анна ")
        first_rows = read_rows(path)
        assert len(first_rows) == 4
        app.wait_for("Last name:")
        app.send("\x1b")
        assert app.process.wait(timeout=5) == 0
    finally:
        app.close()

    app = App(path)
    try:
        for i in range(2):
            app.student(f"Петров{i}", "Иван")
        app.wait_for("Last name:")
        app.send("Незавершённый\r")
        app.wait_for("First name:")
        app.send("\x1b")
        assert app.process.wait(timeout=5) == 0
    finally:
        app.close()
    final_rows = read_rows(path)
    assert len(final_rows) == 6
    assert final_rows[:4] == first_rows
    assert final_rows[1][1] == "Анна"
    assert all(1 <= row[2] <= 20 for row in final_rows[1:])


def test_actual_process_kill_after_save_keeps_record(tmp_path):
    path = tmp_path / "journal.xlsx"
    app = App(path)
    try:
        app.student("Сохранённый", "Студент")
        app.process.kill()
        app.process.wait(timeout=5)
        assert read_rows(path)[1][:2] == ("Сохранённый", "Студент")
    finally:
        app.close()
