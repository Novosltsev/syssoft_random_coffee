import logging
import random
from datetime import datetime
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext, filters
from aiogram.dispatcher.filters.state import State, StatesGroup
import sqlite3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import re
from config import *
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Установка уровня логирования
logging.basicConfig(filename='app.log', level=logging.INFO)

# Создание форматировщика для логов
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# Создание обработчика для вывода логов в файл
file_handler = logging.FileHandler('app.log')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)

# Создание обработчика для вывода логов на консоль
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)

# Получение корневого логгера
logger = logging.getLogger()

# Добавление обработчика вывода на консоль к корневому логгеру
logger.addHandler(console_handler)

# Добавление обработчика вывода в файл к корневому логгеру
logger.addHandler(file_handler)

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
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    email TEXT,
                    code TEXT,
                    status TEXT,
                    activity TEXT)''')
conn.commit()

cursor.execute('''CREATE TABLE IF NOT EXISTS pair_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user1_id INTEGER,
                    user2_id INTEGER,
                    date TEXT,
                    meeting_answer TEXT,
                    enjoyed_answer TEXT)''')
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

    # Проверяем, зарегистрирован ли пользователь
    cursor.execute('SELECT * FROM db_botuser WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()

    if user:
        await message.reply(dis_allow)
    else:
        # Отправляем приветственное сообщение
        await message.reply(f"{hi} {first_name}! {enter_address}")

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

    if not re.match(r"[^@]+@[^@]+\.[^@]+", message.text.lower()):
        await message.reply(bad_address)
    else:
        email = message.text.lower()

        # Проверяем, является ли домен почты разрешенным
        domain = email.split('@')[1]  # Получаем домен из адреса электронной почты

        if domain not in allowed_domains:
            await message.reply(no_address)
        else:
            # Проверяем, существует ли пользователь с такой почтой в базе данных
            cursor.execute('SELECT * FROM db_botuser WHERE email = ?', (email,))
            user = cursor.fetchone()

            if user:
                # Получаем информацию о пользователе
                user_id = message.from_user.id
                username = message.from_user.username
                first_name = message.from_user.first_name
                last_name = message.from_user.last_name
                # Обновляем данные пользователя в базе данных
                cursor.execute(
                    'UPDATE db_botuser SET user_id = ?, username = ?, first_name = ?, last_name = ?, activity = ? WHERE email = ?',
                    (user_id, username, first_name, last_name, 'pause', email))
                conn.commit()

                # Переходим в состояние ввода кода подтверждения
                await RegistrationState.code.set()

                # Отправляем код подтверждения на адрес электронной почты
                confirmation_code = str(random.randint(100000, 999999))
                confirmation_message = f"Код подтверждения: {confirmation_code}"
                send_email(email, "Код подтверждения", confirmation_message)
                # Сохранение кода в базе данных
                cursor.execute('UPDATE db_botuser SET code = ? WHERE user_id = ?', (confirmation_code, user_id))
                conn.commit()

                await message.reply(sent_email)
            else:
                # Обработка сообщения от пользователя, отсутствующего в базе данных
                await message.reply("Простите, вы не в команде syssoft.ru")
                photo_path = "./godfather.jpg"  # путь к файлу изображения

                # Отправка изображения из файла
                with open(photo_path, 'rb') as photo_file:
                    await bot.send_photo(chat_id=message.chat.id, photo=photo_file)


@dp.message_handler(filters.Regexp(r"^\d{6}$"), state=RegistrationState.code)
async def process_code(message: types.Message, state: FSMContext):
    # Получаем информацию о пользователе
    user_id = message.from_user.id

    # Проверяем, зарегистрирован ли пользователь
    cursor.execute('SELECT * FROM db_botuser WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    current_time = datetime.now()
    start_time = current_time

    print(f"База данных: {user[5]}, Введенный код: {message.text}")
    while True:
        if user[5] == message.text:
            # Код верен, проверяем время ввода
            current_time = datetime.now()
            time_difference = current_time - start_time
            if time_difference.total_seconds() <= 20 * 60:  # Проверяем, что прошло не более 20 минут
                # Код верен, выполняем необходимые действия
                # Например, можно установить статус "active" и активность "game"
                cursor.execute('UPDATE db_botuser SET status = ?, activity = ? WHERE user_id = ?',
                               ('active', 'game', user_id))
                conn.commit()

                await message.reply(great_register)
            else:
                await message.reply(time_gone)
            break
        else:
            await message.reply(incorrect)
            break

    # Завершаем состояние и очищаем контекст
    await state.finish()


async def send_game_question():
    # Получаем список пользователей со статусом "активный" и активностью "game"
    cursor.execute('SELECT * FROM db_botuser WHERE status = ? AND activity = ?', ('active', 'game'))
    users = cursor.fetchall()

    # Создаем клавиатуру с кнопками "Да" и "Нет" для каждого вопроса
    for user in users:
        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("Да", callback_data="yes"),
            InlineKeyboardButton("Нет", callback_data="no"),
        )
        # Отправляем сообщение текущему пользователю с индивидуальной клавиатурой
        await bot.send_message(chat_id=user[1], text=start_week,
                               reply_markup=keyboard)


@dp.callback_query_handler(lambda query: query.data == 'yes')
async def handle_yes_callback(query: types.CallbackQuery):
    # Получаем информацию о пользователе
    user_id = query.from_user.id

    # Обновляем активность пользователя на "game" в базе данных
    cursor.execute('UPDATE db_botuser SET activity = ? WHERE user_id = ?', ('game', user_id))
    conn.commit()

    await query.answer(text=button_yes, show_alert=True)


@dp.callback_query_handler(lambda query: query.data == 'no')
async def handle_no_callback(query: types.CallbackQuery):
    # Получаем информацию о пользователе
    user_id = query.from_user.id

    # Обновляем активность пользователя на "pause" в базе данных
    cursor.execute('UPDATE db_botuser SET activity = ? WHERE user_id = ?', ('pause', user_id))
    conn.commit()

    await query.answer(text=button_no, show_alert=True)


@dp.callback_query_handler(lambda query: query.data == 'meeting_yes')
async def handle_meeting_yes_callback(query: types.CallbackQuery):
    # Получаем информацию о пользователе
    user_id = query.from_user.id

    # Ищем запись в БД по user_id
    cursor.execute('SELECT id FROM db_botuser WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()

    if result:
        db_id = result[0]

        # Определяем, является ли пользователь user1 или user2
        cursor.execute('SELECT * FROM pair_history WHERE user1_id = ? OR user2_id = ?', (db_id, db_id))
        quest = cursor.fetchone()

        if quest:
            user1_id = quest[1]
            user2_id = quest[2]

            # Сохраняем ответ в соответствующей колонке
            if user1_id == db_id:
                cursor.execute('UPDATE pair_history SET meeting_answer_user1_id = ? WHERE user1_id = ?',
                               ('Да', user1_id))
            elif user2_id == db_id:
                cursor.execute('UPDATE pair_history SET meeting_answer_user2_id = ? WHERE user2_id = ?',
                               ('Да', user2_id))

            conn.commit()

            await bot.send_message(chat_id=user_id, text="Спасибо за ваш ответ!")
        else:
            await bot.send_message(chat_id=user_id, text="Вы не связаны с парой.")


@dp.callback_query_handler(lambda query: query.data == 'meeting_no')
async def handle_meeting_no_callback(query: types.CallbackQuery):
    # Получаем информацию о пользователе
    user_id = query.from_user.id

    # Ищем запись в БД по user_id
    cursor.execute('SELECT id FROM db_botuser WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()

    if result:
        db_id = result[0]

        # Определяем, является ли пользователь user1 или user2
        cursor.execute('SELECT * FROM pair_history WHERE user1_id = ? OR user2_id = ?', (db_id, db_id))
        quest = cursor.fetchone()

        if quest:
            user1_id = quest[1]
            user2_id = quest[2]

            # Сохраняем ответ в соответствующей колонке
            if user1_id == db_id:
                cursor.execute('UPDATE pair_history SET meeting_answer_user1_id = ? WHERE user1_id = ?',
                               ('Нет', user1_id))
            elif user2_id == db_id:
                cursor.execute('UPDATE pair_history SET meeting_answer_user2_id = ? WHERE user2_id = ?',
                               ('Нет', user2_id))

            conn.commit()

            await bot.send_message(chat_id=user_id, text="Спасибо за ваш ответ!")
        else:
            await bot.send_message(chat_id=user_id, text="Вы не связаны с парой.")


@dp.callback_query_handler(lambda query: query.data == 'enjoyed_yes')
async def handle_enjoyed_yes_callback(query: types.CallbackQuery):
    # Получаем информацию о пользователе
    user_id = query.from_user.id

    # Ищем запись в БД по user_id
    cursor.execute('SELECT id FROM db_botuser WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()

    if result:
        db_id = result[0]

        # Определяем, является ли пользователь user1 или user2
        cursor.execute('SELECT * FROM pair_history WHERE user1_id = ? OR user2_id = ?', (db_id, db_id))
        quest = cursor.fetchone()

        if quest:
            user1_id = quest[1]
            user2_id = quest[2]

            # Сохраняем ответ в соответствующей колонке
            if user1_id == db_id:
                cursor.execute('UPDATE pair_history SET enjoyed_answer_user1_id = ? WHERE user1_id = ?',
                               ('Понравилось', user1_id))
            elif user2_id == db_id:
                cursor.execute('UPDATE pair_history SET enjoyed_answer_user2_id = ? WHERE user2_id = ?',
                               ('Понравилось', user2_id))

            conn.commit()

            await bot.send_message(chat_id=user_id, text="Спасибо за ваш ответ!")
        else:
            await bot.send_message(chat_id=user_id, text="Вы не связаны с парой.")


@dp.callback_query_handler(lambda query: query.data == 'enjoyed_no')
async def handle_enjoyed_no_callback(query: types.CallbackQuery):
    # Получаем информацию о пользователе
    user_id = query.from_user.id

    # Ищем запись в БД по user_id
    cursor.execute('SELECT id FROM db_botuser WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()

    if result:
        db_id = result[0]

        # Определяем, является ли пользователь user1 или user2
        cursor.execute('SELECT * FROM pair_history WHERE user1_id = ? OR user2_id = ?', (db_id, db_id))
        quest = cursor.fetchone()

        if quest:
            user1_id = quest[1]
            user2_id = quest[2]

            # Сохраняем ответ в соответствующей колонке
            if user1_id == db_id:
                cursor.execute('UPDATE pair_history SET enjoyed_answer_user1_id = ? WHERE user1_id = ?',
                               ('Не очень', user1_id))
            elif user2_id == db_id:
                cursor.execute('UPDATE pair_history SET enjoyed_answer_user2_id = ? WHERE user2_id = ?',
                               ('Не очень', user2_id))

            conn.commit()

            await bot.send_message(chat_id=user_id, text="Спасибо за ваш ответ!")
        else:
            await bot.send_message(chat_id=user_id, text="Вы не связаны с парой.")


async def save_pair_history(user1_id, user2_id):
    date = datetime.now().strftime('%d.%m.%Y')
    cursor.execute('INSERT INTO pair_history (user1_id, user2_id, date) VALUES (?, ?, ?)', (user1_id, user2_id, date))
    conn.commit()


async def show_pair_history(user_id):
    cursor.execute('SELECT id FROM db_botuser WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()

    if result:
        user_db_id = result[0]

        cursor.execute('SELECT * FROM pair_history WHERE user1_id = ? OR user2_id = ?', (user_db_id, user_db_id))
        history = cursor.fetchall()

        if history:
            for row in history:
                user1_id = row[1]
                user2_id = row[2]
                date = row[3]
                meeting_answer_user1_id = row[4]
                enjoyed_answer_user1_id = row[5]
                meeting_answer_user2_id = row[6]
                enjoyed_answer_user2_id = row[7]

                if user1_id == user_db_id:
                    user2 = cursor.execute('SELECT * FROM db_botuser WHERE id = ?', (user2_id,)).fetchone()
                    if user2:
                        message = f"Вы были в паре с пользователем:\n" \
                                  f"{user2[3]} {user2[4]}\n" \
                                  f"Почта - ({user2[8]})\n" \
                                  f"Дата - {date}\n" \
                                  f"Состоялась встреча? - {meeting_answer_user1_id}\n" \
                                  f"Понравилось общение? - {enjoyed_answer_user1_id}"
                        await bot.send_message(chat_id=user_id, text=message)
                elif user2_id == user_db_id:
                    user1 = cursor.execute('SELECT * FROM db_botuser WHERE id = ?', (user1_id,)).fetchone()
                    if user1:
                        message = f"Вы были в паре с пользователем:\n" \
                                  f"{user1[3]} {user1[4]}\n" \
                                  f"Почта - ({user1[8]})\n" \
                                  f"Дата - {date}\n" \
                                  f"Состоялась встреча? - {meeting_answer_user2_id}\n" \
                                  f"Понравилось общение? - {enjoyed_answer_user2_id}\n"
                        await bot.send_message(chat_id=user_id, text=message)
        else:
            message = f"У вас отсутствует история"
            await bot.send_message(chat_id=user_id, text=message)
    else:
        message = f"Мы не нашли вас в базе данных"
        await bot.send_message(chat_id=user_id, text=message)


async def send_coffee_pairs():
    # Получаем список пользователей со статусом "active" и активностью "game"
    cursor.execute('SELECT * FROM db_botuser WHERE status = ? AND activity = ?', ('active', 'game'))
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
                await bot.send_message(chat_id=user1[1],
                                       text=f"Привет, {user1[3]}! 👋\n"
                                            f"Твоя пара на эту неделю:\n"
                                            f"{user2[3] or 'имя отсутствует'} {user2[4] or 'фамилия отсутствует'}\n"
                                            f"\n"
                                            f"Напиши собеседнику на почту – {user2[8] or 'почта отсутствует'}\n"
                                            f"Или в Telegram – @{user2[2] or 'ник отсутствует'}\n"
                                            f"Не откладывай, договорись о встрече сразу 🙂")
                await save_pair_history(user1[0], user2[0])
                await bot.send_message(chat_id=user2[1],
                                       text=f"Привет, {user2[3]}! 👋\n"
                                            f"Твоя пара на эту неделю:\n"
                                            f"{user1[3] or 'имя отсутствует'} {user1[4] or 'фамилия отсутствует'}\n"
                                            f"\n"
                                            f"Напиши собеседнику на почту – {user1[8] or 'почта отсутствует'}\n"
                                            f"Или в Telegram – @{user1[2] or 'ник отсутствует'}\n"
                                            f"Не откладывай, договорись о встрече сразу 🙂")
            else:
                await bot.send_message(chat_id=user1[1], text="Вы не получили пару.")
                # Назначаем администратора системы в пару для пользователя без пары
                if not admin:
                    admin = cursor.execute('SELECT * FROM db_botuser WHERE status = ? AND activity = ? AND id != ?',
                                           ('активный', 'в игре', user1[0])).fetchone()

                    if admin:
                        await bot.send_message(chat_id=user1[1], text=f"{admin[2]} ({admin[3]})")
                        await save_pair_history(user1[0], admin[0])  # Сохраняем историю пары


@dp.message_handler(commands=['history'])
async def cmd_history(message: types.Message):
    # Получаем информацию о пользователе
    user_id = message.from_user.id
    await show_pair_history(user_id)


async def send_survey():
    # Получаем список пользователей со статусом "active" и активностью "game"
    cursor.execute('SELECT * FROM db_botuser WHERE status = ? AND activity = ?', ('active', 'game'))
    users = cursor.fetchall()

    for user in users:
        keyboard1 = InlineKeyboardMarkup(row_width=2)
        keyboard1.add(
            InlineKeyboardButton("Состоялась", callback_data="meeting_yes"),
            InlineKeyboardButton("Не состоялась", callback_data="meeting_no"),
        )
        # Отправляем первый опрос текущему пользователю с индивидуальной клавиатурой
        await bot.send_message(chat_id=user[1], text=friday_question_1,
                               reply_markup=keyboard1)

        keyboard2 = InlineKeyboardMarkup(row_width=2)
        keyboard2.add(
            InlineKeyboardButton("Понравилось 😊", callback_data="enjoyed_yes"),
            InlineKeyboardButton("Не очень ☹", callback_data="enjoyed_no"),
        )
        # Отправляем второй опрос текущему пользователю с индивидуальной клавиатурой
        await bot.send_message(chat_id=user[1], text=friday_question_2,
                               reply_markup=keyboard2)

        keyboard = InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("Да", callback_data="yes"),
            InlineKeyboardButton("Нет", callback_data="no"),
        )
        # Отправляем сообщение текущему пользователю с индивидуальной клавиатурой
        await bot.send_message(chat_id=user[1], text=friday_question_3,
                               reply_markup=keyboard)


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
    # Запускаем функцию send_coffee_pairs() при запуске бота
    scheduler = AsyncIOScheduler(event_loop=bot.loop)
    scheduler.add_job(send_game_question, 'cron', day_of_week='mon', hour=9, minute=0)
    scheduler.add_job(send_coffee_pairs, 'cron', day_of_week='mon', hour=9, minute=15)
    scheduler.add_job(send_survey, 'cron', day_of_week='fri', hour=17, minute=0)
    scheduler.start()

    # Запускаем бота
    executor.start_polling(dp, skip_updates=True)
