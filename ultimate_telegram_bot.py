
import telebot
from telebot import types
from datetime import datetime
import os
import time
import threading
import sqlite3

TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = os.getenv('ADMIN_ID')

if not TOKEN:
    raise ValueError("❌ BOT_TOKEN is not set in environment variables.")
if not ADMIN_ID:
    raise ValueError("❌ ADMIN_ID is not set in environment variables.")
ADMIN_ID = int(ADMIN_ID)

bot = telebot.TeleBot(TOKEN)

if not os.path.exists("media"):
    os.makedirs("media")

# DB Setup
conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    first_name TEXT,
    last_name TEXT,
    username TEXT,
    joined_at TEXT
)''')
conn.commit()

def save_user_to_db(user):
    user_id = user.id
    cursor.execute("SELECT id FROM users WHERE id=?", (user_id,))
    if not cursor.fetchone():
        fname = user.first_name or ""
        lname = user.last_name or ""
        uname = user.username or ""
        joined = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT INTO users (id, first_name, last_name, username, joined_at) VALUES (?, ?, ?, ?, ?)",
                       (user_id, fname, lname, uname, joined))
        conn.commit()

user_ids = set()
message_queue = {}

def delayed_delete(chat_id, msg_id, delay=60):
    def delete_later():
        time.sleep(delay)
        try:
            bot.delete_message(chat_id, msg_id)
        except:
            pass
    threading.Thread(target=delete_later).start()

@bot.message_handler(commands=['start'])
def handle_start(message):
    save_user_to_db(message.from_user)
    welcome_text = (
        "Ku soo biir adduunka madadaalada!\n\n"
        "📺 Botkaan wuxuu kuu keenayaa:\n\n"
        "🎞️ Aflaam Cusub iyo Kuwo Classic ah\n"
        "📽️ Musalsalo caalami ah iyo kuwa maxalli ah\n"
        "🔎 Raadinta fudud & helitaan degdeg ah\n"
        "📥 Download & daawasho online ah"
    )
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("🎬 Aflaam", callback_data='films'),
        types.InlineKeyboardButton("📺 Musalsalo", callback_data='series')
    )
    markup.row(
        types.InlineKeyboardButton("🌐 Daawo Online", url='https://youtube.com'),
        types.InlineKeyboardButton("⬇️ Soo Degso App", url='https://play.google.com')
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_buttons(call):
    if call.data == 'films':
        bot.send_message(call.message.chat.id, "🎬 Aflaam cusub iyo kuwa classic ah ayaa diyaar ah!")
    elif call.data == 'series':
        bot.send_message(call.message.chat.id, "📺 Musalsalo cusub & kuwa horeba way kuu diyaar yihiin.")

@bot.message_handler(commands=['help'])
def handle_help(message):
    help_text = (
        "🤖 *Talooyin iyo Amarro Muhiim ah:*\n\n"
        "/start - Fariin soo dhaweyn\n"
        "/help - Talooyin iyo amarro\n"
        "/go_online - Soo dir fariimihii dadku horey u soo direen\n"
        "/broadcast [fariin] - Dir fariin dhammaan dadka la xiriiray"
    )
    bot.send_message(message.chat.id, help_text, parse_mode='Markdown')

@bot.message_handler(commands=['broadcast'])
def admin_send_all(message):
    if message.from_user.id != ADMIN_ID:
        return
    parts = message.text.split(" ", 1)
    if len(parts) == 2:
        text = parts[1]
        sent = 0
        for row in cursor.execute("SELECT id FROM users"):
            uid = row[0]
            try:
                bot.send_message(uid, text)
                sent += 1
            except:
                pass
        bot.send_message(ADMIN_ID, f"📢 Fariintaada waxaa loo diray {sent} qof.")

@bot.message_handler(commands=['go_online'])
def handle_go_online(message):
    if message.from_user.id == ADMIN_ID:
        for uid, msg in message_queue.items():
            bot.forward_message(ADMIN_ID, uid, msg.message_id)
        message_queue.clear()
        bot.send_message(ADMIN_ID, "Dhamaan fariimihii keydsanaa waa lagu soo diray.")

@bot.message_handler(content_types=['text', 'photo', 'voice', 'document', 'audio', 'video', 'sticker'])
def handle_all(message):
    user = message.from_user
    user_id = user.id
    user_text = message.text.lower() if message.content_type == 'text' else ''

    if user_id != ADMIN_ID:
        save_user_to_db(user)
        user_ids.add(user_id)
        message_queue[user_id] = message
        bot.send_message(user_id, "Fariintaada waa la helay.")
        try:
            bot.delete_message(user_id, message.message_id)
        except:
            pass

        if any(word in user_text for word in ["film", "aflaam"]):
            bot.send_message(user_id, "🎬 Waxaad ka heli kartaa aflaam cusub iyo kuwa classic ah!")
        elif "musalsal" in user_text:
            bot.send_message(user_id, "📺 Musalsalo badan ayaa diyaar ah!")
        elif "download" in user_text:
            bot.send_message(user_id, "📥 Si aad u download garaysato, isticmaal badhamada kore.")
        elif "netflix" in user_text:
            bot.send_message(user_id, "🎥 Waxaan haynaa wax la mid ah Netflix... isku day!")
        elif "youtube" in user_text:
            bot.send_message(user_id, "➡️ Daawo YouTube links-ka aan kuu hayno.")
        elif any(word in user_text for word in ["hello", "salaan", "hi"]):
            bot.send_message(user_id, "Waa salaaman tahay! Sidee kuu caawin karaa?")

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

bot.polling()
