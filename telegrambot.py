import sys
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils.markdown import hlink
import botsettings
import sqlite3
import time
from urllib.parse import urlparse
from wildbozon import get_content
import logging
import client_kb
from aiogram.utils.executor import start_webhook
import asyncio


logging.basicConfig(format='Date-Time : %(asctime)s : Line No. : %(lineno)d - %(message)s', level = logging.INFO, filename = botsettings.logs, filemode = 'a')

class Geturl(StatesGroup):
    url = State()
    urltodelete = State()
    messagesend = State()

bot = Bot(token = botsettings.token)
dp = Dispatcher(bot, storage=MemoryStorage())

# This options needed if you use self-signed SSL certificate
# Instructions: https://core.telegram.org/bots/self-signed
WEBHOOK_SSL_CERT = './certbot/conf/live/bugatti282telegrambot.cf/cert.pem'  # Path to the ssl certificate
WEBHOOK_SSL_PRIV = './certbot/conf/live/bugatti282telegrambot.cf/privkey.pem'  # Path to the ssl private key

WEBHOOK_HOST = 'https://bugatti282telegrambot.cf'
WEBHOOK_PATH = '/' + botsettings.token
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

# # webserver settings
WEBAPP_HOST = '0.0.0.0'  # or ip
WEBAPP_PORT = 7771


async def on_startup(_):
    await bot.set_webhook(WEBHOOK_URL)
    logging.info(f'Бот запущен')
    connect = sqlite3.connect(botsettings.db)
    cursor = connect.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY,
        datetime_register TEXT
        )""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS urls(
        id INTEGER,
        link_id INTEGER,
        url TEXT,
        price,
        title,
        lastprice,
        FOREIGN KEY(link_id) REFERENCES users(id)
        )""")
    connect.commit()
    logging.info(f'База создана или существует')
    asyncio.create_task(check_price())
    
async def on_shutdown(_):
    logging.info(f'Бот завершил работу')
    await bot.delete_webhook()


@dp.message_handler(commands='start')
async def registering(message: types.Message):
    connect = sqlite3.connect(botsettings.db)
    cursor = connect.cursor()
    people = message.from_user.id
    cursor.execute(f"SELECT id FROM users WHERE id = {people}")
    data = cursor.fetchone()
    if data is None:
        dt = time.strftime('%Y/%m/%d %H:%M:%S')
        user_id = message.from_user.id
        cursor.execute("INSERT INTO 'users' ('id', 'datetime_register') VALUES(?,?)",(user_id,dt))
        connect.commit()
        connect.close()
        logging.info(f'Пользователи с id = {message.from_user.id} зарегистрировался')
        await bot.send_message(687724238,f'Пользователь {message.from_user.id} зарегистрировался')
        await bot.send_message(message.from_user.id,'Привет, вы зарегистрированы',reply_markup=client_kb.buttons)
    else:
        if message.from_user.id in botsettings.admins:
            await bot.send_message(message.from_user.id, 'Здарова Админушка',reply_markup=client_kb.buttonsadmin)
        else:
            await bot.send_message(message.from_user.id, 'Вы уже зарегистрированы',reply_markup=client_kb.buttons)


@dp.message_handler(commands='Админка')
async def getusers(message: types.Message):
    connect = sqlite3.connect(botsettings.db)
    cursor = connect.cursor()
    cursor.execute(f"SELECT id FROM users")
    users = cursor.fetchall()
    errors = []
    for user in users:
        if message.from_user.id in botsettings.admins:
            await asyncio.sleep(1 / 2)
            await bot.send_message(message.from_user.id, f'Пользователь с id = {user}\n')
        else:
            await bot.send_message(message.from_user.id, f'Вы не администратор')
            break
    connect.close()
    connect = sqlite3.connect(botsettings.db)
    cursor = connect.cursor()
    cursor.execute(f"SELECT url, price FROM urls")
    urls = cursor.fetchall()
    for i in urls:
        errors.append(int(i[1]))
    if message.from_user.id in botsettings.admins:
        if 99999999 not in errors:
            await bot.send_message(message.from_user.id, f'Проблем парсинга не обнаружено, всего ссылок {len(errors)}')
        else:
            await bot.send_message(message.from_user.id, f'Проблема парсинга в {errors.count(99999999)}/{len(errors)} ссылках') 
    else:
        await bot.send_message(message.from_user.id, f'Вы не администратор')


@dp.message_handler(commands='Сообщение', state=None)
async def privateget(message: types.Message):
    await Geturl.messagesend.set()
    await bot.send_message(message.from_user.id, 'Введите сообщение')

@dp.message_handler(state=Geturl.messagesend)
async def privatesend(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['messagesend'] = message.text
    await bot.send_message('1486204773', message.text)
    await state.finish()


@dp.message_handler(commands='Добавить_URL', state=None)
async def set_url(message: types.Message):
    await Geturl.url.set()
    await bot.send_message(message.from_user.id, 'Введите url')
    

@dp.message_handler(state=Geturl.url)
async def save_url(message: types.Message, state: FSMContext, title = None, price = None):
    async with state.proxy() as data:
        data['url'] = message.text
    id = 1
    all = []
    user_id = message.from_user.id
    connect = sqlite3.connect(botsettings.db)
    cursor = connect.cursor()
    cursor.execute(f'SELECT id from urls WHERE link_id = {user_id}')
    count = cursor.fetchall()
    for i in count:
        all.append(i[0])
    while True:
        if id in all:
            id += 1
        else:
            break
    if urlparse(message.text).netloc not in botsettings.sites:
        await bot.send_message(message.from_user.id, 'Это ссылка не OZON или Wildberries')
    else:
        title, price = get_content(message.text)
        cursor.execute("INSERT INTO 'urls' (id,'link_id','url',title,price,lastprice) VALUES(?,?,?,?,?,?)",(id,user_id,message.text,title,price,price))
        connect.commit()
        connect.close()
        await bot.send_message(message.from_user.id, 'Ссылка успешно сохранена')
    logging.info(f'Пользователи с id = {message.from_user.id} добавил URL = {message.text}')
    await state.finish()


@dp.message_handler(commands='Показать_все_мои_URL')
async def get_all_my_url(message: types.Message):
    user_id = message.from_user.id 
    connect = sqlite3.connect(botsettings.db)
    cursor = connect.cursor()
    cursor.execute(f"SELECT url, id, price, title, lastprice FROM urls WHERE link_id = {user_id} ORDER BY id")
    data = cursor.fetchall()
    if len(data) == 0:
        await bot.send_message(message.from_user.id, 'У вас нету сохраненных ссылок')
    else:
        for i in data:
            priceact = i[4]
            if int(i[4]) == 99999999:
                priceact = 'NoData'
            elif int(i[4]) == 999999998:
                priceact = 'Нет в наличии'
            price = i[2]
            if int(i[2]) == 99999999:
                price = 'NoData'
            elif int(i[2]) == 999999998:
                price = 'Нет в наличии'
            url = hlink(f'{str(i[3][:20])}...', f'{str(i[0])}')
            await bot.send_message(message.from_user.id,f'{url}\nНомер ссылки = {i[1]}\nЦена(самая низкая из наблюдаемых) = {price}\nЦена(на данный момент) = {priceact}',parse_mode='HTML',disable_web_page_preview=True)
            await asyncio.sleep(1)
    logging.info(f'Пользователь {message.from_user.id} запрос всех ссылок')

@dp.message_handler(commands='Удалить_определенные_URL', state=None)
async def del_url(message: types.Message):
    await Geturl.urltodelete.set()
    await bot.send_message(message.from_user.id, 'Введите номер удаляемых url через пробел')
    
@dp.message_handler(state=Geturl.urltodelete)
async def delete_url(message: types.Message, state: FSMContext):
    success = False
    async with state.proxy() as data:
        data['urltodelete'] = message.text
    numbers = message.text.split()
    user_id = message.from_user.id 
    connect = sqlite3.connect(botsettings.db)
    cursor = connect.cursor()
    for i in numbers:
        try:
            i = int(i)
            cursor.execute(f"DELETE FROM urls WHERE id = {i}")
            logging.info(f'Пользователь {message.from_user.id} удалил ссылку под номером {i}')
            success = True
        except:
            await bot.send_message(message.from_user.id, 'Вы что-то ввели не так, попробуйте еще раз')
            await state.finish()
            break
    if success:
        connect.commit()
        connect.close()
        await bot.send_message(message.from_user.id, 'Ссылки успешно удалены')
        await state.finish()
    
@dp.message_handler(commands='Удалить_все_мои_URL')
async def delete_all_url(message):
    user_id = message.from_user.id 
    connect = sqlite3.connect(botsettings.db)
    cursor = connect.cursor()
    cursor.execute(f"DELETE FROM urls WHERE link_id = {user_id}")
    connect.commit()
    connect.close()
    logging.info(f'Пользователь {message.from_user.id} удалил все ссылки')
    await bot.send_message(message.from_user.id, 'Все ссылки удалены')

async def check_price():
    logging.info(f'Запуск парсера')
    while True:
        connect = sqlite3.connect(botsettings.db)
        cursor = connect.cursor()
        cursor.execute("SELECT link_id,url,price,id,lastprice FROM urls")
        data = cursor.fetchall()
        for i in data:
            try:
                await asyncio.sleep(5)
                try:
                    title, price = get_content(i[1])
                except:
                    logging.info(f'Не удалось получить данные парсера')
                if int(price) < int(i[2]) and i[2] == 999999998 or int(price) < int(i[2]) and i[2] == 99999999: # проверка на наличие если товар был добавлен когда его не было
                    try:
                        await bot.send_message(i[0],f'{i[1]}\n{"~" * 20}\n Товар снова в наличии по цене в {price} руб.')
                        logging.info(f'Сообщение о наличии пользователю {i[0]} успешно отправлено')
                        cursor.execute(f"UPDATE urls SET price = (?) WHERE link_id = {i[0]} AND id = {i[3]} ",(price,))
                        connect.commit()
                    except:
                        cursor.execute(f"UPDATE urls SET price = (?) WHERE link_id = {i[0]} AND id = {i[3]} ",(999999998,))
                        connect.commit()
                elif int(price) < int(i[4]) and int(i[4]) == 999999998 and int(price) != 99999999: # проверка на наличие если товар исчезал
                    logging.info(f'Товар {i[1]} снова в наличии')
                    cursor.execute(f"UPDATE urls SET price = (?) WHERE link_id = {i[0]} AND id = {i[3]} ",(price,))
                    connect.commit()
                    try:
                        await bot.send_message(i[0],f'{i[1]}\n{"~" * 20}\n Товар снова в наличии по цене в {price} руб.')
                        logging.info(f'Сообщение о наличии пользователю {i[0]} успешно отправлено')
                    except:
                        cursor.execute(f"UPDATE urls SET price = (?) WHERE link_id = {i[0]} AND id = {i[3]} ",(999999998,))
                        connect.commit()
                elif int(price) < int(i[2]) and i[2] != 999999998 and i[2] != 99999999: # если товар подешевел
                    try:
                        await bot.send_message(i[0],f'{i[1]}\n{"~"*20}\nТовар подешевел на {int(i[2]) - int(price)}')
                        logging.info(f'Сообщение успешно отправлено Пользователи с id = {i[0]} | Цена на товар {title} уменьшилась')
                        cursor.execute(f"UPDATE urls SET price = (?) WHERE link_id = {i[0]} AND id = {i[3]} ",(price,))
                        connect.commit()
                    except:
                        logging.info(f'Сообщение о уменьшении цены не отправлено Пользователю с id = {i[0]}, попробует в следующий раз')
                elif int(price) == 99999999:
                        await bot.send_message(687724238,f'Парсинг {i[1]} поломался')  
                        logging.info(f'Парсинг {i[1]} поломался (elif)')
                cursor.execute(f"UPDATE urls SET lastprice = (?) WHERE link_id = {i[0]} AND id = {i[3]} ",(price,))
                connect.commit()
                logging.info(f'{title}, {price} прошлись по ценам')
            except:
                await bot.send_message(687724238,f'Парсинг {i[1]} поломался (except)')
                continue
        connect.close()
        await asyncio.sleep(1800)
        


if __name__ == '__main__':
    start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True,
        host=WEBAPP_HOST,
        port=WEBAPP_PORT,
    )
