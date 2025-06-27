import telebot
from flask import Flask, request

API_TOKEN = "8036134324:AAHC2LKLX6zr6fpNC4BShFKkdE3d_efxGl8"
bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

WEBHOOK_URL = f"https://telegram-bot-caashyuusuf990.onrender.com/{API_TOKEN}"

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, """Ku soo biir adduunka madadaalada!

📺 Botkaan wuxuu kuu keenayaa:

🎞️ Aflaam Cusub iyo Kuwo Classic ah
📽️ Musalsalo caalami ah iyo kuwa maxalli ah
🔎 Raadinta fudud & helitaan degdeg ah
📥 Download & daawasho online ah""")

@bot.message_handler(func=lambda m: True)
def echo_all(message):
    bot.reply_to(message, "Fariintaada waan helay 🎬")

@app.route(f'/{API_TOKEN}', methods=['POST'])
def webhook():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return '', 200

@app.route('/')
def index():
    return 'Bot is running with webhook!', 200

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host='0.0.0.0', port=10000)
