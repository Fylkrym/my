# the_odds_api_parser.py
"""
Модуль для получения коэффициентов через The Odds API
"""

import requests
import json
import logging
import os
from datetime import datetime

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
logger = logging.getLogger("TheOddsAPI")


def get_odds(api_key, sport="soccer_germany_bundesliga", regions="eu", markets="h2h"):
    """
    Получает коэффициенты через The Odds API
    
    Args:
        api_key (str): API ключ для The Odds API
        sport (str): Идентификатор спорта
        regions (str): Регионы для коэффициентов (eu, uk, us)
        markets (str): Типы рынков (h2h - 1X2, totals - тоталы, spreads - форы)
        
    Returns:
        dict: Словарь с коэффициентами
    """
    logger.info(f"Запрос коэффициентов через The Odds API для {sport}")
    
    url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds"
    params = {
        "apiKey": api_key,
        "regions": regions,
        "markets": markets,
        "oddsFormat": "decimal"
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        odds_data = response.json()
        logger.info(f"Получены коэффициенты для {len(odds_data)} матчей")
        
        # Сохраняем полученные данные
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        odds_file = f"{ODDS_DIR}/the_odds_api_{timestamp}.json"
        
        os.makedirs(ODDS_DIR, exist_ok=True)
        
        with open(odds_file, 'w', encoding='utf-8') as f:
            json.dump(odds_data, f, indent=4, ensure_ascii=False)
        
        logger.info(f"Данные сохранены в {odds_file}")
        
        # Преобразуем данные в формат, используемый нашей системой
        result_data = {}
        
        for match in odds_data:
            match_id = match.get('id')
            home_team = match.get('home_team')
            away_team = match.get('away_team')
            
            # Обрабатываем коэффициенты
            bookmakers = match.get('bookmakers', [])
            if not bookmakers:
                continue
            
            # Берем первого букмекера в списке
            bookmaker = bookmakers[0]
            markets = bookmaker.get('markets', [])
            
            # Получаем коэффициенты 1X2
            h2h_market = next((m for m in markets if m.get('key') == 'h2h'), None)
            if not h2h_market:
                continue
            
            outcomes = h2h_market.get('outcomes', [])
            
            # Создаем словарь с коэффициентами
            odds = {}
            
            for outcome in outcomes:
                name = outcome.get('name')
                price = outcome.get('price')
                
                if name == home_team:
                    odds['1'] = price
                elif name == away_team:
                    odds['2'] = price
                elif name == 'Draw':
                    odds['X'] = price
            
            # Если не все коэффициенты найдены, пропускаем
            if '1' not in odds or 'X' not in odds or '2' not in odds:
                continue
            
            # Создаем запись о матче
            result_data[match_id] = {
                'match_id': match_id,
                'home_team': home_team,
                'away_team': away_team,
                'date': match.get('commence_time', ''),
                'odds': odds,
                'timestamp': datetime.now().isoformat(),
                'source': 'the_odds_api'
            }
            
            # Сохраняем коэффициенты для каждого матча
            match_odds_file = f"{ODDS_DIR}/odds_{match_id}.json"
            with open(match_odds_file, 'w', encoding='utf-8') as f:
                json.dump(result_data[match_id], f, indent=4, ensure_ascii=False)
        
        return result_data
        
    except Exception as e:
        logger.error(f"Ошибка при запросе к The Odds API: {e}")
        return {}


# Запуск сбора коэффициентов при запуске скрипта напрямую
if __name__ == "__main__":
    # Рабочий API ключ
    API_KEY = "58a2f2727f4ce6fd686ed4f6d347c600"  # Действующий ключ для the-odds-api
    
    odds_data = get_odds(API_KEY)
    
    if odds_data:
        print(f"Получены коэффициенты для {len(odds_data)} матчей")
    else:
        print("Не удалось получить коэффициенты")