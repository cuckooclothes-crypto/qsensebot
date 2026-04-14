import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from typing import Callable, Dict, Any, Awaitable

# ===== НАСТРОЙКИ =====
TOKEN = "8617615907:AAEvE6tQZLwbd-Mmz_pPu2soVXpwD_crG4o"
ADMIN_ID = 854447207  # ЗАМЕНИТЕ НА СВОЙ TELEGRAM ID

# Список разрешённых пользователей (загружается при старте)
ALLOWED_USERS = []

# Хранилище заявок (в памяти)
PENDING_REQUESTS = {}  # {user_id: {"username": "...", "full_name": "..."}}

# Программы
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

# ===== ПРОВЕРКА ДОСТУПА =====
def is_user_allowed(user_id: int) -> bool:
    return user_id in ALLOWED_USERS

# Middleware для проверки доступа
class AccessMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user = None
        if hasattr(event, 'from_user'):
            user = event.from_user
        elif hasattr(event, 'message') and event.message:
            user = event.message.from_user
        elif hasattr(event, 'callback_query') and event.callback_query:
            user = event.callback_query.from_user
        
        if user:
            user_id = user.id
            
            # Команды, доступные даже без доступа
            is_auth_command = False
            if hasattr(event, 'message') and event.message:
                text = event.message.text or ""
                if text.startswith('/start') or text.startswith('/request') or text.startswith('/myid'):
                    is_auth_command = True
            if hasattr(event, 'callback_query') and event.callback_query:
                if event.callback_query.data in ["request_access", "menu"]:
                    is_auth_command = True
            
            if not is_user_allowed(user_id) and not is_auth_command:
                await event.message.answer(
                    "🚫 *Доступ запрещён*\n\n"
                    "Нажмите кнопку ниже, чтобы отправить заявку администратору.",
                    reply_markup=request_access_keyboard(),
                    parse_mode="Markdown"
                )
                if hasattr(event, 'callback_query') and event.callback_query:
                    await event.callback_query.answer()
                return
        
        return await handler(event, data)

def request_access_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Подать заявку на доступ", callback_data="request_access")]
    ])

def main_menu():
    buttons = []
    for key, prog in PROGRAMS.items():
        buttons.append([InlineKeyboardButton(text=prog["name"], callback_data=key)])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ===== КОМАНДА /start =====
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    
    if is_user_allowed(user_id):
        await message.answer(
            "🌟 *Добро пожаловать!*\n\nВыберите программу:",
            reply_markup=main_menu(),
            parse_mode="Markdown"
        )
    else:
        await message.answer(
            "🌟 *Добро пожаловать!*\n\n"
            "Этот бот содержит закрытый контент.\n"
            "Чтобы получить доступ, нажмите кнопку ниже и дождитесь одобрения администратора.",
            reply_markup=request_access_keyboard(),
            parse_mode="Markdown"
        )

# ===== ОТПРАВКА ЗАЯВКИ =====
@dp.callback_query(lambda c: c.data == "request_access")
async def request_access(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    username = callback.from_user.username or "нет username"
    full_name = callback.from_user.full_name
    
    if is_user_allowed(user_id):
        await callback.message.answer("✅ У вас уже есть доступ! Выберите программу:", reply_markup=main_menu())
        await callback.answer()
        return
    
    # Сохраняем заявку
    PENDING_REQUESTS[user_id] = {
        "username": username,
        "full_name": full_name,
        "user_id": user_id
    }
    
    # Кнопки для администратора
    admin_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Принять", callback_data=f"approve_{user_id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"deny_{user_id}")
        ]
    ])
    
    # Отправляем уведомление администратору
    await bot.send_message(
        ADMIN_ID,
        f"📝 *Новая заявка на доступ!*\n\n"
        f"👤 Имя: {full_name}\n"
        f"🆔 Username: @{username}\n"
        f"📱 ID: `{user_id}`\n"
        f"⏰ Время: {callback.message.date}",
        reply_markup=admin_keyboard,
        parse_mode="Markdown"
    )
    
    await callback.message.answer(
        "✅ *Заявка отправлена!*\n\n"
        "Администратор рассмотрит ваш запрос в ближайшее время.\n"
        "После одобрения вы получите уведомление.",
        parse_mode="Markdown"
    )
    await callback.answer()

# ===== ОБРАБОТКА РЕШЕНИЯ АДМИНИСТРАТОРА =====
@dp.callback_query(lambda c: c.data.startswith("approve_") or c.data.startswith("deny_"))
async def handle_admin_decision(callback: types.CallbackQuery):
    # Проверяем, что команду дал администратор
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ У вас нет прав для этого действия.", show_alert=True)
        return
    
    action, user_id_str = callback.data.split("_")
    user_id = int(user_id_str)
    
    if action == "approve":
        # Добавляем пользователя в белый список
        if user_id not in ALLOWED_USERS:
            ALLOWED_USERS.append(user_id)
        
        # Удаляем заявку из хранилища
        user_info = PENDING_REQUESTS.pop(user_id, {"full_name": "Пользователь"})
        
        # Уведомляем администратора об успехе
        await callback.message.edit_text(
            f"✅ *Пользователь {user_info['full_name']} добавлен в белый список!*",
            parse_mode="Markdown"
        )
        
        # Отправляем пользователю сообщение об одобрении
        try:
            await bot.send_message(
                user_id,
                "🎉 *Доступ одобрен!*\n\n"
                "Добро пожаловать! Теперь вы можете пользоваться ботом.\n"
                "Нажмите /start, чтобы начать.",
                parse_mode="Markdown"
            )
        except Exception as e:
            await callback.message.answer(f"⚠️ Не удалось отправить сообщение пользователю: {e}")
        
        await callback.answer("✅ Пользователь одобрен")
        
    elif action == "deny":
        # Удаляем заявку
        user_info = PENDING_REQUESTS.pop(user_id, {"full_name": "Пользователь"})
        
        # Уведомляем администратора
        await callback.message.edit_text(
            f"❌ *Заявка от {user_info['full_name']} отклонена*",
            parse_mode="Markdown"
        )
        
        # Отправляем пользователю сообщение об отказе
        try:
            await bot.send_message(
                user_id,
                "😔 *Доступ отклонён*\n\n"
                "К сожалению, администратор отклонил вашу заявку.\n"
                "Если вы считаете, что это ошибка, свяжитесь с администратором напрямую.",
                parse_mode="Markdown"
            )
        except Exception as e:
            pass
        
        await callback.answer("❌ Пользователь отклонён")

# ===== КОМАНДА ДЛЯ ПРОВЕРКИ СВОЕГО СТАТУСА =====
@dp.message(Command("status"))
async def check_status(message: types.Message):
    user_id = message.from_user.id
    if is_user_allowed(user_id):
        await message.answer("✅ У вас есть доступ к боту!")
    else:
        await message.answer(
            "⏳ У вас пока нет доступа.\n"
            "Нажмите /start и отправьте заявку администратору."
        )

# ===== ОБРАБОТКА ВЫБОРА ПРОГРАММЫ =====
@dp.callback_query()
async def handle_choice(callback: types.CallbackQuery):
    if not is_user_allowed(callback.from_user.id):
        await callback.answer("⛔ У вас нет доступа. Отправьте заявку через /start", show_alert=True)
        return
    
    if callback.data == "menu":
        await callback.message.answer(
            "Главное меню:",
            reply_markup=main_menu()
        )
        await callback.answer()
        return
    
    prog = PROGRAMS.get(callback.data)
    if prog:
        await callback.message.answer(
            f"📋 *{prog['name']}*\n\n{prog['description']}\n\n(Видео и аудио будут добавлены позже)",
            parse_mode="Markdown"
        )
        back_btn = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 В главное меню", callback_data="menu")]
        ])
        await callback.message.answer("Что дальше?", reply_markup=back_btn)
    await callback.answer()

# ===== КОМАНДА ДЛЯ АДМИНИСТРАТОРА (список пользователей) =====
@dp.message(Command("users"))
async def list_users(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ У вас нет прав.")
        return
    
    if not ALLOWED_USERS:
        await message.answer("📋 Список пользователей пуст.")
        return
    
    users_list = "\n".join([f"• `{uid}`" for uid in ALLOWED_USERS])
    await message.answer(
        f"📋 *Список пользователей с доступом:*\n\n{users_list}\n\nВсего: {len(ALLOWED_USERS)}",
        parse_mode="Markdown"
    )

# ===== ЗАПУСК =====
dp.update.middleware(AccessMiddleware())

async def main():
    print("✅ Бот запущен!")
    print(f"👑 Администратор: {ADMIN_ID}")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())