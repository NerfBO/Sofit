import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from handlers import router
from storage import get_db_pool

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def main():
    """🚀 Запуск бота Софит"""
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN не указан! Проверь config.py")
        return

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(router)

    try:
        await bot.set_my_description(
            """🏠 Добро пожаловать в Софит!

Мы — производитель корпусной мебели в г. Уфа. Прямые поставки от производителя.

✨ В нашем боте вы можете:
• Просмотреть каталог товаров
• Оставить заявку
• Получить консультацию от менеджера
• Узнать ответы на частые вопросы

🛏️ Наша продукция:
• Мебель для ванной комнаты
• Мебель для спальни
• Индивидуальные решения

Выбирайте лучшее для своего пространства!"""
        )

        await bot.set_my_short_description(
            "Софит — магазин корпусной мебели от производителя в г. Уфа. Каталог, заявки, консультации!"
        )
        logger.info("📝 Описание и короткое описание бота успешно установлены.")
    except Exception as e:
        logger.warning(f"⚠️ Не удалось установить описание бота: {e}")

                      
    try:
        await get_db_pool()
        logger.info("✅ Подключение к базе данных инициализировано")
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации БД: {e}")
        logger.warning("⚠️ Бот будет работать без сохранения данных в БД")
    
            
    logger.info("🚀 Бот запускается...")
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logger.info("🛑 Получен сигнал остановки (Ctrl+C)")
    except Exception as e:
        logger.error(f"💥 Критическая ошибка во время работы бота: {e}")
    finally:
        await bot.session.close()
        logger.info("✅ Сессия бота завершена")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.critical(f"🔥 Ошибка при запуске main(): {e}")

