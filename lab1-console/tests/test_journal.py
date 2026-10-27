from pathlib import Path
from unittest.mock import patch

import pytest
from openpyxl import load_workbook

from tickets.journal import Entry, HEADERS, Journal, JournalBusy, JournalError


def rows(path):
    book = load_workbook(path)
    try:
        return list(book.active.values)
    finally:
        book.close()


def test_restart_appends_without_changing_first_three(tmp_path):
    path = tmp_path / "journal.xlsx"
    journal = Journal(path)
    for number in range(1, 4):
        journal.append(Entry.create(f"Студент{number}", "Имя", number))
    previous = rows(path)
    assert previous[0] == HEADERS
    assert len(previous) == 4
    # New instance represents a new application process.
    for number in (4, 5):
        Journal(path).append(Entry.create(f"Студент{number}", "Имя", number))
    assert rows(path)[:4] == previous
    assert len(rows(path)) == 6


@pytest.mark.parametrize("last,first", [("", "A"), (" ", "B"), ("A", ""), ("A", "  ")])
def test_blank_names_are_rejected(last, first):
    with pytest.raises(ValueError):
        Entry.create(last, first, 1)


def test_whitespace_unicode_and_formula_like_name(tmp_path):
    entry = Entry.create("  =Иванов  ", " Анна ", 20)
    path = tmp_path / "journal.xlsx"
    Journal(path).append(entry)
    assert rows(path)[1][:3] == ("=Иванов", "Анна", 20)
    book = load_workbook(path)
    assert book.active["A2"].data_type == "s"
    book.close()


def test_permission_error_preserves_journal_then_retry_succeeds(tmp_path):
    path = tmp_path / "journal.xlsx"
    journal = Journal(path)
    journal.append(Entry.create("Первый", "Студент", 1))
    before = path.read_bytes()
    entry = Entry.create("Второй", "Студент", 2)
    with patch("tickets.journal.os.replace", side_effect=PermissionError):
        with pytest.raises(JournalBusy):
            journal.append(entry)
    assert path.read_bytes() == before
    assert not list(tmp_path.glob("*.tmp"))
    journal.append(entry)
    assert len(rows(path)) == 3


def test_excel_owner_file_is_respected(tmp_path):
    path = tmp_path / "journal.xlsx"
    (tmp_path / "~$journal.xlsx").touch()
    with pytest.raises(JournalBusy):
        Journal(path).append(Entry.create("Иванов", "Иван", 1))
    assert not path.exists()


def test_corrupt_workbook_is_not_overwritten(tmp_path):
    path = tmp_path / "journal.xlsx"
    path.write_bytes(b"not an xlsx")
    with pytest.raises(JournalError):
        Journal(path).append(Entry.create("Иванов", "Иван", 1))
    assert path.read_bytes() == b"not an xlsx"

