import logging
import requests
import asyncio
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application, CallbackQueryHandler, ContextTypes, filters
)

TOKEN = "8482524807:AAGu-hiB7P58plabCEGkGFd7I3xcTYaCI9w"
OWNER_ID = 280793936
TARGET_CHAT_ID = -1002519528951

config = {
    "emoji": "👶🏼⚔️",
    "video": "https://www.pexels.com/video/854159.mp4"
}

# ========= XRPL BUY INTEGRATION SECTION =========

def get_latest_buys():
    # Ejemplo de integración: consulta las últimas TXs, filtra solo COMPRA
    # Usa la api de xrpscan (o puedes integrar una WebSocket real)
    # Mejorable: usa el websocket para detección instantánea y menor delay
    url = "https://api.xrpscan.com/api/v1/account/txs/BABYARMY_rHJGTuRZLakgmV4Dyb1m3Tj8MMCH4xAoYh_XRP"
    try:
        data = requests.get(url, timeout=10).json()
        result = []
        for tx in data.get("transactions", []):
            # Aquí debes SUPLANTAR LA LÓGICA para identificar una "compra" en tu par de XRPL
            # Simulación: es 'buy' si TransactionType es Payment y Destination es tu cuenta
            txinfo = tx.get("tx", {})
            if txinfo.get("TransactionType") != "Payment":
                continue
            # TODO: aquí tu lógica para COMPRA real (puede variar)
            result.append({
                "buyer": txinfo.get("Account"),
                "tx_hash": txinfo.get("hash"),
                "amount_xrp": float(txinfo.get("Amount"))/1_000_000,
                "amount_usd": 100,  # Debes traer precio y convertir aquí
                "marketcap": 1_800_000,  # Lo puedes calcular/fetch adecuado en la integración real
                "is_new_holder": True,
                "increase_pct": 0,
                "holders_total": 789,  # Supón lo calculas/fetch
                "trustlines": 4321,
                "timestamp": txinfo.get("date"),
            })
        return result
    except Exception as e:
        logging.error(f"Error fetch XRPL: {e}")
        return []

# Guardamos TX ya notificadas para evitar repeticiones
seen_txs = set()

async def notify_buys(app):
    while True:
        buys = get_latest_buys()
        for tx in buys:
            txid = tx["tx_hash"]
            if txid in seen_txs:
                continue
            seen_txs.add(txid)
            await send_buy_message(app, tx)
        await asyncio.sleep(20)  # Consulta cada 20 seg

async def send_buy_message(app, tx):
    emoji_count = min(int(tx["amount_usd"] // 10), 20)
    emojis = config["emoji"] * emoji_count if emoji_count else "💸"
    msg = (
        f"{emojis}\n\n"
        f"🪙 <b>COMPRA:</b> {tx['amount_xrp']:.2f} XRP (${tx['amount_usd']:.2f})\n"
        f"💸 <b>Marketcap:</b> ${tx['marketcap']:,}\n"
        + ("🎉 ¡Nuevo holder!\n" if tx["is_new_holder"] else f"⬆️ Aumentó su posición en {tx['increase_pct']}%\n")
        + f"👥 Holders: <b>{tx['holders_total']}</b>\n"
        f"🔗 Trustlines: <b>{tx['trustlines']}</b>\n\n"
    )
    buttons = [
        [
            InlineKeyboardButton("Tx", url=f"https://xrpscan.com/tx/{tx['tx_hash']}"),
            InlineKeyboardButton("Buyer", url=f"https://xrpscan.com/account/{tx['buyer']}"),
            InlineKeyboardButton("Chart", url="https://dexscreener.com/xrpl/4241425941524D59000000000000000000000000.rHJGTuRZLakgmV4Dyb1m3Tj8MMCH4xAoYh_xrp"),
        ],
        [
            InlineKeyboardButton("Xmagnetic", url="https://xmagnetic.org/dex/BABYARMY%2BrHJGTuRZLakgmV4Dyb1m3Tj8MMCH4xAoYh_XRP%2BXRP?network=mainnet"),
            InlineKeyboardButton("BUY", url="https://t.me/firstledger_bot?start=ref_P3qusTcUSdc2")
        ]
    ]
    keyboard = InlineKeyboardMarkup(buttons)
    await app.bot.send_video(
        chat_id=TARGET_CHAT_ID,
        video=config["video"],
        caption=msg,
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard
    )

# ========= ADMIN BOTONES PANEL =========

from telegram.ext import CallbackQueryHandler, CommandHandler

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("No tienes permisos para usar este panel.")
        return
    keyboard = [
        [
            InlineKeyboardButton("Cambiar Emojis", callback_data='admin_setemoji'),
            InlineKeyboardButton("Cambiar Video", callback_data='admin_setvideo')
        ]
    ]
    await update.message.reply_text(
        "Panel de ajustes de BabyArmy Bot",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_admin_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if update.effective_user.id != OWNER_ID:
        await query.edit_message_text("No tienes permisos.")
        return

    if query.data == 'admin_setemoji':
        await query.edit_message_text("Responde a este mensaje con el/los emojis nuevos (máx 8 caracteres).")
        context.user_data['wait_emoji'] = True
    elif query.data == 'admin_setvideo':
        await query.edit_message_text("Responde a este mensaje con el enlace directo al nuevo video (mp4).")
        context.user_data['wait_video'] = True

async def text_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    ud = context.user_data
    if ud.get('wait_emoji'):
        if len(update.message.text) <= 8:
            config["emoji"] = update.message.text
            await update.message.reply_text(f"Emoji actualizado a: {config['emoji']}")
        else:
            await update.message.reply_text("Demasiado largo. Intenta con menos de 8 caracteres.")
        ud['wait_emoji'] = False
    elif ud.get('wait_video'):
        if update.message.text.lower().startswith("http"):
            config["video"] = update.message.text
            await update.message.reply_text("Video actualizado correctamente.")
        else:
            await update.message.reply_text("No es un enlace válido.")
        ud['wait_video'] = False

def main():
    app = Application.builder().token(TOKEN).build()

    # Admin/Config buttons
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CallbackQueryHandler(handle_admin_buttons))
    app.add_handler(MessageHandler(filters.TEXT & filters.User(OWNER_ID), text_reply))
    # Arranca polling y la tarea XRPL
    app.run_async(notify_buys(app))
    app.run_polling()

if __name__ == '__main__':
    main()
