# Скрипт для проверки The Odds API для Бундеслиги
import requests
import json
from datetime import datetime

# Константы
API_KEY = "58a2f2727f4ce6fd686ed4f6d347c600"
BASE_URL = "https://api.the-odds-api.com/v4/sports"
SPORT = "soccer_germany_bundesliga"  # Немецкая Бундеслига
REGIONS = "eu"
MARKETS = "h2h"  # 1X2
ODDS_FORMAT = "decimal"

def check_bundesliga_odds_api():
    """Проверяет The Odds API для получения коэффициентов на матчи Бундеслиги"""
    
    url = f"{BASE_URL}/{SPORT}/odds"
    
    params = {
        "apiKey": API_KEY,
        "regions": REGIONS,
        "markets": MARKETS,
        "oddsFormat": ODDS_FORMAT
    }
    
    print(f"Отправка запроса к API для Бундеслиги: {url}")
    print(f"Параметры: {params}")
    
    try:
        # Выполнение запроса
        response = requests.get(url, params=params, timeout=10)
        
        print(f"Статус ответа: {response.status_code}")
        
        if response.status_code == 200:
            # Успешный ответ
            data = response.json()
            print(f"Получено матчей Бундеслиги: {len(data)}")
            
            # Выведем список всех доступных матчей
            print("\nДоступные матчи Бундеслиги:")
            for i, match in enumerate(data, 1):
                home_team = match.get('home_team', '')
                away_team = match.get('away_team', '')
                commence_time = match.get('commence_time', '')
                
                # Преобразуем время в более читаемый формат
                try:
                    dt = datetime.fromisoformat(commence_time.replace('Z', '+00:00'))
                    formatted_time = dt.strftime("%d.%m.%Y %H:%M")
                except:
                    formatted_time = commence_time
                
                print(f"{i}. {home_team} vs {away_team} ({formatted_time})")
                
                # Выведем коэффициенты для первого букмекера
                bookmakers = match.get('bookmakers', [])
                if bookmakers:
                    bookmaker = bookmakers[0]
                    print(f"   Букмекер: {bookmaker['title']}")
                    
                    for market in bookmaker.get('markets', []):
                        if market['key'] == 'h2h':
                            print(f"   Коэффициенты (1X2):")
                            for outcome in market.get('outcomes', []):
                                name = outcome['name']
                                price = outcome['price']
                                
                                # Преобразуем имена исходов в формат 1X2
                                if name == home_team:
                                    label = "1"
                                elif name == away_team:
                                    label = "2"
                                elif name == "Draw":
                                    label = "X"
                                else:
                                    label = name
                                
                                print(f"     {label}: {price}")
            
            # Сохраним все данные в JSON
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"bundesliga_odds_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            
            print(f"\nРезультаты сохранены в файл: {filename}")
            
            # Проверим, есть ли коэффициенты на матчи из файлов в your_data
            check_matches_with_known_ids(data)
            
            return data
        
        else:
            print(f"Ошибка запроса: {response.status_code}")
            print(response.text)
            return None
    
    except Exception as e:
        print(f"Произошла ошибка: {e}")
        return None

def check_matches_with_known_ids(api_data):
    """
    Проверяет, есть ли в API данные о матчах с известными ID из ваших данных
    """
    # ID матчей из ваших JSON файлов
    known_match_ids = [
        "270bd497305946dc86e005935ca9c8ea",  # FC Bayern München vs FC St. Pauli
        "05a7fada857a9d4374f36392fa317c27",  # Holstein Kiel vs Werder Bremen
        "73b7f2ef877dd65079d4b77b552873c7",  # Werder Bremen vs Eintracht Frankfurt
        "4f44d53966b10aaafaeb3805f174c32b",  # Borussia Dortmund vs FSV Mainz 05
        "774e12e31a16c24aa1f1296d2cb29ac1",  # FC Augsburg vs FC Bayern München
        "2d1de07d7ac740c1c6d5c8cb66ed0e77",  # 1. FC Union Berlin vs VfL Wolfsburg
        "3babe307bf679c8f45ac5c237561a6b8"   # FSV Mainz 05 vs Holstein Kiel
    ]
    
    # Соответствие команд
    team_mappings = {
        "FC Bayern Munich": "FC Bayern München",
        "Bayern Munich": "FC Bayern München",
        "St Pauli": "FC St. Pauli",
        "St. Pauli": "FC St. Pauli",
        "Werder Bremen": "Werder Bremen",
        "Holstein Kiel": "Holstein Kiel",
        "Eintracht Frankfurt": "Eintracht Frankfurt",
        "Borussia Dortmund": "Borussia Dortmund",
        "Mainz": "FSV Mainz 05",
        "Mainz 05": "FSV Mainz 05",
        "FC Augsburg": "FC Augsburg",
        "Augsburg": "FC Augsburg",
        "Union Berlin": "1. FC Union Berlin",
        "Wolfsburg": "VfL Wolfsburg"
    }
    
    print("\n" + "="*50)
    print("ПРОВЕРКА МАТЧЕЙ С ИЗВЕСТНЫМИ ID")
    print("="*50)
    
    # Создадим список пар команд из API данных
    api_matches = []
    for match in api_data:
        home_team = match.get('home_team', '')
        away_team = match.get('away_team', '')
        api_matches.append((home_team, away_team))
    
    # Проверим каждый известный матч
    matches_found = 0
    
    for match_id in known_match_ids:
        # Попробуем найти информацию о матче из локальных данных
        try:
            with open(f"data/odds/odds_{match_id}.json", 'r', encoding='utf-8') as f:
                match_data = json.load(f)
            
            home_team = match_data.get('home_team', '')
            away_team = match_data.get('away_team', '')
            match_date = match_data.get('date', '')
            
            # Выводим информацию о матче из локальных данных
            print(f"\nМатч ID: {match_id}")
            print(f"Локальные данные: {home_team} vs {away_team} ({match_date})")
            
            # Проверяем, есть ли этот матч в данных API
            match_found = False
            
            for api_home, api_away in api_matches:
                # Проверяем прямое соответствие
                if (api_home == home_team and api_away == away_team) or \
                   (api_home == away_team and api_away == home_team):
                    match_found = True
                    print(f"✅ НАЙДЕНО ПРЯМОЕ СООТВЕТСТВИЕ: {api_home} vs {api_away}")
                    break
                
                # Проверяем соответствие через маппинг
                normalized_api_home = team_mappings.get(api_home, api_home)
                normalized_api_away = team_mappings.get(api_away, api_away)
                
                if (normalized_api_home == home_team and normalized_api_away == away_team) or \
                   (normalized_api_home == away_team and normalized_api_away == home_team):
                    match_found = True
                    print(f"✅ НАЙДЕНО СООТВЕТСТВИЕ ЧЕРЕЗ МАППИНГ: {api_home} ({normalized_api_home}) vs {api_away} ({normalized_api_away})")
                    break
            
            if not match_found:
                print(f"❌ НЕ НАЙДЕНО СООТВЕТСТВИЕ В API")
            else:
                matches_found += 1
        
        except FileNotFoundError:
            print(f"\nМатч ID: {match_id}")
            print(f"❌ Файл с данными не найден: data/odds/odds_{match_id}.json")
        except Exception as e:
            print(f"\nМатч ID: {match_id}")
            print(f"❌ Ошибка при обработке: {e}")
    
    print("\n" + "="*50)
    print(f"ИТОГО: Найдено соответствий - {matches_found} из {len(known_match_ids)}")
    print("="*50)

# Выполняем проверку
if __name__ == "__main__":
    result = check_bundesliga_odds_api()