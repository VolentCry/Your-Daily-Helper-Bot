# modules/mood_tracker.py
import asyncio
import sqlite3
from datetime import datetime, timedelta
import os
import logging
import matplotlib.pyplot as plt
import seaborn as sns
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv
from keyboards.modules_inline import *
from databases.add_mood_to_db import *

# --- Конфигурация модуля ---
load_dotenv("config.env")
DB_PATH = "databases/mood_base.db"
CHARTS_PATH = "monthly_chart" # Папка для сохранения графиков
ADMIN_ID = int(os.getenv("ADMIN_ID"))

os.makedirs(CHARTS_PATH, exist_ok=True)
os.makedirs("databases", exist_ok=True)

router = Router()
logger = logging.getLogger(__name__)

# --- Функции для работы с базой данных ---




# --- Словари и палитры для настроений ---
# Сопоставление ID настроения с его названием и эмодзи
MOOD_MAP = {
    0: "Положительное 😊", 1: "Уставшее 😩", 2: "Грустное 😢", 3: "Злое 😠",
    4: "Восхитительное 🤩", 5: "Раздражённое 😖", 6: "Спокойное 🙂", 7: "Энергичное ⚡️",
    8: "Тревожное 😰", 9: "Воодушевлённое 🤯", 10: "Скучающее 🫠", 11: "Влюблённое 🥰",
    12: "Безразличное 🥱", 13: "Испуганное 😱", 14: "Гордое 😎", 15: "Завистливое 😒",
    16: "Растерянное 😓", 17: "Игривое 😏", 18: "Сосредоточенное 🤔", 19: "Болезненное 🤧"
}

MOOD_PALETTE = sns.color_palette("viridis", len(MOOD_MAP)).as_hex()

# --- Функция построения графика ---
def make_and_save_plot(period_name: str, moods_in_period: dict, year: str = ""):
    """Создает круговую диаграмму, сохраняет её в файл и возвращает путь."""
    if not moods_in_period:
        return None # Если данных нет, возвращаем None

    labels = [MOOD_MAP[mid] for mid in moods_in_period.keys()]
    sizes = list(moods_in_period.values())
    colors = [MOOD_PALETTE[mid] for mid in moods_in_period.keys()]
    
    plt.figure(figsize=(10, 8)) # Задаем размер изображения
    # Создаем диаграмму с процентами
    plt.pie(sizes, labels=[l.split(' ')[0] for l in labels], colors=colors, autopct='%1.1f%%', startangle=140)
    plt.title(f"График настроения за {period_name} {year}", fontsize=16) # Заголовок с годом
    plt.axis('equal') # Делаем диаграмму круглой
    plt.legend(labels, bbox_to_anchor=(1.05, 1), loc='upper left') # Выносим легенду за пределы диаграммы
    plt.tight_layout() # Оптимизируем расположение элементов
    
    filename = f"{ADMIN_ID}_plot_{period_name.replace(' ', '_')}.png"
    filepath = os.path.join(CHARTS_PATH, filename)
    plt.savefig(filepath, dpi=300, bbox_inches='tight') # Сохраняем в высоком разрешении
    plt.close() # Закрываем плоттер, чтобы избежать утечек памяти
    return filepath

# --- Обработчики (хендлеры) ---
@router.callback_query(F.data == "record_mood")
async def process_record_mood_callback(callback: CallbackQuery):
    """Обрабатывает нажатие на кнопку 'Запись настроения'."""
    await callback.message.edit_text(
        "Выбери какое у тебя сегодня настроение:",
        reply_markup=get_mood_selection_keyboard()
    )
    await callback.answer() # Отвечаем на колбэк, чтобы убрать "часики" на кнопке

@router.callback_query(F.data.startswith("mood_"))
async def process_mood_selection_callback(callback: CallbackQuery):
    """Обрабатывает выбор конкретного настроения."""
    mood_id = int(callback.data.split("_")[1])
    mood_text = MOOD_MAP.get(mood_id, "Неизвестное")

    add_mood_to_db(mood_id) # Сохраняем выбор в базу данных

    await callback.message.edit_text(
        f"Настроение '<b>{mood_text}</b>' записано!\nСпасибо! ✨",
        reply_markup=None # Убираем клавиатуру после выбора
    )
    await callback.answer(text=f"Записано: {mood_text}")
    logger.info(f"Admin {ADMIN_ID} recorded mood: {mood_text}")

    await asyncio.sleep(2) # Небольшая пауза
    # Возвращаем пользователя в главное меню
    await callback.message.answer(
        "Что дальше?",
        reply_markup=get_main_menu_keyboard()
    )

@router.callback_query(F.data.in_(["plot_of_mood", "plot_back"]))
async def show_plot_period_selection(callback: CallbackQuery):
    """Показывает меню выбора периода для графика."""
    keyboard = get_plot_period_keyboard()
    if not keyboard.inline_keyboard:
        await callback.message.edit_text(
            "У вас пока нет записей настроения. Сначала сделайте несколько записей!",
            reply_markup=get_main_menu_keyboard()
        )
    else:
        await callback.message.edit_text(
            "Выберите период для просмотра статистики:",
            reply_markup=keyboard
        )
    await callback.answer()
    
@router.callback_query(F.data.startswith("plot_page_"))
async def handle_plot_pagination(callback: CallbackQuery):
    """Обрабатывает нажатия на кнопки пагинации."""
    page = int(callback.data.split("_")[2])
    keyboard = get_plot_period_keyboard(page)
    await callback.message.edit_text(
        "Выберите период для просмотра статистики:",
        reply_markup=keyboard
    )
    await callback.answer()

@router.callback_query(F.data.startswith("plot_"))
async def show_selected_plot(callback: CallbackQuery):
    """Генерирует и отправляет график за выбранный период."""
    await callback.answer("Генерирую график...") # Уведомляем пользователя
    period_type = callback.data.split("_")[1]
    
    all_moods = get_moods_from_db()
    mood_counts = {}
    period_name = ""
    year = ""

    # Логика для месячного отчета
    if period_type == "month":
        year_month = callback.data.split("_")[2] # "ГГГГ-ММ"
        year, month_num_str = year_month.split('-')
        months_list_ru = ["Январь", 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']
        period_name = months_list_ru[int(month_num_str) - 1]
        
        # Фильтруем записи по выбранному месяцу
        filtered_moods = [m for m in all_moods if m[0].startswith(year_month)]
        for _, mood_id in filtered_moods:
            mood_counts[mood_id] = mood_counts.get(mood_id, 0) + 1
            
    # Логика для недельного отчета
    elif period_type == "week":
        period_name = "последнюю неделю"
        today = datetime.now()
        last_week_start = today - timedelta(days=7)
        
        # Фильтруем записи за последние 7 дней
        filtered_moods = [
            m for m in all_moods 
            if last_week_start <= datetime.strptime(m[0], '%Y-%m-%d %H:%M:%S') <= today
        ]
        for _, mood_id in filtered_moods:
            mood_counts[mood_id] = mood_counts.get(mood_id, 0) + 1
    
    path_to_plot = make_and_save_plot(period_name, mood_counts, year)
    
    if path_to_plot:
        photo = FSInputFile(path_to_plot)
        # Отправляем график как фото
        await callback.message.answer_photo(
            photo=photo,
            caption=f"Вот ваша диаграмма за <b>{period_name} {year}</b>",
            reply_markup=get_main_menu_keyboard()
        )
        await callback.message.delete() # Удаляем старое сообщение с кнопками
    else:
        await callback.message.edit_text(
            f"Нет данных для построения графика за <b>{period_name} {year}</b>.",
            reply_markup=get_main_menu_keyboard()
        )

# --- Запланированные отчеты ---
async def send_weekly_report(bot: Bot, user_id: int):
    """Готовит и отправляет еженедельный отчет."""
    logger.info("Генерация еженедельного эмоционального отчета.")
    all_moods = get_moods_from_db()
    mood_counts = {}
    
    today = datetime.now()
    last_week_start = today - timedelta(days=7)
    
    # Собираем данные за последнюю неделю
    filtered_moods = [
        m for m in all_moods 
        if last_week_start <= datetime.strptime(m[0], '%Y-%m-%d %H:%M:%S') <= today
    ]
    for _, mood_id in filtered_moods:
        mood_counts[mood_id] = mood_counts.get(mood_id, 0) + 1
        
    path_to_plot = make_and_save_plot("недельный отчёт", mood_counts)
    
    if path_to_plot:
        photo = FSInputFile(path_to_plot)
        await bot.send_message(user_id, "💌 <b>Ваш еженедельный эмоциональный отчёт:</b>")
        await bot.send_photo(
            chat_id=user_id,
            photo=photo,
            caption="Настроение за прошедшую неделю."
        )
    else:
        await bot.send_message(user_id, "💌 Недостаточно данных для еженедельного отчёта.")

async def send_monthly_heatmap(bot: Bot, user_id: int):
    """Готовит и отправляет ежемесячный отчет (heatmap)."""
    # Реализация heatmap - сложная задача. Пока что отправляем заглушку.
    logger.info("Генерация ежемесячного отчета (heatmap).")
    await bot.send_message(
        user_id,
        "🗓️ <b>Ваш ежемесячный отчёт (heatmap)</b>\n\n"
        "<i>(Функция генерации heatmap в разработке. Скоро здесь будет красивая визуализация!)</i>"
    )

async def schedule_jobs(scheduler: AsyncIOScheduler, bot: Bot, user_id: int):
    """Добавляет задачи по отчетам в планировщик."""
    # Еженедельный отчет каждое воскресенье в 19:00 (GMT+5)
    scheduler.add_job(
        send_weekly_report,
        trigger=CronTrigger(day_of_week='sun', hour=19, minute=0),
        args=[bot, user_id],
        id='weekly_mood_report',
        replace_existing=True
    )
    # Ежемесячный отчет в последний день месяца в 19:00 (GMT+5)
    scheduler.add_job(
        send_monthly_heatmap,
        trigger=CronTrigger(day='last', hour=19, minute=0),
        args=[bot, user_id],
        id='monthly_mood_report',
        replace_existing=True
    )
    logger.info("Задачи модуля 'mood_tracker' успешно запланированы.")