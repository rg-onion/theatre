from aiogram.dispatcher.filters.state import State, StatesGroup


class From(StatesGroup):
    TIKET_APPLICATION = State()
    PHONE_NUMBER = State()
    LOCALITY = State()
    NUMBER_OF_TICKETS = State()
    SEND_YES = State()

    HELP = State()

    ADMIN_MESSAGE = State()


