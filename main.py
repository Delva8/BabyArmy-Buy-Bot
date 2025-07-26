import asyncio
import logging
import websockets
import json
import aiohttp
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
        emojis=emojis,
        amount_xrp=data["amount_xrp"],
        amount_usd=data["amount_usd"],
        marketcap=data["marketcap"],
        holder_text=holder_text,
        holders_total=data["holders_total"],
        trustlines=data["trustlines"],
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
