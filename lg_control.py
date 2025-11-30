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
        "title": "LG Monitor Mode Switcher",
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
        "already_running": "Application is already running!",
        "already_running_msg": "The application is already running!\n\nPlease check the system tray.",
    },
    "ru": {
        "title": "Переключатель режимов монитора LG",
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
        "already_running": "Приложение уже запущено!",
        "already_running_msg": "Приложение уже запущено!\n\nПроверьте системный трей.",
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
        "normal": "Нормальный",
        "vivid": "Яркий",
        "cinema": "Кино",
        "sports": "Спорт",
        "eco": "Автоматическое энергосбережение",
        "filmMaker": "Кинематографист",
        "expert1": "Эксперт 1",
        "expert2": "Эксперт 2",
        "hdrPersonalized": "HDR Персонализированное изображение",
        "hdrGame": "HDR Оптимизация игр",
        "hdrStandard": "HDR Стандартный",
        "hdrCinema": "HDR Кино",
        "hdrCinemaBright": "HDR Кинотеатр",
        "hdrVivid": "HDR Яркий",
        "hdrEco": "HDR Автоматическое энергосбережение",
        "hdrFilmMaker": "HDR Кинематографист",
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


def save_monitor_config(
    ip: str,
    language: str = "en",
    start_minimized: bool = False,
    mac: Optional[str] = None,
):
    """Сохранить IP адрес монитора, MAC адрес, язык и настройку запуска в конфигурационный файл"""
    try:
        config = {
            "last_monitor_ip": ip,
            "language": language,
            "start_minimized": start_minimized,
        }
        if mac:
            config["last_monitor_mac"] = mac
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        print(f"Ошибка сохранения конфигурации: {e}")


def load_monitor_config() -> tuple[Optional[str], str, bool, Optional[str]]:
    """Загрузить IP адрес, MAC адрес последнего подключенного монитора, язык и настройку запуска"""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
                ip = config.get("last_monitor_ip")
                language = config.get("language", "en")
                start_minimized = config.get("start_minimized", False)
                mac = config.get("last_monitor_mac")
                return ip, language, start_minimized, mac
    except Exception as e:
        print(f"Ошибка загрузки конфигурации: {e}")
    return None, "en", False, None


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

    async def _on_picture_settings_change(self, settings):
        """Обработчик изменений настроек изображения"""
        if settings and "pictureMode" in settings and self.picture_mode_callback:
            picture_mode = settings["pictureMode"]
            # Вызываем callback (может быть async или sync)
            if asyncio.iscoroutinefunction(self.picture_mode_callback):
                await self.picture_mode_callback(picture_mode)
            else:
                self.picture_mode_callback(picture_mode)

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
        self.root.geometry("500x450")
        self.root.resizable(False, False)  # Запрещаем изменение размеров окна

        self.controller = LGMonitorController()
        self.controller._gui_mode = (
            True  # Флаг для GUI режима (не открываем окно настроек Windows)
        )
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.connected = False
        self.tray_icon = None
        self.tray_thread = None
        self.current_hdr_state = None  # Текущее состояние HDR на мониторе
        self.connect_button = None  # Кнопка подключения/обновления
        self.hdr_monitor_task = None  # Задача мониторинга HDR
        # Загружаем сохраненный язык и настройку запуска, по умолчанию английский
        _, self.language, self.start_minimized, _ = load_monitor_config()
        if not self.language:
            self.language = "en"  # Язык интерфейса (en/ru)

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

        # Заголовок
        self.title_label = ttk.Label(
            self.root, text=self.get_text("title"), font=("Arial", 16, "bold")
        )
        self.title_label.pack(pady=10)

        # Переключатель языка
        lang_frame = ttk.Frame(self.root)
        lang_frame.pack(pady=5)
        self.language_label = ttk.Label(
            lang_frame, text=self.get_text("language_label")
        )
        self.language_label.pack(side=tk.LEFT, padx=5)
        self.language_var = tk.StringVar(value=self.language)
        lang_combo = ttk.Combobox(
            lang_frame,
            textvariable=self.language_var,
            values=["en", "ru"],
            state="readonly",
            width=10,
        )
        lang_combo.pack(side=tk.LEFT, padx=5)
        lang_combo.bind("<<ComboboxSelected>>", self.on_language_change)

        # Чекбокс автозапуска (только для Windows)
        if platform.system() == "Windows":
            self.autostart_var = tk.BooleanVar(value=self.is_autostart_enabled())
            self.autostart_check = ttk.Checkbutton(
                lang_frame,
                text=self.get_text("autostart"),
                variable=self.autostart_var,
                command=self.toggle_autostart,
            )
            self.autostart_check.pack(side=tk.LEFT, padx=10)

        # Чекбокс "запускать свернутой"
        self.start_minimized_var = tk.BooleanVar(value=self.start_minimized)
        self.start_minimized_check = ttk.Checkbutton(
            lang_frame,
            text=self.get_text("start_minimized"),
            variable=self.start_minimized_var,
            command=self.toggle_start_minimized,
        )
        self.start_minimized_check.pack(side=tk.LEFT, padx=10)

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
            self.root, text=self.get_text("ready"), relief=tk.SUNKEN
        )
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X, pady=5)

    def update_ui_texts(self):
        """Обновить все тексты интерфейса при смене языка"""
        self.root.title(self.get_text("title"))
        self.title_label.config(text=self.get_text("title"))
        self.language_label.config(text=self.get_text("language_label"))
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
        if not self.connected:
            self.status_label.config(text=self.get_text("ready"))

    def on_language_change(self, event=None):
        """Обработчик изменения языка"""
        new_language = self.language_var.get()
        if new_language != self.language:
            self.language = new_language
            # Сохраняем язык в конфиг
            if self.controller.ip:
                # Получаем MAC адрес для текущего IP, если он есть
                saved_ip, _, _, saved_mac = load_monitor_config()
                save_monitor_config(
                    self.controller.ip, self.language, self.start_minimized, saved_mac
                )
            else:
                save_monitor_config("", self.language, self.start_minimized, None)
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
        # Сохраняем в конфиг
        if self.controller.ip:
            # Получаем MAC адрес для текущего IP, если он есть
            saved_ip, _, _, saved_mac = load_monitor_config()
            save_monitor_config(
                self.controller.ip, self.language, self.start_minimized, saved_mac
            )
        else:
            save_monitor_config("", self.language, self.start_minimized, None)

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
            saved_ip, _, _, saved_mac = load_monitor_config()
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
            saved_ip, _, _, saved_mac = load_monitor_config()
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
                    # Устанавливаем переведенное значение
                    translated_mode = get_mode_translation(current_mode, self.language)

                    def set_mode_value(value):
                        self.mode_var.set(value)

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

        # Обновляем меню трея
        if TRAY_AVAILABLE and self.tray_icon:
            self.update_tray_menu()

    def load_and_connect_saved_monitor(self):
        """Загрузить сохраненный IP и попытаться подключиться"""
        saved_ip, _, _, saved_mac = load_monitor_config()
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

    def stop_hdr_monitoring(self):
        """Остановить мониторинг изменений HDR"""
        # Задача остановится автоматически при проверке self.connected
        self.hdr_monitor_task = None

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
            hdr_enabled = original_mode.startswith("hdr")
            if self.current_hdr_state != hdr_enabled:
                self.current_hdr_state = hdr_enabled
                self._update_modes_ui(hdr_enabled)
        else:
            self.status_label.config(text=f"✗ {self.get_text('mode_error')}")

    def create_app_icon(self):
        """Создать иконку приложения - круглую с белым фоном и красным кольцом"""
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

        return image

    def create_tray_icon(self):
        """Создать иконку для системного трея - использует ту же иконку что и окно"""
        return self.create_app_icon()

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
        """Обработка закрытия окна - сворачивание в трей"""
        if TRAY_AVAILABLE and self.tray_icon:
            self.root.withdraw()  # Скрываем окно
        else:
            self.quit_application()

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
                saved_ip, language, _, _ = load_monitor_config()
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
