import os

API_TOKEN = os.getenv("BOT_TOKEN")

print("TOKEN DEBUG =", repr(API_TOKEN))  # 👈 IMPORTANT (on garde pour test)

import asyncio
import json
import random
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
# ================= CONFIG =================
import os
from aiogram import Bot, Dispatcher

API_TOKEN = os.getenv("API_TOKEN")
print("TOKEN =", API_TOKEN)

if not API_TOKEN:
    raise ValueError("API_TOKEN est manquant dans Railway Variables")

ADMIN_ID = 8364685971

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
# ================= DATABASE USERS =================
try:
    with open("users.json", "r") as f:
        users = json.load(f)
except:
    users = {}

def save_users():
    with open("users.json", "w") as f:
        json.dump(users, f)

# ================= VIDEO STORAGE =================
try:
    with open("config.json", "r") as f:
        VIDEO_FILE_ID = json.load(f).get("video_id")
except:
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

    await message.answer("✅ Vidéo enregistrée par admin")

# ================= START VIP =================
@dp.message(lambda m: m.text == "🔐 Activer VIP")
async def vip_start(message: types.Message):
    user_id = str(message.from_user.id)

    users.setdefault(user_id, {"vip": False, "step": None, "data": {}})

    users[user_id]["step"] = "1win"
    save_users()

    await message.answer("📌 Envoie ton ID compte 1WIN créé avec le code promo 22B9 :")

# ================= FORM FLOW (IMPORTANT) =================
@dp.message(lambda m: m.text and m.text not in ["📡 SIGNAL", "📊 STATUT", "🔐 Activer VIP"])
async def form_flow(message: types.Message):
    user_id = str(message.from_user.id)

    if user_id not in users:
        return

    step = users[user_id].get("step")

    if not step:
        return

    # STEP 1
    if step == "1win":
        users[user_id]["data"]["1win"] = message.text
        users[user_id]["step"] = "date"
        save_users()

        await message.answer("📌 Envoie la date de création de ton compte :")
        return

    # STEP 2
    if step == "date":
        users[user_id]["data"]["date"] = message.text
        users[user_id]["step"] = None
        save_users()

        data = users[user_id]["data"]

        await message.answer("⏳ Vérification de l'accès VIP en cours, veuillez patienter...")

        text = f"""📥 NOUVELLE DEMANDE VIP

👤 ID TELEGRAM: {user_id}
🆔 1WIN: {data['1win']}
📅 DATE: {data['date']}
"""

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Accepter", callback_data=f"vip_yes_{user_id}"),
                    InlineKeyboardButton(text="❌ Refuser", callback_data=f"vip_no_{user_id}")
                ]
            ]
        )

        await bot.send_message(ADMIN_ID, text, reply_markup=keyboard)
        return

# ================= ADMIN VALIDATION =================
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

        await bot.send_message(user_id, "🎉 VIP ACTIVÉ\n👉 Clique sur 📡 SIGNAL")
        await callback.message.edit_text(callback.message.text + "\n\n✅ ACCEPTÉ")

    else:
        users[user_id]["vip"] = False
        save_users()

        await bot.send_message(user_id, "❌ Refusé")
        await callback.message.edit_text(callback.message.text + "\n\n❌ REFUSÉ")

    await callback.answer()

# ================= SIGNAL =================
@dp.message(lambda m: m.text == "📡 SIGNAL")
async def signal(message: types.Message):
    user_id = str(message.from_user.id)

    if user_id not in users:
        await message.answer("❌ Utilise /start")
        return

    if not users[user_id].get("vip"):
        await message.answer("🔒 VIP requis")
        return

    if not VIDEO_FILE_ID:
        await message.answer("❌ Vidéo admin non enregistrée")
        return

    chance = random.randint(1, 100)

    if chance <= 10:
        target = round(random.uniform(20, 60), 2)
    elif chance <= 40:
        target = round(random.uniform(6, 18), 2)
    elif chance <= 75:
        target = round(random.uniform(3, 8), 2)
    else:
        target = round(random.uniform(1.5, 4), 2)

    safe = round(random.uniform(1.3, 2.2), 2)
    time_str = (datetime.now() + timedelta(minutes=2)).strftime("%H:%M")

    caption = f"""🚀 PREDICTION LUCKY JET

📡 SIGNAL: {time_str}

🎯 Objectif: jusqu'à {target}X
🛡️ SECURITÉ: {safe}X
"""

    await bot.send_video(message.chat.id, VIDEO_FILE_ID, caption=caption)

# ================= STATUT =================
@dp.message(lambda m: m.text == "📊 STATUT")
async def status(message: types.Message):
    user_id = str(message.from_user.id)

    if users.get(user_id, {}).get("vip"):
        await message.answer("✅ VIP ACTIF")
    else:
        await message.answer("❌ NON VIP")

# ================= RUN BOT =================
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
