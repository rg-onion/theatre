from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

send_user_reservation0 = InlineKeyboardButton('Подтвердить резервацию', callback_data='send_user_reservation0')

keyboard_admin = InlineKeyboardMarkup().add(send_user_reservation0)
