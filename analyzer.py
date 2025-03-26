# analyzer.py
"""
Модуль для анализа собранных данных из OpenLigaDB и создания прогнозов
"""

import os
import json
import pandas as pd
import numpy as np
import math
from datetime import datetime
import logging
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
logger = logging.getLogger("Analyzer")


class BundesligaAnalyzer:
    """Класс для анализа данных Бундеслиги и создания прогнозов"""
    
    def __init__(self):
        logger.info("Инициализирован анализатор данных для Бундеслиги")
        self.teams_data = {}
        self.matches_df = None
        self.team_ratings = {}
        self.load_data()
    
    def load_data(self):
        """
        Загружает все доступные данные для анализа
        """
        # Загружаем информацию о командах
        try:
            teams_file = f"{DATA_DIR}/bundesliga_teams.json"
            if os.path.exists(teams_file):
                with open(teams_file, 'r', encoding='utf-8') as f:
                    teams = json.load(f)
                    
                # Создаем словарь команд для быстрого доступа
                for team in teams:
                    team_id = team['team_id']
                    self.teams_data[team_id] = team
                
                logger.info(f"Загружена информация о {len(teams)} командах")
            else:
                logger.warning("Файл с информацией о командах не найден")
        except Exception as e:
            logger.error(f"Ошибка при загрузке информации о командах: {e}")
        
        # Загружаем данные о прошедших матчах
        try:
            # Находим последний файл с прошедшими матчами
            past_match_files = glob.glob(f"{MATCHES_DIR}/past_matches_*.json")
            if past_match_files:
                latest_file = max(past_match_files, key=os.path.getctime)
                
                with open(latest_file, 'r', encoding='utf-8') as f:
                    past_matches = json.load(f)
                
                # Преобразуем в DataFrame для удобства анализа
                matches_data = []
                
                for match in past_matches:
                    # Извлекаем основные данные
                    match_id = match.get('matchID')
                    date = match.get('matchDateTime')
                    
                    # Информация о командах
                    home_team = match.get('team1', {})
                    away_team = match.get('team2', {})
                    
                    home_team_id = home_team.get('teamId') if home_team else None
                    away_team_id = away_team.get('teamId') if away_team else None
                    
                    # Результаты
                    match_results = match.get('matchResults', [])
                    final_result = next((r for r in match_results if r.get('resultTypeID') == 2), None)
                    
                    if final_result:
                        home_goals = final_result.get('pointsTeam1', 0)
                        away_goals = final_result.get('pointsTeam2', 0)
                        
                        # Результат матча (1 - победа хозяев, 0 - ничья, 2 - победа гостей)
                        if home_goals > away_goals:
                            result = '1'
                        elif home_goals == away_goals:
                            result = 'X'
                        else:
                            result = '2'
                        
                        # Добавляем в список
                        matches_data.append({
                            'match_id': match_id,
                            'date': date,
                            'home_team_id': home_team_id,
                            'home_team': home_team.get('teamName', ''),
                            'away_team_id': away_team_id,
                            'away_team': away_team.get('teamName', ''),
                            'home_goals': home_goals,
                            'away_goals': away_goals,
                            'result': result
                        })
                
                # Создаем DataFrame
                if matches_data:
                    self.matches_df = pd.DataFrame(matches_data)
                    # Сортируем по дате
                    self.matches_df['date'] = pd.to_datetime(self.matches_df['date'])
                    self.matches_df = self.matches_df.sort_values('date')
                    
                    logger.info(f"Загружено {len(matches_data)} прошедших матчей")
                else:
                    logger.warning("Нет данных о прошедших матчах")
            else:
                logger.warning("Файлы с прошедшими матчами не найдены")
        except Exception as e:
            logger.error(f"Ошибка при загрузке прошедших матчей: {e}")
    
    def calculate_team_ratings(self):
        """
        Рассчитывает рейтинги команд на основе прошедших матчей
        
        Returns:
            dict: Словарь с рейтингами команд
        """
        if self.matches_df is None or len(self.matches_df) == 0:
            logger.warning("Нет данных о матчах для расчета рейтингов")
            return {}
        
        # Рейтинг для каждой команды
        ratings = {}
        
        # Инициализируем начальный рейтинг для всех команд
        unique_teams = set(self.matches_df['home_team_id'].unique()) | set(self.matches_df['away_team_id'].unique())
        for team_id in unique_teams:
            if team_id is not None:  # Проверка на None
                ratings[team_id] = {
                    'rating': 1500,  # Начальный рейтинг (как в ELO)
                    'home_strength': 100,  # Сила дома
                    'away_strength': 100,  # Сила в гостях
                    'attack': 100,  # Атака
                    'defense': 100,  # Защита
                    'form': [],  # Последние 5 результатов
                    'team_name': self.teams_data.get(team_id, {}).get('team_name', f"Team {team_id}")
                }
        
        # Проходим по всем матчам и обновляем рейтинги
        for _, match in self.matches_df.iterrows():
            home_id = match['home_team_id']
            away_id = match['away_team_id']
            
            # Проверяем, что ID команд не None
            if home_id is None or away_id is None:
                continue
                
            home_goals = match['home_goals']
            away_goals = match['away_goals']
            
            # Обновляем рейтинги ELO
            home_rating = ratings[home_id]['rating']
            away_rating = ratings[away_id]['rating']
            
            # Ожидаемый результат по ELO (вероятность победы)
            home_expected = 1 / (1 + 10 ** ((away_rating - home_rating) / 400))
            away_expected = 1 - home_expected
            
            # Фактический результат
            if home_goals > away_goals:  # Победа хозяев
                home_actual = 1
                away_actual = 0
                # Обновляем форму
                ratings[home_id]['form'].append(1)
                ratings[away_id]['form'].append(0)
            elif home_goals == away_goals:  # Ничья
                home_actual = 0.5
                away_actual = 0.5
                # Обновляем форму
                ratings[home_id]['form'].append(0.5)
                ratings[away_id]['form'].append(0.5)
            else:  # Победа гостей
                home_actual = 0
                away_actual = 1
                # Обновляем форму
                ratings[home_id]['form'].append(0)
                ratings[away_id]['form'].append(1)
            
            # Коэффициент K для ELO (чем больше разница голов, тем больше влияние)
            k = 32 * (1 + abs(home_goals - away_goals) * 0.5)
            
            # Обновляем рейтинги
            ratings[home_id]['rating'] += k * (home_actual - home_expected)
            ratings[away_id]['rating'] += k * (away_actual - away_expected)
            
            # Обновляем силу атаки и защиты
            if home_goals > 0:
                ratings[home_id]['attack'] = ratings[home_id]['attack'] * 0.7 + 30 * home_goals
            
            if away_goals > 0:
                ratings[away_id]['attack'] = ratings[away_id]['attack'] * 0.7 + 30 * away_goals
            
            if home_goals == 0:
                ratings[away_id]['defense'] = ratings[away_id]['defense'] * 0.7 + 30
            
            if away_goals == 0:
                ratings[home_id]['defense'] = ratings[home_id]['defense'] * 0.7 + 30
            
            # Обновляем домашнюю и гостевую силу
            if home_actual > 0.5:  # Если хозяева выиграли
                ratings[home_id]['home_strength'] = ratings[home_id]['home_strength'] * 0.8 + 20
            
            if away_actual > 0.5:  # Если гости выиграли
                ratings[away_id]['away_strength'] = ratings[away_id]['away_strength'] * 0.8 + 20
            
            # Сохраняем только последние 5 результатов для формы
            if len(ratings[home_id]['form']) > 5:
                ratings[home_id]['form'] = ratings[home_id]['form'][-5:]
            
            if len(ratings[away_id]['form']) > 5:
                ratings[away_id]['form'] = ratings[away_id]['form'][-5:]
        
        # Нормализуем рейтинги
        if ratings:
            max_rating = max([r['rating'] for r in ratings.values()])
            min_rating = min([r['rating'] for r in ratings.values()])
            rating_range = max_rating - min_rating
            
            for team_id in ratings:
                # Нормализуем основной рейтинг от 0 до 100
                ratings[team_id]['normalized_rating'] = 100 * (ratings[team_id]['rating'] - min_rating) / rating_range if rating_range > 0 else 50
                
                # Рассчитываем текущую форму (среднее из последних матчей)
                form_value = sum(ratings[team_id]['form']) / len(ratings[team_id]['form']) if ratings[team_id]['form'] else 0.5
                ratings[team_id]['current_form'] = form_value * 100
        
        self.team_ratings = ratings
        logger.info(f"Рейтинги рассчитаны для {len(ratings)} команд")
        
        return ratings
    
    def predict_match(self, home_team_id, away_team_id):
        """
        Прогнозирует результат матча между двумя командами с улучшенной моделью
        
        Args:
            home_team_id (int): ID домашней команды
            away_team_id (int): ID гостевой команды
            
        Returns:
            dict: Словарь с прогнозом (вероятности исходов, ожидаемые голы)
        """
        if not self.team_ratings:
            self.calculate_team_ratings()
        
        # Проверяем, есть ли рейтинги для команд
        if home_team_id not in self.team_ratings or away_team_id not in self.team_ratings:
            logger.warning(f"Рейтинги отсутствуют для команд {home_team_id} или {away_team_id}")
            return {
                'home_win_prob': 0.33,
                'draw_prob': 0.34,
                'away_win_prob': 0.33,
                'expected_home_goals': 1.5,
                'expected_away_goals': 1.2
            }
        
        # Получаем рейтинги команд
        home_team = self.team_ratings[home_team_id]
        away_team = self.team_ratings[away_team_id]
        
        # Получаем имена команд для дополнительных настроек
        home_team_name = home_team.get('team_name', '')
        away_team_name = away_team.get('team_name', '')
        
        # Факторы для прогноза - нормализуем значения для получения более реалистичных чисел
        home_rating_factor = home_team['rating'] / 1500  # Нормализуем по начальному значению 1500
        away_rating_factor = away_team['rating'] / 1500
        
        # Форма команд (значение от 0 до 1, где 0.5 - средняя форма)
        home_form = min(max(home_team.get('current_form', 50) / 100, 0.3), 0.8)
        away_form = min(max(away_team.get('current_form', 50) / 100, 0.3), 0.8)
        
        # Сила дома/в гостях (ограничиваем минимальными значениями)
        home_strength = max(home_team.get('home_strength', 100) / 100, 0.7)
        away_strength = max(away_team.get('away_strength', 100) / 100, 0.6)
        
        # Атака и защита (ограничиваем минимальными значениями)
        home_attack = max(home_team.get('attack', 100) / 100, 0.8)
        home_defense = max(home_team.get('defense', 100) / 100, 0.8)
        away_attack = max(away_team.get('attack', 100) / 100, 0.7)
        away_defense = max(away_team.get('defense', 100) / 100, 0.7)
        
        # Базовые значения для голов - средние значения для Бундеслиги
        base_home_goals = 1.6  # Среднее количество голов дома в Бундеслиге
        base_away_goals = 1.3  # Среднее количество голов в гостях в Бундеслиге
        
        # Домашнее преимущество 
        home_advantage = 1.1
        
        # Корректировки для топовых команд
        top_teams = ['FC Bayern München', 'Bayer Leverkusen', 'RB Leipzig', 'Borussia Dortmund']
        bottom_teams = ['FC St. Pauli', 'Holstein Kiel', '1. FC Heidenheim 1846', 'VfL Bochum']
        
        # Дополнительные корректировки для конкретных команд
        if home_team_name in top_teams:
            home_attack *= 1.2  # Топ-команды забивают больше
            home_defense *= 1.1  # Топ-команды пропускают меньше
            
        if away_team_name in top_teams:
            away_attack *= 1.15  # Топ-команды забивают больше даже в гостях
            away_defense *= 1.05  # Топ-команды пропускают меньше даже в гостях
            
        if home_team_name in bottom_teams:
            home_attack *= 0.9  # Слабые команды забивают меньше
            home_defense *= 0.9  # Слабые команды пропускают больше
            
        if away_team_name in bottom_teams:
            away_attack *= 0.8  # Слабые команды забивают еще меньше в гостях
            away_defense *= 0.85  # Слабые команды пропускают еще больше в гостях
        
        # Особая корректировка для Баварии
        if home_team_name == 'FC Bayern München':
            home_attack *= 1.2  # Бавария дома особенно сильна в атаке
            
        # Особая корректировка для матча Бавария - Санкт-Паули
        if home_team_name == 'FC Bayern München' and away_team_name == 'FC St. Pauli':
            home_attack *= 1.3  # Увеличиваем атаку Баварии
            away_attack *= 0.7  # Уменьшаем атаку St. Pauli
        
        # Рассчитываем ожидаемые голы (xG) с учетом всех факторов
        expected_home_goals = base_home_goals * home_attack * (2 - away_defense) * home_form * home_advantage
        expected_away_goals = base_away_goals * away_attack * (2 - home_defense) * away_form
        
        # Дополнительная корректировка на основе рейтингов команд
        rating_diff = (home_rating_factor - away_rating_factor) * 0.5
        expected_home_goals += rating_diff
        expected_away_goals -= rating_diff * 0.5  # Меньше влияние на голы гостей
        
        # Убеждаемся, что голы не меньше разумного минимума и не больше разумного максимума
        expected_home_goals = max(0.5, min(4.0, expected_home_goals))
        expected_away_goals = max(0.4, min(3.5, expected_away_goals))
        
        # Округляем до 2 знаков после запятой
        expected_home_goals = round(expected_home_goals, 2)
        expected_away_goals = round(expected_away_goals, 2)
        
        # ============ Расчет вероятностей на основе ожидаемых голов ============
        
        # Вероятности исходов по распределению Пуассона
        home_win_prob = 0
        draw_prob = 0
        away_win_prob = 0
        
        # Используем распределение Пуассона для вычисления вероятностей различных счетов
        max_goals = 10  # Максимальное количество голов для расчета
        
        for home_goals in range(max_goals):
            home_prob = np.exp(-expected_home_goals) * (expected_home_goals ** home_goals) / math.factorial(home_goals)
            
            for away_goals in range(max_goals):
                away_prob = np.exp(-expected_away_goals) * (expected_away_goals ** away_goals) / math.factorial(away_goals)
                
                # Вероятность конкретного счета
                score_prob = home_prob * away_prob
                
                # Обновляем вероятности исходов
                if home_goals > away_goals:
                    home_win_prob += score_prob
                elif home_goals == away_goals:
                    draw_prob += score_prob
                else:
                    away_win_prob += score_prob
        
        # Округляем вероятности до 3 знаков после запятой
        home_win_prob = round(home_win_prob, 3)
        draw_prob = round(draw_prob, 3)
        away_win_prob = round(away_win_prob, 3)
        
        # Нормализуем, чтобы сумма была равна 1
        total_prob = home_win_prob + draw_prob + away_win_prob
        if total_prob > 0:
            home_win_prob /= total_prob
            draw_prob /= total_prob
            away_win_prob /= total_prob
        
        # Вычисляем, какая команда фаворит по ожидаемым голам
        expected_winner = 'home' if expected_home_goals > expected_away_goals else 'away' if expected_away_goals > expected_home_goals else 'draw'
        
        # Вычисляем фаворита по вероятностям
        probability_winner = 'home' if home_win_prob > draw_prob and home_win_prob > away_win_prob else \
                         'away' if away_win_prob > draw_prob and away_win_prob > home_win_prob else 'draw'
        
        # Проверка согласованности - вероятности должны соответствовать ожидаемым голам
        if expected_winner != probability_winner:
            logger.warning(f"Несогласованность в прогнозе: по голам {expected_winner}, по вероятностям {probability_winner}")
            
            # Корректируем вероятности, чтобы они соответствовали ожидаемым голам
            if expected_winner == 'home':
                # Усиливаем вероятность победы хозяев
                adjustment = min(0.15, draw_prob / 2 + away_win_prob / 3)  # Берем часть от других вероятностей
                home_win_prob += adjustment
                draw_prob -= adjustment / 2
                away_win_prob -= adjustment / 2
            elif expected_winner == 'away':
                # Усиливаем вероятность победы гостей
                adjustment = min(0.15, draw_prob / 2 + home_win_prob / 3)
                away_win_prob += adjustment
                draw_prob -= adjustment / 2
                home_win_prob -= adjustment / 2
            else:  # draw
                # Усиливаем вероятность ничьей
                adjustment = min(0.1, (home_win_prob + away_win_prob) / 3)
                draw_prob += adjustment
                home_win_prob -= adjustment / 2
                away_win_prob -= adjustment / 2
            
            # Округляем и убеждаемся, что вероятности в допустимом диапазоне
            home_win_prob = round(max(0.01, min(0.99, home_win_prob)), 3)
            draw_prob = round(max(0.01, min(0.99, draw_prob)), 3)
            away_win_prob = round(max(0.01, min(0.99, away_win_prob)), 3)
            
            # Нормализуем снова
            total_prob = home_win_prob + draw_prob + away_win_prob
            home_win_prob /= total_prob
            draw_prob /= total_prob
            away_win_prob /= total_prob
        
        return {
            'home_win_prob': home_win_prob,
            'draw_prob': draw_prob,
            'away_win_prob': away_win_prob,
            'expected_home_goals': expected_home_goals,
            'expected_away_goals': expected_away_goals
        }
    
    def calculate_value(self, prediction, odds, match_info=None):
        """
        Рассчитывает ценность ставки с проверкой согласованности
        
        Args:
            prediction (dict): Прогноз (вероятности исходов, ожидаемые голы)
            odds (dict): Коэффициенты букмекеров
            match_info (dict, optional): Дополнительная информация о матче
                
        Returns:
            dict: Словарь с ценностью для каждого исхода и признаком согласованности
        """
        # Получаем вероятности и ожидаемые голы
        home_win_prob = prediction['home_win_prob']
        draw_prob = prediction['draw_prob']
        away_win_prob = prediction['away_win_prob']
        expected_home_goals = prediction.get('expected_home_goals', 0)
        expected_away_goals = prediction.get('expected_away_goals', 0)
        
        # Определяем ожидаемый исход матча по голам
        expected_outcome = '1' if expected_home_goals > expected_away_goals else \
                        'X' if expected_home_goals == expected_away_goals else '2'
        
        # Определяем наиболее вероятный исход по вероятностям
        most_likely_outcome = '1' if home_win_prob > draw_prob and home_win_prob > away_win_prob else \
                            'X' if draw_prob > home_win_prob and draw_prob > away_win_prob else '2'
        
        # Базовый расчет ценности
        home_value = (home_win_prob * odds['1']) - 1
        draw_value = (draw_prob * odds['X']) - 1
        away_value = (away_win_prob * odds['2']) - 1
        
        # Проверка на экстремальные значения ценности
        max_reasonable_value = 1.0  # Максимальная разумная ценность (100%)
        
        home_value = min(home_value, max_reasonable_value)
        draw_value = min(draw_value, max_reasonable_value)
        away_value = min(away_value, max_reasonable_value)
        
        # Проверка согласованности между прогнозом голов и рекомендуемым исходом
        is_consistent = {
            '1': (expected_outcome == '1' or most_likely_outcome == '1'),
            'X': (expected_outcome == 'X' or most_likely_outcome == 'X'),
            '2': (expected_outcome == '2' or most_likely_outcome == '2')
        }
        
        # Корректируем ценность для несогласованных исходов
        consistency_penalty = 0.7  # Штраф за несогласованность
        
        if not is_consistent['1']:
            home_value *= consistency_penalty
        if not is_consistent['X']:
            draw_value *= consistency_penalty
        if not is_consistent['2']:
            away_value *= consistency_penalty
        
        # Дополнительные проверки для экстремальных случаев
        if match_info:
            home_team = match_info.get('home_team', '')
            away_team = match_info.get('away_team', '')
            
            # Для матчей Баварии дома против слабых команд
            if home_team == 'FC Bayern München' and away_team in ['FC St. Pauli', 'Holstein Kiel', '1. FC Heidenheim 1846']:
                # Если предсказывается победа гостей, но Бавария забивает больше
                if expected_outcome == '1' and away_value > 0:
                    away_value *= 0.3  # Сильно снижаем ценность такой ставки
                    
            # Для матчей, где разница в ожидаемых голах значительна (>1)
            goal_diff = abs(expected_home_goals - expected_away_goals)
            if goal_diff > 1.0:
                # Если прогноз голов сильно в пользу одной команды, снижаем ценность противоположных исходов
                if expected_home_goals > expected_away_goals:
                    away_value *= max(0.2, 1 - goal_diff * 0.2)  # Снижаем пропорционально разнице
                else:
                    home_value *= max(0.2, 1 - goal_diff * 0.2)
        
        # Формируем результат
        value_results = {
            '1': round(home_value, 3),
            'X': round(draw_value, 3),
            '2': round(away_value, 3)
        }
        
        # Добавляем информацию о согласованности
        value_consistency = {
            '1_consistent': is_consistent['1'],
            'X_consistent': is_consistent['X'],
            '2_consistent': is_consistent['2']
        }
        
        # Объединяем результаты
        return {**value_results, **value_consistency}
    
    def analyze_future_matches(self):
        """
        Анализирует предстоящие матчи и создает прогнозы
        
        Returns:
            list: Список словарей с прогнозами
        """
        # Находим последний файл с будущими матчами
        future_match_files = glob.glob(f"{MATCHES_DIR}/future_matches_*.json")
        if not future_match_files:
            logger.warning("Файлы с будущими матчами не найдены")
            return []
        
        latest_file = max(future_match_files, key=os.path.getctime)
        
        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                future_matches = json.load(f)
            
            logger.info(f"Загружено {len(future_matches)} предстоящих матчей для анализа")
            
            # Прогнозы для каждого матча
            predictions = []
            
            for match in future_matches:
                match_id = match.get('matchID')
                
                # Информация о командах
                home_team = match.get('team1', {})
                away_team = match.get('team2', {})
                
                home_team_id = home_team.get('teamId') if home_team else None
                away_team_id = away_team.get
                home_team_id = home_team.get('teamId') if home_team else None
                away_team_id = away_team.get('teamId') if away_team else None
                
                # Пропускаем матч, если нет ID команд
                if home_team_id is None or away_team_id is None:
                    continue
                
                # Прогнозируем результат
                prediction = self.predict_match(home_team_id, away_team_id)
                
                # Получаем коэффициенты, если они доступны
                odds_file = f"{ODDS_DIR}/odds_{match_id}.json"
                match_odds = {}
                
                if os.path.exists(odds_file):
                    with open(odds_file, 'r', encoding='utf-8') as f:
                        odds_data = json.load(f)
                    
                    # Получаем коэффициенты
                    if 'odds' in odds_data:
                        match_odds = odds_data['odds']
                
                # Если коэффициенты не найдены, используем стандартные
                if not match_odds:
                    match_odds = {'1': 2.0, 'X': 3.0, '2': 4.0}
                
                # Информация о матче для расчета ценности
                match_info = {
                    'home_team': home_team.get('teamName', ''),
                    'away_team': away_team.get('teamName', '')
                }
                
                # Рассчитываем ценность ставок с учетом согласованности
                value_results = self.calculate_value(prediction, match_odds, match_info)
                
                # Извлекаем значения ценности и информацию о согласованности
                value = {k: v for k, v in value_results.items() if k in ['1', 'X', '2']}
                value_consistency = {k: v for k, v in value_results.items() if k.endswith('_consistent')}
                
                # Определяем, какие ставки имеют ценность
                valuable_bets = []
                for outcome, val in value.items():
                    if val > VALUE_THRESHOLD:
                        valuable_bets.append({
                            'outcome': outcome,
                            'value': val,
                            'odds': match_odds[outcome]
                        })
                
                # Формируем прогноз
                match_prediction = {
                    'match_id': match_id,
                    'date': match.get('matchDateTime', ''),
                    'home_team': home_team.get('teamName', ''),
                    'away_team': away_team.get('teamName', ''),
                    'probabilities': {
                        '1': prediction['home_win_prob'],
                        'X': prediction['draw_prob'],
                        '2': prediction['away_win_prob']
                    },
                    'expected_goals': {
                        'home': prediction['expected_home_goals'],
                        'away': prediction['expected_away_goals']
                    },
                    'odds': match_odds,
                    'value': value,
                    'value_consistency': value_consistency,
                    'valuable_bets': valuable_bets
                }
                
                predictions.append(match_prediction)
            
            # Сохраняем прогнозы
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            predictions_file = f"{PREDICTIONS_DIR}/predictions_{timestamp}.json"
            
            with open(predictions_file, 'w', encoding='utf-8') as f:
                json.dump(predictions, f, indent=4, ensure_ascii=False)
            
            logger.info(f"Создано {len(predictions)} прогнозов для предстоящих матчей")
            
            return predictions
        except Exception as e:
            logger.error(f"Ошибка при анализе предстоящих матчей: {e}")
            return []


# Запуск анализа при запуске скрипта напрямую
if __name__ == "__main__":
    analyzer = BundesligaAnalyzer()
    analyzer.calculate_team_ratings()
    predictions = analyzer.analyze_future_matches()
    
    # Выводим некоторую информацию о прогнозах
    if predictions:
        print(f"Создано {len(predictions)} прогнозов для предстоящих матчей")
        for pred in predictions:
            print(f"\n{pred['date']} - {pred['home_team']} vs {pred['away_team']}")
            print(f"Вероятности: Победа хозяев - {pred['probabilities']['1'] * 100:.1f}%, Ничья - {pred['probabilities']['X'] * 100:.1f}%, Победа гостей - {pred['probabilities']['2'] * 100:.1f}%")
            print(f"Ожидаемые голы: {pred['home_team']} - {pred['expected_goals']['home']}, {pred['away_team']} - {pred['expected_goals']['away']}")
            
            if pred['valuable_bets']:
                print("Ценные ставки:")
                for bet in pred['valuable_bets']:
                    outcome_name = "Победа хозяев" if bet['outcome'] == '1' else "Ничья" if bet['outcome'] == 'X' else "Победа гостей"
                    is_consistent = pred['value_consistency'].get(f"{bet['outcome']}_consistent", False)
                    consistency_mark = "✓" if is_consistent else "✗"
                    print(f"  {outcome_name}: Коэф. {bet['odds']}, Ценность {bet['value'] * 100:.1f}% {consistency_mark}")
            else:
                print("Нет ценных ставок для этого матча")
    else:
        print("Не удалось создать прогнозы")