# modules/daily_words.py
import os
import logging
import re
import random
from aiogram import Router, Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from aiogram.enums import ParseMode

# --- Конфигурация ---
WORDS_FILE_PATH = os.getenv("PATH_TO_WORDS_FILE")

router = Router()
logger = logging.getLogger(__name__)

# --- Функции ---
def get_random_word() -> tuple[str]|None:
    """ Читает файл и возвращает случайное слово и его определение. """
    if not WORDS_FILE_PATH or not os.path.exists(WORDS_FILE_PATH):
        logger.error(f"Файл со словами не был найден: {WORDS_FILE_PATH}")
        return None

    try:
        with open(WORDS_FILE_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Шаблон для поиска: **слово** — определение
        pattern = re.compile(r'\*\*(.*?)\*\* — (.*)', re.MULTILINE)
        matches = pattern.findall(content)
        
        if not matches:
            logger.warning("В файле не найдено слов в указанном формате.")
            return None
        
        word, definition = random.choice(matches)
        return word.strip(), definition.strip()

    except Exception as e:
        logger.error(f"Ошибка при чтении файла со словами: {e}")
        return None

# --- Планировщик ---
async def send_daily_word(bot: Bot, user_id: int):
    """Отправляет ежедневное слово."""
    logger.info(f"Sending daily word to {user_id}")
    word_data = get_random_word()
    
    if word_data:
        word, definition = word_data
        message = (
            f"🧐 <b>Слово дня:</b> {word}\n\n"
            f"<b>Значение:</b> {definition}"
        )
        await bot.send_message(user_id, message, parse_mode=ParseMode.HTML)
    else:
        await bot.send_message(user_id, "Не смог найти новое слово на сегодня. Проверьте файл-источник.")

async def schedule_jobs(scheduler: AsyncIOScheduler, bot: Bot, user_id: int):
    # Ежедневное слово дня. По умолчанию в 14:00 (GMT+5)
    scheduler.add_job(
        send_daily_word,
        trigger=CronTrigger(hour=14, minute=0),
        args=[bot, user_id],
        id='daily_word_notification',
        replace_existing=True
    )
    logger.info("Задачи модуля 'daily_word' успешно запланированы.")