import time
import requests
from bs4 import BeautifulSoup
import telebot
import threading
import os
from flask import Flask

TOKEN = os.getenv("TOKEN")  # токен бота из Environment Variables
bot = telebot.TeleBot(TOKEN)

SEARCH_QUERY = "iphone"
CITY_URL = "https://www.avito.ru/ufa"
CHECK_INTERVAL = 60  # проверка каждые 60 секунд
LAST_IDS = set()
ALLOWED_MODELS = ["xs","xr","11","12","13","14","15","16","pro","max"]

app = Flask(__name__)

def is_modern_model(title):
    title = title.lower()
    return any(model in title for model in ALLOWED_MODELS)

def fetch_ads():
    headers = {"User-Agent": "Mozilla/5.0"}
    url = f"{CITY_URL}?q={SEARCH_QUERY}"
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")
    ads = soup.select("div[data-marker='item']")
    new_ads = []

    for ad in ads:
        ad_id = ad.get("data-item-id")
        if not ad_id or ad_id in LAST_IDS:
            continue

        title_tag = ad.select_one("h3")
        link_tag = ad.select_one("a.link-link-MbQDP")
        price_tag = ad.select_one("span.price-text-_YGDY")

        if not title_tag or not link_tag:
            continue

        title = title_tag.text.strip()
        if not is_modern_model(title):
            continue

        link = "https://www.avito.ru" + link_tag.get("href")
        price = price_tag.text.strip() if price_tag else "Цена не указана"

        LAST_IDS.add(ad_id)
        new_ads.append((title, price, link))
    return new_ads

def check_ads(chat_id):
    while True:
        new = fetch_ads()
        for title, price, link in new:
            msg = f"📱 {title}\n💰 {price}\n🔗 {link}"
            bot.send_message(chat_id, msg)
        time.sleep(CHECK_INTERVAL)

@bot.message_handler(commands=["start"])
def start(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "✅ Отслеживаю новые iPhone XS и выше в Уфе.")
    t = threading.Thread(target=check_ads, args=(chat_id,))
    t.start()

@app.route("/")
def home():
    return "Bot is running!"

def run_bot():
    bot.infinity_polling()

if __name__ == "__main__":
    t = threading.Thread(target=run_bot)
    t.start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
