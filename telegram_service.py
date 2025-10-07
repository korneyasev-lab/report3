# -*- coding: utf-8 -*-
"""
telegram_service.py — отправка отчётов в Telegram
"""

import json
import ssl
from urllib import request, error, parse
from database import get_report_by_id
import config


class TelegramService:
    """Сервис для отправки отчётов в Telegram"""

    def __init__(self):
        """Инициализация с проверкой настроек"""
        self.bot_token = getattr(config, 'TELEGRAM_BOT_TOKEN', '')
        self.chat_id = getattr(config, 'TELEGRAM_CHAT_ID', '')
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"

    def is_configured(self):
        """Проверка что токен и chat_id заполнены"""
        return bool(self.bot_token.strip() and self.chat_id.strip())

    def send_report(self, report_id):
        """
        Отправить отчёт в Telegram

        Args:
            report_id: ID отчёта из базы данных

        Returns:
            tuple: (success: bool, message: str)
        """
        # Проверка настроек
        if not self.is_configured():
            return False, "Telegram не настроен. Заполните токен бота и chat_id в настройках."

        try:
            # Получаем данные отчёта из БД
            report_data = get_report_by_id(report_id)

            if not report_data:
                return False, f"Отчёт с ID {report_id} не найден в базе данных"

            # Форматируем сообщение
            message_text = self._format_message(report_data)

            # Проверяем длину (лимит Telegram 4096 символов)
            if len(message_text) > 4096:
                # Если слишком длинное, отправляем частями
                return self._send_long_message(message_text)

            # Отправляем в Telegram
            success = self._send_to_telegram(message_text)

            if success:
                return True, "✅ Отчёт успешно отправлен в Telegram"
            else:
                return False, "❌ Ошибка при отправке в Telegram"

        except Exception as e:
            return False, f"Ошибка: {str(e)}"

    def _format_message(self, report_data):
        """
        Форматировать отчёт в красивый текст для Telegram

        Args:
            report_data: словарь с данными отчёта из БД

        Returns:
            str: отформатированное сообщение
        """
        lines = []

        # Заголовок
        header = f"📋 {report_data['form_name']} - {report_data['month']} {report_data['year']}"
        lines.append(header)
        lines.append(f"📅 Дата отчёта: {report_data['report_date']}")
        lines.append(f"🕐 Создан: {report_data['created_at']}")
        lines.append("")
        lines.append("─" * 40)
        lines.append("")

        # Вопросы и ответы
        for i, answer in enumerate(report_data['answers'], 1):
            question = answer['question_text']
            ans = answer['answer_yes_no']
            comment = answer.get('comment', '').strip()

            # Номер и вопрос
            lines.append(f"{i}. {question}")

            # Ответ с эмодзи
            if ans == "Да":
                lines.append(f"✅ Ответ: Да")
            elif ans == "Нет":
                lines.append(f"❌ Ответ: Нет")
            else:
                lines.append(f"▪️ Ответ: {ans}")

            # Комментарий если есть
            if comment:
                lines.append(f"💬 {comment}")

            lines.append("")

        lines.append("─" * 40)
        lines.append(f"📊 Всего вопросов: {len(report_data['answers'])}")

        return "\n".join(lines)

    def _send_to_telegram(self, text):
        """
        Отправить текст в Telegram через Bot API

        Args:
            text: текст сообщения

        Returns:
            bool: True если успешно, False если ошибка
        """
        try:
            # Подготовка данных
            data = {
                'chat_id': self.chat_id,
                'text': text
            }

            # Кодируем данные
            data_encoded = parse.urlencode(data).encode('utf-8')

            # Создаём запрос
            req = request.Request(self.api_url, data=data_encoded, method='POST')

            # SSL context для обхода проверки сертификата (для macOS)
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

            # Отправляем
            with request.urlopen(req, timeout=15, context=ssl_context) as response:
                result = json.loads(response.read().decode('utf-8'))

                if config.DEBUG_MODE:
                    print(f"Telegram API response: {result}")

                return result.get('ok', False)

        except error.HTTPError as e:
            error_body = e.read().decode('utf-8') if e.fp else ""
            if config.DEBUG_MODE:
                print(f"HTTP ошибка {e.code}: {e.reason}")
                print(f"Детали: {error_body}")
            return False
        except error.URLError as e:
            if config.DEBUG_MODE:
                print(f"Ошибка сети: {e.reason}")
            return False
        except Exception as e:
            if config.DEBUG_MODE:
                print(f"Неизвестная ошибка: {type(e).__name__}: {e}")
            return False

    def _send_long_message(self, text):
        """
        Отправить длинное сообщение частями

        Args:
            text: длинный текст

        Returns:
            tuple: (success: bool, message: str)
        """
        # Разбиваем по 4000 символов (с запасом)
        max_length = 4000
        parts = []

        while text:
            if len(text) <= max_length:
                parts.append(text)
                break

            # Ищем последний перенос строки в пределах лимита
            split_pos = text.rfind('\n', 0, max_length)
            if split_pos == -1:
                split_pos = max_length

            parts.append(text[:split_pos])
            text = text[split_pos:].lstrip()

        # Отправляем части
        for i, part in enumerate(parts, 1):
            header = f"[Часть {i}/{len(parts)}]\n\n" if len(parts) > 1 else ""
            success = self._send_to_telegram(header + part)

            if not success:
                return False, f"Ошибка при отправке части {i} из {len(parts)}"

        return True, f"✅ Отчёт отправлен в Telegram ({len(parts)} сообщений)"

    def test_connection(self):
        """
        Проверить соединение с Telegram (отправить тестовое сообщение)

        Returns:
            tuple: (success: bool, message: str)
        """
        if not self.is_configured():
            return False, "Заполните токен и chat_id"

        test_message = "🔔 Тестовое сообщение от системы автоматизации отчётов"

        try:
            # Подготовка данных
            data = {
                'chat_id': self.chat_id,
                'text': test_message
            }

            # Кодируем данные
            data_encoded = parse.urlencode(data).encode('utf-8')

            # Создаём запрос
            req = request.Request(self.api_url, data=data_encoded, method='POST')

            # SSL context для обхода проверки сертификата (для macOS)
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

            # Отправляем
            with request.urlopen(req, timeout=15, context=ssl_context) as response:
                result = json.loads(response.read().decode('utf-8'))

                if result.get('ok'):
                    return True, "✅ Соединение установлено! Тестовое сообщение отправлено."
                else:
                    error_desc = result.get('description', 'Неизвестная ошибка')
                    return False, f"❌ Telegram API вернул ошибку: {error_desc}"

        except error.HTTPError as e:
            try:
                error_body = json.loads(e.read().decode('utf-8'))
                error_desc = error_body.get('description', str(e.reason))
            except:
                error_desc = str(e.reason)

            if e.code == 401:
                return False, f"❌ Неверный токен бота.\n\nПолучите новый токен у @BotFather"
            elif e.code == 400:
                return False, f"❌ Неверный Chat ID: {self.chat_id}\n\nПроверьте Chat ID у @userinfobot"
            else:
                return False, f"❌ HTTP ошибка {e.code}: {error_desc}"

        except error.URLError as e:
            return False, f"❌ Ошибка сети: {e.reason}\n\nПроверьте интернет-соединение"
        except Exception as e:
            return False, f"❌ Ошибка: {type(e).__name__}: {str(e)}"


# Вспомогательные функции для GUI
def get_telegram_service():
    """Получить экземпляр TelegramService"""
    return TelegramService()


def validate_settings(bot_token, chat_id):
    """
    Валидация настроек Telegram

    Args:
        bot_token: токен бота
        chat_id: ID чата

    Returns:
        tuple: (valid: bool, error_message: str or None)
    """
    if not bot_token or not bot_token.strip():
        return False, "Токен бота не может быть пустым"

    if not chat_id or not chat_id.strip():
        return False, "Chat ID не может быть пустым"

    # Проверка формата токена (примерно)
    if ':' not in bot_token:
        return False, "Неверный формат токена. Должен быть формат: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz"

    # Проверка что chat_id числовой или начинается с -
    chat_id_clean = chat_id.strip()
    if not (chat_id_clean.lstrip('-').isdigit()):
        return False, "Chat ID должен быть числом (например: 123456789 или -123456789)"

    return True, None