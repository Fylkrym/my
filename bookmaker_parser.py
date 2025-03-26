# bookmaker_parser.py
"""
Модуль для парсинга коэффициентов букмекеров для матчей Бундеслиги
"""

import requests
import pandas as pd
import logging
import re
import json
import os
import glob
import random
from datetime import datetime
from bs4 import BeautifulSoup

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
logger = logging.getLogger("BookmakerParser")


class BookmakerParser:
    """Класс для парсинга коэффициентов букмекеров"""
    
    def __init__(self):
        """Инициализирует парсер коэффициентов"""
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        logger.info("Инициализирован парсер коэффициентов")
    
    def get_all_odds(self, league="bundesliga"):
        """
        Получает коэффициенты для всех предстоящих матчей лиги
        
        Args:
            league (str): Название лиги (bundesliga, premier-league, etc.)
            
        Returns:
            pd.DataFrame: DataFrame с коэффициентами
        """
        try:
            # В реальном проекте здесь код для парсинга коэффициентов с сайтов букмекеров
            # В этом примере мы генерируем синтетические коэффициенты
            
            # Находим последний файл с будущими матчами
            future_match_files = glob.glob(f"{MATCHES_DIR}/future_matches_*.json")
            if not future_match_files:
                logger.warning("Файлы с будущими матчами не найдены")
                return pd.DataFrame()
            
            latest_file = max(future_match_files, key=os.path.getctime)
            
            with open(latest_file, 'r', encoding='utf-8') as f:
                future_matches = json.load(f)
            
            logger.info(f"Загружено {len(future_matches)} предстоящих матчей для получения коэффициентов")
            
            # Создаем DataFrame с синтетическими коэффициентами
            odds_data = []
            
            for match in future_matches:
                match_id = match.get('matchID')
                match_date_str = match.get('matchDateTime', '')
                
                # Преобразуем дату в нужный формат
                try:
                    match_date = datetime.fromisoformat(match_date_str.replace('Z', '+00:00'))
                    formatted_date = match_date.strftime("%Y-%m-%d %H:%M")
                except:
                    formatted_date = match_date_str
                
                # Информация о командах
                home_team = match.get('team1', {})
                away_team = match.get('team2', {})
                
                home_team_name = home_team.get('teamName', '')
                away_team_name = away_team.get('teamName', '')
                
                # Генерируем коэффициенты для основных исходов
                # Диапазоны основаны на средних значениях для Бундеслиги
                
                # Разные диапазоны для разных команд (топ-команды имеют более низкие коэффициенты)
                top_teams = ['FC Bayern München', 'Bayer Leverkusen', 'RB Leipzig', 'Borussia Dortmund']
                
                if home_team_name in top_teams:
                    # Топ-команда дома
                    home_win = round(random.uniform(1.2, 1.7), 2)
                    draw = round(random.uniform(3.5, 5.5), 2)
                    away_win = round(random.uniform(4.5, 8.0), 2)
                elif away_team_name in top_teams:
                    # Топ-команда в гостях
                    home_win = round(random.uniform(2.5, 4.5), 2)
                    draw = round(random.uniform(3.0, 4.5), 2)
                    away_win = round(random.uniform(1.7, 2.5), 2)
                else:
                    # Равные команды
                    home_win = round(random.uniform(2.0, 3.0), 2)
                    draw = round(random.uniform(3.0, 3.8), 2)
                    away_win = round(random.uniform(2.4, 3.5), 2)
                
                # Создаем специальные коэффициенты для особых матчей
                if home_team_name == 'FC Bayern München' and away_team_name == 'FC St. Pauli':
                    home_win = 1.18
                    draw = 7.50
                    away_win = 15.00
                
                # Добавляем запись в список
                odds_data.append({
                    'match_id': match_id,
                    'home_team': home_team_name,
                    'away_team': away_team_name,
                    'match_date': formatted_date,
                    'home_win': home_win,
                    'draw': draw,
                    'away_win': away_win,
                    'over_2.5': round(random.uniform(1.65, 2.10), 2),
                    'under_2.5': round(random.uniform(1.70, 2.25), 2),
                    'both_teams_to_score': round(random.uniform(1.70, 2.10), 2),
                    'bookmaker': 'Synthetic'
                })
            
            # Создаем DataFrame
            df = pd.DataFrame(odds_data)
            
            logger.info(f"Сгенерированы коэффициенты для {len(df)} матчей")
            return df
            
        except Exception as e:
            logger.error(f"Ошибка при получении коэффициентов: {e}")
            return pd.DataFrame()
    
    def normalize_team_names(self, odds_df):
        """
        Нормализует названия команд для совместимости с данными из OpenLigaDB
        
        Args:
            odds_df (pd.DataFrame): DataFrame с коэффициентами
            
        Returns:
            pd.DataFrame: DataFrame с нормализованными названиями команд
        """
        # Словарь соответствия названий команд
        team_name_mapping = {
            'Bayern': 'FC Bayern München',
            'Bayern Munich': 'FC Bayern München',
            'Munich': 'FC Bayern München',
            'Dortmund': 'Borussia Dortmund',
            'Bayer Leverkusen': 'Bayer 04 Leverkusen',
            'Leverkusen': 'Bayer 04 Leverkusen',
            'RB Leipzig': 'RasenBallsport Leipzig',
            'Leipzig': 'RasenBallsport Leipzig',
            'Gladbach': 'Borussia Mönchengladbach',
            'Monchengladbach': 'Borussia Mönchengladbach',
            'Borussia M.Gladbach': 'Borussia Mönchengladbach',
            'Wolfsburg': 'VfL Wolfsburg',
            'Eintracht Frankfurt': 'Eintracht Frankfurt',
            'Frankfurt': 'Eintracht Frankfurt',
            'Hoffenheim': 'TSG 1899 Hoffenheim',
            'Freiburg': 'SC Freiburg',
            'Mainz': '1. FSV Mainz 05',
            'Mainz 05': '1. FSV Mainz 05',
            'Union Berlin': '1. FC Union Berlin',
            'Berlin': '1. FC Union Berlin',
            'Koln': '1. FC Köln',
            'Cologne': '1. FC Köln',
            'FC Koln': '1. FC Köln',
            'Werder Bremen': 'SV Werder Bremen',
            'Bremen': 'SV Werder Bremen',
            'St Pauli': 'FC St. Pauli',
            'St. Pauli': 'FC St. Pauli',
            'Augsburg': 'FC Augsburg',
            'Holstein Kiel': 'Holstein Kiel',
            'Kiel': 'Holstein Kiel',
            'Heidenheim': '1. FC Heidenheim 1846',
            'FC Heidenheim': '1. FC Heidenheim 1846'
        }
        
        # Применяем маппинг к обеим колонкам с командами
        if 'home_team' in odds_df.columns and 'away_team' in odds_df.columns:
            for old_name, new_name in team_name_mapping.items():
                # Применяем только к точным совпадениям
                odds_df['home_team'] = odds_df['home_team'].replace(old_name, new_name)
                odds_df['away_team'] = odds_df['away_team'].replace(old_name, new_name)
        
        return odds_df


# Запуск сбора коэффициентов при запуске скрипта напрямую
if __name__ == "__main__":
    parser = BookmakerParser()
    odds_df = parser.get_all_odds()
    
    if not odds_df.empty:
        print(f"Получены коэффициенты для {len(odds_df)} матчей:")
        print(odds_df[['home_team', 'away_team', 'home_win', 'draw', 'away_win']].head())
    else:
        print("Не удалось получить коэффициенты")