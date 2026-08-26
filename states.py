from aiogram.fsm.state import State, StatesGroup

class ProductState(StatesGroup):
    name = State()
    description = State()
    price = State()
    code = State()
    discount = State()

class SearchState(StatesGroup):
    code = State()

class OrderState(StatesGroup):
    delivery_type = State()
    address = State()