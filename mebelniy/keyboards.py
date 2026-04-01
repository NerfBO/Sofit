from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
    WebAppInfo
)
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from config import CATALOG_MINI_APP_URL


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    buttons = [
        "🛍️ Каталог товаров",
        "❓ Часто задаваемые вопросы",
        "📝 Оставить заявку",
        "🎨 Подобрать мебель",
        "💬 Связь с менеджером",
        "ℹ️ О магазине"
    ]
    for label in buttons:
        builder.add(KeyboardButton(text=label))
    builder.adjust(2, 2, 2)
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=False)


def catalog_keyboard() -> ReplyKeyboardMarkup:
    """Кнопка для открытия каталога с принудительной светлой темой"""
                                                        
                                                                     
    separator = "&" if "?" in CATALOG_MINI_APP_URL else "?"
    catalog_url = f"{CATALOG_MINI_APP_URL}{separator}forceTheme=light"
    
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(
        text="🛍️ Открыть каталог",
        web_app=WebAppInfo(url=catalog_url)
    ))
    builder.add(KeyboardButton(text="🏠 В главное меню"))
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=False)


def skip_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="⏭️ Пропустить", callback_data="skip"))
    builder.add(InlineKeyboardButton(text="🏠 В главное меню", callback_data="main_menu"))
    builder.adjust(1)
    return builder.as_markup()


def phone_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="📱 Отправить телефон", request_contact=True))
    builder.add(KeyboardButton(text="🏠 В главное меню"))
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


def confirmation_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="✅ Отправить заявку", callback_data="send_order"))
    builder.add(InlineKeyboardButton(text="🏠 В главное меню", callback_data="main_menu"))
    builder.adjust(1)
    return builder.as_markup()


def get_admin_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📢 Сделать рассылку", callback_data="admin_broadcast")],
            [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]
        ]
    )
    return keyboard


def get_broadcast_back_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]
        ]
    )
    return keyboard


def get_broadcast_confirm_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Подтвердить", callback_data="broadcast_confirm")],
            [InlineKeyboardButton(text="❌ Отменить", callback_data="broadcast_cancel")]
        ]
    )
    return keyboard


def consent_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для подтверждения согласия на обработку персональных данных"""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="✅ Подтвердить", callback_data="consent_confirm"))
    builder.adjust(1)
    return builder.as_markup()


def quiz_question_1_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для вопроса 1: Где планируете установить мебель"""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="🚿 Ванная комната", callback_data="quiz_room_bathroom"))
    builder.add(InlineKeyboardButton(text="🛏️ Спальня", callback_data="quiz_room_bedroom"))
    builder.add(InlineKeyboardButton(text="🍳 Кухня", callback_data="quiz_room_kitchen"))
    builder.add(InlineKeyboardButton(text="🛋️ Гостиная / кабинет", callback_data="quiz_room_living"))
    builder.add(InlineKeyboardButton(text="🏠 В главное меню", callback_data="main_menu"))
    builder.adjust(1)
    return builder.as_markup()


def quiz_question_2_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для вопроса 2: Стиль (для не-кухни)"""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="✨ Современный / минимализм", callback_data="quiz_style_modern"))
    builder.add(InlineKeyboardButton(text="🏛️ Классический", callback_data="quiz_style_classic"))
    builder.add(InlineKeyboardButton(text="🎨 Матовая / глянец", callback_data="quiz_style_enamel"))
    builder.add(InlineKeyboardButton(text="🏠 В главное меню", callback_data="main_menu"))
    builder.adjust(1)
    return builder.as_markup()


def quiz_question_2_kitchen_style_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для вопроса 2: Стиль кухни"""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="✨ Современная", callback_data="quiz_kitchen_style_modern"))
    builder.add(InlineKeyboardButton(text="🏛️ Классика", callback_data="quiz_kitchen_style_classic"))
    builder.add(InlineKeyboardButton(text="🎨 Минимализм", callback_data="quiz_kitchen_style_minimalism"))
    builder.add(InlineKeyboardButton(text="🏠 В главное меню", callback_data="main_menu"))
    builder.adjust(1)
    return builder.as_markup()


def quiz_question_3_material_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для вопроса 3: Материалы (для кухни)"""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="🎨 Эмаль", callback_data="quiz_material_enamel"))
    builder.add(InlineKeyboardButton(text="🪵 ЛДСП", callback_data="quiz_material_ldsp"))
    builder.add(InlineKeyboardButton(text="🔲 Пластик", callback_data="quiz_material_plastic"))
    builder.add(InlineKeyboardButton(text="🏠 В главное меню", callback_data="main_menu"))
    builder.adjust(1)
    return builder.as_markup()


def quiz_question_4_finish_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для вопроса 4: Матовая/глянец (для кухни)"""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="🔳 Матовая", callback_data="quiz_finish_matte"))
    builder.add(InlineKeyboardButton(text="✨ Глянец", callback_data="quiz_finish_glossy"))
    builder.add(InlineKeyboardButton(text="🏠 В главное меню", callback_data="main_menu"))
    builder.adjust(1)
    return builder.as_markup()


def quiz_question_3_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для вопроса 3: Тип мебели"""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="📦 Пенал", callback_data="quiz_type_penal"))
    builder.add(InlineKeyboardButton(text="🗄️ Тумба", callback_data="quiz_type_tumba"))
    builder.add(InlineKeyboardButton(text="📚 Комплект мебели", callback_data="quiz_type_set"))
    builder.add(InlineKeyboardButton(text="🪑 Комод", callback_data="quiz_type_komod"))
    builder.add(InlineKeyboardButton(text="🏠 В главное меню", callback_data="main_menu"))
    builder.adjust(1)
    return builder.as_markup()


def quiz_question_4_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для вопроса 4: Цена"""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="💰 До 10 000 руб.", callback_data="quiz_price_0_10k"))
    builder.add(InlineKeyboardButton(text="💵 10 000–20 000 руб.", callback_data="quiz_price_10_20k"))
    builder.add(InlineKeyboardButton(text="💶 20 000–30 000 руб.", callback_data="quiz_price_20_30k"))
    builder.add(InlineKeyboardButton(text="💷 30 000+ руб.", callback_data="quiz_price_30k_plus"))
    builder.add(InlineKeyboardButton(text="🏠 В главное меню", callback_data="main_menu"))
    builder.adjust(1)
    return builder.as_markup()


def quiz_question_5_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для вопроса 5: Функциональные особенности"""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="👆 Push-to-Open", callback_data="quiz_feature_push"))
    builder.add(InlineKeyboardButton(text="📥 С ящиками", callback_data="quiz_feature_drawers"))
    builder.add(InlineKeyboardButton(text="🧺 Для стиральной машины", callback_data="quiz_feature_washing"))
    builder.add(InlineKeyboardButton(text="📦 Комплекты", callback_data="quiz_feature_sets"))
    builder.add(InlineKeyboardButton(text="🏠 В главное меню", callback_data="main_menu"))
    builder.adjust(1)
    return builder.as_markup()


def quiz_results_navigation_keyboard(current_index: int, total: int) -> InlineKeyboardMarkup:
    """Клавиатура для навигации по результатам квиза"""
    builder = InlineKeyboardBuilder()
    
    if total > 1:
        if current_index > 0:
            builder.add(InlineKeyboardButton(text="◀️ Предыдущий", callback_data=f"quiz_prev_{current_index}"))
        if current_index < total - 1:
            builder.add(InlineKeyboardButton(text="Следующий ▶️", callback_data=f"quiz_next_{current_index}"))
        builder.adjust(2)
    
    builder.add(InlineKeyboardButton(text="📝 Оставить заявку", callback_data=f"quiz_order_{current_index}"))
    builder.add(InlineKeyboardButton(text="🏠 В главное меню", callback_data="main_menu"))
    
    return builder.as_markup()
