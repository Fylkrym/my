# config.py
"""
Файл с настройками проекта для использования OpenLigaDB API
"""

# API для OpenLigaDB (бесплатный, без ключа)
OPENLIGA_API_URL = "https://api.openligadb.de/getmatchdata"

# Настройки для Бундеслиги
LEAGUE_NAME = "bl1"  # Сокращение для Bundesliga 1
CURRENT_SEASON = "2024"  # Текущий сезон

# Настройки для анализа
MIN_ODDS_VALUE = 1.1  # Минимальное значение для коэффициента
MAX_ODDS_VALUE = 10.0  # Максимальное значение для коэффициента
VALUE_THRESHOLD = 0.1  # Минимальный порог ценности ставки (10%)

# Настройки для улучшенной модели прогнозирования
CONSISTENCY_CHECK = True  # Включить проверку согласованности
MIN_CONSISTENT_VALUE = 0.15  # Минимальная ценность для согласованных ставок
FORCE_CONSISTENT_BETS = True  # Принудительно выбирать только согласованные ставки
TOP_TEAMS_BOOST = 1.2  # Коэффициент усиления для топовых команд
BOTTOM_TEAMS_PENALTY = 0.8  # Штраф для аутсайдеров
BAYERN_HOME_BOOST = 1.3  # Дополнительное усиление для Баварии дома

# Настройки для модели прогнозирования
USE_HEAD_TO_HEAD = True  # Использовать историю личных встреч
USE_EXTENDED_MARKETS = True  # Использовать расширенные рынки ставок (тоталы, форы)
MAX_H2H_MATCHES = 10  # Максимальное количество матчей для анализа личных встреч
H2H_WEIGHT = 0.2  # Вес истории личных встреч в прогнозе

# Настройки для управления банкроллом
BANK_INITIAL = 1000  # Начальный банк (в рублях/долларах/евро)
BET_SIZE_PERCENT = 2  # Размер ставки (% от банка)
MAX_DAILY_BETS = 5  # Максимальное количество ставок в день
MIN_VALUE_FOR_BET = 0.15  # Минимальная ценность для размещения ставки (15%)
VALUE_BASED_SIZING = True  # Регулировать размер ставки в зависимости от ценности

# Пути к файлам данных
DATA_DIR = "data"
MATCHES_DIR = f"{DATA_DIR}/matches"
ODDS_DIR = f"{DATA_DIR}/odds"
PREDICTIONS_DIR = f"{DATA_DIR}/predictions"
REPORTS_DIR = f"{DATA_DIR}/reports"
CHARTS_DIR = f"{DATA_DIR}/charts"

# Настройки для Telegram уведомлений
TELEGRAM_NOTIFICATIONS = True  # Включить/выключить уведомления в Telegram
TELEGRAM_BOT_TOKEN = "7544739929:AAEGvj2WqaglYh3xrH1Ec_djcfiwPQHs2VY"  # Токен вашего Telegram бота
TELEGRAM_CHAT_ID = "-4767450455"  # ID чата для отправки уведомлений

# Настройки для визуализации
VISUALIZATION = True  # Включить визуализацию результатов

# Настройки для логирования
LOG_LEVEL = "INFO"
LOG_FILE = "bundesliga_predictor.log"