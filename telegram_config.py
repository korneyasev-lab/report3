# -*- coding: utf-8 -*-
"""
telegram_config.py — сохранение настроек Telegram в файл
"""

import json
import os

CONFIG_FILE = "telegram_config.json"


def save_telegram_settings(bot_token, chat_id):
    """Сохранить настройки Telegram в файл"""
    settings = {
        "bot_token": bot_token,
        "chat_id": chat_id
    }
    
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=2)


def load_telegram_settings():
    """
    Загрузить настройки Telegram из файла
    
    Returns:
        tuple: (bot_token, chat_id) или (None, None) если файла нет
    """
    if not os.path.exists(CONFIG_FILE):
        return None, None
    
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            settings = json.load(f)
            return settings.get('bot_token'), settings.get('chat_id')
    except:
        return None, None


def has_saved_settings():
    """Проверить есть ли сохранённые настройки"""
    return os.path.exists(CONFIG_FILE)
