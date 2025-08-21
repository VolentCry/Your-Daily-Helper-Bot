import os
import logging
import re
import random
from aiogram.enums import ParseMode
from aiogram import Router, Bot
from aiogram.types import Message
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# --- Конфигурация ---
QUOTES_FILE_PATH = os.getenv("PATH_TO_QUOTES_FILE")

router = Router()
logger = logging.getLogger(__name__)

# --- Функции ---
def get_random_quote() -> list[str]|None:
    """ Читает файл и возвращает случайную цитату и её автора/источник. """
    if not QUOTES_FILE_PATH or not os.path.exists(QUOTES_FILE_PATH):
        logger.error(f"Файл с цитатами не найден по указанному пути: {QUOTES_FILE_PATH}")
        return None

    try:
        with open(QUOTES_FILE_PATH, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Шаблон для парсинга цитат
        # 1. (текст цитаты) *(необязательная часть с автором/источником)*
        pattern = re.compile(r'^\d+\.\s+(.*?)(?:\s+\*\((.*)\)\*)?$', re.MULTILINE)
        
        quotes = []
        for line in lines:
            match = pattern.match(line.strip())
            if match:
                quote_text = match.group(1).strip()
                source = match.group(2).strip() if match.group(2) else None
                quotes.append((quote_text, source))

        if not quotes:
            logger.warning("Цитаты в указанном формате в файле не найдены..")
            return None
        
        return random.choice(quotes)

    except Exception as e:
        logger.error(f"Ошибка чтения или анализа файла с цитатами: {e}")
        return None

# --- Планировщик ---
async def send_daily_quote(bot: Bot, user_id: int):
    """ Отправляет ежедневную цитату. """
    logger.info(f"Sending daily quote to {user_id}")
    quote_data = get_random_quote()
    
    if quote_data:
        quote, source = quote_data
        message = f"<i>«{quote}»</i>"
        if source:
            message += f"\n\n— {source}"
            
        await bot.send_message(user_id, message, parse_mode=ParseMode.HTML)
    else:
        await bot.send_message(user_id, "Не смог найти цитату на сегодня. Проверьте файл-источник.")

async def schedule_jobs(scheduler: AsyncIOScheduler, bot: Bot, user_id: int):
    # Ежедневная цитата. По умолчанию в 16:00 (GMT+5)
    scheduler.add_job(
        send_daily_quote,
        trigger=CronTrigger(hour=16, minute=0),
        args=[bot, user_id],
        id='daily_quote_notification',
        replace_existing=True
    )
    logger.info("Задачи модуля 'daily_quotation' успешно запланированы.")