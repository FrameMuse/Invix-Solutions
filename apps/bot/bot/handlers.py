import html
import logging
from io import BytesIO

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, Message, User

from bot.api import ProductApi
from bot.config import Settings
from bot.keyboards import catalog_keyboard

logger = logging.getLogger(__name__)
router = Router(name="catalog")

INSTRUCTION = "Пришлите фото товара, а в подписи укажите название."
START_TEXT = "У меня есть товар.\nОткройте каталог, чтобы посмотреть товары."


def is_admin_user(user: User | None, settings: Settings) -> bool:
    if user is None:
        return False
    if user.id in settings.admin_ids:
        return True
    username = (user.username or "").casefold()
    return bool(username) and username in settings.admin_usernames


def is_admin(message: Message, settings: Settings) -> bool:
    return is_admin_user(message.from_user, settings)


def sender_id(message: Message) -> int:
    return message.from_user.id if message.from_user else 0


async def send_catalog(message: Message, settings: Settings) -> None:
    await message.answer(
        START_TEXT,
        reply_markup=catalog_keyboard(settings.webapp_url, is_admin(message, settings)),
    )


@router.message(CommandStart())
async def start(message: Message, settings: Settings) -> None:
    await send_catalog(message, settings)


@router.message(Command("add"))
async def add(message: Message, settings: Settings) -> None:
    if not is_admin(message, settings):
        await message.answer(f"Вы не администратор. Ваш ID: {sender_id(message)}")
        return
    await message.answer(INSTRUCTION)


@router.message(Command("id"))
async def show_id(message: Message) -> None:
    await message.answer(f"Ваш ID: {sender_id(message)}")


@router.message(F.text)
async def text_message(message: Message, settings: Settings) -> None:
    if is_admin(message, settings) and "создать товар" in (message.text or "").casefold():
        await message.answer(INSTRUCTION)
        return
    await send_catalog(message, settings)


@router.callback_query(F.data == "create_product")
async def create_product_callback(callback: CallbackQuery, settings: Settings) -> None:
    if not is_admin_user(callback.from_user, settings):
        await callback.answer("Недостаточно прав", show_alert=True)
        return

    if isinstance(callback.message, Message):
        await callback.message.answer(INSTRUCTION)
    await callback.answer()


@router.message(F.photo)
async def create_product(
    message: Message,
    bot: Bot,
    settings: Settings,
    product_api: ProductApi,
) -> None:
    if not is_admin(message, settings):
        await message.answer("Добавлять товары может только администратор.")
        return

    title = (message.caption or "").strip()
    if not title:
        await message.answer("Пришлите фото ещё раз, а в подписи укажите название.")
        return

    buffer = BytesIO()
    try:
        await bot.download(message.photo[-1], destination=buffer)
        await product_api.create_product(title, buffer.getvalue())
    except Exception:
        logger.exception("Failed to create product from message %s", message.message_id)
        await message.answer("Не удалось добавить товар. Попробуйте ещё раз.")
        return

    await message.answer(f"Товар «{html.escape(title)}» добавлен.")
