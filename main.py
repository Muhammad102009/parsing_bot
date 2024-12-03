import asyncio
import logging
import sqlite3
from aiogram import Bot, Dispatcher,F
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup
from aiogram.filters import CommandStart, Command
from bs4 import BeautifulSoup
import requests
from config import token

bot = Bot(token=token)
dp = Dispatcher()

logging.basicConfig(level=logging.INFO)

news_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="/news")]],
    resize_keyboard=True
)

stop_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="/stop")]],
    resize_keyboard=True
) 

url = 'https://24.kg/page_'


stop_event = asyncio.Event()

conn = sqlite3.connect("news.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS news (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    news TEXT NOT NULL
)
""")
conn.commit()

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "Привет Нажми news для получения новостей или stop для остановки парсинга.",
        reply_markup=news_keyboard
    )

@dp.message(F.text == "/news")
async def fetch_news(message: Message):
    stop_event.clear()
    await message.answer("Начинаю парсинг новостей", reply_markup=stop_keyboard)

    for page in range(1):  
        if stop_event.is_set():
            await(f"Парсинг остановлен.")
            break
        try:
            response = requests.get(url.format(page))
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'lxml')

            news_items = soup.find_all("div", class_="title")
            if not news_items:
                await(f"На странице {page} не удалось найти новости.")
                continue
            for item in news_items:
                if stop_event.is_set():
                    break
                news_text = item.text.strip()
                cursor.execute("INSERT INTO news (news) VALUES (?)", (news_text,))
                conn.commit()
                await message.answer(news_text)


        except Exception as e:
            await(f"Ошибка при парсинге страницы")
            break


@dp.message(F.text == "/stop")
async def stop_parsing(message: Message):
    stop_event.set()
    await message.answer("Парсинг новостей остановлен.", reply_markup=news_keyboard)

async def main():
    try:
        await dp.start_polling(bot)
    finally:
        conn.close()
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
