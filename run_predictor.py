# run_predictor.py
"""
Скрипт для проверки окружения и запуска системы прогнозирования Бундеслиги
"""

import os
import sys
import importlib
import subprocess
import traceback

def check_requirements():
    """
    Проверяет наличие необходимых библиотек и устанавливает их при необходимости
    
    Returns:
        bool: True, если все требования удовлетворены, иначе False
    """
    required_packages = [
        'pandas',
        'numpy',
        'matplotlib',
        'seaborn',
        'requests',
        'beautifulsoup4'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            importlib.import_module(package)
            print(f"✓ Библиотека {package} установлена")
        except ImportError:
            missing_packages.append(package)
            print(f"✗ Библиотека {package} отсутствует")
    
    if missing_packages:
        print("\nНеобходимо установить отсутствующие библиотеки.")
        answer = input("Установить отсутствующие библиотеки? (y/n): ")
        
        if answer.lower() in ['y', 'yes', 'да']:
            try:
                for package in missing_packages:
                    print(f"Установка {package}...")
                    subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
                print("Все библиотеки успешно установлены!")
                return True
            except Exception as e:
                print(f"Ошибка при установке библиотек: {e}")
                return False
        else:
            print("Для работы системы необходимо установить все библиотеки.")
            return False
    
    return True

def check_directories():
    """
    Проверяет наличие необходимых директорий и создает их при необходимости
    
    Returns:
        bool: True, если все директории созданы успешно, иначе False
    """
    # Загружаем конфигурацию
    try:
        from config import DATA_DIR, MATCHES_DIR, ODDS_DIR, PREDICTIONS_DIR, REPORTS_DIR, CHARTS_DIR
        
        directories = [
            DATA_DIR,
            MATCHES_DIR,
            ODDS_DIR,
            PREDICTIONS_DIR,
            REPORTS_DIR,
            CHARTS_DIR
        ]
        
        for directory in directories:
            if not os.path.exists(directory):
                print(f"Создание директории {directory}...")
                os.makedirs(directory, exist_ok=True)
            else:
                print(f"✓ Директория {directory} существует")
        
        return True
    except Exception as e:
        print(f"Ошибка при проверке директорий: {e}")
        return False

def check_files():
    """
    Проверяет наличие необходимых файлов
    
    Returns:
        bool: True, если все файлы существуют, иначе False
    """
    required_files = [
        'main.py',
        'config.py',
        'analyzer.py',
        'data_collector.py',
        'odds_collector.py',
        'telegram_notifier.py',
        'visualizer.py',
        'bookmaker_parser.py'
    ]
    
    missing_files = []
    
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
            print(f"✗ Файл {file} отсутствует")
        else:
            print(f"✓ Файл {file} существует")
    
    if missing_files:
        print("\nОтсутствуют следующие необходимые файлы:")
        for file in missing_files:
            print(f"  - {file}")
        return False
    
    return True

def run_main():
    """
    Запускает основной модуль системы прогнозирования
    
    Returns:
        int: Код возврата (0 - успешно, 1 - ошибка)
    """
    try:
        print("\nЗапуск системы прогнозирования Бундеслиги...")
        import main
        
        # Создаем экземпляр предиктора
        predictor = main.BundesligaPredictor()
        
        # Запускаем полный цикл
        results = predictor.run_full_cycle_improved()
        
        if 'error' in results:
            print(f"\nОшибка при выполнении цикла: {results['error']}")
            return 1
        
        print("\n✓ Система успешно выполнила полный цикл работы")
        print(f"  - Создано прогнозов: {results.get('predictions_count', 0)}")
        print(f"  - Предложено ставок: {len(results.get('suggested_bets', []))}")
        print(f"  - Размещено ставок: {len(results.get('placed_bets', []))}")
        print(f"  - Текущий банк: {results.get('current_bank', 0)}")
        
        return 0
    except ImportError as e:
        print(f"\nОшибка импорта модуля: {e}")
        print("Убедитесь, что все необходимые файлы находятся в одной директории.")
        return 1
    except Exception as e:
        print(f"\nНепредвиденная ошибка: {e}")
        traceback.print_exc()
        return 1

def main():
    """
    Основная функция запуска предиктора
    """
    print("=" * 70)
    print("СИСТЕМА ПРОГНОЗИРОВАНИЯ БУНДЕСЛИГИ")
    print("=" * 70)
    print("\nПроверка необходимых компонентов...\n")
    
    # Проверяем необходимые библиотеки
    if not check_requirements():
        print("\nОшибка: не все требования удовлетворены.")
        return 1
    
    print("\nПроверка директорий...")
    if not check_directories():
        print("\nОшибка: не удалось создать необходимые директории.")
        return 1
    
    print("\nПроверка файлов...")
    if not check_files():
        print("\nОшибка: отсутствуют необходимые файлы.")
        return 1
    
    # Запускаем основной модуль
    return run_main()

if __name__ == "__main__":
    sys.exit(main())