# setup.py
"""
Скрипт для установки и настройки проекта по прогнозированию Бундеслиги
"""

import os
import sys
import shutil

# Проверяем, что мы находимся в корневой директории проекта
if not os.path.exists("main.py"):
    print("Ошибка: скрипт должен запускаться из корневой директории проекта")
    sys.exit(1)

# Создаем необходимые директории
directories = [
    "data",
    "data/matches",
    "data/odds",
    "data/predictions",
    "data/reports",
    "data/charts"
]

print("Создание директорий для данных...")
for directory in directories:
    os.makedirs(directory, exist_ok=True)
    print(f"  - Создана директория: {directory}")

# Проверяем наличие необходимых файлов
required_files = [
    "main.py",
    "analyzer.py",
    "config.py",
    "odds_collector.py",
    "telegram_notifier.py",
    "visualizer.py"
]

print("\nПроверка наличия необходимых файлов...")
missing_files = []
for file in required_files:
    if not os.path.exists(file):
        missing_files.append(file)
        print(f"  - Отсутствует файл: {file}")
    else:
        print(f"  - Файл найден: {file}")

if missing_files:
    print("\nВНИМАНИЕ: Отсутствуют некоторые необходимые файлы!")
else:
    print("\nВсе необходимые файлы найдены.")

# Проверка зависимостей
try:
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    import seaborn as sns
    print("\nВсе необходимые библиотеки установлены.")
except ImportError as e:
    print(f"\nОшибка: Отсутствует необходимая библиотека: {e}")
    print("Пожалуйста, установите необходимые библиотеки с помощью pip:")
    print("pip install pandas numpy matplotlib seaborn requests")

print("\nНастройка проекта завершена. Теперь вы можете запустить систему с помощью команды:")
print("python main.py")