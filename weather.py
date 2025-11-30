import logging
import os
import httpx as requests
from aiogram import types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import WEATHER_API_KEY, SUPPORTED_CITIES, WEATHER_EMOJIS, WIND_DIRECTIONS

logger = logging.getLogger(__name__)

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

def format_weather_message(weather_data, city_name):
    """Форматирует сообщение с прогнозом погоды"""
    try:
        if not weather_data:
            return "❌ Не удалось получить данные о погоде. Попробуйте позже."
        
        if 'fact' not in weather_data:
            return f"❌ Неверный формат ответа API для {city_name}. Попробуйте позже."
        
        current = weather_data['fact']
        forecasts = weather_data.get('forecasts', [])
        
        condition = current.get('condition', 'unknown')
        icon = WEATHER_EMOJIS.get(condition, '🌤️')
        
        temp = current.get('temp', 0)
        feels_like = current.get('feels_like', temp)
        
        wind_dir = current.get('wind_dir', '')
        wind_speed = current.get('wind_speed', 0)
        wind_dir_ru = WIND_DIRECTIONS.get(wind_dir, wind_dir)
        
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
        
        if forecasts:
            message += "\n📅 **Прогноз на 2 дня:**\n"
            
            for forecast in forecasts[:2]:
                date_parts = forecast.get('date', '').split('-')
                parts = forecast.get('parts', {})
                day_part = parts.get('day', {})
                
                if day_part:
                    temp_min = day_part.get('temp_min', 0)
                    temp_max = day_part.get('temp_max', 0)
                    condition_day = day_part.get('condition', 'unknown')
                    icon_day = WEATHER_EMOJIS.get(condition_day, '🌤️')
                    
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
            "• Салехард\n"
            "• Тюмень\n"
            "• Самара\n"
            "• Тольятти\n"
            "• Новокуйбышевск\n\n"
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

async def process_weather_city(message: types.Message):
    """Обработчик ввода города для получения прогноза"""
    try:
        city_name = message.text.strip()
        
        if city_name.startswith('/'):
            return
        
        coords = SUPPORTED_CITIES.get(city_name.lower().strip())
        
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
                "• Новокуйбышевск\n\n"
                "🔙 Или вернитесь в главное меню:",
                parse_mode="Markdown",
                reply_markup=get_weather_keyboard()
            )
            return
        
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

def register_weather_handlers(dp):
    """Регистрирует обработчики погоды"""
    dp.callback_query.register(process_weather_callback, F.data == "weather")
    dp.message.register(process_weather_city, F.content_type == "text")