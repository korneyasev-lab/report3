"""
GUI модуль для системы автоматизации отчётов
Версия с config.py и поддержкой типов отчётов
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime
from logic import ReportLogic, find_form_file
import subprocess
import os
import sys
import config
from telegram_service import TelegramService, validate_settings
from telegram_config import save_telegram_settings, load_telegram_settings


class ReportApp:
    """Главный класс приложения с GUI"""

    def __init__(self, root):
        self.root = root
        self.root.title(config.APP_TITLE)

        # Адаптация размеров под операционную систему
        if os.name == 'nt':  # Windows
            fonts = config.FONTS_WINDOWS
            padding = config.PADDING_WINDOWS
        else:  # macOS/Linux
            fonts = config.FONTS_MACOS
            padding = config.PADDING_MACOS

        self.FONT_TITLE = fonts["title"]
        self.FONT_LARGE = fonts["large"]
        self.FONT_MEDIUM = fonts["medium"]
        self.FONT_SMALL = fonts["small"]
        self.PADY = padding["pady"]
        self.PADX = padding["padx"]
        self.COMMENT_HEIGHT = config.COMMENT_HEIGHT
        self.BUTTON_WIDTH = config.BUTTON_WIDTH

        # Развернуть окно на весь экран
        try:
            if os.name == 'nt':
                self.root.state('zoomed')
            else:
                screen_width = self.root.winfo_screenwidth()
                screen_height = self.root.winfo_screenheight()
                self.root.geometry(f"{screen_width}x{screen_height}+0+0")
        except:
            self.root.geometry("1400x900")

        self.logic = ReportLogic()
        self.current_block_widgets = {}

        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.show_main_menu()

    def clear_frame(self):
        """Очистка главного контейнера"""
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def show_main_menu(self):
        """Показать главное меню с README слева и кнопками справа"""
        self.clear_frame()

        # Заголовок
        tk.Label(
            self.main_frame,
            text=config.APP_TITLE,
            font=("Arial", self.FONT_TITLE + 4, "bold")
        ).pack(pady=30)

        # Контейнер для двух колонок
        content_frame = tk.Frame(self.main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=40)

        # ЛЕВАЯ КОЛОНКА - README
        left_frame = tk.Frame(content_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 20))

        readme_frame = tk.LabelFrame(
            left_frame,
            text="📖 Инструкция",
            font=("Arial", self.FONT_MEDIUM + 1, "bold"),
            padx=20,
            pady=15
        )
        readme_frame.pack(fill=tk.BOTH, expand=True)

        readme_text = """
КАК НАЧАТЬ РАБОТУ:

1. ПРИ ПЕРВОМ ЗАПУСКЕ
   Программа автоматически создаёт папки рядом с исполняемым файлом:
   • формы/ - для файлов с вопросами
   • отчеты/ - для готовых отчётов
   • шаблоны/ - для документов-образцов

2. ПОДГОТОВКА ФАЙЛОВ С ВОПРОСАМИ
   В папку "формы/" поместите Excel файлы (.xlsx) со следующей структурой:

   Формат таблицы (4 колонки):
   | Вопрос | ГОСТ ИСО 9001 | Руководство по качеству | Документы |

   Первая строка - заголовки (программа их пропускает)
   Со второй строки - ваши вопросы и справочная информация

3. НАЗВАНИЯ ФАЙЛОВ
   • Должность_1.xlsx - месячные отчёты (короткий список вопросов)
   • Должность_2.xlsx - квартальные (март, июнь, сентябрь, декабрь)
   • Должность_3.xlsx - годовые (январь, полный список)
   • Должность.xlsx - универсальный (если нет разделения по типам)

   Пример: Главный_инженер_1.xlsx, Директор_2.xlsx

4. СОЗДАНИЕ ОТЧЁТА
   • Выберите должность из списка
   • Выберите месяц - программа автоматически определит тип отчёта
   • Заполните ответы (ДА/НЕТ) и комментарии
   • Сохранённые отчёты появятся в папке "отчеты/"

5. ДОПОЛНИТЕЛЬНО
   • Копировать/Вставить - через меню Edit
   • Шаблоны документов храните в "шаблоны/"
        """

        tk.Label(
            readme_frame,
            text=readme_text.strip(),
            font=("Arial", self.FONT_SMALL + 1),
            justify=tk.LEFT,
            anchor='nw'
        ).pack(fill=tk.BOTH, expand=True)

        # ПРАВАЯ КОЛОНКА - Кнопки
        right_frame = tk.Frame(content_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y)

        # Отступ сверху чтобы кнопки были по центру
        tk.Frame(right_frame, height=100).pack()

        tk.Button(
            right_frame,
            text="Создать новый отчёт",
            font=("Arial", self.FONT_MEDIUM),
            width=self.BUTTON_WIDTH,
            height=2,
            command=self.show_report_creation
        ).pack(pady=self.PADY * 2)

        tk.Button(
            right_frame,
            text="Архив отчётов",
            font=("Arial", self.FONT_MEDIUM),
            width=self.BUTTON_WIDTH,
            height=2,
            command=self.show_reports_archive
        ).pack(pady=self.PADY * 2)

        tk.Button(
            right_frame,
            text="Выход",
            font=("Arial", self.FONT_MEDIUM),
            width=self.BUTTON_WIDTH,
            height=2,
            command=self.root.quit
        ).pack(pady=self.PADY * 2)

    def show_report_creation(self):
        """Экран выбора формы и параметров отчёта"""
        self.clear_frame()
        tk.Label(
            self.main_frame,
            text="Новый отчёт",
            font=("Arial", self.FONT_TITLE, "bold")
        ).pack(pady=30)

        form_frame = tk.Frame(self.main_frame)
        form_frame.pack(pady=20)

        # Выбор формы из списка файлов в папке "формы"
        tk.Label(
            form_frame,
            text="Выберите форму:",
            font=("Arial", self.FONT_MEDIUM)
        ).grid(row=0, column=0, sticky="w", pady=self.PADY * 2)

        self.form_var = tk.StringVar()
        forms = self.logic.load_forms_list()

        if not forms:
            messagebox.showerror(
                config.DIALOG_TITLES["error"],
                config.ERROR_MESSAGES["no_forms"]
            )
            self.show_main_menu()
            return

        ttk.Combobox(
            form_frame,
            textvariable=self.form_var,
            values=forms,
            font=("Arial", self.FONT_MEDIUM),
            width=30,
            state="readonly"
        ).grid(row=0, column=1, pady=self.PADY * 2, padx=self.PADX)

        # Месяц
        tk.Label(
            form_frame,
            text="Месяц:",
            font=("Arial", self.FONT_MEDIUM)
        ).grid(row=1, column=0, sticky="w", pady=self.PADY * 2)

        self.month_var = tk.StringVar()
        months = [
            "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
            "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
        ]
        ttk.Combobox(
            form_frame,
            textvariable=self.month_var,
            values=months,
            font=("Arial", self.FONT_MEDIUM),
            width=30,
            state="readonly"
        ).grid(row=1, column=1, columnspan=2, pady=self.PADY * 2, padx=self.PADX, sticky="w")

        # Год
        tk.Label(
            form_frame,
            text="Год:",
            font=("Arial", self.FONT_MEDIUM)
        ).grid(row=2, column=0, sticky="w", pady=self.PADY * 2)

        self.year_var = tk.StringVar(value=str(datetime.now().year))
        tk.Entry(
            form_frame,
            textvariable=self.year_var,
            font=("Arial", self.FONT_MEDIUM),
            width=32
        ).grid(row=2, column=1, columnspan=2, pady=self.PADY * 2, padx=self.PADX, sticky="w")

        # Дата создания
        tk.Label(
            form_frame,
            text="Дата создания:",
            font=("Arial", self.FONT_MEDIUM)
        ).grid(row=3, column=0, sticky="w", pady=self.PADY * 2)

        self.date_var = tk.StringVar(value=datetime.now().strftime("%d.%m.%Y"))
        tk.Entry(
            form_frame,
            textvariable=self.date_var,
            font=("Arial", self.FONT_MEDIUM),
            width=32
        ).grid(row=3, column=1, columnspan=2, pady=self.PADY * 2, padx=self.PADX, sticky="w")

        # Кнопки управления
        btn_frame = tk.Frame(self.main_frame)
        btn_frame.pack(pady=30)

        tk.Button(
            btn_frame,
            text="Начать заполнение",
            font=("Arial", self.FONT_MEDIUM),
            width=20,
            command=self.start_filling
        ).pack(side=tk.LEFT, padx=self.PADX)

        tk.Button(
            btn_frame,
            text="Назад",
            font=("Arial", self.FONT_MEDIUM),
            width=20,
            command=self.show_main_menu
        ).pack(side=tk.LEFT, padx=self.PADX)

    def start_filling(self):
        """Начать заполнение отчёта"""
        form_name = self.form_var.get()
        month = self.month_var.get()
        year = self.year_var.get()
        report_date = self.date_var.get()

        if not all([form_name, month, year, report_date]):
            messagebox.showerror(
                config.DIALOG_TITLES["error"],
                config.ERROR_MESSAGES["fill_all_fields"]
            )
            return

        # Загружаем вопросы из файла с учётом типа отчёта
        excel_file, filename = find_form_file(form_name, month)

        if not excel_file:
            messagebox.showerror(
                config.DIALOG_TITLES["error"],
                f"Не найден файл формы для:\n{form_name}\n\nОжидается один из файлов:\n{form_name}_1.xlsx (месячный)\n{form_name}_2.xlsx (квартальный)\n{form_name}_3.xlsx (годовой)\nили\n{form_name}.xlsx (универсальный)"
            )
            return

        if not self.logic.load_questions_from_excel(excel_file):
            messagebox.showerror(
                config.DIALOG_TITLES["error"],
                f"Не удалось загрузить вопросы из файла:\n{filename}"
            )
            return

        self.logic.init_report(form_name, month, year, report_date)
        self.show_questions_screen()

    def show_questions_screen(self):
        """Экран заполнения вопросов блоками"""
        self.clear_frame()

        start, end = self.logic.get_current_block_questions()
        total = len(self.logic.questions_list)

        header = f"Отчёт: {self.logic.current_report_data['form_name']} {self.logic.current_report_data['month']} {self.logic.current_report_data['year']}"
        tk.Label(
            self.main_frame,
            text=header,
            font=("Arial", self.FONT_MEDIUM, "bold")
        ).pack(pady=self.PADY)

        tk.Label(
            self.main_frame,
            text=f"Вопросы {start + 1}-{end} из {total}",
            font=("Arial", self.FONT_SMALL)
        ).pack(pady=self.PADY // 2)

        canvas_frame = tk.Frame(self.main_frame)
        canvas_frame.pack(pady=self.PADY, fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(canvas_frame)
        scrollbar = tk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.current_block_widgets = {}
        for i in range(start, end):
            self.create_question_widget(scrollable_frame, i)

        btn_frame = tk.Frame(self.main_frame)
        btn_frame.pack(pady=self.PADY * 2)

        btn_prev = tk.Button(
            btn_frame,
            text="← Назад",
            font=("Arial", self.FONT_LARGE),
            width=15,
            command=self.on_prev_block
        )
        btn_prev.pack(side=tk.LEFT, padx=self.PADX)
        if start == 0:
            btn_prev.config(state=tk.DISABLED)

        btn_next = tk.Button(
            btn_frame,
            text="Далее →" if end < total else "Завершить",
            font=("Arial", self.FONT_LARGE),
            width=15,
            command=self.on_next_block
        )
        btn_next.pack(side=tk.LEFT, padx=self.PADX)

    def create_question_widget(self, parent, question_index):
        """Создать виджет для одного вопроса"""
        question = self.logic.questions_list[question_index]
        answer_data = self.logic.answers_list[question_index]

        q_frame = tk.LabelFrame(
            parent,
            text=f"Вопрос {question_index + 1}",
            font=("Arial", self.FONT_MEDIUM, "bold"),
            padx=self.PADX,
            pady=self.PADY
        )
        q_frame.pack(pady=self.PADY, padx=20, fill=tk.X)

        top_frame = tk.Frame(q_frame)
        top_frame.pack(fill=tk.X, pady=self.PADY // 2)

        answer_frame = tk.Frame(top_frame)
        answer_frame.pack(side=tk.LEFT, padx=(0, 15))

        current_answer = answer_data['answer_yes_no']

        btn_yes = tk.Button(
            answer_frame,
            text="ДА",
            font=("Arial", self.FONT_LARGE, "bold"),
            width=5,
            bg="green" if current_answer == "Да" else "lightgray",
            fg="white" if current_answer == "Да" else "darkgreen",
            command=lambda idx=question_index: self.set_answer(idx, "Да")
        )
        btn_yes.pack(side=tk.LEFT, padx=3)

        btn_no = tk.Button(
            answer_frame,
            text="НЕТ",
            font=("Arial", self.FONT_LARGE, "bold"),
            width=5,
            bg="red" if current_answer == "Нет" else "lightgray",
            fg="white" if current_answer == "Нет" else "darkred",
            command=lambda idx=question_index: self.set_answer(idx, "Нет")
        )
        btn_no.pack(side=tk.LEFT, padx=3)

        tk.Label(
            top_frame,
            text=question['question'],
            font=("Arial", self.FONT_LARGE),
            wraplength=800,
            justify=tk.LEFT,
            anchor='w'
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)

        buttons_frame = tk.Frame(top_frame)
        buttons_frame.pack(side=tk.RIGHT, padx=self.PADX)

        tk.Button(
            buttons_frame,
            text="?",
            font=("Arial", self.FONT_MEDIUM, "bold"),
            width=3,
            command=lambda: self.show_help(question)
        ).pack(side=tk.LEFT, padx=2)

        if question.get('documents'):
            tk.Button(
                buttons_frame,
                text="📄",
                font=("Arial", self.FONT_MEDIUM, "bold"),
                width=3,
                command=lambda: self.show_documents(question)
            ).pack(side=tk.LEFT, padx=2)

        comment_frame = tk.Frame(q_frame)
        comment_frame.pack(fill=tk.X, pady=self.PADY // 2)

        tk.Label(
            comment_frame,
            text="Комментарий:",
            font=("Arial", self.FONT_LARGE)
        ).pack(side=tk.LEFT, padx=(0, self.PADX))

        comment_text = tk.Text(
            comment_frame,
            height=self.COMMENT_HEIGHT,
            font=("Arial", self.FONT_LARGE),
            wrap=tk.WORD
        )
        comment_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        if answer_data['comment']:
            comment_text.insert(1.0, answer_data['comment'])

        def adjust_height(event=None):
            lines = comment_text.get("1.0", tk.END).count('\n')
            comment_text.config(height=max(self.COMMENT_HEIGHT, min(6, lines + 1)))

        comment_text.bind('<KeyRelease>', adjust_height)
        adjust_height()

        self.current_block_widgets[question_index] = {
            'btn_yes': btn_yes,
            'btn_no': btn_no,
            'comment': comment_text
        }

    def set_answer(self, question_index, answer):
        """Установить ответ с инверсией цвета кнопок"""
        widgets = self.current_block_widgets[question_index]

        if answer == "Да":
            widgets['btn_yes'].config(bg="green", fg="white")
            widgets['btn_no'].config(bg="lightgray", fg="darkred")
        else:
            widgets['btn_yes'].config(bg="lightgray", fg="darkgreen")
            widgets['btn_no'].config(bg="red", fg="white")

        comment = widgets['comment'].get(1.0, tk.END).strip()
        self.logic.save_answer(question_index, answer, comment)

    def show_help(self, question):
        """Показать справку"""
        help_window = tk.Toplevel(self.root)
        help_window.title(config.DIALOG_TITLES["help"])
        help_window.geometry("1000x700")

        tk.Label(
            help_window,
            text="ГОСТ ИСО 9001:",
            font=("Arial", self.FONT_SMALL, "bold")
        ).pack(pady=(15, self.PADY))

        gost_text = scrolledtext.ScrolledText(
            help_window,
            height=3,
            width=110,
            font=("Arial", self.FONT_SMALL),
            wrap=tk.WORD
        )
        gost_text.pack(pady=self.PADY, padx=20, fill=tk.X)
        gost_text.insert(1.0, question['gost'] or "Информация отсутствует")
        gost_text.config(state=tk.DISABLED)

        tk.Label(
            help_window,
            text="Руководство по качеству:",
            font=("Arial", self.FONT_SMALL, "bold")
        ).pack(pady=(15, self.PADY))

        quality_text = scrolledtext.ScrolledText(
            help_window,
            width=110,
            font=("Arial", self.FONT_SMALL),
            wrap=tk.WORD
        )
        quality_text.pack(pady=self.PADY, padx=20, fill=tk.BOTH, expand=True)
        quality_text.insert(1.0, question['quality'] or "Информация отсутствует")
        quality_text.config(state=tk.DISABLED)

        tk.Button(
            help_window,
            text="Закрыть",
            font=("Arial", self.FONT_SMALL - 2),
            width=20,
            command=help_window.destroy
        ).pack(pady=20)

    def show_documents(self, question):
        """Показать связанные документы"""
        docs = question.get('documents', '')

        if not docs:
            messagebox.showinfo(
                config.DIALOG_TITLES["documents"],
                "Для этого вопроса нет связанных документов"
            )
            return

        doc_window = tk.Toplevel(self.root)
        doc_window.title(config.DIALOG_TITLES["documents"])
        doc_window.geometry("700x500")

        tk.Label(
            doc_window,
            text="Документы для этого вопроса:",
            font=("Arial", self.FONT_SMALL, "bold")
        ).pack(pady=15)

        text_widget = scrolledtext.ScrolledText(
            doc_window,
            height=18,
            width=80,
            font=("Arial", self.FONT_SMALL),
            wrap=tk.WORD
        )
        text_widget.pack(pady=self.PADY * 2, padx=20, fill=tk.BOTH, expand=True)
        text_widget.insert(1.0, docs)
        text_widget.config(state=tk.DISABLED)

        btn_frame = tk.Frame(doc_window)
        btn_frame.pack(pady=15)

        tk.Button(
            btn_frame,
            text="Открыть папку шаблонов",
            font=("Arial", self.FONT_SMALL - 2),
            command=self.open_templates_folder
        ).pack(side=tk.LEFT, padx=self.PADX)

        tk.Button(
            btn_frame,
            text="Закрыть",
            font=("Arial", self.FONT_SMALL - 2),
            command=doc_window.destroy
        ).pack(side=tk.LEFT, padx=self.PADX)

    def open_templates_folder(self):
        """Открыть папку шаблонов"""
        templates_path = os.path.abspath(config.TEMPLATES_FOLDER.rstrip('/'))

        if not os.path.exists(templates_path):
            os.makedirs(templates_path)
            messagebox.showinfo(
                config.DIALOG_TITLES["info"],
                config.INFO_MESSAGES["templates_folder_created"]
            )

        try:
            if os.name == 'nt':
                os.startfile(templates_path)
            elif sys.platform == 'darwin':
                subprocess.Popen(['open', templates_path])
            else:
                subprocess.Popen(['xdg-open', templates_path])
        except Exception as e:
            messagebox.showerror(
                config.DIALOG_TITLES["error"],
                f"Не удалось открыть папку:\n{e}"
            )

    def save_current_block(self):
        """Сохранить ответы текущего блока"""
        for idx, widgets in self.current_block_widgets.items():
            comment = widgets['comment'].get(1.0, tk.END).strip()
            current_answer = self.logic.answers_list[idx]['answer_yes_no']
            if current_answer:
                self.logic.save_answer(idx, current_answer, comment)

    def on_prev_block(self):
        """Обработка кнопки Назад"""
        self.save_current_block()
        self.logic.prev_block()
        self.show_questions_screen()

    def on_next_block(self):
        """Обработка кнопки Далее/Завершить"""
        for idx in self.current_block_widgets.keys():
            if not self.logic.answers_list[idx]['answer_yes_no']:
                messagebox.showwarning(
                    config.DIALOG_TITLES["warning"],
                    f"{config.ERROR_MESSAGES['no_answer']} {idx + 1}"
                )
                return

        self.save_current_block()

        if not self.logic.next_block():
            # Это был последний блок
            if messagebox.askyesno(
                config.DIALOG_TITLES["confirm_save"],
                config.INFO_MESSAGES["all_questions_answered"]
            ):
                self.save_report()
        else:
            self.show_questions_screen()

    def save_report(self):
        """Сохранить отчёт"""
        success, result = self.logic.save_report()
        if success:
            messagebox.showinfo(
                config.DIALOG_TITLES["success"],
                config.INFO_MESSAGES["report_saved"].format(
                    filename=result,
                    folder=config.REPORTS_FOLDER
                )
            )
            self.show_main_menu()
        else:
            messagebox.showerror(
                config.DIALOG_TITLES["error"],
                f"Ошибка при сохранении:\n{result}"
            )

    def show_reports_archive(self):
        """Архив отчётов"""
        self.clear_frame()
        tk.Label(
            self.main_frame,
            text="Архив отчётов",
            font=("Arial", self.FONT_LARGE, "bold")
        ).pack(pady=20)

        reports = self.logic.get_all_reports_from_db()
        if not reports:
            tk.Label(
                self.main_frame,
                text=config.INFO_MESSAGES["no_reports"],
                font=("Arial", self.FONT_SMALL)
            ).pack(pady=20)
        else:
            tree = self.create_reports_tree(
                reports,
                ["ID", "Форма", "Месяц", "Год", "Дата создания"],
                [50, 250, 100, 80, 150]
            )

            btn_frame = tk.Frame(self.main_frame)
            btn_frame.pack(pady=20)

            tk.Button(
                btn_frame,
                text="Просмотр",
                font=("Arial", self.FONT_SMALL),
                width=20,
                command=lambda: self.open_report(tree)
            ).pack(side=tk.LEFT, padx=self.PADX)

            tk.Button(
                btn_frame,
                text="📤 Отправить в Telegram",
                font=("Arial", self.FONT_SMALL),
                width=25,
                command=lambda: self.send_report_to_telegram(tree)
            ).pack(side=tk.LEFT, padx=self.PADX)

            tk.Button(
                btn_frame,
                text="⚙️ Настройки TG",
                font=("Arial", self.FONT_SMALL),
                width=18,
                command=self.open_telegram_settings
            ).pack(side=tk.LEFT, padx=self.PADX)

            tk.Button(
                btn_frame,
                text="Удалить",
                font=("Arial", self.FONT_SMALL),
                width=20,
                command=lambda: self.delete_report(tree)
            ).pack(side=tk.LEFT, padx=self.PADX)

        tk.Button(
            self.main_frame,
            text="Назад",
            font=("Arial", self.FONT_SMALL),
            width=20,
            command=self.show_main_menu
        ).pack(pady=self.PADY * 2)

    def create_reports_tree(self, reports, columns, widths=None):
        """Создать таблицу отчётов"""
        tree_frame = tk.Frame(self.main_frame)
        tree_frame.pack(pady=self.PADY * 2, padx=20, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(tree_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            yscrollcommand=scrollbar.set
        )
        scrollbar.config(command=tree.yview)

        for i, col in enumerate(columns):
            tree.heading(col, text=col)
            tree.column(col, width=widths[i] if widths else 150)

        for report in reports:
            values = [
                report['id'],
                report['form_name'],
                report['month'],
                report['year'],
                report['created_at']
            ]
            tree.insert("", tk.END, values=values)

        tree.pack(fill=tk.BOTH, expand=True)
        return tree

    def open_report(self, tree):
        """Открыть выбранный отчёт"""
        selected = tree.selection()
        if not selected:
            messagebox.showwarning(
                config.DIALOG_TITLES["warning"],
                config.ERROR_MESSAGES["select_report"]
            )
            return

        report_id = tree.item(selected[0])['values'][0]
        report_data = self.logic.get_report_from_db(report_id)

        if report_data:
            self.view_report(report_data)
        else:
            messagebox.showerror(
                config.DIALOG_TITLES["error"],
                "Не удалось загрузить отчёт"
            )

    def view_report(self, report_data):
        """Просмотр отчёта"""
        self.clear_frame()

        header = f"{report_data['form_name']} - {report_data['month']} {report_data['year']}"
        tk.Label(
            self.main_frame,
            text=header,
            font=("Arial", self.FONT_MEDIUM, "bold")
        ).pack(pady=20)

        info = f"Дата отчёта: {report_data['report_date']}\nСоздан: {report_data['created_at']}"
        tk.Label(
            self.main_frame,
            text=info,
            font=("Arial", self.FONT_SMALL - 1)
        ).pack(pady=self.PADY)

        text_frame = tk.Frame(self.main_frame)
        text_frame.pack(pady=self.PADY * 2, padx=20, fill=tk.BOTH, expand=True)

        text_widget = scrolledtext.ScrolledText(
            text_frame,
            font=("Arial", self.FONT_SMALL - 1),
            wrap=tk.WORD
        )
        text_widget.pack(fill=tk.BOTH, expand=True)

        for i, answer in enumerate(report_data['answers']):
            text_widget.insert(tk.END, f"\n{i+1}. {answer['question_text']}\n", "bold")
            text_widget.insert(tk.END, f"Ответ: {answer['answer_yes_no']}\n")
            if answer['comment']:
                text_widget.insert(tk.END, f"Комментарий: {answer['comment']}\n")
            text_widget.insert(tk.END, "\n" + "-"*80 + "\n")

        text_widget.tag_config("bold", font=("Arial", self.FONT_SMALL - 1, "bold"))
        text_widget.config(state=tk.DISABLED)

        tk.Button(
            self.main_frame,
            text="Назад",
            font=("Arial", self.FONT_SMALL),
            width=20,
            command=self.show_reports_archive
        ).pack(pady=20)

    def delete_report(self, tree):
        """Удалить отчёт"""
        selected = tree.selection()
        if not selected:
            messagebox.showwarning(
                config.DIALOG_TITLES["warning"],
                config.ERROR_MESSAGES["select_report"]
            )
            return

        item = tree.item(selected[0])
        report_id = item['values'][0]
        report_name = f"{item['values'][1]} {item['values'][2]} {item['values'][3]}"

        if messagebox.askyesno(
            config.DIALOG_TITLES["confirm_delete"],
            f"Вы уверены, что хотите удалить отчёт:\n{report_name}?"
        ):
            success, message = self.logic.delete_report_from_db(report_id)
            if success:
                messagebox.showinfo(config.DIALOG_TITLES["success"], message)
                self.show_reports_archive()
            else:
                messagebox.showerror(
                    config.DIALOG_TITLES["error"],
                    f"Ошибка при удалении:\n{message}"
                )

    def open_telegram_settings(self):
        """Открыть окно настроек Telegram (для кнопки ⚙️)"""
        self.show_telegram_settings()

    def send_report_to_telegram(self, tree):
        """Отправить выбранный отчёт в Telegram"""
        # Проверка выбора отчёта
        selected = tree.selection()
        if not selected:
            messagebox.showwarning(
                config.DIALOG_TITLES["warning"],
                config.ERROR_MESSAGES["select_report"]
            )
            return

        # Получаем ID отчёта
        report_id = tree.item(selected[0])['values'][0]

        # Создаём сервис Telegram
        telegram = TelegramService()

        # Проверяем настройки
        if not telegram.is_configured():
            # Показываем окно настроек
            self.show_telegram_settings(report_id)
            return

        # Отправляем отчёт
        success, message = telegram.send_report(report_id)

        if success:
            messagebox.showinfo("Telegram", message)
        else:
            # Если ошибка - предлагаем настроить заново
            if messagebox.askyesno(
                "Ошибка отправки",
                f"{message}\n\nХотите проверить настройки Telegram?"
            ):
                self.show_telegram_settings(report_id)

    def show_telegram_settings(self, report_id=None):
        """Окно настроек Telegram"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Настройки Telegram")
        settings_window.geometry("600x500")

        # Заголовок
        tk.Label(
            settings_window,
            text="Настройки Telegram бота",
            font=("Arial", self.FONT_MEDIUM, "bold")
        ).pack(pady=15)

        # Инструкция
        instruction_frame = tk.LabelFrame(
            settings_window,
            text="📖 Инструкция",
            font=("Arial", self.FONT_SMALL, "bold"),
            padx=10,
            pady=10
        )
        instruction_frame.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)

        instruction_text = scrolledtext.ScrolledText(
            instruction_frame,
            height=10,
            width=65,
            font=("Arial", self.FONT_SMALL - 1),
            wrap=tk.WORD
        )
        instruction_text.pack(fill=tk.BOTH, expand=True)
        instruction_text.insert(1.0, config.TELEGRAM_SETUP_INFO)
        instruction_text.config(state=tk.DISABLED)

        # Поля ввода
        fields_frame = tk.Frame(settings_window)
        fields_frame.pack(pady=10, padx=20, fill=tk.X)

        # Токен бота
        tk.Label(
            fields_frame,
            text="Токен бота:",
            font=("Arial", self.FONT_SMALL)
        ).grid(row=0, column=0, sticky="w", pady=5)

        # Загрузить сохранённые настройки
        saved_token, saved_chat_id = load_telegram_settings()
        token_var = tk.StringVar(value=saved_token or config.TELEGRAM_BOT_TOKEN)
        token_entry = tk.Entry(
            fields_frame,
            textvariable=token_var,
            font=("Arial", self.FONT_SMALL),
            width=45
        )
        token_entry.grid(row=0, column=1, pady=5, padx=10)

        # Chat ID
        tk.Label(
            fields_frame,
            text="Chat ID:",
            font=("Arial", self.FONT_SMALL)
        ).grid(row=1, column=0, sticky="w", pady=5)

        chat_id_var = tk.StringVar(value=saved_chat_id or config.TELEGRAM_CHAT_ID)
        chat_id_entry = tk.Entry(
            fields_frame,
            textvariable=chat_id_var,
            font=("Arial", self.FONT_SMALL),
            width=45
        )
        chat_id_entry.grid(row=1, column=1, pady=5, padx=10)

        # Кнопки
        buttons_frame = tk.Frame(settings_window)
        buttons_frame.pack(pady=15)

        def save_settings():
            """Сохранить настройки в config.py"""
            token = token_var.get().strip()
            chat_id = chat_id_var.get().strip()

            # Валидация
            valid, error = validate_settings(token, chat_id)
            if not valid:
                messagebox.showerror("Ошибка валидации", error)
                return

            # Сохраняем в config (в памяти)
            config.TELEGRAM_BOT_TOKEN = token
            config.TELEGRAM_CHAT_ID = chat_id

            # Сохраняем в файл для автозагрузки при следующем запуске
            save_telegram_settings(token, chat_id)

            # Тестируем соединение
            telegram = TelegramService()
            success, message = telegram.test_connection()

            if success:
                messagebox.showinfo("Успех", message)
                settings_window.destroy()

                # Если был передан report_id - отправляем отчёт
                if report_id:
                    success, msg = telegram.send_report(report_id)
                    if success:
                        messagebox.showinfo("Telegram", msg)
                    else:
                        messagebox.showerror("Ошибка", msg)
            else:
                messagebox.showerror("Ошибка", message)

        tk.Button(
            buttons_frame,
            text="Тест соединения и сохранить",
            font=("Arial", self.FONT_SMALL),
            width=30,
            command=save_settings
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            buttons_frame,
            text="Отмена",
            font=("Arial", self.FONT_SMALL),
            width=15,
            command=settings_window.destroy
        ).pack(side=tk.LEFT, padx=5)