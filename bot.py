import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# ВСТАВЬТЕ ВАШ ТОКЕН СЮДА
TOKEN = "8617615907:AAEvE6tQZLwbd-Mmz_pPu2soVXpwD_crG4o"

# ПРОГРАММЫ (обновил названия)
PROGRAMS = {
    "recovery": {
        "name": "Восстановление",
        "description": "Мягкая практика для восстановления после нагрузок."
    },
    "resource": {
        "name": "Ресурсный код",
        "description": "Практика для наполнения энергией и внутренним ресурсом."
    },
    "harmony": {
        "name": "Гармония движения",
        "description": "Плавные движения для баланса тела и ума."
    },
    "express": {
        "name": "Экспресс-обновление",
        "description": "Быстрая практика для бодрости и ясности."
    }
}

bot = Bot(token=TOKEN)
dp = Dispatcher()

def main_menu():
    """Главное меню с 4 кнопками"""
    buttons = []
    for key, prog in PROGRAMS.items():
        buttons.append([InlineKeyboardButton(text=prog["name"], callback_data=key)])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "🌟 *Добро пожаловать!*\n\nВыберите программу:",
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )

@dp.callback_query()
async def handle_choice(callback: types.CallbackQuery):
    prog_key = callback.data
    
    # Обработка кнопки "Назад в меню"
    if prog_key == "menu":
        await callback.message.answer(
            "Главное меню:",
            reply_markup=main_menu()
        )
        await callback.answer()
        return
    
    # Обработка выбора программы
    prog = PROGRAMS.get(prog_key)
    if prog:
        await callback.message.answer(
            f"📋 *{prog['name']}*\n\n{prog['description']}\n\n(Видео и аудио будут добавлены позже)",
            parse_mode="Markdown"
        )
        
        back_btn = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 В главное меню", callback_data="menu")]
        ])
        await callback.message.answer("Что дальше?", reply_markup=back_btn)
    else:
        await callback.answer("Такой программы нет")
    
    await callback.answer()

async def main():
    print("✅ Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())