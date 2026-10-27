from docx import Document
import pytest
from ui_tickets.samples import create
from ui_tickets.sources import SourceError, load_students, load_tickets


def test_groups_and_empty_group(tmp_path):
    create(tmp_path)
    groups = load_students(tmp_path / "students.xlsx")
    assert set(groups) == {"AI-101", "AI-102", "Пустая группа"}
    assert len(groups["AI-101"]) == 3
    assert groups["Пустая группа"] == []
    assert groups["AI-102"][0].group == "AI-102"


def test_native_word_numbering(tmp_path):
    create(tmp_path)
    tickets = load_tickets(tmp_path / "tickets.docx")
    assert len(tickets) == 4
    assert tickets[1].questions[0] == "Что такое переменная?"


def test_malformed_and_noncontiguous_tickets(tmp_path, caplog):
    doc = Document()
    for heading, questions in [
        ("Билет 1", ["1. Один", "2. Два"]),
        ("Билет x", ["1. Не билет", "2. Не билет", "3. Не билет"]),
        ("Билет 7", ["1. A", "2. B", "3. C"]),
    ]:
        doc.add_paragraph(heading)
        for question in questions:
            doc.add_paragraph(question)
    path = tmp_path / "tickets.docx"
    doc.save(path)
    assert set(load_tickets(path)) == {7}
    assert "fewer than 3" in caplog.text
    assert "Unrecognized ticket" in caplog.text


def test_duplicate_ids_are_not_ambiguous(tmp_path):
    doc = Document()
    for _ in range(2):
        doc.add_paragraph("Билет 1")
        for q in ("1. A", "2. B", "3. C"):
            doc.add_paragraph(q)
    path = tmp_path / "tickets.docx"
    doc.save(path)
    assert load_tickets(path) == {}


@pytest.mark.parametrize("loader,name", [(load_students, "students.xlsx"), (load_tickets, "tickets.docx")])
def test_missing_sources_are_readable_errors(tmp_path, loader, name):
    with pytest.raises(SourceError, match=name):
        loader(tmp_path / name)


def test_demo_setup_never_overwrites(tmp_path):
    create(tmp_path)
    before = (tmp_path / "students.xlsx").read_bytes()
    with pytest.raises(FileExistsError):
        create(tmp_path)
    assert (tmp_path / "students.xlsx").read_bytes() == before
