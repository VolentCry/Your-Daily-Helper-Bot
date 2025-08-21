# main.py
import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart, Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message
from aiogram.client.default import DefaultBotProperties
from apscheduler.schedulers.asyncio import AsyncIOScheduler
# Импортируем все модули
from modules import mood_tracker, weather, daily_words, daily_quotation

# --- Конфигурация и Логирование ---
BOT_TOKEN = os.getenv("TOKEN")
# Убедимся, что ADMIN_ID читается как число
ADMIN_ID = int(os.getenv("ADMIN_ID"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Основная логика бота ---
async def main():
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode='HTML'))
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    # Устанавливаем часовой пояс для планировщика (Екатеринбург, GMT+5)
    scheduler = AsyncIOScheduler(timezone="Asia/Yekaterinburg")

    # --- Подключаем роутеры из всех модулей ---
    dp.include_router(mood_tracker.router)
    dp.include_router(weather.router)
    dp.include_router(daily_words.router)
    dp.include_router(daily_quotation.router)

    @dp.message(CommandStart())
    async def send_welcome(message: Message):
        if message.from_user.id == ADMIN_ID:
            await message.answer(
                f"👋 Привет, {message.from_user.full_name}!\n"
                "Я твой личный помощник. Чем могу помочь?",
                reply_markup=mood_tracker.get_main_menu_keyboard())
        else:
            await bot.send_message(message.from_user.id, "⛔️ У вас нет прав, чтобы пользоваться этим ботом.")
        
    @dp.message(Command("menu"))
    async def command_menu(message: Message):
        await message.answer(
            "Меню:",
            reply_markup=mood_tracker.get_main_menu_keyboard()
        )

    # --- Запуск планировщика и бота ---
    try:
        # Загружаем и планируем задачи из всех модулей
        await mood_tracker.schedule_jobs(scheduler, bot, ADMIN_ID)
        await weather.schedule_jobs(scheduler, bot, ADMIN_ID)
        await daily_words.schedule_jobs(scheduler, bot, ADMIN_ID)
        await daily_quotation.schedule_jobs(scheduler, bot, ADMIN_ID)
        
        scheduler.start()
        logger.info("Задчаи запущены успешно.")
        
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Бот начал работу...")
        await dp.start_polling(bot)

    except Exception as e:
        logger.error(f"Возникла ошибка при старте бота и запуске планировщика {e}.")
    finally:
        logger.info("Бот отключен.")
        await bot.session.close()


if __name__ == '__main__':
    asyncio.run(main())