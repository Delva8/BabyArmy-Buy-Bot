from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters
import logging
import os

app = Flask(__name__)

TOKEN = os.environ.get("TELEGRAM_TOKEN")  # Pon tu token en variables de entorno en Render

bot = Bot(token=TOKEN)
dispatcher = Dispatcher(bot, None, workers=0, use_context=True)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Comandos
def start(update, context):
    update.message.reply_text("Hola! Soy tu bot listo para comprar BabyArmy 🍼")

def buy(update, context):
    update.message.reply_text("Vamos a comprar BabyArmy! (Esto es un ejemplo)")

def echo(update, context):
    text = update.message.text
    update.message.reply_text(f"Has escrito: {text}")

# Registrar handlers
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("buy", buy))
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    json_update = request.get_json(force=True)
    update = Update.de_json(json_update, bot)
    dispatcher.process_update(update)
    return 'OK'

@app.route('/')
def index():
    return "Bot BabyArmy Buy está funcionando!"

if __name__ == '__main__':
    # Establecer webhook en Render:
    webhook_url = f"https://babyarmy-buy-bot.onrender.com/{TOKEN}"
    bot.set_webhook(webhook_url)
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
