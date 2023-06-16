#!/usr/bin/env python
# -*- coding: utf-8 -*-
import asyncio
import logging
import random

import config
import photos as p
from aiogram import Bot, types
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.utils.markdown import text
from modules.database import SQLighter
from state import From
from keyboards import inline_keyboard as kb
from text import text_message as t
from modules import send_group_applications
from config import TOKEN

# троллинг
from aiogram.dispatcher.middlewares import BaseMiddleware
from cachetools import TTLCache
from aiogram.dispatcher.handler import CancelHandler

logging.basicConfig(format=u'%(filename)+13s [ LINE:%(lineno)-4s] %(levelname)-8s [%(asctime)s] %(message)s',
                    level=logging.DEBUG)

bot = Bot(token=TOKEN, parse_mode=types.ParseMode.HTML)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
cache = TTLCache(maxsize=float('inf'), ttl=0.5)


class ThrottleMiddleware(BaseMiddleware):
    async def on_process_message(self, message: types.Message, data: dict):
        if not cache.get(message.chat.id):
            cache[message.chat.id] = True
            return
        else:
            raise CancelHandler


dp.middleware.setup(ThrottleMiddleware())

# database____________________
# Connect to the database or create it if it doesn't exist
bd = SQLighter('/home/aid/PycharmProjects/marion_theatre/bd/reservation.db')


# ____________________________
def check_admin(user_id):
    admin_ids = config.ADMIN_ID  # админ

    return user_id in admin_ids


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    user_id = message.from_user.id
    is_admin = check_admin(user_id)  # Функция check_admin должна проверять, является ли пользователь администратором

    if is_admin:
        # Если пользователь является администратором, выводим дополнительные кнопки
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("Рассылка по группам", "Рассылка всем пользователям").add("user menu")
        await message.answer("Добро пожаловать, администратор!", reply_markup=markup)
    else:
        # Если пользователь не администратор, выводим обычное меню
        await message.answer(t.text_start, reply_markup=kb.start_keyboard)


# Функция для рассылки сообщений по user_id
async def send_message_to_user(user_id, message):
    try:
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        yes_button = types.InlineKeyboardButton("Да", callback_data="yes")
        no_button = types.InlineKeyboardButton("Нет", callback_data="no")
        keyboard.add(yes_button, no_button)
        message = await bot.send_message(user_id, message, reply_markup=keyboard)
        print(f"Сообщение отправлено пользователю с ID {user_id}")
        await asyncio.sleep(1)  # Пауза 1 секунда между отправкой каждого сообщения
        return message  # Возвращаем сообщение для дальнейшего использования
    except Exception as e:
        print(f"Ошибка при отправке сообщения пользователю с ID {user_id}: {str(e)}")


@dp.callback_query_handler(lambda query: query.data in ['yes', 'no'])
async def handle_keyboard_callback(query: types.CallbackQuery):
    user_id = query.from_user.id
    answer = query.data
    # Отправить ответ администратору в личные сообщения
    await bot.send_message(config.ADMIN_ID, f"Пользователь {user_id} выбрал {answer}")

    # Удалить клавиатуру у сообщения пользователя
    await bot.edit_message_reply_markup(chat_id=query.message.chat.id, message_id=query.message.message_id,
                                        reply_markup=None)

    await query.answer("Спасибо за ответ!")


@dp.message_handler(Text(equals="Рассылка по группам"))
async def broadcast_all_users(message: types.Message):
    # Получаем данные по количеству резерваций с указанием ID пользователя
    data = bd.get_user_id()
    # Формируем рассылаемое сообщение и отправляем его каждому пользователю
    for row in data:
        locality = row[0]
        user_id = row[1]
        weight = row[2]

        if weight > 0:
            message = f"Вы зарезервировали {weight} билетов для мероприятия в городе {locality}. " \
                      f"Пожалуйста, подтвердите ваше участие!"
            sent_message = await send_message_to_user(user_id, message)

        # Добавляем паузу после отправки каждого пакета сообщений
        if len(data) > 10 and data.index(row) % 10 == 9:
            await asyncio.sleep(60)  # Пауза 1 минута после отправки каждого пакета

    await message.answer("Рассылка завершена.")


@dp.message_handler(Text(equals="user menu"))
async def broadcast_all_users(message: types.Message):
    await message.answer_photo(p.poster_pic, t.text_start, reply_markup=kb.start_keyboard)


# Функция для рассылки сообщений всем
async def send_message_all(user_id, message):
    try:
        await bot.send_message(user_id, message)
        print(f"Сообщение отправлено пользователю с ID {user_id}")
        await asyncio.sleep(1)  # Пауза 1 секунда между отправкой каждого сообщения
    except Exception as e:
        print(f"Ошибка при отправке сообщения пользователю с ID {user_id}: {str(e)}")


@dp.message_handler(Text(equals="Рассылка всем пользователям"))
async def send_message_to_all_users(message: types.Message):
    await message.answer(t.admin_message0)
    await From.ADMIN_MESSAGE.set()
    await message.delete()


@dp.message_handler(state=From.ADMIN_MESSAGE)
async def buy_product_set(message: types.Message, state: FSMContext):
    async with state.proxy() as user_data:
        user_data['ADMIN_MESSAGE'] = message.text.replace('\n', ' ')
    await state.finish()
    # Получаем текст для рассылки из временного хранилища
    admin_message = text(f"{user_data['ADMIN_MESSAGE']}")

    # Получаем список всех пользователей
    all_users = bd.get_all_users()

    # Ограничение на количество сообщений, отправляемых ботом в единицу времени
    message_limit = 2

    for row in all_users:
        user_id = row[0]
        try:
            # Отправляем сообщение пользователю
            await send_message_all(user_id, admin_message)
        except Exception as e:
            print(f"Ошибка при отправке сообщения пользователю с ID {user_id}: {str(e)}")

        # Пауза между отправкой сообщений, чтобы не превысить лимит
        await asyncio.sleep(1 / message_limit)

    await message.edit_text("Рассылка завершена.")


@dp.callback_query_handler(lambda c: c.data == 'information_theatre0')
async def info_theatre(call: types.CallbackQuery):
    await call.answer(cache_time=1)
    num_photos = 3
    selected_photos = random.sample(p.all_photos, num_photos)
    photos = [
        types.InputMediaPhoto(media=photo['media'], caption=photo['caption'])
        for photo in selected_photos
    ]
    await bot.send_media_group(call.message.chat.id, media=photos)
    await asyncio.sleep(0.5)
    await call.message.answer(t.information_theatre_text, reply_markup=kb.back)


# next perfomance
@dp.callback_query_handler(lambda c: c.data == 'next_performance0')
async def next_perfomance(call: types.CallbackQuery):
    await call.answer(cache_time=1)
    await call.message.edit_text(t.next_performance_text, reply_markup=kb.back)


@dp.callback_query_handler(lambda c: c.data == 'back0')
async def back(call: types.CallbackQuery):
    await call.answer(cache_time=1)
    await call.message.edit_text(t.text_start, reply_markup=kb.start_keyboard)


# начинаем опрос
@dp.callback_query_handler(lambda c: c.data == 'reservation_buy0')
async def buy_product_set(call: types.CallbackQuery):
    await call.message.answer(t.text_set0)
    await From.TIKET_APPLICATION.set()
    await call.message.delete()


# возможность отмены опроса
@dp.message_handler(state='*', commands='cancel')
@dp.message_handler(Text(equals='отмена', ignore_case=True), state='*')
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.finish()
    cancel_text = text(
        "До новых встреч 😉"
    )
    markup = types.ReplyKeyboardRemove()
    await message.answer(cancel_text, reply_markup=markup)
    await asyncio.sleep(2)
    await message.answer_photo(p.poster_pic, t.text_start, reply_markup=kb.start_keyboard)


@dp.message_handler(state=From.TIKET_APPLICATION)
async def translation(message: types.Message, state: FSMContext):
    async with state.proxy() as user_data:
        user_data['TIKET_APPLICATION'] = message.text
    await From.next()
    await message.answer(t.text_set1)


# ловим ответ
def is_valid_number(number):
    return number.isdigit() and len(number) <= 9


@dp.message_handler(lambda message: not is_valid_number(message.text), state=From.PHONE_NUMBER)
async def only_numbers_invalid(message: types.Message):
    await message.answer("<b>Упс, вы, наверное, ввели неправильный номер телефона...</b>\n\n"
                         "<i>Укажите номер в цифрах без пробелов и символов или нажмите /cancel</i>")


@dp.message_handler(state=From.PHONE_NUMBER)
async def buy_product_set(message: types.Message, state: FSMContext):
    async with state.proxy() as user_data:
        user_data['PHONE_NUMBER'] = message.text.replace('\n', ' ')
    await From.next()
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.row("📍Wrocław").add("Отмена")
    await message.answer(t.text_set2, reply_markup=markup)


@dp.message_handler(lambda message: message.text not in ["📍Wrocław"], state=From.LOCALITY)
async def translation_invalid(message: types.Message):
    await message.answer("Выберите город или нажмите 'Отмена' для возврата в главное меню.")


@dp.message_handler(state=From.LOCALITY)
async def buy_product_set(message: types.Message, state: FSMContext):
    async with state.proxy() as user_data:
        user_data['LOCALITY'] = message.text.replace('\n', ' ')
    await From.next()
    markup = types.ReplyKeyboardRemove(selective=True)
    await message.answer(t.text_set3, reply_markup=markup)


@dp.message_handler(lambda message: not message.text.isdigit(), state=From.NUMBER_OF_TICKETS)
async def only_numbers_invalid(message: types.Message):
    await message.answer("Напишите количество цифрами <i>или нажмите /cancel</i>")


@dp.message_handler(state=From.NUMBER_OF_TICKETS)
async def translation(message: types.Message, state: FSMContext):
    async with state.proxy() as user_data:
        user_data['NUMBER_OF_TICKETS'] = message.text
    await From.next()
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add("Да", "Отмена")
    await message.answer(f"Вы зарезервировали <b>{user_data['NUMBER_OF_TICKETS']}</b> 🎟\n"
                         f"На имя <b>{user_data['TIKET_APPLICATION']}</b>\n"
                         f"В городе {user_data['LOCALITY']}\n"
                         f"и указали этот <b>+48{user_data['PHONE_NUMBER']}</b> номер телефона для связи.\n\n"
                         f"Подтвердить и отправить?", reply_markup=markup)


@dp.message_handler(lambda message: message.text not in ["Да", "Отмена"], state=From.SEND_YES)
async def translation_invalid(message: types.Message):
    await message.answer("Нажмите 'Да' для подтверждения или 'Отмена' для возврата в главное меню.")


@dp.message_handler(state=From.SEND_YES)
async def translation(message: types.Message, state: FSMContext):
    async with state.proxy() as user_data:
        user_data['SEND_YES'] = message.text
    buy_product = user_data['TIKET_APPLICATION']
    phone_number = user_data['PHONE_NUMBER']
    user_locality = user_data['LOCALITY']
    weight_data = user_data['NUMBER_OF_TICKETS']
    userinfo_id = message.from_user.id
    userinfo_first_name = message.from_user.first_name
    userinfo_last_name = message.from_user.last_name
    userinfo_username = message.from_user.username
    userinfo_language = message.from_user.language_code
    bd.user_add_reservation(buy_product, user_locality, weight_data, userinfo_id)
    await asyncio.sleep(1)
    send_user_message = text(
        "\n     <b>Спасибо. \nМы будем очень рады видеть вас на нашем спектакле!</b>" + "👍",
        "\n\n<i>Вам придет оповещение о необходимости подтвердить участие.</i>")
    markup = types.ReplyKeyboardRemove(selective=True)
    await message.answer(send_user_message, reply_markup=markup)
    locality_data = bd.get_reservation()
    sale_view_text = "Зарезервировано:\n"
    for locality in locality_data:
        sale_view_text += f"В {locality[0]} 🎟 {locality[1]} \n"
    await send_group_applications.send(f"ник в telegram @{userinfo_username}"
                                       f"\n\nБилеты на имя:"
                                       f"\n     🟢   {buy_product}"
                                       f"\n     📞   +48{phone_number}"
                                       f"\n\nLocal: '{user_locality}'"
                                       f"\nКоличество 🎟: '{weight_data}'"
                                       f"\n\n_______________________________\n"
                                       f"{sale_view_text}"
                                       f"\n_______________________________"
                                       f"\nℹ️ о пользователе: ℹ️"
                                       f"\n\nuser_id🟢   {userinfo_id}"
                                       f"\n👤    {userinfo_first_name} {userinfo_last_name}"
                                       f"\nЯзык месседжера🔘 '{userinfo_language}'"
                                       f"\n_______________________________")
    await asyncio.sleep(3)
    await message.answer_photo(p.poster_pic, t.text_start, reply_markup=kb.start_keyboard)
    await state.finish()


@dp.message_handler(commands=['help'])
async def help_message(message: types.Message):
    await message.answer('Опишите свою проблему и мы постораемся её решить.')
    await From.HELP.set()
    await message.delete()


@dp.message_handler(state=From.HELP)
async def translation(message: types.Message, state: FSMContext):
    async with state.proxy() as user_data:
        user_data['HELP'] = message.text
    await state.finish()
    userinfo_first_name = message.from_user
    await message.answer(f"Это сообщения из меню /help\n\n"
                         f"<< {user_data['HELP']} >>\n\n"
                         f"Полная информация о пользователе:\n"
                         f"{userinfo_first_name}")


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
