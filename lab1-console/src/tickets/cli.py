"""Interactive Unicode input; ESC exits immediately from either name field."""
import os
from pathlib import Path
import secrets

from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings

from .journal import Entry, Journal, JournalError

BINDINGS = KeyBindings()


@BINDINGS.add("escape", eager=True)
def escape(event):
    event.app.exit(exception=EOFError())


def read_required(session, label):
    while True:
        value = session.prompt(label).strip()
        if value:
            return value
        print("Поле не может быть пустым. Повторите ввод.")


def run(session, journal, random_ticket=None, output=print):
    random_ticket = random_ticket or (lambda: secrets.randbelow(20) + 1)
    output("Для выхода нажмите ESC.")
    try:
        while True:
            last = read_required(session, "Last name: ")
            first = read_required(session, "First name: ")
            entry = Entry.create(last, first, random_ticket())
            while True:
                try:
                    journal.append(entry)
                    break
                except JournalError as exc:
                    output(str(exc))
                    output("Запись пока не сохранена. Закройте файл и нажмите Enter для повтора; ESC — выход.")
                    session.prompt("Повторить сохранение: ")
            output(f"Билет № {entry.ticket}. Запись сохранена.")
    except (EOFError, KeyboardInterrupt):
        output("Работа завершена.")
        return 0


def main():
    session = PromptSession(key_bindings=BINDINGS)
    # Distinguish a lone ESC from an escape sequence without waiting for Enter.
    session.app.ttimeoutlen = 0.1
    path = Path(os.environ.get("JOURNAL_PATH", "journal.xlsx"))
    return run(session, Journal(path))

