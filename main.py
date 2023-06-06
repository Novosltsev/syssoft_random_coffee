import logging
import random
import asyncio
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext, filters
from aiogram.dispatcher.filters.state import State, StatesGroup
import sqlite3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import re
from config import *
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

# Установка уровня логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

conn = sqlite3.connect('./admin/main.db')
cursor = conn.cursor()

# Создание таблицы пользователей, если она не существует
cursor.execute('''CREATE TABLE IF NOT EXISTS db_botuser
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    first_name TEXT,
                    last_name TEXT,
                    email TEXT,
                    code TEXT,
                    status TEXT,
                    activity TEXT)''')
conn.commit()


class RegistrationState(StatesGroup):
    email = State()
    code = State()


class HistoryState(StatesGroup):
    history = State()


@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message, state: FSMContext):
    # Получаем информацию о пользователе
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name

    # Проверяем, зарегистрирован ли пользователь
    cursor.execute('SELECT * FROM db_botuser WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()

    if user:
        await message.reply(dis_allow)
    else:
        # Отправляем приветственное сообщение
        await message.reply(f"{hi} {first_name}! {enter_address}")

        # Добавляем пользователя в базу данных со статусом "регистрация"
        cursor.execute('INSERT INTO db_botuser (user_id, first_name, last_name, status) VALUES (?, ?, ?, ?)',
                       (user_id, first_name, last_name, 'регистрация'))
        conn.commit()

        # Переходим в состояние ввода адреса электронной почты
        await RegistrationState.email.set()


@dp.message_handler(state=RegistrationState.email)
async def process_email(message: types.Message, state: FSMContext):
    # Получаем информацию о пользователе
    user_id = message.from_user.id

    allowed_domains = DOMAINS

    # Проверяем, зарегистрирован ли пользователь
    cursor.execute('SELECT * FROM db_botuser WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()

    if not re.match(r"[^@]+@[^@]+\.[^@]+", message.text):
        await message.reply(bad_address)
    else:
        email = message.text

        domain = email.split('@')[1]  # Получаем домен из адреса электронной почты

        if domain not in allowed_domains:
            await message.reply(no_address)
        else:
            # Генерируем и сохраняем код подтверждения
            confirmation_code = str(random.randint(100000, 999999))
            print(confirmation_code)
            cursor.execute('UPDATE db_botuser SET email = ?, code = ? WHERE user_id = ?',
                           (email, confirmation_code, user_id))
            conn.commit()

            confirmation_message = f"Код подтверждения: {confirmation_code}"
            send_email(email, "Код подтверждения", confirmation_message)

            # Переходим в состояние ввода кода подтверждения
            await RegistrationState.code.set()

            # Отправляем код подтверждения на адрес электронной почты
            await message.reply(sent_email)


@dp.message_handler(filters.Regexp(r"^\d{6}$"), state=RegistrationState.code)
async def process_code(message: types.Message, state: FSMContext):
    # Получаем информацию о пользователе
    user_id = message.from_user.id

    # Проверяем, зарегистрирован ли пользователь
    cursor.execute('SELECT * FROM db_botuser WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()

    print(f"База данных: {user[5]}, Введенный код: {message.text}")
    if user[4] == message.text:
        # Код верен, выполняем необходимые действия
        # Например, можно установить статус "зарегистрирован" и активность "в игре"
        cursor.execute('UPDATE db_botuser SET status = ?, activity = ? WHERE user_id = ?',
                       ('зарегистрирован', 'в игре', user_id))
        conn.commit()

        # Сохраняем информацию о собеседнике в историю
        history_user_id = user[0]
        history_first_name = user[2]
        history_last_name = user[3]
        cursor.execute('INSERT INTO db_botuser (user_id, first_name, last_name, activity) VALUES (?, ?, ?, ?)',
                       (history_user_id, history_first_name, history_last_name, 'в игре'))
        conn.commit()

        await message.reply(great_register)
    else:
        await message.reply(incorrect)

    # Завершаем состояние и очищаем контекст
    await state.finish()


@dp.message_handler(commands=['history'])
async def cmd_history(message: types.Message):
    # Получаем информацию о пользователе
    user_id = message.from_user.id

    # Проверяем, зарегистрирован ли пользователь
    cursor.execute('SELECT * FROM db_botuser WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()

    if user:
        # Получаем историю взаимодействий для данного пользователя
        cursor.execute('SELECT * FROM db_botuser WHERE activity = ? AND id != ?', ('в игре', user[0]))
        interactions = cursor.fetchall()

        if len(interactions) > 0:
            history_text = "История взаимодействий:\n"
            for interaction in interactions:
                history_text += f"- {interaction[2]} {interaction[3]}\n"

            await message.reply(history_text)
        else:
            await message.reply("История взаимодействий пуста.")
    else:
        await message.reply("Вы не зарегистрированы.")


async def send_coffee_pairs():
    # Получаем текущий день недели и время
    current_day = datetime.now().strftime('%A')
    current_time = datetime.now().strftime('%H:%M')

    if current_day == 'Monday' and current_time == '09:00':
        # Получаем список пользователей со статусом "активный" и активностью "в игре"
        cursor.execute('SELECT * FROM db_botuser WHERE status = ? AND activity = ?', ('активный', 'в игре'))
        users = cursor.fetchall()

        if len(users) >= 2:
            # Формируем пары случайным образом
            random.shuffle(users)

            if len(users) % 2 == 0:
                pairs = [(users[i], users[i + 1]) for i in range(0, len(users), 2)]
            else:
                pairs = [(users[i], users[i + 1]) for i in range(0, len(users) - 1, 2)]
                pairs.append((users[-1], None))

            admin = None  # Переменная для хранения администратора системы

            for pair in pairs:
                user1 = pair[0]
                user2 = pair[1]

                # Отправляем сообщение каждому пользователю с его парой
                if user2:
                    await bot.send_message(chat_id=user1[1], text=f"{pairs} {user2[2]} ({user2[3]})")
                    await bot.send_message(chat_id=user2[1], text=f"{pairs} {user1[2]} ({user1[3]})")
                else:
                    await bot.send_message(chat_id=user1[1], text=no_pairs)
                    # Назначаем администратора системы в пару для пользователя без пары
                    if not admin:
                        admin = cursor.execute('SELECT * FROM db_botuser WHERE status = ? AND activity = ? AND id != ?',
                                               ('активный', 'в игре', user1[0])).fetchone()

                        if admin:
                            await bot.send_message(chat_id=user1[1], text=f"{pairs} {admin[2]} ({admin[3]})")

    elif current_day == 'Monday' and current_time == '09:15':
        # Получаем список пользователей со статусом "активный" и активностью "в игре"
        cursor.execute('SELECT * FROM db_botuser WHERE status = ? AND activity = ?', ('активный', 'в игре'))
        users = cursor.fetchall()

        for user in users:
            await bot.send_message(chat_id=user[1], text=f"{pairs} {user[2]} ({user[3]}). {contact}")

    elif current_day == 'Friday' and current_time == '17:00':
        # Получаем список пользователей со статусом "активный" и активностью "в игре"
        cursor.execute('SELECT * FROM db_botuser WHERE status = ? AND activity = ?', ('активный', 'в игре'))
        users = cursor.fetchall()

        for user in users:
            await bot.send_message(chat_id=user[1], text=check)
            await bot.send_message(chat_id=user[1], text=one_q)
            await bot.send_message(chat_id=user[1], text=two_q)
            await bot.send_message(chat_id=user[1], text=three_q)

    # Задержка в 15 минут перед повторной отправкой пар
    await asyncio.sleep(900)
    await send_coffee_pairs()


def send_email(to_email, subject, message):
    # Настройки SMTP-сервера
    smtp_host = smtp_host_co
    smtp_port = smtp_port_co
    smtp_username = smtp_username_co
    smtp_password = smtp_password_co

    # Создаем сообщение электронной почты
    msg = MIMEMultipart()
    msg["From"] = smtp_username
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(message, "plain"))

    try:
        # Создаем соединение с SMTP-сервером
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)

        # Отправляем сообщение
        server.send_message(msg)

        # Закрываем соединение
        server.quit()
        print("Email sent successfully")
    except Exception as e:
        print("Error sending email:", str(e))


if __name__ == '__main__':
    # Run the on_startup function when the bot starts
    executor.start_polling(dp, skip_updates=True)
