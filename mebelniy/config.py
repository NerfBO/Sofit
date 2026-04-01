import os
import re
from dotenv import load_dotenv

                                                                        
                                                                
load_dotenv(override=False)

BOT_TOKEN = os.getenv("BOT_TOKEN")

CONTACT_PHONE = os.getenv("CONTACT_PHONE", "+79378500140")
CONTACT_EMAIL = os.getenv("CONTACT_EMAIL", "info@sofit-mebel.ru")
ADMIN_CHAT_IDS = [int(x) for x in os.getenv("ADMIN_CHAT_IDS", "").split(",") if x.strip()]                                                       
ADMIN_USER_IDS = [int(x) for x in os.getenv("ADMIN_USER_IDS", "").split(",") if x.strip()]                      

CATALOG_MINI_APP_URL = os.getenv("CATALOG_MINI_APP_URL", "https://example.com/catalog")

                                                 
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
                                                                        
                                                                                           
    match = re.match(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', DATABASE_URL)
    if match:
        DB_USER = match.group(1)
        DB_PASSWORD = match.group(2)
        DB_HOST = match.group(3)
        DB_PORT = int(match.group(4))
        DB_NAME = match.group(5)                                 
    else:
                                                                      
        default_db_host = "postgres" if os.path.exists("/app") else "localhost"
        DB_HOST = os.getenv("DB_HOST") or default_db_host
        DB_PORT = int(os.getenv("DB_PORT", "5432"))
        DB_NAME = os.getenv("DB_NAME", "sofit_bot")
        DB_USER = os.getenv("DB_USER", "postgres")
        DB_PASSWORD = os.getenv("DB_PASSWORD", "")
else:
                                     
                                                                                                 
                                                                                    
                                                            
    
                                                                                             
                                                                                         
    default_db_host = "postgres" if os.path.exists("/app") else "localhost"
    DB_HOST = os.getenv("DB_HOST") or default_db_host
    DB_PORT = int(os.getenv("DB_PORT", "5432"))
    DB_NAME = os.getenv("DB_NAME", "sofit_bot")                                       
    DB_USER = os.getenv("DB_USER", "postgres")                                             
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")

SHOP_INFO = """В нашем боте вы можете приобрести корпусную мебель напрямую от производителя в г. Уфа.
В боте представлены следующие виды мебели:

Для ванной комнаты:
— подвесные тумбы под стиральную машину
— подвесные тумбы под раковину
— пеналы

Для спальни:
— прикроватные тумбы
— комоды
— модульные шкафы

Выбирайте лучшее для своего пространства!

+79378500140 / info@sofit-mebel.ru"""

