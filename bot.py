import telebot
import requests
import speech_recognition as sr
from pydub import AudioSegment
import sqlite3
import os

API_TOKEN = '' #токен
bot = telebot.TeleBot(API_TOKEN)

# Создаем или подключаемся к базе данных
conn = sqlite3.connect('user_filters.db', check_same_thread=False)
cursor = conn.cursor()

# Создаем таблицы, если они не существуют
cursor.execute('''
CREATE TABLE IF NOT EXISTS whitelist (
    chat_id INTEGER,
    user_id INTEGER,
    username TEXT,
    PRIMARY KEY (chat_id, user_id)
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS blacklist (
    chat_id INTEGER,
    user_id INTEGER,
    username TEXT,
    PRIMARY KEY (chat_id, user_id)
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS chat_settings (
    chat_id INTEGER PRIMARY KEY,
    mode TEXT DEFAULT 'blacklist'
)
''')
conn.commit()
conn.close()

# Функции для работы с базой данных
def add_to_whitelist(chat_id, user_id, username):
    try:
        conn = sqlite3.connect('user_filters.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO whitelist (chat_id, user_id, username) VALUES (?, ?, ?)', (chat_id, user_id, username))
        conn.commit()
        conn.close()
    except Exception as e:
        print('52 '+str(e))

def remove_from_whitelist(chat_id, user_id, username):
    try:
        conn = sqlite3.connect('user_filters.db', check_same_thread=False)
        cursor = conn.cursor()

        cursor.execute('DELETE FROM whitelist WHERE chat_id = ? AND user_id = ? AND username = ?', (chat_id, user_id, username))
        conn.commit()
        conn.close()
    except Exception as e:
        print('63 '+str(e))

def add_to_blacklist(chat_id, user_id, username):
    try:
        conn = sqlite3.connect('user_filters.db', check_same_thread=False)
        cursor = conn.cursor()

        cursor.execute('INSERT OR IGNORE INTO blacklist (chat_id, user_id, username) VALUES (?, ?, ?)', (chat_id, user_id, username))
        conn.commit()
        conn.close()
    except Exception as e:
        print('74 '+str(e))

def remove_from_blacklist(chat_id, user_id, username):
    try:
        conn = sqlite3.connect('user_filters.db', check_same_thread=False)
        cursor = conn.cursor()

        cursor.execute('DELETE FROM blacklist WHERE chat_id = ? AND user_id = ? AND username = ?', (chat_id, user_id, username))
        conn.commit()
        conn.close()
    except Exception as e:
        print('85 '+str(e))

def show_whitelist(chat_id):
    try:
        conn = sqlite3.connect('user_filters.db', check_same_thread=False)
        cursor = conn.cursor()

        cursor.execute('SELECT username FROM whitelist WHERE chat_id = ?', (chat_id,))
        a = cursor.fetchall()
        conn.close()
        return a
    except Exception as e:
        print('97 '+str(e))

def show_blacklist(chat_id):
    try:
        conn = sqlite3.connect('user_filters.db', check_same_thread=False)
        cursor = conn.cursor()

        cursor.execute('SELECT username FROM blacklist WHERE chat_id = ?', (chat_id,))
        a = cursor.fetchall()
        conn.close()
        return a
    except Exception as e:
        print('109 '+str(e))


def set_chat_mode(chat_id, mode):
    try:
        conn = sqlite3.connect('user_filters.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute('INSERT OR REPLACE INTO chat_settings (chat_id, mode) VALUES (?, ?)', (chat_id, mode))
        conn.commit()
        conn.close()
    except Exception as e:
        print('120 '+str(e))

def get_chat_mode(chat_id):
    try:
        conn = sqlite3.connect('user_filters.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute('SELECT mode FROM chat_settings WHERE chat_id = ?', (chat_id,))
        result = cursor.fetchone()
        a = result[0] if result else 'blacklist'
        conn.close()
        return a
    except Exception as e:
        print('132 '+str(e))

def is_user_in_whitelist(chat_id, user_id):
    try:
        conn = sqlite3.connect('user_filters.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM whitelist WHERE chat_id = ? AND user_id = ?', (chat_id, user_id))
        a = cursor.fetchone()
        conn.close()
        return a
    except Exception as e:
        print('143 '+str(e))

def is_user_in_blacklist(chat_id, user_id):
    try:
        conn = sqlite3.connect('user_filters.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM blacklist WHERE chat_id = ? AND user_id = ?', (chat_id, user_id))
        a = cursor.fetchone()
        conn.close()
        return a
    except Exception as e:
        print('154 '+str(e))

def get_username(user):
    try:
        conn = sqlite3.connect('user_filters.db', check_same_thread=False)
        cursor = conn.cursor()
        if user.username:
            a = f"@{user.username}"
        else:
            a = f"{user.first_name} {user.last_name}" if user.first_name or user.last_name else "Пользователь без имени"
        conn.close()
        return a
    except Exception as e:
        print('167 '+str(e))

def download_audio(file_id, is_video=False):
    try:
        # Получаем информацию о файле
        file_info = bot.get_file(file_id)

        # Формируем URL для скачивания файла
        file_url = f'https://api.telegram.org/file/bot{API_TOKEN}/{file_info.file_path}'

        # Скачиваем файл
        response = requests.get(file_url)

        # Сохраняем файл на диск
        audio_file_path = str(file_id) + 'voice_message.ogg' if not is_video else str(file_id) + 'video_message.mp4'
        with open(audio_file_path, 'wb') as f:
            f.write(response.content)

        return audio_file_path
    except Exception as e:
        print('187 '+str(e))


def recognize_speech(audio_file_path):
    try:
        # Преобразуем аудиофайл в WAV
        wav_file_path = 'voice_message.wav'
        audio = AudioSegment.from_file(audio_file_path)  # Поддерживает различные форматы
        audio.export(wav_file_path, format='wav')

        # Распознавание речи
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_file_path) as source:
            audio_data = recognizer.record(source)  # Читаем аудиофайл
            try:
                # Попробуем распознать на русском
                text = recognizer.recognize_google(audio_data, language='ru-RU')
                os.remove(audio_file_path)
                return text
            except sr.UnknownValueError:
                os.remove(audio_file_path)
                return None
            except sr.RequestError as e:
                os.remove(audio_file_path)
                return f"Ошибка сервиса распознавания: {e}"
    except Exception as e:
        print('213 '+str(e))


def is_admin(message):
    try:
        chat_member = bot.get_chat_member(message.chat.id, message.from_user.id)
        return chat_member.status in ['administrator', 'creator']
    except Exception as e:
        print('221 '+str(e))

# Обработчики команд
@bot.message_handler(commands=['whitelist'])
def handle_whitelist(message):
    try:
        if not is_admin(message):
            bot.reply_to(message, "Эта команда доступна только администраторам.")
            return
        bot.reply_to(message, "Режим белого списка активирован.")
    except Exception as e:
        print('232 '+str(e))

@bot.message_handler(commands=['blacklist'])
def handle_blacklist(message):
    try:
        if not is_admin(message):
            bot.reply_to(message, "Эта команда доступна только администраторам.")
            return
        bot.reply_to(message, "Режим черного списка активирован.")
    except Exception as e:
        print('242 '+str(e))

@bot.message_handler(commands=['whitelist_add'])
def handle_whitelist_add(message):
    try:
        if not is_admin(message):
            bot.reply_to(message, "Эта команда доступна только администраторам.")
            return
        chat_id = message.chat.id
        if message.reply_to_message:
            user_id = message.reply_to_message.from_user.id
            user = message.reply_to_message.from_user
            username = get_username(user)
            add_to_whitelist(chat_id, user_id, username)
            bot.reply_to(message, f"Пользователь {username} добавлен в белый список.")
        else:
            bot.reply_to(message, "Пожалуйста, ответьте на сообщение пользователя, которого хотите добавить.")
    except Exception as e:
        print('260 '+str(e))

@bot.message_handler(commands=['blacklist_add'])
def handle_blacklist_add(message):
    try:
        if not is_admin(message):
            bot.reply_to(message, "Эта команда доступна только администраторам.")
            return
        chat_id = message.chat.id
        if message.reply_to_message:
            user_id = message.reply_to_message.from_user.id
            user = message.reply_to_message.from_user
            username = get_username(user)
            add_to_blacklist(chat_id, user_id, username)
            bot.reply_to(message, f"Пользователь {username} добавлен в черный список.")
        else:
            bot.reply_to(message, "Пожалуйста, ответьте на сообщение пользователя, которого хотите добавить.")
    except Exception as e:
        print('278 '+str(e))

@bot.message_handler(commands=['whitelist_remove'])
def handle_whitelist_remove(message):
    try:
        if not is_admin(message):
            bot.reply_to(message, "Эта команда доступна только администраторам.")
            return
        chat_id = message.chat.id
        if message.reply_to_message:
            user_id = message.reply_to_message.from_user.id
            user = message.reply_to_message.from_user
            username = get_username(user)
            remove_from_whitelist(chat_id, user_id, username)
            bot.reply_to(message, f"Пользователь {username} удален из белого списка.")
        else:
            bot.reply_to(message, "Пожалуйста, ответьте на сообщение пользователя, которого хотите удалить.")
    except Exception as e:
        print('296 '+str(e))

@bot.message_handler(commands=['blacklist_remove'])
def handle_blacklist_remove(message):
    try:
        if not is_admin(message):
            bot.reply_to(message, "Эта команда доступна только администраторам.")
            return
        chat_id = message.chat.id
        if message.reply_to_message:
            user_id = message.reply_to_message.from_user.id
            user = message.reply_to_message.from_user
            username = get_username(user)
            remove_from_blacklist(chat_id, user_id, username)
            bot.reply_to(message, f"Пользователь {username} удален из черного списка.")
        else:
            bot.reply_to(message, "Пожалуйста, ответьте на сообщение пользователя, которого хотите удалить.")
    except Exception as e:
        print('314 '+str(e))

@bot.message_handler(commands=['show_whitelist'])
def handle_show_whitelist(message):
    try:
        if not is_admin(message):
            bot.reply_to(message, "Эта команда доступна только администраторам.")
            return
        chat_id = message.chat.id
        whitelist = show_whitelist(chat_id)
        if whitelist:
            users = ', '.join(str(user[0]) for user in whitelist)
            bot.reply_to(message, f"Белый список: {users}")
        else:
            bot.reply_to(message, "Белый список пуст.")
    except Exception as e:
        print('330 '+str(e))

@bot.message_handler(commands=['show_blacklist'])
def handle_show_blacklist(message):
    try:
        if not is_admin(message):
            bot.reply_to(message, "Эта команда доступна только администраторам.")
            return
        chat_id = message.chat.id
        blacklist = show_blacklist(chat_id)
        if blacklist:
            users = ', '.join(str(user[0]) for user in blacklist)
            bot.reply_to(message, f"Черный список: {users}")
        else:
            bot.reply_to(message, "Черный список пуст.")
    except Exception as e:
        print('346 '+str(e))

@bot.message_handler(content_types=['voice'])
def handle_voice(message):
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id

        mode = get_chat_mode(chat_id)

        if mode == 'whitelist' and not is_user_in_whitelist(chat_id, user_id):
            return

        if mode == 'blacklist' and is_user_in_blacklist(chat_id, user_id):
            return

        audio_file_path = download_audio(message.voice.file_id)
        text = recognize_speech(audio_file_path)

        if text:
            bot.reply_to(message, f'Распознанный текст:\n{text}')
        else:
            bot.reply_to(message, "Не удалось распознать речь.")
    except Exception as e:
        print('370 '+str(e))

@bot.message_handler(content_types=['video_note'])
def handle_video_note(message):
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id

        mode = get_chat_mode(chat_id)

        if mode == 'whitelist' and not is_user_in_whitelist(chat_id, user_id):
            return

        if mode == 'blacklist' and is_user_in_blacklist(chat_id, user_id):
            return

        file_id = message.video_note.file_id
        video_file_path = download_audio(file_id, is_video=True)

        text = recognize_speech(video_file_path)

        if text:
            bot.reply_to(message, f'Распознанный текст:\n{text}')
        else:
            bot.reply_to(message, "Не удалось распознать речь.")
    except Exception as e:
        print('396 '+str(e))

@bot.message_handler(content_types=['audio'])
def handle_audio(message):
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id

        mode = get_chat_mode(chat_id)

        if mode == 'whitelist' and not is_user_in_whitelist(chat_id, user_id):
            return

        if mode == 'blacklist' and is_user_in_blacklist(chat_id, user_id):
            return

        audio_file_path = download_audio(message.audio.file_id)
        text = recognize_speech(audio_file_path)
        if text:
            bot.reply_to(message, f'Распознанный текст:\n{text}')
        else:
            bot.reply_to(message, "Не удалось распознать речь.")
    except Exception as e:
        print('419 '+str(e))

@bot.message_handler(commands=['settings'])
def handle_settings(message):
    try:
        bot.reply_to(message, "В группах доступны настройки фильтра для сообщений. Доступны следующие фильтры:\n"
                              "По пользователю: бот хранит чёрный и белый список пользователей. "
                              "В режиме чёрного списка бот распознаёт сообщения от всех пользователей, "
                              "кроме тех, кто в чёрном списке. В режиме белого списка бот распознаёт сообщения "
                              "только тех пользователей, которые находятся в белом списке. Список команд:\n"
                              "/whitelist - включает режим белого списка\n"
                              "/blacklist - включает режим чёрного списка\n"
                              "/whitelist_add - добавляет пользователя в белый список (нужно писать команду ответом на любое сообщение пользователя, которого нужно внести в белый список)\n"
                              "/blacklist_add - добавляет пользователя в чёрный список (нужно писать команду ответом на любое сообщение пользователя, которого нужно внести в чёрный список)\n"
                              "/whitelist_remove - убирает пользователя из белого списка (нужно писать команду ответом на любое сообщение пользователя, которого нужно убрать из белого списка)\n"
                              "/blacklist_remove - убирает пользователя из чёрного списка (нужно писать команду ответом на любое сообщение пользователя, которого нужно добавить в чёрный список)\n"
                              "/show_whitelist - показывает белый список\n"
                              "/show_blacklist - показывает чёрный список")
    except Exception as e:
        print('438 '+str(e))

@bot.message_handler(func=lambda message: True)
def handle_other_messages(message):
    try:
        if message.chat.type == 'private':
            bot.reply_to(message, "Пожалуйста, отправьте голосовое или видеосообщение для распознавания.")
    except Exception as e:
        print('446 '+str(e))

if __name__ == '__main__':
    try:
        bot.polling(none_stop=True, timeout=60, interval=10)
    except Exception as e:
        print('452 '+str(e))
