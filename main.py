# main.py
"""
Главный файл для запуска системы прогнозирования Бундеслиги (OpenLigaDB)
"""

import os
import json
import logging
import traceback
from constants import *
from datetime import datetime
import pandas as pd

# Импортируем настройки
from config import *

# Импортируем модули нашей системы
from data_collector import BundesligaDataCollector
from analyzer import BundesligaAnalyzer

# Новые импорты для улучшенной версии
from odds_collector import OddsCollector
from visualizer import BundesligaVisualizer
from telegram_notifier import TelegramNotifier

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("BundesligaPredictor")


class BundesligaPredictor:
    """Главный класс системы прогнозирования"""
    
    def __init__(self):
        print("Инициализация системы прогнозирования Бундеслиги...")
        logger.info("Инициализация системы прогнозирования Бундеслиги")
        self.collector = BundesligaDataCollector()
        self.analyzer = BundesligaAnalyzer()
        self.bank = BANK_INITIAL
        self.bet_history = []
        
        # Загружаем историю ставок, если она существует
        self._load_bet_history()
        
        # Инициализируем дополнительные компоненты
        self.initialize_additional_components()
    
    def initialize_additional_components(self):
        """
        Инициализирует дополнительные компоненты системы
        """
        print("Инициализация дополнительных компонентов системы...")
        
        # Инициализация сборщика коэффициентов
        self.odds_collector = OddsCollector()
        
        # Инициализация визуализатора, если включено
        if VISUALIZATION:
            self.visualizer = BundesligaVisualizer()
        
        # Инициализация Telegram-нотификатора, если включено
        if TELEGRAM_NOTIFICATIONS and TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
            self.notifier = TelegramNotifier()
            print("Telegram уведомления включены")
        else:
            self.notifier = None
            print("Telegram уведомления отключены")
    
    def _load_bet_history(self):
        """Загружает историю ставок из CSV-файла"""
        history_file = f"{DATA_DIR}/bet_history.csv"
        
        if os.path.exists(history_file):
            try:
                history_df = pd.read_csv(history_file)
                self.bet_history = history_df.to_dict('records')
                
                # Обновляем текущий банк
                self.bank = BANK_INITIAL
                
                for bet in self.bet_history:
                    # Вычитаем сумму ставки из банка
                    self.bank -= bet['amount']
                    
                    # Если ставка выиграла, добавляем выигрыш
                    if bet['status'] == 'won':
                        self.bank += bet['potential_win']
                
                logger.info(f"Загружена история ставок: {len(self.bet_history)} ставок, текущий банк: {self.bank}")
                print(f"Загружена история ставок: {len(self.bet_history)} ставок, текущий банк: {self.bank}")
            except Exception as e:
                logger.error(f"Ошибка при загрузке истории ставок: {e}")
                print(f"Ошибка при загрузке истории ставок: {e}")
    
    def collect_data(self):
        """Собирает данные о матчах и коэффициентах"""
        print("Начинаем сбор данных...")
        logger.info("Начинаем сбор данных...")
        try:
            data = self.collector.collect_all_data()
            print("Сбор данных завершен успешно")
            logger.info("Сбор данных завершен")
            return data
        except Exception as e:
            print(f"ОШИБКА при сборе данных: {e}")
            logger.error(f"Ошибка при сборе данных: {e}")
            traceback.print_exc()
            return None
    
    def collect_data_improved(self):
        """
        Улучшенная версия сбора данных с более точными коэффициентами
        """
        print("Начинаем сбор данных...")
        logger.info("Начинаем сбор данных...")
        
        try:
            # Сбор данных о матчах
            data = self.collector.collect_all_data()
            
            # Сбор и обновление коэффициентов
            print("Сбор коэффициентов для предстоящих матчей...")
            
            # Пытаемся сначала получить коэффициенты через The Odds API
            from bookmaker_integration import get_odds_from_api
            odds_data = get_odds_from_api()
            
            if odds_data and len(odds_data) > 0:
                print(f"Получены реальные коэффициенты через The Odds API для {len(odds_data)} матчей")
            else:
                # Если не удалось получить через API, пробуем другие источники
                print("Не удалось получить коэффициенты через The Odds API")
                print("Пробуем получить коэффициенты через другие источники...")
                
                # Пытаемся получить реальные коэффициенты через парсер
                try:
                    from bookmaker_parser import BookmakerParser
                    parser = BookmakerParser()
                    odds_df = parser.get_all_odds()
                    
                    if not odds_df.empty:
                        print(f"Получены синтетические коэффициенты для {len(odds_df)} матчей")
                    else:
                        print("Не удалось получить синтетические коэффициенты")
                except Exception as e:
                    print(f"Ошибка при получении синтетических коэффициентов: {e}")
                    
                # Если предыдущие методы не сработали, используем внутренний генератор коэффициентов
                print("Используем внутренний генератор коэффициентов...")
                odds_data = self.odds_collector.collect_odds_for_all_matches()
                print(f"Сгенерированы коэффициенты для {len(odds_data)} матчей")
            
            # Обновление исторических коэффициентов для анализа
            self.odds_collector.update_historical_odds()
            
            print("Сбор данных завершен успешно")
            logger.info("Сбор данных завершен")
            
            return data
        except Exception as e:
            print(f"ОШИБКА при сборе данных: {e}")
            logger.error(f"Ошибка при сборе данных: {e}")
            traceback.print_exc()
            return None
    
    def generate_predictions(self):
        """Генерирует прогнозы для предстоящих матчей"""
        print("Начинаем анализ и создание прогнозов...")
        logger.info("Начинаем анализ и создание прогнозов...")
        try:
            # Сначала рассчитываем рейтинги команд
            print("Расчет рейтингов команд...")
            self.analyzer.calculate_team_ratings()
            
            # Затем анализируем предстоящие матчи
            print("Анализ предстоящих матчей...")
            predictions = self.analyzer.analyze_future_matches()
            
            print(f"Создано {len(predictions)} прогнозов")
            logger.info(f"Создано {len(predictions)} прогнозов")
            return predictions
        except Exception as e:
            print(f"ОШИБКА при создании прогнозов: {e}")
            logger.error(f"Ошибка при создании прогнозов: {e}")
            traceback.print_exc()
            return []
    
    def suggest_bets(self, predictions, min_value=0.1, max_bets=5):
        """
        Предлагает ставки на основе прогнозов с проверкой на согласованность
        
        Args:
            predictions (list): Список прогнозов
            min_value (float): Минимальная ценность для предложения ставки
            max_bets (int): Максимальное количество предлагаемых ставок
            
        Returns:
            list: Список предлагаемых ставок
        """
        print("Выбираем ставки для предложения...")
        logger.info("Выбираем ставки для предложения...")
        
        try:
            # Проверяем, что есть прогнозы
            if not predictions:
                print("Нет прогнозов для предложения ставок")
                return []
                
            # Сортируем все ценные ставки по убыванию ценности
            all_bets = []
            
            for pred in predictions:
                valuable_bets = pred.get('valuable_bets', [])
                for bet in valuable_bets:
                    # Проверяем ценность и согласованность
                    outcome_key = f"{bet['outcome']}_consistent"
                    is_consistent = pred.get('value_consistency', {}).get(outcome_key, True)
                    
                    if bet['value'] >= min_value:
                        # Создаем запись о ставке с дополнительной информацией
                        bet_info = {
                            'match_id': pred['match_id'],
                            'date': pred['date'],
                            'home_team': pred['home_team'],
                            'away_team': pred['away_team'],
                            'outcome': bet['outcome'],
                            'odds': bet['odds'],
                            'value': bet['value'],
                            'expected_goals': pred['expected_goals'],
                            'is_consistent': is_consistent
                        }
                        
                        # Добавляем информацию о согласованности с ожидаемыми голами
                        home_goals = pred['expected_goals']['home']
                        away_goals = pred['expected_goals']['away']
                        
                        if bet['outcome'] == '1' and home_goals <= away_goals:
                            bet_info['has_contradiction'] = True
                            bet_info['contradiction_details'] = f"Ставка на П1, но ожидаемые голы: {home_goals}-{away_goals}"
                        elif bet['outcome'] == '2' and away_goals <= home_goals:
                            bet_info['has_contradiction'] = True
                            bet_info['contradiction_details'] = f"Ставка на П2, но ожидаемые голы: {home_goals}-{away_goals}"
                        else:
                            bet_info['has_contradiction'] = False
                            
                        all_bets.append(bet_info)
            
            # Фильтруем ставки без противоречий и с согласованностью
            consistent_bets = [bet for bet in all_bets if not bet.get('has_contradiction', False) and bet.get('is_consistent', True)]
            
            # Если после фильтрации не осталось ставок, можем вернуться к лучшим ставкам по ценности
            if not consistent_bets and all_bets:
                logger.warning("Нет согласованных ставок, используем ставки с наибольшей ценностью")
                print("Предупреждение: Нет согласованных ставок, используем ставки с наибольшей ценностью")
                
                # Сортируем по ценности (от большей к меньшей)
                all_bets = sorted(all_bets, key=lambda x: x['value'], reverse=True)
                
                # Выбираем лучшие ставки
                suggested_bets = all_bets[:max_bets]
            else:
                # Сортируем согласованные ставки по ценности
                consistent_bets = sorted(consistent_bets, key=lambda x: x['value'], reverse=True)
                
                # Выбираем лучшие согласованные ставки
                suggested_bets = consistent_bets[:max_bets]
            
            # Удаляем техническую информацию из выходных данных
            for bet in suggested_bets:
                bet.pop('has_contradiction', None)
                bet.pop('contradiction_details', None)
                bet.pop('is_consistent', None)
            
            print(f"Предложено {len(suggested_bets)} ставок из {len(all_bets)} возможных")
            logger.info(f"Предложено {len(suggested_bets)} ставок из {len(all_bets)} возможных")
            
            return suggested_bets
        except Exception as e:
            print(f"ОШИБКА при предложении ставок: {e}")
            logger.error(f"Ошибка при предложении ставок: {e}")
            traceback.print_exc()
            return []
    
    def place_bets(self, suggested_bets):
        """
        Имитирует размещение ставок (для демонстрации и тестирования)
        
        Args:
            suggested_bets (list): Список предлагаемых ставок
            
        Returns:
            list: Список размещенных ставок
        """
        print("Размещаем ставки...")
        placed_bets = []
        
        try:
            if not suggested_bets:
                print("Нет ставок для размещения")
                return []
                
            for bet in suggested_bets:
                # Расчет размера ставки (процент от текущего банка)
                bet_amount = round(self.bank * BET_SIZE_PERCENT / 100, 2)
                
                # Если включено регулирование размера ставки на основе ценности
                if VALUE_BASED_SIZING:
                    # Увеличиваем размер ставки для более ценных ставок (макс до 1.5x базового размера)
                    value_factor = min(1.5, 1 + bet['value'])
                    bet_amount = round(bet_amount * value_factor, 2)
                
                # Ограничиваем максимальный размер ставки
                max_bet = self.bank * 0.05  # Максимум 5% от банка
                bet_amount = min(bet_amount, max_bet)
                
                # Добавляем информацию о ставке
                placed_bet = bet.copy()
                placed_bet['amount'] = bet_amount
                placed_bet['potential_win'] = round(bet_amount * bet['odds'], 2)
                placed_bet['status'] = 'pending'  # Статус ставки (pending, won, lost)
                placed_bet['placement_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                placed_bets.append(placed_bet)
                
                # Обновляем историю ставок
                self.bet_history.append(placed_bet)
                
                # Вычитаем сумму ставки из банка
                self.bank -= bet_amount
                
                logger.info(f"Размещена ставка на {placed_bet['home_team']} vs {placed_bet['away_team']}, "
                           f"исход: {placed_bet['outcome']}, сумма: {bet_amount}, коэфф: {bet['odds']}")
                print(f"Размещена ставка на {placed_bet['home_team']} vs {placed_bet['away_team']}, "
                     f"исход: {placed_bet['outcome']}, сумма: {bet_amount}, коэфф: {bet['odds']}")
            
            # Сохраняем историю ставок
            self._save_bet_history()
            
            return placed_bets
        except Exception as e:
            print(f"ОШИБКА при размещении ставок: {e}")
            logger.error(f"Ошибка при размещении ставок: {e}")
            traceback.print_exc()
            return []
    
    def _save_bet_history(self):
        """Сохраняет историю ставок в CSV-файл"""
        if not self.bet_history:
            return
        
        try:
            history_df = pd.DataFrame(self.bet_history)
            history_df.to_csv(f"{DATA_DIR}/bet_history.csv", index=False)
            
            logger.info(f"История ставок сохранена, всего {len(self.bet_history)} ставок")
            print(f"История ставок сохранена, всего {len(self.bet_history)} ставок")
        except Exception as e:
            print(f"ОШИБКА при сохранении истории ставок: {e}")
            logger.error(f"Ошибка при сохранении истории ставок: {e}")
            traceback.print_exc()
    
    def update_bet_results(self, results):
        """
        Обновляет результаты ставок и пересчитывает банк
        
        Args:
            results (list): Список с результатами матчей
            
        Returns:
            float: Новый размер банка
        """
        # В реальной системе здесь бы получали результаты матчей из API
        # Для демонстрации используем переданные результаты
        
        # Обновляем статусы ставок и пересчитываем банк
        for result in results:
            match_id = result['match_id']
            match_result = result['result']  # '1', 'X' или '2'
            
            # Находим все ставки на этот матч
            for bet in self.bet_history:
                if str(bet['match_id']) == str(match_id) and bet['status'] == 'pending':
                    if bet['outcome'] == match_result:
                        # Ставка выиграла
                        bet['status'] = 'won'
                        self.bank += bet['potential_win']
                        logger.info(f"Ставка выиграла: {bet['home_team']} vs {bet['away_team']}, прибыль: {bet['potential_win'] - bet['amount']}")
                    else:
                        # Ставка проиграла
                        bet['status'] = 'lost'
                        logger.info(f"Ставка проиграла: {bet['home_team']} vs {bet['away_team']}, убыток: {bet['amount']}")
        
        # Сохраняем обновленную историю ставок
        self._save_bet_history()
        
        logger.info(f"Текущий банк: {self.bank}")
        
        return self.bank
    
    def run_full_cycle(self):
        """
        Запускает полный цикл работы системы:
        1. Сбор данных
        2. Генерация прогнозов
        3. Предложение ставок
        4. Размещение ставок (имитация)
        
        Returns:
            dict: Результаты работы системы
        """
        logger.info("Запуск полного цикла работы системы")
        print("Запуск полного цикла работы системы")
        
        try:
            # Сбор данных
            data = self.collect_data()
            if data is None:
                return {'error': 'Ошибка при сборе данных'}
            
            # Генерация прогнозов
            predictions = self.generate_predictions()
            if not predictions:
                return {'error': 'Не удалось создать прогнозы'}
            
            # Предложение ставок
            suggested_bets = self.suggest_bets(predictions)
            
            # Размещение ставок (имитация)
            placed_bets = self.place_bets(suggested_bets)
            
            return {
                'predictions_count': len(predictions),
                'suggested_bets': suggested_bets,
                'placed_bets': placed_bets,
                'current_bank': self.bank
            }
        except Exception as e:
            print(f"КРИТИЧЕСКАЯ ОШИБКА в цикле: {e}")
            logger.error(f"Критическая ошибка в цикле: {e}")
            traceback.print_exc()
            return {'error': str(e)}
    
    def run_full_cycle_improved(self):
        """
        Запускает полный улучшенный цикл работы системы с визуализациями и уведомлениями
    
        Returns:
        dict: Результаты работы системы
        """
        logger.info("Запуск полного цикла работы системы")
        print("Запуск полного цикла работы системы")
        
        try:
            # Сбор данных
            data = self.collect_data_improved()
        
            if data is None:
                print("ОШИБКА: Не удалось собрать данные для анализа")
                # Попробуем создать минимальный набор данных вручную
                print("Пытаемся создать минимальный набор данных вручную...")
                try:
                    # Импортируем сборщик данных и получаем матчи
                    from data_collector import BundesligaDataCollector
                    collector = BundesligaDataCollector()
                    _, future_matches = collector.get_matches(past=False, future=True)
                
                    if future_matches:
                        print(f"Получено {len(future_matches)} будущих матчей напрямую")
                    
                        # Сохраняем их принудительно
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        os.makedirs(MATCHES_DIR, exist_ok=True)
                        future_match_file = f"{MATCHES_DIR}/future_matches_{timestamp}.json"
                    
                        with open(future_match_file, 'w', encoding='utf-8') as f:
                            json.dump(future_matches, f, indent=4, ensure_ascii=False)
                    
                        print(f"Матчи сохранены в {future_match_file}")
                        # Не делаем return, продолжаем выполнение
                except Exception as e:
                    print(f"Не удалось получить данные вручную: {e}")
                    return {'error': 'Ошибка при сборе данных'}
        
            # Генерация прогнозов
            print("Создание прогнозов...")
            predictions = self.generate_predictions()
        
            if not predictions:
                return {'error': 'Не удалось создать прогнозы'}
        
            # Визуализация результатов, если включено
            if VISUALIZATION and hasattr(self, 'visualizer'):
                try:
                    # Создаем график распределения прогнозов
                    chart_path = os.path.join(CHARTS_DIR, f"predictions_{datetime.now().strftime('%Y%m%d')}.png")
                    self.visualizer.plot_prediction_distribution(predictions, save_path=chart_path)
                    print(f"График прогнозов сохранен: {chart_path}")
                    
                    # График истории банка
                    bank_chart_path = os.path.join(CHARTS_DIR, "bank_history.png")
                    self.visualizer.plot_bank_history(save_path=bank_chart_path)
                    print(f"График истории банка сохранен: {bank_chart_path}")
                except Exception as e:
                    logger.error(f"Ошибка при создании визуализаций: {e}")
                    print(f"Ошибка при создании визуализаций: {e}")
        
            # Предложение ставок с улучшенными проверками
            print("Выбор ценных ставок...")
            suggested_bets = self.suggest_bets(predictions, min_value=MIN_VALUE_FOR_BET, max_bets=MAX_DAILY_BETS)
        
            # Отправка уведомлений, если включено
            if hasattr(self, 'notifier') and self.notifier:
                try:
                    # Отправляем ежедневную сводку с прогнозами
                    self.notifier.notify_daily_predictions(predictions, max_bets=MAX_DAILY_BETS)
                    
                    # Отправляем уведомления о каждой ценной ставке
                    for bet in suggested_bets:
                        self.notifier.notify_value_bet(bet)
                    
                    print("Уведомления в Telegram отправлены")
                except Exception as e:
                    logger.error(f"Ошибка при отправке уведомлений: {e}")
                    print(f"Ошибка при отправке уведомлений: {e}")
        
            # Размещение ставок (имитация)
            print("Размещение ставок...")
            placed_bets = self.place_bets(suggested_bets)
        
            # Генерация отчета о производительности
            if VISUALIZATION and hasattr(self, 'visualizer'):
                try:
                    os.makedirs(REPORTS_DIR, exist_ok=True)
                    report_path = os.path.join(REPORTS_DIR, f"performance_report_{datetime.now().strftime('%Y%m%d')}.json")
                    report = self.visualizer.generate_performance_report(save_path=report_path)
                    if report:
                        print(f"Отчет о производительности сохранен: {report_path}")
                except Exception as e:
                    logger.error(f"Ошибка при создании отчета: {e}")
                    print(f"Ошибка при создании отчета: {e}")
        
            return {
                'predictions_count': len(predictions),
                'suggested_bets': suggested_bets,
                'placed_bets': placed_bets,
                'current_bank': self.bank
            }
        except Exception as e:
            print(f"КРИТИЧЕСКАЯ ОШИБКА в цикле: {e}")
            logger.error(f"Критическая ошибка в цикле: {e}")
            traceback.print_exc()
            return {'error': str(e)} 
    # Запуск полного цикла при запуске скрипта напрямую
if __name__ == "__main__":
        print("Программа запущена!")
        try:
            print("=" * 50)
            print("ЗАПУСК СИСТЕМЫ ПРОГНОЗИРОВАНИЯ БУНДЕСЛИГИ")
            print("=" * 50)
            
            # Проверяем директории
            print(f"Проверка директорий:")
            for dir_path in [DATA_DIR, MATCHES_DIR, ODDS_DIR, PREDICTIONS_DIR, CHARTS_DIR, REPORTS_DIR]:
                exists = os.path.exists(dir_path)
                print(f" - {dir_path}: {'существует' if exists else 'ОТСУТСТВУЕТ'}")
                if not exists:
                    os.makedirs(dir_path, exist_ok=True)
                    print(f"   Создана директория {dir_path}")
            
            print("Создание экземпляра предиктора...")
            predictor = BundesligaPredictor()
            print("Экземпляр предиктора создан успешно!")
            
            print("Запуск цикла анализа...")
            results = predictor.run_full_cycle_improved()
            print("Цикл анализа завершен!")
            
            print("\n" + "=" * 30)
            print("РЕЗУЛЬТАТЫ РАБОТЫ СИСТЕМЫ")
            print("=" * 30)
            
            if 'error' in results:
                print(f"Произошла ошибка: {results['error']}")
            else:
                print(f"Создано прогнозов: {results.get('predictions_count', 0)}")
                
                # Информация о предложенных ставках
                suggested_bets = results.get('suggested_bets', [])
                if suggested_bets:
                    print("\nПредложенные ставки:")
                    for i, bet in enumerate(suggested_bets, 1):
                        outcome_name = "Победа хозяев" if bet['outcome'] == '1' else "Ничья" if bet['outcome'] == 'X' else "Победа гостей"
                        print(f"{i}. {bet['date']} - {bet['home_team']} vs {bet['away_team']}")
                        print(f"   Исход: {outcome_name}, Коэф: {bet['odds']}, Ценность: {bet['value'] * 100:.1f}%")
                        print(f"   Ожидаемые голы: {bet['home_team']} - {bet['expected_goals']['home']}, {bet['away_team']} - {bet['expected_goals']['away']}")
                else:
                    print("\nНет предложенных ставок.")
                
                # Информация о размещенных ставках
                placed_bets = results.get('placed_bets', [])
                if placed_bets:
                    print("\nРазмещенные ставки:")
                    for i, bet in enumerate(placed_bets, 1):
                        outcome_name = "Победа хозяев" if bet['outcome'] == '1' else "Ничья" if bet['outcome'] == 'X' else "Победа гостей"
                        print(f"{i}. {bet['date']} - {bet['home_team']} vs {bet['away_team']}")
                        print(f"   Исход: {outcome_name}, Коэф: {bet['odds']}, Сумма: {bet['amount']}, Потенциальный выигрыш: {bet['potential_win']}")
                else:
                    print("\nНет размещенных ставок.")
                
                # Информация о банке
                print(f"\nТекущий банк: {results.get('current_bank', 0)}")
            
        except Exception as e:
            print(f"КРИТИЧЕСКАЯ ОШИБКА ПРИ ЗАПУСКЕ: {e}")
            traceback.print_exc()
            print("Программа аварийно завершена")