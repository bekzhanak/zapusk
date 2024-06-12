import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.filters import CommandStart, Command
import asyncio
from utils import *
import csv
import random

API_TOKEN = "7377189411:AAE0QptG4Ng9sttPw6RsSxtXwPeVbcucWfw"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

paychecks = load_json("paychecks.json")
payments = load_json("payments.json")


# Define states
class Form(StatesGroup):
    name = State()
    phone = State()
    kaspi = State()
    prodamus = State()
    wheel_available = State()


def load_prizes_from_csv(file_path):
    prizes = []
    try:
        with open(file_path, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                row['chance'] = int(row['chance'])
                row['count'] = float('inf') if row['count'] == 'inf' else int(row['count'])
                row['winners'] = row['winners'].split(';') if row['winners'] else []
                prizes.append(row)
    except FileNotFoundError:
        logging.error("Prizes CSV file not found.")
    return prizes


# Save prizes to CSV
def save_prizes_to_csv(file_path, prizes):
    with open(file_path, 'w', newline='') as csvfile:
        fieldnames = ['name', 'chance', 'count', 'photo_id', 'video_id', 'winners']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for prize in prizes:
            prize['winners'] = ';'.join(prize['winners'])
            writer.writerow(prize)


prizes_file = 'prizes.csv'
prizes = load_prizes_from_csv(prizes_file)


def play_game(prizes, user_id):
    prize_list = []
    for prize in prizes:
        prize_list.extend([prize] * prize['chance'])

    while True:
        selected_prize = random.choice(prize_list)
        if selected_prize['count'] > 0 or selected_prize['count'] == float('inf'):
            if selected_prize['count'] != float('inf'):
                selected_prize['count'] -= 1
                selected_prize['winners'].append(str(user_id))
                save_prizes_to_csv(prizes_file, prizes)
            return selected_prize['name']
        else:
            prize_list = [p for p in prize_list if p['name'] != selected_prize['name']]


# Start command handler
@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    current_time = int(time.time())

    telegram_id = message.from_user.id
    user_data = {
        "start_time": current_time,
        "telegram_id": str(telegram_id),
        "name": "",
        "phone": "",
        "crm_id": "",
        "payment_time": 0  # Initialize crm_id with a default value
    }

    # Load existing users
    existing_users = {}
    try:
        with open('user_data.csv', 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                existing_users[row['telegram_id']] = row
    except FileNotFoundError:
        pass

    if str(telegram_id) in existing_users:
        user_data = existing_users[str(telegram_id)]

    await state.update_data(**user_data)
    await state.set_state(Form.name)
    await message.answer(
        "Привет! 🌟\nСейчас расскажу, как можно попасть по самой низкой цене и выиграть в колесе фортуны! 🎡💫")
    await message.answer("Для продолжения оплаты, пожалуйста, отправьте свое имя 💌 👇")


# Name and surname handler
@dp.message(Form.name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.reply("Отправьте мне свой номер 👇📲", reply_markup=ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Номер", request_contact=True)]],
        one_time_keyboard=True
    ))
    await state.set_state(Form.phone)


# Phone number handler
@dp.message(Form.phone)
async def process_phone(message: types.Message, state: FSMContext):
    if message.contact:
        await state.update_data(phone=message.contact.phone_number)

    data = await state.get_data()
    current_state = await state.get_state()

    telegram_id = data['telegram_id']

    # Load existing users
    existing_users = {}
    try:
        with open('user_data.csv', 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                existing_users[row['telegram_id']] = row
    except FileNotFoundError:
        pass

    # Check if the user already exists
    if telegram_id in existing_users:
        crm_id = existing_users[telegram_id]["crm_id"]
    else:
        info = [data["name"], "+" + data["phone"], data["start_time"]]
        crm_id = add_crm(info[0], info[1], info[2])
        await state.update_data(crm_id=crm_id)

    # Update user data
    existing_users[telegram_id] = {
        "start_time": data["start_time"],
        "telegram_id": data["telegram_id"],
        "name": data["name"],
        "phone": data["phone"],
        "state": str(current_state),
        "crm_id": crm_id
    }

    # Write updated data back to CSV
    with open('user_data.csv', 'w', newline='') as csvfile:
        fieldnames = ["start_time", "telegram_id", "name", "phone", "state", "crm_id", "payment_time"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for user in existing_users.values():
            writer.writerow(user)

    kb = [
        [types.InlineKeyboardButton(text="Kaspi 🇰🇿", callback_data="pay_kaspi")],
        [types.InlineKeyboardButton(text="Я из России 🇷🇺", callback_data="pay_prodamus")]
    ]

    await message.reply("Как вам удобнее оплатить?", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb))


@dp.callback_query(lambda c: c.data in ["pay_kaspi", "pay_prodamus"])
async def payment_method_handler(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()  # Acknowledge the callback

    if callback_query.data == "pay_prodamus":
        kb = [
            [types.InlineKeyboardButton(text="Перейти на продамус", url="https://enalika.proeducation.kz/")]
        ]
        await callback_query.message.reply("оплата", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb))
        await state.set_state(Form.prodamus)
        await callback_query.message.reply("When finished click /check")
    elif callback_query.data == "pay_kaspi":
        media_group = []
        photo_file_ids = ["AgACAgIAAxkBAAJSZWZpszHqwseqXDaxAAEUjLbYfE9aGwACqd8xG7LqUUvVCQw9Igyo3gEAAwIAA3kAAzUE",
                          "AgACAgIAAxkBAAJSZmZpszFXTIKxVpsLOiD97UFcGa0PAAKq3zEbsupRS6qQ-AL3ifiaAQADAgADeQADNQQ",
                          "AgACAgIAAxkBAAJSZ2ZpszGVWpfoOWu8uMcKPaTWtud6AAKr3zEbsupRS-528G3UftoRAQADAgADeQADNQQ",
                          "AgACAgIAAxkBAAJSaGZpszGwuk-9aB-prMVrvaJdtW15AAKP3zEbsupRS65DAn38zuLwAQADAgADeQADNQQ"]
        for photo_id in photo_file_ids:
            media_group.append(types.InputMediaPhoto(media=photo_id))

        await callback_query.message.answer_media_group(media_group)
        # Prompt for PDF receipt instead of opening the URL directly
        await callback_query.message.answer(
            "Тариф: Курс по стилю от Енлик\n\n"
            "Способ оплаты: Kaspi\n"
            "Сумма к оплате: **9.990тг.**\n\n"
            "Информация об оплате:\n"
            "1.После оплаты, отправь скрин файлом сюда\n"
            "2.Сумма должна быть ровно **9.990 тг ❤️**\n"
            "3.Получи доступ к каналу"
        )
        await state.set_state(Form.kaspi)
        kb = [
            [types.InlineKeyboardButton(text="Перейти на Каспи", url="https://pay.kaspi.kz/pay/5t1euuhq")]
        ]
        await callback_query.message.reply("Click", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb))
        await callback_query.message.answer("Загрузите квитанцию ​​об оплате Kaspi в формате PDF.")


# Receipt handler
@dp.message(Form.kaspi)
async def process_receipt(message: types.Message, state: FSMContext):
    if not message.document or message.document.mime_type != "application/pdf":
        await message.reply("Отправить чек")
        return

    try:
        pdf = "check.pdf"
        await bot.download(message.document, pdf)
        pdf_data = parse_pdf(pdf)
        online_data = parse_online_receipt(pdf)
    except Exception as e:
        await message.reply(
            "❗️ Чек некорректный, пожалуйста, проверь, что ты сделала все верно. И попробуй отправить его снова. В случае проблем можешь обратиться за помощью ниже:\n\n📞 номер для помощи wa.me/+77778378822")
        print(e)
        return

    if pdf_data != online_data:
        await message.reply("Данные не соответствуют")
        await message.reply(
            "❗️ Чек некорректный, пожалуйста, проверь, что ты сделала все верно. И попробуй отправить его снова. В случае проблем можешь обратиться за помощью ниже:\n\n📞 номер для помощи wa.me/+77778378822")

        return

    os.remove("check.pdf")
    await process_paycheck(message, online_data, state)


async def process_paycheck(message: types.Message, paycheck_data, state: FSMContext):
    paycheck_id = paycheck_data["check_number"]
    if paycheck_id in paychecks:
        await message.reply("Данный чек уже был отправлен")
        await message.reply(
            "❗️ Чек некорректный, пожалуйста, проверь, что ты сделала все верно. И попробуй отправить его снова. В случае проблем можешь обратиться за помощью ниже:\n\n📞 номер для помощи wa.me/+77778378822")

        return

    elif int(paychecks[paycheck_id]["price"]) < 9990:
        await message.reply("Сумма не соответствует цене")
        return

    print(f"Paycheck {paycheck_id} added")
    paycheck_data["user_id"] = message.from_user.id
    paychecks[paycheck_id] = paycheck_data
    save_json('paychecks.json', paychecks)

    data = await state.get_data()
    crm_id = data.get("crm_id")
    if crm_id:
        edit_crm(crm_id)
        await message.reply("Успешная оплата:\n✨ Отлично! Вижу твою оплату, сейчас вышлю ссылку для входа на канал 💕")
        await message.reply("https://t.me/+bbRnrQObMrgxYTQy")
        await message.reply("Чтобы покрутить колесо фортуны, жми на кнопку ниже и крути Колесо фортуны! 🍀🎡\n /wheel")

        # Update state to wheel_available and add payment time
        payment_time = int(time.time())
        await state.update_data(payment_time=payment_time)
        await state.set_state(Form.wheel_available)

        # Update CSV with payment time
        existing_users = {}
        try:
            with open('user_data.csv', 'r') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    existing_users[row['telegram_id']] = row
        except FileNotFoundError:
            pass

        existing_users[data["telegram_id"]].update({"payment_time": payment_time})
        existing_users[data["telegram_id"]].update({"state": "payment"})

        with open('user_data.csv', 'w', newline='') as csvfile:
            fieldnames = ["start_time", "telegram_id", "name", "phone", "state", "crm_id", "payment_time"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for user in existing_users.values():
                writer.writerow(user)
    else:
        await message.reply("CRM ID not found, cannot validate receipt.")


@dp.message(Form.prodamus)
async def proccess_prodamus(message: types.Message, state: FSMContext):
    data = await state.get_data()
    if not data["phone"] in payments or int(data["phone"]) < 9990:
        await message.reply("Proccess the payment")
        return

    crm_id = data.get("crm_id")
    if crm_id:
        print(crm_id)
        edit_crm(crm_id)
        await message.reply("Оплата валидирована")
        await message.reply("https://t.me/+E6WNLXGZH8E3ZTli")
        await message.reply("колесо фортуны /wheel")

        # Update state to wheel_available and add payment time
        payment_time = int(time.time())
        await state.update_data(payment_time=payment_time)
        await state.set_state(Form.wheel_available)

        # Update CSV with payment time
        existing_users = {}
        try:
            with open('user_data.csv', 'r') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    existing_users[row['telegram_id']] = row
        except FileNotFoundError:
            pass

        existing_users[data["telegram_id"]].update({"payment_time": payment_time})
        existing_users[data["telegram_id"]].update({"state": "payment"})

        with open('user_data.csv', 'w', newline='') as csvfile:
            fieldnames = ["start_time", "telegram_id", "name", "phone", "state", "crm_id", "payment_time"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for user in existing_users.values():
                writer.writerow(user)
    else:
        await message.reply("CRM ID not found, cannot validate receipt.")


@dp.message(Command(commands=["wheel"]))
async def play_wheel_game(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if str(current_state)[5:] != "wheel_available" or current_state is None:
        await message.reply("Please validate your receipt first.")
        return

    user_data = await state.get_data()
    name = user_data.get("name", None)
    if not name:
        await message.reply("Please enter your name first. Use /start command.")
        return

    try:
        winning_item = str(play_game(prizes, message.from_user.id))
        for prize in prizes:
            if prize['name'] == winning_item:
                photo_id = prize['photo_id']
                video_id = prize['video_id']
        video = await message.reply_video(video=video_id)

        async def delete_video_later():
            await asyncio.sleep(13)
            await bot.delete_message(chat_id=message.chat.id, message_id=video.message_id)

        await asyncio.ensure_future(delete_video_later())
        await message.reply_photo(photo=photo_id)
        await message.reply(f"Поздравляю, {name} 🔥\nТебе выпал {winning_item}.")
        if winning_item == "Урок по трендам и как их прогнозировать":
            await message.reply("https://youtu.be/3CmIe4F6IqY?si=-9HfHWKbe1fi3X2h")
        elif winning_item == "Гайд антитрендов на лето":
            await message.reply_document(
                document="BQACAgIAAxkBAAJSR2ZpmtLBbXQ6emmjqtAzPbSZvuMhAAKDTAACsupRS6G0Q08377DfNQQ")
        elif winning_item == "Урок: как правильно сочетать цвета в образах?":
            await message.reply("https://youtu.be/DKdEPHjZw3E?si=aueHIfdxRWWhKOUv")
        elif winning_item == "150.000 тг и составление капсулы от меня на лето":
            await message.reply("Напишите нам!")
        elif winning_item == "Сумка Jacquemus":
            await message.reply("Напишите нам!")

        # Save updated prize counts back to the CSV file
        with open('prizes.csv', 'w', newline='') as csvfile:
            fieldnames = ["name", "chance", "count", "photo_id", "video_id", "winners"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for prize in prizes:
                writer.writerow(prize)

    except Exception as e:
        await message.reply("Произошла ошибка. Пожалуйста, попробуйте позже.")
        print(f"Error during game: {e}")

    await state.clear()


async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())