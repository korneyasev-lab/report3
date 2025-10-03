"""
Система автоматизации составления отчетов
Главный файл запуска
Версия с правильным определением рабочей директории
"""

import tkinter as tk
import os
import sys
import config
from gui import ReportApp
from database import init_database


def resolve_app_dir():
    """
    Определить папку где лежит исполняемый файл (.exe/.app)
    Для macOS выходит из бандла .app наружу
    """
    if getattr(sys, 'frozen', False):
        # Программа скомпилирована
        exe = sys.executable

        if sys.platform == "darwin" and "/Contents/MacOS/" in exe:
            # macOS: поднимаемся из Contents/MacOS на 3 уровня к корню .app
            app_bundle = os.path.abspath(os.path.join(exe, "../../.."))
            # Возвращаем папку где лежит .app
            return os.path.dirname(app_bundle)
        else:
            # Windows/Linux: просто папка где .exe
            return os.path.dirname(exe)
    else:
        # Режим разработки: текущая папка проекта
        return os.path.dirname(os.path.abspath(__file__))


def setup_working_directory():
    """
    Настройка рабочей директории и создание необходимых папок
    Returns: путь к рабочей директории
    """
    try:
        # Определяем папку рядом с программой
        app_dir = resolve_app_dir()

        # Проверяем права на запись
        if os.access(app_dir, os.W_OK):
            # Есть права - работаем рядом с программой
            work_dir = app_dir
            if config.DEBUG_MODE:
                print(f"Рабочая директория: {work_dir} (рядом с программой)")
        else:
            # Нет прав (Applications/карантин) - fallback в Documents
            work_dir = os.path.join(
                os.path.expanduser("~"),
                "Documents",
                config.WORK_DIR_NAME
            )
            os.makedirs(work_dir, exist_ok=True)
            if config.DEBUG_MODE:
                print(f"Нет прав на запись рядом с программой")
                print(f"Рабочая директория: {work_dir} (Documents)")

        # Переключаемся на рабочую директорию
        os.chdir(work_dir)

        # Создаём подпапки
        folders_to_create = [
            config.FORMS_FOLDER.rstrip('/'),
            config.REPORTS_FOLDER.rstrip('/'),
            config.TEMPLATES_FOLDER.rstrip('/')
        ]

        if config.BACKUP_FOLDER:
            folders_to_create.append(config.BACKUP_FOLDER.rstrip('/'))

        for folder in folders_to_create:
            os.makedirs(folder, exist_ok=True)

        return work_dir

    except Exception as e:
        print(f"Ошибка настройки рабочей директории: {e}")
        raise


def main():
    """Главная функция запуска"""
    try:
        # Настройка директорий
        work_dir = setup_working_directory()

        # Инициализация БД
        init_database()

        # Запуск GUI
        root = tk.Tk()

        # Показываем пользователю где создались папки
        from tkinter import messagebox
        messagebox.showinfo(
            "Рабочая директория",
            f"Папки созданы в:\n{work_dir}\n\n"
            f"Файлы форм (.xlsx) кладите в:\n{work_dir}/формы/\n\n"
            f"Отчёты сохраняются в:\n{work_dir}/отчеты/"
        )

        app = ReportApp(root)
        root.mainloop()

    except Exception as e:
        print(f"Критическая ошибка запуска: {e}")

        if config.DEBUG_MODE:
            import traceback
            traceback.print_exc()

        # Показываем ошибку пользователю
        try:
            root = tk.Tk()
            root.withdraw()
            from tkinter import messagebox
            messagebox.showerror(
                config.DIALOG_TITLES["error"],
                f"Не удалось запустить приложение:\n{e}"
            )
        except:
            pass


if __name__ == "__main__":
    main()