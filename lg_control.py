import socket
import asyncio
from aiopylgtv import WebOsClient
import ipaddress
from concurrent.futures import ThreadPoolExecutor, as_completed
import tkinter as tk
from tkinter import ttk, messagebox
import threading
from typing import Optional, List
import subprocess
import platform
import re
import json
import os
import sys

# Отключаем логи в exe файле
if getattr(sys, "frozen", False):
    # Если запущено из exe - перенаправляем print в никуда
    import io

    sys.stdout = io.StringIO()
    sys.stderr = io.StringIO()

# Для системного трея
try:
    import pystray
    from PIL import Image, ImageDraw, ImageTk

    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False
    print("⚠ Для работы системного трея установите: pip install pystray pillow")

# ============================================================================
# СОХРАНЕНИЕ НАСТРОЕК
# ============================================================================

# Определяем базовую директорию (где находится exe или скрипт)
if getattr(sys, "frozen", False):
    # Для exe файла
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # Для скрипта
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(BASE_DIR, "lg_monitor_config.json")
WEBOS_KEY_FILE = os.path.join(BASE_DIR, "webos_key.json")

# Словарь переводов интерфейса
UI_TRANSLATIONS = {
    "en": {
        "title": "LG Mode Switcher",
        "language_label": "Language:",
        "search_monitors": "Search Monitors",
        "find_monitors": "Find Monitors",
        "connect": "Connect",
        "picture_mode": "Picture Mode",
        "mode": "Mode:",
        "apply": "Apply",
        "hint": "💡 Tip: Toggle HDR in Windows - Win+Alt+B",
        "ready": "Ready",
        "connected_to": "Connected to",
        "connection_error": "Connection error",
        "monitors_found": "monitor(s) found",
        "no_monitors": "No monitors found",
        "searching": "Searching monitors (may take 30-60 sec)...",
        "auto_connecting": "Auto-connecting to",
        "connection_success": "Success!\nIf a request appeared on the monitor - confirm it",
        "connection_failed": "Failed to connect",
        "select_monitor": "Select a monitor",
        "connect_first": "Connect to monitor first",
        "setting_mode": "Setting mode",
        "mode_set": "Mode:",
        "mode_error": "Mode setting error",
        "exit": "Exit",
        "open": "Open",
        "mode_label": "Mode:",
        "autostart": "Start with Windows",
        "start_minimized": "Start minimized",
        "close_to_tray": "Close to tray",
        "theme": "Theme:",
        "theme_light": "Light",
        "theme_dark": "Dark",
        "already_running": "Application is already running!",
        "already_running_msg": "The application is already running!\n\nPlease check the system tray.",
        "settings": "Picture Settings",
        "brightness": "OLED Brightness",
        "black_level": "Black Level",
        "color_depth": "Color Depth",
        "reset_settings": "Reset to Default",
    },
    "ru": {
        "title": "Переключатель режимов LG",
        "language_label": "Язык:",
        "search_monitors": "Поиск мониторов",
        "find_monitors": "Найти мониторы",
        "connect": "Подключиться",
        "picture_mode": "Режим экрана",
        "mode": "Режим:",
        "apply": "Применить",
        "hint": "💡 Подсказка: Переключение HDR в Windows - Win+Alt+B",
        "ready": "Готов к работе",
        "connected_to": "Подключен к",
        "connection_error": "Ошибка подключения",
        "monitors_found": "монитор(ов) найдено",
        "no_monitors": "Мониторы не найдены",
        "searching": "Поиск мониторов (может занять 30-60 сек)...",
        "auto_connecting": "Автоподключение к",
        "connection_success": "Успешно!\nЕсли появился запрос на мониторе - подтвердите",
        "connection_failed": "Не удалось подключиться",
        "select_monitor": "Выберите монитор",
        "connect_first": "Сначала подключитесь к монитору",
        "setting_mode": "Установка режима",
        "mode_set": "Режим:",
        "mode_error": "Ошибка установки режима",
        "exit": "Выход",
        "open": "Открыть",
        "mode_label": "Режим:",
        "autostart": "Запуск с Windows",
        "start_minimized": "Запускать свернутой",
        "close_to_tray": "Закрывать в трей",
        "theme": "Тема:",
        "theme_light": "Светлая",
        "theme_dark": "Темная",
        "already_running": "Приложение уже запущено!",
        "already_running_msg": "Приложение уже запущено!\n\nПроверьте системный трей.",
        "settings": "Настройки изображения",
        "brightness": "Яркость",
        "black_level": "Уровень черного",
        "color_depth": "Глубина цвета",
        "reset_settings": "Сбросить по умолчанию",
    },
}

# Словарь переводов режимов
MODE_TRANSLATIONS = {
    "en": {
        "personalized": f"Personalized Picture",
        "game": "Game Optimizer",
        "normal": "Standard",
        "vivid": "Vivid",
        "cinema": "Cinema",
        "sports": "Sports",
        "eco": "Auto Power Save",
        "filmMaker": "Film Maker",
        "expert1": "Expert 1",
        "expert2": "Expert 2",
        "hdrPersonalized": "HDR Personalized Picture",
        "hdrGame": "HDR Game Optimizer",
        "hdrStandard": "HDR Standard",
        "hdrCinema": "HDR Cinema",
        "hdrCinemaBright": "HDR Cinema Home",
        "hdrVivid": "HDR Vivid",
        "hdrEco": "HDR Auto Energy Saving",
        "hdrFilmMaker": "HDR Film Maker",
    },
    "ru": {
        "personalized": "Персонализированное изображение",
        "game": "Оптимизация игр",
        "normal": "Стандартный",
        "vivid": "Яркий",
        "cinema": "Кино",
        "sports": "Спорт",
        "eco": "Автоматическое энергосбережение",
        "filmMaker": "FilmMaker",
        "expert1": "Эксперт 1",
        "expert2": "Эксперт 2",
        "hdrPersonalized": "HDR Персонализированное изображение",
        "hdrGame": "HDR Оптимизация игр",
        "hdrStandard": "HDR Стандартный",
        "hdrCinema": "HDR Кино",
        "hdrCinemaBright": "HDR Кинотеатр",
        "hdrVivid": "HDR Яркий",
        "hdrEco": "HDR Автоматическое энергосбережение",
        "hdrFilmMaker": "HDR FilmMaker",
    },
}


def get_mode_translation(mode: str, language: str = "en") -> str:
    """Получить перевод режима"""
    return MODE_TRANSLATIONS.get(language, MODE_TRANSLATIONS["en"]).get(mode, mode)


def get_mode_from_translation(translated_mode: str, language: str = "en") -> str:
    """Получить оригинальное имя режима из перевода"""
    translations = MODE_TRANSLATIONS.get(language, MODE_TRANSLATIONS["en"])
    for mode, translation in translations.items():
        if translation == translated_mode:
            return mode
    # Если не найдено, возвращаем как есть (может быть уже оригинальное имя)
    return translated_mode


def can_adjust_black_level(mode: str) -> bool:
    """Проверить, можно ли изменять уровень черного в данном режиме"""
    # Уровень черного нельзя изменять в режимах game, hdrGame
    blocked_modes = ["game", "hdrGame"]
    return mode not in blocked_modes


def can_adjust_color_depth(mode: str) -> bool:
    """Проверить, можно ли изменять глубину цвета в данном режиме"""
    # Глубину цвета нельзя изменять в режимах personalized, hdrPersonalized, game, hdrGame
    blocked_modes = ["personalized", "hdrPersonalized", "game", "hdrGame"]
    return mode not in blocked_modes


# Настройки по умолчанию для каждого режима (яркость, уровень черного, глубина цвета)
DEFAULT_MODE_SETTINGS = {
    # HDR режимы
    "hdrPersonalized": (100, 50, 65),
    "hdrVivid": (100, 50, 70),
    "hdrStandard": (100, 50, 55),
    "hdrEco": (100, 50, 65),
    "hdrCinemaBright": (100, 50, 60),
    "hdrCinema": (100, 50, 50),
    "hdrGame": (100, 50, 55),
    "hdrFilmMaker": (100, 50, 50),
    # SDR режимы
    "personalized": (100, 50, 55),
    "vivid": (100, 50, 70),
    "normal": (90, 50, 55),
    "eco": (90, 50, 60),
    "cinema": (80, 50, 50),
    "sports": (100, 50, 80),
    "game": (95, 50, 55),
    "filmMaker": (80, 50, 50),
    "expert1": (90, 50, 50),
    "expert2": (60, 50, 50),
}


def save_monitor_config(
    ip: str,
    language: str = "en",
    start_minimized: bool = False,
    mac: Optional[str] = None,
    close_to_tray: bool = True,
    theme: str = "light",
):
    """Сохранить IP адрес монитора, MAC адрес, язык и все настройки в конфигурационный файл"""
    try:
        config = {
            "last_monitor_ip": ip,
            "language": language,
            "start_minimized": start_minimized,
            "close_to_tray": close_to_tray,
            "theme": theme,
        }
        if mac:
            config["last_monitor_mac"] = mac
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        print(f"Ошибка сохранения конфигурации: {e}")


def load_monitor_config() -> tuple[Optional[str], str, bool, Optional[str], bool, str]:
    """Загрузить IP адрес, MAC адрес последнего подключенного монитора, язык и настройки"""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
                ip = config.get("last_monitor_ip")
                language = config.get("language", "en")
                start_minimized = config.get("start_minimized", False)
                mac = config.get("last_monitor_mac")
                close_to_tray = config.get("close_to_tray", True)
                theme = config.get("theme", "light")
                return ip, language, start_minimized, mac, close_to_tray, theme
    except Exception as e:
        print(f"Ошибка загрузки конфигурации: {e}")
    return None, "en", False, None, True, "light"


# ============================================================================
# СКАНЕР LG УСТРОЙСТВ
# ============================================================================


def get_ip_mac_mapping() -> dict[str, str]:
    """Получить словарь IP -> MAC адресов из ARP таблицы"""
    ip_mac_map = {}

    try:
        if platform.system() == "Windows":
            # Используем PowerShell команду для получения IP и MAC адресов
            try:
                result = subprocess.run(
                    [
                        "powershell",
                        "-Command",
                        "Get-NetNeighbor | Where-Object {$_.State -eq 'Reachable'} | Select-Object IPAddress, LinkLayerAddress | Format-Table -HideTableHeaders",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    # Парсим вывод PowerShell
                    for line in result.stdout.strip().split("\n"):
                        parts = line.strip().split()
                        if len(parts) >= 2:
                            ip = parts[0].strip()
                            mac = parts[1].strip().replace("-", ":")
                            if (
                                ip and mac and len(mac) == 17
                            ):  # MAC адрес должен быть 17 символов (xx:xx:xx:xx:xx:xx)
                                ip_mac_map[ip] = mac.lower()
            except:
                pass

            # Fallback: используем arp -a (работает на всех версиях Windows)
            try:
                result = subprocess.run(
                    ["arp", "-a"], capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    # Парсим вывод arp -a: ищем строки вида "192.168.1.1    xx-xx-xx-xx-xx-xx   dynamic"
                    # Паттерн для IP и MAC адреса
                    pattern = r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s+([0-9a-fA-F]{2}[-:][0-9a-fA-F]{2}[-:][0-9a-fA-F]{2}[-:][0-9a-fA-F]{2}[-:][0-9a-fA-F]{2}[-:][0-9a-fA-F]{2})"
                    matches = re.findall(pattern, result.stdout)
                    for ip, mac in matches:
                        # Нормализуем MAC адрес (приводим к формату xx:xx:xx:xx:xx:xx)
                        mac_normalized = mac.replace("-", ":").lower()
                        ip_mac_map[ip] = mac_normalized
            except:
                pass
        else:
            # Linux/Mac: используем ip neigh или arp
            try:
                result = subprocess.run(
                    ["ip", "neigh", "show"], capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    # Парсим вывод: ищем строки вида "192.168.1.1 dev eth0 lladdr xx:xx:xx:xx:xx:xx REACHABLE"
                    pattern = r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}).*lladdr\s+([0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2})"
                    matches = re.findall(pattern, result.stdout)
                    for ip, mac in matches:
                        ip_mac_map[ip] = mac.lower()
            except:
                # Fallback на arp
                try:
                    result = subprocess.run(
                        ["arp", "-a"], capture_output=True, text=True, timeout=5
                    )
                    if result.returncode == 0:
                        pattern = r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}).*\(([0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2})\)"
                        matches = re.findall(pattern, result.stdout)
                        for ip, mac in matches:
                            ip_mac_map[ip] = mac.lower()
                except:
                    pass

    except Exception as e:
        print(f"Предупреждение: не удалось получить ARP таблицу: {e}")

    # Фильтруем локальные адреса (127.x.x.x, 169.254.x.x)
    filtered_map = {
        ip: mac
        for ip, mac in ip_mac_map.items()
        if not ip.startswith("127.") and not ip.startswith("169.254.")
    }

    return filtered_map


def get_reachable_ips() -> List[str]:
    """Получить список достижимых IP адресов из ARP таблицы"""
    ip_mac_map = get_ip_mac_mapping()
    return list(ip_mac_map.keys())


def discover_lg_monitors(
    timeout=2, saved_mac: Optional[str] = None
) -> tuple[List[str], dict[str, str]]:
    """Поиск LG мониторов через WebSocket порт 3001 (только среди достижимых IP)

    Возвращает:
        - список IP адресов найденных мониторов
        - словарь IP -> MAC адресов для найденных мониторов
    """

    print("Получение списка достижимых устройств из ARP таблицы...")
    ip_mac_map = get_ip_mac_mapping()
    reachable_ips = list(ip_mac_map.keys())

    if not reachable_ips:
        print(
            "⚠ Не удалось получить список достижимых IP. Используется полное сканирование подсети."
        )
        # Fallback на старый метод
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        network = ipaddress.IPv4Network(f"{local_ip}/24", strict=False)
        reachable_ips = [str(ip) for ip in network.hosts()]
        # Для fallback метода MAC адреса недоступны
        ip_mac_map = {}

    print(f"Проверка {len(reachable_ips)} достижимых устройств на порт 3001...")

    lg_devices = []
    lg_devices_mac = {}  # IP -> MAC для найденных мониторов

    def check_ip(ip):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((ip, 3001))
            sock.close()
            if result == 0:
                return ip
        except:
            pass
        return None

    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = {executor.submit(check_ip, ip): ip for ip in reachable_ips}

        for future in as_completed(futures):
            result = future.result()
            if result:
                lg_devices.append(result)
                # Сохраняем MAC адрес для найденного монитора, если он доступен
                if result in ip_mac_map:
                    lg_devices_mac[result] = ip_mac_map[result]
                print(f"✓ Найден LG монитор: {result}")

    # Если есть сохраненный MAC адрес, проверяем, найден ли он в списке
    if saved_mac:
        saved_mac_lower = saved_mac.lower()
        for ip, mac in lg_devices_mac.items():
            if mac.lower() == saved_mac_lower:
                print(f"✓ Найден монитор по сохраненному MAC адресу: {ip} (MAC: {mac})")
                # Если этот IP не был в списке найденных (маловероятно, но на всякий случай)
                if ip not in lg_devices:
                    lg_devices.insert(0, ip)  # Добавляем в начало списка
                break

    return lg_devices, lg_devices_mac


# ============================================================================
# КОНТРОЛЛЕР LG МОНИТОРА
# ============================================================================


class LGMonitorController:
    def __init__(self, ip=None):
        self.ip = ip
        self.client = None
        self.model_name = None  # Название модели монитора
        self.picture_mode_callback = None  # Callback для изменений picture mode

    async def connect(self):
        """Подключение к монитору"""
        if not self.ip:
            return False

        try:
            print(f"Подключение к {self.ip}...")
            # Создаем клиент (ключ будет загружен из файла или запрошен при первом подключении)
            self.client = WebOsClient(self.ip, key_file_path=WEBOS_KEY_FILE)
            await self.client.async_init()
            await self.client.connect()
            print("✓ Подключено!")

            # Получаем информацию о модели
            try:
                system_info = await self.client.get_system_info()
                if system_info and "modelName" in system_info:
                    self.model_name = system_info["modelName"]
                    print(f"Модель: {self.model_name}")
                elif hasattr(self.client, "system_info") and self.client.system_info:
                    if "modelName" in self.client.system_info:
                        self.model_name = self.client.system_info["modelName"]
                        print(f"Модель: {self.model_name}")
            except Exception as e:
                print(f"Не удалось получить модель: {e}")
                self.model_name = None

            return True
        except Exception as e:
            print(f"✗ Ошибка: {e}")
            return False

    async def set_picture_mode(self, mode):
        """Установить режим изображения"""
        if not self.client:
            return False

        # Проверяем подключение и переподключаемся при необходимости
        if not self.client.is_connected():
            print("Клиент не подключен, пытаемся переподключиться...")
            try:
                await self.client.connect()
                print("✓ Переподключено!")
            except Exception as e:
                print(f"✗ Не удалось переподключиться: {e}")
                return False

        try:
            # Используем правильный метод set_current_picture_mode из aiopylgtv
            result = await self.client.set_current_picture_mode(mode)
            print(f"Режим изменен на '{mode}': {result}")
            return True
        except Exception as e:
            print(f"Ошибка при установке через set_current_picture_mode: {e}")
            # Попробуем альтернативный метод с получением текущего входа
            try:
                current_input = await self.client.get_input()
                print(f"Текущий вход: {current_input}")
                result = await self.client.set_picture_mode(mode, current_input)
                print(f"Режим изменен на '{mode}' через set_picture_mode: {result}")
                return True
            except Exception as e2:
                print(f"Ошибка при установке через set_picture_mode: {e2}")
                return False

    async def get_current_picture_mode(self) -> Optional[str]:
        """Получить текущий режим изображения"""
        if not self.client:
            return None

        try:
            payload = {"category": "picture", "keys": ["pictureMode"]}
            result = await self.client.request("settings/getSystemSettings", payload)
            if result and "settings" in result:
                settings = result["settings"]
                if "pictureMode" in settings:
                    return settings["pictureMode"]
        except Exception as e:
            print(f"Ошибка получения текущего режима: {e}")

        print("⚠ Не удалось получить текущий режим изображения")
        return None

    async def get_picture_modes(self):
        """Получить доступные режимы"""
        if not self.client:
            return None

        try:
            modes = await self.client.request(
                "ssap://com.webos.service.tv.picture/getPictureModeList"
            )
            return modes
        except Exception as e:
            print(f"Ошибка: {e}")
            return None

    async def subscribe_picture_mode_changes(self, callback):
        """Подписаться на изменения picture mode"""
        if not self.client:
            return False

        try:
            self.picture_mode_callback = callback
            # Подписываемся на изменения pictureMode
            await self.client.subscribe_picture_settings(
                self._on_picture_settings_change, keys=["pictureMode"]
            )
            return True
        except Exception as e:
            print(f"Ошибка подписки на изменения picture mode: {e}")
            return False

    async def subscribe_picture_settings_changes(self, callback):
        """Подписаться на изменения настроек изображения (яркость, уровень черного, глубина цвета)"""
        if not self.client:
            return False

        try:
            self.picture_settings_callback = callback
            # Подписываемся на изменения всех параметров
            await self.client.subscribe_picture_settings(
                self._on_all_picture_settings_change,
                keys=["backlight", "brightness", "color"],
            )
            return True
        except Exception as e:
            print(f"Ошибка подписки на изменения настроек: {e}")
            return False

    async def _on_picture_settings_change(self, settings):
        """Обработчик изменений настроек изображения (только pictureMode)"""
        if settings and "pictureMode" in settings and self.picture_mode_callback:
            picture_mode = settings["pictureMode"]
            # Вызываем callback (может быть async или sync)
            if asyncio.iscoroutinefunction(self.picture_mode_callback):
                await self.picture_mode_callback(picture_mode)
            else:
                self.picture_mode_callback(picture_mode)

    async def _on_all_picture_settings_change(self, settings):
        """Обработчик изменений всех настроек изображения"""
        if settings and self.picture_settings_callback:
            # Вызываем callback (может быть async или sync)
            if asyncio.iscoroutinefunction(self.picture_settings_callback):
                await self.picture_settings_callback(settings)
            else:
                self.picture_settings_callback(settings)

    async def get_picture_setting(self, key: str) -> Optional[int]:
        """Получить значение параметра изображения"""
        if not self.client:
            return None

        try:
            payload = {"category": "picture", "keys": [key]}
            result = await self.client.request("settings/getSystemSettings", payload)
            if result and "settings" in result and key in result["settings"]:
                value = result["settings"][key]
                return int(value) if isinstance(value, (str, int)) else None
        except Exception as e:
            print(f"Ошибка получения {key}: {e}")
        return None

    async def set_picture_setting(self, key: str, value: int) -> bool:
        """Установить значение параметра изображения"""
        if not self.client:
            return False

        try:
            payload = {"category": "picture", "settings": {key: value}}
            result = await self.client.request("settings/setSystemSettings", payload)
            return result.get("returnValue", False)
        except Exception as e:
            print(f"Ошибка установки {key}: {e}")
            return False

    async def get_brightness(self) -> Optional[int]:
        """Получить яркость (backlight)"""
        return await self.get_picture_setting("backlight")

    async def set_brightness(self, value: int) -> bool:
        """Установить яркость (backlight)"""
        return await self.set_picture_setting("backlight", value)

    async def get_black_level(self) -> Optional[int]:
        """Получить уровень черного (brightness)"""
        return await self.get_picture_setting("brightness")

    async def set_black_level(self, value: int) -> bool:
        """Установить уровень черного (brightness)"""
        return await self.set_picture_setting("brightness", value)

    async def get_color_depth(self) -> Optional[int]:
        """Получить глубину цвета (color)"""
        return await self.get_picture_setting("color")

    async def set_color_depth(self, value: int) -> bool:
        """Установить глубину цвета (color)"""
        return await self.set_picture_setting("color", value)

    async def disconnect(self):
        """Отключение"""
        if self.client:
            await self.client.disconnect()


# ============================================================================
# GUI ПРИЛОЖЕНИЕ
# ============================================================================


class LGMonitorGUI:
    def __init__(self, root):
        self.root = root
        self.root.geometry("550x650")  # Увеличили для ползунков
        self.root.resizable(False, False)  # Запрещаем изменение размеров окна

        self.controller = LGMonitorController()
        self.controller._gui_mode = (
            True  # Флаг для GUI режима (не открываем окно настроек Windows)
        )
        self.controller.picture_settings_callback = None  # Callback для настроек
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.connected = False
        self.tray_icon = None
        self.tray_thread = None
        self.current_hdr_state = None  # Текущее состояние HDR на мониторе
        self.connect_button = None  # Кнопка подключения/обновления
        self.hdr_monitor_task = None  # Задача мониторинга HDR
        self._hdr_check_id = None  # ID для периодической проверки HDR
        self.current_picture_mode = None  # Текущий режим для проверки ограничений

        # Переменные для ползунков
        self.brightness_var = tk.IntVar(value=50)
        self.black_level_var = tk.IntVar(value=50)
        self.color_depth_var = tk.IntVar(value=50)

        # Виджеты ползунков (для блокировки/разблокировки)
        self.brightness_label = None
        self.brightness_value_label = None
        self.black_level_scale = None
        self.black_level_label = None
        self.black_level_value_label = None
        self.color_depth_scale = None
        self.color_depth_label = None
        self.color_depth_value_label = None

        # Таймеры для debounce (задержка перед отправкой)
        self._brightness_timer = None
        self._black_level_timer = None
        self._color_depth_timer = None

        # Флаг для игнорирования обновлений из WebOS (чтобы не создавать циклы)
        self._updating_from_webos = False

        # Загружаем сохраненные настройки
        _, self.language, self.start_minimized, _, self.close_to_tray, _ = (
            load_monitor_config()
        )
        if not self.language:
            self.language = "en"  # Язык интерфейса (en/ru)

        # Всегда используем светлую тему
        self.theme = "light"

        self.setup_ui()
        self.start_asyncio_thread()

        # Устанавливаем иконку окна
        self.set_window_icon()

        # Настройка закрытия окна - сворачивание в трей
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Пытаемся загрузить и подключиться к сохраненному монитору
        # Вызываем после небольшой задержки, чтобы UI успел инициализироваться
        self.root.after(100, self.load_and_connect_saved_monitor)

        # Запускаем системный трей
        if TRAY_AVAILABLE:
            self.start_tray()

        # Если нужно запустить свернутой - сворачиваем окно
        if self.start_minimized and TRAY_AVAILABLE:
            self.root.after(200, lambda: self.root.withdraw())

    def get_text(self, key: str) -> str:
        """Получить переведенный текст"""
        return UI_TRANSLATIONS.get(self.language, UI_TRANSLATIONS["en"]).get(key, key)

    def setup_ui(self):
        # Устанавливаем заголовок окна
        self.root.title(self.get_text("title"))

        # Настраиваем стили один раз
        self.setup_styles()

        # Верхняя панель с заголовком и иконками переключения
        top_frame = ttk.Frame(self.root)
        top_frame.pack(pady=10, fill=tk.X)

        # Заголовок
        self.title_label = ttk.Label(
            top_frame, text=self.get_text("title"), font=("Arial", 16, "bold")
        )
        self.title_label.pack(side=tk.LEFT, padx=(20, 0))

        # Иконки переключения справа
        controls_frame = ttk.Frame(top_frame)
        controls_frame.pack(side=tk.RIGHT, padx=(0, 20))

        # Кнопка переключения языка - текст EN/RU
        self.language_var = tk.StringVar(value=self.language)
        lang_text = self.language.upper()  # EN или RU
        self.lang_button = tk.Button(
            controls_frame,
            text=lang_text,
            font=("Arial", 9, "bold"),
            command=self.toggle_language_icon,
            relief="flat",
            cursor="hand2",
            width=3,
            height=1,
            padx=4,
            pady=2,
            bg="#f0f0f0",
            fg="#000000",
            activebackground="#e0e0e0",
        )
        self.lang_button.pack(side=tk.LEFT, padx=3)

        # Настройки
        settings_frame = ttk.Frame(self.root)
        settings_frame.pack(pady=5)

        # Чекбокс автозапуска (только для Windows)
        if platform.system() == "Windows":
            self.autostart_var = tk.BooleanVar(value=self.is_autostart_enabled())
            self.autostart_check = ttk.Checkbutton(
                settings_frame,
                text=self.get_text("autostart"),
                variable=self.autostart_var,
                command=self.toggle_autostart,
            )
            self.autostart_check.pack(side=tk.LEFT, padx=10)

        # Чекбокс "запускать свернутой"
        self.start_minimized_var = tk.BooleanVar(value=self.start_minimized)
        self.start_minimized_check = ttk.Checkbutton(
            settings_frame,
            text=self.get_text("start_minimized"),
            variable=self.start_minimized_var,
            command=self.toggle_start_minimized,
        )
        self.start_minimized_check.pack(side=tk.LEFT, padx=10)

        # Чекбокс "закрывать в трей"
        self.close_to_tray_var = tk.BooleanVar(value=self.close_to_tray)
        self.close_to_tray_check = ttk.Checkbutton(
            settings_frame,
            text=self.get_text("close_to_tray"),
            variable=self.close_to_tray_var,
            command=self.toggle_close_to_tray,
        )
        self.close_to_tray_check.pack(side=tk.LEFT, padx=10)

        # Поиск мониторов
        self.search_frame = ttk.LabelFrame(
            self.root, text=self.get_text("search_monitors"), padding=10
        )
        self.search_frame.pack(pady=5, padx=20, fill=tk.X)

        self.find_button = ttk.Button(
            self.search_frame,
            text=self.get_text("find_monitors"),
            command=self.discover_monitors,
        )
        self.find_button.pack(pady=5)

        self.monitor_var = tk.StringVar()
        self.monitor_list = ttk.Combobox(
            self.search_frame, textvariable=self.monitor_var, state="readonly", width=30
        )
        self.monitor_list.pack(pady=5)

        self.connect_button = ttk.Button(
            self.search_frame,
            text=self.get_text("connect"),
            command=self.connect_or_refresh,
        )
        self.connect_button.pack(pady=5)

        # Режимы изображения
        self.mode_frame = ttk.LabelFrame(
            self.root, text=self.get_text("picture_mode"), padding=10
        )
        self.mode_frame.pack(pady=10, padx=20, fill=tk.X)

        self.mode_label = ttk.Label(self.mode_frame, text=self.get_text("mode"))
        self.mode_label.pack(side=tk.LEFT, padx=5)

        self.mode_var = tk.StringVar(value="normal")
        # Начальный список режимов (будет обновляться в зависимости от HDR)
        self.all_modes = {
            "sdr": [
                "personalized",
                "game",
                "normal",
                "vivid",
                "cinema",
                "sports",
                "eco",
                "filmMaker",
                "expert1",
                "expert2",
            ],
            "hdr": [
                "hdrPersonalized",
                "hdrGame",
                "hdrStandard",
                "hdrCinema",
                "hdrCinemaBright",
                "hdrVivid",
                "hdrEco",
                "hdrFilmMaker",
            ],
        }
        self.mode_combo = ttk.Combobox(
            self.mode_frame,
            textvariable=self.mode_var,
            values=self.all_modes["sdr"],
            state="readonly",
            width=35,
        )
        self.mode_combo.pack(side=tk.LEFT, padx=5)

        self.apply_button = ttk.Button(
            self.mode_frame, text=self.get_text("apply"), command=self.set_mode
        )
        self.apply_button.pack(side=tk.LEFT, padx=5)

        # Настройки изображения (ползунки)
        self.settings_frame = ttk.LabelFrame(
            self.root, text=self.get_text("settings"), padding=15
        )
        self.settings_frame.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)

        # Создаем ползунки
        self.create_brightness_slider()
        self.create_black_level_slider()
        self.create_color_depth_slider()

        # Кнопка сброса настроек
        reset_frame = ttk.Frame(self.settings_frame)
        reset_frame.pack(fill=tk.X, pady=(15, 5))
        self.reset_button = ttk.Button(
            reset_frame,
            text=self.get_text("reset_settings"),
            command=self.reset_picture_settings,
        )
        self.reset_button.pack(side=tk.RIGHT)

        # Подсказка
        self.hint_frame = ttk.Frame(self.root)
        self.hint_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=5)
        self.hint_label = ttk.Label(
            self.hint_frame,
            text=self.get_text("hint"),
            font=("TkDefaultFont", 8),
            foreground="gray",
        )
        self.hint_label.pack()

        # Статус
        self.status_label = ttk.Label(
            self.root, text=self.get_text("ready"), font=("TkDefaultFont", 9)
        )
        self.status_label.pack(pady=5)

    def create_brightness_slider(self):
        """Создать ползунок яркости"""
        frame = ttk.Frame(self.settings_frame)
        frame.pack(fill=tk.X, pady=8)

        self.brightness_label = ttk.Label(
            frame,
            text=self.get_text("brightness"),
            width=15,
            anchor=tk.W,
        )
        self.brightness_label.pack(side=tk.LEFT, padx=(0, 10))

        self.brightness_value_label = ttk.Label(frame, text="50", width=3)
        self.brightness_value_label.pack(side=tk.RIGHT, padx=(10, 0))

        scale = ttk.Scale(
            frame,
            from_=0,
            to=100,
            variable=self.brightness_var,
            orient=tk.HORIZONTAL,
            command=lambda v: self.on_brightness_change(v),
        )
        scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)

        # Обновляем метку при изменении переменной
        self.brightness_var.trace_add(
            "write",
            lambda *args: self.brightness_value_label.config(
                text=str(int(self.brightness_var.get()))
            ),
        )

    def create_black_level_slider(self):
        """Создать ползунок уровня черного"""
        frame = ttk.Frame(self.settings_frame)
        frame.pack(fill=tk.X, pady=8)

        self.black_level_label = ttk.Label(
            frame,
            text=self.get_text("black_level"),
            width=15,
            anchor=tk.W,
        )
        self.black_level_label.pack(side=tk.LEFT, padx=(0, 10))

        self.black_level_value_label = ttk.Label(frame, text="50", width=3)
        self.black_level_value_label.pack(side=tk.RIGHT, padx=(10, 0))

        self.black_level_scale = ttk.Scale(
            frame,
            from_=0,
            to=100,
            variable=self.black_level_var,
            orient=tk.HORIZONTAL,
            command=lambda v: self.on_black_level_change(v),
        )
        self.black_level_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)

        # Обновляем метку при изменении переменной
        self.black_level_var.trace_add(
            "write",
            lambda *args: self.black_level_value_label.config(
                text=str(int(self.black_level_var.get()))
            ),
        )

    def create_color_depth_slider(self):
        """Создать ползунок глубины цвета"""
        frame = ttk.Frame(self.settings_frame)
        frame.pack(fill=tk.X, pady=8)

        self.color_depth_label = ttk.Label(
            frame,
            text=self.get_text("color_depth"),
            width=15,
            anchor=tk.W,
        )
        self.color_depth_label.pack(side=tk.LEFT, padx=(0, 10))

        self.color_depth_value_label = ttk.Label(frame, text="50", width=3)
        self.color_depth_value_label.pack(side=tk.RIGHT, padx=(10, 0))

        self.color_depth_scale = ttk.Scale(
            frame,
            from_=0,
            to=100,
            variable=self.color_depth_var,
            orient=tk.HORIZONTAL,
            command=lambda v: self.on_color_depth_change(v),
        )
        self.color_depth_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)

        # Обновляем метку при изменении переменной
        self.color_depth_var.trace_add(
            "write",
            lambda *args: self.color_depth_value_label.config(
                text=str(int(self.color_depth_var.get()))
            ),
        )

    def on_brightness_change(self, value):
        """Обработчик изменения яркости с задержкой (debounce)"""
        if not self.connected or self._updating_from_webos:
            return

        # Отменяем предыдущий таймер, если есть
        if self._brightness_timer:
            self.root.after_cancel(self._brightness_timer)

        # Устанавливаем новый таймер на 300мс
        int_value = int(float(value))
        self._brightness_timer = self.root.after(
            300, lambda: self._send_brightness(int_value)
        )

    def _send_brightness(self, value):
        """Отправить значение яркости на монитор"""

        async def set_value():
            await self.controller.set_brightness(value)

        self.run_async(set_value())

    def on_black_level_change(self, value):
        """Обработчик изменения уровня черного с задержкой (debounce)"""
        if not self.connected or self._updating_from_webos:
            return

        # Проверяем, разрешено ли изменение в текущем режиме
        if self.current_picture_mode and not can_adjust_black_level(
            self.current_picture_mode
        ):
            return

        # Отменяем предыдущий таймер, если есть
        if self._black_level_timer:
            self.root.after_cancel(self._black_level_timer)

        # Устанавливаем новый таймер на 300мс
        int_value = int(float(value))
        self._black_level_timer = self.root.after(
            300, lambda: self._send_black_level(int_value)
        )

    def _send_black_level(self, value):
        """Отправить значение уровня черного на монитор"""

        async def set_value():
            await self.controller.set_black_level(value)

        self.run_async(set_value())

    def on_color_depth_change(self, value):
        """Обработчик изменения глубины цвета с задержкой (debounce)"""
        if not self.connected or self._updating_from_webos:
            return

        # Проверяем, разрешено ли изменение в текущем режиме
        if self.current_picture_mode and not can_adjust_color_depth(
            self.current_picture_mode
        ):
            return

        # Отменяем предыдущий таймер, если есть
        if self._color_depth_timer:
            self.root.after_cancel(self._color_depth_timer)

        # Устанавливаем новый таймер на 300мс
        int_value = int(float(value))
        self._color_depth_timer = self.root.after(
            300, lambda: self._send_color_depth(int_value)
        )

    def _send_color_depth(self, value):
        """Отправить значение глубины цвета на монитор"""

        async def set_value():
            await self.controller.set_color_depth(value)

        self.run_async(set_value())

    def update_slider_states(self):
        """Обновить состояние ползунков в зависимости от режима"""
        if not self.current_picture_mode:
            return

        # Проверяем доступность параметров
        can_black = can_adjust_black_level(self.current_picture_mode)
        can_color = can_adjust_color_depth(self.current_picture_mode)

        # Уровень черного
        if can_black:
            self.black_level_scale.state(["!disabled"])
            self.black_level_label.config(foreground="black")
        else:
            self.black_level_scale.state(["disabled"])
            self.black_level_label.config(foreground="gray")

        # Глубина цвета
        if can_color:
            self.color_depth_scale.state(["!disabled"])
            self.color_depth_label.config(foreground="black")
        else:
            self.color_depth_scale.state(["disabled"])
            self.color_depth_label.config(foreground="gray")

    def load_slider_values(self):
        """Загрузить текущие значения с монитора"""
        if not self.connected:
            return

        async def load_values():
            try:
                brightness = await self.controller.get_brightness()
                black_level = await self.controller.get_black_level()
                color_depth = await self.controller.get_color_depth()

                def update_ui():
                    if brightness is not None:
                        self.brightness_var.set(brightness)
                        self.black_level_value_label.config(text=str(brightness))
                    if black_level is not None:
                        self.black_level_var.set(black_level)
                        self.black_level_value_label.config(text=str(black_level))
                    if color_depth is not None:
                        self.color_depth_var.set(color_depth)
                        self.color_depth_value_label.config(text=str(color_depth))

                self.root.after(0, update_ui)
            except Exception as e:
                print(f"Ошибка загрузки значений: {e}")

        self.run_async(load_values())

    def reset_picture_settings(self):
        """Сбросить настройки изображения на значения по умолчанию для текущего режима"""
        if not self.connected or not self.current_picture_mode:
            return

        # Получаем настройки по умолчанию для текущего режима
        if self.current_picture_mode not in DEFAULT_MODE_SETTINGS:
            print(f"Нет настроек по умолчанию для режима {self.current_picture_mode}")
            return

        default_brightness, default_black_level, default_color_depth = (
            DEFAULT_MODE_SETTINGS[self.current_picture_mode]
        )

        async def apply_defaults():
            try:
                # Всегда применяем яркость
                await self.controller.set_brightness(default_brightness)

                # Применяем уровень черного только если это разрешено
                if can_adjust_black_level(self.current_picture_mode):
                    await self.controller.set_black_level(default_black_level)

                # Применяем глубину цвета только если это разрешено
                if can_adjust_color_depth(self.current_picture_mode):
                    await self.controller.set_color_depth(default_color_depth)

                # Обновляем UI
                def update_ui():
                    self.brightness_var.set(default_brightness)
                    if can_adjust_black_level(self.current_picture_mode):
                        self.black_level_var.set(default_black_level)
                    if can_adjust_color_depth(self.current_picture_mode):
                        self.color_depth_var.set(default_color_depth)

                    # Обновляем статус
                    self.status_label.config(
                        text=f"✓ {self.get_text('reset_settings')}"
                    )

                self.root.after(0, update_ui)
                print(
                    f"Сброс настроек для режима {self.current_picture_mode}: яркость={default_brightness}, уровень черного={default_black_level}, глубина цвета={default_color_depth}"
                )

            except Exception as e:
                print(f"Ошибка сброса настроек: {e}")
                self.root.after(
                    0, lambda: self.status_label.config(text=f"✗ Ошибка сброса")
                )

        self.run_async(apply_defaults())

    def update_ui_texts(self):
        """Обновить все тексты интерфейса при смене языка"""
        self.root.title(self.get_text("title"))
        self.title_label.config(text=self.get_text("title"))
        self.search_frame.config(text=self.get_text("search_monitors"))
        self.find_button.config(text=self.get_text("find_monitors"))
        self.connect_button.config(text=self.get_text("connect"))
        self.mode_frame.config(text=self.get_text("picture_mode"))
        self.mode_label.config(text=self.get_text("mode"))
        self.apply_button.config(text=self.get_text("apply"))
        self.hint_label.config(text=self.get_text("hint"))
        # Обновляем текст чекбокса автозапуска
        if platform.system() == "Windows" and hasattr(self, "autostart_check"):
            self.autostart_check.config(text=self.get_text("autostart"))
        # Обновляем текст чекбокса "запускать свернутой"
        if hasattr(self, "start_minimized_check"):
            self.start_minimized_check.config(text=self.get_text("start_minimized"))
        # Обновляем текст чекбокса "закрывать в трей"
        if hasattr(self, "close_to_tray_check"):
            self.close_to_tray_check.config(text=self.get_text("close_to_tray"))
        # Обновляем тексты настроек изображения
        if hasattr(self, "settings_frame"):
            self.settings_frame.config(text=self.get_text("settings"))
        if hasattr(self, "brightness_label"):
            self.brightness_label.config(text=self.get_text("brightness"))
        if hasattr(self, "black_level_label"):
            self.black_level_label.config(text=self.get_text("black_level"))
        if hasattr(self, "color_depth_label"):
            self.color_depth_label.config(text=self.get_text("color_depth"))
        if hasattr(self, "reset_button"):
            self.reset_button.config(text=self.get_text("reset_settings"))
        # Обновляем статус
        if hasattr(self, "status_label"):
            if not self.connected:
                self.status_label.config(text=self.get_text("ready"))
            # Если подключен, статус обновится автоматически при следующем изменении

    def toggle_language_icon(self):
        """Переключить язык через кнопку-иконку"""
        # Переключаем язык
        new_language = "ru" if self.language == "en" else "en"
        self.language = new_language
        self.language_var.set(new_language)

        # Обновляем текст на кнопке
        lang_text = new_language.upper()  # EN или RU
        self.lang_button.config(text=lang_text)

        # Очищаем строку состояния (будет обновлена при следующем событии)
        if hasattr(self, "status_label"):
            if self.connected:
                self.status_label.config(text="")
            else:
                # Если не подключены, показываем "Готов"
                self.status_label.config(text=self.get_text("ready"))

        # Сохраняем настройки и обновляем интерфейс
        self.save_all_settings()
        self.update_ui_texts()

        # Обновляем UI режимов
        if self.connected:
            self._update_modes_ui(
                self.current_hdr_state if self.current_hdr_state is not None else False
            )

        # Обновляем меню трея
        if TRAY_AVAILABLE and self.tray_icon:
            self.update_tray_menu()

    def on_language_change(self, event=None):
        """Обработчик изменения языка (старый метод для совместимости)"""
        new_language = self.language_var.get()
        if new_language != self.language:
            self.language = new_language
            # Сохраняем язык в конфиг
            # Используем общий метод сохранения
            self.save_all_settings()
            # Обновляем все тексты интерфейса
            self.update_ui_texts()
            # Обновляем UI режимов
            if self.connected:
                self._update_modes_ui(
                    self.current_hdr_state
                    if self.current_hdr_state is not None
                    else False
                )
            # Обновляем меню трея
            if TRAY_AVAILABLE and self.tray_icon:
                self.update_tray_menu()

    def is_autostart_enabled(self) -> bool:
        """Проверить, включен ли автозапуск"""
        if platform.system() != "Windows":
            return False

        try:
            import winreg

            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_READ,
            )
            try:
                winreg.QueryValueEx(key, "LGMonitorModeSwitcher")
                winreg.CloseKey(key)
                return True
            except FileNotFoundError:
                winreg.CloseKey(key)
                return False
        except Exception:
            return False

    def toggle_autostart(self):
        """Переключить автозапуск"""
        if platform.system() != "Windows":
            return

        try:
            import winreg

            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"

            if self.autostart_var.get():
                # Включаем автозапуск
                if getattr(sys, "frozen", False):
                    # Если запущено из exe
                    exe_path = sys.executable
                else:
                    # Если запущено из Python скрипта (для разработки)
                    exe_path = f'"{sys.executable}" "{os.path.abspath(__file__)}"'

                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    key_path,
                    0,
                    winreg.KEY_SET_VALUE,
                )
                winreg.SetValueEx(
                    key, "LGMonitorModeSwitcher", 0, winreg.REG_SZ, exe_path
                )
                winreg.CloseKey(key)
            else:
                # Выключаем автозапуск
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    key_path,
                    0,
                    winreg.KEY_SET_VALUE,
                )
                try:
                    winreg.DeleteValue(key, "LGMonitorModeSwitcher")
                except FileNotFoundError:
                    pass  # Уже удалено
                winreg.CloseKey(key)
        except Exception:
            pass  # Игнорируем ошибки

    def toggle_start_minimized(self):
        """Переключить настройку запуска свернутой"""
        self.start_minimized = self.start_minimized_var.get()
        self.save_all_settings()

    def toggle_close_to_tray(self):
        """Переключить настройку закрытия в трей"""
        self.close_to_tray = self.close_to_tray_var.get()
        self.save_all_settings()

    def save_all_settings(self):
        """Сохранить все настройки в конфиг"""
        saved_ip, _, _, saved_mac, _, _ = load_monitor_config()
        ip = self.controller.ip if self.controller.ip else saved_ip if saved_ip else ""
        save_monitor_config(
            ip,
            self.language,
            self.start_minimized,
            saved_mac,
            self.close_to_tray,
            self.theme,
        )

    def start_asyncio_thread(self):
        """Запуск asyncio в отдельном потоке"""

        def run_loop(loop):
            asyncio.set_event_loop(loop)
            loop.run_forever()

        self.loop = asyncio.new_event_loop()
        thread = threading.Thread(target=run_loop, args=(self.loop,), daemon=True)
        thread.start()

    def run_async(self, coro):
        """Запуск асинхронной функции"""
        return asyncio.run_coroutine_threadsafe(coro, self.loop)

    def discover_monitors(self):
        self.status_label.config(text=self.get_text("searching"))

        def search():
            # Получаем сохраненный MAC адрес для поиска по нему
            saved_ip, _, _, saved_mac, _, _ = load_monitor_config()
            monitors, monitors_mac = discover_lg_monitors(
                timeout=1, saved_mac=saved_mac
            )
            self.root.after(0, self.update_monitor_list, monitors, monitors_mac)

        threading.Thread(target=search, daemon=True).start()

    def update_monitor_list(self, monitors, monitors_mac=None):
        if monitors:
            # Если монитор уже подключен и есть название модели, сохраняем его
            if self.connected and self.controller.ip and self.controller.model_name:
                # Обновляем список, сохраняя название модели для подключенного монитора
                updated_monitors = []
                for monitor_ip in monitors:
                    if monitor_ip == self.controller.ip:
                        # Для подключенного монитора добавляем название модели
                        updated_monitors.append(
                            f"{monitor_ip} ({self.controller.model_name})"
                        )
                    else:
                        updated_monitors.append(monitor_ip)
                monitors = updated_monitors

            self.monitor_list["values"] = monitors

            # Проверяем, изменился ли IP для сохраненного MAC адреса
            saved_ip, _, _, saved_mac, _, _ = load_monitor_config()
            if saved_mac and monitors_mac:
                # Ищем монитор по сохраненному MAC адресу
                for ip, mac in monitors_mac.items():
                    if mac.lower() == saved_mac.lower():
                        # Если IP изменился, обновляем его
                        if ip != saved_ip:
                            print(
                                f"IP адрес изменился: {saved_ip} -> {ip} (MAC: {mac})"
                            )
                            # Удаляем старый ключ, так как он привязан к старому IP
                            if os.path.exists(WEBOS_KEY_FILE):
                                try:
                                    os.remove(WEBOS_KEY_FILE)
                                    print(
                                        f"Удален старый ключ для IP {saved_ip}, будет запрошен новый ключ для IP {ip}"
                                    )
                                except Exception as e:
                                    print(f"Не удалось удалить старый ключ: {e}")
                            # Если монитор был подключен, отключаем его
                            if self.connected:
                                self.connected = False
                                # Останавливаем мониторинг HDR
                                self.stop_hdr_monitoring()
                                # Показываем кнопку подключения
                                if self.connect_button:
                                    self.connect_button.pack(pady=5)
                                # Обновляем статус
                                self.status_label.config(text=self.get_text("ready"))
                            self.controller.ip = ip
                            # Обновляем сохраненный IP в конфиге
                            save_monitor_config(
                                ip, self.language, self.start_minimized, mac
                            )
                            # Если монитор был подключен, обновляем отображаемое имя
                            if self.controller.model_name:
                                self.update_monitor_display_name()
                        break

            # Устанавливаем текущий выбор на подключенный монитор, если он есть
            if self.connected and self.controller.ip and self.controller.model_name:
                display_name = f"{self.controller.ip} ({self.controller.model_name})"
                if display_name in monitors:
                    self.monitor_var.set(display_name)
                elif self.controller.ip in monitors:
                    self.monitor_var.set(self.controller.ip)
                else:
                    self.monitor_list.current(0)
                    self.monitor_var.set(monitors[0])
            else:
                self.monitor_list.current(0)
                self.controller.ip = (
                    monitors[0].split(" (")[0] if " (" in monitors[0] else monitors[0]
                )
                self.monitor_var.set(monitors[0])

            self.status_label.config(
                text=f"{len(monitors)} {self.get_text('monitors_found')}"
            )
        else:
            self.status_label.config(text=self.get_text("no_monitors"))
            messagebox.showwarning(
                self.get_text("search_monitors"), self.get_text("no_monitors")
            )

    def check_connection_status(self):
        """Проверить статус подключения к монитору"""
        if self.controller.client and hasattr(self.controller.client, "is_connected"):
            try:
                # Используем метод is_connected() если доступен
                return self.controller.client.is_connected()
            except Exception:
                # Если метод не работает, проверяем connection напрямую
                if hasattr(self.controller.client, "connection"):
                    return self.controller.client.connection is not None
        return False

    def connect_or_refresh(self):
        """Подключиться к монитору"""
        # Если уже подключен, ничего не делаем (мониторинг работает автоматически)
        if self.connected or self.check_connection_status():
            return
        # Если не подключен - подключаемся
        self.connect_monitor()

    def connect_monitor(self):
        monitor_str = self.monitor_var.get()
        if not monitor_str:
            messagebox.showwarning(
                self.get_text("ready"), self.get_text("select_monitor")
            )
            return

        # Извлекаем IP из строки (может быть "IP" или "IP (модель)")
        ip = monitor_str.split(" (")[0] if " (" in monitor_str else monitor_str
        self.controller.ip = ip
        self.status_label.config(text=f"{self.get_text('connect')} {ip}...")

        async def do_connect():
            result = await self.controller.connect()
            self.root.after(0, self.on_connect_result, result)

        self.run_async(do_connect())

    def on_connect_result(self, result, auto_connect=False):
        if result:
            self.connected = True
            # Формируем строку статуса с IP и моделью
            status_text = f"✓ {self.get_text('connected_to')} {self.controller.ip}"
            if self.controller.model_name:
                status_text += f" ({self.controller.model_name})"
            self.status_label.config(text=status_text)
            # Обновляем отображаемое имя в списке мониторов
            self.update_monitor_display_name()
            # Получаем MAC адрес для текущего IP из ARP таблицы
            ip_mac_map = get_ip_mac_mapping()
            mac_address = ip_mac_map.get(self.controller.ip)
            if mac_address:
                print(f"MAC адрес монитора: {mac_address}")
            # Сохраняем IP и MAC адрес при успешном подключении
            save_monitor_config(
                self.controller.ip, self.language, self.start_minimized, mac_address
            )
            # Обновляем список режимов в зависимости от текущего HDR состояния
            self.update_modes_based_on_hdr()
            # Скрываем кнопку подключения, так как мониторинг работает автоматически
            self.connect_button.pack_forget()
            # Запускаем мониторинг изменений HDR
            self.start_hdr_monitoring()
            if not auto_connect:
                messagebox.showinfo(
                    self.get_text("connect"),
                    self.get_text("connection_success"),
                )
        else:
            self.connected = False
            self.status_label.config(text=f"✗ {self.get_text('connection_error')}")
            # Показываем кнопку подключения обратно
            if self.connect_button:
                self.connect_button.pack(pady=5)
            # Останавливаем мониторинг HDR
            self.stop_hdr_monitoring()
            if not auto_connect:
                messagebox.showerror(
                    self.get_text("connection_error"),
                    self.get_text("connection_failed"),
                )

    def update_modes_based_on_hdr(self):
        """Обновить список режимов в зависимости от состояния HDR на мониторе"""
        if not self.connected:
            return

        async def check_hdr_state():
            try:
                current_mode = await self.controller.get_current_picture_mode()
                print(f"DEBUG: Текущий режим для определения HDR: {current_mode}")
                if current_mode:
                    # Определяем состояние HDR по текущему режиму
                    hdr_enabled = current_mode.lower().startswith("hdr")
                    print(f"DEBUG: HDR включен: {hdr_enabled}")
                    self.root.after(0, self._update_modes_ui, hdr_enabled)
                else:
                    print(
                        "DEBUG: Не удалось получить текущий режим, используем значение по умолчанию"
                    )
                    # Если не удалось получить режим, оставляем текущее состояние
                    self.root.after(
                        0,
                        self._update_modes_ui,
                        (
                            self.current_hdr_state
                            if self.current_hdr_state is not None
                            else False
                        ),
                    )
            except Exception as e:
                print(f"Ошибка при проверке состояния HDR: {e}")
                # В случае ошибки используем текущее состояние или False
                self.root.after(
                    0,
                    self._update_modes_ui,
                    (
                        self.current_hdr_state
                        if self.current_hdr_state is not None
                        else False
                    ),
                )

        self.run_async(check_hdr_state())

    def _update_modes_ui(self, hdr_enabled):
        """Обновить UI с режимами в зависимости от HDR"""
        print(f"DEBUG: Обновление UI, HDR включен: {hdr_enabled}")
        self.current_hdr_state = hdr_enabled
        modes = self.all_modes["hdr"] if hdr_enabled else self.all_modes["sdr"]
        print(f"DEBUG: Режимы для отображения: {modes}")

        # Создаем список переведенных режимов для отображения
        translated_modes = [get_mode_translation(mode, self.language) for mode in modes]

        # Обновляем выпадающий список с переводами
        # Сохраняем соответствие между переводами и оригинальными именами
        self.mode_combo["values"] = translated_modes

        # Получаем текущий режим с монитора и устанавливаем его
        async def set_current_mode():
            try:
                current_mode = await self.controller.get_current_picture_mode()
                print(f"DEBUG: Текущий режим с монитора: {current_mode}")
                if current_mode and current_mode in modes:
                    # Сохраняем текущий режим
                    self.current_picture_mode = current_mode
                    # Устанавливаем переведенное значение
                    translated_mode = get_mode_translation(current_mode, self.language)

                    def set_mode_value(value):
                        self.mode_var.set(value)
                        # Обновляем состояние ползунков
                        self.update_slider_states()
                        # Загружаем значения
                        self.load_slider_values()

                    self.root.after(0, set_mode_value, translated_mode)
                    print(f"DEBUG: Установлен текущий режим: {translated_mode}")
                else:
                    # Если текущий режим не в новом списке, выбираем первый
                    default_mode = (
                        modes[0]
                        if modes
                        else ("normal" if not hdr_enabled else "hdrStandard")
                    )
                    translated_default = get_mode_translation(
                        default_mode, self.language
                    )

                    def set_default_value(value):
                        self.mode_var.set(value)

                    self.root.after(0, set_default_value, translated_default)
                    print(f"DEBUG: Установлен режим по умолчанию: {translated_default}")
            except Exception as e:
                print(f"Ошибка при установке текущего режима: {e}")
                # При ошибке выбираем первый режим
                default_mode = (
                    modes[0]
                    if modes
                    else ("normal" if not hdr_enabled else "hdrStandard")
                )
                translated_default = get_mode_translation(default_mode, self.language)

                def set_error_value(value):
                    self.mode_var.set(value)

                self.root.after(0, set_error_value, translated_default)

        self.run_async(set_current_mode())

        # Обновляем меню трея и иконку
        if TRAY_AVAILABLE and self.tray_icon:
            self.update_tray_menu()
            self.update_tray_icon(hdr_enabled)

    def load_and_connect_saved_monitor(self):
        """Загрузить сохраненный IP и попытаться подключиться"""
        saved_ip, _, _, saved_mac, _, _ = load_monitor_config()
        if saved_ip:
            self.monitor_var.set(saved_ip)
            self.monitor_list["values"] = [saved_ip]
            self.controller.ip = saved_ip
            self.status_label.config(
                text=f"{self.get_text('auto_connecting')} {saved_ip}..."
            )

            # Пытаемся подключиться автоматически
            async def do_auto_connect():
                # Сначала проверяем, может уже подключен
                if self.check_connection_status():
                    self.root.after(0, lambda: self.on_connect_result(True, True))
                else:
                    result = await self.controller.connect()
                    self.root.after(0, self.on_connect_result, result, True)

            self.run_async(do_auto_connect())

    def get_windows_hdr_state(self) -> Optional[bool]:
        """Получить текущее состояние HDR в Windows"""
        if platform.system() != "Windows":
            return None

        try:
            # Пробуем получить через PowerShell
            ps_script = """
            try {
                $regPath = "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\HDR"
                if (Test-Path $regPath) {
                    $value = Get-ItemProperty -Path $regPath -Name "UseHDR" -ErrorAction SilentlyContinue
                    if ($value) {
                        Write-Output $value.UseHDR
                    }
                }
            } catch {
                Write-Output "ERROR"
            }
            """

            result = subprocess.run(
                ["powershell", "-Command", ps_script],
                capture_output=True,
                text=True,
                timeout=3,
            )

            if result.returncode == 0 and result.stdout.strip():
                output = result.stdout.strip()
                if output == "1" or output.lower() == "true":
                    return True
                elif output == "0" or output.lower() == "false":
                    return False
        except Exception:
            pass  # Игнорируем ошибки

        return None

    def start_hdr_monitoring(self):
        """Запустить мониторинг изменений HDR"""
        if not self.connected:
            return

        # Подписка на изменения picture mode на мониторе через webOS
        def on_picture_mode_change(picture_mode):
            """Обработчик изменений picture mode с монитора"""
            if picture_mode:
                monitor_hdr = picture_mode.lower().startswith("hdr")
                self.root.after(0, self._update_modes_ui, monitor_hdr)
                print(
                    f"Изменение режима на мониторе: {picture_mode} (HDR: {monitor_hdr})"
                )

        # Подписываемся на изменения на мониторе
        self.run_async(
            self.controller.subscribe_picture_mode_changes(on_picture_mode_change)
        )

        # Подписка на изменения настроек изображения (яркость, уровень черного, глубина цвета)
        def on_picture_settings_change(settings):
            """Обработчик изменений настроек изображения с монитора"""
            if settings:
                # Проверяем, действительно ли значение изменилось
                changed = False
                if "backlight" in settings:
                    new_value = int(settings["backlight"])
                    if new_value != int(self.brightness_var.get()):
                        changed = True
                if "brightness" in settings:
                    new_value = int(settings["brightness"])
                    if new_value != int(self.black_level_var.get()):
                        changed = True
                if "color" in settings:
                    new_value = int(settings["color"])
                    if new_value != int(self.color_depth_var.get()):
                        changed = True

                if changed:
                    print(f"Изменение настроек: {settings}")

                def update_sliders():
                    # Устанавливаем флаг, чтобы не отправлять обратно на монитор
                    self._updating_from_webos = True

                    # Обновляем ползунки
                    if "backlight" in settings:
                        value = int(settings["backlight"])
                        self.brightness_var.set(value)
                    if "brightness" in settings:
                        value = int(settings["brightness"])
                        self.black_level_var.set(value)
                    if "color" in settings:
                        value = int(settings["color"])
                        self.color_depth_var.set(value)

                    # Сбрасываем флаг через небольшую задержку
                    self.root.after(
                        100, lambda: setattr(self, "_updating_from_webos", False)
                    )

                self.root.after(0, update_sliders)

        # Подписываемся на изменения настроек
        self.run_async(
            self.controller.subscribe_picture_settings_changes(
                on_picture_settings_change
            )
        )

        # Запускаем периодический опрос состояния HDR (каждые 3 секунды)
        # Это резервный механизм на случай, если подписка перестанет работать
        self._start_periodic_hdr_check()

    def stop_hdr_monitoring(self):
        """Остановить мониторинг изменений HDR"""
        # Задача остановится автоматически при проверке self.connected
        self.hdr_monitor_task = None
        # Отменяем периодическую проверку, если она запущена
        if hasattr(self, "_hdr_check_id") and self._hdr_check_id:
            self.root.after_cancel(self._hdr_check_id)
            self._hdr_check_id = None

    def _start_periodic_hdr_check(self):
        """Запустить периодическую проверку состояния HDR"""
        if not self.connected:
            return

        async def check_and_update_hdr():
            """Проверить текущее состояние HDR и обновить UI при необходимости"""
            if not self.connected:
                return

            try:
                current_mode = await self.controller.get_current_picture_mode()
                if current_mode:
                    hdr_enabled = current_mode.lower().startswith("hdr")
                    # Обновляем UI только если состояние изменилось
                    if self.current_hdr_state != hdr_enabled:
                        print(
                            f"Периодическая проверка: обнаружено изменение HDR ({self.current_hdr_state} -> {hdr_enabled})"
                        )
                        self.root.after(0, self._update_modes_ui, hdr_enabled)
            except Exception as e:
                print(f"Ошибка при периодической проверке HDR: {e}")
                # Если произошла ошибка подключения, пытаемся переподключиться
                if self.controller.client and not self.controller.client.is_connected():
                    print("Потеря соединения обнаружена, попытка переподключения...")
                    try:
                        await self.controller.client.connect()
                        print("✓ Переподключение успешно")
                    except Exception as reconnect_error:
                        print(f"✗ Не удалось переподключиться: {reconnect_error}")

        # Запускаем асинхронную проверку
        self.run_async(check_and_update_hdr())

        # Планируем следующую проверку через 5 секунд
        if self.connected:
            self._hdr_check_id = self.root.after(5000, self._start_periodic_hdr_check)

    def update_monitor_display_name(self):
        """Обновить отображаемое имя монитора в списке"""
        if self.controller.ip and self.controller.model_name:
            display_name = f"{self.controller.ip} ({self.controller.model_name})"
            # Обновляем текущее значение в списке
            current_values = list(self.monitor_list["values"])
            if current_values:
                # Заменяем IP на IP + модель, если IP найден в списке
                if self.controller.ip in current_values:
                    idx = current_values.index(self.controller.ip)
                    current_values[idx] = display_name
                    self.monitor_list["values"] = current_values
                    self.monitor_var.set(display_name)
                # Или добавляем новое значение, если его нет
                elif display_name not in current_values:
                    current_values.append(display_name)
                    self.monitor_list["values"] = current_values
                    self.monitor_var.set(display_name)

    def set_mode(self):
        if not self.connected:
            messagebox.showwarning("Внимание", "Сначала подключитесь к монитору")
            return

        translated_mode = self.mode_var.get()
        # Конвертируем переведенное значение обратно в оригинальное имя режима
        mode = get_mode_from_translation(translated_mode, self.language)
        self.status_label.config(
            text=f"{self.get_text('setting_mode')} {translated_mode}..."
        )

        async def do_set_mode():
            result = await self.controller.set_picture_mode(mode)
            self.root.after(0, self.on_mode_result, result, translated_mode)

        self.run_async(do_set_mode())

    def on_mode_result(self, result, translated_mode):
        if result:
            # translated_mode - это переведенное значение для отображения
            self.status_label.config(
                text=f"✓ {self.get_text('mode_set')} {translated_mode}"
            )
            # Получаем оригинальное значение для проверки HDR
            original_mode = get_mode_from_translation(translated_mode, self.language)
            self.current_picture_mode = original_mode
            hdr_enabled = original_mode.startswith("hdr")
            if self.current_hdr_state != hdr_enabled:
                self.current_hdr_state = hdr_enabled
                self._update_modes_ui(hdr_enabled)
            else:
                # Даже если HDR состояние не изменилось, обновляем ограничения ползунков
                self.update_slider_states()
        else:
            self.status_label.config(text=f"✗ {self.get_text('mode_error')}")

    def create_app_icon(self, hdr_mode=False):
        """Создать иконку приложения - круглую с белым фоном и красным кольцом

        Args:
            hdr_mode: если True, добавляет текст "HDR" по центру
        """
        # Создаем изображение с прозрачностью
        image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)

        # Центр и радиусы
        center = (32, 32)
        outer_radius = 30  # Радиус белого круга
        inner_radius = 23  # Радиус красного кольца (на 3px меньше)
        ring_thickness = 4  # Толщина красного кольца

        # Рисуем белый круг
        bbox_outer = [
            center[0] - outer_radius,
            center[1] - outer_radius,
            center[0] + outer_radius,
            center[1] + outer_radius,
        ]
        draw.ellipse(bbox_outer, fill="white", outline="white")

        # Рисуем красное кольцо (окружность)
        # Внешний радиус кольца
        bbox_ring_outer = [
            center[0] - inner_radius - ring_thickness,
            center[1] - inner_radius - ring_thickness,
            center[0] + inner_radius + ring_thickness,
            center[1] + inner_radius + ring_thickness,
        ]
        # Внутренний радиус кольца (для создания кольца рисуем большой круг и вырезаем маленький)
        bbox_ring_inner = [
            center[0] - inner_radius,
            center[1] - inner_radius,
            center[0] + inner_radius,
            center[1] + inner_radius,
        ]
        # Рисуем большой красный круг
        draw.ellipse(bbox_ring_outer, fill="#cb1744", outline="#cb1744")
        # Вырезаем внутреннюю часть (рисуем белый круг поверх)
        draw.ellipse(bbox_ring_inner, fill="white", outline="white")

        # Если HDR режим, добавляем красный круг по центру
        if hdr_mode:
            hdr_indicator_radius = 10
            bbox_hdr = [
                center[0] - hdr_indicator_radius,
                center[1] - hdr_indicator_radius,
                center[0] + hdr_indicator_radius,
                center[1] + hdr_indicator_radius,
            ]
            draw.ellipse(bbox_hdr, fill="#cb1744", outline="#cb1744")

        return image

    def create_tray_icon(self, hdr_mode=False):
        """Создать иконку для системного трея - использует ту же иконку что и окно

        Args:
            hdr_mode: если True, добавляет текст "HDR" по центру
        """
        return self.create_app_icon(hdr_mode)

    def set_window_icon(self):
        """Установить иконку окна приложения"""
        try:
            if TRAY_AVAILABLE:
                icon_image = self.create_app_icon()
                # Конвертируем PIL Image в PhotoImage для tkinter
                photo = ImageTk.PhotoImage(icon_image)
                # Устанавливаем иконку (True означает использовать для всех окон)
                self.root.iconphoto(True, photo)
                # Сохраняем ссылку, чтобы изображение не было удалено сборщиком мусора
                self.root.icon_image = photo
        except Exception:
            # Игнорируем ошибки установки иконки
            pass

    def create_tray_menu(self):
        """Создать меню трея с учетом текущего состояния HDR"""
        menu_items = [
            pystray.MenuItem(self.get_text("open"), self.show_window, default=True),
            pystray.Menu.SEPARATOR,
        ]

        # Добавляем режимы в зависимости от состояния HDR
        if self.current_hdr_state:
            # HDR режимы
            hdr_modes = self.all_modes["hdr"]
            for mode in hdr_modes:
                translated_name = get_mode_translation(mode, self.language)

                # Создаем функцию-обертку для каждого режима
                def make_mode_handler(m):
                    def handler(icon, item):
                        self.tray_set_mode(m)

                    return handler

                menu_items.append(
                    pystray.MenuItem(
                        f"{self.get_text('mode_label')} {translated_name}",
                        make_mode_handler(mode),
                    )
                )
        else:
            # SDR режимы
            sdr_modes = self.all_modes["sdr"]
            for mode in sdr_modes:
                translated_name = get_mode_translation(mode, self.language)

                # Создаем функцию-обертку для каждого режима
                def make_mode_handler(m):
                    def handler(icon, item):
                        self.tray_set_mode(m)

                    return handler

                menu_items.append(
                    pystray.MenuItem(
                        f"{self.get_text('mode_label')} {translated_name}",
                        make_mode_handler(mode),
                    )
                )

        menu_items.extend(
            [
                pystray.Menu.SEPARATOR,
                pystray.MenuItem(self.get_text("exit"), self.quit_application),
            ]
        )

        return pystray.Menu(*menu_items)

    def update_tray_menu(self):
        """Обновить меню трея"""
        if not TRAY_AVAILABLE or not self.tray_icon:
            return

        # Обновляем меню
        self.tray_icon.menu = self.create_tray_menu()

    def update_tray_icon(self, hdr_mode=False):
        """Обновить иконку трея в зависимости от режима HDR"""
        if not TRAY_AVAILABLE or not self.tray_icon:
            return

        # Создаем новую иконку с учетом HDR режима
        new_icon = self.create_tray_icon(hdr_mode)
        # Обновляем иконку
        self.tray_icon.icon = new_icon

    def start_tray(self):
        """Запустить системный трей"""
        if not TRAY_AVAILABLE:
            return

        def tray_worker():
            image = self.create_tray_icon()
            menu = self.create_tray_menu()
            self.tray_icon = pystray.Icon(
                "LG Monitor", image, "LG Monitor Mode Switcher", menu
            )
            self.tray_icon.run()

        self.tray_thread = threading.Thread(target=tray_worker, daemon=True)
        self.tray_thread.start()

    def show_window(self, icon=None, item=None):
        """Показать окно приложения"""
        self.root.after(0, self._show_window)

    def _show_window(self):
        """Показать окно (вызывается из главного потока)"""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def on_closing(self):
        """Обработка закрытия окна - сворачивание в трей или выход"""
        if self.close_to_tray and TRAY_AVAILABLE and self.tray_icon:
            self.root.withdraw()  # Скрываем окно в трей
        else:
            self.quit_application()  # Полный выход

    def setup_styles(self):
        """Настроить стили интерфейса"""
        style = ttk.Style()

        # Светлая тема
        bg_color = "#f0f0f0"
        fg_color = "#000000"
        button_bg = "#e0e0e0"
        entry_bg = "#ffffff"

        self.root.configure(bg=bg_color)

        # Используем clam для единообразия
        style.theme_use("clam")

        # Frame
        style.configure("TFrame", background=bg_color)
        style.configure("TLabelframe", background=bg_color, foreground=fg_color)
        style.configure("TLabelframe.Label", background=bg_color, foreground=fg_color)

        # Label
        style.configure("TLabel", background=bg_color, foreground=fg_color)

        # Button
        style.configure(
            "TButton",
            background=button_bg,
            foreground=fg_color,
            borderwidth=1,
            relief="raised",
        )
        style.map("TButton", background=[("active", "#d0d0d0")])

        # Checkbutton
        style.configure("TCheckbutton", background=bg_color, foreground=fg_color)

        # Combobox
        style.configure(
            "TCombobox",
            fieldbackground=entry_bg,
            background=button_bg,
            foreground=fg_color,
            arrowcolor=fg_color,
            selectbackground=entry_bg,  # Убираем выделение - цвет фона = цвет выделения
            selectforeground=fg_color,  # Цвет текста при выделении = обычный цвет
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", entry_bg)],
            selectbackground=[("readonly", entry_bg)],  # Выделение = фон
            selectforeground=[
                ("readonly", fg_color)
            ],  # Текст выделения = обычный текст
            foreground=[("readonly", fg_color), ("!readonly", fg_color)],
        )

        # Scale (ползунки)
        style.configure(
            "TScale",
            background=bg_color,
            troughcolor=entry_bg,
            borderwidth=1,
            relief="sunken",
        )

    def quit_application(self, icon=None, item=None):
        """Полный выход из приложения"""
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.after(0, self.root.quit)
        self.root.after(0, self.root.destroy)

    def tray_set_mode(self, mode):
        """Установка режима из трея"""
        if not self.connected:
            self.show_window()
            messagebox.showwarning(
                self.get_text("ready"), self.get_text("connect_first")
            )
            return

        # mode - это оригинальное имя режима, нужно перевести для отображения
        translated_mode = get_mode_translation(mode, self.language)
        self.mode_var.set(translated_mode)
        self.set_mode()


# ============================================================================
# КОНСОЛЬНАЯ ВЕРСИЯ
# ============================================================================


async def console_version():
    controller = LGMonitorController()

    print("=== Поиск мониторов ===")
    monitors, monitors_mac = discover_lg_monitors(timeout=1)

    if not monitors:
        print("Мониторы не найдены")
        return

    controller.ip = monitors[0]

    print("\n=== Подключение ===")
    if not await controller.connect():
        return

    print("\n⚠ Подтвердите подключение на мониторе (если появился запрос)")
    await asyncio.sleep(3)

    try:
        # Пример использования - установка режима
        print("\n=== Установка режима ===")
        await controller.set_picture_mode("game")

    finally:
        await controller.disconnect()


# ============================================================================
# ПРОВЕРКА ЕДИНСТВЕННОГО ЭКЗЕМПЛЯРА
# ============================================================================

# Глобальная переменная для хранения сокета блокировки
_lock_socket = None


def is_already_running():
    """Проверить, запущен ли уже экземпляр приложения (через локальный сокет)"""
    global _lock_socket

    # Используем фиксированный порт для блокировки (в диапазоне динамических портов)
    LOCK_PORT = 54321  # Фиксированный порт для проверки единственного экземпляра

    try:
        # Пробуем подключиться к порту - если удалось, значит приложение уже запущено
        test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        test_socket.settimeout(0.1)  # Короткий таймаут
        result = test_socket.connect_ex(("127.0.0.1", LOCK_PORT))
        test_socket.close()

        if result == 0:
            # Порт занят - приложение уже запущено
            return True

        # Порт свободен - создаем сокет блокировки
        _lock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        _lock_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        _lock_socket.bind(("127.0.0.1", LOCK_PORT))
        _lock_socket.listen(1)  # Начинаем слушать (но не принимаем соединения)

        # Регистрируем функцию очистки при выходе
        import atexit

        def cleanup_lock():
            global _lock_socket
            try:
                if _lock_socket:
                    _lock_socket.close()
                    _lock_socket = None
            except:
                pass

        atexit.register(cleanup_lock)
        return False  # Это первый экземпляр
    except OSError:
        # Если не удалось привязать сокет, значит порт занят - приложение уже запущено
        if _lock_socket:
            try:
                _lock_socket.close()
            except:
                pass
            _lock_socket = None
        return True
    except Exception:
        # В случае любой другой ошибки считаем что приложение уже запущено
        if _lock_socket:
            try:
                _lock_socket.close()
            except:
                pass
            _lock_socket = None
        return True


# ============================================================================
# ЗАПУСК
# ============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--console":
        # Консольный режим
        asyncio.run(console_version())
    else:
        # GUI режим - проверяем единственный экземпляр
        if is_already_running():
            # Показываем сообщение и выходим
            root = tk.Tk()
            root.withdraw()  # Скрываем главное окно

            # Определяем язык для сообщения (пробуем загрузить из конфига)
            try:
                saved_ip, language, _, _, _, _ = load_monitor_config()
                if not language:
                    language = "en"
            except:
                language = "en"

            # Получаем переводы
            translations = UI_TRANSLATIONS.get(language, UI_TRANSLATIONS["en"])
            title = translations.get(
                "already_running", "Application is already running!"
            )
            message = translations.get(
                "already_running_msg",
                "The application is already running!\n\nPlease check the system tray.",
            )

            messagebox.showwarning(title, message)
            root.destroy()
            sys.exit(1)

        # GUI режим
        root = tk.Tk()
        app = LGMonitorGUI(root)
        root.mainloop()
