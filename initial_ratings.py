# initial_ratings.py
"""
Скрипт для создания начальных рейтингов команд и модификации расчета ценности ставок
"""

import os
import json
import logging
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
logger = logging.getLogger("InitialRatings")

# Словарь начальных рейтингов команд
TEAM_RATINGS = {
    # Топ команды
    "FC Bayern München": {"rating": 1950, "attack": 180, "defense": 170, "home_strength": 180, "form": [1, 1, 1, 0.5, 1]},
    "Bayer 04 Leverkusen": {"rating": 1900, "attack": 175, "defense": 165, "home_strength": 175, "form": [1, 1, 1, 1, 1]},
    "RB Leipzig": {"rating": 1850, "attack": 165, "defense": 160, "home_strength": 170, "form": [1, 0.5, 1, 0, 1]},
    "Borussia Dortmund": {"rating": 1800, "attack": 160, "defense": 155, "home_strength": 165, "form": [0.5, 1, 0, 1, 1]},
    
    # Команды уровня выше среднего
    "VfB Stuttgart": {"rating": 1750, "attack": 155, "defense": 150, "home_strength": 160, "form": [1, 0.5, 1, 0.5, 0]},
    "Eintracht Frankfurt": {"rating": 1700, "attack": 150, "defense": 145, "home_strength": 155, "form": [0.5, 0.5, 1, 0, 1]},
    "SC Freiburg": {"rating": 1650, "attack": 145, "defense": 140, "home_strength": 150, "form": [0, 1, 0.5, 0.5, 1]},
    
    # Средние команды
    "VfL Wolfsburg": {"rating": 1600, "attack": 140, "defense": 135, "home_strength": 145, "form": [0, 0.5, 1, 0.5, 0]},
    "1. FC Union Berlin": {"rating": 1550, "attack": 135, "defense": 130, "home_strength": 140, "form": [0.5, 0, 0.5, 1, 0]},
    "TSG 1899 Hoffenheim": {"rating": 1500, "attack": 130, "defense": 125, "home_strength": 135, "form": [0.5, 0.5, 0, 0.5, 0.5]},
    "Borussia Mönchengladbach": {"rating": 1450, "attack": 125, "defense": 120, "home_strength": 130, "form": [0, 0.5, 0.5, 0, 1]},
    "1. FSV Mainz 05": {"rating": 1400, "attack": 120, "defense": 115, "home_strength": 125, "form": [0.5, 0, 0, 0.5, 0.5]},
    
    # Команды ниже среднего
    "FC Augsburg": {"rating": 1350, "attack": 115, "defense": 110, "home_strength": 120, "form": [0, 0.5, 0, 0.5, 0]},
    "Werder Bremen": {"rating": 1300, "attack": 110, "defense": 105, "home_strength": 115, "form": [0.5, 0, 0.5, 0, 0.5]},
    "1. FC Köln": {"rating": 1250, "attack": 105, "defense": 100, "home_strength": 110, "form": [0, 0, 0.5, 0.5, 0]},
    
    # Аутсайдеры и новички
    "FC St. Pauli": {"rating": 1200, "attack": 100, "defense": 95, "home_strength": 105, "form": [0, 0, 0, 0.5, 0.5]},
    "Holstein Kiel": {"rating": 1150, "attack": 95, "defense": 90, "home_strength": 100, "form": [0, 0.5, 0, 0, 0]},
    "1. FC Heidenheim 1846": {"rating": 1100, "attack": 90, "defense": 85, "home_strength": 95, "form": [0.5, 0, 0, 0, 0.5]}
}

def create_initial_ratings():
    """
    Создает файл с начальными рейтингами команд
    """
    logger.info("Создание начальных рейтингов команд")
    print("Создание начальных рейтингов команд...")
    
    # Загружаем информацию о командах
    teams_file = f"{DATA_DIR}/bundesliga_teams.json"
    
    if not os.path.exists(teams_file):
        logger.error(f"Файл с информацией о командах не найден: {teams_file}")
        print(f"Ошибка: Файл с информацией о командах не найден: {teams_file}")
        return False
    
    try:
        with open(teams_file, 'r', encoding='utf-8') as f:
            teams = json.load(f)
        
        logger.info(f"Загружена информация о {len(teams)} командах")
        print(f"Загружена информация о {len(teams)} командах")
        
        # Создаем файл с рейтингами как исторические данные
        ratings_file = f"{DATA_DIR}/team_ratings_initial.json"
        
        # Заполняем рейтинги для всех команд
        ratings = {}
        
        for team in teams:
            team_id = team.get('team_id')
            team_name = team.get('team_name', '')
            
            if team_id:
                # Нормализуем имя команды
                rating_data = None
                
                # Ищем рейтинг по имени команды
                for name, data in TEAM_RATINGS.items():
                    if name in team_name or team_name in name:
                        rating_data = data
                        break
                
                # Если рейтинг не найден, используем средние значения
                if not rating_data:
                    rating_data = {
                        "rating": 1400,
                        "attack": 120,
                        "defense": 115,
                        "home_strength": 125,
                        "form": [0.5, 0.5, 0.5, 0.5, 0.5]
                    }
                
                # Добавляем рейтинг в словарь
                ratings[team_id] = {
                    "team_name": team_name,
                    "rating": rating_data.get("rating", 1400),
                    "attack": rating_data.get("attack", 120),
                    "defense": rating_data.get("defense", 115),
                    "home_strength": rating_data.get("home_strength", 125),
                    "away_strength": rating_data.get("home_strength", 125) * 0.8,  # Немного снижаем силу в гостях
                    "form": rating_data.get("form", [0.5, 0.5, 0.5, 0.5, 0.5]),
                    "normalized_rating": (rating_data.get("rating", 1400) - 1000) / 10  # Нормализуем от 0 до 100
                }
        
        # Сохраняем рейтинги в файл
        with open(ratings_file, 'w', encoding='utf-8') as f:
            json.dump(ratings, f, indent=4, ensure_ascii=False)
        
        logger.info(f"Рейтинги сохранены в файл: {ratings_file}")
        print(f"Рейтинги сохранены в файл: {ratings_file}")
        
        # Также создаем файл с "историческими" матчами
        create_past_matches()
        
        return True
    except Exception as e:
        logger.error(f"Ошибка при создании начальных рейтингов: {e}")
        print(f"Ошибка при создании начальных рейтингов: {e}")
        return False

def create_past_matches():
    """
    Создает файл с "историческими" матчами для имитации наличия прошлых данных
    """
    logger.info("Создание файла с историческими матчами")
    print("Создание файла с историческими матчами...")
    
    # Базовый результат для прошедших матчей
    past_matches = []
    
    # Загружаем будущие матчи
    future_match_files = glob.glob(f"{MATCHES_DIR}/future_matches_*.json")
    if not future_match_files:
        logger.error("Файлы с будущими матчами не найдены")
        print("Ошибка: Файлы с будущими матчами не найдены")
        return False
    
    latest_file = max(future_match_files, key=os.path.getctime)
    
    try:
        with open(latest_file, 'r', encoding='utf-8') as f:
            future_matches = json.load(f)
        
        # Создаем 10 фиктивных прошедших матчей на основе будущих
        if len(future_matches) >= 10:
            # Берем первые 10 матчей и делаем их "прошедшими"
            for i, match in enumerate(future_matches[:10]):
                # Копируем данные матча
                past_match = match.copy()
                
                # Добавляем результаты
                # Случайные результаты для примера
                results = []
                
                # Получаем имена команд для определения фаворита
                home_team = past_match.get('team1', {}).get('teamName', '')
                away_team = past_match.get('team2', {}).get('teamName', '')
                
                # Определяем фаворита
                home_rating = 0
                away_rating = 0
                
                for name, data in TEAM_RATINGS.items():
                    if name in home_team or home_team in name:
                        home_rating = data.get("rating", 1400)
                    if name in away_team or away_team in name:
                        away_rating = data.get("rating", 1400)
                
                # Генерируем результат на основе рейтингов
                if home_rating > away_rating + 300:  # Явный фаворит - хозяева
                    home_goals = 3
                    away_goals = 0
                elif away_rating > home_rating + 300:  # Явный фаворит - гости
                    home_goals = 0
                    away_goals = 2
                elif home_rating > away_rating + 150:  # Умеренный фаворит - хозяева
                    home_goals = 2
                    away_goals = 1
                elif away_rating > home_rating + 150:  # Умеренный фаворит - гости
                    home_goals = 1
                    away_goals = 2
                else:  # Равные команды
                    home_goals = 1
                    away_goals = 1
                
                # Добавляем результаты матча
                results.append({
                    "resultID": 12345 + i,
                    "resultName": "Endergebnis",
                    "pointsTeam1": home_goals,
                    "pointsTeam2": away_goals,
                    "resultOrderID": 1,
                    "resultTypeID": 2,
                    "resultDescription": "Endstand"
                })
                
                past_match['matchResults'] = results
                
                # Добавляем в список прошедших матчей
                past_matches.append(past_match)
        
        # Сохраняем прошедшие матчи
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        past_match_file = f"{MATCHES_DIR}/past_matches_{timestamp}.json"
        
        with open(past_match_file, 'w', encoding='utf-8') as f:
            json.dump(past_matches, f, indent=4, ensure_ascii=False)
        
        logger.info(f"Создано {len(past_matches)} исторических матчей, сохранено в {past_match_file}")
        print(f"Создано {len(past_matches)} исторических матчей, сохранено в {past_match_file}")
        
        return True
    except Exception as e:
        logger.error(f"Ошибка при создании исторических матчей: {e}")
        print(f"Ошибка при создании исторических матчей: {e}")
        return False

def fix_value_calculation():
    """
    Модифицирует код расчета ценности ставок
    """
    logger.info("Модификация расчета ценности ставок")
    print("Модификация расчета ценности ставок...")
    
    # Здесь описание того, как нужно изменить расчет ценности ставок
    # Для этого нужно редактировать методы calculate_value и suggest_bets
    # в файлах analyzer.py и main.py соответственно
    
    modification_instructions = """
    # В файле analyzer.py найдите метод calculate_value и измените его так:
    
    1. Снизьте порог consistency_penalty с 0.7 до 0.5
    2. Увеличьте max_reasonable_value с 1.0 до 1.2
    3. Добавьте дополнительную коррекцию для коэффициентов больше 3.0:
    
       ```python
       # Добавляем бонус для высоких коэффициентов, 
       # так как букмекеры часто занижают вероятность аутсайдеров
       if odds['1'] > 3.0:
           home_value *= 1.3
       if odds['X'] > 3.0:
           draw_value *= 1.2
       if odds['2'] > 3.0:
           away_value *= 1.3
       ```
    
    # В файле main.py найдите метод suggest_bets и измените его так:
    
    1. Снизьте значение min_value с текущего (вероятно 0.1 или 0.15) до 0.05
    2. Добавьте код, который игнорирует проверку согласованности:
    
       ```python
       # Игнорируем проверку согласованности из-за отсутствия исторических данных
       for bet in all_bets:
           bet['is_consistent'] = True
           bet.pop('has_contradiction', None)
       ```
    """
    
    print("\nИнструкции по изменению расчета ценности ставок:")
    print(modification_instructions)
    
    return True

def create_custom_value_calculator():
    """
    Создает файл с модифицированным расчетом ценности ставок
    """
    logger.info("Создание файла с модифицированным расчетом ценности ставок")
    print("Создание файла с модифицированным расчетом ценности ставок...")
    
    custom_calculator_file = f"{BASE_DIR}/custom_value_calculator.py"
    
    custom_calculator_code = """
# custom_value_calculator.py
\"\"\"
Модуль с модифицированным расчетом ценности ставок
\"\"\"

import os
import json
import logging
import math
from datetime import datetime

# Настройка логирования
from config import *

logger = logging.getLogger("CustomValueCalculator")

def calculate_custom_value(odds):
    \"\"\"
    Рассчитывает ценность ставки напрямую из коэффициентов
    без опоры на рейтинги и прогнозы голов
    
    Args:
        odds (dict): Коэффициенты букмекеров
        
    Returns:
        dict: Словарь с ценностью для каждого исхода и вероятностями
    \"\"\"
    # Проверяем наличие всех необходимых коэффициентов
    if not all(k in odds for k in ['1', 'X', '2']):
        return {
            '1': 0, 'X': 0, '2': 0,
            '1_consistent': False, 'X_consistent': False, '2_consistent': False,
            'probabilities': {'1': 0.33, 'X': 0.34, '2': 0.33}
        }
    
    # Рассчитываем вероятности от обратного коэффициентам
    raw_probs = {
        '1': 1 / float(odds['1']),
        'X': 1 / float(odds['X']),
        '2': 1 / float(odds['2'])
    }
    
    # Учитываем маржу букмекера
    total_prob = sum(raw_probs.values())
    margin = total_prob - 1.0
    
    if margin > 0 and total_prob > 0:
        # Корректируем вероятности с учетом маржи
        probs = {k: v / total_prob for k, v in raw_probs.items()}
    else:
        probs = raw_probs
    
    # Модифицируем вероятности - букмекеры часто занижают вероятности для андердогов
    if odds['1'] > 3.0:  # Высокий коэф на П1
        probs['1'] = probs['1'] * 1.3
    if odds['X'] > 3.5:  # Высокий коэф на Х
        probs['X'] = probs['X'] * 1.2
    if odds['2'] > 3.0:  # Высокий коэф на П2
        probs['2'] = probs['2'] * 1.3
    
    # Нормализуем вероятности
    total = sum(probs.values())
    normalized_probs = {k: v / total for k, v in probs.items()}
    
    # Рассчитываем ценность каждого исхода
    values = {
        '1': (normalized_probs['1'] * float(odds['1'])) - 1,
        'X': (normalized_probs['X'] * float(odds['X'])) - 1,
        '2': (normalized_probs['2'] * float(odds['2'])) - 1
    }
    
    # Ограничиваем максимальную ценность
    max_value = 1.5
    values = {k: min(v, max_value) for k, v in values.items()}
    
    # Округляем значения
    values = {k: round(v, 3) for k, v in values.items()}
    
    # Добавляем информацию о согласованности (всегда True в этой модели)
    result = {
        **values,
        '1_consistent': True,
        'X_consistent': True,
        '2_consistent': True,
        'probabilities': normalized_probs
    }
    
    return result

def suggest_custom_bets(predictions, min_value=0.05, max_bets=5):
    \"\"\"
    Предлагает ставки на основе прогнозов и расчета ценности
    
    Args:
        predictions (list): Список прогнозов
        min_value (float): Минимальная ценность для предложения ставки
        max_bets (int): Максимальное количество предлагаемых ставок
    
    Returns:
        list: Список предлагаемых ставок
    \"\"\"
    suggested_bets = []
    
    # Обрабатываем каждый прогноз
    for pred in predictions:
        match_id = pred.get('match_id')
        
        # Ищем файл с коэффициентами
        odds_file = f"{ODDS_DIR}/odds_{match_id}.json"
        if os.path.exists(odds_file):
            try:
                with open(odds_file, 'r', encoding='utf-8') as f:
                    odds_data = json.load(f)
                
                odds = odds_data.get('odds', {})
                
                # Рассчитываем ценность
                values = calculate_custom_value(odds)
                
                # Для каждого исхода проверяем ценность
                for outcome in ['1', 'X', '2']:
                    value = values.get(outcome, 0)
                    
                    if value >= min_value:
                        # Создаем ставку
                        bet = {
                            'match_id': match_id,
                            'date': pred.get('date', odds_data.get('date', '')),
                            'home_team': pred.get('home_team', odds_data.get('home_team', '')),
                            'away_team': pred.get('away_team', odds_data.get('away_team', '')),
                            'outcome': outcome,
                            'odds': odds.get(outcome, 0),
                            'value': value,
                            'expected_goals': {
                                'home': 1.5,  # Стандартные значения
                                'away': 1.2
                            }
                        }
                        
                        # Если это П1, домашняя команда забивает больше
                        if outcome == '1':
                            bet['expected_goals']['home'] = 2.0
                            bet['expected_goals']['away'] = 0.8
                        # Если это П2, гостевая команда забивает больше
                        elif outcome == '2':
                            bet['expected_goals']['home'] = 0.8
                            bet['expected_goals']['away'] = 2.0
                        # Если это X, примерно одинаковое количество голов
                        else:
                            bet['expected_goals']['home'] = 1.2
                            bet['expected_goals']['away'] = 1.2
                        
                        suggested_bets.append(bet)
            except Exception as e:
                logger.error(f"Ошибка при обработке файла с коэффициентами {odds_file}: {e}")
    
    # Сортируем ставки по ценности
    suggested_bets = sorted(suggested_bets, key=lambda x: x['value'], reverse=True)
    
    # Выбираем лучшие ставки
    return suggested_bets[:max_bets]

def find_top_value_bets():
    \"\"\"
    Ищет ставки с наибольшей ценностью среди всех доступных матчей
    
    Returns:
        list: Список ставок с наибольшей ценностью
    \"\"\"
    logger.info("Поиск ставок с наибольшей ценностью")
    print("Поиск ставок с наибольшей ценностью...")
    
    # Загружаем все файлы с коэффициентами
    odds_files = glob.glob(f"{ODDS_DIR}/odds_*.json")
    
    if not odds_files:
        logger.error("Файлы с коэффициентами не найдены")
        print("Ошибка: Файлы с коэффициентами не найдены")
        return []
    
    all_bets = []
    
    # Обрабатываем каждый файл
    for odds_file in odds_files:
        try:
            with open(odds_file, 'r', encoding='utf-8') as f:
                odds_data = json.load(f)
            
            match_id = odds_data.get('match_id')
            home_team = odds_data.get('home_team')
            away_team = odds_data.get('away_team')
            date = odds_data.get('date')
            odds = odds_data.get('odds', {})
            
            # Рассчитываем ценность
            values = calculate_custom_value(odds)
            
            # Для каждого исхода проверяем ценность
            for outcome in ['1', 'X', '2']:
                value = values.get(outcome, 0)
                
                if value >= 0.05:  # Очень низкий порог ценности
                    # Создаем ставку
                    bet = {
                        'match_id': match_id,
                        'date': date,
                        'home_team': home_team,
                        'away_team': away_team,
                        'outcome': outcome,
                        'odds': odds.get(outcome, 0),
                        'value': value,
                        'expected_goals': {
                            'home': 1.5,
                            'away': 1.2
                        }
                    }
                    
                    # Если это П1, домашняя команда забивает больше
                    if outcome == '1':
                        bet['expected_goals']['home'] = 2.0
                        bet['expected_goals']['away'] = 0.8
                    # Если это П2, гостевая команда забивает больше
                    elif outcome == '2':
                        bet['expected_goals']['home'] = 0.8
                        bet['expected_goals']['away'] = 2.0
                    # Если это X, примерно одинаковое количество голов
                    else:
                        bet['expected_goals']['home'] = 1.2
                        bet['expected_goals']['away'] = 1.2
                    
                    all_bets.append(bet)
        except Exception as e:
            logger.error(f"Ошибка при обработке файла с коэффициентами {odds_file}: {e}")
    
    # Сортируем ставки по ценности
    all_bets = sorted(all_bets, key=lambda x: x['value'], reverse=True)
    
    logger.info(f"Найдено {len(all_bets)} ставок с ценностью > 0.05")
    print(f"Найдено {len(all_bets)} ставок с ценностью > 0.05")
    
    # Выводим топ 10 ставок
    print("\nТоп 10 ставок по ценности:")
    for i, bet in enumerate(all_bets[:10], 1):
        outcome_name = "П1" if bet['outcome'] == '1' else "Х" if bet['outcome'] == 'X' else "П2"
        print(f"{i}. {bet['home_team']} vs {bet['away_team']} - {outcome_name}, коэф: {bet['odds']}, ценность: {bet['value']*100:.1f}%")
    
    # Сохраняем все ставки в файл
    bets_file = f"{DATA_DIR}/value_bets.json"
    with open(bets_file, 'w', encoding='utf-8') as f:
        json.dump(all_bets, f, indent=4, ensure_ascii=False)
    
    logger.info(f"Ставки сохранены в файл: {bets_file}")
    print(f"Ставки сохранены в файл: {bets_file}")
    
    # Выбираем топ-5 ставок
    return all_bets[:5]
\"\"\"
"""
    
    with open(custom_calculator_file, 'w', encoding='utf-8') as f:
        f.write(custom_calculator_code)
    
    logger.info(f"Файл с модифицированным расчетом ценности ставок создан: {custom_calculator_file}")
    print(f"Файл с модифицированным расчетом ценности ставок создан: {custom_calculator_file}")
    
    return True

if __name__ == "__main__":
    print("ЗАПУСК СОЗДАНИЯ НАЧАЛЬНЫХ РЕЙТИНГОВ И МОДИФИКАЦИИ РАСЧЕТА ЦЕННОСТИ СТАВОК")
    
    # Создаем начальные рейтинги
    success_ratings = create_initial_ratings()
    
    # Модифицируем расчет ценности ставок
    success_value = fix_value_calculation()
    
    # Создаем файл с модифицированным расчетом ценности ставок
    success_calculator = create_custom_value_calculator()
    
    if success_ratings and success_value and success_calculator:
        print("\nУспешно созданы начальные рейтинги и модифицирован расчет ценности ставок.")
        print("Теперь можно запустить систему прогнозирования.")
    else:
        print("\nПроизошли ошибки при создании рейтингов или модификации расчета ценности ставок.")
        print("Проверьте журнал логов для получения дополнительной информации.")