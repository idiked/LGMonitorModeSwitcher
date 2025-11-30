"""
Скрипт для создания exe файла из lg_control.py
Использование: python build_exe.py

Требования:
    pip install pyinstaller
"""

import PyInstaller.__main__
import os
import sys

# Параметры для PyInstaller
args = [
    "lg_control.py",
    "--onefile",  # Один exe файл
    "--windowed",  # Без консоли (GUI приложение)
    "--name=LGMonitorModeSwitcher",  # Имя exe файла
    "--icon=NONE",  # Можно добавить иконку позже
    "--clean",  # Очистить кэш перед сборкой
    "--noconfirm",  # Не спрашивать подтверждение
    "--noupx",  # Не использовать UPX для сжатия
]

# Добавляем скрытые импорты
hidden_imports = [
    "pystray",
    "PIL",
    "PIL._tkinter_finder",
    "aiopylgtv",
    "asyncio",
    "tkinter",
    "winreg",  # Для автозапуска в Windows
]

for imp in hidden_imports:
    args.append(f"--hidden-import={imp}")

# Запускаем PyInstaller
try:
    PyInstaller.__main__.run(args)
    print("\n✓ Exe файл создан в папке dist/")
    print("Файл: dist/LGMonitorModeSwitcher.exe")
except Exception as e:
    print(f"\n✗ Ошибка при создании exe: {e}")
    sys.exit(1)
