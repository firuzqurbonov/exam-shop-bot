import asyncio
from aiogram import Dispatcher, Bot, types, F
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

from states import ProductState, SearchState, OrderState
from db import create_tables, add_user, get_id, add_product, get_products, delete_product
from db import get_product_by_code, get_product, get_users, add_to_cart, get_cart, clear_cart
from db import add_order, add_order_item, get_orders, get_user_orders, update_order_status

TOKEN = '8668062119:AAEYl1SiqWmRkmujB2DgDum6If03XdPSLC4'
ADMIN_ID = 111111111

bot = Bot(token=TOKEN)
dp = Dispatcher()

user_kb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='🛍 Товары'), KeyboardButton(text='🔎 Поиск')],
    [KeyboardButton(text='🧺 Корзина'), KeyboardButton(text='📦 Мои заказы')]
], resize_keyboard=True)

admin_kb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='➕ Добавить товар'), KeyboardButton(text='🛍 Товары')],
    [KeyboardButton(text='👥 Пользователи'), KeyboardButton(text='📦 Заказы')]
], resize_keyboard=True)

@dp.message(Command('start'))
async def start(message: types.Message):
    create_tables()
    add_user(message.from_user.id, message.from_user.first_name)
    
    if message.from_user.id == ADMIN_ID:
        await message.answer("Вы администратор", reply_markup=admin_kb)
    else:
        await message.answer("Вы зарегистрированы", reply_markup=user_kb)

@dp.message(F.text == '➕ Добавить товар')
async def add(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer('Введите название товара')
    await state.set_state(ProductState.name)

@dp.message(ProductState.name)
async def get_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer('Введите описание товара')
    await state.set_state(ProductState.description)

@dp.message(ProductState.description)
async def get_desc(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer('Введите цену товара')
    await state.set_state(ProductState.price)

@dp.message(ProductState.price)
async def get_price(message: types.Message, state: FSMContext):
    await state.update_data(price=int(message.text))
    await message.answer('Введите код товара')
    await state.set_state(ProductState.code)

@dp.message(ProductState.code)
async def get_code(message: types.Message, state: FSMContext):
    await state.update_data(code=message.text)
    await message.answer('Введите скидку (0 если нет)')
    await state.set_state(ProductState.discount)

@dp.message(ProductState.discount)
async def get_discount(message: types.Message, state: FSMContext):
    await state.update_data(discount=int(message.text))
    data = await state.get_data()
    
    add_product(data['name'], data['description'], data['price'], data['code'], data['discount'])
    
    await state.clear()
    await message.answer('Товар добавлен')

@dp.message(F.text == '👥 Пользователи')
async def show_users(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    users = get_users()
    for user in users:
        await message.answer(f"ID: {user[0]}\nTelegram ID: {user[1]}\nИмя: {user[2]}")

@dp.message(F.text == '🛍 Товары')
async def show_products(message: types.Message):
    await send_page(message.chat.id, message.from_user.id, 0)

async def send_page(chat_id, user_tg_id, page):
    offset = page * 5
    products = get_products(offset)
    
    if not products:
        await bot.send_message(chat_id, "Товаров нет")
        return
        
    for product in products:
        id = product[0]
        name = product[1]
        desc = product[2]
        price = product[3]
        code = product[4]
        discount = product[5]
        
        final_price = int(price - (price * discount / 100))
        
        text = f"{name}\n{desc}\nКод: {code}\nЦена: {price}\nСкидка: {discount}%\nЦена со скидкой: {final_price}"
        
        if user_tg_id == ADMIN_ID:
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="❌ Удалить", callback_data=f"delete_{id}")]
            ])
        else:
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🛒 В корзину", callback_data=f"add_{id}")]
            ])
            
        await bot.send_message(chat_id, text, reply_markup=kb)
        
    buttons = []
    if page > 0:
        buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"page_{page-1}"))
    buttons.append(InlineKeyboardButton(text="➡️ Вперёд", callback_data=f"page_{page+1}"))
    
    kb_page = InlineKeyboardMarkup(inline_keyboard=[buttons])
    await bot.send_message(chat_id, f"Страница {page}", reply_markup=kb_page)

@dp.callback_query(F.data.startswith('page_'))
async def paginate(callback: types.CallbackQuery):
    data = callback.data.split('_')
    page = int(data[1])
    await callback.message.delete()
    await send_page(callback.message.chat.id, callback.from_user.id, page)

@dp.callback_query(F.data.startswith('delete_'))
async def del_product(callback: types.CallbackQuery):
    data = callback.data.split('_')
    product_id = int(data[1])
    delete_product(product_id)
    await callback.message.delete()
    await callback.answer("Товар удален")

@dp.message(F.text == '🔎 Поиск')
async def search(message: types.Message, state: FSMContext):
    await message.answer('Введите код товара')
    await state.set_state(SearchState.code)

@dp.message(SearchState.code)
async def get_search_code(message: types.Message, state: FSMContext):
    code = message.text
    product = get_product_by_code(code)
    await state.clear()
    
    if product:
        id = product[0]
        name = product[1]
        desc = product[2]
        price = product[3]
        code = product[4]
        discount = product[5]
        final_price = int(price - (price * discount / 100))
        
        text = f"{name}\n{desc}\nКод: {code}\nЦена: {price}\nСкидка: {discount}%\nЦена со скидкой: {final_price}"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🛒 В корзину", callback_data=f"add_{id}")]
        ])
        await message.answer(text, reply_markup=kb)
    else:
        await message.answer('Товар не найден')

@dp.callback_query(F.data.startswith('add_'))
async def cart_add(callback: types.CallbackQuery):
    data = callback.data.split('_')
    product_id = int(data[1])
    user_id = get_id(callback.from_user.id)
    add_to_cart(user_id, product_id)
    await callback.answer("Товар в корзине")

@dp.message(F.text == '🧺 Корзина')
async def show_cart(message: types.Message):
    user_id = get_id(message.from_user.id)
    cart = get_cart(user_id)
    
    if not cart:
        await message.answer("Корзина пустая")
        return
        
    text = "Ваша корзина:\n\n"
    total = 0
    
    for item in cart:
        cart_id = item[0]
        product_id = item[1]
        quantity = item[2]
        
        product = get_product(product_id)
        name = product[1]
        price = product[3]
        discount = product[5]
        
        final_price = int(price - (price * discount / 100))
        summa = final_price * quantity
        total = total + summa
        
        text += f"{name}\nЦена: {final_price}\nКоличество: {quantity}\nСумма: {summa}\n\n"
        
    text += f"Итог: {total}"
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🧹 Очистить", callback_data="clear_cart")],
        [InlineKeyboardButton(text="✅ Оформить заказ", callback_data="make_order")]
    ])
    await message.answer(text, reply_markup=kb)

@dp.callback_query(F.data == 'clear_cart')
async def clear_cart_handler(callback: types.CallbackQuery):
    user_id = get_id(callback.from_user.id)
    clear_cart(user_id)
    await callback.message.edit_text("Корзина очищена")

@dp.callback_query(F.data == 'make_order')
async def make_order(callback: types.CallbackQuery, state: FSMContext):
    kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text='🚚 Доставка'), KeyboardButton(text='🏬 Самовывоз')]
    ], resize_keyboard=True)
    await callback.message.answer('Выберите тип доставки', reply_markup=kb)
    await state.set_state(OrderState.delivery_type)

@dp.message(OrderState.delivery_type)
async def get_delivery(message: types.Message, state: FSMContext):
    await state.update_data(delivery_type=message.text)
    if message.text == '🚚 Доставка':
        await message.answer('Введите адрес доставки')
        await state.set_state(OrderState.address)
    else:
        await state.update_data(address='Самовывоз')
        await finish_order(message, state)

@dp.message(OrderState.address)
async def get_address(message: types.Message, state: FSMContext):
    await state.update_data(address=message.text)
    await finish_order(message, state)

async def finish_order(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_id = get_id(message.from_user.id)
    cart = get_cart(user_id)
    
    total = 0
    for item in cart:
        product_id = item[1]
        quantity = item[2]
        product = get_product(product_id)
        price = product[3]
        discount = product[5]
        
        final_price = int(price - (price * discount / 100))
        summa = final_price * quantity
        total = total + summa
        
    order_id = add_order(user_id, total, data['delivery_type'], data['address'])
    
    for item in cart:
        product_id = item[1]
        quantity = item[2]
        product = get_product(product_id)
        price = product[3]
        discount = product[5]
        
        final_price = int(price - (price * discount / 100))
        add_order_item(order_id, product_id, quantity, final_price)
        
    clear_cart(user_id)
    await state.clear()
    
    if message.from_user.id == ADMIN_ID:
        kb = admin_kb
    else:
        kb = user_kb
        
    await message.answer("Заказ успешно оформлен", reply_markup=kb)

@dp.message(F.text == '📦 Мои заказы')
async def my_orders(message: types.Message):
    user_id = get_id(message.from_user.id)
    orders = get_user_orders(user_id)
    
    if not orders:
        await message.answer("У вас нет заказов")
        return
        
    for order in orders:
        await message.answer(f"Заказ {order[0]}\nСумма: {order[1]}\nСтатус: {order[2]}\nДоставка: {order[3]}")

@dp.message(F.text == '📦 Заказы')
async def admin_orders(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    orders = get_orders()
    for order in orders:
        order_id = order[0]
        total = order[2]
        status = order[3]
        
        text = f"Заказ {order_id}\nСумма: {total}\nСтатус: {status}"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"status_confirmed_{order_id}")],
            [InlineKeyboardButton(text="🚚 В пути", callback_data=f"status_indelivery_{order_id}")],
            [InlineKeyboardButton(text="📦 Доставлено", callback_data=f"status_delivered_{order_id}")]
        ])
        await message.answer(text, reply_markup=kb)

@dp.callback_query(F.data.startswith('status_'))
async def change_status(callback: types.CallbackQuery):
    data = callback.data.split('_')
    status = data[1]
    order_id = int(data[2])
    
    update_order_status(order_id, status)
    await callback.message.edit_text(f"Статус заказа {order_id} изменен на {status}")

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())