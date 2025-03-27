# match_odds_linker.py
"""
Скрипт для связывания матчей с коэффициентами от The Odds API
"""

import os
import json
import glob
import logging
from datetime import datetime
from team_mappings import normalize_team_name

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
logger = logging.getLogger("MatchOddsLinker")

def match_odds_with_matches():
    """
    Связывает файлы с коэффициентами и файлы с матчами на основе названий команд и дат
    """
    logger.info("Начинаем связывание матчей с коэффициентами")
    print("Начинаем связывание матчей с коэффициентами...")
    
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
        
        logger.info(f"Загружено {len(future_matches)} предстоящих матчей для связывания")
        print(f"Загружено {len(future_matches)} предстоящих матчей")
        
        # Загружаем все файлы с коэффициентами
        odds_files = glob.glob(f"{ODDS_DIR}/odds_*.json")
        
        if not odds_files:
            logger.error("Файлы с коэффициентами не найдены")
            print("Ошибка: Файлы с коэффициентами не найдены")
            return False
        
        logger.info(f"Найдено {len(odds_files)} файлов с коэффициентами")
        print(f"Найдено {len(odds_files)} файлов с коэффициентами")
        
        # Создаем словарь коэффициентов по командам и датам
        odds_data = {}
        
        for odds_file in odds_files:
            try:
                with open(odds_file, 'r', encoding='utf-8') as f:
                    odds_info = json.load(f)
                
                # Ключ: (дом. команда, гост. команда, дата)
                home_team = normalize_team_name(odds_info.get('home_team', ''))
                away_team = normalize_team_name(odds_info.get('away_team', ''))
                match_date = odds_info.get('date', '')
                
                key = (home_team, away_team, match_date)
                odds_data[key] = {
                    'file': odds_file,
                    'odds': odds_info.get('odds', {}),
                    'match_id': odds_info.get('match_id', '')
                }
            except Exception as e:
                logger.error(f"Ошибка при обработке файла {odds_file}: {e}")
        
        # Счетчики
        matches_with_odds = 0
        matches_without_odds = 0
        link_entries = []
        
        # Связываем матчи с коэффициентами
        for match in future_matches:
            match_id = match.get('matchID', '')
            home_team = normalize_team_name(match.get('team1', {}).get('teamName', ''))
            away_team = normalize_team_name(match.get('team2', {}).get('teamName', ''))
            match_date = match.get('matchDateTime', '')
            
            # Создаем ключ для поиска
            key = (home_team, away_team, match_date)
            
            # Также проверяем обратный порядок команд
            key_reverse = (away_team, home_team, match_date)
            
            if key in odds_data:
                # Создаем символическую связь в виде копии файла с ID матча
                source_file = odds_data[key]['file']
                with open(source_file, 'r', encoding='utf-8') as f:
                    odds_content = json.load(f)
                
                # Обновляем ID матча в файле
                odds_content['match_id'] = match_id
                
                # Сохраняем с ID матча
                target_file = f"{ODDS_DIR}/odds_{match_id}.json"
                with open(target_file, 'w', encoding='utf-8') as f:
                    json.dump(odds_content, f, indent=4, ensure_ascii=False)
                
                logger.info(f"Связь создана: {home_team} vs {away_team} -> {match_id}")
                matches_with_odds += 1
                
                link_entries.append({
                    'match_id': match_id,
                    'home_team': home_team,
                    'away_team': away_team,
                    'date': match_date,
                    'odds_file': target_file
                })
            elif key_reverse in odds_data:
                # Тот же процесс для обратного порядка команд
                source_file = odds_data[key_reverse]['file']
                with open(source_file, 'r', encoding='utf-8') as f:
                    odds_content = json.load(f)
                
                # Поменяем местами команды и обновим ID
                odds_content['match_id'] = match_id
                odds_content['home_team'] = home_team
                odds_content['away_team'] = away_team
                
                # Меняем местами коэффициенты
                if 'odds' in odds_content:
                    odds = odds_content['odds']
                    odds_content['odds'] = {
                        '1': odds.get('2', 0),
                        '2': odds.get('1', 0),
                        'X': odds.get('X', 0)
                    }
                
                # Сохраняем с ID матча
                target_file = f"{ODDS_DIR}/odds_{match_id}.json"
                with open(target_file, 'w', encoding='utf-8') as f:
                    json.dump(odds_content, f, indent=4, ensure_ascii=False)
                
                logger.info(f"Связь создана (обратный порядок): {home_team} vs {away_team} -> {match_id}")
                matches_with_odds += 1
                
                link_entries.append({
                    'match_id': match_id,
                    'home_team': home_team,
                    'away_team': away_team,
                    'date': match_date,
                    'odds_file': target_file
                })
            else:
                logger.warning(f"Не найдены коэффициенты для матча: {home_team} vs {away_team} ({match_date})")
                matches_without_odds += 1
        
        # Сохраняем информацию о связях
        links_file = f"{DATA_DIR}/match_odds_links.json"
        with open(links_file, 'w', encoding='utf-8') as f:
            json.dump(link_entries, f, indent=4, ensure_ascii=False)
        
        logger.info(f"Связывание завершено: {matches_with_odds} матчей связаны с коэффициентами, {matches_without_odds} без коэффициентов")
        print(f"Связывание завершено: {matches_with_odds} матчей связаны с коэффициентами, {matches_without_odds} без коэффициентов")
        print(f"Информация о связях сохранена в {links_file}")
        
        return True
    except Exception as e:
        logger.error(f"Ошибка при связывании матчей с коэффициентами: {e}")
        print(f"Ошибка при связывании матчей с коэффициентами: {e}")
        return False

if __name__ == "__main__":
    match_odds_with_matches()