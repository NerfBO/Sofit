import re
from typing import Optional, Tuple

def validate_name(name: str) -> Tuple[bool, str]:
    """
    Проверка корректности русскоязычного имени.

    Возвращает:
        (True, "OK")                 – имя прошло проверку
        (False, "сообщение об ошибке") – имя некорректно
    """
    name = name.strip()

              
    if len(name) < 2:
        return False, "Имя должно содержать минимум 2 символа"
    if len(name) > 30:
        return False, "Имя слишком длинное (максимум 30 символов)"

                                                          
    if not re.fullmatch(r"[А-ЯЁа-яё\s\-]+", name):
        return False, "Имя может содержать только русские буквы, пробелы и дефисы"

                                          
    name_without_spaces = name.replace(" ", "").replace("-", "")
    if re.search(r"(.)\1{2,}", name_without_spaces, re.IGNORECASE):
        return False, "Имя не может содержать более 2 одинаковых букв подряд"

                                                       
    unique_chars = set(name.lower().replace(" ", "").replace("-", ""))
    if len(unique_chars) == 1:
        return False, "Имя не может состоять из одинаковых букв"

                                                           
    if len(name) >= 4:
        half = len(name) // 2
        if name[:half].lower() == name[half:half*2].lower():
            return False, "Имя выглядит как повторяющийся шаблон"


                                           
    keyboard_patterns = ("йцукен", "фыва", "ячсм", "абвг", "тест", "йцу")
    clean = name.lower().replace(" ", "").replace("-", "")
    if any(pat in clean for pat in keyboard_patterns):
        return False, "Имя выглядит подозрительно, введите настоящее имя"



    return True, "OK"

def validate_phone(phone: str) -> Optional[str]:
    """Валидация телефона для стран СНГ"""
                                            
    clean_phone = re.sub(r'[^\d+]', '', phone)
    
                               
    patterns = [
        r'^\+7\d{10}$',                           
        r'^8\d{10}$',                              
        r'^\+380\d{9}$',                            
        r'^\+375\d{9}$',                             
        r'^\+77\d{9}$',                              
        r'^\+996\d{9}$',                               
        r'^\+992\d{9}$',                                
        r'^\+993\d{8}$',                                
        r'^\+998\d{9}$',                               
    ]
    
    for pattern in patterns:
        if re.match(pattern, clean_phone):
            return None
    
    return "Введите корректный номер телефона (например: +7XXXXXXXXXX или 8XXXXXXXXXX)"

def format_phone(phone: str) -> str:
    """Форматирование телефона"""
    clean_phone = re.sub(r'[^\d+]', '', phone)
    
                                   
    if clean_phone.startswith('8') and len(clean_phone) == 11:
        clean_phone = '+7' + clean_phone[1:]
    elif clean_phone.startswith('7') and len(clean_phone) == 11:
        clean_phone = '+' + clean_phone
    
    return clean_phone

def validate_measurements(measurements: str) -> Optional[str]:
    """Валидация описания замеров помещения"""
    if len(measurements.strip()) < 10:
        return "Пожалуйста, укажите более подробную информацию о замерах помещения (минимум 10 символов)"
    if len(measurements.strip()) > 1000:
        return "Описание замеров не должно превышать 1000 символов"
    
    return None


