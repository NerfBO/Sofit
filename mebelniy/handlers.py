import asyncio
import json
import logging
from aiogram import Router, F
from aiogram.filters import CommandStart, Command 
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove, ContentType, InputMediaPhoto
from aiogram.fsm.context import FSMContext
from datetime import datetime
from collections import defaultdict, deque

from states import OrderForm, AdminStates, QuizForm, QuizOrderForm
from keyboards import (
    main_menu_keyboard, catalog_keyboard, skip_keyboard,
    phone_keyboard, confirmation_keyboard,
    get_admin_keyboard, get_broadcast_back_keyboard, get_broadcast_confirm_keyboard,
    consent_keyboard,
    quiz_question_1_keyboard, quiz_question_2_keyboard, quiz_question_3_keyboard,
    quiz_question_4_keyboard, quiz_question_5_keyboard,
    quiz_question_2_kitchen_style_keyboard, quiz_question_3_material_keyboard,
    quiz_question_4_finish_keyboard,
    quiz_results_navigation_keyboard
)
from validators import validate_name, validate_phone, format_phone, validate_measurements
from config import CONTACT_PHONE, CONTACT_EMAIL, ADMIN_CHAT_IDS, ADMIN_USER_IDS, SHOP_INFO
from storage import user_service_messages, save_user, get_all_users, is_user_registered

logger = logging.getLogger(__name__)

router = Router()
user_service_messages = defaultdict(lambda: deque(maxlen=11))


def is_admin(user_id: int) -> bool:
    """Проверка, является ли пользователь администратором"""
    return user_id in ADMIN_USER_IDS


async def check_registration(user_id: int) -> bool:
    """Проверка регистрации пользователя. Возвращает True, если зарегистрирован"""
    return await is_user_registered(user_id)


def load_products() -> list:
    """Загрузка товаров из JSON файла"""
    import os
    try:
                             
        paths = [
            'catalog_products.json',
            'beautybixbot/catalog_products.json',
            os.path.join(os.path.dirname(__file__), '..', 'catalog_products.json'),
            os.path.join(os.path.dirname(__file__), 'catalog_products.json')
        ]
        for path in paths:
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        logger.error("Файл catalog_products.json не найден")
        return []
    except Exception as e:
        logger.error(f"Ошибка загрузки товаров: {e}")
        return []


def filter_products_by_quiz(products: list, quiz_data: dict) -> list:
    """Фильтрация товаров на основе ответов квиза"""
    filtered = []
    
    room = quiz_data.get('room')
    is_kitchen = room == 'kitchen'
    
                                      
    if is_kitchen:
        kitchen_style = quiz_data.get('kitchen_style')
        material = quiz_data.get('material')
        finish = quiz_data.get('finish')
        price_range = quiz_data.get('price')
        features = quiz_data.get('features')
    else:
                                         
        style = quiz_data.get('style')
        furniture_type = quiz_data.get('type')
        price_range = quiz_data.get('price')
        features = quiz_data.get('features')
    
                                              
    room_keywords = {
        'bathroom': ['ванн', 'пенал', 'тумба подвесн', 'тумба для стирал', 'комплект для ванн', 'тумба подвесная', 'тумба под стирал'],
        'bedroom': ['прикроватн', 'комод', 'тумба прикроватн'],
        'kitchen': ['кухн', 'шкаф', 'кухонн'],
        'living': ['комод', 'шкаф', 'стол']
    }
    
                                    
    kitchen_style_keywords = {
        'modern': ['современн', 'модерн', 'бел', 'белый', 'белая'],
        'classic': ['классическ', 'классик', 'фрезеровк', 'дуб сонома', 'сонома'],
        'minimalism': ['минимализм', 'минималист', 'лаконичн', 'простой']
    }
    
                                         
    material_keywords = {
        'enamel': ['эмал', 'эмали', 'эмаль'],
        'ldsp': ['лдсп', 'лдсп', 'дсп'],
        'plastic': ['пластик', 'пластиков']
    }
    
                                      
    finish_keywords = {
        'matte': ['матов', 'матовой', 'матовый', 'матовые', 'шелков'],
        'glossy': ['глянец', 'глянцев', 'глянцевой', 'глянцевый', 'глянцевые', 'блеск']
    }
    
                                             
    style_keywords = {
        'modern': ['бел', 'лаконичн', 'минимализм', 'современн', 'arctica', 'белый', 'белая'],
        'classic': ['фрезеровк', 'дуб сонома', 'классическ', 'сонома'],
        'enamel': ['эмал', 'мдф', 'матов', 'шелков', 'матовой', 'эмали']
    }
    
                                                          
    type_keywords = {
        'penal': ['пенал'],
        'tumba': ['тумба'],
        'set': ['комплект'],
        'komod': ['комод']
    }
    
                   
    price_ranges = {
        '0_10k': (0, 10000),
        '10_20k': (10000, 20000),
        '20_30k': (20000, 30000),
        '30k_plus': (30000, float('inf'))
    }
    
                                
    feature_keywords = {
        'push': ['push-to-open', 'push', 'от нажатия'],
        'drawers': ['ящик', 'выдвижн', 'ящики'],
        'washing': ['стирал', 'стиральной'],
        'sets': ['комплект']
    }
    
    for product in products:
        name_lower = product.get('name', '').lower()
        description_lower = product.get('description', '').lower() if product.get('description') else ''
        text_lower = f"{name_lower} {description_lower}"
        
                           
        if room and room in room_keywords:
            if not any(kw in text_lower for kw in room_keywords[room]):
                continue
        
        if is_kitchen:
                               
            if kitchen_style and kitchen_style in kitchen_style_keywords:
                if not any(kw in text_lower for kw in kitchen_style_keywords[kitchen_style]):
                    continue
            
            if material and material in material_keywords:
                if not any(kw in text_lower for kw in material_keywords[material]):
                    continue
            
            if finish and finish in finish_keywords:
                if not any(kw in text_lower for kw in finish_keywords[finish]):
                    continue
        else:
                                  
            if style and style in style_keywords:
                if not any(kw in text_lower for kw in style_keywords[style]):
                    continue
            
            if furniture_type and furniture_type in type_keywords:
                if not any(kw in text_lower for kw in type_keywords[furniture_type]):
                    continue
        
                                   
        if price_range and price_range in price_ranges:
            price_str = product.get('price', '0')
            try:
                cleaned = price_str.replace(' ', '').replace('р.', '').replace('р', '').replace('.', '')
                digits = ''.join(filter(str.isdigit, cleaned))
                if digits:
                    price_value = int(digits)
                    min_price, max_price = price_ranges[price_range]
                    if not (min_price <= price_value < max_price):
                        continue 
                else:
                    continue 
            except (ValueError, IndexError, TypeError) as e:
                logger.debug(f"Ошибка парсинга цены '{product.get('price')}': {e}")
                continue
        
                                                    
        if features and features in feature_keywords:
            if not any(kw in text_lower for kw in feature_keywords[features]):
                continue
        
        filtered.append(product)
    
    return filtered



@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()

    user_id = message.from_user.id
    
    await save_user(
        telegram_user_id=user_id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name
    )
    
    if not await is_user_registered(user_id):
                                                   
        consent_text = """
Добрый день, это магазин Софит 🏠!

Мы рады помочь вам выбрать мебель и получить всю необходимую информацию.

Для продолжения работы с ботом необходимо:
1. Подтвердить согласие на обработку персональных данных
2. Пройти регистрацию, указав ваш номер телефона

📋 <b>Согласие на обработку персональных данных</b>
В соответствии с Федеральным законом № 152-ФЗ «О персональных данных» от 27.07.2006 г., подтверждая согласие, вы даете разрешение на обработку ваших персональных данных для предоставления услуг магазина мебели Софит.

Нажмите кнопку ниже, чтобы подтвердить согласие:
        """
        msg = await message.answer(consent_text, reply_markup=consent_keyboard(), parse_mode="HTML")
        user_service_messages[user_id].append(msg.message_id)
        return

                                                      
    welcome_text = f"""
🏠 Привет, <b>{message.from_user.first_name}</b>!

Добро пожаловать в <b>Софит</b> — магазин корпусной мебели!

✨ Мы производим качественную мебель напрямую в г. Уфа и предлагаем лучшие решения для вашего дома.

👇 Выберите нужный раздел в меню ниже:
    """

    msg = await message.answer(welcome_text, reply_markup=main_menu_keyboard(), parse_mode="HTML")
    user_service_messages[user_id].append(msg.message_id)


@router.message(Command("help"))
async def cmd_help(message: Message, state: FSMContext):
    await state.clear()
    
    user_id = message.from_user.id
    
                           
    if not await is_user_registered(user_id):
        await message.answer("❌ Для использования бота необходимо подтвердить согласие на обработку персональных данных. Используйте команду /start")
        return
    
    help_text = f"""
<b>📖 Справка по боту Софит</b>

Я помогу вам выбрать и заказать мебель для вашего дома.

<b>🧭 Доступные команды:</b>
• <code>/start</code> — Вернуться в главное меню  
• <code>/help</code> — Показать эту справку

<b>🛍️ Функциональность:</b>
• Просмотреть каталог товаров 🛍️  
• Узнать ответы на частые вопросы ❓  
• Оставить заявку📝  
• Подобрать мебель 🎨  
• Связаться с менеджером 💬  
• Узнать о магазине ℹ️

<b>📞 Связаться с нами:</b>
• Телефон: {CONTACT_PHONE}
• Email: {CONTACT_EMAIL}

💡 <i>Подсказка:</i> вы всегда можете вернуться в меню, нажав «🏠 В главное меню»
    """
    msg = await message.answer(help_text, reply_markup=main_menu_keyboard(), parse_mode="HTML")
    user_service_messages[user_id].append(msg.message_id)


@router.callback_query(F.data == "consent_confirm")
async def handle_consent_confirm(callback: CallbackQuery, state: FSMContext):
    """Обработчик подтверждения согласия на обработку персональных данных"""
    await state.clear()
    
    user_id = callback.from_user.id
    
                                        
    await save_user(
        telegram_user_id=user_id,
        username=callback.from_user.username,
        first_name=callback.from_user.first_name,
        last_name=callback.from_user.last_name,
        consent=True
    )
    
                                   
    try:
        await callback.message.delete()
    except Exception as e:
        logger.error(f"Ошибка удаления сообщения: {e}")
    
                            
    welcome_text = f"""
✅ <b>Согласие подтверждено!</b>

🏠 Привет, <b>{callback.from_user.first_name}</b>!

Добро пожаловать в <b>Софит</b> — магазин корпусной мебели!

✨ Мы производим качественную мебель напрямую в г. Уфа и предлагаем лучшие решения для вашего дома.

👇 Выберите нужный раздел в меню ниже:
    """
    
    msg = await callback.message.answer(welcome_text, reply_markup=main_menu_keyboard(), parse_mode="HTML")
    user_service_messages[user_id].append(msg.message_id)
    await callback.answer("✅ Согласие подтверждено!")


@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext):
    """Команда для доступа к админ-панели"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к админ-панели.")
        return
    
    await state.clear()
    admin_text = (
        "🔐 *Админ-панель*\n\n"
        "Выберите действие:"
    )
    
    await message.answer(
        admin_text,
        parse_mode="Markdown",
        reply_markup=get_admin_keyboard()
    )


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    """Отмена текущей операции"""
    current_state = await state.get_state()
    
    if current_state == AdminStates.waiting_for_broadcast:
        await state.clear()
        await message.answer(
            "❌ Рассылка отменена.",
            reply_markup=ReplyKeyboardRemove()
        )
    elif current_state in [OrderForm.waiting_for_measurements, OrderForm.waiting_for_name, 
                          OrderForm.waiting_for_phone, OrderForm.waiting_for_photo]:
        await state.clear()
        await message.answer("❌ Заявка отменена.", reply_markup=main_menu_keyboard())
    elif current_state in [QuizForm.question_1_room, QuizForm.question_2_style, 
                          QuizForm.question_2_kitchen_style, QuizForm.question_3_type,
                          QuizForm.question_3_material, QuizForm.question_4_finish,
                          QuizForm.question_4_price, QuizForm.question_5_features, 
                          QuizForm.viewing_results]:
        await state.clear()
        await message.answer("❌ Квиз отменен.", reply_markup=main_menu_keyboard())
    elif current_state in [QuizOrderForm.waiting_for_name, QuizOrderForm.waiting_for_phone, QuizOrderForm.confirmation]:
        await state.clear()
        await message.answer("❌ Заявка отменена.", reply_markup=main_menu_keyboard())
    else:
        await message.answer("Нет активной операции для отмены.")


@router.message(F.text == "🏠 В главное меню")
@router.callback_query(F.data == "main_menu")
async def go_home(update, state: FSMContext):
    await state.clear()
    
    if isinstance(update, Message):
        msg = await update.answer("🏠 Главное меню", reply_markup=main_menu_keyboard())
        user_service_messages[update.from_user.id].append(msg.message_id)
    else:
        await update.message.edit_text("🏠 Главное меню", reply_markup=None)
        msg1 = await update.message.answer("Выберите действие:", reply_markup=main_menu_keyboard())
        await update.answer()
        user_service_messages[update.from_user.id].append(msg1.message_id)



@router.message(F.text == "🛍️ Каталог товаров")
async def show_catalog(message: Message):
    if not await check_registration(message.from_user.id):
        await message.answer("❌ Для использования бота необходимо подтвердить согласие на обработку персональных данных. Используйте команду /start")
        return
    
    catalog_text = """
🛍️ <b>Каталог товаров</b>

Нажмите на кнопку ниже, чтобы открыть каталог в Mini App:
    """
    msg = await message.answer(catalog_text, reply_markup=catalog_keyboard(), parse_mode="HTML")
    user_service_messages[message.from_user.id].append(msg.message_id)


@router.message(F.text == "❓ Часто задаваемые вопросы")
async def show_faq(message: Message):
    if not await check_registration(message.from_user.id):
        await message.answer(
            "❌ Для использования бота необходимо подтвердить согласие на обработку персональных данных. Используйте команду /start"
        )
        return

    faq_text = """
❓ Как посмотреть ассортимент?
Вы можете просматривать каталог товаров на сайте, если понадобится помощь можно связаться с менеджером по телефону или через мессенджер.

❓ Как я могу заказать товар?
Добавьте в корзину, заполните контактные данные или свяжитесь с нами напрямую по телефону/почте для уточнения заказа.

📏 Индивидуальные заказы

❓ Можно ли заказать мебель по моим размерам?
Да — мы можем изготовить наши позиции под нужный для Вас размер (указать ширину и глубину) срок и стоимость увеличится.

💰 Оплата, цены и условия

❓ Какие способы оплаты вы принимаете?
Оплату можно осуществить любым удобным для Вас способом, от оплаты наличными или по карте на нашем производстве, до безналичного с организации, для удобства, можно сразу добавить в корзину и оплатить.

❓ Есть ли рассрочка или специальные условия?
Да, возможна рассрочка — уточняйте подробности у менеджера.

🛡️ Гарантии и сервис

❓ Даёте ли вы гарантию на мебель?
Гарантия на мебель и фурнитуру предоставляется — на два года.

🚚 Доставка и установка

❓ Вы осуществляете доставку?
Да, мы доставляем мебель по Уфе бесплатно. Отправляем любой ТК в другие регионы, в надежной упаковке.

❓ Могу ли я заказать сборку/монтаж?
Да — доставка, монтаж и установка доступны. Наши специалисты собирают мебель аккуратно и профессионально.
"""

    msg = await message.answer(faq_text, reply_markup=main_menu_keyboard())
    user_service_messages[message.from_user.id].append(msg.message_id)

@router.message(F.text == "🎨 Подобрать мебель")
async def show_quiz(message: Message, state: FSMContext):
    if not await check_registration(message.from_user.id):
        await message.answer("❌ Для использования бота необходимо подтвердить согласие на обработку персональных данных. Используйте команду /start")
        return
    
    await state.clear()
    await state.set_state(QuizForm.question_1_room)
    
    quiz_text = """🎨 <b>Подбор мебели</b>

Поможем подобрать идеальную мебель для вашего дома!

<b>Вопрос 1:</b> Где вы планируете установить мебель?"""
    
    msg = await message.answer(quiz_text, reply_markup=quiz_question_1_keyboard(), parse_mode="HTML")
    user_service_messages[message.from_user.id].append(msg.message_id)

@router.callback_query(F.data.startswith("quiz_room_"), QuizForm.question_1_room)
async def handle_quiz_question_1(callback: CallbackQuery, state: FSMContext):
    room = callback.data.replace("quiz_room_", "")
    room_names = {
        'bathroom': '🚿 Ванная комната',
        'bedroom': '🛏️ Спальня',
        'kitchen': '🍳 Кухня',
        'living': '🛋️ Гостиная / кабинет'
    }
    
    await state.update_data(room=room)
    await callback.answer()
    
                                                      
    if room == 'kitchen':
        await callback.message.edit_text(
            f"""🎨 <b>Подбор мебели</b>

✅ Выбрано: {room_names.get(room, room)}

<b>Вопрос 2 из 6:</b> Какой стиль кухни вам нравится?""",
            reply_markup=quiz_question_2_kitchen_style_keyboard(),
            parse_mode="HTML"
        )
        await state.set_state(QuizForm.question_2_kitchen_style)
    else:
                                             
        await callback.message.edit_text(
            f"""🎨 <b>Подбор мебели</b>

✅ Выбрано: {room_names.get(room, room)}

<b>Вопрос 2 из 5:</b> Какой стиль вам нравится?""",
            reply_markup=quiz_question_2_keyboard(),
            parse_mode="HTML"
        )
        await state.set_state(QuizForm.question_2_style)


@router.callback_query(F.data.startswith("quiz_style_"), QuizForm.question_2_style)
async def handle_quiz_question_2(callback: CallbackQuery, state: FSMContext):
    style = callback.data.replace("quiz_style_", "")
    style_names = {
        'modern': '✨ Современный / минимализм',
        'classic': '🏛️ Классический',
        'enamel': '🎨 Матовая / глянец'
    }
    
    data = await state.get_data()
    await state.update_data(style=style)
    await callback.answer()
    
    await callback.message.edit_text(
        f"""🎨 <b>Подбор мебели</b>

✅ Выбрано: {style_names.get(style, style)}

<b>Вопрос 3 из 5:</b> Какой тип мебели вам нужен?""",
        reply_markup=quiz_question_3_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(QuizForm.question_3_type)


@router.callback_query(F.data.startswith("quiz_kitchen_style_"), QuizForm.question_2_kitchen_style)
async def handle_quiz_question_2_kitchen_style(callback: CallbackQuery, state: FSMContext):
    """Обработчик вопроса 2 для кухни: стиль кухни"""
    style = callback.data.replace("quiz_kitchen_style_", "")
    style_names = {
        'modern': '✨ Современная',
        'classic': '🏛️ Классика',
        'minimalism': '🎨 Минимализм'
    }
    
    await state.update_data(kitchen_style=style)
    await callback.answer()
    
    await callback.message.edit_text(
        f"""🎨 <b>Подбор мебели</b>

✅ Выбрано: {style_names.get(style, style)}

<b>Вопрос 3 из 6:</b> Какой материал вам нравится?""",
        reply_markup=quiz_question_3_material_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(QuizForm.question_3_material)


@router.callback_query(F.data.startswith("quiz_material_"), QuizForm.question_3_material)
async def handle_quiz_question_3_material(callback: CallbackQuery, state: FSMContext):
    """Обработчик вопроса 3 для кухни: материалы"""
    material = callback.data.replace("quiz_material_", "")
    material_names = {
        'enamel': '🎨 Эмаль',
        'ldsp': '🪵 ЛДСП',
        'plastic': '🔲 Пластик'
    }
    
    await state.update_data(material=material)
    await callback.answer()
    
    await callback.message.edit_text(
        f"""🎨 <b>Подбор мебели</b>

✅ Выбрано: {material_names.get(material, material)}

<b>Вопрос 4 из 6:</b> Какая отделка вам нравится?""",
        reply_markup=quiz_question_4_finish_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(QuizForm.question_4_finish)


@router.callback_query(F.data.startswith("quiz_finish_"), QuizForm.question_4_finish)
async def handle_quiz_question_4_finish(callback: CallbackQuery, state: FSMContext):
    """Обработчик вопроса 4 для кухни: матовая/глянец"""
    finish = callback.data.replace("quiz_finish_", "")
    finish_names = {
        'matte': '🔳 Матовая',
        'glossy': '✨ Глянец'
    }
    
    await state.update_data(finish=finish)
    await callback.answer()
    
    await callback.message.edit_text(
        f"""🎨 <b>Подбор мебели</b>

✅ Выбрано: {finish_names.get(finish, finish)}

<b>Вопрос 5 из 6:</b> Предпочтения по цене""",
        reply_markup=quiz_question_4_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(QuizForm.question_4_price)


@router.callback_query(F.data.startswith("quiz_type_"), QuizForm.question_3_type)
async def handle_quiz_question_3(callback: CallbackQuery, state: FSMContext):
    furniture_type = callback.data.replace("quiz_type_", "")
    type_names = {
        'penal': '📦 Пенал',
        'tumba': '🗄️ Тумба',
        'set': '📚 Комплект мебели',
        'komod': '🪑 Комод'
    }
    
    await state.update_data(type=furniture_type)
    await callback.answer()

    await callback.message.edit_text(
        f"""🎨 <b>Подбор мебели</b>

✅ Выбрано: {type_names.get(furniture_type, furniture_type)}

<b>Вопрос 4 из 5:</b> Предпочтения по цене""",
        reply_markup=quiz_question_4_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(QuizForm.question_4_price)


@router.callback_query(F.data.startswith("quiz_price_"), QuizForm.question_4_price)
async def handle_quiz_question_4(callback: CallbackQuery, state: FSMContext):
    price_range = callback.data.replace("quiz_price_", "")
    price_names = {
        '0_10k': '💰 До 10 000 руб.',
        '10_20k': '💵 10 000–20 000 руб.',
        '20_30k': '💶 20 000–30 000 руб.',
        '30k_plus': '💷 30 000+ руб.'
    }
    
    data = await state.get_data()
    is_kitchen = data.get('room') == 'kitchen'
    
    await state.update_data(price=price_range)
    await callback.answer()
    
    if is_kitchen:
                                     
        await callback.message.edit_text(
            f"""🎨 <b>Подбор мебели</b>

✅ Выбрано: {price_names.get(price_range, price_range)}

<b>Вопрос 6 из 6:</b> Функциональные особенности""",
            reply_markup=quiz_question_5_keyboard(),
            parse_mode="HTML"
        )
    else:
                                             
        await callback.message.edit_text(
            f"""🎨 <b>Подбор мебели</b>

✅ Выбрано: {price_names.get(price_range, price_range)}

<b>Вопрос 5 из 5:</b> Функциональные особенности""",
            reply_markup=quiz_question_5_keyboard(),
            parse_mode="HTML"
        )
    await state.set_state(QuizForm.question_5_features)


async def show_quiz_product(product: dict, index: int, total: int, callback: CallbackQuery):
    """Показывает один товар из результатов квиза"""
    product_text = f"""🎨 <b>Результаты подбора</b>

Товар {index + 1} из {total}

<b>{product.get('name', 'Без названия')}</b>

💰 Цена: {product.get('price', 'Не указана')}

📝 {product.get('description', 'Описание отсутствует')[:500]}{'...' if len(product.get('description', '')) > 500 else ''}"""
    
    images = product.get('images', [])
    
    images = images[:10]
    
    if images:
        try:
            media_group = []
            for i, img_url in enumerate(images):
                if i == 0:
                    media_group.append(InputMediaPhoto(media=img_url, caption=product_text, parse_mode="HTML"))
                else:
                    media_group.append(InputMediaPhoto(media=img_url))
            
            await callback.message.answer_media_group(media=media_group)
            
            await callback.message.answer(
                f"Товар {index + 1} из {total}",
                reply_markup=quiz_results_navigation_keyboard(index, total)
            )
        except Exception as e:
            logger.error(f"Ошибка отправки медиа-группы: {e}")
            try:
                await callback.message.answer_photo(
                    photo=images[0],
                    caption=product_text,
                    parse_mode="HTML",
                    reply_markup=quiz_results_navigation_keyboard(index, total)
                )
            except Exception as e2:
                logger.error(f"Ошибка отправки фото: {e2}")
                await callback.message.answer(
                    product_text,
                    reply_markup=quiz_results_navigation_keyboard(index, total),
                    parse_mode="HTML"
                )
    else:
        await callback.message.answer(
            product_text,
            reply_markup=quiz_results_navigation_keyboard(index, total),
            parse_mode="HTML"
        )


@router.callback_query(F.data.startswith("quiz_feature_"), QuizForm.question_5_features)
async def handle_quiz_question_5(callback: CallbackQuery, state: FSMContext):
    features = callback.data.replace("quiz_feature_", "")
    feature_names = {
        'push': '👆 Push-to-Open',
        'drawers': '📥 С ящиками',
        'washing': '🧺 Для стиральной машины',
        'sets': '📦 Комплекты'
    }
    
    await state.update_data(features=features)
    await callback.answer("Ищем подходящие товары...")
    
    products = load_products()
    quiz_data = await state.get_data()
    
    logger.info(f"Данные квиза: {quiz_data}")
    logger.info(f"Всего товаров в каталоге: {len(products)}")
    
    filtered_products = filter_products_by_quiz(products, quiz_data)
    
    logger.info(f"Найдено товаров после фильтрации: {len(filtered_products)}")
    
    if not filtered_products:
        await callback.message.edit_text(
            """🎨 <b>Результаты подбора</b>

К сожалению, по вашим критериям не найдено подходящих товаров.

Попробуйте изменить параметры или свяжитесь с менеджером для индивидуального подбора!""",
            reply_markup=None,
            parse_mode="HTML"
        )
        await callback.message.answer(
            "Выберите действие:",
            reply_markup=main_menu_keyboard()
        )
        await state.clear()
        return

    await state.update_data(
        quiz_results=filtered_products,
        quiz_current_index=0
    )
    await state.set_state(QuizForm.viewing_results)
    
    try:
        await callback.message.delete()
    except Exception:
        pass
    
    await show_quiz_product(filtered_products[0], 0, len(filtered_products), callback)


@router.callback_query(F.data.startswith("quiz_prev_"))
async def handle_quiz_prev(callback: CallbackQuery, state: FSMContext):
    """Обработчик кнопки 'Предыдущий товар'"""
    data = await state.get_data()
    results = data.get('quiz_results', [])
    current_index = data.get('quiz_current_index', 0)
    
    if not results or current_index <= 0:
        await callback.answer("Это первый товар", show_alert=True)
        return
    
    new_index = current_index - 1
    await state.update_data(quiz_current_index=new_index)
    
    try:
        await callback.message.delete()
    except Exception as e:
        logger.error(f"Ошибка удаления сообщения: {e}")
    
    await callback.answer()
    await show_quiz_product(results[new_index], new_index, len(results), callback)


@router.callback_query(F.data.startswith("quiz_next_"))
async def handle_quiz_next(callback: CallbackQuery, state: FSMContext):
    """Обработчик кнопки 'Следующий товар'"""
    data = await state.get_data()
    results = data.get('quiz_results', [])
    current_index = data.get('quiz_current_index', 0)
    
    if not results or current_index >= len(results) - 1:
        await callback.answer("Это последний товар", show_alert=True)
        return
    
    new_index = current_index + 1
    await state.update_data(quiz_current_index=new_index)
    
    try:
        await callback.message.delete()
    except Exception as e:
        logger.error(f"Ошибка удаления сообщения: {e}")
    
    await callback.answer()
    await show_quiz_product(results[new_index], new_index, len(results), callback)


@router.callback_query(F.data.startswith("quiz_order_"), QuizForm.viewing_results)
async def start_quiz_order(callback: CallbackQuery, state: FSMContext):
    """Начало заявки из квиза"""
    data = await state.get_data()
    results = data.get('quiz_results', [])
    current_index = int(callback.data.replace("quiz_order_", ""))
    
    if not results or current_index >= len(results):
        await callback.answer("Ошибка: товар не найден", show_alert=True)
        return
    
    selected_product = results[current_index]
    
    await state.update_data(
        quiz_selected_product=selected_product,
        quiz_selected_index=current_index
    )
    
    await state.set_state(QuizOrderForm.waiting_for_name)
    
    await callback.message.answer(
        f"📝 <b>Оставить заявку на товар</b>\n\n"
        f"<b>{selected_product.get('name', 'Товар')}</b>\n\n"
        f"Для оформления заявки нам нужны ваши данные.\n\n"
        f"👤 <b>Введите ваше имя:</b>",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardRemove()
    )
    
    await callback.answer()


@router.message(QuizOrderForm.waiting_for_name)
async def process_quiz_order_name(message: Message, state: FSMContext):
    """Обработка имени в заявке из квиза"""
    name = message.text.strip()
    
    ok, info = validate_name(name)
    if not ok:
        await message.answer(
            f"❌ {info}\n\n"
            "👤 <b>Введите ваше имя:</b>",
            parse_mode="HTML"
        )
        return
    
    await state.update_data(name=name)
    await state.set_state(QuizOrderForm.waiting_for_phone)
    
    await message.answer(
        f"✅ Имя сохранено: <b>{name}</b>\n\n"
        f"📞 <b>Введите ваш номер телефона:</b>\n\n"
        f"Или используйте кнопку ниже:",
        parse_mode="HTML",
        reply_markup=phone_keyboard()
    )


@router.message(QuizOrderForm.waiting_for_phone, F.contact)
async def process_quiz_order_phone_contact(message: Message, state: FSMContext):
    """Обработка телефона из контакта в заявке из квиза"""
    phone = message.contact.phone_number
    if not phone.startswith('+'):
        phone = '+' + phone
    
    await state.update_data(phone=phone)
    await confirm_quiz_order(message, state)


@router.message(QuizOrderForm.waiting_for_phone)
async def process_quiz_order_phone(message: Message, state: FSMContext):
    """Обработка телефона в заявке из квиза"""
    phone = message.text.strip()
    
    error = validate_phone(phone)
    if error:
        await message.answer(
            f"❌ {error}\n\n"
            "📞 <b>Введите ваш номер телефона:</b>",
            parse_mode="HTML",
            reply_markup=phone_keyboard()
        )
        return
    
    formatted_phone = format_phone(phone)
    await state.update_data(phone=formatted_phone)
    await confirm_quiz_order(message, state)


async def confirm_quiz_order(message: Message, state: FSMContext):
    """Подтверждение заявки из квиза"""
    data = await state.get_data()
    product = data.get('quiz_selected_product', {})
    name = data.get('name', '')
    phone = data.get('phone', '')
    
    summary = f"""📝 <b>Заявка на товар</b>

✅ Все данные заполнены

🛍️ <b>Товар:</b> {product.get('name', 'Не указан')}
👤 <b>Имя:</b> {name}
📞 <b>Телефон:</b> {phone}

✅ Всё верно? Отправим заявку?"""
    
    await message.answer(
        summary,
        reply_markup=confirmation_keyboard(),
        parse_mode="HTML"
    )
    
    await state.set_state(QuizOrderForm.confirmation)


@router.callback_query(F.data == "send_order", QuizOrderForm.confirmation)
async def send_quiz_order(callback: CallbackQuery, state: FSMContext):
    """Отправка заявки из квиза"""
    data = await state.get_data()
    user = callback.from_user
    user_id = user.id
    time_code = datetime.now().strftime('%H%M')
    product = data.get('quiz_selected_product', {})
    
    success_text = f"""
🎉 Заявка успешно отправлена!

Спасибо, {data.get('name')}! 
Мы получили вашу заявку на товар <b>{product.get('name', '')}</b> и свяжемся с вами в ближайшее время для уточнения деталей.

📞 Контакты:
• Телефон: {CONTACT_PHONE}
• Email: {CONTACT_EMAIL}

Номер заявки: #{user_id}-{time_code}
    """
    await callback.message.answer(success_text, parse_mode="HTML", reply_markup=main_menu_keyboard())
    
    logger.info(f"Попытка отправить заявку из квиза администраторам. ADMIN_CHAT_IDS: {ADMIN_CHAT_IDS}")
    
    if not ADMIN_CHAT_IDS:
        logger.warning("ADMIN_CHAT_IDS пуст! Заявка не будет отправлена администраторам.")
    else:
        admin_text = f"""
🆕 НОВАЯ ЗАЯВКА ИЗ КВИЗА

👤 <b>Клиент:</b> {user.first_name} {user.last_name or ''}
📱 <b>Username:</b> @{user.username or 'не указан'}
🆔 <b>User ID:</b> {user_id}

🛍️ <b>Товар:</b> {product.get('name', 'Не указан')}
💰 <b>Цена:</b> {product.get('price', 'Не указана')}

👤 <b>Имя:</b> {data.get('name', '')}
📞 <b>Телефон:</b> {data.get('phone', '')}

⏰ <b>Время:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}
        """
        
        success_count = 0
        
        for admin_chat_id in ADMIN_CHAT_IDS:
            try:
                await callback.bot.send_message(admin_chat_id, admin_text, parse_mode="HTML")
                logger.info(f"✅ Заявка из квиза успешно отправлена админу {admin_chat_id}")
                success_count += 1
            except Exception as e:
                logger.error(f"❌ Ошибка отправки админу {admin_chat_id}: {e}", exc_info=True)
        
        logger.info(f"Заявка из квиза отправлена {success_count} из {len(ADMIN_CHAT_IDS)} администраторов")
    
    await state.clear()
    await callback.answer()


@router.message(F.text == "💬 Связь с менеджером")
async def show_contact(message: Message):
    if not await check_registration(message.from_user.id):
        await message.answer("❌ Для использования бота необходимо подтвердить согласие на обработку персональных данных. Используйте команду /start")
        return
    
    contact_text = f"""
💬 <b>Связь с менеджером</b>

Если у вас есть вопросы, нужна помощь в выборе мебели или индивидуальная консультация:

🔹 <b>Телефон:</b> {CONTACT_PHONE}  
🔹 <b>Email:</b> {CONTACT_EMAIL}
🔹 <b>Наш канал:</b> https://t.me/sofit_vanna

Мы на связи каждый день и отвечаем максимально быстро!
    """
    msg = await message.answer(contact_text, parse_mode="HTML", reply_markup=main_menu_keyboard())
    user_service_messages[message.from_user.id].append(msg.message_id)



@router.message(F.text == "ℹ️ О магазине")
async def show_shop_info(message: Message):
    if not await check_registration(message.from_user.id):
        await message.answer("❌ Для использования бота необходимо подтвердить согласие на обработку персональных данных. Используйте команду /start")
        return

    msg = await message.answer(SHOP_INFO, reply_markup=main_menu_keyboard())
    user_service_messages[message.from_user.id].append(msg.message_id)



@router.message(F.text == "📝 Оставить заявку")
async def start_order(message: Message, state: FSMContext):
    user_id = message.from_user.id
    
    if not await check_registration(user_id):
        await message.answer("❌ Для использования бота необходимо подтвердить согласие на обработку персональных данных. Используйте команду /start")
        return
    
    user_service_messages[user_id].append(message.message_id)

    await state.set_state(OrderForm.waiting_for_measurements)

    form_text = """📝 <b>Заявка</b>

<b>Шаг 1/4:</b> Опишите параметры помещения
<i>Можно пропустить</i>"""
    
    msg = await message.answer(
        form_text,
        reply_markup=skip_keyboard(),
        parse_mode="HTML"
    )
    await state.update_data(form_message_id=msg.message_id)
    user_service_messages[user_id].append(msg.message_id)

    
@router.message(OrderForm.waiting_for_measurements)
async def handle_measurements(message: Message, state: FSMContext):
    try:
        await message.delete()
    except Exception:
        pass

    error = validate_measurements(message.text)
    if error:
        msg = await message.answer(f"❗ {error}")
        user_service_messages[message.from_user.id].append(msg.message_id)
        return

    await state.update_data(measurements=message.text.strip())
    await state.set_state(OrderForm.waiting_for_name)

    data = await state.get_data()
    form_message_id = data.get('form_message_id')
    
    form_text = """👤 <b>Шаг 2 из 4:</b> Как к вам обращаться?

Пожалуйста, укажите ваше имя — так нам будет проще общаться.
<i>Например: Александра, Настя, Иван</i>"""
    
    try:
        await message.bot.edit_message_text(
            chat_id=message.from_user.id,
            message_id=form_message_id,
            text=form_text,
            reply_markup=None,
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Ошибка редактирования сообщения: {e}")


@router.callback_query(F.data == "skip", OrderForm.waiting_for_measurements)
async def skip_measurements(callback: CallbackQuery, state: FSMContext):
    await state.update_data(measurements="Не указано", form_message_id=callback.message.message_id)
    await state.set_state(OrderForm.waiting_for_name)

    form_text = """👤 <b>Шаг 2 из 4:</b> Как к вам обращаться?

Пожалуйста, укажите ваше имя — так нам будет проще общаться.
<i>Например: Александра, Настя, Иван</i>"""
    
    try:
        await callback.message.edit_text(
            text=form_text,
            reply_markup=None,
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Ошибка редактирования сообщения: {e}")

    await callback.answer()

    
@router.message(OrderForm.waiting_for_name)
async def handle_name(message: Message, state: FSMContext):
    try:
        await message.delete()
    except Exception:
        pass

    ok, info = validate_name(message.text)
    if not ok:
        msg = await message.answer(f"❗ {info}\n\nПопробуйте ещё раз:")
        user_service_messages[message.from_user.id].append(msg.message_id)
        return

    await state.update_data(name=message.text.strip())
    await state.set_state(OrderForm.waiting_for_phone)

    data = await state.get_data()
    form_message_id = data.get('form_message_id')
    
    form_text = """📞 <b>Шаг 3 из 4:</b> Ваш номер телефона

Пожалуйста, укажите номер для связи.
<i>Пример: +7XXXXXXXXXX</i>"""
    
    try:
                                   
        await message.bot.edit_message_text(
            chat_id=message.from_user.id,
            message_id=form_message_id,
            text=form_text,
            reply_markup=None,
            parse_mode="HTML"
        )
        msg = await message.answer("Выберите действие:", reply_markup=phone_keyboard())
        await state.update_data(keyboard_message_id=msg.message_id)
        user_service_messages[message.from_user.id].append(msg.message_id)
    except Exception as e:
        logger.error(f"Ошибка редактирования сообщения: {e}")


@router.message(OrderForm.waiting_for_phone, F.contact)
async def handle_contact(message: Message, state: FSMContext):
    formatted = format_phone(message.contact.phone_number)
    await state.update_data(phone=formatted)
    
    try:
        await message.delete()
    except Exception:
        pass
    
    data = await state.get_data()
    keyboard_message_id = data.get('keyboard_message_id')
    if keyboard_message_id:
        try:
            await message.bot.delete_message(
                chat_id=message.from_user.id,
                message_id=keyboard_message_id
            )
        except Exception:
            pass
    
    await state.set_state(OrderForm.waiting_for_photo)
    
    data = await state.get_data()
    form_message_id = data.get('form_message_id')
    
    form_text = """📷 <b>Шаг 4 из 4:</b> Фотография помещения (необязательно)

При желании прикрепите фотографию помещения для лучшего понимания задачи.

Или нажмите "Пропустить", чтобы продолжить без фото."""
    
    try:
        await message.bot.edit_message_text(
            chat_id=message.from_user.id,
            message_id=form_message_id,
            text=form_text,
            reply_markup=skip_keyboard(),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Ошибка редактирования сообщения: {e}")


@router.message(OrderForm.waiting_for_phone)
async def handle_phone_text(message: Message, state: FSMContext):
    try:
        await message.delete()
    except Exception:
        pass
    
    error = validate_phone(message.text)
    if error:
        msg = await message.answer(f"❗ {error}\n\nПопробуйте еще раз:")
        user_service_messages[message.from_user.id].append(msg.message_id)
        return
    
    formatted = format_phone(message.text)
    await state.update_data(phone=formatted)
    
    data = await state.get_data()
    keyboard_message_id = data.get('keyboard_message_id')
    if keyboard_message_id:
        try:
            await message.bot.delete_message(
                chat_id=message.from_user.id,
                message_id=keyboard_message_id
            )
        except Exception:
            pass
    
    await state.set_state(OrderForm.waiting_for_photo)
    
    data = await state.get_data()
    form_message_id = data.get('form_message_id')
    
    form_text = """📷 <b>Шаг 4 из 4:</b> Фотография помещения (необязательно)

При желании прикрепите фотографию помещения для лучшего понимания задачи.

Или нажмите "Пропустить", чтобы продолжить без фото."""
    
    try:
        await message.bot.edit_message_text(
            chat_id=message.from_user.id,
            message_id=form_message_id,
            text=form_text,
            reply_markup=skip_keyboard(),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Ошибка редактирования сообщения: {e}")


@router.message(OrderForm.waiting_for_photo, F.photo)
async def handle_photo(message: Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    await state.update_data(photo_id=photo_id)
    logger.info(f"Фото сохранено: photo_id={photo_id}")
    
    try:
        await message.delete()
    except Exception:
        pass
    
    await confirm_order(message, state)


@router.callback_query(F.data == "skip", OrderForm.waiting_for_photo)
async def skip_photo(callback: CallbackQuery, state: FSMContext):
    await state.update_data(photo_id=None)

    await confirm_order(callback.message, state)
    await callback.answer()


async def confirm_order(message: Message, state: FSMContext):
    data = await state.get_data()

    measurements = data.get('measurements', 'Не указано')
    name = data.get('name', '')
    phone = data.get('phone', '')
    photo_id = data.get('photo_id')
    form_message_id = data.get('form_message_id')
    
    summary = f"""📝 <b>Заявка</b>

✅ Все шаги заполнены

📐 <b>Замеры:</b> {measurements}
👤 <b>Имя:</b> {name}
📞 <b>Телефон:</b> {phone}
📷 <b>Фото:</b> {'Да' if photo_id else 'Нет'}

✅ Всё верно? Отправим заявку?"""
    
    user_id = message.from_user.id if hasattr(message, 'from_user') else message.chat.id
    
    try:
        bot_instance = message.bot if hasattr(message, 'bot') else None
        
        if bot_instance and form_message_id:
            await bot_instance.edit_message_text(
                chat_id=user_id,
                message_id=form_message_id,
                text=summary,
                reply_markup=confirmation_keyboard(),
                parse_mode="HTML"
            )
        else:
            msg = await message.answer(summary, reply_markup=confirmation_keyboard(), parse_mode="HTML")
            user_service_messages[user_id].append(msg.message_id)
    except Exception as e:
        logger.error(f"Ошибка редактирования сообщения: {e}")
        msg = await message.answer(summary, reply_markup=confirmation_keyboard(), parse_mode="HTML")
        user_service_messages[user_id].append(msg.message_id)
    
    await state.set_state(OrderForm.confirmation)


@router.callback_query(F.data == "send_order", OrderForm.confirmation)
async def send_order(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user = callback.from_user
    user_id = user.id
    time_code = datetime.now().strftime('%H%M')

    for msg_id in user_service_messages.get(user_id, []):
        try:
            await callback.bot.delete_message(chat_id=user_id, message_id=msg_id)
        except Exception as e:
            logger.error(f"Ошибка удаления сообщения {msg_id}: {e}")
    user_service_messages.pop(user_id, None)

    success_text = f"""
🎉 Заявка успешно отправлена!

Спасибо, {data.get('name')}! 
Мы получили вашу заявку и свяжемся с вами в ближайшее время для уточнения деталей.

📞 Контакты:
• Телефон: {CONTACT_PHONE}
• Email: {CONTACT_EMAIL}

Номер заявки: #{user_id}-{time_code}
    """
    await callback.message.answer(success_text)
    await callback.message.answer("Выберите действие:", reply_markup=main_menu_keyboard())

    logger.info(f"Попытка отправить заявку администраторам. ADMIN_CHAT_IDS: {ADMIN_CHAT_IDS}")
    
    if not ADMIN_CHAT_IDS:
        logger.warning("ADMIN_CHAT_IDS пуст! Заявка не будет отправлена администраторам.")
    else:
        admin_text = f"""
🆕 НОВАЯ ЗАЯВКА

👤 <b>Клиент:</b> {user.first_name} {user.last_name or ''}
📱 <b>Username:</b> @{user.username or 'не указан'}
🆔 <b>User ID:</b> {user_id}

📐 <b>Замеры помещения:</b>
{data.get('measurements', 'Не указано')}

👤 <b>Имя:</b> {data.get('name', '')}
📞 <b>Телефон:</b> {data.get('phone', '')}
📷 <b>Фото:</b> {'Прикреплено' if data.get('photo_id') else 'Не прикреплено'}

⏰ <b>Время:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}
        """
        
        success_count = 0
        photo_id = data.get('photo_id')
        logger.info(f"Отправка заявки администраторам. photo_id: {photo_id}")
        
        for admin_chat_id in ADMIN_CHAT_IDS:
            try:
                if photo_id:
                    await callback.bot.send_photo(
                        admin_chat_id,
                        photo=photo_id,
                        caption=admin_text,
                        parse_mode="HTML"
                    )
                    logger.info(f"✅ Заявка с фото успешно отправлена админу {admin_chat_id}, photo_id={photo_id}")
                else:
                    await callback.bot.send_message(admin_chat_id, admin_text, parse_mode="HTML")
                    logger.info(f"✅ Заявка успешно отправлена админу {admin_chat_id} (без фото)")
                success_count += 1
            except Exception as e:
                logger.error(f"❌ Ошибка отправки админу {admin_chat_id}: {e}", exc_info=True)
        
        logger.info(f"Заявка отправлена {success_count} из {len(ADMIN_CHAT_IDS)} администраторов")

    await state.clear()
    await callback.answer()



@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа", show_alert=True)
        return
    
    try:
        await callback.answer()
    except Exception:
        pass
    
    text = (
        "📢 *Рассылка сообщений*\n\n"
        "Отправьте сообщение, которое хотите разослать всем пользователям.\n\n"
        "Поддерживаются:\n"
        "• Текст\n"
        "• Фото с подписью\n"
        "• Видео с подписью\n\n"
    )
    
    await callback.message.answer(
        text,
        parse_mode="Markdown",
        reply_markup=get_broadcast_back_keyboard()
    )
    await state.set_state(AdminStates.waiting_for_broadcast)


@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа", show_alert=True)
        return
    
    try:
        await callback.answer()
    except Exception:
        pass
    
    try:
        users = await get_all_users()
        total_users = len(users)
        
        stats_text = (
            f"📊 *Статистика бота*\n\n"
            f"👥 Всего пользователей: {total_users}\n"
            f"📅 Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        )
        
        await callback.message.answer(
            stats_text,
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Ошибка при получении статистики: {e}")
        await callback.message.answer("❌ Ошибка при получении статистики")


@router.callback_query(F.data == "admin_back")
async def admin_back(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа", show_alert=True)
        return

    try:
        await callback.answer()
    except Exception:
        pass
    
    current_state = await state.get_state()
    
    if current_state == AdminStates.waiting_for_broadcast:
        await state.clear()
        admin_text = (
            "🔐 *Админ-панель*\n\n"
            "Выберите действие:"
        )
        
        await callback.message.answer(
            admin_text,
            parse_mode="Markdown",
            reply_markup=get_admin_keyboard()
        )
    else:
        await state.clear()
        await callback.message.answer(
            "🔐 *Админ-панель*\n\n"
            "Выберите действие:",
            parse_mode="Markdown",
            reply_markup=get_admin_keyboard()
        )


@router.message(AdminStates.waiting_for_broadcast, F.content_type.in_([ContentType.TEXT, ContentType.PHOTO, ContentType.VIDEO]))
async def process_broadcast(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к админ-панели.")
        await state.clear()
        return

    confirm_text = (
        "📢 *Подтверждение рассылки*\n\n"
        "Вы уверены, что хотите разослать это сообщение всем пользователям?\n\n"
        "Нажмите '✅ Подтвердить' для начала рассылки или '❌ Отменить' для отмены."
    )
    
    confirm_keyboard = get_broadcast_confirm_keyboard()
    
    await state.update_data(
        broadcast_message=message.model_dump_json(),
        content_type=message.content_type
    )
    
    if message.content_type == ContentType.TEXT:
        preview_text = f"*Превью:*\n\n{message.text}"
        await message.answer(
            preview_text,
            parse_mode="Markdown",
            reply_markup=confirm_keyboard
        )
    elif message.content_type == ContentType.PHOTO:
        if message.caption:
            preview_text = f"*Превью (фото с подписью):*\n\n{message.caption}"
        else:
            preview_text = "*Превью: Фото без подписи*"
        await message.answer_photo(
            message.photo[-1].file_id,
            caption=preview_text,
            parse_mode="Markdown",
            reply_markup=confirm_keyboard
        )
    elif message.content_type == ContentType.VIDEO:
        if message.caption:
            preview_text = f"*Превью (видео с подписью):*\n\n{message.caption}"
        else:
            preview_text = "*Превью: Видео без подписи*"
        await message.answer_video(
            message.video.file_id,
            caption=preview_text,
            parse_mode="Markdown",
            reply_markup=confirm_keyboard
        )


@router.callback_query(F.data == "broadcast_confirm")
async def broadcast_confirm(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа", show_alert=True)
        return
    
    try:
        await callback.answer("Начинаю рассылку...")
    except Exception:
        pass
    
    data = await state.get_data()
    broadcast_message = data.get("broadcast_message")
    content_type = data.get("content_type")
    
    if not broadcast_message:
        await callback.message.answer("❌ Ошибка: сообщение не найдено.")
        await state.clear()
        return

    users = await get_all_users()
    total_users = len(users)
    
    if total_users == 0:
        await callback.message.answer("❌ Нет пользователей для рассылки.")
        await state.clear()
        return

    message_data = json.loads(broadcast_message)
    bot = callback.bot
    
    await callback.message.answer(f"📤 Начинаю рассылку для {total_users} пользователей...")
    
    success_count = 0
    error_count = 0
    
    for user in users:
        try:
            user_id = user.get("telegram_user_id")
            
            if content_type == ContentType.TEXT:
                text = message_data.get("text", "")
                await bot.send_message(user_id, text)
            elif content_type == ContentType.PHOTO:
                photos = message_data.get("photo", [])
                if photos:
                    photo_id = photos[-1].get("file_id")
                    caption = message_data.get("caption")
                    await bot.send_photo(user_id, photo_id, caption=caption)
                else:
                    continue
            elif content_type == ContentType.VIDEO:
                video_data = message_data.get("video", {})
                if video_data:
                    video_id = video_data.get("file_id")
                    caption = message_data.get("caption")
                    await bot.send_video(user_id, video_id, caption=caption)
                else:
                    continue
            
            success_count += 1
            
            if success_count % 10 == 0:
                await asyncio.sleep(1)
                
        except Exception as e:
            error_count += 1
            user_id = user.get("telegram_user_id", "unknown")
            logger.error(f"Ошибка при отправке сообщения пользователю {user_id}: {e}")
    
    result_text = (
        f"✅ *Рассылка завершена*\n\n"
        f"📊 Статистика:\n"
        f"• Успешно отправлено: {success_count}\n"
        f"• Ошибок: {error_count}\n"
        f"• Всего пользователей: {total_users}"
    )
    
    await callback.message.answer(
        result_text,
        parse_mode="Markdown",
        reply_markup=get_admin_keyboard()
    )
    
    await state.clear()


@router.callback_query(F.data == "broadcast_cancel")
async def broadcast_cancel(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет доступа", show_alert=True)
        return
    
    try:
        await callback.answer("Рассылка отменена")
    except Exception:
        pass
    
    await state.clear()
    await callback.message.answer(
        "❌ Рассылка отменена.",
        reply_markup=get_admin_keyboard()
    )
