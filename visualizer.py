# visualizer.py
"""
Модуль для визуализации результатов прогнозирования и статистики ставок
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import json
from datetime import datetime, timedelta
import glob

# Импортируем настройки
from config import *

# Настройка стиля графиков
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 12


class BundesligaVisualizer:
    """Класс для визуализации данных Бундеслиги"""
    
    def __init__(self):
        """Инициализирует визуализатор"""
        # Создаем директорию для графиков, если не существует
        os.makedirs(CHARTS_DIR, exist_ok=True)
    
    def plot_team_ratings(self, team_ratings, top_n=18, save_path=None):
        """
        Создает график рейтингов команд
        
        Args:
            team_ratings (dict): Словарь с рейтингами команд
            top_n (int): Количество команд для отображения
            save_path (str): Путь для сохранения графика (если None, график будет показан)
        """
        # Преобразуем рейтинги в DataFrame
        ratings_data = []
        
        for team_id, data in team_ratings.items():
            ratings_data.append({
                'team_id': team_id,
                'team_name': data.get('team_name', f"Team {team_id}"),
                'rating': data.get('rating', 0),
                'normalized_rating': data.get('normalized_rating', 0),
                'attack': data.get('attack', 0),
                'defense': data.get('defense', 0),
                'form': sum(data.get('form', [])) / len(data.get('form', [1])) if data.get('form', []) else 0.5
            })
        
        df = pd.DataFrame(ratings_data)
        
        # Сортируем по рейтингу
        df = df.sort_values('normalized_rating', ascending=False).head(top_n)
        
        # Создаем график
        fig, ax = plt.subplots(figsize=(12, 10))
        
        # Цветовая карта для рейтинга
        cmap = plt.cm.Blues
        
        # Основной рейтинг
        bars = ax.barh(df['team_name'], df['normalized_rating'], color=cmap(df['normalized_rating']/100))
        
        # Добавляем показатели формы
        for i, (_, row) in enumerate(df.iterrows()):
            form_color = 'green' if row['form'] > 0.6 else 'orange' if row['form'] > 0.4 else 'red'
            ax.text(row['normalized_rating'] + 1, i, f"Форма: {row['form']*100:.1f}%", va='center', color=form_color)
        
        # Настройка графика
        ax.set_xlabel('Рейтинг команды')
        ax.set_title('Рейтинги команд Бундеслиги')
        ax.invert_yaxis()  # Команды с наивысшим рейтингом сверху
        
        # Добавляем значения на график
        for i, bar in enumerate(bars):
            width = bar.get_width()
            ax.text(width / 2, i, f"{width:.1f}", ha='center', va='center', color='white', fontweight='bold')
        
        plt.tight_layout()
        
        # Сохраняем или показываем график
        if save_path:
            plt.savefig(save_path)
            plt.close()
        else:
            plt.show()
        
        return fig, ax
    
    def plot_prediction_distribution(self, predictions, save_path=None):
        """
        Визуализирует распределение прогнозов (вероятности исходов, ожидаемые голы)
        
        Args:
            predictions (list): Список прогнозов
            save_path (str): Путь для сохранения графика
        """
        # Извлекаем данные из прогнозов
        home_win_probs = []
        draw_probs = []
        away_win_probs = []
        home_goals = []
        away_goals = []
        total_goals = []
        
        for pred in predictions:
            probs = pred.get('probabilities', {})
            expected_goals = pred.get('expected_goals', {})
            
            home_win_probs.append(probs.get('1', 0))
            draw_probs.append(probs.get('X', 0))
            away_win_probs.append(probs.get('2', 0))
            
            home_goal = expected_goals.get('home', 0)
            away_goal = expected_goals.get('away', 0)
            
            home_goals.append(home_goal)
            away_goals.append(away_goal)
            total_goals.append(home_goal + away_goal)
        
        # Создаем график
        fig, axs = plt.subplots(2, 2, figsize=(14, 12))
        
        # График 1: Распределение вероятностей исходов
        outcomes = ['П1', 'Х', 'П2']
        probs_avg = [np.mean(home_win_probs), np.mean(draw_probs), np.mean(away_win_probs)]
        
        axs[0, 0].bar(outcomes, probs_avg, color=['green', 'gray', 'blue'])
        axs[0, 0].set_title('Средние вероятности исходов')
        axs[0, 0].set_ylabel('Вероятность')
        axs[0, 0].grid(axis='y', linestyle='--', alpha=0.7)
        
        for i, v in enumerate(probs_avg):
            axs[0, 0].text(i, v + 0.01, f"{v:.2f}", ha='center')
        
        # График 2: Распределение ожидаемых голов
        axs[0, 1].boxplot([home_goals, away_goals, total_goals], labels=['Хозяева', 'Гости', 'Общий'])
        axs[0, 1].set_title('Распределение ожидаемых голов')
        axs[0, 1].set_ylabel('Голы')
        axs[0, 1].grid(axis='y', linestyle='--', alpha=0.7)
        
        # График 3: Гистограмма вероятностей домашних побед
        axs[1, 0].hist(home_win_probs, bins=20, color='green', alpha=0.7)
        axs[1, 0].set_title('Распределение вероятностей П1')
        axs[1, 0].set_xlabel('Вероятность')
        axs[1, 0].set_ylabel('Количество матчей')
        axs[1, 0].grid(axis='y', linestyle='--', alpha=0.7)
        
        # График 4: Гистограмма ожидаемых тоталов
        axs[1, 1].hist(total_goals, bins=20, color='orange', alpha=0.7)
        axs[1, 1].set_title('Распределение ожидаемых тоталов')
        axs[1, 1].set_xlabel('Общий тотал матча')
        axs[1, 1].set_ylabel('Количество матчей')
        axs[1, 1].grid(axis='y', linestyle='--', alpha=0.7)
        
        plt.tight_layout()
        
        # Сохраняем или показываем график
        if save_path:
            plt.savefig(save_path)
            plt.close()
        else:
            plt.show()
        
        return fig, axs
    
    def plot_bank_history(self, bet_history_file=f"{DATA_DIR}/bet_history.csv", save_path=None):
        """
        Строит график изменения банка
        
        Args:
            bet_history_file (str): Путь к файлу с историей ставок
            save_path (str): Путь для сохранения графика
        """
        if not os.path.exists(bet_history_file):
            print(f"Файл истории ставок не найден: {bet_history_file}")
            return None, None
        
        # Загружаем историю ставок
        df = pd.read_csv(bet_history_file)
        
        # Преобразуем даты
        df['placement_date'] = pd.to_datetime(df['placement_date'])
        
        # Сортируем по дате
        df = df.sort_values('placement_date')
        
        # Создаем DataFrame для банка
        bank_history = []
        current_bank = BANK_INITIAL
        
        # Начальное значение
        bank_history.append({
            'date': df['placement_date'].min() - timedelta(days=1) if not df.empty else datetime.now(),
            'bank': current_bank,
            'event': 'Начальный банк'
        })
        
        # Рассчитываем изменение банка для каждой ставки
        for _, bet in df.iterrows():
            # Вычитаем сумму ставки
            current_bank -= bet['amount']
            
            # Если ставка выиграла, добавляем выигрыш
            if bet['status'] == 'won':
                current_bank += bet['potential_win']
                event = f"Выигрыш: {bet['home_team']} vs {bet['away_team']}"
            elif bet['status'] == 'lost':
                event = f"Проигрыш: {bet['home_team']} vs {bet['away_team']}"
            else:
                event = f"Ставка: {bet['home_team']} vs {bet['away_team']}"
            
            bank_history.append({
                'date': bet['placement_date'],
                'bank': current_bank,
                'event': event
            })
        
        # Преобразуем в DataFrame
        bank_df = pd.DataFrame(bank_history)
        
        # Создаем график
        fig, ax = plt.subplots(figsize=(14, 8))
        
        # Линия с изменением банка
        ax.plot(bank_df['date'], bank_df['bank'], marker='o', linestyle='-', 
                color='green', linewidth=2, markersize=8)
        
        # Линия начального банка
        ax.axhline(y=BANK_INITIAL, color='red', linestyle='--', alpha=0.5, 
                   label=f'Начальный банк: {BANK_INITIAL}')
        
        # Добавляем текущий ROI
        if len(bank_df) > 1:
            initial_bank = BANK_INITIAL
            final_bank = bank_df['bank'].iloc[-1]
            roi = (final_bank - initial_bank) / initial_bank * 100
            roi_text = f'ROI: {roi:.2f}%'
            ax.annotate(roi_text, xy=(0.02, 0.95), xycoords='axes fraction', 
                       fontsize=14, bbox=dict(boxstyle="round,pad=0.3", fc="yellow", ec="black", alpha=0.7))
        
        # Улучшаем внешний вид
        ax.set_title('История изменения банка', fontsize=16)
        ax.set_xlabel('Дата', fontsize=14)
        ax.set_ylabel('Банк', fontsize=14)
        ax.grid(True, alpha=0.3)
        
        # Форматирование осей
        plt.xticks(rotation=45)
        
        # Добавляем подписи к точкам
        for i, row in bank_df.iterrows():
            if i > 0:  # Пропускаем начальную точку
                ax.annotate(f"{row['bank']:.2f}", 
                          xy=(row['date'], row['bank']), 
                          xytext=(5, 0), textcoords='offset points',
                          fontsize=10, fontweight='bold')
        
        plt.tight_layout()
        
        # Сохраняем или показываем график
        if save_path:
            plt.savefig(save_path)
            plt.close()
        else:
            plt.show()
        
        return fig, ax
    
    def plot_value_vs_result(self, bet_history_file=f"{DATA_DIR}/bet_history.csv", save_path=None):
        """
        Визуализирует зависимость результатов ставок от их ценности
        
        Args:
            bet_history_file (str): Путь к файлу с историей ставок
            save_path (str): Путь для сохранения графика
        """
        if not os.path.exists(bet_history_file):
            print(f"Файл истории ставок не найден: {bet_history_file}")
            return None, None
        
        # Загружаем историю ставок
        df = pd.read_csv(bet_history_file)
        
        # Фильтруем только завершенные ставки
        df_finished = df[df['status'].isin(['won', 'lost'])].copy()
        
        if len(df_finished) < 5:
            print("Недостаточно завершенных ставок для анализа")
            return None, None
        
        # Добавляем столбец с результатом (1 - выигрыш, 0 - проигрыш)
        df_finished['result'] = df_finished['status'].apply(lambda x: 1 if x == 'won' else 0)
        
        # Добавляем столбец с прибылью/убытком
        df_finished['profit'] = df_finished.apply(
            lambda row: row['potential_win'] - row['amount'] if row['status'] == 'won' else -row['amount'], 
            axis=1
        )
        
        # Создаем график
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 8))
        
        # График 1: Ценность vs Результат
        ax1.scatter(df_finished['value'], df_finished['result'], 
                  c=df_finished['result'].map({1: 'green', 0: 'red'}),
                  s=100, alpha=0.7)
        
        # Добавляем линию тренда
        if len(df_finished) > 1:
            try:
                z = np.polyfit(df_finished['value'], df_finished['result'], 1)
                p = np.poly1d(z)
                ax1.plot(df_finished['value'], p(df_finished['value']), "r--", alpha=0.7)
            except:
                pass
        
        ax1.set_title('Зависимость результата от ценности', fontsize=16)
        ax1.set_xlabel('Ценность ставки', fontsize=14)
        ax1.set_ylabel('Результат (1 - выигрыш, 0 - проигрыш)', fontsize=14)
        ax1.grid(True, alpha=0.3)
        
        # График 2: Распределение прибыли от ценности
        ax2.scatter(df_finished['value'], df_finished['profit'], 
                  c=df_finished['profit'].apply(lambda x: 'green' if x > 0 else 'red'),
                  s=100, alpha=0.7)
        
        # Добавляем линию тренда
        if len(df_finished) > 1:
            try:
                z = np.polyfit(df_finished['value'], df_finished['profit'], 1)
                p = np.poly1d(z)
                ax2.plot(df_finished['value'], p(df_finished['value']), "r--", alpha=0.7)
            except:
                pass
        
        ax2.set_title('Зависимость прибыли от ценности', fontsize=16)
        ax2.set_xlabel('Ценность ставки', fontsize=14)
        ax2.set_ylabel('Прибыль', fontsize=14)
        ax2.grid(True, alpha=0.3)
        
        # Добавляем линию нулевой прибыли
        ax2.axhline(y=0, color='black', linestyle='-', alpha=0.5)
        
        plt.tight_layout()
        
        # Сохраняем или показываем график
        if save_path:
            plt.savefig(save_path)
            plt.close()
        else:
            plt.show()
        
        return fig, (ax1, ax2)
    
    def generate_performance_report(self, bet_history_file=f"{DATA_DIR}/bet_history.csv", save_path=None):
        """
        Создает отчет об эффективности стратегии ставок
        
        Args:
            bet_history_file (str): Путь к файлу с историей ставок
            save_path (str): Путь для сохранения отчета
            
        Returns:
            dict: Данные отчета
        """
        if not os.path.exists(bet_history_file):
            print(f"Файл истории ставок не найден: {bet_history_file}")
            return {}
        
        # Загружаем историю ставок
        df = pd.read_csv(bet_history_file)
        
        # Базовая статистика
        total_bets = len(df)
        settled_bets = len(df[df['status'].isin(['won', 'lost'])])
        won_bets = len(df[df['status'] == 'won'])
        lost_bets = len(df[df['status'] == 'lost'])
        
        if settled_bets == 0:
            print("Нет завершенных ставок для анализа")
            return {}
        
        win_rate = won_bets / settled_bets if settled_bets > 0 else 0
        
        # Финансовая статистика
        total_staked = df['amount'].sum()
        total_returns = df[df['status'] == 'won']['potential_win'].sum()
        profit_loss = total_returns - total_staked
        roi = profit_loss / total_staked * 100 if total_staked > 0 else 0
        
        # Анализ по типам ставок
        bet_types = df['outcome'].value_counts().to_dict()
        bet_type_win_rates = {}
        bet_type_roi = {}
        
        for outcome in df['outcome'].unique():
            type_df = df[df['outcome'] == outcome]
            type_settled = len(type_df[type_df['status'].isin(['won', 'lost'])])
            type_won = len(type_df[type_df['status'] == 'won'])
            
            if type_settled > 0:
                type_win_rate = type_won / type_settled
                type_staked = type_df['amount'].sum()
                type_returns = type_df[type_df['status'] == 'won']['potential_win'].sum()
                type_profit = type_returns - type_staked
                type_roi = type_profit / type_staked * 100 if type_staked > 0 else 0
                
                bet_type_win_rates[outcome] = type_win_rate
                bet_type_roi[outcome] = type_roi
        
        # Группировка по месяцам
        df['placement_date'] = pd.to_datetime(df['placement_date'])
        df['month'] = df['placement_date'].dt.strftime('%Y-%m')
        
        monthly_stats = {}
        for month, month_df in df.groupby('month'):
            month_settled = len(month_df[month_df['status'].isin(['won', 'lost'])])
            month_won = len(month_df[month_df['status'] == 'won'])
            month_staked = month_df['amount'].sum()
            month_returns = month_df[month_df['status'] == 'won']['potential_win'].sum()
            month_profit = month_returns - month_staked
            
            monthly_stats[month] = {
                'bets': len(month_df),
                'win_rate': month_won / month_settled if month_settled > 0 else 0,
                'profit': month_profit,
                'roi': month_profit / month_staked * 100 if month_staked > 0 else 0
            }
        
        # Формируем отчет
        report = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'basic_stats': {
                'total_bets': total_bets,
                'settled_bets': settled_bets,
                'won_bets': won_bets,
                'lost_bets': lost_bets,
                'win_rate': win_rate
            },
            'financial_stats': {
                'total_staked': total_staked,
                'total_returns': total_returns,
                'profit_loss': profit_loss,
                'roi': roi,
                'current_bank': BANK_INITIAL + profit_loss
            },
            'bet_types': {
                'counts': bet_types,
                'win_rates': bet_type_win_rates,
                'roi': bet_type_roi
            },
            'monthly_stats': monthly_stats
        }
        
        # Сохраняем отчет
        if save_path:
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=4, ensure_ascii=False)
        
        return report


# Пример использования при запуске скрипта напрямую
if __name__ == "__main__":
    visualizer = BundesligaVisualizer()
    
    # Пример визуализации истории банка
    bank_chart_path = os.path.join(CHARTS_DIR, "bank_history.png")
    visualizer.plot_bank_history(save_path=bank_chart_path)
    print(f"График истории банка сохранен: {bank_chart_path}")
    
    # Пример анализа ценности ставок
    value_chart_path = os.path.join(CHARTS_DIR, "value_analysis.png")
    visualizer.plot_value_vs_result(save_path=value_chart_path)
    print(f"График анализа ценности сохранен: {value_chart_path}")
    
    # Генерация отчета
    os.makedirs(REPORTS_DIR, exist_ok=True)
    report_path = os.path.join(REPORTS_DIR, f"performance_report_{datetime.now().strftime('%Y%m%d')}.json")
    report = visualizer.generate_performance_report(save_path=report_path)
    
    if report:
        print(f"Отчет о производительности сохранен: {report_path}")
        print(f"Общая статистика:")
        print(f"Всего ставок: {report['basic_stats']['total_bets']}")
        print(f"Выигрышей: {report['basic_stats']['won_bets']}")
        print(f"Проигрышей: {report['basic_stats']['lost_bets']}")
        print(f"Процент выигрышей: {report['basic_stats']['win_rate']*100:.2f}%")
        print(f"ROI: {report['financial_stats']['roi']:.2f}%")
        print(f"Текущий банк: {report['financial_stats']['current_bank']:.2f}")