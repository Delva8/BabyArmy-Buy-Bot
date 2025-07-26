import asyncio
import logging
import websockets
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler,
    ContextTypes, filters
)

TOKEN = "8482524807:AAGu-hiB7P58plabCEGkGFd7I3xcTYaCI9w"
OWNER_ID = 280793936
TARGET_CHAT_ID = -1002519528951

config = {
    "emoji": "👶🏼⚔️",
    "video": "https://www.pexels.com/video/854159.mp4",
    "msg_template": (
        "{emojis}\n\n"
        "🪙 <b>COMPRA:</b> {amount_xrp:.2f} XRP (${amount_usd:.2f})\n"
        "💸 <b>Marketcap:</b> ${marketcap:,}\n"
        "{holder_text}"
        "👥 Holders: <b>{holders_total}</b>\n"
        "🔗 Trustlines: <b>{trustlines}</b>\n\n"
    ),
    "link_tx": "https://xrpscan.com/tx/{tx_hash}",
    "link_buyer": "https://xrpscan.com/account/{buyer}",
    "link_chart": "https://dexscreener.com/xrpl/4241425941524D59000000000000000000000000.rHJGTuRZLakgmV4Dyb1m3Tj8MMCH4xAoYh_xrp",
    "link_xmag": "https://xmagnetic.org/dex/BABYARMY%2BrHJGTuRZLakgmV4Dyb1m3Tj8MMCH4xAoYh_XRP%2BXRP?network=mainnet",
    "link_buy": "https://t.me/firstledger_bot?start=ref_P3qusTcUSdc2",
    "button_tx": "Tx",
    "button_buyer": "Buyer",
    "button_chart": "Chart",
    "button_xmag": "Xmagnetic",
    "button_buy": "BUY"
}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def xrpl_listener(app):
    URL = "wss://xrplcluster.com"
    CURRENCY = "4241425941524D59000000000000000000000000"  # BabyArmy (HEX)
    ISSUER = "rHJGTuRZLakgmV4Dyb1m3Tj8MMCH4xAoYh"
    seen = set()
    async with websockets.connect(URL) as ws:
        await ws.send(json.dumps({
            "id": 1,
            "command": "subscribe",
            "streams": ["transactions"]
        }))
        while True:
            data = await ws.recv()
            try:
                dct = json.loads(data)
                tx = dct.get("transaction", {})
                amt = tx.get("Amount")
                if tx.get("TransactionType") != "Payment" or not isinstance(amt, dict):
                    continue
                if amt.get("currency") != CURRENCY or amt.get("issuer") != ISSUER:
                    continue
                txhash = tx.get("hash")
                if txhash in seen:
                    continue
                seen.add(txhash)
                buyer = tx.get("Account")
                amount_xrp = float(amt.get("value"))
                amount_usd = amount_xrp * 0.5
                marketcap = 1_800_000
                is_new_holder = True
                increase_pct = 15
                holders_total = 789
                trustlines = 4321

                await send_buy_message(
                    app, buyer=buyer, tx_hash=txhash, amount_xrp=amount_xrp,
                    amount_usd=amount_usd, marketcap=marketcap,
                    is_new_holder=is_new_holder, increase_pct=increase_pct,
                    holders_total=holders_total, trustlines=trustlines
                )
            except Exception as ex:
                logging.warning(f"Parse fail: {ex}")

async def send_buy_message(
    app, buyer, tx_hash, amount_xrp, amount_usd, marketcap,
    is_new_holder, increase_pct, holders_total, trustlines
):
    emoji_count = min(int(amount_usd // 10), 20)
    emojis = config["emoji"] * emoji_count if emoji_count else "💸"
    holder_text = (
        "🎉 ¡Nuevo holder!\n" if is_new_holder
        else f"⬆️ Aumentó su posición en {increase_pct}%\n"
    )
    msg = config["msg_template"].format(
        emojis=emojis, amount_xrp=amount_xrp, amount_usd=amount_usd,
        marketcap=marketcap, holder_text=holder_text,
        holders_total=holders_total, trustlines=trustlines
    )
    buttons = [
        [
            InlineKeyboardButton(
                config["button_tx"], url=config["link_tx"].format(tx_hash=tx_hash)
            ),
            InlineKeyboardButton(
                config["button_buyer"], url=config["link_buyer"].format(buyer=buyer)
            ),
            InlineKeyboardButton(
                config["button_chart"], url=config["link_chart"])
        ],
        [
            InlineKeyboardButton(
                config["button_xmag"], url=config["link_xmag"]
            ),
            InlineKeyboardButton(
                config["button_buy"], url=config["link_buy"]
            )
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

# ========== Panel Admin Full Personalización =========
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("No tienes permisos para usar este panel.")
        return
    edit_list = [
        ("Cambiar emojis", "setemoji"),
        ("Cambiar video", "setvideo"),
        ("Cambiar plantilla mensaje", "setmsg"),
        ("Cambiar link TX", "setlink_tx"),
        ("Cambiar link buyer", "setlink_buyer"),
        ("Cambiar link chart", "setlink_chart"),
        ("Cambiar link xmagnetic", "setlink_xmag"),
        ("Cambiar link buy", "setlink_buy"),
        ("Cambiar texto botón Tx", "setbutton_tx"),
        ("Cambiar texto botón Buyer", "setbutton_buyer"),
        ("Cambiar texto botón Chart", "setbutton_chart"),
        ("Cambiar texto botón Xmagnetic", "setbutton_xmag"),
        ("Cambiar texto botón BUY", "setbutton_buy"),
    ]
    keyboard = [
        [InlineKeyboardButton(text, callback_data=cb)]
        for text, cb in edit_list
    ]
    await update.message.reply_text(
        "PANEL DE ADMINISTRACIÓN: Cambia cualquier aspecto del mensaje y botones.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_admin_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if update.effective_user.id != OWNER_ID:
        await query.edit_message_text("No tienes permisos.")
        return

    field = query.data
    prompts = {
        "setemoji": "Responde con los nuevos emojis (máx 8 caracteres):",
        "setvideo": "Responde con el enlace directo al nuevo video (mp4):",
        "setmsg": (
            "Responde con la NUEVA PLANTILLA de mensaje. Puedes usar estos campos: "
            "{emojis} {amount_xrp} {amount_usd} {marketcap} {holder_text} "
            "{holders_total} {trustlines}"
        ),
        "setlink_tx": "Responde con la nueva URL para 'Tx' (usa {tx_hash} para el hash).",
        "setlink_buyer": "Responde con la nueva URL para 'Buyer' (usa {buyer} para la dirección).",
        "setlink_chart": "Responde con la nueva URL de Chart",
        "setlink_xmag": "Responde con la nueva URL de Xmagnetic",
        "setlink_buy": "Responde con la nueva URL de BUY",
        "setbutton_tx": "Responde con el NUEVO texto para el botón 'Tx'",
        "setbutton_buyer": "Responde con el NUEVO texto para el botón 'Buyer'",
        "setbutton_chart": "Responde con el NUEVO texto para el botón 'Chart'",
        "setbutton_xmag": "Responde con el NUEVO texto para el botón 'Xmagnetic'",
        "setbutton_buy": "Responde con el NUEVO texto para el botón 'BUY'"
    }
    await query.edit_message_text(prompts.get(field, "¿Qué deseas personalizar?"))
    context.user_data["edit_field"] = field

async def admin_text_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    field = context.user_data.pop("edit_field", None)
    if not field:
        return
    text = update.message.text.strip()
    if field == "setemoji":
        if len(text) <= 8:
            config["emoji"] = text
            await update.message.reply_text(f"Emoji actualizado a: {text}")
        else:
            await update.message.reply_text("Máximo 8 caracteres.")
    elif field == "setvideo":
        if text.lower().startswith("http"):
            config["video"] = text
            await update.message.reply_text("Video actualizado.")
        else:
            await update.message.reply_text("Enlace inválido.")
    elif field == "setmsg":
        config["msg_template"] = text
        await update.message.reply_text("Plantilla de mensaje actualizada.")
    elif field.startswith("setlink_"):
        key = field.replace("setlink_", "link_")
        config[key] = text
        await update.message.reply_text(f"Link actualizado para {key}.")
    elif field.startswith("setbutton_"):
        key = field.replace("setbutton_", "button_")
        config[key] = text
        await update.message.reply_text(f"Texto del botón '{key}' actualizado.")
    else:
        await update.message.reply_text("Campo desconocido.")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CallbackQueryHandler(handle_admin_buttons))
    app.add_handler(MessageHandler(filters.TEXT & filters.User(OWNER_ID), admin_text_response))

    # Inicia el listener XRPL como tarea en segundo plano
    loop = asyncio.get_event_loop()
    loop.create_task(xrpl_listener(app))

    app.run_polling()

if __name__ == "__main__":
    main()
