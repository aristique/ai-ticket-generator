"""Persistent first-assignment lookup and append-only event history."""
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import os
import secrets
import tempfile

from openpyxl import Workbook, load_workbook

from .sources import Student, Ticket

HEADERS = ("Группа", "Фамилия", "Имя", "Номер билета", "Дата и время", "Повтор")


class JournalError(Exception):
    pass


@dataclass(frozen=True)
class Pending:
    student: Student
    ticket: Ticket
    repeat: bool
    timestamp: str


class Service:
    def __init__(self, path, tickets, chooser=None):
        self.path = Path(path)
        self.tickets = tickets
        self.chooser = chooser or secrets.choice

    def _book(self):
        if not self.path.exists():
            book = Workbook()
            book.active.title = "Results"
            book.active.append(HEADERS)
            book.active.freeze_panes = "A2"
            return book
        try:
            book = load_workbook(self.path)
            if tuple(c.value for c in book.active[1]) != HEADERS:
                book.close()
                raise JournalError("Неверная шапка results.xlsx. Исходные данные не изменены.")
            return book
        except JournalError:
            raise
        except Exception as exc:
            raise JournalError("Не удалось прочитать results.xlsx. Проверьте файл; он не будет перезаписан.") from exc

    def prepare(self, student: Student) -> Pending:
        if not self.tickets:
            raise JournalError("В Word нет корректных билетов.")
        book = self._book()
        try:
            first = next((row[3] for row in book.active.iter_rows(min_row=2, values_only=True)
                          if tuple(row[:3]) == student.key), None)
        finally:
            book.close()
        repeat = first is not None
        if repeat:
            if first not in self.tickets:
                raise JournalError(f"Первый билет студента № {first} отсутствует в Word. Новый билет не назначен.")
            ticket = self.tickets[first]
        else:
            ticket = self.tickets[self.chooser(tuple(self.tickets))]
        return Pending(student, ticket, repeat,
                       datetime.now().astimezone().isoformat(timespec="seconds"))

    def save(self, pending: Pending):
        temporary, book = None, None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            if any(self.path.with_name(name).exists() for name in (
                "~$" + self.path.name, ".~lock." + self.path.name + "#"
            )):
                raise JournalError("Закройте results.xlsx в Excel или LibreOffice и повторите сохранение.")
            book = self._book()
            sheet = book.active
            sheet.append((*pending.student.key, pending.ticket.number, pending.timestamp,
                          "да" if pending.repeat else "нет"))
            for column in (1, 2, 3):
                sheet.cell(sheet.max_row, column).data_type = "s"
            handle, temporary = tempfile.mkstemp(dir=self.path.parent,
                                                 prefix=".results-", suffix=".tmp")
            os.close(handle)
            book.save(temporary)
            with open(temporary, "rb") as stream:
                os.fsync(stream.fileno())
            os.replace(temporary, self.path)
            temporary = None
        except JournalError:
            raise
        except PermissionError as exc:
            raise JournalError("Файл results.xlsx недоступен для записи. Закройте Excel и повторите попытку.") from exc
        except Exception as exc:
            raise JournalError("Не удалось сохранить results.xlsx. Проверьте права и свободное место.") from exc
        finally:
            if book is not None:
                book.close()
            if temporary:
                Path(temporary).unlink(missing_ok=True)
