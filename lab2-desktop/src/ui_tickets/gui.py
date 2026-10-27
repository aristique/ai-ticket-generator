from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox

from .sources import SourceError, load_students, load_tickets
from .service import Service, JournalError


class App:
    def __init__(self, root, directory):
        self.root, self.directory = root, Path(directory)
        self.groups, self.tickets = {}, {}
        self.result = None
        root.title("Экзаменационные билеты · Лабораторная №2")
        root.geometry("820x620")
        root.minsize(660, 500)
        root.configure(bg="#f2f5f9")
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#f2f5f9")
        style.configure("TLabel", background="#f2f5f9", foreground="#1b2540",
                        font=("DejaVu Sans", 11))
        style.configure("Title.TLabel", font=("DejaVu Sans", 24, "bold"))
        style.configure("Caption.TLabel", foreground="#59687d", font=("DejaVu Sans", 10))
        style.configure("TButton", font=("DejaVu Sans", 11), padding=(16, 12))
        style.configure("TCombobox", padding=8, font=("DejaVu Sans", 11))
        frame = ttk.Frame(root, padding=36)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="ЭКЗАМЕН · ВЫБОР БИЛЕТА", style="Caption.TLabel").pack(anchor="w")
        ttk.Label(frame, text="Ваш следующий билет", style="Title.TLabel").pack(anchor="w", pady=(12, 8))
        ttk.Label(frame, text="Выберите группу и студента. Результат сохранится в журнале.",
                  wraplength=680).pack(anchor="w", pady=(0, 30))
        ttk.Label(frame, text="Группа").pack(anchor="w", pady=(0, 7))
        self.group = ttk.Combobox(frame, state="readonly")
        self.group.pack(fill="x")
        self.group.bind("<<ComboboxSelected>>", self.select_group)
        ttk.Label(frame, text="Студент").pack(anchor="w", pady=(24, 7))
        self.student = ttk.Combobox(frame, state="readonly")
        self.student.pack(fill="x")
        self.student.bind("<<ComboboxSelected>>", self.selection_changed)
        self.generate_button = ttk.Button(frame, text="Сгенерировать билет",
                                          command=self.generate, state="disabled")
        self.generate_button.pack(fill="x", pady=(28, 14))
        self.status = tk.StringVar()
        ttk.Label(frame, textvariable=self.status, style="Caption.TLabel",
                  wraplength=680).pack(anchor="w", pady=(0, 16))
        ttk.Button(frame, text="Перечитать входные файлы", command=self.reload).pack(anchor="w")
        self.reload()

    def reload(self):
        self.group.set("")
        self.student.set("")
        self.student.configure(values=())
        self.generate_button.configure(state="disabled")
        try:
            self.groups = load_students(self.directory / "students.xlsx")
            self.tickets = load_tickets(self.directory / "tickets.docx")
            self.group.configure(values=tuple(self.groups))
            self.service = Service(self.directory / "results.xlsx", self.tickets)
            self.status.set(f"Групп: {len(self.groups)} · Корректных билетов: {len(self.tickets)}")
            if not self.tickets:
                self.status.set("В Word нет корректных билетов. Проверьте tickets.docx и application.log.")
        except SourceError as exc:
            self.groups, self.tickets = {}, {}
            self.group.configure(values=())
            self.status.set(str(exc))

    def select_group(self, _event=None):
        self.student.set("")
        students = self.groups.get(self.group.get(), [])
        self.student.configure(values=tuple(s.label for s in students))
        self.selection_changed()
        if not students:
            self.status.set("В выбранной группе нет студентов.")

    def selection_changed(self, _event=None):
        group = self.group.get()
        index = self.student.current()
        valid = group in self.groups and 0 <= index < len(self.groups[group]) and bool(self.tickets)
        self.generate_button.configure(state="normal" if valid else "disabled")

    def generate(self):
        group, index = self.group.get(), self.student.current()
        if group not in self.groups or index < 0 or index >= len(self.groups[group]):
            return
        try:
            pending = self.service.prepare(self.groups[group][index])
        except JournalError as exc:
            messagebox.showerror("Не удалось назначить билет", str(exc), parent=self.root)
            return
        while True:
            try:
                self.service.save(pending)
                break
            except JournalError as exc:
                if not messagebox.askretrycancel("Запись пока не сохранена", str(exc), parent=self.root):
                    self.status.set("Сохранение отменено. Новая строка в журнал не добавлена.")
                    return
        self.status.set("Запись сохранена. Повтор: " + ("да" if pending.repeat else "нет"))
        self.show_result(pending)

    def show_result(self, pending):
        if self.result is not None and self.result.winfo_exists():
            self.result.destroy()
        window = self.result = tk.Toplevel(self.root)
        window.title("Ваш экзаменационный билет")
        window.geometry("680x460")
        window.transient(self.root)
        window.configure(bg="#f2f5f9")
        frame = ttk.Frame(window, padding=30)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text=pending.student.label, style="Caption.TLabel").pack(anchor="w")
        ttk.Label(frame, text=f"Ваш билет № {pending.ticket.number}",
                  style="Title.TLabel").pack(anchor="w", pady=(12, 25))
        for number, question in enumerate(pending.ticket.questions, 1):
            ttk.Label(frame, text=f"{number}. {question}", wraplength=590).pack(anchor="w", pady=8)
        ttk.Label(frame, text="Сохранено в журнале · ESC — вернуться к выбору",
                  style="Caption.TLabel").pack(anchor="w", pady=(20, 10))
        ttk.Button(frame, text="Вернуться к выбору", command=window.destroy).pack(anchor="w")
        window.bind("<Escape>", lambda _event: window.destroy())
        window.focus_set()
