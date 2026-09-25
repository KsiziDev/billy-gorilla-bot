from aiogram import Bot
from aiogram.types import LabeledPrice
from config import PRICE_PRO, PRICE_LIFETIME, PRICE_PROGRAM


async def send_pro_invoice(bot: Bot, chat_id: int):
    await bot.send_invoice(
        chat_id=chat_id,
        title="PRO подписка на 30 дней",
        description="Полная программа, адаптив, аналитика, уроки питания",
        payload="pro_monthly",
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label="PRO 30 дней", amount=PRICE_PRO)],
    )


async def send_lifetime_invoice(bot: Bot, chat_id: int):
    await bot.send_invoice(
        chat_id=chat_id,
        title="LIFETIME доступ",
        description="Всё навсегда. Без подписок.",
        payload="lifetime",
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label="Lifetime", amount=PRICE_LIFETIME)],
    )


async def send_program_invoice(bot: Bot, chat_id: int):
    await bot.send_invoice(
        chat_id=chat_id,
        title="Персональная программа",
        description="Программа на 8-12 недель под твои параметры",
        payload="program_once",
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label="Программа", amount=PRICE_PROGRAM)],
    )
