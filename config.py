# config.py
"""
Файл конфигурации для системы прогнозирования ставок на Бундеслигу
с использованием The Odds API
"""

import os
import logging

# Настройки The Odds API
ODDS_API_KEY = "58a2f2727f4ce6fd686ed4f6d347c600"
ODDS_API_BASE_URL = "https://api.the-odds-api.com/v4/sports"
ODDS_SPORT = "soccer_germany_bundesliga"
ODDS_REGIONS = "eu,uk"
ODDS_MARKETS = "h2h"
ODDS_FORMAT = "decimal"

# Пути к директориям
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
MATCHES_DIR = os.path.join(DATA_DIR, 'matches')
ODDS_DIR = os.path.join(DATA_DIR, 'odds')
PREDICTIONS_DIR = os.path.join(DATA_DIR, 'predictions')
REPORTS_DIR = os.path.join(DATA_DIR, 'reports')
CHARTS_DIR = os.path.join(DATA_DIR, 'charts')

# Функция создания директорий
def ensure_directories_exist():
    """
    Создает все необходимые директории для работы системы
    """
    directories = [
        DATA_DIR, 
        MATCHES_DIR, 
        ODDS_DIR, 
        PREDICTIONS_DIR, 
        REPORTS_DIR, 
        CHARTS_DIR
    ]
    
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            if not os.path.isdir(directory):
                raise ValueError(f"{directory} не является директорией")
            if not os.access(directory, os.W_OK):
                raise PermissionError(f"Нет прав на запись в {directory}")
        except Exception as e:
            print(f"ОШИБКА при создании директории {directory}: {e}")
            raise

# Создаем директории при загрузке модуля
ensure_directories_exist()

# Настройки для анализа и прогнозирования
MIN_ODDS_VALUE = 1.1  # Минимальное значение для коэффициента
MAX_ODDS_VALUE = 10.0  # Максимальное значение для коэффициента
VALUE_THRESHOLD = 0.15  # Порог ценности ставки (15%)

# Настройки для прогнозирования
CONSISTENCY_CHECK = True  # Проверка согласованности прогноза
MIN_CONSISTENT_VALUE = 0.15  # Минимальная ценность для согласованных ставок
FORCE_CONSISTENT_BETS = True  # Выбирать только согласованные ставки

# Настройки для управления банкроллом
BANK_INITIAL = 1000  # Начальный банк
BET_SIZE_PERCENT = 2  # Размер ставки в % от банка
MAX_DAILY_BETS = 5  # Максимальное количество ставок в день
MIN_VALUE_FOR_BET = 0.15  # Минимальная ценность для ставки
VALUE_BASED_SIZING = True  # Регулировать размер ставки в зависимости от ценности

# Настройки Telegram
TELEGRAM_NOTIFICATIONS = True
TELEGRAM_BOT_TOKEN = "7544739929:AAEGvj2WqaglYh3xrH1Ec_djcfiwPQHs2VY"
TELEGRAM_CHAT_ID = "-4767450455"

# Настройки логирования
LOG_LEVEL = "INFO"
LOG_FILE = os.path.join(BASE_DIR, 'bundesliga_predictor.log')

# Настройки визуализации
VISUALIZATION = True

# Текущий сезон
CURRENT_SEASON = "2024"