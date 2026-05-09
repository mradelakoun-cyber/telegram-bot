import os
API_TOKEN = os.getenv("API_TOKEN") or os.getenv("BOT_TOKEN")

print("TOKEN =", API_TOKEN)

import asyncio
import json
import random
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# ================= DEBUG ENV =================
API_TOKEN = "8615451117:AAHO6pIOhxqJ8frnrCPQ0A_XLEhFZDbM7Ew"
print("🔎 TOKEN DEBUG =", API_TOKEN)

# ⚠️ STOP SI TOKEN ABSENT
if API_TOKEN is None or API_TOKEN.strip() == "":
    raise RuntimeError(
        "❌ API_TOKEN manquant. Vérifie Railway → Variables → API_TOKEN"
    )

ADMIN_ID = 8364685971

# ================= BOT INIT =================
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# ================= DATABASE USERS =================
try:
    with open("users.json", "r") as f:
        users = json.load(f)
except FileNotFoundError:
    users = {}

def save_users():
    with open("users.json", "w") as f:
        json.dump(users, f)

# ================= VIDEO CONFIG =================
try:
    with open("config.json", "r") as f:
        VIDEO_FILE_ID = json.load(f).get("video_id")
except FileNotFoundError:
    VIDEO_FILE_ID = None

# ================= MENU =================
menu = types.ReplyKeyboardMarkup(
    keyboard=[
        [types.KeyboardButton(text="📡 SIGNAL"), types.KeyboardButton(text="📊 STATUT")],
        [types.KeyboardButton(text="🔐 Activer VIP")]
    ],
    resize_keyboard=True
)

# ================= START =================
@dp.message(CommandStart())
async def start(message: types.Message):
    user_id = str(message.from_user.id)

    users.setdefault(user_id, {"vip": False, "step": None, "data": {}})
    save_users()

    await message.answer("🚀 BOT VIP ACTIF", reply_markup=menu)

# ================= ADMIN VIDEO =================
@dp.message(lambda m: m.video and m.from_user.id == ADMIN_ID)
async def save_video(message: types.Message):
    global VIDEO_FILE_ID
    VIDEO_FILE_ID = message.video.file_id

    with open("config.json", "w") as f:
        json.dump({"video_id": VIDEO_FILE_ID}, f)

    await message.answer("✅ Vidéo enregistrée")

# ================= VIP START (MODIFIÉ UNIQUEMENT ICI) =================
@dp.message(lambda m: m.text == "🔐 Activer VIP")
async def vip_start(message: types.Message):
    user_id = str(message.from_user.id)

    users.setdefault(user_id, {"vip": False, "step": None, "data": {}})

    # 🔥 AJOUT DEMANDÉ
    if users[user_id].get("vip"):
        await message.answer("🎉 Vous êtes actuellement en mode VIP")
        return

    users[user_id]["step"] = "1win"
    save_users()

    await message.answer("📌 Envoie ton ID 1WIN (code promo 22B9)")

# ================= FORM FLOW =================
@dp.message(lambda m: m.text and m.text not in ["📡 SIGNAL", "📊 STATUT", "🔐 Activer VIP"])
async def form_flow(message: types.Message):
    user_id = str(message.from_user.id)

    if user_id not in users:
        return

    step = users[user_id].get("step")
    if not step:
        return

    if step == "1win":
        users[user_id]["data"]["1win"] = message.text
        users[user_id]["step"] = "date"
        save_users()
        await message.answer("📌 Date de création ?")
        return

    if step == "date":
        users[user_id]["data"]["date"] = message.text
        users[user_id]["step"] = None
        save_users()

        data = users[user_id]["data"]

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Accepter", callback_data=f"vip_yes_{user_id}"),
                    InlineKeyboardButton(text="❌ Refuser", callback_data=f"vip_no_{user_id}")
                ]
            ]
        )

        await bot.send_message(
            ADMIN_ID,
            f"📥 DEMANDE VIP\n\n👤 {user_id}\n🆔 {data['1win']}\n📅 {data['date']}",
            reply_markup=keyboard
        )

# ================= ADMIN VIP =================
@dp.callback_query(lambda c: c.data.startswith("vip_"))
async def admin_vip(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Non autorisé", show_alert=True)
        return

    action, user_id = callback.data.split("_")[1:]

    users.setdefault(user_id, {"vip": False, "step": None, "data": {}})

    if action == "yes":
        users[user_id]["vip"] = True
        save_users()
        await bot.send_message(user_id, "🎉 VIP ACTIVÉ")
    else:
        users[user_id]["vip"] = False
        save_users()
        await bot.send_message(user_id, "❌ Refusé")

    await callback.answer()

# ================= SIGNAL =================
@dp.message(lambda m: m.text == "📡 SIGNAL")
async def signal(message: types.Message):
    user_id = str(message.from_user.id)

    if not users.get(user_id, {}).get("vip"):
        await message.answer("🔒 VIP requis")
        return

    if not VIDEO_FILE_ID:
        await message.answer("❌ Vidéo admin manquante")
        return

    target = round(random.uniform(1.5, 60), 2)
    safe = round(random.uniform(1.3, 1.6), 2)

    time_str = (datetime.now() + timedelta(minutes=2)).strftime("%H:%M")

    caption = f"""🚀 SIGNAL

📡 Heure: {time_str}
🎯 Objectif: {target}X
🛡️ Sécurité: {safe}X"""

    await bot.send_video(message.chat.id, VIDEO_FILE_ID, caption=caption)

# ================= STATUT =================
@dp.message(lambda m: m.text == "📊 STATUT")
async def status(message: types.Message):
    user_id = str(message.from_user.id)

    if users.get(user_id, {}).get("vip"):
        await message.answer("✅ VIP ACTIF")
    else:
        await message.answer("❌ NON VIP")

# ================= START BOT =================
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())