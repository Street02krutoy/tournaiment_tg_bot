import asyncio
import logging
import re
from sqlite3 import IntegrityError
import sys

from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import F, Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    KeyboardButton,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    CallbackQuery,
)
from aiogram.filters import Filter
from dotenv import dotenv_values, load_dotenv
from db import (
    approve_chel,
    create_user,
    get_data,
    get_data_by_sent_id,
    set_about_me,
    set_dota_rating,
    set_steam_url,
)
from states import UserStates

url_pattern = "^https:\\/\\/(?:www\\.)?[-a-zA-Z0-9@:%._\\+~#=]{1,256}\\.[a-zA-Z0-9()]{1,6}\\b(?:[-a-zA-Z0-9()@:%_\\+.~#?&\\/=]*)$"

load_dotenv()
TOKEN = dotenv_values()["TOKEN"]
dp = Dispatcher()
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

cancel_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Отмена")]],
    one_time_keyboard=True,
)

main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Ссылка на стим"), KeyboardButton(text="MMR")],
        [KeyboardButton(text="О себе")],
        [KeyboardButton(text="Посмотреть анкету"), KeyboardButton(text="Отправить")],
    ],
    one_time_keyboard=True,
)


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    try:
        create_user(message.from_user.id)
        await message.answer(
            f"Привет, {html.bold(message.from_user.full_name)} заполни форму, чтобы подать заявку на турнир!",
            reply_markup=main_keyboard,
        )
    except IntegrityError as e:
        await message.answer(
            f"Привет, {html.bold(message.from_user.full_name)} заполни форму, чтобы подать заявку на турнир!",
            reply_markup=main_keyboard,
        )


@dp.message(F.text == "Ссылка на стим")
async def steam_url_set(message: Message, state: FSMContext):
    await state.set_state(state=UserStates.steam_url)
    await message.answer("Напишите ссылку на ваш Steam", reply_markup=cancel_keyboard)


@dp.message(F.text == "MMR")
async def rating_set(message: Message, state: FSMContext):
    await state.set_state(state=UserStates.rating)
    await message.answer("Напишите ваше количество MMR", reply_markup=cancel_keyboard)


@dp.message(F.text == "О себе")
async def about_me_set(message: Message, state: FSMContext):
    await state.set_state(state=UserStates.about_me)
    await message.answer(
        "Напишите данные о себе(роль,предпочтения,характер)",
        reply_markup=cancel_keyboard,
    )


@dp.message(F.text == "Посмотреть анкету")
async def check_data(message: Message, state: FSMContext):
    data = get_data(message.from_user.id)
    await message.answer(
        f"Steam URL: {data.steam_url}\nМмр: {data.dota_rating}\nО себе {data.about_me}",
        reply_markup=main_keyboard,
    )


@dp.message(F.text, UserStates.steam_url)
async def steam_url_set(message: Message, state: FSMContext):
    if re.match(url_pattern, message.text) == None:
        return await message.answer(
            "Введите корректную ссылку", reply_markup=cancel_keyboard
        )
    set_steam_url(message.from_user.id, message.text)
    await state.clear()
    await message.answer(
        f"Привет, {html.bold(message.from_user.full_name)} заполни остальные поля, чтобы подать заявку!",
        reply_markup=main_keyboard,
    )


@dp.message(F.text, UserStates.rating)
async def rating_set(message: Message, state: FSMContext):

    try:
        set_dota_rating(message.from_user.id, int(message.text))
        await state.clear()
        await message.answer(
            f"Привет, {html.bold(message.from_user.full_name)} заполни остальные поля, чтобы подать заявку!",
            reply_markup=main_keyboard,
        )
    except ValueError:
        await message.delete()
        await message.answer(
            f"Напишите корректное число ммр",
            reply_markup=cancel_keyboard,
        )


@dp.message(F.text, UserStates.about_me)
async def about_me_set(message: Message, state: FSMContext):
    set_about_me(message.from_user.id, message.text)
    await state.clear()
    await message.answer(
        f"Привет, {html.bold(message.from_user.full_name)} заполни остальные поля, чтобы подать заявку!",
        reply_markup=main_keyboard,
    )


@dp.message(F.text == "Отмена")
async def cancel(message: Message, state: FSMContext):
    await message.delete()
    await message.answer("Выберите один из пунктов ниже:", reply_markup=main_keyboard)
    await state.clear()


@dp.message(F.text == "Отправить")
async def send_data(message: Message, state: FSMContext):
    data = get_data(message.from_user.id)
    if data.sent_id != None:
        return message.answer(
            "Вы уже отправили данные.", reply_markup=ReplyKeyboardRemove()
        )
    if data.steam_url == None or data.dota_rating == None or data.about_me == None:
        return message.answer("Вы ввели не всю информацию", reply_markup=main_keyboard)
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="одобрить", callback_data="approve"))
    builder.add(InlineKeyboardButton(text="не одобрить", callback_data="decline"))

    msg = await bot.send_message(
        chat_id=dotenv_values()["CHAT_ID"],
        text=f"Steam URL: {data.steam_url}\nМмр: {data.dota_rating}\nО себе {data.about_me}\nтелеграм: @{message.from_user.username} ({message.from_user.id})",
        reply_markup=builder.as_markup(),
    )

    approve_chel(message.from_user.id, msg.message_id)

    await state.clear()

    await message.answer(
        "Данные были успешно отправлены!", reply_markup=ReplyKeyboardRemove()
    )


@dp.callback_query(F.data == "approve")
async def approve_user(callback: CallbackQuery):
    data = get_data_by_sent_id(callback.message.message_id)
    if data == None:
        return await callback.answer("ne ok")
    print(data.id)
    await bot.send_message(
        chat_id=data.id,
        text=f"вы были одобрены",
    )
    await callback.answer("ок")


@dp.callback_query(F.data == "decline")
async def approve_user(callback: CallbackQuery):
    data = get_data_by_sent_id(callback.message.message_id)
    if data == None:
        return await callback.answer("ne ok")
    await bot.send_message(
        chat_id=data.id,
        text=f"вы были не одобрены ",
    )
    await callback.answer("ок")


@dp.message()
async def message(message: Message):
    return


async def main() -> None:

    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
