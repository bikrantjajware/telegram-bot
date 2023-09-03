# from telegram import Update, Bot
from telegram.ext import Application, ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters, CallbackContext
import csv
from io import StringIO, BytesIO
from telethon.sync import TelegramClient
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty, InputPeerChannel
from telethon.tl.functions.channels import InviteToChannelRequest
import logging
logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s',
                    level=logging.WARNING)
import constants

client = TelegramClient(phone,api_id,api_hash)
# .start(bot_token=TOKEN)

# client.loop.run_until_complete(client.disconnected)

"""
this bot is working, although it required more polishing and error hanndling edge cases.
A simple flow is explained in start() method below
the csv file is assumed to have single column of usernames only

NOTE: Your group must be public to show in list, and to add members to group you user must have admin rights
NOTE: It's not required to add the bot in the selected group.
"""
async def start(update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not client.is_connected():
        await client.connect()
    await update.message.reply_text(f'Hello {update.effective_user.first_name} \nfollow these steps to add members to your group')
    steps = []
    steps.append('step1: use /login to login the bot')
    steps.append('step2: use /select to select a group')
    steps.append('step3: send the csv file')
    steps.append('step4: wait for bot to complete processing')
    for msg in steps:
        await update.message.reply_text(msg)  


async def login(update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        is_logged_in = await client.is_user_authorized()
        if not is_logged_in:
            res = await client.send_code_request(phone)
            context.user_data['phone_code_hash']= res.phone_code_hash
            await update.message.reply_text(f'Hello {update.effective_user.first_name}')
            await update.message.reply_text('enter the received code in this format code <received code>(check telegram inbox for code)')
        else:
            await update.message.reply_text(f'you\'re already logged in')
    except Exception as e:
        await update.message.reply_text(f"cause:{str(e)}")


async def handle_otp(update,context):
    print(update.message.text)
    params = update.message.text.split(" ")
    code = params[1]+params[2]
    msg = "default"
    if code:
        try:
            if 'phone_code_hash' in context.user_data:
                await client.sign_in(phone,code,phone_code_hash=context.user_data['phone_code_hash'])
            else:
                await client.sign_in(phone,code)
            msg = "login successful. Now /select the group"
        except Exception as e:
            print(str(e))
            msg = "login failed: "+ str(e)
    else:
        msg = "code not found, check the code format ex:- code 13713"
    await update.message.reply_text(msg)

async def select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:

        chats = []
        last_date = None
        chunk_size = 200
        groups=[]
        result = await client(GetDialogsRequest(
                    offset_date=last_date,
                    offset_id=0,
                    offset_peer=InputPeerEmpty(),
                    limit=chunk_size,
                    hash = 0
                ))
        chats.extend(result.chats)
        for chat in chats:
            try:
                if chat.megagroup == True and chat.admin_rights is not None:
                    groups.append(chat)
            except:
                continue
        reply_keyboard = [[ group.title for group in groups ]]
        group_map = {}
        for group in groups:
            group_map[group.title] = { 'id': group.id, 'access_hash': group.access_hash }
        context.user_data['group_map'] = group_map
        await update.message.reply_text("select from list where you want to the users", reply_markup= ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard= True, input_field_placeholder= "select group"
        ))
    except Exception as e:
        await update.message.reply_text(f"cause: {str(e)}")




async def handle_file(update, context):
    if context.user_data is None or 'target_group_id' not in context.user_data:
        return await update.message.reply_text("No group selected, /select the group again")
    file = await update.message.document.get_file()
    file_content = await file.download_as_bytearray()
    target_group_id = context.user_data['target_group_id']
    target_group_access_hash = context.user_data['target_group_access_hash']
    target_group_entity = InputPeerChannel(target_group_id,target_group_access_hash)
    usernames = file_content.decode('utf-8').split('\n')[1:]
    # await update.message.reply_document(document=BytesIO(file_content), filename='received_file.txt')
    for user_to_add in usernames:
        print(user_to_add);
        try:
            await client(InviteToChannelRequest(target_group_entity,[user_to_add]))
            await update.message.reply_text(f"done {user_to_add}")
        except Exception as e:
            await update.message.reply_text(f"error {str(e)}")
        # mem = await bot.get_users(<user_id>)
        # print("mem",mem)
        # if mem:
        #     mem = mem[0]
        # await bot.invite_chat_member(<group_id>,mem.id)
    # Reset user_data here



async def command(update,context):
    if not update.message:
        await update.message.reply_text("invalid")
    command = update.message.text[8:].strip()
    message = ""
    print(command)
    if not command:
        message = "invalid command"
    else:
        context.user_data['command'] = command
        message = "now send the file"
    await update.message.reply_text(message)

async def handle_select(update,context):
    try:
        selected_group = update.message.text
        print('user data',context.user_data)
        if 'group_map' not in context.user_data or selected_group not in context.user_data['group_map']:
            await update.message.reply_text(f"incorrect group {selected_group}, try again!")
            return
        context.user_data['target_group_id'] = context.user_data['group_map'][selected_group]['id']
        context.user_data['target_group_access_hash'] = context.user_data['group_map'][selected_group]['access_hash']
        await update.message.reply_text(f"you selected {selected_group}")
        await update.message.reply_text("now send the csv file")
    except Exception as e:
        await update.message.reply_text(f"cause: {str(e)}")



async def logout(update,context):
    await client.log_out()
app = ApplicationBuilder().token(TOKEN).build()
# command handler reads the message that starts with /<command> and only if a handler is added (ignored othwewise)
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("login", login))
app.add_handler(MessageHandler(filters.Regex(r'code\s\d+'), handle_otp))
app.add_handler(CommandHandler("select", select))

app.add_handler(CommandHandler("command", command))
app.add_handler(CommandHandler("logout", logout))

# Message handler is triggerd by raw text, we can match the text with a regex or some common types like (TEXT, MEDIA, DOCUMENT, etc)
app.add_handler(MessageHandler(filters.TEXT, handle_select))
app.add_handler(MessageHandler(filters.ATTACHMENT, handle_file))
app.run_polling(allowed_updates=Update.ALL_TYPES)



# __________

# python3 -m pip install --upgrade pip

"""
Update(message=Message(channel_chat_created=False, chat=Chat(first_name='bikrant', id=506620090, type=<ChatType.PRIVATE>, username='x62696b72616e74'), date=datetime.datetime(2023, 8, 28, 13, 9, 47, tzinfo=datetime.timezone.utc), delete_chat_photo=False, entities=(MessageEntity(length=6, offset=0, type=<MessageEntityType.BOT_COMMAND>),), from_user=User(first_name='bikrant', id=506620090, is_bot=False, language_code='en', username='x62696b72616e74'), group_chat_created=False, message_id=7, supergroup_chat_created=False, text='/hello'), update_id=608039715) <telegram.ext._callbackcontext.CallbackContext object at 0x1025184a0>
Update(message=Message(channel_chat_created=False, chat=Chat(api_kwargs={'all_members_are_administrators': True}, id=-935559002, title='MFM', type=<ChatType.GROUP>), date=datetime.datetime(2023, 8, 28, 13, 11, 8, tzinfo=datetime.timezone.utc), delete_chat_photo=False, entities=(MessageEntity(length=6, offset=0, type=<MessageEntityType.BOT_COMMAND>),), from_user=User(first_name='bikrant', id=506620090, is_bot=False, language_code='en', username='x62696b72616e74'), group_chat_created=False, message_id=9, supergroup_chat_created=False, text='/hello'), update_id=608039718) <telegram.ext._callbackcontext.CallbackContext object at 0x1025184a0>
"""

