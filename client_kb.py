from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove


button1 = KeyboardButton('/Добавить_URL')
button2 = KeyboardButton('/Показать_все_мои_URL')
button3 = KeyboardButton('/Удалить_все_мои_URL')
button4 = KeyboardButton('/Удалить_определенные_URL')
button5 = KeyboardButton('/Админка')
button6 = KeyboardButton('/Сообщение')
buttons = ReplyKeyboardMarkup(resize_keyboard=True)
buttonsadmin = ReplyKeyboardMarkup(resize_keyboard=True)
buttons.add(button1).add(button2).add(button3).add(button4)
buttonsadmin.add(button1).add(button2).add(button3).add(button4).add(button5).add(button6)