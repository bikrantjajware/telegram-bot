
from telethon import TelegramClient, events
from telethon.sync import TelegramClient as TelegramClientSync
import csv
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty
import logging
import constants

client = TelegramClient(f'{phone}-bot',api_id,api_hash).start(bot_token=TOKEN).start()
client_user = TelegramClient(phone,api_id,api_hash)
client_user.connect()

logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s',
                    level=logging.WARNING)

"""
NOT FULLY WORKING
A BOT CLIENT DOESN'T HAVE ACCESS TO USER GROUPS, HAVING ISSUES HERE TO GET THE GROUP,CHATS

"""
#bot client listening to events, the handler will be triggered when, pattern matches the message
# message sent to the bot or if bot is added to the group (probably with admin role)
@client.on(events.NewMessage(pattern='/(?i)start')) 
async def func(event):
    sender = await event.get_sender()
    id = sender.id
    await client.send_message(id,f"Hello {sender.first_name},\n i\'ll help you add users to your groups")


@client.on(events.NewMessage(pattern='/(?i)login')) 
async def login(event):
    sender = await event.get_sender()
    id = sender.id
    if not await client_user.is_user_authorized():
        phone_code_hash = client_user.send_code_request(phone).phone_code_hash
        # client_user.sign_in(phone, input('Enter the code: '))
        # await client.send_message(id,"logged in successfully")
    else:
        await client.send_message(id,"already logged in")


@client.on(events.NewMessage(pattern='/(?i)code')) 
async def handle_otp(event):
    sender = await event.get_sender()
    id = sender.id
    if await client_user.is_user_authorized():
        return await client.send_message(id,"user already logged in")
    res = list(filter(lambda word: len(word),event.message.text.split(" ")))
    print(res)
    if len(res) != 2:
        return await client.send_message(id,"invalid code format")
    code = res[1]
    await client_user.sign_in(phone,code,phone_code_hash)
    phone_code_hash = ""
    return await client.send_message(id,"invalid code format")




@client.on(events.NewMessage(pattern='/(?i)select')) 
async def handle_select(event):
    """ doesnt work using 2 clients connecting to telegram.
    And a bot client cannot interact with user groups
    """
    sender = await event.get_sender()
    chats = []
    groups=[]
    last_date = None
    chunk_size = 200
    result = await client_user(GetDialogsRequest(
                offset_date=last_date,
                offset_id=0,
                offset_peer=InputPeerEmpty(),
                limit=chunk_size,
                hash = 0
            ))
    print(result)
    chats.extend(result.chats)
    for chat in chats:
        try:
            if chat.megagroup == True and chat.admin_rights is not None:
                groups.append(chat)
        except:
            continue
    reply_keyboard = [[ group.title for group in groups ]]*10
    group_map = {}
    for group in groups:
        group_map[group.title] = { 'id': group.id, 'access_hash': group.access_hash }
    context.user_data['group_map'] = group_map
    await client.send_message("select from list where you want to the users", reply_markup= ReplyKeyboardMarkup(
        reply_keyboard, one_time_keyboard= True, input_field_placeholder= "select group"
    ))

