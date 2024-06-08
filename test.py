import asyncio
from pyrogram import Client
from pyrogram import errors
API_TOKEN = '6422952891:AAFWdrhr7-2mUnsMnNCZsYYPAjB_SY-bDvM'
API_ID = '21800165'
API_HASH = '93d868f138ceffc726270b437797ce47'
CHAT_ID = "-4255470098"


async def main():
    async with Client("my_account", API_ID, API_HASH) as app:
        try:
            link = await app.create_chat_invite_link(CHAT_ID, member_limit=3)
            print(link)
        except errors.exceptions.bad_request_400.PeerIdInvalid:
            print("Error: Peer ID invalid. Make sure your bot is in the chat.")

asyncio.run(main())
