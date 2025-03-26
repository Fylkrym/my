# odds_collector.py
"""
Модуль для сбора и обработки коэффициентов для матчей Бундеслиги
"""

import os
import json
import logging
import pandas as pd
import numpy as np
import random
import glob
from datetime import datetime, timedelta
from bookmaker_parser import BookmakerParser

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
logger = logging.getLogger("OddsCollector")


class OddsCollector:
    """Класс для сбора и обработки коэффициентов букмекеров для матчей Бундеслиги"""
    
    def __init__(self):
        """Инициализирует сборщик коэффициентов"""
        # Создаем директорию для коэффициентов, если не существует
        os.makedirs(ODDS_DIR, exist_ok=True)
        self.teams_data = {}
        self.load_team_rankings()
        logger.info("Инициализирован сборщик коэффициентов")
    
    def load_team_rankings(self):
        """
        Загружает данные о рейтингах команд для более точной генерации коэффициентов
        """
        try:
            # Пытаемся загрузить рейтинги команд
            teams_file = f"{DATA_DIR}/bundesliga_teams.json"
            
            if os.path.exists(teams_file):
                with open(teams_file, 'r', encoding='utf-8') as f:
                    teams_list = json.load(f)
                
                # Обогащаем данными о силе команд
                for team in teams_list:
                    team_id = team.get('team_id')
                    team_name = team.get('team_name', '')
                    
                    # Оценка силы команд (от 0 до 100)
                    strength = self._get_team_strength(team_name)
                    
                    self.teams_data[team_id] = {
                        'team_name': team_name,
                        'strength': strength
                    }
                
                logger.info(f"Загружены данные о {len(self.teams_data)} командах")
                
                # Создаем rankings.json с актуальными данными о силе команд
                self._save_team_rankings()
            else:
                logger.warning("Файл с информацией о командах не найден")
        except Exception as e:
            logger.error(f"Ошибка при загрузке информации о командах: {e}")
    
    def _get_team_strength(self, team_name):
        """
        Определяет силу команды на основе её названия и текущего положения
        
        Args:
            team_name (str): Название команды
            
        Returns:
            int: Оценка силы команды (от 0 до 100)
        """
        # Топ-команды
        if team_name == 'FC Bayern München':
            return 95  # Бавария - сильнейшая команда
        elif team_name == 'Bayer Leverkusen':
            return 90  # Чемпион прошлого сезона
        elif team_name == 'RB Leipzig':
            return 85
        elif team_name == 'Borussia Dortmund':
            return 82
        
        # Команды верхней половины таблицы
        elif team_name in ['VfB Stuttgart', 'Eintracht Frankfurt', 'SC Freiburg']:
            return random.randint(70, 80)
        
        # Середняки
        elif team_name in ['VfL Wolfsburg', '1. FC Union Berlin', 'TSG 1899 Hoffenheim', 
                           'Borussia Mönchengladbach', '1. FSV Mainz 05']:
            return random.randint(55, 70)
        
        # Команды нижней половины таблицы
        elif team_name in ['FC Augsburg', 'SV Werder Bremen', '1. FC Köln']:
            return random.randint(40, 55)
        
        # Аутсайдеры и новички
        elif team_name in ['FC St. Pauli', 'Holstein Kiel', '1. FC Heidenheim 1846']:
            return random.randint(20, 40)
        
        # Для остальных команд
        return random.randint(40, 60)
    
    def _save_team_rankings(self):
        """
        Сохраняет данные о рейтингах команд в отдельный файл
        """
        rankings = []
        
        for team_id, data in self.teams_data.items():
            rankings.append({
                'team_id': team_id,
                'team_name': data.get('team_name', ''),
                'strength': data.get('strength', 50)
            })
        
        # Сортируем по убыванию силы
        rankings.sort(key=lambda x: x.get('strength', 0), reverse=True)
        
        rankings_file = f"{DATA_DIR}/team_rankings.json"
        with open(rankings_file, 'w', encoding='utf-8') as f:
            json.dump(rankings, f, indent=4, ensure_ascii=False)
        
        logger.info(f"Рейтинги команд сохранены в {rankings_file}")
    
    def collect_real_odds(self):
        """
        Собирает реальные коэффициенты 
        
        Returns:
            dict: Словарь с коэффициентами для матчей
        """
        logger.info("Сбор реальных коэффициентов")
        print("Сбор реальных коэффициентов...")
        
        try:
            # Инициализация парсера
            parser = BookmakerParser()
            
            # Получение коэффициентов
            odds_df = parser.get_all_odds(league="bundesliga")
            
            if not odds_df.empty:
                # Нормализация названий команд
                odds_df = parser.normalize_team_names(odds_df)
                
                # Получаем директорию для сохранения из конфигурации
                os.makedirs(ODDS_DIR, exist_ok=True)
                
                # Путь для сохранения данных
                odds_file = f"{ODDS_DIR}/real_bookmaker_odds.csv"
                
                # Сохранение данных
                odds_df.to_csv(odds_file, index=False)
                
                logger.info(f"Получены реальные коэффициенты для {len(odds_df)} матчей от букмекеров")
                print(f"Получены реальные коэффициенты для {len(odds_df)} матчей от букмекеров")
                print(f"Данные сохранены в {odds_file}")
                
                # Преобразуем данные в формат, используемый в системе
                odds_data = {}
                
                for _, row in odds_df.iterrows():
                    match_id = f"{row['home_team']}_{row['away_team']}".replace(' ', '_')
                    
                    odds = {
                        '1': float(row['home_win']),
                        'X': float(row['draw']),
                        '2': float(row['away_win'])
                    }
                    
                    odds_data[match_id] = {
                        'match_id': match_id,
                        'home_team': row['home_team'],
                        'away_team': row['away_team'],
                        'date': row['match_date'],
                        'odds': odds,
                        'timestamp': datetime.now().isoformat(),
                        'source': 'real_bookmaker'
                    }
                    
                    # Сохраняем коэффициенты для каждого матча
                    match_odds_file = f"{ODDS_DIR}/odds_{match_id}.json"
                    with open(match_odds_file, 'w', encoding='utf-8') as f:
                        json.dump(odds_data[match_id], f, indent=4, ensure_ascii=False)
                
                return odds_data
            else:
                logger.warning("Не удалось получить коэффициенты от букмекеров")
                print("Не удалось получить коэффициенты от букмекеров")
                return {}
        
        except Exception as e:
            logger.error(f"Ошибка при сборе реальных коэффициентов: {e}")
            print(f"Ошибка при сборе реальных коэффициентов: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    def collect_odds_for_all_matches(self):
        """
        Собирает коэффициенты для всех будущих матчей
        
        Returns:
            dict: Словарь с коэффициентами для всех матчей
        """
        logger.info("Начинаем сбор коэффициентов для всех матчей")
        print("Начинаем сбор коэффициентов для всех матчей...")
        
        # Метод 1: Пробуем использовать The Odds API Parser
        api_parser_odds = self.try_odds_api_parser()
        if api_parser_odds:
            logger.info("Используем коэффициенты из The Odds API Parser")
            print("Используем коэффициенты из The Odds API Parser")
            return api_parser_odds
        
    # Метод 2: Пробуем напрямую использовать The Odds API
    api_odds = self.get_odds_from_api()
    if api_odds:
        logger.info("Используем коэффициенты из The Odds API")
        print("Используем коэффициенты из The Odds API")
        return api_odds
        
    # Метод 3: Пытаемся получить реальные коэффициенты через парсер
    real_odds = self.collect_real_odds()
    if real_odds:
        logger.info("Используем реальные коэффициенты из парсера")
        print("Используем реальные коэффициенты из парсера")
        return real_odds
    
    # Если все методы не сработали, генерируем свои
    logger.info("Все методы получения реальных коэффициентов не сработали. Генерация синтетических коэффициентов.")
    print("ВНИМАНИЕ: Все методы получения реальных коэффициентов не сработали!")
    print("Генерация синтетических коэффициентов...")
            
            # (остальной код метода)

        else:
            # (код для обработки ошибок)
            return {}
    except Exception as e:
        # (код для обработки исключений)
        return {}
    
    def try_odds_api_parser(self):
        """
        Пытается получить коэффициенты через отдельный парсер The Odds API
    
        Returns:
            dict: Словарь с коэффициентами для матчей
        """
        try:
            from the_odds_api_parser import get_odds
        
            print("Получение коэффициентов через the_odds_api_parser...")
            logger.info("Получение коэффициентов через the_odds_api_parser")
        
            API_KEY = "58a2f2727f4ce6fd686ed4f6d347c600"
            odds_data = get_odds(API_KEY)
        
            if odds_data and len(odds_data) > 0:
               # (остальной код метода)
                return result_data
            else:
                print("Не удалось получить данные через the_odds_api_parser")
                return {}
        except Exception as e:
            logger.error(f"Ошибка при использовании the_odds_api_parser: {e}")
            print(f"Ошибка при использовании the_odds_api_parser: {e}")
            return {}
        
        if real_odds:
            logger.info("Используем реальные коэффициенты")
            print("Используем реальные коэффициенты")
            return real_odds
        
        # Если реальные коэффициенты не получены, генерируем свои
        logger.info("Генерация коэффициентов")
        print("Генерация коэффициентов")
        
        # Находим последний файл с будущими матчами
        future_match_files = glob.glob(f"{MATCHES_DIR}/future_matches_*.json")
        if not future_match_files:
            logger.warning("Файлы с будущими матчами не найдены")
            return {}
        
        latest_file = max(future_match_files, key=os.path.getctime)
        
        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                future_matches = json.load(f)
            
            logger.info(f"Загружено {len(future_matches)} предстоящих матчей")
            
            odds_data = {}
            
            for match in future_matches:
                try:
                    match_id = match.get('matchID')
                    match_date_str = match.get('matchDateTime', '')
                    
                    # Информация о командах
                    home_team = match.get('team1', {})
                    away_team = match.get('team2', {})
                    
                    home_team_name = home_team.get('teamName', '')
                    away_team_name = away_team.get('teamName', '')
                    
                    # Генерируем коэффициенты
                    odds = self.generate_realistic_odds(match, self.teams_data)
                    
                    # Добавляем информацию о матче
                    odds_data[match_id] = {
                        'match_id': match_id,
                        'home_team': home_team_name,
                        'away_team': away_team_name,
                        'date': match_date_str,
                        'odds': odds,
                        'timestamp': datetime.now().isoformat(),
                        'source': 'generated'
                    }
                    
                    # Сохраняем коэффициенты для каждого матча
                    odds_file = f"{ODDS_DIR}/odds_{match_id}.json"
                    with open(odds_file, 'w', encoding='utf-8') as f:
                        json.dump(odds_data[match_id], f, indent=4, ensure_ascii=False)
                
                except Exception as e:
                    logger.error(f"Ошибка при сборе коэффициентов для матча {match.get('matchID')}: {e}")
            
            logger.info(f"Сбор коэффициентов завершен. Обработано {len(odds_data)} матчей")
            return odds_data
        
        except Exception as e:
            logger.error(f"Ошибка при сборе коэффициентов: {e}")
            return {}
    
    def generate_realistic_odds(self, match_data, teams_data):
        """
        Генерирует реалистичные коэффициенты на основе данных о командах
        
        Args:
            match_data (dict): Данные о матче
            teams_data (dict): Данные о командах
            
        Returns:
            dict: Словарь с коэффициентами
        """
        # Получаем ID команд
        home_team = match_data.get('team1', {})
        away_team = match_data.get('team2', {})
        
        home_team_id = home_team.get('teamId')
        away_team_id = away_team.get('teamId')
        
        # Получаем имена команд
        home_team_name = home_team.get('teamName', '')
        away_team_name = away_team.get('teamName', '')
        
        # Получаем информацию о силе команд
        home_team_info = teams_data.get(home_team_id, {})
        away_team_info = teams_data.get(away_team_id, {})
        
        home_strength = home_team_info.get('strength', 50)
        away_strength = away_team_info.get('strength', 50)
        
        # Расчет разницы в силе команд
        strength_diff = home_strength - away_strength
        
        # Базовые вероятности (без учета домашнего преимущества)
        # Используем логистическую функцию для преобразования разницы в силе в вероятности
        home_advantage_factor = 10  # Домашнее преимущество
        scaled_diff = (strength_diff + home_advantage_factor) / 40  # Нормализация
        
        # Вероятность победы хозяев (с учетом домашнего преимущества)
        home_win_prob = 1 / (1 + np.exp(-scaled_diff))
        
        # Вероятность ничьей (зависит от близости сил команд)
        draw_bias = 0.26 - abs(scaled_diff) * 0.1  # Чем ближе силы, тем выше вероятность ничьей
        draw_prob = max(0.12, min(0.32, draw_bias))  # Ограничиваем в разумных пределах
        
        # Вероятность победы гостей
        away_win_prob = 1 - home_win_prob - draw_prob
        
        # Корректируем для очень сильных или очень слабых команд
        if home_strength > 85 and away_strength < 50:  # Топ команда против слабой
            home_win_prob = min(0.85, home_win_prob * 1.15)
            away_win_prob = max(0.05, away_win_prob * 0.8)
            draw_prob = 1 - home_win_prob - away_win_prob
        elif away_strength > 85 and home_strength < 50:  # Топ гостевая команда против слабой
            away_win_prob = min(0.75, away_win_prob * 1.2)
            home_win_prob = max(0.15, home_win_prob * 0.85)
            draw_prob = 1 - home_win_prob - away_win_prob
        
        # Корректировка для специфических противостояний
        if 'FC Bayern München' in [home_team_name, away_team_name]:
            if home_team_name == 'FC Bayern München':
                # Бавария дома
                home_win_prob = min(0.88, home_win_prob * 1.1)
                away_win_prob = max(0.04, away_win_prob * 0.8)
            else:
                # Бавария в гостях
                away_win_prob = min(0.78, away_win_prob * 1.1)
                home_win_prob = max(0.12, home_win_prob * 0.9)
            draw_prob = 1 - home_win_prob - away_win_prob
            
        # Очень конкретные матчи
        if home_team_name == 'FC Bayern München' and away_team_name == 'FC St. Pauli':
            home_win_prob = 0.88
            draw_prob = 0.08
            away_win_prob = 0.04
        elif home_team_name == 'FC St. Pauli' and away_team_name == 'Bayer Leverkusen':
            home_win_prob = 0.12
            draw_prob = 0.15
            away_win_prob = 0.73
        
        # Преобразуем вероятности в коэффициенты
        # Формула: коэффициент = 1/вероятность
        raw_home_odds = 1 / home_win_prob
        raw_draw_odds = 1 / draw_prob
        raw_away_odds = 1 / away_win_prob
        
        # Добавляем маржу букмекера (обычно 5-10%)
        margin = 0.07  # 7% маржа
        total_prob = home_win_prob + draw_prob + away_win_prob
        
        margin_factor = (1 + margin) / total_prob
        
        home_odds = round(raw_home_odds * margin_factor, 2)
        draw_odds = round(raw_draw_odds * margin_factor, 2)
        away_odds = round(raw_away_odds * margin_factor, 2)
        
        # Ограничиваем коэффициенты разумными значениями
        home_odds = max(1.05, min(home_odds, 12.00))
        draw_odds = max(3.00, min(draw_odds, 8.00))
        away_odds = max(1.05, min(away_odds, 12.00))
        
        # Специальные случаи для конкретных матчей
        if home_team_name == 'FC Bayern München' and away_team_name == 'FC St. Pauli':
            home_odds = 1.16
            draw_odds = 7.50
            away_odds = 15.00
        elif home_team_name == 'FC St. Pauli' and away_team_name == 'Bayer Leverkusen':
            home_odds = 7.80
            draw_odds = 5.20
            away_odds = 1.36
        
        # Формируем объект с коэффициентами
        odds = {
            '1': home_odds,
            'X': draw_odds,
            '2': away_odds
        }
        
        # Добавляем коэффициенты на тоталы
        total_goals_expected = self._calculate_expected_total_goals(home_team_name, away_team_name, home_strength, away_strength)
        
        # Коэффициенты для тотала больше/меньше 2.5
        if total_goals_expected > 2.8:  # Ожидается много голов
            over_25_prob = 0.65
        elif total_goals_expected < 2.2:  # Ожидается мало голов
            over_25_prob = 0.40
        else:  # Средняя результативность
            over_25_prob = 0.55
            
        # Добавляем вариацию
        over_25_prob += (random.random() - 0.5) * 0.06
        
        under_25_prob = 1 - over_25_prob
        
        # Добавляем маржу для тоталов
        total_margin = 0.06  # 6% маржа
        total_margin_factor = (1 + total_margin)
        
        over_25_odds = round((1 / over_25_prob) * total_margin_factor, 2)
        under_25_odds = round((1 / under_25_prob) * total_margin_factor, 2)
        
        # Ограничиваем значения
        over_25_odds = max(1.30, min(over_25_odds, 2.50))
        under_25_odds = max(1.30, min(under_25_odds, 2.50))
        
        # Добавляем в словарь
        odds.update({
            'Over 2.5': over_25_odds,
            'Under 2.5': under_25_odds
        })
        
        # Коэффициенты для фор
        if home_win_prob > 0.65:  # Явный фаворит - хозяева
            handicap_home_minus_odds = round((1 / (home_win_prob * 0.8)) * margin_factor, 2)
            handicap_away_plus_odds = round((1 / (1 - (home_win_prob * 0.8))) * margin_factor, 2)
            odds.update({
                'Handicap -1.5 (1)': max(1.50, min(handicap_home_minus_odds, 3.50)),
                'Handicap +1.5 (2)': max(1.20, min(handicap_away_plus_odds, 2.80))
            })
        elif away_win_prob > 0.60:  # Явный фаворит - гости
            handicap_away_minus_odds = round((1 / (away_win_prob * 0.8)) * margin_factor, 2)
            handicap_home_plus_odds = round((1 / (1 - (away_win_prob * 0.8))) * margin_factor, 2)
            odds.update({
                'Handicap +1.5 (1)': max(1.20, min(handicap_home_plus_odds, 2.80)),
                'Handicap -1.5 (2)': max(1.50, min(handicap_away_minus_odds, 3.50))
            })
        
        return odds
    
    def _calculate_expected_total_goals(self, home_team, away_team, home_strength, away_strength):
        """
        Рассчитывает ожидаемое количество голов в матче
        
        Args:
            home_team (str): Название домашней команды
            away_team (str): Название гостевой команды
            home_strength (int): Сила домашней команды
            away_strength (int): Сила гостевой команды
            
        Returns:
            float: Ожидаемое количество голов
        """
        # Базовая результативность в Бундеслиге
        base_total_goals = 3.1
        
        # Корректировка на основе силы команд
        # Сильные команды обычно забивают больше
        strength_factor = ((home_strength + away_strength) / 100) * 0.3
        
        # Корректировка для команд с определенным стилем
        style_factor = 0
        
        # Команды с атакующим стилем
        attacking_teams = ['FC Bayern München', 'Bayer Leverkusen', 'RB Leipzig', 'Borussia Dortmund']
        # Команды с оборонительным стилем
        defensive_teams = ['FC St. Pauli', '1. FC Union Berlin', '1. FC Heidenheim 1846']
        
        # Если обе команды атакующие, ожидаем больше голов
        if home_team in attacking_teams and away_team in attacking_teams:
            style_factor += 0.5
        # Если обе команды оборонительные, ожидаем меньше голов
        elif home_team in defensive_teams and away_team in defensive_teams:
            style_factor -= 0.5
        # Если микс, небольшая корректировка
        elif home_team in attacking_teams or away_team in attacking_teams:
            style_factor += 0.3
        elif home_team in defensive_teams or away_team in defensive_teams:
            style_factor -= 0.3
            
        # Разница в силе также влияет на результативность
        # В очень неравных матчах обычно забивается больше голов
        strength_diff = abs(home_strength - away_strength)
        diff_factor = (strength_diff / 100) * 0.5
        
        # Итоговое ожидаемое количество голов
        expected_goals = base_total_goals + strength_factor + style_factor + diff_factor
        
        # Добавляем немного случайности для реализма
        expected_goals += (random.random() - 0.5) * 0.3
        
        # Ограничиваем в разумных пределах
        expected_goals = max(1.8, min(expected_goals, 4.5))
        
        return expected_goals

    def update_historical_odds(self, match_id=None):
        """
        Обновляет исторические коэффициенты для анализа их точности
        
        Args:
            match_id (int, optional): ID матча для обновления (если None, обновляются все)
            
        Returns:
            dict: Словарь с обновленной информацией
        """
        # Находим все файлы с прошедшими матчами
        past_match_files = glob.glob(f"{MATCHES_DIR}/past_matches_*.json")
        if not past_match_files:
            logger.warning("Файлы с прошедшими матчами не найдены")
            return {}
        
        latest_file = max(past_match_files, key=os.path.getctime)
        
        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                past_matches = json.load(f)
            
            logger.info(f"Загружено {len(past_matches)} прошедших матчей для обновления исторических коэффициентов")
            
            # Результаты обновления
            updated_data = {}
            
            # Обрабатываем матчи
            for match in past_matches:
                try:
                    match_id_current = match.get('matchID')
                    
                    # Если указан конкретный ID матча, обновляем только его
                    if match_id is not None and match_id != match_id_current:
                        continue
                    
                    # Проверяем, есть ли файл с коэффициентами для этого матча
                    odds_file = f"{ODDS_DIR}/odds_{match_id_current}.json"
                    
                    if os.path.exists(odds_file):
                        # Загружаем существующие коэффициенты
                        with open(odds_file, 'r', encoding='utf-8') as f:
                            odds_data = json.load(f)
                        
                        # Получаем результат матча
                        match_results = match.get('matchResults', [])
                        final_result = next((r for r in match_results if r.get('resultTypeID') == 2), None)
                        
                        if final_result:
                            home_goals = final_result.get('pointsTeam1', 0)
                            away_goals = final_result.get('pointsTeam2', 0)
                            
                            # Определяем исход
                            if home_goals > away_goals:
                                result = '1'
                            elif home_goals == away_goals:
                                result = 'X'
                            else:
                                result = '2'
                            
                            # Определяем тоталы
                            total_goals = home_goals + away_goals
                            total_over_25 = total_goals > 2.5
                            
                            # Обновляем данные с результатом
                            odds_data['result'] = {
                                'home_goals': home_goals,
                                'away_goals': away_goals,
                                'outcome': result,
                                'total_goals': total_goals,
                                'total_over_25': total_over_25
                            }
                            
                            # Сохраняем обновленные данные
                            with open(odds_file, 'w', encoding='utf-8') as f:
                                json.dump(odds_data, f, indent=4, ensure_ascii=False)
                            
                            updated_data[match_id_current] = odds_data
                            logger.info(f"Обновлены исторические коэффициенты для матча {odds_data['home_team']} vs {odds_data['away_team']}, результат: {result}")
                except Exception as e:
                    logger.error(f"Ошибка при обновлении исторических коэффициентов для матча {match.get('matchID')}: {e}")
            
            logger.info(f"Обновление исторических коэффициентов завершено. Обновлено {len(updated_data)} матчей")
            return updated_data
        except Exception as e:
            logger.error(f"Ошибка при обновлении исторических коэффициентов: {e}")
            return {}

# Запуск сбора коэффициентов при запуске скрипта напрямую
if __name__ == "__main__":
    collector = OddsCollector()
    odds_data = collector.collect_odds_for_all_matches()
    print(f"Собраны коэффициенты для {len(odds_data)} матчей")
    
    # Попытка обновить исторические коэффициенты
    print("Обновление исторических коэффициентов...")
    historical_updates = collector.update_historical_odds()
    print(f"Обновлено исторических записей: {len(historical_updates)}")