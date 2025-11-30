# LG Monitor Mode Switcher

A Windows application for switching picture modes on LG webOS monitors.

## Supported Models

- **34GX90SA**
- **39GX90SA**
- **45GX90SA**

## Requirements

- PC and monitor must be connected to the same network
- Monitor should have a static IP address (recommended)
- Windows operating system

## Monitor Settings

For optimal functionality, configure your monitor with the following settings:

- **Support - IP Control Settings - SDDP**: On
- **Support - IP Control Settings - Wake on LAN**: On
- **General - External Devices - HDMI Settings - SIMPLINK (HDMI-CEC)**: On
- **General - External Devices - Monitor On With Mobile - Turn via Wi-Fi**: On
- **General - System - Additional Settings - Quick Start+**: On

**Note**: This application has been tested with these settings on Windows 11 25H2 with monitor LG UltraGear 39GX90SA-W.

**Tip**: For automatic monitor wake-up after PC resumes from sleep, I recommend using [LGTV Companion](https://github.com/JPersson77/LGTVCompanion).

## Dependencies

This application is built using the following open-source libraries:

- **[aiopylgtv](https://github.com/bendavid/aiopylgtv)** - Python library for controlling LG webOS TVs and monitors
- **[pystray](https://github.com/moses-palmer/pystray)** - System tray icon library
- **[Pillow](https://github.com/python-pillow/Pillow)** - Python Imaging Library for icon creation
- **[PyInstaller](https://github.com/pyinstaller/pyinstaller)** - Application packaging tool

## Features

- **Easy Mode Switching**: Quickly change picture modes directly from your PC
- **System Tray Integration**: Change picture modes directly from the system tray
- **Auto-start with Windows**: Option to launch automatically on system startup
- **Start Minimized**: Launch directly to the system tray
- **Auto-connect**: Automatically connects to the last used monitor
- **Multi-language Support**: English and Russian interfaces
- **HDR Mode Detection**: Automatically shows appropriate modes based on HDR state

## Usage

1. Launch the application
2. Click "Find Monitors" to search for available LG monitors on your network
3. Select your monitor from the list
4. Click "Connect" (you may need to confirm the connection on the monitor screen)
5. Choose a picture mode from the dropdown and click "Apply"

The application will minimize to the system tray. You can access all features by clicking the tray icon.

## Installation

1. Download `LGMonitorModeSwitcher.exe` from the [Releases](https://github.com/idiked/LGMonitorModeSwitcher/releases) page
2. Run the executable
3. The application will create configuration files in the same directory

## Configuration

- **Auto-start**: Enable "Start with Windows" checkbox to launch on system startup
- **Start Minimized**: Enable "Start minimized" to launch directly to the system tray
- **Language**: Switch between English and Russian from the language dropdown

---

# Переключатель режимов монитора LG

Приложение для Windows для переключения режимов изображения на мониторах LG с webOS.

## Поддерживаемые модели

- **34GX90SA**
- **39GX90SA**
- **45GX90SA**

## Требования

- ПК и монитор должны быть подключены к одной сети
- Монитору желательно иметь статический IP адрес
- Операционная система Windows

## Настройки монитора

Для оптимальной работы настройте монитор со следующими параметрами:

- **Поддержка - Настройки управления IP-адресами - SDDP**: Вкл
- **Поддержка - Настройки управления IP-адресами - Включение по сети LAN**: Вкл
- **Общие - Внешние устройства - Настройки HDMI - SIMPLINK (HDMI-CEC)**: Вкл
- **Общие - Внешние устройства - Включение монитора с мобильного устройства - Включить через Wi-Fi**: Вкл
- **Общие - Система - Дополнительные настройки - Быстрая загрузка+**: Вкл

**Примечание**: Программа протестирована с такими настройками на Windows 11 25H2, монитор LG UltraGear 39GX90SA.

**Совет**: Для автоматического включения монитора после выхода ПК из сна рекомендую использовать [LGTV Companion](https://github.com/JPersson77/LGTVCompanion).

## Зависимости

Приложение создано с использованием следующих библиотек с открытым исходным кодом:

- **[aiopylgtv](https://github.com/bendavid/aiopylgtv)** - Python библиотека для управления LG webOS телевизорами и мониторами
- **[pystray](https://github.com/moses-palmer/pystray)** - Библиотека для работы с иконкой системного трея
- **[Pillow](https://github.com/python-pillow/Pillow)** - Библиотека для работы с изображениями и создания иконок
- **[PyInstaller](https://github.com/pyinstaller/pyinstaller)** - Инструмент для упаковки приложения

## Возможности

- **Простое переключение режимов**: Быстрая смена режимов изображения прямо с ПК
- **Интеграция с системным треем**: Доступ к смене режима экрана из системного трея
- **Автозапуск с Windows**: Возможность автоматического запуска при старте системы
- **Запуск свернутым**: Запуск сразу в системный трей
- **Автоподключение**: Автоматическое подключение к последнему использованному монитору
- **Многоязычная поддержка**: Интерфейс на английском и русском языках
- **Определение режима HDR**: Автоматическое отображение соответствующих режимов в зависимости от состояния HDR

## Использование

1. Запустите приложение
2. Нажмите "Найти мониторы" для поиска доступных мониторов LG в сети
3. Выберите ваш монитор из списка
4. Нажмите "Подключиться" (возможно, потребуется подтвердить подключение на экране монитора)
5. Выберите режим изображения из выпадающего списка и нажмите "Применить"

Приложение свернется в системный трей. Вы можете получить доступ ко всем функциям, нажав на иконку в трее.

## Установка

1. Скачайте `LGMonitorModeSwitcher.exe` со страницы [Releases](https://github.com/idiked/LGMonitorModeSwitcher/releases)
2. Запустите исполняемый файл
3. Приложение создаст файлы конфигурации в той же папке

## Настройки

- **Автозапуск**: Включите галочку "Запуск с Windows" для автоматического запуска при старте системы
- **Запуск свернутым**: Включите "Запускать свернутой" для запуска сразу в системный трей
- **Язык**: Переключение между английским и русским из выпадающего списка языков

