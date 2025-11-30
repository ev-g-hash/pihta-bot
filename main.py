import logging
import os
import asyncio
import signal
import sys
import requests
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.enums import ContentType
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла (для локальной разработки)
load_dotenv()

# Токен бота и API ключ погоды из переменных окружения
BOT_TOKEN = os.getenv('BOT_TOKEN') or "YOUR_BOT_TOKEN_HERE"
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')

# Создание директории для логов
os.makedirs('/app/logs', exist_ok=True)

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

# Глобальная переменная для корректного завершения
running = True

# Создание бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Создание inline клавиатуры с кнопками
def get_main_keyboard():
    """Создает основную клавиатуру с кнопками"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🌤️ Посмотреть прогноз погоды", callback_data="weather"),
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

# Функция для получения координат города
def get_city_coordinates(city_name):
    """Получает координаты города через Яндекс Геокодер"""
    try:
        # Для простоты используем предопределенные координаты популярных городов
        city_coords = {
            'москва': {'lat': 55.7558, 'lon': 37.6176},
            'спб': {'lat': 59.9311, 'lon': 30.3609},
            'санкт-петербург': {'lat': 59.9311, 'lon': 30.3609},
            'новосибирск': {'lat': 55.0084, 'lon': 82.9357},
            'екатеринбург': {'lat': 56.8389, 'lon': 60.6057},
            'нижний новгород': {'lat': 56.2965, 'lon': 43.9361},
            'казань': {'lat': 55.8304, 'lon': 49.0661},
            'челябинск': {'lat': 55.1644, 'lon': 61.4368},
            'омск': {'lat': 54.9885, 'lon': 73.3242},
            'самара': {'lat': 53.1959, 'lon': 50.1008},
            'ростов': {'lat': 47.2357, 'lon': 39.7015},
            'уфа': {'lat': 54.7388, 'lon': 55.9721},
            'красноярск': {'lat': 56.0153, 'lon': 92.8932},
            'воронеж': {'lat': 51.6755, 'lon': 39.2089},
            'пермь': {'lat': 58.0105, 'lon': 56.2502}
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
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка запроса к API погоды: {e}")
        return None
    except Exception as e:
        logger.error(f"Неожиданная ошибка при получении погоды: {e}")
        return None

# Функция для форматирования прогноза погоды
def format_weather_message(weather_data, city_name):
    """Форматирует сообщение с прогнозом погоды"""
    try:
        if not weather_data or 'forecasts' not in weather_data:
            return "❌ Не удалось получить данные о погоде. Попробуйте позже."
        
        current = weather_data['fact']
        forecasts = weather_data['forecasts']
        
        # Эмодзи для условий погоды
        weather_emojis = {
            'clear': '☀️',
            'partly-cloudy': '⛅',
            'cloudy': '☁️',
            'overcast': '☁️',
            'drizzle': '🌦️',
            'light-rain': '🌦️',
            'rain': '🌧️',
            'moderate-rain': '🌧️',
            'heavy-rain': '🌧️',
            'thunderstorm': '⛈️',
            'snow': '❄️',
            'snowfall': '❄️'
        }
        
        condition = current.get('condition', 'unknown')
        icon = weather_emojis.get(condition, '🌤️')
        
        # Температура
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
        
        # Влажность
        humidity = current.get('humidity', 0)
        pressure = current.get('pressure_mm', 0)
        
        message = f"🌤️ **Погода в {city_name.title()}** 🌤️\n\n"
        message += f"{icon} **{condition}**\n\n"
        message += f"🌡️ **Температура:** {temp:+d}°C\n"
        message += f"🌡️ **Ощущается как:** {feels_like:+d}°C\n\n"
        
        if wind_speed > 0:
            message += f"💨 **Ветер:** {wind_dir_ru} {wind_speed} м/с\n"
        
        if humidity > 0:
            message += f"💧 **Влажность:** {humidity}%\n"
        
        if pressure > 0:
            message += f"📊 **Давление:** {pressure} мм рт.ст.\n"
        
        message += "\n📅 **Прогноз на 2 дня:**\n"
        
        for i, forecast in enumerate(forecasts[:2]):
            date_parts = forecast['date'].split('-')
            day_name = forecast.get('parts', [{}])[0]
            
            temp_min = day_name.get('temp_min', 0)
            temp_max = day_name.get('temp_max', 0)
            condition_day = day_name.get('condition', 'unknown')
            icon_day = weather_emojis.get(condition_day, '🌤️')
            
            message += f"📅 **{date_parts[2]}.{date_parts[1]}:** {icon_day} {temp_min:+d}°...{temp_max:+d}°C\n"
        
        return message
        
    except Exception as e:
        logger.error(f"Ошибка при форматировании прогноза погоды: {e}")
        return "❌ Ошибка при обработке данных о погоде."

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
        await callback.answer()
        
        weather_text = (
            "🌤️ **Прогноз погоды** 🌤️\n\n"
            "🔍 Введите название города для получения прогноза погоды:\n\n"
            "📍 **Поддерживаемые города:**\n"
            "• Москва\n"
            "• Санкт-Петербург\n"
            "• Новосибирск\n"
            "• Екатеринбург\n"
            "• Нижний Новгород\n"
            "• Казань\n"
            "• Челябинск\n"
            "• Омск\n"
            "• Самара\n\n"
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

# Обработчик текстовых сообщений в режиме погоды
@dp.message(F.content_type == ContentType.TEXT)
async def process_weather_city(message: types.Message):
    """Обработчик ввода города для получения прогноза"""
    try:
        city_name = message.text.strip()
        
        # Проверяем, что это не команда
        if city_name.startswith('/'):
            return
        
        # Получаем координаты города
        coords = get_city_coordinates(city_name)
        
        if not coords:
            await message.answer(
                f"❌ Город '{city_name}' не найден в базе данных.\n\n"
                "📍 **Попробуйте ввести:**\n"
                "• Москва\n"
                "• СПб\n"
                "• Новосибирск\n"
                "• Екатеринбург\n"
                "• Казань\n\n"
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
        logger.error(f"Ошибка при обработке запроса погоды для города {message.text}: {e}")
        await message.answer(
            "❌ Произошла ошибка при получении прогноза погоды.\n\n"
            "🔄 Попробуйте еще раз:",
            reply_markup=get_weather_keyboard()
        )

# Обработчик кнопки "Назад"
@dp.callback_query(F.data == "back_to_menu")
async def process_back_to_menu(callback: types.CallbackQuery):
    """Обработчик возврата в главное меню"""
    try:
        await callback.answer()
        
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

# Обработчик кнопки "Поиск товаров"
@dp.callback_query(F.data == "products")
async def process_products_callback(callback: types.CallbackQuery):
    """Обработчик нажатия на кнопку поиска товаров"""
    try:
        await callback.answer()
        
        products_text = (
            "🛒 **Поиск товаров** 🛒\n\n"
            "🔍 Функция поиска товаров в разработке!\n\n"
            "📋 **Как это будет работать:**\n"
            "• Опишите нужный товар\n"
            "• Сравните цены в разных магазинах\n"
            "• Найдете лучшие предложения\n"
            "• Получите ссылки на покупку\n\n"
            "🏪 **Источники данных:**\n"
            "• Яндекс.Маркет\n"
            "• Wildberries\n"
            "• Ozon\n"
            "• Авито\n\n"
            "⏳ **Скоро будет доступно!**"
        )
        
        await callback.message.edit_text(
            products_text,
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
        logger.info(f"Пользователь {callback.from_user.id} нажал на кнопку поиска товаров")
        
    except Exception as e:
        logger.error(f"Ошибка при обработке поиска товаров: {e}")

# Обработчик кнопки "Поиск жилья"
@dp.callback_query(F.data == "real_estate")
async def process_real_estate_callback(callback: types.CallbackQuery):
    """Обработчик нажатия на кнопку поиска жилья"""
    try:
        await callback.answer()
        
        real_estate_text = (
            "🏠 **Поиск жилья** 🏠\n\n"
            "🔍 Функция поиска недвижимости в разработке!\n\n"
            "🏡 **Как это будет работать:**\n"
            "• Укажите город и район\n"
            "• Выберите тип жилья (квартира/дом)\n"
            "• Задайте ценовой диапазон\n"
            "• Получите подходящие варианты\n\n"
            "📊 **Информация о жилье:**\n"
            "• Фотографии и планировка\n"
            "• Цена за м²\n"
            "• Инфраструктура района\n"
            "• Транспортная доступность\n\n"
            "⏳ **Скоро будет доступно!**"
        )
        
        await callback.message.edit_text(
            real_estate_text,
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
        logger.info(f"Пользователь {callback.from_user.id} нажал на кнопку поиска жилья")
        
    except Exception as e:
        logger.error(f"Ошибка при обработке поиска жилья: {e}")

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
        "🛒 Поиск товаров (скоро)\n"
        "🏠 Поиск жилья (скоро)\n\n"
        "📞 **Поддержка:**\n"
        "Если у вас есть вопросы или предложения - пишите!"
    )
    
    await message.answer(help_text, parse_mode="Markdown")

# Обработчик неизвестных текстовых сообщений
@dp.message()
async def unknown_message(message: types.Message):
    """Обработчик неизвестных сообщений"""
    try:
        unknown_text = (
            "🤔 **Не понял ваше сообщение** 🤔\n\n"
            "👋 Воспользуйтесь кнопками ниже или командой /start\n"
            "для выбора нужной функции!"
        )
        
        await message.answer(
            unknown_text,
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
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"❌ Ошибка при запуске бота: {e}")
        await shutdown()

if __name__ == "__main__":
    # Запуск бота
    asyncio.run(main())