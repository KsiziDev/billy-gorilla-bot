import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
CHANNEL_ID = os.getenv("CHANNEL_ID", "@billy_gorilla")
CHANNEL_URL = os.getenv("CHANNEL_URL", "https://t.me/billy_gorilla")

DB_PATH = "data/bot.db"

# Цены в звёздах
PRICE_PRO = 199          # ⭐/мес
PRICE_LIFETIME = 2490    # ⭐ навсегда
PRICE_PROGRAM = 590      # ⭐ разовая программа

# Плейлист
PLAYLIST_URL = CHANNEL_URL
