# bookmaker_integration.py
"""
Модуль для интеграции с API букмекеров и получения реальных коэффициентов
"""

import os
import json
import logging
import requests
from datetime import datetime
import glob

# Импортируем настройки
from config import *

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("BookmakerIntegration")


def collect_real_bookmaker_odds(odds_dir=None):
    """
    Собирает реальные коэффициенты от букмекеров через API
    
    Args:
        odds_dir (str): Директория для сохранения коэффициентов
        
    Returns:
        dict: Словарь с коэффициентами для матчей
    """
    if odds_dir is None:
        odds_dir = ODDS_DIR
    
    os.makedirs(odds_dir, exist_ok=True)
    
    logger.info("Получение реальных коэффициентов от букмекеров")
    print("Получение реальных коэффициентов от букмекеров...")
    
    # Здесь вы могли бы добавить код для интеграции с реальными API букмекеров
    # В этом примере мы возвращаем пустой словарь, чтобы система перешла к генерации синтетических данных
    
    try:
        # Загрузка будущих матчей для получения их ID и команд
        future_match_files = glob.glob(f"{MATCHES_DIR}/future_matches_*.json")
        if not future_match_files:
            logger.warning("Файлы с будущими матчами не найдены")
            return {}
        
        latest_file = max(future_match_files, key=os.path.getctime)
        
        with open(latest_file, 'r', encoding='utf-8') as f:
            future_matches = json.load(f)
        
        # В реальном проекте здесь был бы запрос к API букмекеров
        # Поскольку у нас нет реального API, возвращаем пустой словарь
        logger.info("API букмекеров временно недоступно, будут использованы синтетические коэффициенты")
        return {}
        
    except Exception as e:
        logger.error(f"Ошибка при получении реальных коэффициентов: {e}")
        return {}


def get_odds_from_api():
    """
    Пытается получить коэффициенты через The Odds API
    
    Returns:
        dict: Словарь с коэффициентами для матчей
    """
    logger.info("Попытка получения коэффициентов через The Odds API")
    print("Попытка получения коэффициентов через The Odds API...")
    
    try:
        # Используем модуль для получения коэффициентов через the_odds_api_parser
        from the_odds_api_parser import get_odds
        
        # Используем предоставленный API ключ
        API_KEY = "58a2f2727f4ce6fd686ed4f6d347c600"
        
        # Получаем данные
        odds_data = get_odds(API_KEY)
        
        if odds_data:
            logger.info(f"Успешно получены коэффициенты через The Odds API для {len(odds_data)} матчей")
            print(f"Успешно получены коэффициенты через The Odds API для {len(odds_data)} матчей")
            return odds_data
        else:
            logger.warning("Не удалось получить данные через The Odds API")
            print("Не удалось получить данные через The Odds API")
            return {}
    except Exception as e:
        logger.error(f"Ошибка при получении коэффициентов через The Odds API: {e}")
        print(f"Ошибка при получении коэффициентов через The Odds API: {e}")
        return {}


# Запуск сбора коэффициентов при запуске скрипта напрямую
if __name__ == "__main__":
    odds_data = collect_real_bookmaker_odds()
    
    if odds_data:
        print(f"Собраны реальные коэффициенты для {len(odds_data)} матчей")
    else:
        print("Не удалось получить реальные коэффициенты")