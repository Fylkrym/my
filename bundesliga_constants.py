# Константы для сборщика данных Бундеслиги

# Название лиги для API OpenLigaDB
LEAGUE_NAME = "bl1"  # bl1 - код для Бундеслиги

# Текущий сезон
CURRENT_SEASON = 2024  # Сезон 2024/2025

# Базовый URL для API OpenLigaDB
OPENLIGA_API_URL = "https://api.openligadb.de"

# URL для получения команд
TEAMS_URL = f"{OPENLIGA_API_URL}/getavailableteams/{LEAGUE_NAME}/{CURRENT_SEASON}"

# URL для получения матчей
MATCHES_URL = f"{OPENLIGA_API_URL}/getmatchdata/{LEAGUE_NAME}/{CURRENT_SEASON}"

# Путь к локальной папке с данными
DATA_DIR = "C:\\Users\\Fylkrym\\Desktop\\nextstep\\data"

# Настройки логирования
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"{DATA_DIR}/bundesliga_predictor.log"),
        logging.StreamHandler()
    ]
)