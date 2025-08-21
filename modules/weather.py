# modules/weather.py
import os
import logging
import requests

from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# --- Конфигурация ---
YANDEX_API_KEY = os.getenv("YANDEX_WEATHER_API_KEY")
YANDEX_WEATHER_API_KEY="62061bd3-0025-4be3-99f3-210ca881e8c5"

# Координаты для прогноза (по умолчанию Пемрь)
LATITUDE = 58.010455
LONGITUDE = 56.229443

router = Router()
logger = logging.getLogger(__name__)

# --- Функции ---
def get_weather_forecast():
    """Получает данные о погоде с API Яндекс.Погоды."""
    if not YANDEX_API_KEY:
        logger.error("Yandex Weather API key is not set.")
        return None
    
    url = f"https://api.weather.yandex.ru/v2/forecast?lat={LATITUDE}&lon={LONGITUDE}&lang=ru_RU"
    headers = {"X-Yandex-API-Key": YANDEX_API_KEY}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Проверка на ошибки HTTP
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при получении данных погоды: {e}")
        return None

def format_weather_message(data: dict) -> str:
    """Форматирует данные о погоде в читаемое сообщение и дает рекомендации."""
    if not data:
        return "Не удалось получить прогноз погоды. 😔"

    fact = data['fact']

    temp = fact['temp']
    feels_like = fact['feels_like']
    condition = fact['condition']
    wind_speed = fact['wind_speed']
    prec_type = fact['prec_type']
    
    conditions = {
        'clear': 'ясно ☀️', 'partly-cloudy': 'малооблачно 🌤️',
        'cloudy': 'облачно с прояснениями 🌥️', 'overcast': 'пасмурно ☁️',
        'drizzle': 'морось 💧', 'light-rain': 'небольшой дождь 🌦️',
        'rain': 'дождь 🌧️', 'moderate-rain': 'умеренно сильный дождь 🌧️',
        'heavy-rain': 'сильный дождь 🌧️', 'continuous-heavy-rain': 'длительный сильный дождь 🌧️',
        'showers': 'ливень ⛈️', 'wet-snow': 'дождь со снегом 🌨️',
        'light-snow': 'небольшой снег ❄️', 'snow': 'снег ❄️',
        'snow-showers': 'снегопад 🌨️', 'hail': 'град 🌨️', 'thunderstorm': 'гроза 🌩️',
        'thunderstorm-with-rain': 'дождь с грозой ⛈️', 'thunderstorm-with-hail': 'гроза с градом ⛈️'
    }
    
    # Рекомендации по одежде
    clothing_advice = ""
    if feels_like > 25:
        clothing_advice = "Очень жарко. Наденьте что-то лёгкое: шорты, футболку, сандалии."
    elif 18 <= feels_like <= 25:
        clothing_advice = "Тепло. Футболка и джинсы или лёгкое платье будут в самый раз."
    elif 10 <= feels_like < 18:
        clothing_advice = "Прохладно. Стоит накинуть лёгкую куртку, ветровку или свитер."
    elif 0 <= feels_like < 10:
        clothing_advice = "Холодно. Наденьте тёплую куртку или пальто, шапку и перчатки."
    else:
        clothing_advice = "Очень холодно! Одевайтесь как можно теплее: пуховик, шапка, шарф, варежки."

    if prec_type > 0 and 'rain' in conditions.get(condition, ''):
        clothing_advice += "\nНе забудьте взять зонт! ☔️"
    elif prec_type > 0 and 'snow' in conditions.get(condition, ''):
        clothing_advice += "\nНа дорогах может быть скользко."

    message = (
        f"<b>Доброе утро! Прогноз погоды на сегодня:</b>\n\n"
        f"🌡️ Температура: <b>{temp}°C</b> (ощущается как {feels_like}°C)\n"
        f"📝 Состояние: {conditions.get(condition, condition)}\n"
        f"💨 Ветер: {wind_speed} м/с\n\n"
        f"👕 <b>Совет по одежде:</b>\n{clothing_advice}"
    )
    return message


@router.message(Command("weather"))
async def send_weather_now(message: Message):
    await message.answer("🔍 Узнаю прогноз погоды...")
    weather_data = get_weather_forecast()
    response_message = format_weather_message(weather_data)
    await message.answer(response_message)

# --- Планировщик ---
async def send_daily_weather(bot: Bot, user_id: int):
    """Отправляет ежедневный прогноз погоды."""
    logger.info(f"Sending daily weather to {user_id}")
    weather_data = get_weather_forecast()
    response_message = format_weather_message(weather_data)
    await bot.send_message(user_id, response_message)

async def schedule_jobs(scheduler: AsyncIOScheduler, bot: Bot, user_id: int):
    # Ежедневное уведомление о погоде в 08:30 (GMT+5) по умолчанию
    scheduler.add_job(
        send_daily_weather,
        trigger=CronTrigger(hour=8, minute=30),
        args=[bot, user_id],
        id='daily_weather_notification',
        replace_existing=True
    )
    logger.info("Задачи модуля 'weather' успешно запланированы.")