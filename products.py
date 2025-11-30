import logging
from aiogram import types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

logger = logging.getLogger(__name__)

def get_test_products_data():
    """Тестовые данные товаров для демонстрации"""
    return [
        {
            "id": "001",
            "name": "Смартфон Samsung Galaxy A54 5G",
            "brand": "Samsung",
            "price": 25999,
            "old_price": 29999,
            "rating": 4.5,
            "reviews_count": 1250,
            "image": "https://images.wbstatic.net/cb300x300/1000000-1000999/1000123-1000123-1.jpg",
            "link": "https://www.wildberries.ru/catalog/1000123/detail.aspx",
            "description": "Смартфон с камерой 50 МП и экраном 6.4 дюйма",
            "discount": "-13%",
            "in_stock": True
        },
        {
            "id": "002", 
            "name": "Наушники Sony WH-1000XM4",
            "brand": "Sony",
            "price": 18990,
            "old_price": 21990,
            "rating": 4.8,
            "reviews_count": 3420,
            "image": "https://images.wbstatic.net/cb300x300/2000000-2000999/2000234-2000234-1.jpg",
            "link": "https://www.wildberries.ru/catalog/2000234/detail.aspx",
            "description": "Беспроводные наушники с шумоподавлением",
            "discount": "-14%",
            "in_stock": True
        },
        {
            "id": "003",
            "name": "Кроссовки Nike Air Max 90",
            "brand": "Nike", 
            "price": 8990,
            "old_price": 10990,
            "rating": 4.6,
            "reviews_count": 890,
            "image": "https://images.wbstatic.net/cb300x300/3000000-3000999/3000567-3000567-1.jpg",
            "link": "https://www.wildberries.ru/catalog/3000567/detail.aspx",
            "description": "Классические кроссовки с технологией Air",
            "discount": "-18%",
            "in_stock": True
        },
        {
            "id": "004",
            "name": "Планшет iPad Air 10.9",
            "brand": "Apple",
            "price": 45990,
            "old_price": 52990,
            "rating": 4.7,
            "reviews_count": 567,
            "image": "https://images.wbstatic.net/cb300x300/4000000-4000999/4000789-4000789-1.jpg",
            "link": "https://www.wildberries.ru/catalog/4000789/detail.aspx",
            "description": "Планшет с чипом M1 и дисплеем Liquid Retina",
            "discount": "-13%",
            "in_stock": True
        },
        {
            "id": "005",
            "name": "Умная колонка Яндекс Алиса",
            "brand": "Яндекс",
            "price": 3990,
            "old_price": 4990,
            "rating": 4.4,
            "reviews_count": 2150,
            "image": "https://images.wbstatic.net/cb300x300/5000000-5000999/5000123-5000123-1.jpg",
            "link": "https://www.wildberries.ru/catalog/5000123/detail.aspx",
            "description": "Умная колонка с голосовым помощником",
            "discount": "-20%",
            "in_stock": True
        },
        {
            "id": "006",
            "name": "Фитнес-браслет Xiaomi Mi Band 7",
            "brand": "Xiaomi",
            "price": 2990,
            "old_price": 3990,
            "rating": 4.3,
            "reviews_count": 1840,
            "image": "https://images.wbstatic.net/cb300x300/6000000-6000999/6000789-6000789-1.jpg",
            "link": "https://www.wildberries.ru/catalog/6000789/detail.aspx",
            "description": "Фитнес-браслет с AMOLED дисплеем",
            "discount": "-25%",
            "in_stock": True
        }
    ]

def search_products(query, filters=None):
    """Поиск товаров (тестовые данные)"""
    try:
        all_products = get_test_products_data()
        
        query_lower = query.lower()
        results = []
        
        for product in all_products:
            if (query_lower in product['name'].lower() or 
                query_lower in product['brand'].lower() or
                query_lower in product['description'].lower()):
                results.append(product)
        
        if filters:
            if 'min_price' in filters:
                results = [p for p in results if p['price'] >= filters['min_price']]
            if 'max_price' in filters:
                results = [p for p in results if p['price'] <= filters['max_price']]
            if 'min_rating' in filters:
                results = [p for p in results if p['rating'] >= filters['min_rating']]
        
        return results[:10]
        
    except Exception as e:
        logger.error(f"Ошибка при поиске товаров: {e}")
        return []

def get_products_keyboard():
    """Создает клавиатуру для поиска товаров"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔍 Поиск по категориям", callback_data="products_categories"),
                InlineKeyboardButton(text="💰 Лучшие предложения", callback_data="products_deals")
            ],
            [
                InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_menu")
            ]
        ]
    )
    return keyboard

def get_products_results_keyboard(products):
    """Создает клавиатуру с товарами"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    for i, product in enumerate(products[:5]):
        button_text = f"🛍️ {product['name'][:30]}... - {product['price']:,}₽"
        callback_data = f"product_{product['id']}"
        
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text=button_text, url=product['link'])
        ])
    
    nav_buttons = []
    nav_buttons.append(InlineKeyboardButton(text="🔄 Попробовать другой запрос", callback_data="products_search"))
    
    if len(products) > 5:
        nav_buttons.append(InlineKeyboardButton(text="➡️ Следующие", callback_data="products_next"))
    
    nav_buttons.append(InlineKeyboardButton(text="🔙 Назад", callback_data="products_menu"))
    keyboard.inline_keyboard.append(nav_buttons)
    
    return keyboard

def format_products_message(products, query):
    """Форматирует сообщение с результатами поиска"""
    if not products:
        return f"❌ **Товары не найдены** ❌\n\n🔍 По запросу **{query}** ничего не найдено.\n\n💡 **Попробуйте:**\n• Другие ключевые слова\n• Менее специфичный запрос\n• Проверьте правильность написания"
    
    message = f"🛒 **Результаты поиска** 🛒\n\n"
    message += f"🔍 По запросу: **{query}**\n"
    message += f"📦 Найдено товаров: **{len(products)}**\n\n"
    
    for i, product in enumerate(products[:3], 1):
        message += f"**{i}.** {product['name']}\n"
        message += f"💰 Цена: {product['price']:,}₽"
        
        if product.get('old_price'):
            message += f" ~~{product['old_price']:,}₽~~"
        
        if product.get('discount'):
            message += f" {product['discount']}"
        
        message += f"\n⭐ Рейтинг: {product['rating']}/5 ({product['reviews_count']} отзывов)\n"
        message += f"🏷️ Бренд: {product['brand']}\n\n"
    
    if len(products) > 3:
        message += f"💡 И ещё **{len(products) - 3} товаров** - выберите из списка ниже!\n\n"
    
    message += "👇 **Нажмите на товар для перехода в магазин**"
    
    return message

async def process_products_callback(callback: types.CallbackQuery):
    """Обработчик нажатия на кнопку поиска товаров"""
    try:
        await callback.answer()
        
        products_text = (
            "🛒 **Поиск товаров на Wildberries** 🛒\n\n"
            "🔍 Введите название товара для поиска:\n\n"
            "📝 **Примеры поисковых запросов:**\n"
            "• смартфон\n"
            "• наушники\n"
            "• кроссовки\n"
            "• планшет\n"
            "• фитнес браслет\n\n"
            "💡 **Просто напишите что ищете!**"
        )
        
        await callback.message.edit_text(
            products_text,
            parse_mode="Markdown",
            reply_markup=get_products_keyboard()
        )
        logger.info(f"Пользователь {callback.from_user.id} нажал на кнопку поиска товаров")
        
    except Exception as e:
        logger.error(f"Ошибка при обработке поиска товаров: {e}")

async def process_products_search(message: types.Message):
    """Обработчик поиска товаров"""
    try:
        query = message.text.strip()
        
        if query.startswith('/'):
            return
        
        products = search_products(query)
        products_message = format_products_message(products, query)
        
        if products:
            keyboard = get_products_results_keyboard(products)
        else:
            keyboard = get_products_keyboard()
        
        await message.answer(
            products_message,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
        logger.info(f"Поиск товаров выполнен пользователем {message.from_user.id} по запросу: {query}")
        
    except Exception as e:
        logger.error(f"Ошибка при поиске товаров для запроса {message.text}: {e}")
        await message.answer(
            "❌ Произошла ошибка при поиске товаров.\n\n🔄 Попробуйте ещё раз:",
            reply_markup=get_products_keyboard()
        )

async def process_products_categories(callback: types.CallbackQuery):
    """Обработчик поиска по категориям"""
    try:
        await callback.answer()
        
        categories_text = (
            "📂 **Поиск по категориям** 📂\n\n"
            "🔍 **Доступные категории:**\n\n"
            "📱 **Электроника:**\n"
            "• смартфоны\n"
            "• наушники\n"
            "• планшеты\n\n"
            "👟 **Одежда и обувь:**\n"
            "• кроссовки\n"
            "• куртки\n"
            "• джинсы\n\n"
            "🏠 **Дом и сад:**\n"
            "• мебель\n"
            "• посуда\n"
            "• декор\n\n"
            "💡 **Введите название категории или конкретного товара:**"
        )
        
        await callback.message.edit_text(
            categories_text,
            parse_mode="Markdown",
            reply_markup=get_products_keyboard()
        )
        logger.info(f"Пользователь {callback.from_user.id} выбрал поиск по категориям")
        
    except Exception as e:
        logger.error(f"Ошибка при обработке поиска по категориям: {e}")

async def process_products_deals(callback: types.CallbackQuery):
    """Обработчик лучших предложений"""
    try:
        await callback.answer()
        
        all_products = get_test_products_data()
        deals_products = [p for p in all_products if p.get('old_price')]
        deals_products.sort(key=lambda x: int(x['discount'].replace('-', '').replace('%', '')), reverse=True)
        
        deals_text = "🔥 **Лучшие предложения дня** 🔥\n\n"
        deals_text += f"💰 Найдено товаров со скидками: **{len(deals_products)}**\n\n"
        
        for i, product in enumerate(deals_products[:3], 1):
            deals_text += f"**{i}.** {product['name']}\n"
            deals_text += f"💰 {product['price']:,}₽ ~~{product['old_price']:,}₽~~ {product['discount']}\n"
            deals_text += f"⭐ {product['rating']}/5\n\n"
        
        if len(deals_products) > 3:
            deals_text += f"💡 И ещё **{len(deals_products) - 3} выгодных предложений** - выберите из списка ниже!\n\n"
        
        deals_text += "👇 **Нажмите на товар для перехода в магазин**"
        
        if deals_products:
            keyboard = get_products_results_keyboard(deals_products)
        else:
            keyboard = get_products_keyboard()
        
        await callback.message.edit_text(
            deals_text,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        logger.info(f"Пользователь {callback.from_user.id} посмотрел лучшие предложения")
        
    except Exception as e:
        logger.error(f"Ошибка при обработке лучших предложений: {e}")

async def process_products_menu(callback: types.CallbackQuery):
    """Обработчик возврата к меню поиска товаров"""
    try:
        await callback.answer()
        
        products_text = (
            "🛒 **Поиск товаров на Wildberries** 🛒\n\n"
            "🔍 Введите название товара для поиска:\n\n"
            "📝 **Примеры поисковых запросов:**\n"
            "• смартфон\n"
            "• наушники\n"
            "• кроссовки\n"
            "• планшет\n"
            "• фитнес браслет\n\n"
            "💡 **Просто напишите что ищете!**"
        )
        
        await callback.message.edit_text(
            products_text,
            parse_mode="Markdown",
            reply_markup=get_products_keyboard()
        )
        logger.info(f"Пользователь {callback.from_user.id} вернулся к меню поиска товаров")
        
    except Exception as e:
        logger.error(f"Ошибка при возврате к меню поиска товаров: {e}")

def register_products_handlers(dp):
    """Регистрирует обработчики товаров"""
    dp.callback_query.register(process_products_callback, F.data == "products")
    dp.callback_query.register(process_products_categories, F.data == "products_categories")
    dp.callback_query.register(process_products_deals, F.data == "products_deals")
    dp.callback_query.register(process_products_menu, F.data == "products_menu")
    dp.message.register(process_products_search, F.content_type == "text")