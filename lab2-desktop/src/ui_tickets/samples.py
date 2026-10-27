"""Explicit sample setup; never invoked implicitly by application startup."""
from pathlib import Path
import argparse
from docx import Document
from openpyxl import Workbook


def create(directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    paths = [directory / "students.xlsx", directory / "tickets.docx"]
    if any(p.exists() for p in paths):
        raise FileExistsError("Демонстрационные файлы уже существуют. Они не будут перезаписаны.")
    book = Workbook()
    group = book.active
    group.title = "AI-101"
    group.append(("Фамилия", "Имя"))
    for student in (("Иванова", "Анна"), ("Попеску", "Дан"), ("Петров", "Иван")):
        group.append(student)
    other = book.create_sheet("AI-102")
    other.append(("Фамилия", "Имя"))
    other.append(("Иванова", "Анна"))
    empty = book.create_sheet("Пустая группа")
    empty.append(("Фамилия", "Имя"))
    book.save(paths[0])
    book.close()
    document = Document()
    themes = [
        ("Что такое переменная?", "Как работает условный оператор?", "Для чего нужны функции?"),
        ("Что такое список?", "Как работает цикл?", "Что такое исключение?"),
        ("Для чего нужен Git?", "Что такое unit-тест?", "Как работает кэш?"),
        ("Что такое HTTP?", "Для чего нужен Docker?", "Что такое API?")
    ]
    for number, questions in enumerate(themes, 1):
        document.add_paragraph(f"Билет {number}")
        for question in questions:
            document.add_paragraph(question, style="List Number")
    document.save(paths[1])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", nargs="?", default="/data")
    args = parser.parse_args()
    try:
        create(args.directory)
        print("Созданы students.xlsx и tickets.docx с вымышленными данными.")
    except FileExistsError as exc:
        parser.exit(1, str(exc) + "\n")
