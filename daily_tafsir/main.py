import asyncio
import os

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from telegram import Bot

load_dotenv()


TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

bot = Bot(token=TELEGRAM_BOT_TOKEN)


def scrape_daily_ayat_and_tafsir():
    daily_ayat_url = "https://www.kuranvemeali.com/"
    response = requests.get(daily_ayat_url)
    soup = BeautifulSoup(response.text, "html.parser")

    ayat_meal_link = (
        daily_ayat_url + soup.find("a", {"class": "btn-sm btn-warning"})["href"]
    )
    ayat_tafsir_link = ayat_meal_link.replace("-meali", "-tefsiri")

    ayat_div = soup.find("div", {"class": "col-sm-12 team-block text-center"})
    ayat = ayat_div.find("p").get_text(strip=True)

    tafsir_soup = BeautifulSoup(requests.get(ayat_tafsir_link).text, "html.parser")
    tafsir_div = tafsir_soup.find_all("div", {"class": "tefsir"})[-1]

    for tag in tafsir_div.find_all(["h4", "a", "h5"]):
        tag.decompose()

    tafsir = tafsir_div.get_text(strip=True)
    tafsir = tafsir.replace("\r", "").replace("\n", " ")

    return {
        "ayat": ayat,
        "tafsir": tafsir,
        "tafsir_link": ayat_tafsir_link,
    }


async def send_daily_tafsir():
    """Scrape ayet & tefsir and send to Telegram group."""
    data = scrape_daily_ayat_and_tafsir()

    msg = (
        "<b>📖 Günün Ayeti</b>\n\n"
        f"{data['ayat']}\n\n"
        "━━━━━━━━━━━━━━━\n"
        "<b>📘 Tefsir</b>\n\n"
        f"{data['tafsir']}\n\n"
        f"🕊 <i>Kaynak: {data['tafsir_link']}</i>"
    )

    await bot.send_message(
        chat_id=TELEGRAM_CHAT_ID,
        text=msg,
        parse_mode="HTML",
    )


if __name__ == "__main__":
    asyncio.run(send_daily_tafsir())
