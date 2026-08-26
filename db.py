import psycopg

connection = psycopg.connect(
    host="localhost",
    dbname="shopdb",
    user="postgres",
    password="501272687firuzjon",
    port=5432
)

cursor = connection.cursor()

def create_tables():
    cursor.execute("""
    create table if not exists Users(
        id serial primary key,
        tg_id varchar(20) unique,
        name varchar(50)
    );
    
    create table if not exists Products(
        id serial primary key,
        name varchar(100),
        description text,
        price int,
        code varchar(20) unique,
        discount int default 0
    );

    create table if not exists Cart(
        id serial primary key,
        user_id int references Users(id),
        product_id int references Products(id),
        quantity int
    );

    create table if not exists Orders(
        id serial primary key,
        user_id int references Users(id),
        total int,
        status varchar(20),
        delivery_type varchar(20),
        address text
    );

    create table if not exists OrderItems(
        id serial primary key,
        order_id int references Orders(id),
        product_id int references Products(id),
        quantity int,
        price int
    );
    """)
    connection.commit()

def add_user(tg_id, name):
    cursor.execute('select id from Users where tg_id = %s', (str(tg_id),))
    user = cursor.fetchone()
    if not user:
        cursor.execute('insert into Users(tg_id, name) values(%s, %s)', (str(tg_id), name))
        connection.commit()

def get_id(tg_id):
    cursor.execute('select id from Users where tg_id = %s', (str(tg_id),))
    user = cursor.fetchone()
    return user[0]

def add_product(name, description, price, code, discount):
    cursor.execute('insert into Products(name, description, price, code, discount) values(%s, %s, %s, %s, %s)', 
                   (name, description, price, code, discount))
    connection.commit()

def get_products(offset):
    cursor.execute('select id, name, description, price, code, discount from Products limit 5 offset %s', (offset,))
    return cursor.fetchall()

def delete_product(product_id):
    cursor.execute('delete from Cart where product_id = %s', (product_id,))
    cursor.execute('delete from Products where id = %s', (product_id,))
    connection.commit()

def get_product_by_code(code):
    cursor.execute('select id, name, description, price, code, discount from Products where code = %s', (code,))
    return cursor.fetchone()

def get_product(product_id):
    cursor.execute('select id, name, description, price, code, discount from Products where id = %s', (product_id,))
    return cursor.fetchone()

def get_users():
    cursor.execute('select id, tg_id, name from Users')
    return cursor.fetchall()

def add_to_cart(user_id, product_id):
    cursor.execute('select id, quantity from Cart where user_id = %s and product_id = %s', (user_id, product_id))
    item = cursor.fetchone()
    if item:
        cursor.execute('update Cart set quantity = quantity + 1 where id = %s', (item[0],))
    else:
        cursor.execute('insert into Cart(user_id, product_id, quantity) values(%s, %s, 1)', (user_id, product_id))
    connection.commit()

def get_cart(user_id):
    cursor.execute('select id, product_id, quantity from Cart where user_id = %s', (user_id,))
    return cursor.fetchall()

def clear_cart(user_id):
    cursor.execute('delete from Cart where user_id = %s', (user_id,))
    connection.commit()

def remove_from_cart(cart_id):
    cursor.execute('delete from Cart where id = %s', (cart_id,))
    connection.commit()

def add_order(user_id, total, delivery_type, address):
    cursor.execute('insert into Orders(user_id, total, status, delivery_type, address) values(%s, %s, %s, %s, %s) returning id',
                   (user_id, total, 'new', delivery_type, address))
    order_id = cursor.fetchone()[0]
    connection.commit()
    return order_id

def add_order_item(order_id, product_id, quantity, price):
    cursor.execute('insert into OrderItems(order_id, product_id, quantity, price) values(%s, %s, %s, %s)',
                   (order_id, product_id, quantity, price))
    connection.commit()

def get_orders():
    cursor.execute('select id, user_id, total, status, delivery_type, address from Orders order by id desc')
    return cursor.fetchall()

def get_user_orders(user_id):
    cursor.execute('select id, total, status, delivery_type from Orders where user_id = %s order by id desc', (user_id,))
    return cursor.fetchall()

def update_order_status(order_id, status):
    cursor.execute('update Orders set status = %s where id = %s', (status, order_id))
    connection.commit()