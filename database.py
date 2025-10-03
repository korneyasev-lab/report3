"""
Модуль для работы с базой данных SQLite
Версия с config.py
"""

import sqlite3
from datetime import datetime
import os
import config


DB_FILE = config.DB_FILE


def get_connection():
    """
    Получить соединение с БД
    Raises: Exception если не удалось подключиться
    """
    try:
        # Проверка прав на запись в директорию
        db_dir = os.path.dirname(os.path.abspath(DB_FILE)) or '.'
        if not os.access(db_dir, os.W_OK):
            raise PermissionError(config.ERROR_MESSAGES["no_write_access"])

        conn = sqlite3.connect(DB_FILE, timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")

        # Проверка целостности БД
        cursor = conn.cursor()
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()
        if result[0] != 'ok':
            raise sqlite3.DatabaseError(config.ERROR_MESSAGES["db_corrupted"])

        return conn

    except sqlite3.OperationalError as e:
        if "locked" in str(e).lower():
            raise Exception(config.ERROR_MESSAGES["db_locked"])
        elif "unable to open" in str(e).lower():
            raise Exception(f"{config.ERROR_MESSAGES['db_error']}: {e}")
        else:
            raise Exception(f"{config.ERROR_MESSAGES['db_error']}: {e}")
    except PermissionError as e:
        raise Exception(str(e))
    except Exception as e:
        raise Exception(f"{config.ERROR_MESSAGES['db_error']}: {e}")


def init_database():
    """
    Инициализация базы данных - создание таблиц
    Raises: Exception если инициализация не удалась
    """
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Таблица отчетов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                form_name TEXT NOT NULL,
                month TEXT NOT NULL,
                year INTEGER NOT NULL,
                report_date TEXT NOT NULL,
                created_at TEXT NOT NULL,
                file_path TEXT NOT NULL
            )
        ''')

        # Таблица ответов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_id INTEGER NOT NULL,
                question_text TEXT NOT NULL,
                answer_yes_no TEXT NOT NULL,
                comment TEXT,
                gost_text TEXT,
                quality_text TEXT,
                documents_text TEXT,
                FOREIGN KEY (report_id) REFERENCES reports (id) ON DELETE CASCADE
            )
        ''')

        # Индексы
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_answers_report_id 
            ON answers(report_id)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_reports_created_at 
            ON reports(created_at)
        ''')

        conn.commit()

        if config.DEBUG_MODE:
            print(config.INFO_MESSAGES["db_initialized"])

    except Exception as e:
        if conn:
            conn.rollback()
        raise Exception(f"{config.ERROR_MESSAGES['db_error']}: {e}")
    finally:
        if conn:
            conn.close()


def save_report_to_db(report_data, answers_list, file_path):
    """
    Сохранить отчет и ответы в базу данных
    Returns: report_id
    Raises: Exception при ошибке сохранения
    """
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Валидация данных
        if not report_data.get('form_name'):
            raise ValueError("Отсутствует название формы")
        if not report_data.get('month'):
            raise ValueError("Отсутствует месяц")
        if not report_data.get('year'):
            raise ValueError("Отсутствует год")
        if not answers_list:
            raise ValueError("Список ответов пуст")

        cursor.execute('''
            INSERT INTO reports (form_name, month, year, report_date, created_at, file_path)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            report_data['form_name'],
            report_data['month'],
            report_data['year'],
            report_data['report_date'],
            datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
            file_path
        ))

        report_id = cursor.lastrowid

        for answer in answers_list:
            cursor.execute('''
                INSERT INTO answers (report_id, question_text, answer_yes_no, comment, gost_text, quality_text, documents_text)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                report_id,
                answer['question_text'],
                answer['answer_yes_no'],
                answer['comment'],
                answer['gost_text'],
                answer['quality_text'],
                answer.get('documents_text', '')
            ))

        conn.commit()

        if config.DEBUG_MODE:
            print(f"Отчет сохранен в БД с ID: {report_id}")

        return report_id

    except ValueError as e:
        if conn:
            conn.rollback()
        raise Exception(f"{config.ERROR_MESSAGES['validation_error']}: {e}")
    except sqlite3.IntegrityError as e:
        if conn:
            conn.rollback()
        raise Exception(f"{config.ERROR_MESSAGES['validation_error']}: {e}")
    except Exception as e:
        if conn:
            conn.rollback()
        raise Exception(f"{config.ERROR_MESSAGES['db_error']}: {e}")
    finally:
        if conn:
            conn.close()


def get_all_reports():
    """
    Получить список всех отчетов
    Returns: список словарей с данными отчетов
    Raises: Exception при ошибке чтения
    """
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, form_name, month, year, report_date, created_at, file_path
            FROM reports
            ORDER BY created_at DESC
        ''')

        rows = cursor.fetchall()

        reports = []
        for row in rows:
            reports.append({
                'id': row['id'],
                'form_name': row['form_name'],
                'month': row['month'],
                'year': row['year'],
                'report_date': row['report_date'],
                'created_at': row['created_at'],
                'file_path': row['file_path']
            })

        return reports

    except Exception as e:
        raise Exception(f"{config.ERROR_MESSAGES['db_error']}: {e}")
    finally:
        if conn:
            conn.close()


def get_report_by_id(report_id):
    """
    Получить отчет по ID со всеми ответами
    Returns: словарь с данными отчета или None если не найден
    Raises: Exception при ошибке чтения
    """
    conn = None
    try:
        # Валидация ID
        if not isinstance(report_id, int) or report_id <= 0:
            raise ValueError(f"Некорректный ID отчета: {report_id}")

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, form_name, month, year, report_date, created_at, file_path
            FROM reports
            WHERE id = ?
        ''', (report_id,))

        report_row = cursor.fetchone()

        if not report_row:
            if config.DEBUG_MODE:
                print(f"Отчет с ID {report_id} не найден")
            return None

        cursor.execute('''
            SELECT question_text, answer_yes_no, comment, gost_text, quality_text, documents_text
            FROM answers
            WHERE report_id = ?
            ORDER BY id
        ''', (report_id,))

        answer_rows = cursor.fetchall()

        report_data = {
            'id': report_row['id'],
            'form_name': report_row['form_name'],
            'month': report_row['month'],
            'year': report_row['year'],
            'report_date': report_row['report_date'],
            'created_at': report_row['created_at'],
            'file_path': report_row['file_path'],
            'answers': []
        }

        for answer_row in answer_rows:
            report_data['answers'].append({
                'question_text': answer_row['question_text'],
                'answer_yes_no': answer_row['answer_yes_no'],
                'comment': answer_row['comment'],
                'gost_text': answer_row['gost_text'],
                'quality_text': answer_row['quality_text'],
                'documents_text': answer_row['documents_text'] if answer_row['documents_text'] else ''
            })

        return report_data

    except ValueError as e:
        raise Exception(f"{config.ERROR_MESSAGES['validation_error']}: {e}")
    except Exception as e:
        raise Exception(f"{config.ERROR_MESSAGES['db_error']}: {e}")
    finally:
        if conn:
            conn.close()


def delete_report(report_id):
    """
    Удалить отчет из базы данных
    Raises: Exception при ошибке удаления
    """
    conn = None
    try:
        # Валидация ID
        if not isinstance(report_id, int) or report_id <= 0:
            raise ValueError(f"Некорректный ID отчета: {report_id}")

        conn = get_connection()
        cursor = conn.cursor()

        # Проверка существования отчета
        cursor.execute('SELECT id FROM reports WHERE id = ?', (report_id,))
        if not cursor.fetchone():
            raise ValueError(f"Отчет с ID {report_id} не найден")

        # Удаление (ответы удалятся автоматически благодаря ON DELETE CASCADE)
        cursor.execute('DELETE FROM reports WHERE id = ?', (report_id,))

        conn.commit()

        if config.DEBUG_MODE:
            print(f"Отчет {report_id} удален из БД")

    except ValueError as e:
        if conn:
            conn.rollback()
        raise Exception(f"{config.ERROR_MESSAGES['validation_error']}: {e}")
    except Exception as e:
        if conn:
            conn.rollback()
        raise Exception(f"{config.ERROR_MESSAGES['db_error']}: {e}")
    finally:
        if conn:
            conn.close()