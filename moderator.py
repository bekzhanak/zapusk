from aiogram import Bot, Dispatcher, types
import asyncio
import csv

# Replace with your actual Telegram bot token
BOT_TOKEN = "6955797688:AAEL6QuK_E_M4n-sfxbgokzWr5JhlXZjIgI"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def get_auth_users():
    auth_users = []
    with open("user_data.csv", "r") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            if row["status"] == "payment":
                auth_users.append(row["telegram_id"])
    return auth_users

@dp.chat_join_request()
async def handle_new_chat_members(update: types.ChatJoinRequest):
    """Handles new members joining the channel."""
    print("hello")
    new_member = update.from_user.id

    if new_member in get_auth_users():
        await update.approve()


async def main():
    """Starts the Telegram bot."""
    # Run the bot asynchronously
    print("start")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
