from aiogram import Bot, Dispatcher, types
import asyncio

# Replace with your actual Telegram bot token
BOT_TOKEN = "6955797688:AAEL6QuK_E_M4n-sfxbgokzWr5JhlXZjIgI"

# Replace with the channel ID (can be found from the channel info URL)
CHANNEL_ID = -1002166911197  # Use a negative value for channel IDs

# List of authorized user IDs (replace with actual IDs)
AUTHORIZED_USER_IDS = [897190202]

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


async def check_and_delete_user(chat_id: int, user_id: int):
    """Checks if the user is authorized and removes them if not."""
    if user_id not in AUTHORIZED_USER_IDS:
        try:
            await bot.ban_chat_member(chat_id=chat_id, user_id=user_id)
            print(f"Removed unauthorized user: {user_id}")
        except Exception as e:
            print(e)


@dp.message()
async def handle_new_chat_members(message: types.Message):
    """Handles new members joining the channel."""
    print("hello")
    chat = message.chat
    new_members = message.new_chat_members

    if chat.id == CHANNEL_ID:
        for member in new_members:
            await check_and_delete_user(chat.id, member.id)


async def main():
    """Starts the Telegram bot."""

    # Run the bot asynchronously
    await dp.start_polling(bot)


if __name__ == "__main__":
    bot.ban_chat_member(chat_id=CHANNEL_ID, user_id=1)
    asyncio.run(main())
