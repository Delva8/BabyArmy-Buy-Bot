import os
import logging
from flask import Flask, request
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InputMediaVideo
from telegram.constants import ParseMode
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, ContextTypes
)
import asyncio

TOKEN = os.environ.get("TELEGRAM_TOKEN")
OWNER_ID = 123456789  # tu user_id de Telegram (cámbialo por el tuyo)

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update, context):
    await update.message.reply_text("¡Hola! Soy tu bot listo para mostrar compras de BabyArmy 🍼")

async def buy(update, context):
    # Simular datos (sustituye por los reales cuando conectes a la blockchain)
    buyer = "rEXAMPLEaddress"
    tx_hash = "EXAMPLETXHASH"
    amount_xrp = 321.5
    amount_usd = 1234.5
    marketcap = 1800000
    is_new_holder = True
    increase_pct = 15
    holders_total = 789
    trustlines = 4321

    # Un emoji por cada 10 dólares (máximo 20 emojis para no saturar)
    emoji = "🔥"
    emoji_count = min(int(amount_usd // 10), 20)
    emojis = emoji * emoji_count if emoji_count else "💸"

    # Ejemplo video MP4 guardado en carpeta del repo (o usa una URL directa)
    video_url = "https://www.pexels.com/video/854159.mp4"  # Ejemplo externo

    # Texto principal
    msg = (
        f"{emojis}\n\n"
        f"🪙 <b>COMPRA:</b> {amount_xrp:.2f} XRP (${amount_usd:.2f})\n"
        f"💸 <b>Marketcap:</b> ${marketcap:,}\n"
    )

    if is_new_holder:
        msg += "🎉 ¡Nuevo holder!\n"
    else:
        msg += f"⬆️ Aumentó su posición en {increase_pct}%\n"

    msg += (
        f"👥 Holders: <b>{holders_total}</b>\n"
        f"🔗 Trustlines: <b>{trustlines}</b>\n\n"
    )

    # Botones en línea
    buttons = [
        [
            InlineKeyboardButton("Tx", url=f"https://xrpscan.com/tx/{tx_hash}"),
            InlineKeyboardButton("Buyer", url=f"https://xrpscan.com/account/{buyer}"),
            InlineKeyboardButton("Chart", url="https://dexscreener.com/xrpl/4241425941524D59000000000000000000000000.rHJGTuRZLakgmV4Dyb1m3Tj8MMCH4xAoYh_xrp"),
        ],
        [
            InlineKeyboardButton("Xmagnetic", url="https://xmagnetic.org/dex/BABYARMY%2BrHJGTuRZLakgmV4Dyb1m3Tj8MMCH4xAoYh_XRP%2BXRP?network=mainnet"),
            InlineKeyboardButton("BUY", url="https://t.me/firstledger_bot?start=ref_P3qusTcUSdc2")
        ]
    ]

    keyboard = InlineKeyboardMarkup(buttons)

    # Enviar video + mensaje
    await context.bot.send_video(
        chat_id=update.message.chat.id,
        video=video_url,
        caption=msg,
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard
    )

async def admin(update, context):
    """Solo el dueño puede cambiar algunos ajustes."""
    user_id = update.message.from_user.id
    if user_id != OWNER_ID:
        await update.message.reply_text("No tienes permisos para usar este comando.")
        return
    await update.message.reply_text(
        "Aquí puedes cambiar la foto, emojis y ajustes futuros (próximamente)"
    )

def main():  # No uses Flask para la webhook, usa el built-in de la v21
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("buy", buy))
    application.add_handler(CommandHandler("admin", admin))

    # Mensaje eco (texto normal)
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, start)
    )
    # Inicia el bot
    application.run_polling()  # O usa .run_webhook() si prefieres webhook y tienes Render PRO

if __name__ == '__main__':
    main()
