# -*- coding: utf-8 -*-
"""
export_excel.py — создает Excel отчёты в текущей рабочей директории
"""

import os
from datetime import datetime

try:
    import openpyxl
    from openpyxl.styles import Font, Alignment, Border, Side
except Exception as e:
    raise RuntimeError("Требуется пакет 'openpyxl'") from e


def _reports_dir() -> str:
    """Путь к папке отчетов"""
    # Используем текущую рабочую директорию (уже установлена в main.py)
    reports = os.path.join(os.getcwd(), "отчеты")
    os.makedirs(reports, exist_ok=True)
    return reports


def sanitize_filename(name: str) -> str:
    """Удаляет недопустимые символы"""
    bad = r'\/:*?"<>|%#'
    return "".join(("_" if c in bad else c) for c in name).strip() or "report"


# ---------- СОЗДАНИЕ EXCEL-ОТЧЁТА ----------

def create_excel_report(
        report_name: str,
        form_name: str,
        month: str,
        year: str,
        answers
) -> str:
    """Создаёт Excel-отчёт"""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Отчет"

    # Шрифты
    title_font = Font(name="Arial", size=14, bold=True)
    question_font = Font(name="Arial", size=11, bold=True)
    answer_font = Font(name="Arial", size=12, bold=True)
    comment_font = Font(name="Arial", size=10, italic=True)

    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )

    # Шапка
    ws.merge_cells('A1:B1')
    ws['A1'] = report_name
    ws['A1'].font = title_font
    ws['A1'].alignment = Alignment(horizontal='center', vertical='center')

    # Ширина колонок
    ws.column_dimensions['A'].width = 65
    ws.column_dimensions['B'].width = 10

    # Данные
    current_row = 3

    for item in (answers or []):
        if isinstance(item, dict):
            q = str(item.get("question_text", "") or "")
            a = str(item.get("answer_yes_no", "") or "")
            c = str(item.get("comment", "") or "")
        else:
            q = str(getattr(item, "question_text", "") or "")
            a = str(getattr(item, "answer_yes_no", "") or "")
            c = str(getattr(item, "comment", "") or "")

        # Вопрос
        ws[f'A{current_row}'] = q.strip()
        ws[f'A{current_row}'].font = question_font
        ws[f'A{current_row}'].alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)
        ws[f'A{current_row}'].border = thin_border

        # Ответ
        ws[f'B{current_row}'] = a.strip()
        ws[f'B{current_row}'].font = answer_font
        ws[f'B{current_row}'].alignment = Alignment(horizontal='center', vertical='center')
        ws[f'B{current_row}'].border = thin_border

        current_row += 1

        # Комментарий
        if c.strip():
            ws.merge_cells(f'A{current_row}:B{current_row}')
            ws[f'A{current_row}'] = c.strip()
            ws[f'A{current_row}'].font = comment_font
            ws[f'A{current_row}'].alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)
            ws[f'A{current_row}'].border = thin_border
            current_row += 1

    # Дата
    current_row += 1
    ws.merge_cells(f'A{current_row}:B{current_row}')
    ws[f'A{current_row}'] = f"Дата создания отчета: {datetime.now().strftime('%d.%m.%Y')}"
    ws[f'A{current_row}'].font = Font(name='Arial', size=11)
    ws[f'A{current_row}'].alignment = Alignment(horizontal='left', vertical='center')

    # Подпись
    current_row += 2
    ws.merge_cells(f'A{current_row}:B{current_row}')
    ws[f'A{current_row}'] = "Подпись: _________________________"
    ws[f'A{current_row}'].font = Font(name='Arial', size=11)
    ws[f'A{current_row}'].alignment = Alignment(horizontal='left', vertical='center')

    # Печать
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_margins.left = 0.2
    ws.page_margins.right = 0.2
    ws.page_margins.top = 0.75
    ws.page_margins.bottom = 0.75
    ws.print_options.horizontalCentered = True

    # Сохранение
    reports_dir = _reports_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe = sanitize_filename(f"{report_name}_{timestamp}.xlsx")
    out_path = os.path.join(reports_dir, safe)

    wb.save(out_path)

    # Показываем ПОЛНЫЙ путь к сохранённому файлу
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo(
            "Отчёт сохранён",
            f"Файл сохранён в:\n\n{out_path}"
        )
        root.destroy()
    except:
        pass

    return out_path