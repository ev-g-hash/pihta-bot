import logging
import os
import asyncio
import signal
import sys
import requests  # ИЗМЕНЕНИЕ ЗДЕСЬ
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.enums import ContentType
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv
from enum import Enum

# Загружаем переменные окружения из .env файла (для локальной разработки)
load_dotenv()

# Токен бота и API ключ погоды из переменных окружения
BOT_TOKEN = os.getenv('BOT_TOKEN') or "YOUR_BOT_TOKEN_HERE"
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')

# Порт для Cloud Amvera
PORT = int(os.getenv('PORT', 8080))

# Создание директории для логов
os.makedirs('/app/logs', exist_ok=True)  # ИЗМЕНЕНИЕ: /app для контейнера

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger(__name__)

# Проверка токена
if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
    logger.error("Токен бота не настроен! Установите переменную окружения BOT_TOKEN")
    sys.exit(1)

# Проверка API ключа погоды
if not WEATHER_API_KEY:
    logger.error("API ключ погоды не настроен! Установите переменную окружения WEATHER_API_KEY")
    sys.exit(1)

# Состояния бота
class BotMode(Enum):
    IDLE = "idle"           # Главное меню
    WEATHER = "weather"     # Режим ввода города для погоды
    PRODUCTS = "products"   # Режим ввода товара
    REAL_ESTATE = "real_estate"  # Режим поиска жилья

# Глобальная переменная для корректного завершения
running = True

# Глобальная переменная для отслеживания текущего режима
current_mode = BotMode.IDLE

# Создание бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Создание inline клавиатуры с кнопками
def get_main_keyboard():
    """Создает основную клавиатуру с кнопками (каждая в отдельной строке)"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🌤️ Посмотреть прогноз погоды", callback_data="weather")
            ],
            [
                InlineKeyboardButton(text="🛒 Поискать товары", callback_data="products")
            ],
            [
                InlineKeyboardButton(text="🏠 Поискать жильё", callback_data="real_estate")
            ]
        ]
    )
    return keyboard

def get_weather_keyboard():
    """Создает клавиатуру для возврата"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_menu")
            ]
        ]
    )
    return keyboard

def get_products_keyboard():
    """Создает клавиатуру для возврата из поиска товаров"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_menu")
            ]
        ]
    )
    return keyboard

def get_real_estate_keyboard():
    """Создает клавиатуру для возврата из поиска жилья"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_menu")
            ]
        ]
    )
    return keyboard

# Функция для получения координат города
def get_city_coordinates(city_name):
    """Получает координаты города"""
    try:
        # Координаты ваших городов
        city_coords = {
            'москва': {'lat': 55.7558, 'lon': 37.6176},
            'спб': {'lat': 59.9311, 'lon': 30.3609},
            'санкт-петербург': {'lat': 59.9311, 'lon': 30.3609},
            'салехард': {'lat': 66.5345, 'lon': 66.6053},
            'тюмень': {'lat': 57.1530, 'lon': 65.5343},
            'самара': {'lat': 53.1959, 'lon': 50.1008},
            'тольятти': {'lat': 53.5303, 'lon': 49.3461},
            'новокуйбышевск': {'lat': 53.0978, 'lon': 49.9512},
            # Добавлены новые населенные пункты
            'село горки': {'lat': 63.2028, 'lon': 64.7286},  # село Горки, Шурышкарский район, ЯНАО
            'горки': {'lat': 63.2028, 'lon': 64.7286},        # короткое название
            'село мордово': {'lat': 53.6742, 'lon': 51.1239},  # село Мордово, Самарская область
            'мордово': {'lat': 53.6742, 'lon': 51.1239}         # короткое название
        }
        
        city_lower = city_name.lower().strip()
        if city_lower in city_coords:
            return city_coords[city_lower]
        else:
            return None
            
    except Exception as e:
        logger.error(f"Ошибка при получении координат города {city_name}: {e}")
        return None
            
# Функция для получения прогноза погоды
def get_weather_forecast(lat, lon):
    """Получает прогноз погоды через Яндекс.Погода API"""
    try:
        url = 'https://api.weather.yandex.ru/v2/forecast'
        headers = {'X-Yandex-Weather-Key': WEATHER_API_KEY}
        params = {
            'lat': lat,
            'lon': lon,
            'lang': 'ru_RU',
            'limit': 3
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            logger.error(f"API погоды вернул код {response.status_code}: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:  # ИЗМЕНЕНИЕ ЗДЕСЬ
        logger.error(f"Ошибка запроса к API погоды: {e}")
        return None
    except Exception as e:
        logger.error(f"Неожиданная ошибка при получении погоды: {e}")
        return None

# Функция для форматирования прогноза погоды
def format_weather_message(weather_data, city_name):
    """Форматирует сообщение с прогнозом погоды"""
    try:
        if not weather_data:
            return "❌ Не удалось получить данные о погоде. Попробуйте позже."
        
        # Проверяем структуру ответа API
        if 'fact' not in weather_data:
            return f"❌ Неверный формат ответа API для {city_name}. Попробуйте позже."
        
        current = weather_data['fact']
        forecasts = weather_data.get('forecasts', [])
        
        # Эмодзи для условий погоды        
        weather_emojis = {
            'clear': '☀️ Ясно',
            'partly-cloudy': '⛅ Малооблачно',
            'cloudy': '☁️ Облачно',
            'overcast': '☁️ Пасмурно',
            'drizzle': '🌦️ Морось',
            'light-rain': '🌦️ Небольшой дождь',
            'rain': '🌧️ Дождь',
            'moderate-rain': '🌧️ Умеренный дождь',
            'heavy-rain': '🌧️ Сильный дождь',
            'thunderstorm': '⛈️ Гроза',
            'snow': '❄️ Снег',
            'snowfall': '❄️ Снегопад'
        }
        
        condition = current.get('condition', 'unknown')
        icon = weather_emojis.get(condition, '🌤️')
        
        # Температура - безопасное получение
        temp = current.get('temp', 0)
        feels_like = current.get('feels_like', temp)
        
        # Направление ветра
        wind_dir = current.get('wind_dir', '')
        wind_speed = current.get('wind_speed', 0)
        
        wind_directions = {
            'nw': 'СЗ', 'n': 'С', 'ne': 'СВ', 
            'e': 'В', 'se': 'ЮВ', 's': 'Ю', 
            'sw': 'ЮЗ', 'w': 'З', 'c': 'Штиль'
        }
        wind_dir_ru = wind_directions.get(wind_dir, wind_dir)
        
        # Влажность и давление
        humidity = current.get('humidity', 0)
        pressure = current.get('pressure_mm', 0)
        
        message = f"🌤️ **Погода в {city_name.title()}** 🌤️\n\n"
        message += f"{icon} \n\n"
        message += f"🌡️ **Температура:** {temp:+d}°C\n"
        message += f"🌡️ **Ощущается как:** {feels_like:+d}°C\n\n"
        
        if wind_speed > 0:
            message += f"💨 **Ветер:** {wind_dir_ru} {wind_speed} м/с\n"
        
        if humidity > 0:
            message += f"💧 **Влажность:** {humidity}%\n"
        
        if pressure > 0:
            message += f"📊 **Давление:** {pressure} мм рт.ст.\n"
        
        # Прогноз на несколько дней - исправленная обработка
        if forecasts:
            message += "\n📅 **Прогноз на 2 дня:**\n"
            
            for forecast in forecasts[:2]:
                date_parts = forecast.get('date', '').split('-')
                parts = forecast.get('parts', {})
                
                # Берем дневную часть для информации о дне
                day_part = parts.get('day', {})
                
                if day_part:
                    temp_min = day_part.get('temp_min', 0)
                    temp_max = day_part.get('temp_max', 0)
                    condition_day = day_part.get('condition', 'unknown')
                    icon_day = weather_emojis.get(condition_day, '🌤️')
                    
                    if len(date_parts) >= 3:
                        day_str = f"{date_parts[2]}.{date_parts[1]}"
                    else:
                        day_str = "Завтра"
                    
                    message += f"📅 **{day_str}:** {icon_day} {temp_min:+d}°...{temp_max:+d}°C\n"
        
        return message
        
    except Exception as e:
        logger.error(f"Ошибка при форматировании прогноза погоды: {e}")
        logger.error(f"Структура данных: {weather_data}")
        return f"❌ Ошибка при обработке данных о погоде для {city_name}."

# Обработчик команды /start
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    """Обработчик команды /start"""
    try:
        welcome_text = (
            "🌟 **Привет! Я бот на все случаи жизни!** 🌟\n\n"
            "👋 Рад вас видеть! Я умею помогать в различных ситуациях.\n\n"
            "🎯 **Вот что я могу:**\n\n"
            "🌤️ **Прогноз погоды** - узнайте погоду в любом городе\n"
            "🛒 **Поиск товаров** - найдите нужные товары по выгодным ценам\n"
            "🏠 **Поиск жилья** - подберите квартиру или дом для покупки/аренды\n\n"
            "👇 Выберите нужную функцию ниже:"
        )
        
        await message.answer(
            welcome_text,
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
        logger.info(f"Пользователь {message.from_user.id} запустил бота")
    except Exception as e:
        logger.error(f"Ошибка при обработке /start: {e}")

# Обработчик кнопки "Прогноз погоды"
@dp.callback_query(F.data == "weather")
async def process_weather_callback(callback: types.CallbackQuery):
    """Обработчик нажатия на кнопку погоды"""
    try:
        global current_mode
        await callback.answer()
        current_mode = BotMode.WEATHER  # Устанавливаем режим погоды
        
        weather_text = (
            "🌤️ **Прогноз погоды** 🌤️\n\n"
            "🔍 Введите название города для получения прогноза погоды:\n\n"
            "📍 **Поддерживаемые города:**\n"
            "• Москва\n"
            "• Санкт-Петербург\n"
            "• Салехард\n"
            "• Тюмень\n"
            "• Самара\n"
            "• Тольятти\n"
            "• Новокуйбышевск\n"
            "• Село Горки (ЯНАО)\n"
            "• Село Мордово (Самарская область)\n\n"
            "💡 **Пример:** просто напишите название города"
        )
        
        await callback.message.edit_text(
            weather_text,
            parse_mode="Markdown",
            reply_markup=get_weather_keyboard()
        )
        logger.info(f"Пользователь {callback.from_user.id} нажал на кнопку погоды")
        
    except Exception as e:
        logger.error(f"Ошибка при обработке запроса погоды: {e}")

# Обработчик кнопки "Поиск товаров"
@dp.callback_query(F.data == "products")
async def process_products_callback(callback: types.CallbackQuery):
    """Обработчик нажатия на кнопку поиска товаров"""
    try:
        global current_mode
        await callback.answer()
        current_mode = BotMode.PRODUCTS  # Устанавливаем режим поиска товаров
        
        products_text = (
            "🛒 **Поиск товаров** 🛒\n\n"
            "🔍 Опишите товар, который хотите найти:\n\n"
            "💡 **Примеры запросов:**\n"
            "• iPhone 15\n"
            "• Ноутбук ASUS\n"
            "• Фен Dyson\n"
            "• Кроссовки Nike\n\n"
            "📱 **После ввода запроса откроется Яндекс.Маркет**\n"
            "где вы сможете сравнить цены и выбрать лучшее предложение!\n\n"
            "💭 **Введите название товара:**"
        )
        
        await callback.message.edit_text(
            products_text,
            parse_mode="Markdown",
            reply_markup=get_products_keyboard()
        )
        logger.info(f"Пользователь {callback.from_user.id} нажал на кнопку поиска товаров")
        
    except Exception as e:
        logger.error(f"Ошибка при обработке поиска товаров: {e}")

# Обработчик кнопки "Поиск жилья"
@dp.callback_query(F.data == "real_estate")
async def process_real_estate_callback(callback: types.CallbackQuery):
    """Обработчик нажатия на кнопку поиска жилья"""
    try:
        global current_mode
        await callback.answer()
        current_mode = BotMode.REAL_ESTATE  # Устанавливаем режим поиска жилья
        
        real_estate_text = (
            "🏠 **Поиск жилья** 🏠\n\n"
            "🔍 Опишите, что вы ищете:\n\n"
            "💡 **Примеры запросов:**\n"
            "• 1-комнатная квартира\n"
            "• 2-комнатная квартира аренда\n"
            "• Дом продажа\n"
            "• Студия Москва\n\n"
            "📱 **После ввода запроса откроется Авито**\n"
            "где вы сможете просмотреть все доступные варианты!\n\n"
            "💭 **Введите описание жилья:**"
        )
        
        await callback.message.edit_text(
            real_estate_text,
            parse_mode="Markdown",
            reply_markup=get_real_estate_keyboard()
        )
        logger.info(f"Пользователь {callback.from_user.id} нажал на кнопку поиска жилья")
        
    except Exception as e:
        logger.error(f"Ошибка при обработке поиска жилья: {e}")

# Обработчик кнопки "Назад"
@dp.callback_query(F.data == "back_to_menu")
async def process_back_to_menu(callback: types.CallbackQuery):
    """Обработчик возврата в главное меню"""
    try:
        global current_mode
        await callback.answer()
        current_mode = BotMode.IDLE  # Возвращаемся в главное меню
        
        welcome_text = (
            "🌟 **Главное меню** 🌟\n\n"
            "🎯 **Выберите нужную функцию:**\n\n"
            "🌤️ **Прогноз погоды** - узнайте погоду в любом городе\n"
            "🛒 **Поиск товаров** - найдите нужные товары по выгодным ценам\n"
            "🏠 **Поиск жилья** - подберите квартиру или дом для покупки/аренды"
        )
        
        await callback.message.edit_text(
            welcome_text,
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
        logger.info(f"Пользователь {callback.from_user.id} вернулся в главное меню")
        
    except Exception as e:
        logger.error(f"Ошибка при возврате в главное меню: {e}")

# Универсальный обработчик текстовых сообщений
@dp.message(F.content_type == ContentType.TEXT)
async def process_text_message(message: types.Message):
    """Обработчик текстовых сообщений в зависимости от текущего режима"""
    try:
        global current_mode
        
        text = message.text.strip()
        
        # Проверяем, что это не команда
        if text.startswith('/'):
            return
        
        # Обрабатываем сообщения в зависимости от текущего режима
        if current_mode == BotMode.WEATHER:
            await process_weather_city_logic(message, text)
        elif current_mode == BotMode.PRODUCTS:
            await process_products_search_logic(message, text)
        elif current_mode == BotMode.REAL_ESTATE:
            await process_real_estate_search_logic(message, text)
        else:
            # Если мы в главном меню или другом режиме, показываем подсказку
            await message.answer(
                "🤔 **Используйте кнопки для навигации** 🤔\n\n"
                "👇 Выберите нужную функцию ниже:",
                parse_mode="Markdown",
                reply_markup=get_main_keyboard()
            )
        
    except Exception as e:
        logger.error(f"Ошибка при обработке текстового сообщения: {e}")

# Логика обработки запроса погоды
async def process_weather_city_logic(message: types.Message, city_name: str):
    """Логика обработки запроса погоды"""
    try:
        # Получаем координаты города
        coords = get_city_coordinates(city_name)
        
        if not coords:
            await message.answer(
                f"❌ Город '{city_name}' не найден в базе данных.\n\n"
                "📍 **Попробуйте ввести:**\n"
                "• Москва\n"
                "• СПб\n"
                "• Салехард\n"
                "• Тюмень\n"
                "• Самара\n"
                "• Тольятти\n"
                "• Новокуйбышевск\n"
                "• Село Горки\n"
                "• Село Мордово\n\n"
                "🔙 Или вернитесь в главное меню:",
                parse_mode="Markdown",
                reply_markup=get_weather_keyboard()
            )
            return
        
        # Получаем прогноз погоды
        weather_data = get_weather_forecast(coords['lat'], coords['lon'])
        
        if weather_data:
            weather_message = format_weather_message(weather_data, city_name)
            await message.answer(
                weather_message,
                parse_mode="Markdown",
                reply_markup=get_weather_keyboard()
            )
            logger.info(f"Прогноз погоды отправлен пользователю {message.from_user.id} для города {city_name}")
        else:
            await message.answer(
                "❌ Не удалось получить данные о погоде.\n\n"
                "🔄 Попробуйте еще раз или выберите другой город:",
                reply_markup=get_weather_keyboard()
            )
            
    except Exception as e:
        logger.error(f"Ошибка при обработке запроса погоды для города {city_name}: {e}")
        await message.answer(
            "❌ Произошла ошибка при получении прогноза погоды.\n\n"
            "🔄 Попробуйте еще раз:",
            parse_mode="Markdown",
            reply_markup=get_weather_keyboard()
        )

# Логика поиска товаров
async def process_products_search_logic(message: types.Message, product_query: str):
    """Логика поиска товаров"""
    try:
        if not product_query:
            await message.answer(
                "❌ Пожалуйста, введите название товара для поиска:",
                parse_mode="Markdown",
                reply_markup=get_products_keyboard()
            )
            return
        
        # Формируем ссылку на Яндекс.Маркет
        from urllib.parse import quote
        encoded_query = quote(product_query)
        market_url = f"https://market.yandex.ru/search?text={encoded_query}"
        
        # Отправляем ссылку с описанием
        response_text = (
            f"🛒 **Результаты поиска: {product_query}** 🛒\n\n"
            f"🔗 **Откройте Яндекс.Маркет для просмотра результатов:**\n"
            f"{market_url}\n\n"
            f"📊 **На Яндекс.Маркет вы сможете:**\n"
            f"• Сравнить цены разных продавцов\n"
            f"• Читать отзывы покупателей\n"
            f"• Выбрать удобный способ доставки\n"
            f"• Найти лучшие предложения\n\n"
            f"💡 **Совет:** Откройте ссылку в браузере на вашем устройстве!"
        )
        
        # Inline кнопка для быстрого перехода
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🛒 Открыть Яндекс.Маркет", 
                        url=market_url
                    )
                ],
                [
                    InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_menu")
                ]
            ]
        )
        
        await message.answer(
            response_text,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        logger.info(f"Поиск товара '{product_query}' для пользователя {message.from_user.id}")
        
    except Exception as e:
        logger.error(f"Ошибка при поиске товара {product_query}: {e}")
        await message.answer(
            "❌ Произошла ошибка при поиске товара.\n\n"
            "🔄 Попробуйте еще раз:",
            parse_mode="Markdown",
            reply_markup=get_products_keyboard()
        )

# Логика поиска жилья
async def process_real_estate_search_logic(message: types.Message, property_query: str):
    """Логика поиска жилья"""
    try:
        if not property_query:
            await message.answer(
                "❌ Пожалуйста, введите описание жилья для поиска:",
                parse_mode="Markdown",
                reply_markup=get_real_estate_keyboard()
            )
            return
        
        # Формируем ссылку на Авито недвижимость
        from urllib.parse import quote
        encoded_query = quote(property_query)
        # Используем основной раздел недвижимости Авито с поиском
        avito_url = f"https://www.avito.ru/rossiya/nedvizhimost?q={encoded_query}"
        
        # Отправляем ссылку с описанием
        response_text = (
            f"🏠 **Результаты поиска: {property_query}** 🏠\n\n"
            f"🔗 **Откройте Авито для просмотра результатов:**\n"
            f"{avito_url}\n\n"
            f"🏡 **На Авито вы сможете:**\n"
            f"• Найти квартиры, дома, комнаты\n"
            f"• Сравнить цены разных продавцов\n"
            f"• Посмотреть фото и описания\n"
            f"• Связаться с владельцами\n"
            f"• Выбрать покупку или аренду\n\n"
            f"💡 **Совет:** Откройте ссылку в браузере на вашем устройстве!"
        )
        
        # Inline кнопка для быстрого перехода
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🏠 Открыть Авито", 
                        url=avito_url
                    )
                ],
                [
                    InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_to_menu")
                ]
            ]
        )
        
        await message.answer(
            response_text,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        logger.info(f"Поиск жилья '{property_query}' для пользователя {message.from_user.id}")
        
    except Exception as e:
        logger.error(f"Ошибка при поиске жилья {property_query}: {e}")
        await message.answer(
            "❌ Произошла ошибка при поиске жилья.\n\n"
            "🔄 Попробуйте еще раз:",
            parse_mode="Markdown",
            reply_markup=get_real_estate_keyboard()
        )

# Дополнительная команда /help
@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    """Обработчик команды /help"""
    help_text = (
        "❓ **Помощь по боту** ❓\n\n"
        "🤖 **Доступные команды:**\n"
        "/start - Начать работу с ботом\n"
        "/help - Показать эту справку\n\n"
        "🎯 **Функции бота:**\n"
        "🌤️ Прогноз погоды (УЖЕ РАБОТАЕТ!)\n"
        "🛒 Поиск товаров (УЖЕ РАБОТАЕТ!)\n"
        "🏠 Поиск жилья (УЖЕ РАБОТАЕТ!)\n\n"
        "📞 **Поддержка:**\n"
        "Если у вас есть вопросы или предложения - пишите!"
    )
    
    await message.answer(help_text, parse_mode="Markdown")

# Обработчик неизвестных callback'ов
@dp.callback_query()
async def process_unknown_callback(callback: types.CallbackQuery):
    """Обработчик неизвестных callback'ов"""
    try:
        await callback.answer("Неизвестная команда")
        logger.info(f"Неизвестный callback от пользователя {callback.from_user.id}: {callback.data}")
    except Exception as e:
        logger.error(f"Ошибка при обработке неизвестного callback: {e}")

# Обработчик неизвестных сообщений
@dp.message()
async def unknown_message(message: types.Message):
    """Обработчик неизвестных сообщений"""
    try:
        # Если это не текстовое сообщение, показываем подсказку
        if message.content_type != ContentType.TEXT:
            await message.answer(
                "🤔 **Поддерживаю только текстовые сообщения** 🤔\n\n"
                "👇 Воспользуйтесь кнопками ниже или командой /start\n"
                "для выбора нужной функции!",
                parse_mode="Markdown",
                reply_markup=get_main_keyboard()
            )
        # Если это текст, но мы в неопределенном режиме
        elif current_mode == BotMode.IDLE:
            await message.answer(
                "🤔 **Не понял ваше сообщение** 🤔\n\n"
                "👋 Воспользуйтесь кнопками ниже или командой /start\n"
                "для выбора нужной функции!",
                parse_mode="Markdown",
                reply_markup=get_main_keyboard()
            )
            logger.info(f"Неизвестное сообщение от пользователя {message.from_user.id}: {message.text}")
        
    except Exception as e:
        logger.error(f"Ошибка при обработке неизвестного сообщения: {e}")

async def shutdown():
    """Корректное завершение работы бота"""
    global running
    running = False
    logger.info("Получен сигнал завершения. Останавливаю бота...")
    try:
        await bot.session.close()
        logger.info("Бот успешно остановлен")
    except Exception as e:
        logger.error(f"Ошибка при завершении: {e}")
    sys.exit(0)

def signal_handler(signum, frame):
    """Обработчик сигналов для корректного завершения"""
    logger.info(f"Получен сигнал {signum}. Завершение работы...")
    asyncio.create_task(shutdown())

async def main():
    """Главная функция для запуска бота"""
    # Регистрируем обработчики сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        logger.info("🤖 Запуск Telegram бота 'Бот на все случаи жизни'...")
        logger.info(f"Токен бота: {'*' * (len(BOT_TOKEN) - 10) + BOT_TOKEN[-10:] if len(BOT_TOKEN) > 10 else '***'}")
        logger.info(f"API ключ погоды: {WEATHER_API_KEY[:10]}...")
        
        # Пропускаем накопленные обновления
        await bot.delete_webhook(drop_pending_updates=True)
        
        # Запускаем polling
        logger.info("✅ Бот запущен и готов к работе!")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())  # ИЗМЕНЕНИЕ: добавлен allowed_updates
        
    except Exception as e:
        logger.error(f"❌ Ошибка при запуске бота: {e}")
        await shutdown()

if __name__ == "__main__":
    # Запуск бота
    asyncio.run(main())