import tkinter as tk
from openpyxl import load_workbook

from ui_tickets.gui import App
from ui_tickets.samples import create


def test_gui_selection_persistence_and_escape(tmp_path):
    create(tmp_path)
    root = tk.Tk()
    try:
        app = App(root, tmp_path)
        root.update()
        assert str(app.generate_button["state"]) == "disabled"
        app.group.set("Пустая группа")
        app.select_group()
        assert not app.student["values"]
        assert str(app.generate_button["state"]) == "disabled"
        app.group.set("AI-101")
        app.select_group()
        app.student.current(0)
        app.selection_changed()
        assert str(app.generate_button["state"]) == "normal"
        app.generate()
        root.update()
        result = app.result
        assert result.winfo_exists()
        result.focus_force()
        root.update()
        result.event_generate("<Escape>")
        root.update()
        assert not result.winfo_exists()
        assert root.winfo_exists()
        app.generate()
        root.update()
        book = load_workbook(tmp_path / "results.xlsx")
        entries = list(book.active.values)
        book.close()
        assert len(entries) == 3
        assert entries[1][3] == entries[2][3]
        assert entries[2][5] == "да"
        app.group.set("AI-102")
        app.select_group()
        assert app.student.get() == ""
        assert str(app.generate_button["state"]) == "disabled"
    finally:
        root.destroy()


def test_missing_sources_keep_app_alive(tmp_path):
    root = tk.Tk()
    try:
        app = App(root, tmp_path)
        root.update()
        assert "students.xlsx" in app.status.get()
        assert str(app.generate_button["state"]) == "disabled"
        assert root.winfo_exists()
    finally:
        root.destroy()
