import telebot
from telebot import apihelper
import os
from group_queues import GroupDispatcher
from db_controller import Controller
from openpyxl import load_workbook
from dotenv import load_dotenv
from speech_analyzer import VoiceSaver
env_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)
API_TOKEN = os.getenv('API_TOKEN_TEST')


def create_test_data(path='TEST1.xlsx', rows=73, cols=5):
    test = {}
    wb = load_workbook(filename=path)
    sheet = wb.active
    alph = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    res = []
    for i in range(2, rows):
        col = []
        for j in range(cols):
            tmp = ''.join((alph[j], str(i)))
            col.append(sheet[tmp].value)
        if col[0] is None:
            col = col[2:4]
        res.append(col)

    for i in res:
        if len(i) != 2:
            tmp = i[1:4]
            test.update([(tmp[0], {'answers': [], 'scores': []})])
            test[tmp[0]]['answers'].append(tmp[1])
            test[tmp[0]]['scores'].append(tmp[2])
        else:
            test[tmp[0]]['answers'].append(i[0])
            test[tmp[0]]['scores'].append(i[1])
    return test


test_one = create_test_data()
apihelper.proxy = {'https':'http://admin@managewell.ru:gdkLH65%@ua23.nordvpn.com:80'}
ctrl = Controller('base.db')
bot = telebot.TeleBot(API_TOKEN)
VS = VoiceSaver('voice_messages', bot,  API_TOKEN, os.getenv('API_TOKEN_YDX'),
                ctrl.query_adm_data('users', ', '.join(('chat_id', 'audio_message_counter'))))
dispatcher = GroupDispatcher(ctrl.query_any_rows('users.group_code', 'groups.group_code',
                                                 'groups, users', ','.join(('groups.group_name', 'users.chat_id'))),
                             ctrl, test_one, bot)
print(dispatcher.groups_data)
users = {}
callbacks = {}
print(dispatcher.groups_code_map)
print(dispatcher.dispatch_map)


@bot.message_handler(content_types='text')
def handle_text(message):
    if message.chat.id in dispatcher.users_list():
        print('ID = {0}; message = {1}'.format(message.chat.id, message.text))
        dispatcher.users()[message.chat.id].handler(message)
    else:
        dispatcher.add_user(message.chat.id, bot, ctrl, message, test_one)


@bot.message_handler(content_types='voice')
def handle_voice(message):
    if message.chat.id in dispatcher.users_list():
        ctrl.update_voice_counter(message.chat.id)
        cur_user = dispatcher.users()[message.chat.id]
        print('ID = {0}; message = {1}'.format(message.chat.id, message.text))
        VS.download_voice(message, cur_user.id, cur_user.name(), cur_user.surname(), True)
        cur_user.handler(message)
    else:
        dispatcher.add_user(message.chat.id, bot, ctrl, message, test_one)
        print(dispatcher.users_list())

@bot.message_handler(content_types=['document', 'photo', 'video', 'video_note'])
def handle_files(message):
    print(message)
    if message.content_type == 'photo':
        dispatcher.users()[message.chat.id].photo_handler(message)

    elif message.content_type == 'document':
        dispatcher.users()[message.chat.id].document_handler(message)

    elif message.content_type == 'video':
        dispatcher.users()[message.chat.id].video_handler(message)

    elif message.content_type == 'video_note':
        dispatcher.users()[message.chat.id].video_note_handler(message)


@bot.callback_query_handler(func=lambda call: True)
def smo(call):
    try:
        dispatcher.add_callback(call)
        print(call.data)
        if call.data in ['case1', 'case2', 'case3']:
            dispatcher.users()[call.message.chat.id].start_conversation(call.message)
        dispatcher.users()[call.message.chat.id].callback_handler(call)
    except Exception as e:
        print(e)


bot.infinity_polling()
