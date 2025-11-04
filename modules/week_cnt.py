import os
import logging
import re
import random
from aiogram.enums import ParseMode
from aiogram import Router, Bot
from aiogram.types import Message, CallbackQuery
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, date, timedelta
from aiogram.filters import Command
from keyboards.modules_inline import get_main_menu_keyboard

# --- Конфигурация ---
QUOTES_FILE_PATH = os.getenv("PATH_TO_QUOTES_FILE")

router = Router()
logger = logging.getLogger(__name__)



def _get_september_start_reference(today: date) -> date:
    """Возвращает дату 1 сентября текущего учебного года.
    Если сейчас до сентября (январь-август), берём 1 сентября прошлого года.
    """
    year = today.year if today.month >= 9 else today.year - 1
    return date(year, 9, 1)


def _compute_week_number_from_september(today: date) -> int:
    """Вычисляет номер недели, считая с 1 сентября как с начала 1-й недели.
    Недели считаются простыми 7-дневными интервалами: [1–7] -> неделя 1, [8–14] -> 2 и т.д.
    """
    start = _get_september_start_reference(today)
    delta_days = (today - start).days
    return (delta_days // 7) + 1


def _format_week_message(today: date) -> str:
    start = _get_september_start_reference(today)
    week_num = _compute_week_number_from_september(today)
    parity = "чётная" if (week_num % 2 == 0) else "нечётная"
    return (
        f"Сегодня: {today.strftime('%d.%m.%Y')}\n"
        f"Сейчас идёт <b>{week_num}</b> неделя (" + parity + ") с 1 сентября {start.year}."
    )


@router.message(Command("week"))
async def handle_week_command(message: Message):
    """Команда /week: выводит номер текущей недели и её чётность."""
    today = datetime.now().date()
    text = _format_week_message(today)
    await message.answer(text, reply_markup=get_main_menu_keyboard())


@router.callback_query(lambda c: c.data == "week_cnt")
async def handle_week_button(callback: CallbackQuery):
    """Инлайн-кнопка в меню: показывает номер недели и чётность."""
    today = datetime.now().date()
    text = _format_week_message(today)
    await callback.message.answer(text, reply_markup=get_main_menu_keyboard())
    await callback.answer()