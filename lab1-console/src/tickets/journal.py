"""Append-only Excel journal with safe replacement after every student."""
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import os
import tempfile

from openpyxl import Workbook, load_workbook
from openpyxl.utils.exceptions import InvalidFileException

HEADERS = ("Last name", "First name", "Номер билета", "Дата и время")


class JournalError(Exception):
    """A recoverable journal error suitable for displaying to the user."""


class JournalBusy(JournalError):
    pass


@dataclass(frozen=True)
class Entry:
    last_name: str
    first_name: str
    ticket: int
    timestamp: str

    @classmethod
    def create(cls, last_name: str, first_name: str, ticket: int):
        last_name, first_name = last_name.strip(), first_name.strip()
        if not last_name or not first_name:
            raise ValueError("Фамилия и имя не могут быть пустыми.")
        if not 1 <= ticket <= 20:
            raise ValueError("Номер билета должен быть от 1 до 20.")
        return cls(last_name, first_name, ticket,
                   datetime.now().astimezone().isoformat(timespec="seconds"))


class Journal:
    def __init__(self, path: Path):
        self.path = Path(path)

    def append(self, entry: Entry) -> None:
        path = self.path
        temporary = None
        workbook = None
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            # Excel's owner file is visible when the whole data directory is mounted.
            # File-system PermissionError remains the final authority on real locks.
            locks = (path.with_name("~$" + path.name),
                     path.with_name(".~lock." + path.name + "#"))
            if any(lock.exists() for lock in locks):
                raise JournalBusy("Журнал открыт в Excel или LibreOffice. Закройте файл.")
            if path.exists():
                workbook = load_workbook(path)
                sheet = workbook.active
                if tuple(c.value for c in sheet[1]) != HEADERS:
                    raise JournalError("Неверная шапка журнала. Проверьте файл; данные не изменены.")
            else:
                workbook = Workbook()
                sheet = workbook.active
                sheet.title = "Journal"
                sheet.append(HEADERS)
                sheet.freeze_panes = "A2"
            sheet.append((entry.last_name, entry.first_name, entry.ticket, entry.timestamp))
            # A name beginning with '=' is text, not a spreadsheet formula.
            for column in (1, 2):
                sheet.cell(sheet.max_row, column).data_type = "s"
            handle, temporary = tempfile.mkstemp(prefix=".journal-", suffix=".tmp",
                                                 dir=path.parent)
            os.close(handle)
            workbook.save(temporary)
            with open(temporary, "rb") as stream:
                os.fsync(stream.fileno())
            os.replace(temporary, path)
            temporary = None
        except PermissionError as exc:
            raise JournalBusy("Журнал недоступен для записи. Закройте Excel и проверьте права на папку.") from exc
        except JournalError:
            raise
        except (OSError, InvalidFileException, ValueError, KeyError) as exc:
            raise JournalError("Не удалось сохранить журнал. Проверьте файл, права и свободное место.") from exc
        except Exception as exc:
            # Includes a corrupt ZIP/XLSX. Never replace unreadable original data.
            raise JournalError("Не удалось прочитать или сохранить Excel-журнал. Исходный файл сохранён.") from exc
        finally:
            if workbook is not None:
                workbook.close()
            if temporary is not None:
                Path(temporary).unlink(missing_ok=True)
