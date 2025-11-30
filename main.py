import logging
import os
import asyncio
import signal
import sys
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Импортируем модули
from config import BOT_TOKEN
from weather import register_weather_handlers
from products import register_products_handlers

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

# Создание директории для логов
os.makedirs('/app/logs', exist_ok=True)

# Глобальная переменная для корректного завершения
running = True

# Создание бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ===============================
# КЛАВИАТУРЫ И ИНТЕРФЕЙС
# ===============================

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

# ===============================
# ОБРАБОТЧИКИ СООБЩЕНИЙ
# ===============================

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

# Обработчик кнопки "Назад в меню"
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

# Обработчик кнопки "Поиск жилья" (пока заглушка)
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
        "🛒 Поиск товаров (УЖЕ РАБОТАЕТ!)\n"
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

# ===============================
# ФУНКЦИИ ЗАПУСКА
# ===============================

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
        # Регистрируем все обработчики модулей
        register_weather_handlers(dp)
        register_products_handlers(dp)
        
        logger.info("🤖 Запуск Telegram бота 'Бот на все случаи жизни'...")
        logger.info(f"Токен бота: {'*' * (len(BOT_TOKEN) - 10) + BOT_TOKEN[-10:] if len(BOT_TOKEN) > 10 else '***'}")
        
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