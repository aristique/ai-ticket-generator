"""Read genuine XLSX and DOCX sources, including native Word numbering."""
from dataclasses import dataclass
from pathlib import Path
import logging
import re

from docx import Document
from openpyxl import load_workbook

LOG = logging.getLogger(__name__)


class SourceError(Exception):
    pass


@dataclass(frozen=True)
class Student:
    group: str
    last: str
    first: str

    @property
    def label(self):
        return f"{self.last} {self.first}"

    @property
    def key(self):
        return self.group, self.last, self.first


@dataclass(frozen=True)
class Ticket:
    number: int
    questions: tuple[str, str, str]


def load_students(path: Path) -> dict[str, list[Student]]:
    book = None
    try:
        book = load_workbook(path, read_only=True, data_only=True)
        groups = {}
        for sheet in book:
            students = []
            seen = set()
            for last, first, *_ in sheet.iter_rows(min_row=2, min_col=1, max_col=2,
                                                   values_only=True):
                last, first = str(last or "").strip(), str(first or "").strip()
                if not last or not first:
                    if last or first:
                        LOG.warning("Incomplete student in group %s", sheet.title)
                    continue
                student = Student(sheet.title, last, first)
                if student.key not in seen:
                    students.append(student)
                    seen.add(student.key)
            groups[sheet.title] = students
        return groups
    except Exception as exc:
        raise SourceError(f"Не удалось открыть список студентов: {path.name}. Проверьте файл Excel.") from exc
    finally:
        if book is not None:
            book.close()


def native_numbering(paragraph):
    element = paragraph._p
    if element.pPr is not None and element.pPr.numPr is not None:
        return True
    style = paragraph.style
    visited = set()
    while style is not None and style.style_id not in visited:
        visited.add(style.style_id)
        if "number" in style.name.lower() or "номер" in style.name.lower():
            return True
        if style.element.pPr is not None and style.element.pPr.numPr is not None:
            return True
        style = style.base_style
    return False


def load_tickets(path: Path) -> dict[int, Ticket]:
    try:
        document = Document(path)
    except Exception as exc:
        raise SourceError(f"Не удалось открыть билеты: {path.name}. Проверьте файл Word.") from exc
    result, duplicates = {}, set()
    current, questions = None, []

    def finish():
        if current is None:
            return
        if current in result or current in duplicates:
            result.pop(current, None)
            duplicates.add(current)
            LOG.error("Duplicate ticket ID %s skipped", current)
        elif len(questions) < 3:
            LOG.error("Ticket %s has fewer than 3 questions and was skipped", current)
        else:
            result[current] = Ticket(current, tuple(questions[:3]))

    for paragraph in document.paragraphs:
        text = paragraph.text.strip()
        if not text:
            continue
        heading = re.fullmatch(r"Билет\s+(\d+)", text, re.IGNORECASE)
        if heading:
            finish()
            current, questions = int(heading[1]), []
            if current < 1:
                LOG.error("Invalid ticket heading: %s", text)
                current = None
            continue
        style_name = paragraph.style.name.lower()
        if text.lower().startswith("билет") or style_name.startswith("heading"):
            finish()
            current, questions = None, []
            LOG.error("Unrecognized ticket heading: %s", text)
            continue
        if current is None:
            LOG.warning("Paragraph outside a recognized ticket skipped: %s", text)
            continue
        question = re.match(r"^\d+[.)]\s+(.+)$", text)
        if question:
            questions.append(question[1].strip())
        elif native_numbering(paragraph):
            questions.append(text)
        else:
            finish()
            LOG.error("Unrecognized heading or unnumbered paragraph: %s", text)
            current, questions = None, []
    finish()
    return result
