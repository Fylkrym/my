# data_collector.py
"""
Модуль для сбора данных о командах и матчах Бундеслиги с использованием OpenLigaDB API
"""

import os
import json
import requests
import logging
from datetime import datetime, timedelta
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
logger = logging.getLogger("DataCollector")


class BundesligaDataCollector:
    """Класс для сбора данных о командах и матчах Бундеслиги"""
    
    def __init__(self):
        """Инициализирует сборщик данных"""
        # Создаем необходимые директории, если они не существуют
        for directory in [DATA_DIR, MATCHES_DIR, ODDS_DIR, PREDICTIONS_DIR]:
            os.makedirs(directory, exist_ok=True)
        
        logger.info("Инициализирован сборщик данных для Бундеслиги")
    
    def get_teams(self):
        """
        Получает информацию о командах Бундеслиги
        
        Returns:
            list: Список команд с их данными
        """
        logger.info("Получение информации о командах Бундеслиги")
        
        # Формируем URL для запроса к API
        url = f"{OPENLIGA_API_URL}/getavailableteams/{LEAGUE_NAME}/{CURRENT_SEASON}"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            
            teams = response.json()
            logger.info(f"Получена информация о {len(teams)} командах")
            
            # Сохраняем информацию о командах в JSON
            teams_file = f"{DATA_DIR}/bundesliga_teams.json"
            
            # Преобразуем данные в более удобный формат
            formatted_teams = []
            for team in teams:
                formatted_teams.append({
                    'team_id': team.get('TeamId'),
                    'team_name': team.get('TeamName'),
                    'short_name': team.get('ShortName'),
                    'team_icon_url': team.get('TeamIconUrl')
                })
            
            with open(teams_file, 'w', encoding='utf-8') as f:
                json.dump(formatted_teams, f, indent=4, ensure_ascii=False)
            
            logger.info(f"Информация о командах сохранена в {teams_file}")
            return formatted_teams
        
        except Exception as e:
            logger.error(f"Ошибка при получении информации о командах: {e}")
            return []
    
    def get_matches(self, past=True, future=True):
        """
        Получает информацию о матчах Бундеслиги (прошедших и будущих)
        
        Args:
            past (bool): Если True, собирает информацию о прошедших матчах
            future (bool): Если True, собирает информацию о будущих матчах
            
        Returns:
            tuple: (прошедшие матчи, будущие матчи)
        """
        logger.info("Получение информации о матчах Бундеслиги")
        
        # Формируем URL для запроса к API
        url = f"{OPENLIGA_API_URL}/{LEAGUE_NAME}/{CURRENT_SEASON}"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            
            all_matches = response.json()
            logger.info(f"Получена информация о {len(all_matches)} матчах")
            
            # Разделяем матчи на прошедшие и будущие
            current_time = datetime.now()
            past_matches = []
            future_matches = []
            
            for match in all_matches:
                # Парсим дату матча
                match_time_str = match.get('MatchDateTime')
                match_time = datetime.fromisoformat(match_time_str.replace('Z', '+00:00'))
                
                # Если матч уже состоялся и имеет результаты
                if match_time < current_time and match.get('MatchResults'):
                    past_matches.append(match)
                else:
                    future_matches.append(match)
            
            # Сохраняем прошедшие матчи, если нужно
            if past and past_matches:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                past_match_file = f"{MATCHES_DIR}/past_matches_{timestamp}.json"
                
                with open(past_match_file, 'w', encoding='utf-8') as f:
                    json.dump(past_matches, f, indent=4, ensure_ascii=False)
                
                logger.info(f"Информация о {len(past_matches)} прошедших матчах сохранена в {past_match_file}")
            
            # Сохраняем будущие матчи, если нужно
            if future and future_matches:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                future_match_file = f"{MATCHES_DIR}/future_matches_{timestamp}.json"
                
                with open(future_match_file, 'w', encoding='utf-8') as f:
                    json.dump(future_matches, f, indent=4, ensure_ascii=False)
                
                logger.info(f"Информация о {len(future_matches)} предстоящих матчах сохранена в {future_match_file}")
            
            return (past_matches, future_matches)
        
        except Exception as e:
            logger.error(f"Ошибка при получении информации о матчах: {e}")
            return ([], [])
    
    def collect_all_data(self):
        """
        Собирает все необходимые данные для анализа
        
        Returns:
            dict: Словарь с собранными данными
        """
        logger.info("Начинаем сбор всех данных для анализа")
        
        # Получаем информацию о командах
        teams = self.get_teams()
        
        # Получаем информацию о матчах
        past_matches, future_matches = self.get_matches()
        
        return {
            'teams': teams,
            'past_matches': past_matches,
            'future_matches': future_matches,
            'timestamp': datetime.now().isoformat()
        }


# Запуск сбора данных при запуске скрипта напрямую
if __name__ == "__main__":
    collector = BundesligaDataCollector()
    data = collector.collect_all_data()
    
    print(f"Собрана информация о {len(data['teams'])} командах")
    print(f"Обработано {len(data['past_matches'])} прошедших матчей")
    print(f"Обработано {len(data['future_matches'])} предстоящих матчей")