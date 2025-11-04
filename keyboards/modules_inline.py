from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from databases.add_mood_to_db import get_moods_from_db

MOOD_MAP = {
    0: "Положительное 😊", 1: "Уставшее 😩", 2: "Грустное 😢", 3: "Злое 😠",
    4: "Восхитительное 🤩", 5: "Раздражённое 😖", 6: "Спокойное 🙂", 7: "Энергичное ⚡️",
    8: "Тревожное 😰", 9: "Воодушевлённое 🤯", 10: "Скучающее 🫠", 11: "Влюблённое 🥰",
    12: "Безразличное 🥱", 13: "Испуганное 😱", 14: "Гордое 😎", 15: "Завистливое 😒",
    16: "Растерянное 😓", 17: "Игривое 😏", 18: "Сосредоточенное 🤔", 19: "Болезненное 🤧"
}

def get_main_menu_keyboard():
    """Возвращает инлайн-клавиатуру главного меню."""
    buttons = [
        [InlineKeyboardButton(text="📝 Запись настроения", callback_data="record_mood")],
        [InlineKeyboardButton(text="📈 График настроения", callback_data="plot_of_mood")],
        [InlineKeyboardButton(text="📅 Номер недели", callback_data="week_cnt")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_mood_selection_keyboard():
    """Возвращает инлайн-клавиатуру для выбора настроения (2 кнопки в ряд)."""
    buttons = [
        [InlineKeyboardButton(text=mood_name, callback_data=f"mood_{mood_id}")]
        for mood_id, mood_name in MOOD_MAP.items()
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_plot_period_keyboard(page=0):
    """Создает клавиатуру для выбора периода графика с пагинацией."""
    all_moods = get_moods_from_db()
    if not all_moods:
        return InlineKeyboardMarkup(inline_keyboard=[])

    # Получаем уникальные месяцы (в формате "ГГГГ-ММ") и сортируем их по убыванию
    months = sorted(list(set([record[0][:7] for record in all_moods])), reverse=True)
    
    # Создаем кнопки для каждого месяца
    month_buttons = []
    months_list_ru = ["Январь", 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']
    for ym in months:
        year, month_num = ym.split('-')
        month_name = months_list_ru[int(month_num) - 1]
        month_buttons.append(
            InlineKeyboardButton(text=f"{month_name} {year}", callback_data=f"plot_month_{ym}")
        )
    
    # Логика пагинации (разбиения кнопок на страницы)
    items_per_page = 4 # 4 месяца + 1 кнопка "неделя" = 5 кнопок на странице
    total_pages = (len(month_buttons) + items_per_page - 1) // items_per_page
    
    start = page * items_per_page
    end = start + items_per_page
    
    paginated_buttons = [month_buttons[i:i+1] for i in range(start, end) if i < len(month_buttons)]
    
    # Добавляем кнопку "Последняя неделя" только на первую страницу
    if page == 0:
        paginated_buttons.insert(0, [InlineKeyboardButton(text="Последняя неделя", callback_data="plot_week")])

    # Кнопки навигации "Вперед" и "Назад"
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="◀️ Назад", callback_data=f"plot_page_{page-1}"))
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton(text="Вперёд ▶️", callback_data=f"plot_page_{page+1}"))
    
    if nav_buttons:
        paginated_buttons.append(nav_buttons)
        
    return InlineKeyboardMarkup(inline_keyboard=paginated_buttons)