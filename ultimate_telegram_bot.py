
import telebot
from telebot import types
from datetime import datetime
import os
import time
import threading

TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID'))

bot = telebot.TeleBot(TOKEN)

if not os.path.exists("media"):
    os.makedirs("media")

user_map = {}
message_queue = []
user_ids = set()

def log_message(user, content):
    with open("message_log.txt", "a", encoding="utf-8") as f:
        time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{time_now}] {user}: {content}\n")

def save_file(file_id, path):
    file_info = bot.get_file(file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    with open(path, 'wb') as f:
        f.write(downloaded_file)

def delayed_delete(chat_id, msg_id, delay=60):
    def delete_later():
        time.sleep(delay)
        try:
            bot.delete_message(chat_id, msg_id)
        except:
            pass
    threading.Thread(target=delete_later).start()

@bot.message_handler(commands=['broadcast'])
def admin_send_all(message):
    if message.from_user.id != ADMIN_ID:
        return
    parts = message.text.split(" ", 1)
    if len(parts) == 2:
        text = parts[1]
        for uid in user_ids:
            try:
                bot.send_message(uid, text)
            except:
                pass

@bot.message_handler(content_types=['text', 'photo', 'voice', 'document', 'audio', 'video', 'sticker'])
def handle_all(message):
    user_id = message.from_user.id
    user_name = f"{message.from_user.first_name or ''} {message.from_user.last_name or ''}".strip()
    user_info = f"{user_name} (ID: {user_id})"
    time_now = datetime.now().strftime("%Y%m%d_%H%M%S")

    if user_id != ADMIN_ID:
        user_ids.add(user_id)
        message_queue.append((user_info, message))
        bot.send_message(user_id, "Fariintaada waa la helay.")
        try:
            bot.delete_message(user_id, message.message_id)
        except:
            pass
    else:
        if message.reply_to_message:
            forwarded = message.reply_to_message.forward_from
            if forwarded:
                bot.send_message(forwarded.id, message.text)
        else:
            parts = message.text.split(" ", 1)
            if len(parts) == 2:
                uid = int(parts[0])
                bot.send_message(uid, parts[1])
                m = bot.send_message(user_id, "Fariinta waa la diray.")
                delayed_delete(user_id, m.message_id)
                delayed_delete(user_id, message.message_id)

@bot.message_handler(commands=['go_online'])
def handle_go_online(message):
    if message.from_user.id == ADMIN_ID:
        for info, msg in message_queue:
            bot.forward_message(ADMIN_ID, msg.chat.id, msg.message_id)
            log_message(info, f"Fariin keyd ahayd oo la diray: {msg.content_type}")
        message_queue.clear()
        bot.send_message(ADMIN_ID, "Dhamaan fariimihii keydsanaa waa lagu soo diray.")

bot.polling()
