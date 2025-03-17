import asyncio
import logging
import time

from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from aiogram.types import Message

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, NoSuchElementException

from webdriver_manager.chrome import ChromeDriverManager

# 🔹 Твой Telegram токен
TOKEN = "8047733951:AAG4Tyb6TFm65niNsJ2QlAUMHU4IOt4taKc"

# 🔹 Настройки бота
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
dp = Dispatcher()

# 🔹 Настройки парсинга (Разработка и IT - одна категория)
CATEGORY = "41"  # Категория "Разработка" и "ИТ"
BASE_URL = "https://kwork.ru/projects?c="
MIN_PRICE = 1000
MAX_PRICE = 70000

# 🔹 Настройки Selenium
options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')


# 🔹 Функция парсинга заказов
def get_orders():
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    orders = []

    try:
        url = BASE_URL + CATEGORY
        driver.get(url)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.want-card.want-card--list"))
        )

        elements = driver.find_elements(By.CSS_SELECTOR, "div.want-card.want-card--list")

        for element in elements:
            try:
                title_element = element.find_element(By.CSS_SELECTOR, ".wants-card__header-title")
                price_element = element.find_element(By.CSS_SELECTOR, ".wants-card__price")

                title = title_element.text.strip()
                price_text = price_element.text.strip()
                price = int("".join(filter(str.isdigit, price_text))) if price_text else 0

                # 🔹 Описание заказа
                try:
                    desc_element = element.find_element(By.CSS_SELECTOR, "div.want-card__description")
                    description = desc_element.text.strip()
                except NoSuchElementException:
                    description = "Нет описания"

                # 🔹 Ссылка на заказ
                try:
                    link = title_element.find_element(By.XPATH, "..").get_attribute("href")
                    if not link:
                        link = element.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
                except NoSuchElementException:
                    link = "Ссылка недоступна"

                if MIN_PRICE <= price <= MAX_PRICE:
                    orders.append(f"📌 *{title}*\n💰 {price} руб.\n📄 {description}\n🔗 [Ссылка]({link})\n\n")

            except StaleElementReferenceException:
                continue
            except Exception as e:
                print(f"Ошибка: {e}")

    except TimeoutException:
        print(f"⚠ Не удалось загрузить заказы для категории {CATEGORY}")

    driver.quit()
    return orders


# 🔹 Команда /start
@dp.message(Command("start"))
async def start(message: Message):
    await message.answer("Привет! Бот будет отправлять заказы с Kwork каждые 4 часа.\n\n"
                         "Ты можешь вручную запросить заказы командой /parse.")

    global chat_id
    chat_id = 7084242333  # Запоминаем ID чата
    print(f"Получен chat_id: {chat_id}")  # Для отладки


# 🔹 Команда /parse (ручной парсинг)
@dp.message(Command("parse"))
async def parse_kwork(message: Message):
    await message.answer("🔍 Ищу заказы, подожди немного...")

    orders = get_orders()

    if orders:
        for order in orders[:50]:  # 🔹 Ограничиваем 50 заказами
            await message.answer(order, parse_mode="Markdown", disable_web_page_preview=True)
        await message.answer(f"✅ Найдено {len(orders)} заказов.")
    else:
        await message.answer("⚠ Заказы не найдены.")


# 🔹 Фоновая задача: отправлять заказы каждые 4 часа
async def send_orders_every_4h():
    await asyncio.sleep(5)  # Подождем 5 секунд перед запуском (на всякий случай)
    while True:
        print("⏳ Парсим заказы...")
        orders = get_orders()

        if orders:
            for order in orders[:50]:  # 🔹 Ограничиваем 50 заказами
                await bot.send_message(chat_id, order, parse_mode="Markdown", disable_web_page_preview=True)
            await bot.send_message(chat_id, f"✅ Найдено {len(orders)} заказов.")
        else:
            await bot.send_message(chat_id, "⚠ Заказы не найдены.")

        print("✅ Отправка завершена, жду 4 часа...")
        await asyncio.sleep(14400)  # Ждём 4 часа (14400 секунд)


# 🔹 Основная функция запуска бота
async def main():
    asyncio.create_task(send_orders_every_4h())  # Запускаем фоновую задачу
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
