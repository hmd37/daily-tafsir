import asyncio
import os
import textwrap

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from telegram import Bot
from telegram.error import NetworkError, TelegramError

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID").strip()

bot = Bot(token=TELEGRAM_BOT_TOKEN)


def wrap_text(text, limit=4000):
    return textwrap.wrap(text, width=limit, replace_whitespace=False)


async def send_with_retry(text):
    """Send message with retry logic."""
    for attempt in range(1, 3):
        try:
            await bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                text=text,
                parse_mode="Markdown",
            )
            break
        except (NetworkError, TelegramError) as e:
            if attempt == 2:
                raise
            await asyncio.sleep(2)


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
    data = scrape_daily_ayat_and_tafsir()

    header = f"📖 *Günün Ayeti*\n\n{data['ayat']}\n\n━━━━━━━━━━━━━━━\n📘 *Tefsir*\n"

    tafsir_parts = wrap_text(data["tafsir"])
    total_parts = len(tafsir_parts)

    await send_with_retry(header)

    for index, part in enumerate(tafsir_parts, start=1):
        part_header = f"*({index}/{total_parts})*\n\n"
        footer = f"\n\n🕊 Kaynak: {data['tafsir_link']}" if index == total_parts else ""

        text = f"{part_header}{part}{footer}"

        await send_with_retry(text)


if __name__ == "__main__":
    asyncio.run(send_daily_tafsir())
