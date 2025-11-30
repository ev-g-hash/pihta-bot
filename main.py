import logging
import os
import asyncio
import signal
import sys
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.enums import ContentType
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла (для локальной разработки)
load_dotenv()

# Токен бота - сначала из переменной окружения, потом из .env, потом fallback
BOT_TOKEN = os.getenv('BOT_TOKEN') or "YOUR_BOT_TOKEN_HERE"

# Создание директории для логов СРАЗУ
os.makedirs('/app/logs', exist_ok=True)

# Настройка логирования ПОСЛЕ создания директории
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        # Убираем файл логов для продакшена - используем только консоль
        # logging.FileHandler('/app/logs/bot.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Проверка токена
if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
    logger.error("Токен бота не настроен! Установите переменную окружения BOT_TOKEN")
    sys.exit(1)

# Глобальная переменная для корректного завершения
running = True

# Создание бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Обработчик команды /start
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    """Обработчик команды /start"""
    try:
        await message.answer(
            "🤖 Привет! Я эхо-бот.\n\n"
            "Просто напиши мне любое сообщение, и я отправлю его тебе обратно!\n\n"
            "📝 Поддерживаемые типы сообщений:\n"
            "• Текст\n"
            "• Фотографии\n"
            "• Документы\n"
            "• Стикеры\n"
            "• Аудио\n"
            "• Видео\n"
            "• Голосовые сообщения"
        )
        logger.info(f"Пользователь {message.from_user.id} запустил бота")
    except Exception as e:
        logger.error(f"Ошибка при обработке /start: {e}")

# Обработчик всех текстовых сообщений (эхо-функция)
@dp.message(F.content_type == ContentType.TEXT)
async def echo_message(message: types.Message):
    """Эхо-обработчик - отправляет обратно полученный текст"""
    try:
        # Отправляем обратно текст сообщения
        await message.answer(
            f"📝 **Эхо:** {message.text}\n\n"
            f"🆔 ID сообщения: `{message.message_id}`\n"
            f"👤 Ваш ID: `{message.from_user.id}`\n"
            f"👥 Чат ID: `{message.chat.id}`",
            parse_mode="Markdown"
        )
        logger.info(f"Эхо отправлено пользователю {message.from_user.id}")
    except Exception as e:
        logger.error(f"Ошибка при отправке эхо: {e}")
        await message.answer("Извините, произошла ошибка при обработке вашего сообщения.")

# Обработчик фотографий
@dp.message(F.content_type == ContentType.PHOTO)
async def echo_photo(message: types.Message):
    """Обработчик фотографий"""
    try:
        photo = message.photo[-1]  # Берем фото наибольшего размера
        await message.answer_photo(
            photo=photo.file_id,
            caption=f"🖼️ **Фотография получена!**\n\n"
                    f"📏 Размер файла: `{photo.file_size:,}` байт\n"
                    f"🆔 File ID: `{photo.file_id[:20]}...`\n"
                    f"📐 Разрешение: {photo.width}x{photo.height}",
            parse_mode="Markdown"
        )
        logger.info(f"Фото обработано для пользователя {message.from_user.id}")
    except Exception as e:
        logger.error(f"Ошибка при обработке фото: {e}")

# Обработчик документов
@dp.message(F.content_type == ContentType.DOCUMENT)
async def echo_document(message: types.Message):
    """Обработчик документов"""
    try:
        doc = message.document
        await message.answer_document(
            document=doc.file_id,
            caption=f"📄 **Документ получен!**\n\n"
                    f"📁 Название: `{doc.file_name}`\n"
                    f"📏 Размер: `{doc.file_size:,}` байт\n"
                    f"🆔 MIME тип: `{doc.mime_type}`",
            parse_mode="Markdown"
        )
        logger.info(f"Документ обработан для пользователя {message.from_user.id}")
    except Exception as e:
        logger.error(f"Ошибка при обработке документа: {e}")

# Обработчик стикеров
@dp.message(F.content_type == ContentType.STICKER)
async def echo_sticker(message: types.Message):
    """Обработчик стикеров"""
    try:
        sticker = message.sticker
        await message.answer(
            f"😊 **Стикер получен!**\n\n"
            f"😀 Emoji: `{sticker.emoji}`\n"
            f"📦 Набор: `{sticker.set_name or 'неизвестно'}`\n"
            f"📐 Размер: {sticker.width}x{sticker.height}\n"
            f"🆔 File ID: `{sticker.file_id[:20]}...`",
            parse_mode="Markdown"
        )
        logger.info(f"Стикер обработан для пользователя {message.from_user.id}")
    except Exception as e:
        logger.error(f"Ошибка при обработке стикера: {e}")

# Обработчик аудио
@dp.message(F.content_type == ContentType.AUDIO)
async def echo_audio(message: types.Message):
    """Обработчик аудио"""
    try:
        audio = message.audio
        await message.answer_audio(
            audio=audio.file_id,
            caption=f"🎵 **Аудио получено!**\n\n"
                    f"🎤 Исполнитель: `{audio.performer or 'Неизвестен'}`\n"
                    f"🎼 Название: `{audio.title or 'Без названия'}`\n"
                    f"⏱️ Длительность: `{audio.duration} сек`\n"
                    f"📏 Размер: `{audio.file_size:,}` байт",
            parse_mode="Markdown"
        )
        logger.info(f"Аудио обработано для пользователя {message.from_user.id}")
    except Exception as e:
        logger.error(f"Ошибка при обработке аудио: {e}")

# Обработчик видео
@dp.message(F.content_type == ContentType.VIDEO)
async def echo_video(message: types.Message):
    """Обработчик видео"""
    try:
        video = message.video
        await message.answer_video(
            video=video.file_id,
            caption=f"🎬 **Видео получено!**\n\n"
                    f"⏱️ Длительность: `{video.duration} сек`\n"
                    f"📐 Разрешение: {video.width}x{video.height}\n"
                    f"📏 Размер: `{video.file_size:,}` байт",
            parse_mode="Markdown"
        )
        logger.info(f"Видео обработано для пользователя {message.from_user.id}")
    except Exception as e:
        logger.error(f"Ошибка при обработке видео: {e}")

# Обработчик голосовых сообщений
@dp.message(F.content_type == ContentType.VOICE)
async def echo_voice(message: types.Message):
    """Обработчик голосовых сообщений"""
    try:
        voice = message.voice
        await message.answer_voice(
            voice=voice.file_id,
            caption=f"🎙️ **Голосовое получено!**\n\n"
                    f"⏱️ Длительность: `{voice.duration} сек`\n"
                    f"📏 Размер: `{voice.file_size:,}` байт",
            parse_mode="Markdown"
        )
        logger.info(f"Голосовое обработано для пользователя {message.from_user.id}")
    except Exception as e:
        logger.error(f"Ошибка при обработке голосового: {e}")

# Обработчик неизвестных типов сообщений
@dp.message()
async def unknown_message(message: types.Message):
    """Обработчик неизвестных типов сообщений"""
    try:
        await message.answer(
            f"❓ **Неизвестный тип сообщения!**\n\n"
            f"Тип контента: `{message.content_type}`\n\n"
            f"Попробуйте отправить текст, фото, документ или стикер.",
            parse_mode="Markdown"
        )
        logger.info(f"Неизвестный тип сообщения от пользователя {message.from_user.id}: {message.content_type}")
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
        logger.info("🤖 Запуск Telegram бота...")
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