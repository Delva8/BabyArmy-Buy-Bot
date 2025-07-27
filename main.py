import asyncio
import logging
import threading
import websockets
import json
import aiohttp
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler,
    ContextTypes, filters
)

# --- CONFIGURACIÓN BOT ---
TOKEN = "8482524807:AAGu-hiB7P58plabCEGkGFd7I3xcTYaCI9w"
OWNER_ID = 280793936
TARGET_CHAT_ID = -1002519528951
config = {
    "emoji": "👶🏼⚔️",
    "video_file_id": None,
    "video_url": "https://www.pexels.com/video/854159.mp4",
    "msg_template": (
        "{emojis}\n\n"
        "{xrp_price_line}"
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
pending_config = {}

# --- HTTP SERVER PARA MANTENER VIVO EN REPLIT ---
flask_app = Flask(__name__)
@flask_app.route("/")
def index():
    return "I'm alive! BabyArmy Buy Bot está activo!"

def run_flask():
    flask_app.run(host="0.0.0.0", port=8080)

# --- FUNCIONES DEL BOT (NO CAMBIES) ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def get_xrp_price():
    url = "https://api.coingecko.com/api/v3/simple/price?ids=ripple&vs_currencies=usd"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as resp:
                data = await resp.json()
                return float(data["ripple"]["usd"])
    except Exception:
        return None

def build_preview_message(cfg=None, *, example_data=None, xrp_price=0.5):
    if cfg is None:
        cfg = config
    data = example_data or {
        "buyer": "rEXAMPLEaddress",
        "tx_hash": "EXAMPLETXHASH",
        "amount_xrp": 321.5,
        "amount_usd": 1234,
        "marketcap": 1_800_000,
        "is_new_holder": True,
        "increase_pct": 15,
        "holders_total": 789,
        "trustlines": 4321
    }
    emoji_count = min(int(data["amount_usd"] // 10), 20)
    emojis = cfg["emoji"] * emoji_count if emoji_count else "💸"
    holder_text = (
        "🎉 ¡Nuevo holder!\n" if data["is_new_holder"]
        else f"⬆️ Aumentó su posición en {data['increase_pct']}%\n"
    )
    price_line = f"<b>Precio XRP</b>: 1 XRP = ${xrp_price:.4f}\n" if xrp_price else ""
    return cfg["msg_template"].format(
        emojis=emojis, amount_xrp=data["amount_xrp"], amount_usd=data["amount_usd"],
        marketcap=data["marketcap"], holder_text=holder_text,
        holders_total=data["holders_total"], trustlines=data["trustlines"],
        xrp_price_line=price_line
    )

def build_buttons(cfg=None, *, tx_hash="EXAMPLETXHASH", buyer="rEXAMPLEaddress"):
    if cfg is None:
        cfg = config
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                cfg["button_tx"], url=cfg["link_tx"].format(tx_hash=tx_hash)),
            InlineKeyboardButton(
                cfg["button_buyer"], url=cfg["link_buyer"].format(buyer=buyer)),
            InlineKeyboardButton(
                cfg["button_chart"], url=cfg["link_chart"]),
        ],
        [
            InlineKeyboardButton(
                cfg["button_xmag"], url=cfg["link_xmag"]),
            InlineKeyboardButton(
                cfg["button_buy"], url=cfg["link_buy"])
        ]
    ])

async def xrpl_listener(app):
    URL = "wss://xrplcluster.com"
    CURRENCY = "4241425941524D59000000000000000000000000"
    ISSUER = "rHJGTuRZLakgmV4Dyb1m3Tj8MMCH4xAoYh"
    seen = set()
    while True:
        try:
            async with websockets.connect(URL) as ws:
                await ws.send(json.dumps({"id": 1, "command": "subscribe", "streams": ["transactions"]}))
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
                        xrp_usd = await get_xrp_price() or 0.5
                        amount_usd = amount_xrp * xrp_usd
                        marketcap = 1_800_000
                        is_new_holder = True
                        increase_pct = 15
                        holders_total = 789
                        trustlines = 4321
                        await send_buy_message(
                            app, buyer=buyer, tx_hash=txhash, amount_xrp=amount_xrp,
                            amount_usd=amount_usd, marketcap=marketcap,
                            is_new_holder=is_new_holder, increase_pct=increase_pct,
                            holders_total=holders_total, trustlines=trustlines,
                            xrp_usd=xrp_usd
                        )
                    except Exception as ex:
                        logging.warning(f"Parse fail: {ex}")
        except Exception as ex:
            logging.warning(f"XRPL WS error, reintentando: {ex}")
            await asyncio.sleep(10)

async def send_buy_message(
    app, buyer, tx_hash, amount_xrp, amount_usd, marketcap,
    is_new_holder, increase_pct, holders_total, trustlines, xrp_usd
):
    emoji_count = min(int(amount_usd // 10), 20)
    emojis = config["emoji"] * emoji_count if emoji_count else "💸"
    holder_text = (
        "🎉 ¡Nuevo holder!\n" if is_new_holder
        else f"⬆️ Aumentó su posición en {increase_pct}%\n"
    )
    price_line = f"<b>Precio XRP</b>: 1 XRP = ${xrp_usd:.4f}\n" if xrp_usd else ""
    msg = config["msg_template"].format(
        emojis=emojis, amount_xrp=amount_xrp, amount_usd=amount_usd,
        marketcap=marketcap, holder_text=holder_text,
        holders_total=holders_total, trustlines=trustlines,
        xrp_price_line=price_line
    )
    keyboard = build_buttons(cfg=config, tx_hash=tx_hash, buyer=buyer)
    try:
        if config.get("video_file_id"):
            await app.bot.send_video(
                chat_id=TARGET_CHAT_ID,
                video=config["video_file_id"],
                caption=msg,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard
            )
        else:
            await app.bot.send_video(
                chat_id=TARGET_CHAT_ID,
                video=config["video_url"],
                caption=msg,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard
            )
    except Exception as ex:
        logging.warning(f"No se pudo enviar video: {ex}")

# --- PANEL ADMIN omito por brevedad, usa el panel que ya tenías arriba ---
# Añade aquí el admin_fields, admin_panel, admin_callback, admin_text_response,
# handle_confirm_cancel que ya usas. Exactamente igual.

# Para ejemplo usaremos un comando /start mínimo
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("¡Hola! El bot BabyArmy está activo.")

def main():
    # Inicia servidor Flask en hilo paralelo
    threading.Thread(target=run_flask, daemon=True).start()
    # Arranca el bot Telegram
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    # Añade aquí el resto de tus handlers/funciones administrativas...
    loop = asyncio.get_event_loop()
    loop.create_task(xrpl_listener(app))
    app.run_polling()

if __name__ == "__main__":
    main()
