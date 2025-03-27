import requests
import json
import logging
import os
import traceback
from datetime import datetime

# Импортируем настройки
from config import *

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("TheOddsAPI")

# Словарь для нормализации названий команд
TEAM_MAPPINGS = {
    'Union Berlin': '1. FC Union Berlin',
    'Wolfsburg': 'VfL Wolfsburg',
    'Bayern': 'FC Bayern München',
    'Bayern Munich': 'FC Bayern München',
    'Dortmund': 'Borussia Dortmund',
    'Leverkusen': 'Bayer 04 Leverkusen',
    'Leipzig': 'RB Leipzig',
    'Gladbach': 'Borussia Mönchengladbach',
    'Monchengladbach': 'Borussia Mönchengladbach',
    'Frankfurt': 'Eintracht Frankfurt',
    'Hoffenheim': 'TSG 1899 Hoffenheim',
    'Mainz': '1. FSV Mainz 05',
    'Köln': '1. FC Köln',
    'Bremen': 'SV Werder Bremen',
    'St. Pauli': 'FC St. Pauli',
    'Augsburg': 'FC Augsburg',
    'Kiel': 'Holstein Kiel',
    'Heidenheim': '1. FC Heidenheim 1846'
}

def normalize_team_name(team_name):
    """Нормализует название команды"""
    return TEAM_MAPPINGS.get(team_name, team_name)

def get_odds(api_key=ODDS_API_KEY, 
             sport=ODDS_SPORT, 
             regions=ODDS_REGIONS, 
             markets=ODDS_MARKETS):
    """
    Получает коэффициенты через The Odds API с расширенной обработкой
    """
    logger.info(f"НАЧАЛО ЗАПРОСА: sport={sport}, regions={regions}, markets={markets}")
    logger.info(f"API Key: {api_key[:5]}...{api_key[-5:]}")
    
    url = f"{ODDS_API_BASE_URL}/{sport}/odds"
    
    params = {
        "apiKey": api_key,
        "regions": regions,
        "markets": markets,
        "oddsFormat": ODDS_FORMAT
    }
    
    try:
        # Выполнение запроса с таймаутом
        response = requests.get(url, params=params, timeout=10)
        
        logger.info(f"Статус ответа: {response.status_code}")
        logger.info(f"URL запроса: {response.url}")
        
        response.raise_for_status()
        
        # Парсинг JSON
        odds_data = response.json()
        logger.info(f"Получены коэффициенты для {len(odds_data)} матчей")
        
        # Сохранение полного ответа
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        full_response_file = os.path.join(ODDS_DIR, f"the_odds_api_full_{timestamp}.json")
        
        with open(full_response_file, 'w', encoding='utf-8') as f:
            json.dump(odds_data, f, indent=4, ensure_ascii=False)
        
        # Преобразование данных
        result_data = {}
        
        for match in odds_data:
            try:
                # Нормализация названий
                home_team = normalize_team_name(match.get('home_team', ''))
                away_team = normalize_team_name(match.get('away_team', ''))
                
                # Получение коэффициентов
                bookmakers = match.get('bookmakers', [])
                if not bookmakers:
                    continue
                
                bookmaker = bookmakers[0]
                h2h_market = next((m for m in bookmaker.get('markets', []) if m.get('key') == 'h2h'), None)
                
                if not h2h_market:
                    continue
                
                # Извлечение коэффициентов
                odds = {}
                for outcome in h2h_market.get('outcomes', []):
                    name = normalize_team_name(outcome.get('name', ''))
                    price = outcome.get('price')
                    
                    if name == home_team:
                        odds['1'] = price
                    elif name == away_team:
                        odds['2'] = price
                    elif name == 'Draw':
                        odds['X'] = price
                
                # Проверка полноты данных
                if len(odds) != 3:
                    continue
                
                match_id = match.get('id')
                result_data[match_id] = {
                    'match_id': match_id,
                    'home_team': home_team,
                    'away_team': away_team,
                    'date': match.get('commence_time', ''),
                    'odds': odds,
                    'timestamp': datetime.now().isoformat(),
                    'source': 'the_odds_api'
                }
                
                # Сохранение коэффициентов каждого матча
                match_odds_file = os.path.join(ODDS_DIR, f"odds_{match_id}.json")
                with open(match_odds_file, 'w', encoding='utf-8') as f:
                    json.dump(result_data[match_id], f, indent=4, ensure_ascii=False)
            
            except Exception as match_error:
                logger.error(f"Ошибка обработки матча: {match_error}")
                logger.error(traceback.format_exc())
        
        logger.info(f"Обработано матчей: {len(result_data)}")
        return result_data
    
    except requests.exceptions.RequestException as req_err:
        logger.error(f"Ошибка запроса: {req_err}")
        logger.error(traceback.format_exc())
        return {}
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {e}")
        logger.error(traceback.format_exc())
        return {}

# Запуск при прямом запуске скрипта
if __name__ == "__main__":
    odds_data = get_odds()
    
    if odds_data:
        print(f"Получены коэффициенты для {len(odds_data)} матчей")
        
        # Вывод первых 3 матчей для примера
        for match_id, match_data in list(odds_data.items())[:3]:
            print(f"Матч: {match_data['home_team']} - {match_data['away_team']}")
            print(f"Коэффициенты: {match_data['odds']}\n")
    else:
        print("Не удалось получить коэффициенты")