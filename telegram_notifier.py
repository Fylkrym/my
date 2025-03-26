# telegram_notifier.py
"""
Модуль для отправки уведомлений в Telegram о прогнозах и ставках
"""

import os
import json
import requests
import logging
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
logger = logging.getLogger("TelegramNotifier")


class TelegramNotifier:
    """Класс для отправки уведомлений в Telegram"""
    
    def __init__(self, token=None, chat_id=None):
        """
        Инициализирует нотификатор
        
        Args:
            token (str): Токен Telegram бота
            chat_id (str): ID чата для отправки сообщений
        """
        self.token = token or TELEGRAM_BOT_TOKEN
        self.chat_id = chat_id or TELEGRAM_CHAT_ID
        self.api_url = f"https://api.telegram.org/bot{self.token}"
        
        if not self.token or not self.chat_id:
            logger.warning("Токен бота или ID чата не указаны. Уведомления в Telegram не будут отправляться.")
    
    def send_message(self, text):
        """
        Отправляет текстовое сообщение в Telegram
        
        Args:
            text (str): Текст сообщения
            
        Returns:
            bool: True, если отправка успешна, иначе False
        """
        if not self.token or not self.chat_id:
            return False
        
        try:
            url = f"{self.api_url}/sendMessage"
            data = {
                'chat_id': self.chat_id,
                'text': text,
                'parse_mode': 'Markdown'
            }
            
            response = requests.post(url, data=data)
            response.raise_for_status()
            
            logger.info(f"Сообщение успешно отправлено в Telegram")
            return True
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения в Telegram: {e}")
            return False
    
    def notify_value_bet(self, bet_data):
        """
        Отправляет уведомление о ценной ставке
        
        Args:
            bet_data (dict): Информация о ставке
            
        Returns:
            bool: True, если отправка успешна, иначе False
        """
        try:
            # Определяем тип ставки
            outcome = bet_data['outcome']
            if outcome in ['1', 'X', '2']:
                if outcome == '1':
                    bet_type = "П1 (победа хозяев)"
                elif outcome == 'X':
                    bet_type = "Х (ничья)"
                else:
                    bet_type = "П2 (победа гостей)"
            elif outcome.startswith('Over') or outcome.startswith('Under'):
                bet_type = outcome
            else:
                bet_type = outcome
            
            # Формируем текст сообщения
            message = f"*🔥 ЦЕННАЯ СТАВКА 🔥*\n\n"
            message += f"*Матч:* {bet_data['home_team']} vs {bet_data['away_team']}\n"
            message += f"*Дата:* {bet_data['date']}\n"
            message += f"*Ставка:* {bet_type}\n"
            message += f"*Коэффициент:* {bet_data['odds']}\n"
            message += f"*Ценность:* {bet_data['value']*100:.1f}%\n\n"
            
            # Добавляем информацию о прогнозе
            if 'expected_goals' in bet_data:
                message += f"*Ожидаемые голы:*\n"
                message += f"- {bet_data['home_team']}: {bet_data['expected_goals']['home']}\n"
                message += f"- {bet_data['away_team']}: {bet_data['expected_goals']['away']}\n"
            
            message += f"\n💰 *Рекомендуемая ставка:* {bet_data.get('amount', 0)} ед."
            
            return self.send_message(message)
        except Exception as e:
            logger.error(f"Ошибка при создании уведомления о ставке: {e}")
            return False
    
    def notify_daily_predictions(self, predictions, max_bets=5):
        """
        Отправляет ежедневную сводку с прогнозами
        
        Args:
            predictions (list): Список прогнозов
            max_bets (int): Максимальное количество предлагаемых ставок
            
        Returns:
            bool: True, если отправка успешна, иначе False
        """
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            
            # Фильтруем прогнозы на сегодня
            today_predictions = [
                p for p in predictions 
                if p.get('date', '').startswith(today)
            ]
            
            if not today_predictions:
                logger.info(f"Нет прогнозов на сегодня ({today})")
                return True
            
            # Сортируем по ценности ставок
            valuable_predictions = []
            for pred in today_predictions:
                for bet in pred.get('valuable_bets', []):
                    valuable_predictions.append({
                        'match_id': pred['match_id'],
                        'date': pred['date'],
                        'home_team': pred['home_team'],
                        'away_team': pred['away_team'],
                        'outcome': bet['outcome'],
                        'odds': bet['odds'],
                        'value': bet['value'],
                        'expected_goals': pred['expected_goals']
                    })
            
            # Сортируем по ценности
            valuable_predictions = sorted(valuable_predictions, key=lambda x: x['value'], reverse=True)
            
            # Формируем сообщение
            message = f"*📊 ПРОГНОЗЫ НА {today} 📊*\n\n"
            
            if valuable_predictions:
                message += f"*Топ {min(max_bets, len(valuable_predictions))} ценных ставок:*\n\n"
                
                for i, bet in enumerate(valuable_predictions[:max_bets], 1):
                    outcome_name = "П1" if bet['outcome'] == '1' else "Х" if bet['outcome'] == 'X' else "П2"
                    message += f"{i}. *{bet['home_team']} vs {bet['away_team']}*\n"
                    message += f"   Ставка: {outcome_name}, Коэф: {bet['odds']}, Ценность: {bet['value']*100:.1f}%\n"
                    message += f"   Прогноз: {bet['home_team']} {bet['expected_goals']['home']} - {bet['expected_goals']['away']} {bet['away_team']}\n\n"
            else:
                message += "🔍 Нет ценных ставок на сегодня.\n\n"
            
            message += "Удачи! 🍀"
            
            return self.send_message(message)
        except Exception as e:
            logger.error(f"Ошибка при создании ежедневной сводки: {e}")
            return False


# Пример использования при запуске скрипта напрямую
if __name__ == "__main__":
    # Проверяем настройки Telegram
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Для использования уведомлений в Telegram необходимо указать TELEGRAM_BOT_TOKEN и TELEGRAM_CHAT_ID в config.py")
    else:
        notifier = TelegramNotifier()
        notifier.send_message("👋 Привет! Система прогнозирования Бундеслиги запущена и готова отправлять уведомления.")