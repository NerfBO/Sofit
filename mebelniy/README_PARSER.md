# Парсер каталога Тильды

Отдельный скрипт для парсинга товаров с сайта Тильды.

## Установка зависимостей

### Вариант 1: Виртуальное окружение (рекомендуется)

```bash
# Создаем виртуальное окружение
python3 -m venv venv

# Активируем виртуальное окружение
source venv/bin/activate  # На macOS/Linux
# или
venv\Scripts\activate  # На Windows

# Устанавливаем зависимости
pip install playwright beautifulsoup4 lxml

# Устанавливаем браузер для Playwright
playwright install chromium
```

### Вариант 2: С флагом --break-system-packages (не рекомендуется)

```bash
pip3 install --break-system-packages playwright beautifulsoup4 lxml
playwright install chromium
```

## Использование

```bash
python parser.py
```

Скрипт запросит URL каталога и сохранит результаты в `catalog_products.json`.

## Настройка под ваш сайт

В файле `parser.py` нужно адаптировать селекторы под структуру вашего сайта Тильды:

1. Найдите классы/селекторы товаров на вашем сайте
2. Откройте DevTools в браузере (F12)
3. Изучите структуру HTML товаров
4. Обновите селекторы в функции `parse_tilda_catalog()`

## Отладка

Если товары не находятся, скрипт сохранит HTML в `debug_html.html` для анализа.
