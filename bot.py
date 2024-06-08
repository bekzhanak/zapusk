import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.filters import CommandStart
from aiogram.types import contact, document
import asyncio
from utils import *

API_TOKEN = '7287215925:AAFUI8JK7cPgi4QZQh_i6FxUhehK8Qb_pac'

logging.basicConfig(level=logging.INFO)


bot = Bot(token=API_TOKEN)
dp = Dispatcher()

paychecks = load_json('paychecks.json')


# Define states
class Form(StatesGroup):
    name = State()
    phone = State()
    kaspi = State()
    prodamus = State()


# Start command handler
@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await state.set_state(Form.name)
    await message.reply("Please enter your name and surname:")


# Name and surname handler
@dp.message(Form.name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.reply("Please share your phone number:", reply_markup=ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Share phone number", request_contact=True)]],
        one_time_keyboard=True
    ))
    await state.set_state(Form.phone)


# Phone number handler
@dp.message(Form.phone)
async def process_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.contact.phone_number)

    data = await state.get_data()
    with open('user_data.json', 'w') as f:
        json.dump(data, f)
    kb = [
        [types.InlineKeyboardButton(text="Kaspi", callback_data="pay_kaspi")],
        [types.InlineKeyboardButton(text="Prodamus", callback_data="pay_prodamus")]
    ]

    await message.reply("Choose the payment method:", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb))


@dp.callback_query(lambda c: c.data in ["pay_kaspi", "pay_prodamus"])
async def payment_method_handler(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()  # Acknowledge the callback

    if callback_query.data == "pay_prodamus":
        await state.set_state(Form.prodamus)
        await callback_query.message.answer("https://enalika.proeducation.kz/")
        await callback_query.message.answer("Prodamus payment is not yet implemented.")
    elif callback_query.data == "pay_kaspi":
        # Prompt for PDF receipt instead of opening the URL directly
        await state.set_state(Form.kaspi)
        await callback_query.message.answer("https://pay.kaspi.kz/pay/5t1euuhq")
        await callback_query.message.answer("Please upload your PDF receipt for Kaspi payment.")


# Receipt handler
@dp.message(Form.kaspi)
async def process_receipt(message: types.Message, state: FSMContext):
    if not message.document or message.document.mime_type != "application/pdf":
        await message.reply("Send receipt")
        return

    try:
        pdf = "check.pdf"
        await bot.download(message.document, pdf)
        pdf_data = parse_pdf(pdf)
        online_data = parse_online_receipt(pdf)
    except Exception as e:
        await message.reply("Этот чек не корректен")
        print(e)
        return

    if pdf_data != online_data:
        await message.reply("Данные не соответствуют")
        return

    os.remove("check.pdf")
    await process_paycheck(message, online_data, state)


async def process_paycheck(message, paycheck_data, state):
    paycheck_id = paycheck_data["check_number"]
    if paycheck_id in paychecks:
        await message.reply("Данный чек уже был отправлен")
        return

    print(f"Paycheck {paycheck_id} added")
    paycheck_data["user_id"] = message.from_user.id
    paychecks[paycheck_id] = paycheck_data
    save_json('paychecks.json', paychecks)
    await message.reply("Чек валидирован")
    await message.reply("https://t.me/+E6WNLXGZH8E3ZTli")

    await state.clear()


async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
