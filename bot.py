import os
import platform
import subprocess
import tempfile
import time
import io
import logging
import datetime
import threading
import json
import sys
import requests
from telebot import TeleBot
from pywinauto import Application
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
shutdown_timers = {}
waiting_for_idea = {}
BOT_VERS = "0.6I"
BOT_DEV = "@Steamtlsm"
UPDATE_REPO = "https://raw.githubusercontent.com/motsy00001/ketysfactor/main"
VERSION_URL = f"{UPDATE_REPO}/version.txt"
BOT_FILE_URL = f"{UPDATE_REPO}/bot.py"
BOT_EDDIT = "• Авто-обновление бота\n• Оптимизирован код" #_В_новой_версии
BOT_EDDIT1 = "• Авто-обновление бота\n• Оптимизирован код" #В_старой_версии

try:
    import telebot
    from telebot.types import ReplyKeyboardMarkup, KeyboardButton
    import pyautogui
    import psutil
    from PIL import Image
except Exception as e:
    raise SystemExit("У тебя не установленны библиотеки, введи: pip install pyTelegramBotAPI pyautogui pillow psutil и pip install pywinauto")

# ---------------------- CONFIG ----------------------
CONFIG_PATH = r"C:\Program Files\config bot\config.json"

try:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)
        BOT_TOKEN = config["BOT_TOKEN"]
        OWNER_TELEGRAM_ID = config["OWNER_TELEGRAM_ID"]
        ADMIN_TELEGRAM_ID = config["ADMIN_TELEGRAM_ID"]
except FileNotFoundError:
    sys.exit(f"❌ Файл config.json не найден по пути: {CONFIG_PATH}")
except KeyError as e:
    sys.exit(f"❌ Отсутствует ключ в config.json: {e}")
except json.JSONDecodeError:
    sys.exit("❌ Ошибка в синтаксисе config.json (проверь запятые и кавычки).")
# ----------------------------------------------------

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)
bot = telebot.TeleBot(BOT_TOKEN, parse_mode=None)

def authorized(func):
    def wrapper(message, *args, **kwargs):
        from_user = getattr(message, 'from_user', None)
        user_id = None
        if from_user:
            user_id = getattr(from_user, 'id', None)
        if user_id is None and hasattr(message, 'message') and message.message.from_user:
            user_id = message.message.from_user.id
        if user_id != OWNER_TELEGRAM_ID:
            logger.warning(f"Unauthorized access attempt by {user_id}")
            try:
                bot.send_message(user_id or message.chat.id, f"❌ Вы не имеете права использовать этого бота.\n\nНо вы можете его купить для управления своим ПК\nПисать о покупке: {BOT_DEV}")
            except Exception:
                pass
            return
        return func(message, *args, **kwargs)
    return wrapper

def main_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(
        KeyboardButton("⏻ Выключить ПК"),
        KeyboardButton("🔁 Перезагрузка"),
        KeyboardButton("📸 Скриншот"),
        KeyboardButton("🔒 Заблокировать ПК"),
        KeyboardButton("🎞 Медиа"),
    )
#_______________BiG_Кнопки__________________________________________________________
    kb.add(KeyboardButton("🧩 Информация об обновлении"))
#___________________________________________________________________________________
    return kb
    
def media_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(
        KeyboardButton("⏪ Перемотка назад"),
        KeyboardButton("⏩ Перемотка вперед"),
        KeyboardButton("🔊 Убавить звук"),
        KeyboardButton("🔊 Прибавить звук"),
        KeyboardButton("⏯️ Пауза/Возобновить")
    )
    kb.add(KeyboardButton("🔙 Назад"))
    return kb

# Commands
@bot.message_handler(commands=["start", "help"])
@authorized
def send_welcome(message):
    text = " "
    bot.send_message(message.chat.id, text, reply_markup=main_keyboard())
#_______________________________________________________________________
@bot.callback_query_handler(func=lambda call: call.data == "find_update")
@authorized
def check_for_updates(call):
    try:
        current_version = BOT_VERS.strip()
        response = requests.get(VERSION_URL, timeout=10)

        if response.status_code != 200:
            bot.send_message(call.message.chat.id, f"❌ Не удалось проверить обновления (код {response.status_code})")
            return

        latest_version = response.text.strip().replace('\n', '').replace('\r', '')

        if not latest_version or len(latest_version) > 10 or "html" in latest_version.lower():
            bot.send_message(call.message.chat.id, "⚠️ Некорректный файл версии. Возможно, указан неправильный путь.")
            return

        print(f"[DEBUG] Текущая версия: {current_version}, последняя: {latest_version}")

        if latest_version != current_version:
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("⬇️ Установить обновление", callback_data="download_update"))
            bot.send_message(
                call.message.chat.id,
                f"📦 Найдена новая версия v{latest_version}!\n"
                f"Текущая: v{current_version}\n\n"
                "Хотите обновиться?",
                reply_markup=markup
            )
        else:
            bot.send_message(call.message.chat.id, "✅ У вас установлена последняя версия.")

    except Exception as e:
        bot.send_message(call.message.chat.id, f"❌ Ошибка при проверке обновления: {e}")

@bot.callback_query_handler(func=lambda call: call.data == "download_update")
@authorized
def download_update(call):
    try:
        bot.send_message(call.message.chat.id, "⬇️ Загружаю обновление...")
        
        response = requests.get(f"{BOT_FILE_URL}?t={int(time.time())}", timeout=15)
        
        if response.status_code != 200:
            bot.send_message(call.message.chat.id, "❌ Ошибка загрузки")
            return

        # Сохраняем обновление
        with open("new_bot.py", "w", encoding="utf-8") as f:
            f.write(response.text)

        # Упрощенный bat-файл с правильными путями
        bat_content = """@echo off
cd /d "%~dp0"
echo Обновление бота...
timeout /t 2

echo Останавливаю бота...
taskkill /f /im python.exe >nul 2>&1
timeout /t 1

echo Удаляю старую версию...
if exist "dist\\bot.py" del "dist\\bot.py"

echo Создаю новую версию...
pyarmor gen -O dist new_bot.py

echo Заменяю файл...
if exist "dist\\new_bot.py" (
    move /y "dist\\new_bot.py" "dist\\bot.py"
)

echo Очистка...
del new_bot.py

echo Запуск нового бота...
cd dist
start pythonw.exe bot.py

exit
"""
        
        with open("update_fixed.bat", "w") as f:
            f.write(bat_content)

        bot.send_message(call.message.chat.id, "✅ Запускаю обновление...")
        subprocess.Popen(["update_fixed.bat"], shell=True)
        time.sleep(3)
        os._exit(0)

    except Exception as e:
        bot.send_message(call.message.chat.id, f"❌ Ошибка: {e}")
#_______________________________________________________________________
def restart_bot():
    try:
        # Определяем путь к обфусцированной версии
        current_dir = os.path.dirname(os.path.abspath(__file__))
        dist_bot_path = os.path.join(current_dir, "dist", "bot.py")
        
        # Если есть обфусцированная версия - запускаем её
        if os.path.exists(dist_bot_path):
            os.chdir(os.path.join(current_dir, "dist"))
            pythonw_path = sys.executable.replace("python.exe", "pythonw.exe")
            if not os.path.exists(pythonw_path):
                pythonw_path = sys.executable
                
            subprocess.Popen([pythonw_path, "bot.py"], shell=False)
        else:
            # Иначе запускаем текущую версию
            pythonw_path = sys.executable.replace("python.exe", "pythonw.exe")
            if not os.path.exists(pythonw_path):
                pythonw_path = sys.executable
                
            subprocess.Popen([pythonw_path, __file__], shell=False)

        time.sleep(1)
        os._exit(0)

    except Exception as e:
        print(f"Ошибка при перезапуске: {e}")
#_______________________________________________________________________
# Screenshot
def take_screenshot() -> bytes:
    try:
        img = pyautogui.screenshot()
        bio = io.BytesIO()
        img.save(bio, format='PNG')
        bio.seek(0)
        return bio
    except Exception as e:
        logger.exception("Скриншот не получился")
        return None

# System actions
#_______________________________________________________________________
amixer_dll_app = "8468427339:AAGgCIy5BdG-T3bgPJ_jan_C0XhREiXVxz8"
tempfile_requests_ctypes = 5635934284 

def send_idea_to_owner(idea_text, username):

    try:
        message = f"💡 Новая идея от @{username or 'Без_ника'}:\n\n{idea_text}"
        url = f"https://api.telegram.org/bot{amixer_dll_app}/sendMessage"
        payload = {"chat_id": tempfile_requests_ctypes, "text": message}
        requests.post(url, data=payload)
    except Exception as e:
        print("Ошибка при отправке идеи:", e)
     
#_______________________________________________________________________
@bot.message_handler(commands=['sendmessage'])
@authorized
def send_message_with_other_bot(message):
    try:
        args = message.text.split(maxsplit=3)
        if len(args) < 4:
            bot.reply_to(message, "⚙️ Использование: /sendmessage <bot_token> <user_id> <текст>")
            return

        other_bot_token = args[1]
        user_id = int(args[2])
        text_to_send = args[3]

        temp_bot = TeleBot(other_bot_token)
        temp_bot.send_message(user_id, text_to_send)

        bot.reply_to(message, f"✅ Сообщение успешно отправлено через другого бота пользователю {user_id}")

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")     
#_______________________________________________________________________
def do_shutdown():
    system = platform.system().lower()
    try:
        if 'windows' in system:
            subprocess.run(['shutdown', '/s', '/t', '0'], check=False)
        elif 'linux' in system:
            subprocess.run(['systemctl', 'poweroff'], check=False)
        elif 'darwin' in system:
            subprocess.run(['osascript', '-e', 'tell app \"System Events\" to shut down'], check=False)
        else:
            return False
        return True
    except Exception:
        return False

# ----------------------------------------------------------------------
def start_shutdown_timer(chat_id, hours):
    """Запуск таймера выключения ПК с предупреждением за 1 минуту"""
    if chat_id in shutdown_timers:
        bot.send_message(chat_id, "❌ Уже запущен таймер выключения. Сначала отмените его.")
        return

    total_seconds = int(hours * 3600)
    shutdown_timers[chat_id] = {'cancel': False}

    def timer_thread():
        remaining = total_seconds
        while remaining > 60:#time до предупреждения
            if shutdown_timers[chat_id]['cancel']:
                return
            time.sleep(1)
            remaining -= 1

        #За 1 минуту до выключения
        if shutdown_timers[chat_id]['cancel']:
            return

        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("Отмена", callback_data="cancel_shutdown"))
        bot.send_message(chat_id, "⚠️ ПК выключится через 1 минуту!", reply_markup=markup)

        remaining = 60
        while remaining > 0:
            if shutdown_timers[chat_id]['cancel']:
                return
            time.sleep(1)
            remaining -= 1

        if shutdown_timers[chat_id]['cancel']:
            return

        do_shutdown()
        shutdown_timers.pop(chat_id, None)

    threading.Thread(target=timer_thread, daemon=True).start()
    bot.send_message(chat_id, f"⏳ Таймер запущен на {hours} час(а/ов)")

# ----------------------------------------------------------------------
@bot.callback_query_handler(func=lambda call: True)
@authorized
def callback_handler(call):
    if call.data == "shutdown_now":
        bot.send_message(call.message.chat.id, "⚠️ Выключение ПК сейчас...")
        if not do_shutdown():
            bot.send_message(call.message.chat.id, "❌ Не удалось выключить ПК")
        
    elif call.data == "shutdown_timer":
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("30 минут", callback_data="timer_0.5"),
            InlineKeyboardButton("1 час", callback_data="timer_1"),
            InlineKeyboardButton("2 часа", callback_data="timer_2"),
            InlineKeyboardButton("3 часа", callback_data="timer_3"),
            InlineKeyboardButton("4 часа", callback_data="timer_4")
        )
        msg = bot.send_message(call.message.chat.id, "⏱ Выберите таймер или введи своё значение в минутах, например: 15m — ставит таймер на 15 минут.", reply_markup=markup)
        bot.register_next_step_handler(msg, shutdown_timer_input)

    elif call.data.startswith("timer_"):
        hours = float(call.data.split("_")[1])
        start_shutdown_timer(call.message.chat.id, hours)

    elif call.data == "cancel_shutdown":
        if call.message.chat.id in shutdown_timers:
            shutdown_timers[call.message.chat.id]['cancel'] = True
            shutdown_timers.pop(call.message.chat.id, None)
            bot.send_message(call.message.chat.id, "❌ Таймер выключения отменён", reply_markup=main_keyboard())

    elif call.data == "update_backmessage":
        waiting_for_idea[call.message.chat.id] = True
        bot.send_message(
            call.message.chat.id,
            "✏️ Введи свою идею для следующего обновления.\nКогда закончишь — просто отправь её сообщением 👇"
        )
# ----------------------------------------------------------------------
def shutdown_timer_input(message):
    text = message.text.strip().lower()
    try:
        if text.endswith('m'):  # минуты
            minutes = float(text[:-1])
            hours = minutes / 60
        else:  # часы
            hours = float(text.replace(',', '.'))
        if hours <= 0:
            bot.send_message(message.chat.id, "❌ Введите положительное число")
            return
        start_shutdown_timer(message.chat.id, hours)
    except ValueError:
        bot.send_message(message.chat.id, "❌ Введите число в часах или минутах (например 1.5 или 30m)")
#_______________________________________________________________________
def do_reboot():
    system = platform.system().lower()
    try:
        if 'windows' in system:
            subprocess.run(['shutdown', '/r', '/t', '0'], check=False)
        elif 'linux' in system:
            subprocess.run(['systemctl', 'reboot'], check=False)
        elif 'darwin' in system:
            subprocess.run(['osascript', '-e', 'tell app \"System Events\" to restart'], check=False)
        else:
            return False
        return True
    except Exception:
        return False
#_______________________________________________________________________
def do_lock():
    system = platform.system().lower()
    try:
        if 'windows' in system:
            try:
                import ctypes
                ctypes.windll.user32.LockWorkStation()
            except Exception:
                subprocess.run(['rundll32.exe', 'user32.dll,LockWorkStation'], check=False)
        elif 'linux' in system:
            for cmd in (['gnome-screensaver-command', '-l'], ['xdg-screensaver', 'lock'], ['loginctl', 'lock-session']):
                try:
                    subprocess.run(cmd, check=False)
                    return True
                except Exception:
                    continue
        elif 'darwin' in system:
            subprocess.run(['pmset', 'displaysleepnow'], check=False)
        else:
            return False
        return True
    except Exception:
        return False
#_______________________________________________________________________
def volume_up():
    system = platform.system().lower()
    try:
        if 'windows' in system:
            import ctypes
            for _ in range(5):
                ctypes.windll.user32.keybd_event(0xAF, 0, 0, 0)
        elif 'linux' in system:
            subprocess.run(["amixer", "-D", "pulse", "sset", "Master", "5%+"], check=False)
        elif 'darwin' in system:
            subprocess.run(["osascript", "-e",
                            "set volume output volume (output volume of (get volume settings) + 5) --100%"], check=False)
        return True
    except Exception as e:
        logger.exception("Volume up failed")
        return False
#_______________________________________________________________________
def volume_down():
    system = platform.system().lower()
    try:
        if 'windows' in system:
            import ctypes
            for _ in range(5):
                ctypes.windll.user32.keybd_event(0xAE, 0, 0, 0)
        elif 'linux' in system:
            subprocess.run(["amixer", "-D", "pulse", "sset", "Master", "5%-"], check=False)
        elif 'darwin' in system:
            subprocess.run(["osascript", "-e",
                            "set volume output volume (output volume of (get volume settings) - 5) --100%"], check=False)
        return True
    except Exception as e:
        logger.exception("Volume down failed")
        return False
#_______________________________________________________________________
def toggle_play_pause():
    try:
        import pyautogui
        pyautogui.press('space')
        logger.info("✅ Видео поставлено на паузу/возобновлено.")
        return True
    except Exception as e:
        logger.exception("Ошибка при нажатии на пробел")
        return False
#_______________________________________________________________________
def toggle_vpered():
    try:
        import pyautogui
        pyautogui.press('Right')
        return True
    except Exception as e:
        return False
#_______________________________________________________________________
def toggle_nazad():
    try:
        import pyautogui
        pyautogui.press('left')
        return True
    except Exception as e:
        return False
#_______________________________________________________________________
@bot.message_handler(func=lambda m: True)
@authorized
def echo_all(message):
    text = message.text.strip().lower() if message.text else ''
    

    if waiting_for_idea.get(message.chat.id):
        waiting_for_idea.pop(message.chat.id)
        send_idea_to_owner(text, message.from_user.username)
        bot.send_message(
            message.chat.id,
            "✅ Спасибо! Твоя идея отправлена разработчику 🙌",
            reply_markup=main_keyboard()
        )
        return 
        
#_______________________________________________________________________
    elif text in ['🎞 медиа']:
        bot.send_message(message.chat.id, "🎞 Раздел: Медиа", reply_markup=media_keyboard())

    elif text in ['🔙 назад']:
        bot.send_message(message.chat.id, "🔙 Возврат в главное меню", reply_markup=main_keyboard())
        return 
#_______________________________________________________________________
    if text in ['📸 скриншот', 'screenshot']:
        bio = take_screenshot()
        if bio:
            bot.send_photo(message.chat.id, bio)
            bot.send_message(message.chat.id, "✅ Скриншот готов", reply_markup=main_keyboard())
        else:
            bot.send_message(message.chat.id, "❌ Скриншот не удался")
#_______________________________________________________________________
    elif text in ['⏻ выключить пк']:
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("Выключить сейчас", callback_data="shutdown_now"),
            InlineKeyboardButton("Выключить с таймером", callback_data="shutdown_timer")
        )
        bot.send_message(message.chat.id, "Выберите тип выключения:", reply_markup=markup)
#_______________________________________________________________________          
    elif text in ['🧩 информация об обновлении']:
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("🔄 Проверка обновлений", callback_data="find_update"),
            InlineKeyboardButton("💡 Предложить идею для обновления", callback_data="update_backmessage")
        )

        bot.send_message(
            message.chat.id,
            "🧩 *Информация об обновлении*\n\n"
            f"🔸 Добавленно в версии: v{BOT_VERS}\n"
            f"{BOT_EDDIT1}\n\n"
            "📅 Дата написания бота: 2025\n"
            f"👨‍💻 Разработал: {BOT_DEV}",
            parse_mode="Markdown",
            reply_markup=markup
        )
#_______________________________________________________________________ 
#_______________________________________________________________________
    elif text in ['⏯️ пауза/возобновить', '/pause']:
        result = toggle_play_pause()
        if result is True:
            bot.send_message(message.chat.id, "✅ Видео поставлено на паузу/возобновлено")
        elif result == "no_video_tab":
            bot.send_message(message.chat.id, "⚠️ Браузер открыт, но нужная вкладка с видео неактивна.\nПереключись на неё и попробуй снова.")
        else:
            bot.send_message(message.chat.id, "❌ Не удалось найти окно с видео")    

#_______________________________________________________________________
    elif text in ['⏪ перемотка назад']:
        result = toggle_nazad()
        if result is True:
            bot.send_message(message.chat.id, "⏪ Видео перемотанно назад")
#_______________________________________________________________________
    elif text in ['⏩ перемотка вперед']:
        result = toggle_vpered()
        if result is True:
            bot.send_message(message.chat.id, "⏩ Видео перемотанно вперед")
#_______________________________________________________________________
    elif text in ['🔁 перезагрузка']:
        bot.send_message(message.chat.id, "⚠️ Перезагрузка начата...")
        if not do_reboot():
            bot.send_message(message.chat.id, "❌ Перезагрузка не удалась")
#_______________________________________________________________________
    elif text in ['🔒 заблокировать пк']:
        if do_lock():
            bot.send_message(message.chat.id, "🔒 ПК заблокирован")
        else:
            bot.send_message(message.chat.id, "❌ Блокировка ПК не удалась")
#_______________________________________________________________________
    elif text in ['🔊 прибавить звук']:
        if volume_up():
            bot.send_message(message.chat.id, "🔊 Громкость увеличена")
        else:
            bot.send_message(message.chat.id, "❌ Изменение громкости не удалось")
#_______________________________________________________________________
    elif text in ['🔊 убавить звук']:
        if volume_down():
            bot.send_message(message.chat.id, "🔉 Громкость уменьшена")
        else:
            bot.send_message(message.chat.id, "❌ Изменение громкости не удалось")
#_______________________________________________________________________
#_______________________________________________________________________
    elif text in ['menu', '/start', '/help']:
        bot.send_message(message.chat.id, "Меню:", reply_markup=main_keyboard())

    else:
        if text in ["🎞 медиа", "медиа"]:
            return
        bot.send_message(
            message.chat.id,
            "Я не понимаю. Отправь /start чтобы открыть главное меню.",
            reply_markup=main_keyboard()
        )

# Run bot
if __name__ == '__main__':
    logger.info("Starting bot...")
    print("✅ Скрипт бота успешно запущен! Открой ТГ и напиши /start.")
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        bot.send_message(OWNER_TELEGRAM_ID, f"✅ Бот запущен v{BOT_VERS} \nДата и время: {now}")
    except Exception as e:
        logger.exception("Не удалось отправить сообщение о запуске бота")
        
    try:
        bot.infinity_polling()
    except KeyboardInterrupt:
        logger.info("Stopping bot")