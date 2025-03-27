# Интеграция коэффициентов из The Odds API в систему прогнозирования
import requests
import json
import os
import sys
from datetime import datetime

# Константы
API_KEY = "58a2f2727f4ce6fd686ed4f6d347c600"
BASE_URL = "https://api.the-odds-api.com/v4/sports"
SPORT = "soccer_germany_bundesliga"  # Немецкая Бундеслига
REGIONS = "eu"
MARKETS = "h2h"  # 1X2
ODDS_FORMAT = "decimal"

# Определяем путь к директории для хранения коэффициентов
# Используем путь из конфигурации или создаем новую директорию
try:
    # Пытаемся импортировать конфигурацию
    sys.path.append('.')
    from config import ODDS_DIR
    ODDS_DIRECTORY = ODDS_DIR
except ImportError:
    # Если не удалось импортировать, используем текущую директорию
    ODDS_DIRECTORY = os.path.join(os.getcwd(), 'data', 'odds')

# Словарь маппинга названий команд
TEAM_MAPPINGS = {
    "Bayern Munich": "FC Bayern München",
    "Bayern": "FC Bayern München",
    "FC Bayern Munich": "FC Bayern München",
    "FC St. Pauli": "FC St. Pauli",
    "St Pauli": "FC St. Pauli",
    "St. Pauli": "FC St. Pauli",
    "Werder Bremen": "Werder Bremen",
    "SV Werder Bremen": "Werder Bremen",
    "Holstein Kiel": "Holstein Kiel",
    "Kiel": "Holstein Kiel",
    "Eintracht Frankfurt": "Eintracht Frankfurt",
    "Frankfurt": "Eintracht Frankfurt",
    "Borussia Dortmund": "Borussia Dortmund",
    "Dortmund": "Borussia Dortmund",
    "FSV Mainz 05": "FSV Mainz 05",
    "Mainz": "FSV Mainz 05",
    "Mainz 05": "FSV Mainz 05",
    "Augsburg": "FC Augsburg",
    "FC Augsburg": "FC Augsburg",
    "Union Berlin": "1. FC Union Berlin",
    "1. FC Union Berlin": "1. FC Union Berlin",
    "VfL Wolfsburg": "VfL Wolfsburg",
    "Wolfsburg": "VfL Wolfsburg",
    "Bayer Leverkusen": "Bayer 04 Leverkusen",
    "Leverkusen": "Bayer 04 Leverkusen",
    "VfL Bochum": "VfL Bochum",
    "Bochum": "VfL Bochum",
    "1. FC Heidenheim": "1. FC Heidenheim 1846",
    "FC Heidenheim": "1. FC Heidenheim 1846",
    "Heidenheim": "1. FC Heidenheim 1846",
    "TSG Hoffenheim": "TSG 1899 Hoffenheim",
    "Hoffenheim": "TSG 1899 Hoffenheim",
    "Borussia Monchengladbach": "Borussia Mönchengladbach",
    "Borussia Mönchengladbach": "Borussia Mönchengladbach",
    "Gladbach": "Borussia Mönchengladbach",
    "VfB Stuttgart": "VfB Stuttgart",
    "Stuttgart": "VfB Stuttgart",
    "SC Freiburg": "SC Freiburg",
    "Freiburg": "SC Freiburg",
    "RB Leipzig": "RB Leipzig",
    "Leipzig": "RB Leipzig"
}

# Для создания хэшей матчей
import hashlib

def normalize_team_name(team_name):
    """
    Нормализует название команды с использованием словаря маппинга
    """
    return TEAM_MAPPINGS.get(team_name, team_name)

def generate_match_id(home_team, away_team, match_date):
    """
    Генерирует ID матча в формате MD5 хэша
    """
    # Нормализуем названия команд
    normalized_home = normalize_team_name(home_team)
    normalized_away = normalize_team_name(away_team)
    
    # Создаем строку для хэширования
    match_string = f"{normalized_home}_{normalized_away}_{match_date}"
    
    # Генерируем MD5 хэш
    match_id = hashlib.md5(match_string.encode('utf-8')).hexdigest()
    
    return match_id

def fetch_and_save_odds():
    """
    Получает коэффициенты из API и сохраняет их в правильном формате
    """
    # Убедимся, что директория существует
    os.makedirs(ODDS_DIRECTORY, exist_ok=True)
    
    # Запрос к API
    url = f"{BASE_URL}/{SPORT}/odds"
    
    params = {
        "apiKey": API_KEY,
        "regions": REGIONS,
        "markets": MARKETS,
        "oddsFormat": ODDS_FORMAT
    }
    
    print(f"Запрос к API для Бундеслиги: {url}")
    
    try:
        # Выполнение запроса
        response = requests.get(url, params=params, timeout=10)
        
        print(f"Статус ответа: {response.status_code}")
        
        if response.status_code == 200:
            # Успешный ответ
            matches_data = response.json()
            print(f"Получено матчей Бундеслиги: {len(matches_data)}")
            
            # Сохраняем полный ответ API
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            full_response_file = os.path.join(ODDS_DIRECTORY, f"odds_api_response_{timestamp}.json")
            
            with open(full_response_file, 'w', encoding='utf-8') as f:
                json.dump(matches_data, f, indent=4, ensure_ascii=False)
            
            print(f"Полный ответ API сохранен в: {full_response_file}")
            
            # Обрабатываем каждый матч
            processed_matches = 0
            odds_files_created = 0
            
            for match in matches_data:
                try:
                    # Получаем информацию о матче
                    home_team = match.get('home_team', '')
                    away_team = match.get('away_team', '')
                    commence_time = match.get('commence_time', '')
                    
                    # Нормализуем названия команд
                    normalized_home = normalize_team_name(home_team)
                    normalized_away = normalize_team_name(away_team)
                    
                    # Генерируем ID матча
                    match_id = generate_match_id(home_team, away_team, commence_time)
                    # Для проверки также генерируем ID с нормализованными названиями
                    alt_match_id = generate_match_id(normalized_home, normalized_away, commence_time)
                    
                    # Проверяем существующие файлы с ID
                    existing_files = os.listdir(ODDS_DIRECTORY)
                    id_found = False
                    filename = None
                    
                    for file in existing_files:
                        if file.startswith(f"odds_") and file.endswith(".json"):
                            # Извлекаем ID из имени файла
                            file_id = file[5:-5]  # Отрезаем "odds_" и ".json"
                            
                            if file_id == match_id or file_id == alt_match_id:
                                id_found = True
                                filename = file
                                match_id = file_id  # Используем ID из файла для перезаписи
                                break
                    
                    # Если файл с таким ID не найден, используем сгенерированный ID
                    if not id_found:
                        filename = f"odds_{match_id}.json"
                    
                    # Получаем коэффициенты из букмекеров
                    odds_1x2 = {'1': 0, 'X': 0, '2': 0}
                    bookmakers_processed = 0
                    
                    if 'bookmakers' in match and match['bookmakers']:
                        for bookmaker in match['bookmakers']:
                            for market in bookmaker.get('markets', []):
                                if market['key'] == 'h2h':
                                    for outcome in market.get('outcomes', []):
                                        name = outcome['name']
                                        price = outcome['price']
                                        
                                        if name == home_team:
                                            odds_1x2['1'] = price
                                        elif name == away_team:
                                            odds_1x2['2'] = price
                                        elif name == "Draw":
                                            odds_1x2['X'] = price
                                    
                                    bookmakers_processed += 1
                                    break  # Достаточно одного рынка h2h
                            
                            if bookmakers_processed >= 1:
                                break  # Достаточно одного букмекера
                    
                    # Проверяем, что все коэффициенты получены
                    if odds_1x2['1'] > 0 and odds_1x2['X'] > 0 and odds_1x2['2'] > 0:
                        # Формируем данные для сохранения
                        odds_data = {
                            "match_id": match_id,
                            "home_team": normalized_home,
                            "away_team": normalized_away,
                            "date": commence_time,
                            "odds": odds_1x2,
                            "timestamp": datetime.now().isoformat(),
                            "source": "the_odds_api"
                        }
                        
                        # Путь для сохранения
                        odds_file_path = os.path.join(ODDS_DIRECTORY, filename)
                        
                        # Сохраняем файл
                        with open(odds_file_path, 'w', encoding='utf-8') as f:
                            json.dump(odds_data, f, indent=4, ensure_ascii=False)
                        
                        odds_files_created += 1
                        print(f"Сохранены коэффициенты для матча: {normalized_home} vs {normalized_away}")
                        print(f"  Файл: {odds_file_path}")
                        print(f"  Коэффициенты: 1={odds_1x2['1']}, X={odds_1x2['X']}, 2={odds_1x2['2']}")
                    else:
                        print(f"⚠️ Не все коэффициенты получены для матча: {normalized_home} vs {normalized_away}")
                    
                    processed_matches += 1
                    
                except Exception as e:
                    print(f"❌ Ошибка при обработке матча {home_team} vs {away_team}: {e}")
            
            print("\n" + "="*50)
            print(f"ОБРАБОТКА ЗАВЕРШЕНА: {processed_matches} матчей обработано, {odds_files_created} файлов создано")
            print("="*50)
            
            return True
        else:
            print(f"Ошибка запроса: {response.status_code}")
            print(response.text)
            return False
    
    except Exception as e:
        print(f"Произошла ошибка: {e}")
        return False

# Скрипт для проверки и исправления существующих файлов с коэффициентами
def fix_existing_odds_files():
    """
    Проверяет существующие файлы с коэффициентами и исправляет проблемы
    """
    print("\n" + "="*50)
    print("ПРОВЕРКА СУЩЕСТВУЮЩИХ ФАЙЛОВ С КОЭФФИЦИЕНТАМИ")
    print("="*50)
    
    # Убедимся, что директория существует
    if not os.path.exists(ODDS_DIRECTORY):
        print(f"Директория {ODDS_DIRECTORY} не существует.")
        return False
    
    # Получаем список файлов
    odds_files = [f for f in os.listdir(ODDS_DIRECTORY) if f.startswith("odds_") and f.endswith(".json")]
    
    if not odds_files:
        print("Файлы с коэффициентами не найдены.")
        return False
    
    print(f"Найдено {len(odds_files)} файлов с коэффициентами.")
    
    fixed_files = 0
    
    for filename in odds_files:
        file_path = os.path.join(ODDS_DIRECTORY, filename)
        
        try:
            # Загружаем данные из файла
            with open(file_path, 'r', encoding='utf-8') as f:
                odds_data = json.load(f)
            
            # Проверяем наличие ключевых полей
            fields_to_check = ['match_id', 'home_team', 'away_team', 'date', 'odds']
            missing_fields = [field for field in fields_to_check if field not in odds_data]
            
            if missing_fields:
                print(f"⚠️ В файле {filename} отсутствуют поля: {', '.join(missing_fields)}")
                continue
            
            # Проверяем структуру odds
            odds = odds_data.get('odds', {})
            if not all(k in odds for k in ['1', 'X', '2']):
                print(f"⚠️ В файле {filename} некорректная структура коэффициентов.")
                continue
            
            # Файл в порядке
            home_team = odds_data['home_team']
            away_team = odds_data['away_team']
            match_date = odds_data['date']
            
            print(f"✅ Файл {filename} корректен: {home_team} vs {away_team} ({match_date})")
            print(f"   Коэффициенты: 1={odds['1']}, X={odds['X']}, 2={odds['2']}")
            
            fixed_files += 1
            
        except Exception as e:
            print(f"❌ Ошибка при обработке файла {filename}: {e}")
    
    print("\n" + "="*50)
    print(f"ПРОВЕРКА ЗАВЕРШЕНА: {fixed_files} файлов из {len(odds_files)} в порядке")
    print("="*50)
    
    return True

if __name__ == "__main__":
    # Запускаем восстановление коэффициентов
    print("ЗАПУСК ИНТЕГРАЦИИ КОЭФФИЦИЕНТОВ ИЗ THE ODDS API")
    
    # Сначала проверяем существующие файлы
    fix_existing_odds_files()
    
    # Затем получаем и сохраняем новые коэффициенты
    print("\nПолучение новых коэффициентов из API...")
    fetch_and_save_odds()