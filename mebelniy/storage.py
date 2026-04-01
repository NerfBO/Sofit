            
import asyncpg
import logging
from collections import defaultdict, deque
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

logger = logging.getLogger(__name__)

user_service_messages = defaultdict(list)

                             
_db_pool = None


async def get_db_pool():
    """Получение пула подключений к БД"""
    global _db_pool
    if _db_pool is None:
        try:
            _db_pool = await asyncpg.create_pool(
                host=DB_HOST,
                port=DB_PORT,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                min_size=1,
                max_size=10
            )
            await init_db()
            logger.info("✅ Подключение к PostgreSQL установлено")
        except Exception as e:
            error_msg = str(e)
            hint = ""
            
                                                                        
            if "does not exist" in error_msg or ("database" in error_msg.lower() and "does not exist" in error_msg.lower()):
                                                                                          
                hint = f"\n💡 ПОДСКАЗКА: Имя БАЗЫ ДАННЫХ (DB_NAME / в DATABASE_URL после последнего /) должно быть '{DB_NAME}', "
                hint += f"не путать с именем ПОЛЬЗОВАТЕЛЯ (DB_USER) '{DB_USER}'.\n"
                hint += f"   Текущие значения: DB_NAME='{DB_NAME}', DB_USER='{DB_USER}', DB_HOST='{DB_HOST}', DB_PORT={DB_PORT}"
            elif "Connect call failed" in error_msg or "Connection refused" in error_msg or "Errno 111" in error_msg:
                                                           
                hint = f"\n💡 ПОДСКАЗКА: Не удается подключиться к PostgreSQL по адресу {DB_HOST}:{DB_PORT}.\n"
                hint += f"   Проверьте:\n"
                hint += f"   • Запущен ли PostgreSQL сервер?\n"
                if DB_HOST == "localhost" or DB_HOST == "127.0.0.1":
                    hint += f"   • Если бот запущен в Docker, используйте имя сервиса 'postgres' вместо 'localhost'\n"
                    hint += f"   • В docker-compose.yml уже настроено DB_HOST=postgres для контейнера бота\n"
                hint += f"   Текущие значения: DB_HOST='{DB_HOST}', DB_PORT={DB_PORT}, DB_NAME='{DB_NAME}', DB_USER='{DB_USER}'"
            elif "password authentication failed" in error_msg.lower() or "authentication failed" in error_msg.lower():
                                       
                hint = f"\n💡 ПОДСКАЗКА: Ошибка аутентификации. Проверьте правильность DB_USER и DB_PASSWORD.\n"
                hint += f"   Текущие значения: DB_USER='{DB_USER}', DB_PASSWORD={'***' if DB_PASSWORD else '(не задан)'}"
            
            if hint:
                logger.error(f"❌ Ошибка подключения к PostgreSQL: {e}{hint}", exc_info=True)
            else:
                logger.error(f"❌ Ошибка подключения к PostgreSQL: {e}", exc_info=True)
            raise
    return _db_pool


async def init_db():
    """Инициализация таблиц в БД"""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_user_id BIGINT PRIMARY KEY,
                username VARCHAR(255),
                first_name VARCHAR(255),
                last_name VARCHAR(255),
                is_registered BOOLEAN DEFAULT FALSE,
                consent_given_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)


async def is_user_registered(telegram_user_id: int) -> bool:
    """Проверка, зарегистрирован ли пользователь (дал согласие)"""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            result = await conn.fetchval(
                "SELECT is_registered FROM users WHERE telegram_user_id = $1",
                telegram_user_id
            )
            return result is True
    except Exception as e:
        logger.error(f"Ошибка проверки регистрации пользователя {telegram_user_id}: {e}", exc_info=True)
        return False


async def save_user(telegram_user_id: int, username: str = None, first_name: str = None, last_name: str = None, consent: bool = False):
    """Сохранение пользователя в БД"""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            from datetime import datetime
            now = datetime.now()
            
            if consent:
                                                          
                await conn.execute("""
                    INSERT INTO users (telegram_user_id, username, first_name, last_name, is_registered, consent_given_at, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    ON CONFLICT (telegram_user_id) 
                    DO UPDATE SET 
                        username = EXCLUDED.username,
                        first_name = EXCLUDED.first_name,
                        last_name = EXCLUDED.last_name,
                        is_registered = EXCLUDED.is_registered,
                        consent_given_at = EXCLUDED.consent_given_at,
                        updated_at = EXCLUDED.updated_at
                """, telegram_user_id, username, first_name, last_name, True, now, now, now)
            else:
                                                      
                await conn.execute("""
                    INSERT INTO users (telegram_user_id, username, first_name, last_name, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (telegram_user_id) 
                    DO UPDATE SET 
                        username = EXCLUDED.username,
                        first_name = EXCLUDED.first_name,
                        last_name = EXCLUDED.last_name,
                        updated_at = EXCLUDED.updated_at
                """, telegram_user_id, username, first_name, last_name, now, now)
    except Exception as e:
        logger.error(f"Ошибка сохранения пользователя {telegram_user_id}: {e}", exc_info=True)


async def get_all_users():
    """Получение всех зарегистрированных пользователей для рассылки"""
    try:
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT telegram_user_id, username, first_name, last_name FROM users WHERE is_registered = TRUE"
            )
            return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Ошибка получения пользователей: {e}", exc_info=True)
        return []
