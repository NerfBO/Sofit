import asyncio
import json
import re
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def parse_html_directly(html: str, base_url: str):
    """
    Парсит исходный HTML напрямую (до выполнения JavaScript)
    Используется как дополнительный источник данных
    
    Args:
        html: HTML содержимое страницы
        base_url: Базовый URL сайта
        
    Returns:
        dict: Данные товара из исходного HTML
    """
    from urllib.parse import urljoin
    
    result = {
        'images': [],
        'description': '',
        'name': '',
        'price': ''
    }
    
    soup = BeautifulSoup(html, 'html.parser')
    
                                   
    title_elem = soup.find('h1')
    if not title_elem:
        title_elem = soup.find('title')
    if title_elem:
        result['name'] = title_elem.get_text(strip=True)
    
                                          
                                                             
    images_found = set()
    
    def normalize_url(url: str) -> str:
        """Нормализует URL изображения"""
        if not url:
            return ''
        url = url.strip()
                                                                                       
        url = re.sub(r'/-/(format|resizeb|cover)/[^/]+/', '/', url)
        url = re.sub(r'\.webp$', '', url)                           
        if url.startswith('/'):
            url = urljoin(base_url, url)
        elif not url.startswith('http'):
            url = urljoin(base_url, '/' + url.lstrip('/'))
        return url
    
    def is_valid_image_url(url: str) -> bool:
        """Проверяет, что это валидное изображение товара, а не логотип"""
        if not url:
            return False
        url_lower = url.lower()
        skip_patterns = [
            'tildacopy.png', 
            'tildacdn.com/img/tildacopy',
            'icon', 
            'logo', 
            'avatar', 
            'favicon',
            'placeholder',
            'flags7.png'                              
        ]
        return not any(skip in url_lower for skip in skip_patterns)
    
                           
    for img in soup.find_all('img'):
        for attr in ['src', 'data-src', 'data-original', 'data-lazy-src', 'data-bg', 'data-image', 'data-url']:
            img_url = img.get(attr, '')
            if img_url:
                img_url = normalize_url(img_url)
                if img_url and is_valid_image_url(img_url):
                    images_found.add(img_url)
    
                                                                                                    
    data_attrs = ['data-product-img', 'data-original', 'data-bg', 'data-image', 'data-img-zoom-url']
    for attr in data_attrs:
        for elem in soup.find_all(attrs={attr: True}):
            img_url = elem.get(attr, '')
            if img_url:
                img_url = normalize_url(img_url)
                if img_url and is_valid_image_url(img_url):
                    images_found.add(img_url)
    
                                                                               
    for elem in soup.find_all(style=True):
        style = elem.get('style', '')
                                
        urls = re.findall(r'url\(["\']?([^"\')]+)["\']?\)', style)
        for url in urls:
            url = normalize_url(url)
            if url and is_valid_image_url(url):
                images_found.add(url)
    
                                                                               
    slider_classes = ['t-slds__bgimg', 't-store__card__bgimg', 't-bgimg', 'js-product-img']
    for class_name in slider_classes:
        for elem in soup.find_all(class_=lambda x: x and class_name in (x if isinstance(x, list) else [x])):
                                     
            img_url = elem.get('data-original', '')
            if img_url:
                img_url = normalize_url(img_url)
                if img_url and is_valid_image_url(img_url):
                    images_found.add(img_url)
            
                                                
            style = elem.get('style', '')
            if style:
                urls = re.findall(r'url\(["\']?([^"\')]+)["\']?\)', style)
                for url in urls:
                    url = normalize_url(url)
                    if url and is_valid_image_url(url):
                        images_found.add(url)
    
                                                   
    for meta in soup.find_all('meta', itemprop='image'):
        img_url = meta.get('content', '')
        if img_url:
            img_url = normalize_url(img_url)
            if img_url and is_valid_image_url(img_url):
                images_found.add(img_url)
    
    result['images'] = list(images_found)
    
                                   
    description_parts = []
    skip_texts = [
        'все товары', 'каталог', 'главная', 'корзина', 'добавить в корзину',
        'checkout', 'your name', 'your email', 'your phone', 'made on tilda'
    ]
    
                                      
    for elem in soup.find_all(['p', 'div', 'li', 'span']):
        text = elem.get_text(strip=True)
        if text and len(text) > 50:
            text_lower = text.lower()
            if not any(skip in text_lower for skip in skip_texts):
                if '₽' not in text or len(text) > 100:
                    if text not in description_parts:
                        description_parts.append(text)
    
    if description_parts:
        result['description'] = '\n\n'.join(description_parts[:10])                           
    
                               
    price_pattern = re.compile(r'\d+[\s,.]*\d*\s*[₽руб]', re.IGNORECASE)
    for elem in soup.find_all(['div', 'span', 'p', 'h1', 'h2', 'h3']):
        text = elem.get_text(strip=True)
        if price_pattern.search(text) and len(text) < 50:
            result['price'] = text.strip()
            break
    
    return result


async def parse_product_page(page, product_url: str, base_url: str, retry_count=3):
    """
    Парсит страницу отдельного товара
    
    Args:
        page: Playwright page object
        product_url: URL страницы товара
        base_url: Базовый URL сайта
        retry_count: Количество попыток при ошибке
        
    Returns:
        dict: Данные товара (name, url, price, images, description)
    """
    from urllib.parse import urljoin
    
    product = {'url': product_url}
    
    for attempt in range(retry_count):
        try:
            logger.info(f"Парсим товар: {product_url} (попытка {attempt + 1}/{retry_count})")
            
                                                                      
            await page.goto(product_url, wait_until='domcontentloaded', timeout=60000)
            initial_html = await page.content()
            
                                           
            html_data = parse_html_directly(initial_html, base_url)
            logger.info(f"   HTML-парсинг: найдено {len(html_data.get('images', []))} изображений")
            
                                                                       
            try:
                await page.wait_for_selector('body', timeout=10000)
                                                                             
                await page.wait_for_timeout(5000)                            
                
                                                         
                try:
                    await page.wait_for_selector('img[src]:not([src*="tildacopy"])', timeout=10000)
                except:
                    pass                                 
            except:
                pass
            
                                                                 
            final_html = await page.content()
            soup = BeautifulSoup(final_html, 'html.parser')
            
                                                
            title_elem = None
            if html_data.get('name'):
                product['name'] = html_data['name']
            else:
                title_elem = soup.find('h1')
                if not title_elem:
                    title_elem = soup.find(class_=lambda x: x and ('title' in x.lower() or 'name' in x.lower() or 'product-title' in x.lower()))
                if title_elem:
                    product['name'] = title_elem.get_text(strip=True)
            
                                                             
                                                                                   
            visible_images = await page.evaluate("""
                () => {
                    const images = [];
                    const seenUrls = new Set();
                    
                    // Функция для нормализации URL
                    function normalizeUrl(url) {
                        if (!url) return '';
                        url = url.trim();
                        // Убираем параметры оптимизации Tilda
                        url = url.replace(/\\/-\\/(format|resizeb|cover)\\/[^\\/]+\\//g, '/');
                        url = url.replace(/\\.webp$/, '');
                        if (url.startsWith('/')) {
                            url = window.location.origin + url;
                        } else if (!url.startsWith('http')) {
                            url = window.location.origin + '/' + url.replace(/^\\//, '');
                        }
                        return url.split('?')[0]; // Убираем параметры запроса
                    }
                    
                    // Функция для проверки видимости элемента
                    function isVisible(elem) {
                        if (!elem) return false;
                        const style = window.getComputedStyle(elem);
                        if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') {
                            return false;
                        }
                        const rect = elem.getBoundingClientRect();
                        return rect.width > 50 && rect.height > 50 && rect.top >= -100 && rect.left >= -100;
                    }
                    
                    // Функция для проверки, что это не логотип/иконка
                    function isValidImage(url) {
                        if (!url) return false;
                        const urlLower = url.toLowerCase();
                        const skipPatterns = ['tildacopy.png', 'tildacdn.com/img/tildacopy', 'icon', 'logo', 'avatar', 'favicon', 'placeholder', 'flags7.png'];
                        return !skipPatterns.some(skip => urlLower.includes(skip));
                    }
                    
                    // Ищем все видимые изображения товара
                    // 1. Ищем в слайдерах товара (Tilda использует data-img-zoom-url, data-original)
                    const sliders = document.querySelectorAll('[data-img-zoom-url], [data-original], [data-product-img]');
                    sliders.forEach(slider => {
                        if (!isVisible(slider)) return;
                        const imgUrl = slider.getAttribute('data-img-zoom-url') || 
                                      slider.getAttribute('data-original') || 
                                      slider.getAttribute('data-product-img');
                        if (imgUrl) {
                            const normalized = normalizeUrl(imgUrl);
                            if (normalized && isValidImage(normalized) && !seenUrls.has(normalized)) {
                                images.push(normalized);
                                seenUrls.add(normalized);
                            }
                        }
                    });
                    
                    // 2. Ищем видимые теги <img> в основном контенте товара
                    const mainContent = document.querySelector('main, [class*="content"], [class*="product"]') || document.body;
                    const imgTags = mainContent.querySelectorAll('img');
                    imgTags.forEach(img => {
                        if (!isVisible(img)) return;
                        // Пропускаем изображения в навигации, футере, хедере
                        const parent = img.closest('nav, header, footer, [class*="nav"], [class*="menu"]');
                        if (parent) return;
                        
                        const imgUrl = img.getAttribute('src') || 
                                      img.getAttribute('data-src') || 
                                      img.getAttribute('data-original');
                        if (imgUrl) {
                            const normalized = normalizeUrl(imgUrl);
                            if (normalized && isValidImage(normalized) && !seenUrls.has(normalized)) {
                                // Проверяем размеры
                                const rect = img.getBoundingClientRect();
                                if (rect.width >= 100 && rect.height >= 100) {
                                    images.push(normalized);
                                    seenUrls.add(normalized);
                                }
                            }
                        }
                    });
                    
                    return images;
                }
            """)
            
            if visible_images:
                product['images'] = visible_images
                logger.info(f"   Видимых изображений: {len(product['images'])}")
            
                                                                          
                                                                
            description_parts = []
            skip_texts = [
                'все товары', 'каталог', 'главная', 'корзина', 'добавить в корзину',
                'checkout', 'your name', 'your email', 'your phone', 'made on tilda',
                'перейти к оплате', 'соглашаетесь', 'checkout', 'add to cart',
                'ваш телефон', 'ваш email', 'ваше имя', 'добавить в корзину'
            ]
            
                                                          
            if title_elem:
                                                       
                parent = title_elem.find_parent(['div', 'section', 'article', 'main'])
                if parent:
                                                                   
                    for nav in parent.find_all(['nav', 'header', 'footer', 'button', 'a', 'form', 'input']):
                        nav.decompose()
                    
                                                                       
                    found_h1 = False
                    for elem in parent.find_all(['p', 'div', 'li', 'span', 'h2', 'h3', 'h4']):
                                                   
                        if elem == title_elem or title_elem in elem.find_all(['h1']):
                            found_h1 = True
                            continue
                        if not found_h1:
                            continue
                        
                        text = elem.get_text(strip=True)
                                                                      
                        if text and len(text) > 30:
                            text_lower = text.lower()
                            if not any(skip in text_lower for skip in skip_texts):
                                                                                   
                                if '₽' not in text or len(text) > 50:
                                    if text not in description_parts:
                                        description_parts.append(text)
            
                                                                            
            if not description_parts:
                tilda_text_blocks = soup.find_all(['div', 'section'], class_=lambda x: x and (
                    't-text' in str(x).lower() or 
                    't-descr' in str(x).lower() or 
                    't-content' in str(x).lower()
                ))
                
                for block in tilda_text_blocks:
                                                 
                    if block.find_parent(['nav', 'header', 'footer', 'form']):
                        continue
                    
                                                             
                    for nav in block.find_all(['nav', 'header', 'footer', 'button', 'a', 'form', 'input']):
                        nav.decompose()
                    
                    text = block.get_text(separator=' ', strip=True)
                    if text and len(text) > 50:
                        text_lower = text.lower()
                        if not any(skip in text_lower for skip in skip_texts):
                            if text not in description_parts:
                                description_parts.append(text)
            
                                                                                     
            if not description_parts:
                for p in soup.find_all('p'):
                    parent = p.find_parent(['nav', 'header', 'footer', 'form'])
                    if parent:
                        continue
                    
                    text = p.get_text(strip=True)
                    if text and len(text) > 50:
                        text_lower = text.lower()
                        if not any(skip in text_lower for skip in skip_texts):
                            if '₽' not in text or len(text) > 100:
                                if text not in description_parts:
                                    description_parts.append(text)
            
                                           
            if description_parts:
                                                
                unique_parts = []
                seen = set()
                for part in description_parts:
                    part_normalized = part.lower().strip()
                                                                                 
                    part_normalized_clean = ' '.join(part_normalized.split())
                    if part_normalized_clean not in seen and len(part.strip()) > 20:
                        seen.add(part_normalized_clean)
                        unique_parts.append(part.strip())
                
                if unique_parts:
                                               
                    product['description'] = '\n\n'.join(unique_parts)
                    logger.info(f"   Описание: {len(product['description'])} символов")
            
                                                    
            price_elem = None
            price_text = None
            
                                                                                       
            price_elem = soup.find(class_=lambda x: x and (
                'price' in x.lower() or 
                'cost' in x.lower() or
                't-price' in x.lower()
            ))
            
                                               
            if not price_elem:
                price_elem = soup.find(attrs={'data-price': True})
            
                                                                     
            if not price_elem:
                                                            
                for elem in soup.find_all(string=lambda x: x and ('₽' in str(x) or 'руб' in str(x).lower())):
                    parent = elem.find_parent()
                    if parent:
                                                                                             
                        parent_class = parent.get('class', [])
                        parent_class_str = ' '.join(parent_class).lower() if isinstance(parent_class, list) else str(parent_class).lower()
                        if 'price' in parent_class_str or 'cost' in parent_class_str or len(parent.get_text(strip=True)) < 100:
                            price_elem = parent
                            break
            
                                                             
            if not price_elem:
                                                            
                price_pattern = re.compile(r'\d+[\s,.]*\d*\s*[₽руб]', re.IGNORECASE)
                for elem in soup.find_all(['div', 'span', 'p', 'h1', 'h2', 'h3']):
                    text = elem.get_text(strip=True)
                    if price_pattern.search(text) and len(text) < 50:                        
                        price_elem = elem
                        break
            
            if price_elem:
                if hasattr(price_elem, 'get_text'):
                    price_text = price_elem.get_text(strip=True)
                else:
                    price_text = str(price_elem).strip()
                
                                                 
                price_text = price_text.replace('\n', ' ').replace('\r', ' ').strip()
                                               
                price_text = re.sub(r'\s+', ' ', price_text)
                
                if price_text:
                    product['price'] = price_text
            else:
                                                                                  
                if html_data.get('price'):
                    product['price'] = html_data['price']
            
            logger.info(f"✅ Товар обработан: {product.get('name', 'Без названия')}")
            logger.info(f"   Изображений: {len(product.get('images', []))}")
            logger.info(f"   Описание: {'Есть' if product.get('description') else 'Нет'}")
            return product
            
        except Exception as e:
            if attempt < retry_count - 1:
                logger.warning(f"Ошибка при парсинге товара {product_url} (попытка {attempt + 1}): {e}. Повторяем...")
                await asyncio.sleep(2)
            else:
                logger.error(f"Ошибка при парсинге товара {product_url} после {retry_count} попыток: {e}")
    
    return product


async def parse_tilda_catalog(url: str):
    """
    Парсит каталог товаров с сайта Тильды
    Сначала находит ссылки на товары, затем парсит каждую страницу товара
    
    Args:
        url: URL страницы каталога на Тильде
        
    Returns:
        list: Список словарей с данными товаров
    """
    products = []
    product_urls = []
    
    from urllib.parse import urljoin, urlparse
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()
        
        try:
            logger.info(f"Загружаем страницу каталога: {url}")
                                                                                    
            await page.goto(url, wait_until='domcontentloaded', timeout=90000)
                                                                               
            try:
                await page.wait_for_load_state('networkidle', timeout=15000)
            except:
                pass                                  
            await page.wait_for_timeout(5000)                                                      
            
            html = await page.content()
            soup = BeautifulSoup(html, 'html.parser')
            
                                       
                                                       
            product_links = soup.find_all('a', href=True)
            
                                                                       
            base_domain = urlparse(url).netloc
            for link in product_links:
                href = link.get('href', '')
                if not href:
                    continue
                
                                       
                if href.startswith('/'):
                    href = urljoin(url, href)
                
                                                             
                if urlparse(href).netloc != base_domain:
                    continue
                
                                              
                if any(exclude in href.lower() for exclude in ['/cart', '/checkout', '/account', '/login', '/register', '#', 'javascript:']):
                    continue
                
                                                              
                                                              
                parent = link.find_parent(['div', 'article', 'section'])
                if parent:
                                                                                   
                    has_img = parent.find('img') is not None
                    has_title = parent.find(['h1', 'h2', 'h3', 'h4']) is not None
                    
                    if has_img or has_title:
                        if href not in product_urls:
                            product_urls.append(href)
            
                                                                    
            if not product_urls:
                logger.info("Ссылки не найдены, ищем карточки товаров...")
                product_cards = soup.find_all(['div', 'article'], class_=lambda x: x and ('product' in x.lower() or 'item' in x.lower() or 'card' in x.lower()))
                
                for card in product_cards:
                    link = card.find('a', href=True)
                    if link:
                        href = link.get('href', '')
                        if href.startswith('/'):
                            href = urljoin(url, href)
                        if href not in product_urls and urlparse(href).netloc == base_domain:
                            product_urls.append(href)
            
            logger.info(f"Найдено ссылок на товары: {len(product_urls)}")
            
            if not product_urls:
                logger.warning("Ссылки на товары не найдены. Сохраняем HTML для анализа...")
                with open('debug_html.html', 'w', encoding='utf-8') as f:
                    f.write(html)
                logger.info("HTML сохранен в debug_html.html для анализа")
                return products
            
                                           
            for i, product_url in enumerate(product_urls, 1):
                try:
                    logger.info(f"Обрабатываем товар {i}/{len(product_urls)}")
                    
                                              
                    try:
                        product = await parse_product_page(page, product_url, url)
                    except Exception as parse_error:
                                                               
                        if 'closed' in str(parse_error).lower() or 'target' in str(parse_error).lower():
                            logger.warning(f"Страница закрыта, пересоздаем...")
                            try:
                                await page.close()
                            except:
                                pass
                            page = await context.new_page()
                            try:
                                product = await parse_product_page(page, product_url, url)
                            except Exception as retry_error:
                                logger.error(f"Не удалось обработать товар {product_url} после пересоздания: {retry_error}")
                                continue
                        else:
                            logger.error(f"Ошибка парсинга товара {product_url}: {parse_error}")
                            continue
                    
                                                                 
                    if product.get('name'):
                                                                                             
                        filtered_product = {
                            'name': product.get('name'),
                            'url': product.get('url'),
                            'price': product.get('price', ''),
                            'images': product.get('images', []),
                            'description': product.get('description', '')
                        }
                        products.append(filtered_product)
                        logger.info(f"✅ Товар добавлен: {filtered_product.get('name')}")
                    else:
                        logger.warning(f"Товар без названия пропущен: {product_url}")
                    
                                                        
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    logger.error(f"Критическая ошибка при обработке товара {product_url}: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Ошибка при парсинге: {e}", exc_info=True)
        
        finally:
            try:
                await browser.close()
            except Exception as e:
                logger.warning(f"Ошибка при закрытии браузера: {e}")
    
    return products


import os


def load_existing_products() -> dict:
    """
    Загружает существующие товары из JSON файла
    
    Returns:
        dict: Словарь {url: product} для быстрого поиска
    """
    json_file = 'catalog_products.json'
    if not os.path.exists(json_file):
        logger.info(f"Файл {json_file} не найден. Будет создан новый.")
        return {}
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            products_list = json.load(f)
                                                        
            return {p.get('url'): p for p in products_list if p.get('url')}
    except Exception as e:
        logger.error(f"Ошибка загрузки {json_file}: {e}")
        return {}


def save_products(products: list):
    """Сохраняет товары в JSON файл"""
    json_file = 'catalog_products.json'
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=2)
    logger.info(f"Товары сохранены в {json_file}")


def normalize_url_for_comparison(url: str) -> str:
    """Нормализует URL для сравнения (убирает параметры, trailing slash)"""
    if not url:
        return ""
    url = url.strip().rstrip('/')
                               
    if '?' in url:
        url = url.split('?')[0]
    return url


def compare_and_update_product(existing: dict, new: dict) -> dict:
    """
    Сравнивает и обновляет данные товара
    
    Args:
        existing: Существующие данные товара
        new: Новые данные с сайта
        
    Returns:
        dict: Обновленный товар
    """
    updated = existing.copy()
    changes = []
    
                                         
    if new.get('name') and new.get('name') != existing.get('name'):
        updated['name'] = new.get('name')
        changes.append(f"название: '{existing.get('name')}' -> '{new.get('name')}'")
    
                                     
    if new.get('price') and new.get('price') != existing.get('price'):
        updated['price'] = new.get('price')
        changes.append(f"цена: '{existing.get('price')}' -> '{new.get('price')}'")
    
                                            
    new_images = new.get('images', [])
    existing_images = existing.get('images', [])
    
                                               
    def normalize_img_url(url: str) -> str:
        url = url.strip()
                                             
        url = re.sub(r'/-/(format|resizeb|cover)/[^/]+/', '/', url)
        url = re.sub(r'\.webp$', '', url)
        return url.split('?')[0]                             
    
    existing_images_normalized = {normalize_img_url(img) for img in existing_images}
    new_images_normalized = {normalize_img_url(img) for img in new_images}
    
    if new_images_normalized != existing_images_normalized:
                                                
        updated['images'] = new_images
        changes.append(f"изображения: {len(existing_images)} -> {len(new_images)}")
    
                                         
    new_desc = new.get('description', '').strip()
    existing_desc = existing.get('description', '').strip()
    
    if new_desc and new_desc != existing_desc:
        updated['description'] = new_desc
        changes.append(f"описание: {len(existing_desc)} -> {len(new_desc)} символов")
    elif not new_desc and existing_desc:
                                                      
        updated['description'] = ""
        changes.append("описание: удалено")
    
    if changes:
        logger.info(f"   Изменения: {', '.join(changes)}")
    
    return updated




async def update_all_products(catalog_url: str):
    """
    Обновляет все товары: проверяет существующие и добавляет новые
    
    Args:
        catalog_url: URL каталога товаров
    """
                                   
    existing_products_dict = load_existing_products()
    logger.info(f"Загружено существующих товаров: {len(existing_products_dict)}")
    
                                                            
    logger.info("Парсинг каталога для поиска всех товаров...")
    catalog_products = []
    try:
        catalog_products = await parse_tilda_catalog(catalog_url)
        logger.info(f"Найдено товаров в каталоге: {len(catalog_products)}")
    except Exception as e:
        logger.error(f"Ошибка парсинга каталога: {e}")
        logger.warning("Продолжаем обновление только существующих товаров...")
    
                                             
    updated_products_dict = {}
    new_products_count = 0
    updated_products_count = 0
    unchanged_products_count = 0
    
                                           
    for new_product in catalog_products:
        product_url = new_product.get('url')
        if not product_url:
            continue
        
        normalized_url = normalize_url_for_comparison(product_url)
        
                                        
        existing_product = None
        for url, product in existing_products_dict.items():
            if normalize_url_for_comparison(url) == normalized_url:
                existing_product = product
                break
        
        if existing_product:
                                                 
            updated_product = compare_and_update_product(existing_product, new_product)
            updated_products_dict[product_url] = updated_product
            
                                          
            if updated_product != existing_product:
                updated_products_count += 1
            else:
                unchanged_products_count += 1
        else:
                                     
            updated_products_dict[product_url] = new_product
            new_products_count += 1
            logger.info(f"   ✨ Новый товар: {new_product.get('name', 'Без названия')}")
    
                                                                                  
                                                                                              
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()
        
        try:
                                                                   
            products_to_update = []
            for url, product in existing_products_dict.items():
                normalized_url = normalize_url_for_comparison(url)
                found_in_catalog = False
                for cat_url in updated_products_dict.keys():
                    if normalize_url_for_comparison(cat_url) == normalized_url:
                        found_in_catalog = True
                        break
                if not found_in_catalog:
                    products_to_update.append((url, product))
            
            if products_to_update:
                logger.info(f"\nОбновление {len(products_to_update)} товаров, не найденных в каталоге...")
                total = len(products_to_update)
                for i, (url, product) in enumerate(products_to_update, 1):
                    logger.info(f"[{i}/{total}] Обновление: {product.get('name', 'Без названия')}")
                    
                    try:
                                                
                        new_data = await parse_product_page(page, url, url)
                        
                        if new_data and new_data.get('name'):
                                                    
                            updated_product = compare_and_update_product(product, new_data)
                            updated_products_dict[url] = updated_product
                            
                            if updated_product != product:
                                updated_products_count += 1
                            else:
                                unchanged_products_count += 1
                        else:
                                                                                 
                            updated_products_dict[url] = product
                            unchanged_products_count += 1
                            logger.warning(f"   ⚠️ Не удалось обновить товар")
                        
                                                                   
                        if i % 5 == 0:
                            save_products(list(updated_products_dict.values()))
                            logger.info(f"Промежуточное сохранение ({i}/{total})")
                        
                        await asyncio.sleep(2)                            
                        
                    except Exception as e:
                        logger.error(f"Ошибка обновления товара {url}: {e}")
                                                                 
                        updated_products_dict[url] = product
                        unchanged_products_count += 1
                        continue
        
        finally:
            await browser.close()
    
                          
    products_list = list(updated_products_dict.values())
    save_products(products_list)
    
                
    logger.info("\n" + "=" * 60)
    logger.info("РЕЗУЛЬТАТЫ ОБНОВЛЕНИЯ:")
    logger.info(f"   • Всего товаров: {len(products_list)}")
    logger.info(f"   • Новых товаров: {new_products_count}")
    logger.info(f"   • Обновленных товаров: {updated_products_count}")
    logger.info(f"   • Без изменений: {unchanged_products_count}")
    logger.info("=" * 60)


async def main():
    """Основная функция"""
    print("=" * 60)
    print("Обновление каталога товаров")
    print("=" * 60)
    
                              
    catalog_url = input("\nВведите URL каталога на Тильде: ").strip()
    
    if not catalog_url:
        catalog_url = "https://sofitmebel.ru/katalog"
        logger.info(f"Используется URL по умолчанию: {catalog_url}")
    
    if not catalog_url.startswith('http'):
        catalog_url = 'https://' + catalog_url
    
    logger.info(f"Начинаем обновление каталога: {catalog_url}\n")
    
                          
    await update_all_products(catalog_url)
    
    print("\n✅ Обновление завершено!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ Обновление прервано пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True)
