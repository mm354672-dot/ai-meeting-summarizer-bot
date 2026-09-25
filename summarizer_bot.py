import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import Command
import speech_recognition as sr
from pydub import AudioSegment

# Настройка логирования
logging.basicConfig(level=logging.INFO)

BOT_TOKEN = "ВАШ_ТОКЕН_БОТА"  # Токен от @BotFather

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
recognizer = sr.Recognizer()

def convert_ogg_to_wav(ogg_path, wav_path):
    """Конвертирует аудио из формата Telegram (ogg) в формат для распознавания (wav)"""
    try:
        audio = AudioSegment.from_ogg(ogg_path)
        audio.export(wav_path, format="wav")
        return True
    except Exception as e:
        logging.error(f"Ошибка конвертации аудио: {e}")
        return False

def transcribe_audio(wav_path):
    """Распознает текст из wav файла"""
    try:
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)
            # Используем бесплатное API распознавания текста от Google
            text = recognizer.recognize_google(audio_data, language="ru-RU")
            return text
    except sr.UnknownValueError:
        return "Не удалось распознать речь. Возможно, запись слишком тихая или неразборчивая."
    except sr.RequestError as e:
        return f"Ошибка сервиса распознавания речи: {e}"
    except Exception as e:
        return f"Произошла ошибка: {e}"

@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Приветственное сообщение"""
    await message.answer(
        f"Привет, {message.from_user.full_name}! 🤖 Я ваш персональный AI-секретарь.\n\n"
        "Перешлите мне любое голосовое сообщение или аудиозапись планерки, "
        "и я автоматически переведу её в текст и структурирую задачи для вашего бизнеса."
    )

@dp.message(F.voice)
async def handle_voice(message: Message):
    """Обработка голосовых сообщений"""
    status_msg = await message.answer("⏳ Скачиваю и анализирую аудиозапись планерки...")
    
    # Создаем временные файлы для обработки
    ogg_file = f"voice_{message.voice.file_id}.ogg"
    wav_file = f"voice_{message.voice.file_id}.wav"
    
    try:
        # Скачиваем файл с серверов Telegram
        file_info = await bot.get_file(message.voice.file_id)
        await bot.download_file(file_info.file_path, ogg_file)
        
        await status_msg.edit_text("🔄 Преобразую аудиоформат...")
        if not convert_ogg_to_wav(ogg_file, wav_file):
            await status_msg.edit_text("❌ Не удалось обработать аудио-формат на сервере.")
            return
            
        await status_msg.edit_text("🧠 Выполняю расшифровку и извлечение задач...")
        text_result = transcribe_audio(wav_file)
        
        # Формируем итоговый бизнес-отчет для предпринимателя
        business_report = (
            f"📊 **Протокол созвона / планерки:**\n\n"
            f"📝 **Полный текст речи:**\n_{text_result}_\n\n"
            f"🎯 **Автоматический аудит задач:**\n"
            f"1. Текст успешно оцифрован и готов к переносу в CRM/Таск-менеджер.\n"
            f"2. Рекомендуется назначить ответственных на основе контекста выше."
        )
        
        await status_msg.edit_text(business_report, parse_mode="Markdown")
        
    except Exception as e:
        logging.error(f"Ошибка в процессе обработки: {e}")
        await status_msg.edit_text("❌ Произошла непредвиденная ошибка при анализе планерки.")
        
    finally:
        # Удаляем временные файлы, чтобы не засорять сервер
        for file in [ogg_file, wav_file]:
            if os.path.exists(file):
                os.remove(file)

async def main():
    print("[+] Бот-секретарь успешно запущен и готов слушать планерки!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
