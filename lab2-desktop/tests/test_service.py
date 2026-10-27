from unittest.mock import patch
from openpyxl import load_workbook
import pytest

from ui_tickets.sources import Student, Ticket
from ui_tickets.service import HEADERS, JournalError, Service

TICKETS = {1: Ticket(1, ("A", "B", "C")), 7: Ticket(7, ("D", "E", "F"))}
STUDENT = Student("AI-101", "Иванова", "Анна")


def rows(path):
    book = load_workbook(path)
    try:
        return list(book.active.values)
    finally:
        book.close()


def test_first_ticket_and_append_only_repeat_history_survive_restart(tmp_path):
    path = tmp_path / "results.xlsx"
    service = Service(path, TICKETS, chooser=lambda _: 7)
    first = service.prepare(STUDENT)
    service.save(first)
    original = rows(path)
    assert original[0] == HEADERS
    assert original[1][3] == 7 and original[1][5] == "нет"
    for _ in range(2):
        service = Service(path, TICKETS, chooser=lambda _: 1)
        pending = service.prepare(STUDENT)
        assert pending.ticket.number == 7
        service.save(pending)
    final = rows(path)
    assert final[:2] == original
    assert len(final) == 4
    assert all(row[5] == "да" for row in final[2:])


def test_group_is_part_of_identity(tmp_path):
    path = tmp_path / "results.xlsx"
    service = Service(path, TICKETS, chooser=lambda _: 1)
    service.save(service.prepare(STUDENT))
    other = Student("AI-102", STUDENT.last, STUDENT.first)
    service.chooser = lambda _: 7
    pending = service.prepare(other)
    assert pending.ticket.number == 7
    assert not pending.repeat


def test_first_not_latest_journal_row_wins(tmp_path):
    path = tmp_path / "results.xlsx"
    service = Service(path, TICKETS, chooser=lambda _: 7)
    service.save(service.prepare(STUDENT))
    book = load_workbook(path)
    book.active.append((*STUDENT.key, 1, "later", "да"))
    book.save(path)
    book.close()
    assert service.prepare(STUDENT).ticket.number == 7


def test_save_failure_retry_does_not_redraw_or_duplicate(tmp_path):
    path = tmp_path / "results.xlsx"
    service = Service(path, TICKETS, chooser=lambda _: 7)
    pending = service.prepare(STUDENT)
    with patch("ui_tickets.service.os.replace", side_effect=PermissionError):
        with pytest.raises(JournalError):
            service.save(pending)
    assert not path.exists()
    assert not list(tmp_path.glob("*.tmp"))
    service.save(pending)
    assert len(rows(path)) == 2
    assert rows(path)[1][3] == 7


def test_removed_original_ticket_is_not_reassigned(tmp_path):
    path = tmp_path / "results.xlsx"
    service = Service(path, TICKETS, chooser=lambda _: 7)
    service.save(service.prepare(STUDENT))
    with pytest.raises(JournalError, match="отсутствует"):
        Service(path, {1: TICKETS[1]}).prepare(STUDENT)


def test_corrupt_journal_is_not_overwritten(tmp_path):
    path = tmp_path / "results.xlsx"
    path.write_bytes(b"broken")
    with pytest.raises(JournalError):
        Service(path, TICKETS).prepare(STUDENT)
    assert path.read_bytes() == b"broken"


def test_no_valid_tickets(tmp_path):
    with pytest.raises(JournalError, match="нет корректных"):
        Service(tmp_path / "results.xlsx", {}).prepare(STUDENT)
