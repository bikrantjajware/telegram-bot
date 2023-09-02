from telethon import TelegramClient, events
from telethon.sync import TelegramClient as TelegramClientSync
import csv
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty


client = TelegramClient(f'user-bot',api_id,api_hash)
client.connect()

if not client.is_user_authorized():
    client.send_code_request(phone)
    client.sign_in(phone,input('enter the code'))

file_path = sys.argv[1] if len(sys.argv) == 2 else 'usernames.csv'
users = []

#read local file
with open(file_path, encoding='utf-8') as f:
    rows = csv.reader(f,delimiter=",",lineterminator="\n")
    next(rows, None)
    for row in rows:
        user = {}
        user['username'] = row[0]
        # user['id'] = int(row[1])
        # user['access_hash'] = int(row[2])
        # user['name'] = row[3]
        users.append(user)


chats = []
last_date = None
chunk_size = 200
groups=[]

# get all groups, chats, channels (aka dialogues in telegram terms)
result = client(GetDialogsRequest(
             offset_date=last_date,
             offset_id=0,
             offset_peer=InputPeerEmpty(),
             limit=chunk_size,
             hash = 0
         ))
chats.extend(result.chats)
# print(chats)
# print(dir(chats[0]))
for chat in chats:
    try:       
        if chat.megagroup == True: #if its a group
            groups.append(chat)
    except:
        continue
for g in groups:
    if g.admin_rights is not None:
        print(g.title, g.admin_rights)


# get the target_group by their id and access_hash (which we can get from above in the groups variable)
target_group_entity = InputPeerChannel(target_group.id,target_group.access_hash)

# get user by username (from csv)
user_to_add = client.get_input_entity(user['username'])

#invite user to the group
client(InviteToChannelRequest(target_group_entity,[user_to_add]))



client.run_until_disconnected()
