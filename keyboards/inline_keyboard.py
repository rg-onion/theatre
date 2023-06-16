from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


information_theatre0 = InlineKeyboardButton('О спектакле', callback_data='information_theatre0')
next_performance0 = InlineKeyboardButton('Ближайшее выступление', callback_data='next_performance0')
reservation_get0 = InlineKeyboardButton('Билетов зарезервировано', callback_data='reservation_get0')

reservation_buy0 = InlineKeyboardButton('🎟Зарезервировать билеты🎟', callback_data='reservation_buy0')


# information_theatre1_a = InlineKeyboardButton('Наш instagram', url='https://instagram.com/marion_theatre')
start_keyboard = InlineKeyboardMarkup().add(information_theatre0).add(next_performance0).add(reservation_buy0)

back0 = InlineKeyboardButton('🔙', callback_data='back0')
back = InlineKeyboardMarkup().add(back0)
