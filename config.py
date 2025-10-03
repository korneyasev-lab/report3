# -*- coding: utf-8 -*-
"""
Конфигурация для Системы отчетов (report3)
Все настройки в одном месте
"""

import os
import sys
import platform

# =============================================================================
# ОПРЕДЕЛЕНИЕ РАБОЧЕЙ ДИРЕКТОРИИ
# =============================================================================

def get_base_path():
    """Получить базовую директорию для работы программы"""
    if getattr(sys, 'frozen', False):
        # Запущен как .exe/.app
        if platform.system() == 'Windows':
            # На Windows - папка Documents пользователя
            return os.path.join(os.path.expanduser('~'), 'Documents', 'SistemaOtchetov')
        else:
            # На macOS - рядом с программой
            return os.path.dirname(sys.executable)
    else:
        # Запущен из исходников
        return os.path.dirname(os.path.abspath(__file__))

BASE_DIR = get_base_path()

# Папки для работы программы
FORMS_DIR = os.path.join(BASE_DIR, "формы")
REPORTS_DIR = os.path.join(BASE_DIR, "отчеты")
TEMPLATES_DIR = os.path.join(BASE_DIR, "шаблоны")
DB_PATH = os.path.join(BASE_DIR, "reports.db")

# Создать папки при импорте
for directory in [BASE_DIR, FORMS_DIR, REPORTS_DIR, TEMPLATES_DIR]:
    os.makedirs(directory, exist_ok=True)

# =============================================================================
# ПУТИ К ФАЙЛАМ И ПАПКАМ
# =============================================================================

# Название папки в Documents
WORK_DIR_NAME = "Система отчетов"

# База данных
DB_FILE = "reports.db"
BACKUP_FOLDER = "backups/"

# Папки для работы
FORMS_FOLDER = "формы/"
REPORTS_FOLDER = "отчеты/"
TEMPLATES_FOLDER = "шаблоны/"

# =============================================================================
# НАСТРОЙКИ ПРИЛОЖЕНИЯ
# =============================================================================

APP_TITLE = "Система автоматизации отчётов"
QUESTIONS_PER_PAGE = 5

# =============================================================================
# НАСТРОЙКИ ИНТЕРФЕЙСА
# =============================================================================

# Шрифты для Windows
FONTS_WINDOWS = {
    "title": 16,
    "large": 14,
    "medium": 11,
    "small": 10
}

# Шрифты для macOS/Linux
FONTS_MACOS = {
    "title": 20,
    "large": 18,
    "medium": 16,
    "small": 12
}

# Отступы для Windows
PADDING_WINDOWS = {
    "pady": 3,
    "padx": 5
}

# Отступы для macOS/Linux
PADDING_MACOS = {
    "pady": 5,
    "padx": 10
}

# Размеры виджетов
BUTTON_WIDTH = 25
COMMENT_HEIGHT = 2

# =============================================================================
# EXCEL НАСТРОЙКИ
# =============================================================================

# Столбцы Excel
EXCEL_COLUMN_A_WIDTH = 65
EXCEL_COLUMN_B_WIDTH = 10

# Шрифты Excel
EXCEL_TITLE_FONT = {"name": "Arial", "size": 14, "bold": True}
EXCEL_QUESTION_FONT = {"name": "Arial", "size": 11, "bold": True}
EXCEL_ANSWER_FONT = {"name": "Arial", "size": 12, "bold": True}
EXCEL_COMMENT_FONT = {"name": "Arial", "size": 10, "italic": True}
EXCEL_NORMAL_FONT = {"name": "Arial", "size": 11}

# Отступы страницы
EXCEL_PAGE_MARGINS = {
    "left": 0.2,
    "right": 0.2,
    "top": 0.75,
    "bottom": 0.75
}

# =============================================================================
# СООБЩЕНИЯ
# =============================================================================

ERROR_MESSAGES = {
    "no_forms": "Не найдены файлы форм в папке 'формы/'\nПоместите туда Excel файлы с вопросами.",
    "file_not_found": "Файл не найден",
    "file_locked": "Файл заблокирован другим процессом",
    "file_corrupted": "Файл повреждён или имеет неверный формат Excel",
    "no_access": "Нет доступа к файлу. Возможно, он открыт в другой программе",
    "no_data": "Файл не содержит данных (нужно минимум 2 строки)",
    "no_questions": "В файле не найдено ни одного валидного вопроса",
    "invalid_format": "Неподдерживаемый формат файла. Ожидается .xlsx или .xls",
    "db_error": "Ошибка работы с базой данных",
    "db_locked": "База данных заблокирована другим процессом. Закройте другие экземпляры программы.",
    "db_corrupted": "База данных повреждена",
    "no_write_access": "Нет прав на запись в директорию",
    "validation_error": "Ошибка валидации данных",
    "no_answer": "Пожалуйста, ответьте на вопрос",
    "select_report": "Выберите отчёт из списка",
    "fill_all_fields": "Заполните все поля!"
}

INFO_MESSAGES = {
    "questions_loaded": "Успешно загружено {count} вопросов",
    "rows_skipped": "Пропущено {count} строк без вопросов",
    "report_saved": "Отчёт сохранён!\n\nФайл: {filename}\nПапка: {folder}",
    "report_deleted": "Отчет удален",
    "db_initialized": "База данных инициализирована",
    "no_reports": "Нет сохранённых отчётов",
    "templates_folder_created": "Папка 'шаблоны' создана.\nПоместите туда файлы шаблонов документов.",
    "work_dir_set": "Рабочая папка: {path}",
    "all_questions_answered": "Все вопросы заполнены.\n\nСохранить отчёт в базу данных и экспортировать в Excel?"
}

DIALOG_TITLES = {
    "error": "Ошибка",
    "success": "Успех",
    "warning": "Внимание",
    "info": "Информация",
    "confirm_save": "Завершение отчёта",
    "confirm_delete": "Подтверждение",
    "help": "Справка",
    "documents": "Связанные документы"
}

# =============================================================================
# ВАЛИДАЦИЯ
# =============================================================================

# Расширения файлов
VALID_EXCEL_EXTENSIONS = ('.xlsx', '.xls')

# Проверки
VALIDATE_FILE_EXISTS = True
VALIDATE_FILE_FORMAT = True
VALIDATE_FILE_ACCESS = True

# =============================================================================
# РАЗРАБОТЧЕСКИЕ НАСТРОЙКИ
# =============================================================================

DEBUG_MODE = True
PRINT_SQL_QUERIES = False