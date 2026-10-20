from urllib.parse import urlparse

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo


def catalog_keyboard(webapp_url: str, include_create: bool = False) -> InlineKeyboardMarkup:
    if urlparse(webapp_url).scheme == "https":
        catalog = InlineKeyboardButton(
            text="Открыть каталог",
            web_app=WebAppInfo(url=webapp_url),
        )
    else:
        catalog = InlineKeyboardButton(text="Открыть каталог", url=webapp_url)

    rows = [[catalog]]
    if include_create:
        rows.append([InlineKeyboardButton(text="Создать товар", callback_data="create_product")])

    return InlineKeyboardMarkup(inline_keyboard=rows)
