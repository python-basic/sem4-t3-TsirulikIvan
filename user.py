from telebot import types
import smtplib
import random
import datetime
from threading import Timer
from Test import parse_time_from_string
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import re
from dotenv import load_dotenv
import os
env_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)



def normalize_test(test):
    res = []
    for i in test:
        indexs = []
        delt = 0
        for j in test[i]['scores']:
            if j == 1:
                indexs.append(test[i]['scores'].index(j, delt) + 1)
                delt += 1
            else:
                delt += 1
                continue
        res.append(indexs)
    return res


class User:
    def __init__(self, msg, bot, ctrl, test):
        self.test_style = {'hard': ['Мне важнее удовлетворить свои интересы чем сохранить отношения',
                                    'Даже если другой переговорщик испытывает трудности, я не буду пересматривать из-за'
                                    ' этого выгодный договор.', 'Каждый должен заботиться о своих интересах.',
                                    'Всегда лучше получать что-либо даром, чем в обмен на что-то.',
                                    'Надо быть жестким, чтобы преуспеть в бизнесе.',
                                    'Сила более полезна в переговорах, чем аргументация.',
                                    'Нужно давить еще сильнее, если другой переговорщик на это поддается',
                                    'Другой переговорщик может воспользоваться моими эмоциями, поэтому я их не показываю',
                                    'Я готов использовать другого переговорщика в своих интересах, если есть такая '
                                    'возможность', 'Я не должен принимать во внимание, как повлияют на другого'
                                                   ' переговорщика мои хитрости.'],
                           'soft': ['Я считаю нечестным использовать ошибку другого переговорщика в своих интересах',
                                    'Переговорщики должны показывать свои чувства и намерения',
                                    'Сделка с незначительной выгодой, лучше, чем никакая',
                                    'Я более сговорчив, поскольку для меня важны взаимоотношения',
                                    'Создание хороших отношений важнее, чем использование слабых сторон оппонента',
                                    'Я откровенно озвучиваю свои намерения и это приносит пользу',
                                    'Если оппоненты проявляют мягкость и не могут позаботиться о себе, нельзя этим пользоватьс'
                                    'я в своих интересах',
                                    'Лучше сохранить добрые отношения с оппонентом, чем отказаться от'
                                    ' невыгодной сделки с ним', 'Я должен уступать сложным людям, в'
                                                                ' ином случае я потеряю возможности',
                                    'В ходе переговоров, я переживаю, что мне могут отказать'],
                           'partner': ['Я думаю, что в переговорах мы с оппонентом вместе решаем проблему',
                                       'В переговорах прежде всего нужен разумный справедливый результат, а не просто '
                                       'соглашение',
                                       'Мне не важно насколько я доверяю визави, я продолжаю переговоры вне зависимости от'
                                       ' этого',
                                       'Я обязан фокусироваться на интересах сторон, а не на заявленных ими позициях',
                                       'В переговорах я разделяю людей и их проблемы, а не требую уступки для сохранения'
                                       ' отношений',
                                       'Больше пользы приносит мягкий подход с людьми и жесткий с проблемой',
                                       'Вместо того, чтобы делать предложения, я сначала анализирую интересы сторон',
                                       'В переговорах я настаиваю на применении объективных критериев, а не на соглашении',
                                       'Я ищу взаимовыгодные варианты, вместо того чтобы требовать для себя уступки',
                                       'Я готов уступать доводам и не поддавать давлению']}
        self.conv_score = 0
        self.social_score = 0
        self.nego_logger = None
        self.ex_vizavis = []
        self.res_test = {'hard': 0, 'soft': 0, 'partner': 0}
        self.is_winner = None
        self.message_counter = 0
        self.msg = msg
        self.subscribers = []
        self.case_role = None
        self.ctrl = ctrl
        self.bot = bot
        self.id = msg.chat.id
        self.done_test_style = False
        self.test_score = 0
        self.vizavi = None
        self.is_admin = False
        self.NPS = 0
        self.goals = []
        self.counter = 0
        self.case = 'case1'
        self.__name = None
        self.__surname = None
        self.__company = None
        self.__phone = None
        self.last_nego_id = None
        self.__score = 1
        self.__group_code = None
        self.__state = 'NO_REG'
        self.__test_ref = test
        self.container = []
        self.deadlines = None
        self.lang = 'ru'
        self.metadata = []
        self.timer = None
        self.trend = None
        self.ready_to_nego = False
        self.query_data()

    def send_image(self, filename):
        with open(filename, 'rb') as file:
            self.bot.send_photo(self.id, file)

    def create_inline_markup(self, titles=('Хочу провести переговоры✍', 'Личный кабинет☑'),
                             callbacks=None, width=1):
        if callbacks is None:
            callbacks = (self.case, 'profile')
        markup = types.InlineKeyboardMarkup(row_width=width)
        buttons = [types.InlineKeyboardButton(text=title, callback_data=callback_data)
                   for title, callback_data in zip(titles, callbacks)]
        markup.add(*buttons)
        return markup

    def add_NPS_value(self, value):
        self.NPS += value
        self.ctrl.update_data(table_name='NPS_data', cond='user_id', cond_value=self.id, new_value=self.NPS,
                              col_name='NPS_value')

    def add_user_to_db(self):
        groups = self.ctrl.query_adm_data('groups', 'group_code')
        print(groups)
        print(self.group_code())
        groups = [i[0] for i in groups]
        print(groups)
        if self.group_code() not in groups:
            raise KeyError
        else:
            time = datetime.datetime.now().strftime("%Y-%m-%d-%H.%M.%S")
            self.ctrl.add_record(col_values=(self.id, self.name(), self.surname(), self.company(), self.__phone,
                                             self.__group_code, self.__state, time), col_names=('chat_id', 'user_name',
                                                                                                'user_surname', 'company',
                                                                                                'phone_number',
                                                                                                'group_code', 'state',
                                                                                                'reg_date'))

    def welcome_message(self, custom_markup=None, external_text=None, greetings_on=True):
        self.change_state('MAIN_MENU')
        if greetings_on:
            msg = f'Добро пожаловать, {self.name()}\n'
        else:
            msg = ''
        if external_text is not None:
            print('not none external')
            msg += external_text
        print(msg)
        if custom_markup is None:
            self.send_message(msg, markup=self.create_inline_markup(['Личный кабинет'], ['profile']), parse_mode='html')
        else:
            self.send_message(msg, markup=custom_markup, parse_mode='html')

    def edit_message(self, message_id, string, markup=None, parse_mode=None):
        self.bot.edit_message_text(chat_id=self.id, message_id=message_id, text=string, reply_markup=markup,
                                   parse_mode=parse_mode)

    def send_message(self, string, markup=None, parse_mode=None):
        self.bot.send_message(self.id, string, reply_markup=markup, parse_mode=parse_mode)

    def query_vizavi(self):
        print(f'query_vizavi in {self.id}')
        conv_number = int(self.case[4])
        sides = [('rus_side', 'china_side'), ('star_side', 'atom_side'), ('orion_side', 'dental_star_side')]
        tmp = []
        print(conv_number)
        try:
            for i in range(0, conv_number):
                print(sides[i][0])
                print(self.ctrl.query_all(f'conversation{i + 1}'))
                res = self.ctrl.query_any_rows(col_name=', '.join((*sides[i], 'is_finished', 'id')),
                                               table_name=f'conversation{i + 1}', cond_value=self.id, cond=sides[i][0])
                print(f'res1 = {res}')
                if len(res) != 1:
                    print('second query')
                    res = self.ctrl.query_any_rows(col_name=', '.join([*sides[i], 'is_finished', 'id']),
                                                   table_name=f'conversation{i + 1}', cond_value=self.id,
                                                   cond=sides[i][1])
                    print(f'res2 = {res}')
                print(bool(res[0][2]))
                if res[0][2] in ['True', 'true']:
                    print('here')
                    print(res[0][0:2])
                    tmp.append(res[0][0:2])
                    print(res)
                    self.last_nego_id = res[0][3]
                else:
                    self.last_nego_id = res[0][3]
                    print('No end nego')
        except IndexError:
            print(f'tmp = {tmp}')
        print(f'nego_id = {self.last_nego_id} at {self}')
        print(f'tmp = {tmp}')
        for j in tmp:
            for i in j:
                print(j)
                if i != self.id:
                    info = list(self.ctrl.query_any_rows('chat_id', i, col_name=','.join(('chat_id', 'user_name',
                                                                                          'user_surname')))[0])
                    print(info)
                    print(j.index(info[0]))
                    info.append(sides[tmp.index(j)][j.index(info[0])])
                    self.ex_vizavis.append(info)
                    continue
        print(f'Final ex_vizavi= {self.ex_vizavis}')

    def query_data(self):
        data = self.ctrl.query_any_rows('chat_id', self.id,
                                        col_name=','.join(('user_name', 'user_surname', 'company', 'phone_number',
                                                           'group_code', 'score', 'state', 'cur_case', 'social_score')))
        print(data)
        try:
            self.__name, self.__surname, self.__company, self.__phone, self.__group_code, self.__score, self.__state, \
            self.case, self.social_score = data[0]
            if self.state() == 'WAITING_4_CERT':
                try:
                    generic_ratings = open(f'"content/{self.group_code()}/Рейтинги эффективности и социальной активности .pdf"', 'rb')
                    cert = open(f'"content/{self.group_code()}/cert/{self.name()} {self.surname()}.jpg"', 'rb')
                    report = open(f'"content/{self.group_code()}/reports/{self.name()} {self.surname()}.pdf"', 'rb')
                    self.bot.send_document(self.id, generic_ratings)
                    self.bot.send_photo(self.id, cert)
                    self.bot.send_document(self.id, report)
                    self.send_message(
                        'Добрый день!👋🏼\n\nСегодня пора подводить итоги нашего трехнедельного путешествия. Выше Вы'
                        ' увидите общий рейтинг участников, а еще свой именной сертификат и индивидуальный отчет '
                        'получат те участники, которые успешно завершили одни и более переговоров.\n\nВаш Негобот👾')
                    generic_ratings.close()
                    cert.close()
                    report.close()
                except FileNotFoundError as e:
                    self.send_message('Если вам не пришло что-то из вложений, не переживайте, пожалуйста сообщите об'
                                      ' этом на почту bot@sellwell.ru')
            elif self.state() == 'WAITING_4_REPORTS':
                try:
                    report = open(f'"content/{self.group_code()}/reports/{self.name()} {self.surname()}.pdf"', 'rb')
                    self.bot.send_document(self.id, report)
                    self.send_message('Добрый день! Выше вам был отправлен ваш индивидуальный отчет по итогам работы со мной:)'
                                      'С вами было очень приятно работать\n\nВаш Негобот👾')
                except Exception as e:
                    print('Cant send!')
            print(f'{self.last_nego_id}')
            try:
                self.query_vizavi()
            except IndexError as e:
                print(f'Error {e}')
                print(f'{self.last_nego_id}')
                print(f'ex_vizavi = {self.ex_vizavis}')
            print(f'ex_vizavi = {self.ex_vizavis}')
        except IndexError as e:
            print(e)
            self.send_image('content/images/user_agreement.png')
            self.registration()

    def send_message_to_vizavi(self, text, markup=None, parse_mode='html'):
        self.bot.send_message(self.vizavi[0], '<b>{0} {1}</b>:\n{2}'.format(self.name(),
                                                                            self.surname(), text), reply_markup=markup,
                              parse_mode=parse_mode)

    def registration(self):
        first_markup = types.InlineKeyboardMarkup()
        first_markup.add(types.InlineKeyboardButton(text='Принять соглашение', callback_data='accept'))
        self.send_message('Добро пожаловать! Прежде чем мы нанчем обучение, прошу ознакомиться с пользовательским '
                          'соглашением\nhttps://teletype.in/@sellwell/r1AkRWraH\n', first_markup)

    def start_test(self):
        self.send_image('content/images/before_test.png')
        self.change_state('BEGIN_TEST')
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton('Начать тест!', callback_data='start_test'))
        self.send_message('Перед началом переговоров, предлагаю вам пройти небольшой тест из 15 вопросов.  Это займёт'
                          ' не более 10 минут. Тест поможет проверить свои знания,полученные на тренинге, а также'
                          ' подготовит Вас к практике.\n\n<b>Переговоры начнутся только после того, как вы ответите'
                          ' на все вопросы.</b>', markup, parse_mode='html')

    def handler(self, message):
        print('Handler of user: {0}, state: {1}'.format(self.id, self.state()))
        self.save_last_message(message)
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add('Договорились👍', 'Покинуть переговоры!❌')
        if self.state()[0:20] == 'IN_CONVERSATION_CASE' or self.state() == 'WAITING_4_ACCEPT':
            self.message_counter += 1
            if message.voice is None:
                self.subscribers[1].save_message(message.text, self.name(), self.surname())
                vizavi_state = self.subscribers[0].users()[self.vizavi[0]].state()
                if message.text == 'Договорились👍' and vizavi_state == 'WAITING_4_ACCEPT':
                    self.send_message('Ваш визави ожидает подтверждения договоренностей!')
                elif message.text == 'Договорились👍' and self.state()[0:20] == 'IN_CONVERSATION_CASE':
                    self.change_state('WAITING_4_ACCEPT')
                    self.bot.send_message(self.vizavi[0], '<b>Подождите, {0} {1} вводит договоренности...</b>\n\n'
                                                          'После получения предложения визави, Вы можете принять его '
                                                          'или отклонить и продолжить договариваться'
                                                          ''.format(self.name(), self.surname()),
                                          reply_markup=types.ReplyKeyboardRemove(), parse_mode='html')
                    self.goals.clear()
                    self.set_final_goals()

                elif message.text == 'Договорились👍' and self.state() == 'WAITING_4_ACCEPT':
                    self.send_message('Вы уже ввели и отправили договоренности вашему визави!')

                elif message.text == 'Покинуть переговоры!❌':
                    self.send_message('Вы уверены! Если вы покинете переговоры, '
                                      'Вам будет поставлено 0 баллов!', self.create_inline_markup(['Остаться',
                                                                                                   'Покинуть'],
                                                                                                  ['stay', 'leave']))
                else:
                    self.send_message_to_vizavi('' + message.text, markup=markup)
            else:
                self.send_message_to_vizavi('')
                self.send_voice(message.voice.file_id)
        elif self.state() == 'NO_REG':
            self.send_message('Прежде чем начать работу с ботом,\nПримите пользовательское соглашение!')
        elif self.state() == 'SET_CASE_GOALS':
            self.send_message('Во время подготовки к переговорам команды недоступны!')
        elif self.state() == 'READY_TO_CONV':
            self.send_message('Ваш визави еще не закончил подготовку и поэтому не видит ваши сообщения.')
        elif self.state() == 'FINISH_NEGO':
            self.send_message("Вы уже закончили переговоры и получили результаты. Для дальнейшего обучения нажмите"
                              " кнопку 'Сравнить свои цели с результатами', которая находится выше")
        elif self.state() == 'SET_CASE_GOALS':
            self.send_message("В данный момент чат с визави недоступен. Пожалуйста нажмите на кнопку сверху для того "
                              "чтоб двигаться дальше!")
        elif self.state() == 'WAITING_4_FB':
            self.send_message('Визави еще не выдал Вам обратную связь, подождите пожалуйста.')
        else:
            if message.text == '/help':
                self.send_message('<i>/start</i> - Вызов главного меню\n<i>/contact</i> - Контакты для связи',
                                  parse_mode='html')
            elif message.text == '/start':
                self.welcome_message()
            elif message.text == '/contact':
                self.send_message('email: <i>bot@sellwell.ru</i>', parse_mode='html')
            else:
                self.send_message('Я Вас не понимаю. Введите команду /help\nдля вызова справки')

    def NPS_func(self):
        name = ' '.join(self.vizavi[1:3])
        mkp = types.InlineKeyboardMarkup(row_width=5)
        mkp.add(*[types.InlineKeyboardButton(str(i), f'NPS_{i}') for i in range(11)])
        self.send_message(f'Теперь прошу вас подумать и оценить по десятибалльной шкале, насколько вы бы хотели '
                          f'видеть {name} в своей команде переговорщиков на реальных переговорах?\n<b>{name} увидит '
                          f'средний показатель только по итогам всех трех кейсов.</b>', parse_mode='html', markup=mkp)

    def photo_handler(self, message):
        if self.state()[0:20] == 'IN_CONVERSATION_CASE':
            self.message_counter += 1
            try:
                self.bot.send_photo(self.vizavi[0], message.json['photo'][2]['file_id'])
            except IndexError:
                try:
                    self.bot.send_photo(self.vizavi[0], message.json['photo'][1]['file_id'])
                except IndexError:
                    self.bot.send_photo(self.vizavi[0], message.json['photo'][0]['file_id'])

    def document_handler(self, message):
        if self.state()[0:20] == 'IN_CONVERSATION_CASE':
            self.message_counter += 1
            self.bot.send_document(self.vizavi[0], message.document.file_id)

    def video_handler(self, message):
        if self.state()[0:20] == 'IN_CONVERSATION_CASE':
            self.message_counter += 1
            self.bot.send_video(self.vizavi[0], message.video.file_id)

    def video_note_handler(self, message):
        if self.state()[0:20] == 'IN_CONVERSATION_CASE':
            self.message_counter += 1
            self.bot.send_video_note(self.vizavi[0], message.video_note.file_id)

    def callback_handler(self, callback):
        if callback.data == 'accept':
            self.edit_message(callback.message.message_id, 'У меня было достаточно времени, чтобы прочитать'
                                                           ' пользовательское соглашение и я соглашаюсь на его '
                                                           'условия', self.create_inline_markup(('Подтверждаю',
                                                                                                 'Не подтверждаю'),
                                                                                                ('r_accept',
                                                                                                 'r_decline')))

        elif callback.data == 'r_accept':
            def set_name(message):
                self.save_last_message(message)
                self.change_state('IN_REG')
                self.send_message('Введите Ваше имя, например:\n<i>Артем</i>', parse_mode='html')
                self.__surname = message.text
                self.bot.register_next_step_handler(message, set_surname)

            def set_surname(message):
                self.__name = message.text
                self.save_last_message(message)
                self.send_message('Введите название Вашей компании, например: <i>SellWell</i>', parse_mode='html')
                self.bot.register_next_step_handler(message, set_company)

            def set_company(message):
                self.__company = message.text
                self.save_last_message(message)
                keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
                button_phone = types.KeyboardButton(text="Отправить номер телефона", request_contact=True)
                keyboard.add(button_phone)
                self.send_message('Введите номер телефона\n<i>Например:  8919*******</i>', parse_mode='html')
                self.bot.register_next_step_handler(message, set_phone)

            def set_phone(message):
                if message.text is None:
                    number = message.contact.phone_number
                else:
                    number = message.text
                if re.match(r'[7-8]{1}[0-9]{10}', str(number)) is None or len(number) != 11:
                    self.send_message('Номер введен неверно!😔\nпожалуйста повторите ввод через 8 без дополнительных '
                                      'символов.\n<i>Например:  8919*******</i>', parse_mode='html')
                    self.bot.register_next_step_handler(message, set_phone)
                else:
                    self.send_message('Поздравляю с регистрацией, {0}!\n'
                                      'Прошу прочитать инструкцию по работе с ботом, прежде чем двигаться дальше.'
                                      ' Это поможет познакомиться с программой и быстрее вникнуть в особенности'
                                      ' обучения.\n{1}'.format(self.name(), 'https://teletype.in/@sellwell/ZWinpEyF'))
                    self.__phone = number
                    keyboard = types.InlineKeyboardMarkup()
                    key_yes = types.InlineKeyboardButton(text='Есть промокод!', callback_data='have_code')
                    key_no = types.InlineKeyboardButton(text='Нет промокода!', callback_data='no_code')
                    keyboard.add(key_yes, key_no)
                    self.send_message('У вас есть код группы(промокод)\n'
                                      'который вам выдали в начале обучения?', keyboard)

            self.edit_message(callback.message.message_id, 'Вы приняли соглашение.\nПожалуйста введите Вашу фамилию.'
                                                           ' Например:\n<i>Добролюбов</i>', None, parse_mode='html')
            self.bot.register_next_step_handler(callback.message, set_name)

        elif callback.data == 'r_decline':
            self.edit_message(callback.message.message_id, 'Вы не приняли соглашение', None)
            markup1 = types.InlineKeyboardMarkup()
            markup1.add(types.InlineKeyboardButton('Принять соглашение!', callback_data='r_accept'))
            self.send_message('Прежде чем начать работу с ботом,\nПримите пользовательское соглашение!\n'
                              'https://teletype.in/@sellwell/r1AkRWraH', markup1)

        elif callback.data in ['case1', 'case2', 'case3']:
            self.edit_message(callback.message.message_id, 'Вы сможете посмотреть статистику в личном кабинете только'
                                                           ' после завершения переговоров.', markup=None)

        elif callback.data == 'have_code':
            self.edit_message(message_id=callback.message.message_id, string='Прекрасно! В приглашении Вам высылали код'
                                                                             ' доступа. Прошу ввести его в поле ниже '
                                                                             '<b>заглавными буквами без пробелов</b>:\n'
                                                                             'Например:  <i>TEST</i>',
                              parse_mode='html')
            self.bot.register_next_step_handler(callback.message, self.get_code)

        elif callback.data in ['case' + str(i) for i in range(1, 4)]:
            pass

        elif callback.data == 'no_code':
            self.change_state('IS_REG')
            self.edit_message(message_id=callback.message.message_id,
                              string='Вам не предоставили код😔\n'
                                     'К сожалению, без промокода функционал бота недоступен.\nПожалуйста напишите'
                                     ' письмо на почту bot@sellwell.ru😉. Как только Вам придет промокод просто'
                                     ' введите его')
            self.send_mail()
            self.bot.register_next_step_handler(callback.message, self.get_code)

        elif callback.data == 'start_test':
            self.edit_message(callback.message.message_id, 'Перед началом переговоров, предлагаю вам пройти небольшой'
                                                           ' тест из 15 вопросов.  Это займёт не более 10 минут. Тест '
                                                           'поможет проверить свои знания,полученные на тренинге, а'
                                                           ' также подготовит Вас к практике.\n\n<b>Ответы вводятся '
                                                           'через запятую в одну строку</b>\nНапример: 1,4',
                              parse_mode='html')
            self.send_question(len(self.metadata))
            self.bot.register_next_step_handler(callback.message, self.get_answer)

        elif callback.data == 'accept_goals':
            if self.case == 'case1':
                self.edit_message(callback.message.message_id,
                                  'Вспомните материалы тренинга и напишите (в одном сообщении):\n<b>Как именно Вы '
                                  'планируете добиться выгодных для Вас условий?</b>\n\nНапример:\n<i>Я собираюсь '
                                  'сконцентрироваться на шаге ИЗУЧАЮ, а именно буду задавать открытые вопросы, чтобы'
                                  ' найти допустимые диапазоны, приоритеты и интересы визави, и в дальнейшем иметь '
                                  'поле для маневров.</i>\n', markup=None, parse_mode='html')
                self.bot.register_next_step_handler(callback.message, self.set_case_goals)

            elif self.case in ['case2', 'case3']:
                labels = ['Якорю', 'Убеждаю', 'Структурирую', 'Изучаю', 'Предлагаю', 'Торгуюсь', 'Закрываю']
                self.edit_message(callback.message.message_id, 'Исходя из полученной обратной связи по итогам прошлых'
                                                               ' переговоров, какому шагу Вы уделите больше внимания?',
                                  self.create_inline_markup(
                                      ['Шаг {0}. {1}'.format(i, j) for i, j in zip([k for k in range(1, 8)],
                                                                                   labels)],
                                      ['step_{0}'.format(i) for i in range(1, 8)]))

        elif callback.data == 'change_goals':
            self.edit_message(callback.message.message_id, 'Вы решили изменить Цели')
            self.goals.clear()
            self.conv_score = 0
            self.set_goals()

        elif callback.data == 'start_nego_test_style':
            if self.state() == 'MAIN_MENU':
                disc = "Опросник состоит из 30 вопросов, ответы на них обычно занимают до 7 минут.\nДля повышения " \
                       "достоверности и полезности теста вспоминайте, пожалуйста, реальные ситуации и переговоры.\n\n" \
                       "После ответа на все вопросы вы узнаете какой стиль вы демонстрируете в переговорах."
                self.edit_message(callback.message.message_id,
                                  '<b>Тест на определение переговорного стиля начался!</b>\n\n',
                                  None, parse_mode='html')
                self.send_message(disc, parse_mode='html')
                self.change_state('IN_NEGO_TEST')
                self.start_test_style()
            else:
                self.send_message('Простите, но проходить данный тест можно только после завершения переговоров!')

        elif callback.data in ['never', 'rare', 'often', 'always']:
            if callback.data == 'never':
                self.res_test[self.metadata[0]] += 0
                self.edit_message(callback.message.message_id, callback.message.text + '\n✓никогда', None)
            elif callback.data == 'rare':
                self.res_test[self.metadata[0]] += 1
                self.edit_message(callback.message.message_id, callback.message.text + '\n✓редко', None)
            elif callback.data == 'often':
                self.res_test[self.metadata[0]] += 2
                self.edit_message(callback.message.message_id, callback.message.text + '\n✓часто', None)
            elif callback.data == 'always':
                self.res_test[self.metadata[0]] += 3
                self.edit_message(callback.message.message_id, callback.message.text + '\n✓всегда', None)
            self.metadata.clear()
            self.start_test_style()

        elif callback.data == 'send_goals':
            print(callback.message.text)
            tmp = '\n'.join(callback.message.text.split('\n')[1:len(callback.message.text.split('\n'))])
            if self.case == 'case2':
                res12 = list(map(lambda i: i.split(':'), callback.message.text.split('\n')[1:6]))
                lbl = [i[0] for i in res12]
                lbl.pop(2)
                res12.pop(1)
                tmp12 = res12.pop(1)[0]
                res12.insert(1, [' ', tmp12])
                print(res12)
                goals = [i[1] for i in res12]
            else:
                goals = [i.split(':')[1] for i in
                         callback.message.text.split('\n')[1:len(callback.message.text.split('\n'))]]
                lbl = [i.split(':')[0] for i in
                       callback.message.text.split('\n')[1:len(callback.message.text.split('\n'))]]
                print(goals)
                print(lbl)
                if self.case == 'case1':
                    goals = list(map(lambda i: str(i) + ' %', goals))
            text = '<b>{0}:</b> {4}\n<b>{1}:</b> {5}\n<b>{2}:</b> {6}\n<b>{3}:</b> {7}\n' \
                   ''.format(*lbl, *goals)
            if self.case == 'case1':
                tmp = list(map(lambda i: i[:-2:] + '%\n', tmp))
            self.send_message_to_vizavi(text, self.create_inline_markup(['Согласен👍', 'Не согласен👎'], ['v_accept',
                                                                                                          'v_decline']),
                                        parse_mode='html')
            self.edit_message(callback.message.message_id,
                              f'<b>Вы отправили на согласование договоренности</b>\n\n{text}\n\nЕсли Ваш визави принимает'
                              f' данное соглашение, чат будет закрыт и Вы получите результаты переговоров. В случае'
                              f' его отказа, Вам будет необходимо продолжить переговоры.', None, parse_mode='html')

        elif callback.data == 'profile':
            profile_markup = types.InlineKeyboardMarkup(row_width=1)
            profile_markup.add(types.InlineKeyboardButton(text='Результаты тестов', callback_data='details_stat'))
            number_of_users = len(self.ctrl.query_any_rows(table_name='users', col_name='user_name',
                                                           cond_value="'" + self.group_code() + "'", cond='group_code'))
            msg = '<b>Личный кабинет {0}</b>\nЛичный id {1}\n\n1⃣<b>Рейтинг эффективности переговорщика</b>\n' \
                  '🔸Место в рейтинге: {2} / {7}\n🔹Баллы: {3}\n\n2⃣<b>Рейтинг социальной активности</b>\n🔸Место в' \
                  ' рейтинге: {4} / {7}\n🔹Баллы: {5}\n\n<b>3⃣Проведено переговоров {6}</b>'.format(self.name(),
                                                                                                    self.id,
                                                                                                    self.get_current_pos_in_rate(),
                                                                                                    int(self.__score),
                                                                                                    self.get_current_pos_in_social_rate(),
                                                                                                    int(
                                                                                                        self.social_score),
                                                                                                    int(self.case[
                                                                                                            4]) - 1,
                                                                                                    number_of_users)
            self.send_message(msg, parse_mode='html', markup=profile_markup)

        elif callback.data == 'stay':
            self.edit_message(callback.message.message_id, 'Вы можете продолжить переговоры', None)

        elif callback.data == 'details_stat':
            detail_stat_markup = self.create_inline_markup(('Входной тест', 'Опросник "Переговорные стили"'),
                                                           ('start_test_stat', 'test_style_stat'))
            self.send_message('Что вы хотите посмотреть?', markup=detail_stat_markup, parse_mode='html')

        elif callback.data == 'start_test_stat':
            tmp_start_test_res = '🔸<b>Результаты входного теста:</b>\n'
            start_test_res = (self.ctrl.query_any_rows('user_id', self.id, 'start_test_res', '*')[0])
            tmp_start_test_res += 'Ответы на вопросы:\n' + ', '.join(start_test_res[1:-1])

            tmp_start_test_res += f'\nРезультат в баллах: {start_test_res[-1]} ' \
                                  f'({int(int(start_test_res[-1]) / 46 * 100)}%)'
            self.send_message(tmp_start_test_res, parse_mode='html')

        elif callback.data == 'test_style_stat':
            tmp_style_test_res = '\n\n🔸<b>Результаты теста на переговорные стили:</b>\n'
            try:
                style_test_res = (self.ctrl.query_any_rows('user_id', self.id, 'style_test_result', '*')[0])
                tmp_style_test_res += 'Жесткий стиль: {0}\nМягкий стиль: {1}\nПартнерский стиль: {2}' \
                                      ''.format(*style_test_res[1:])
            except IndexError:
                tmp_style_test_res += 'Еще не прошли тест!'
            self.send_message(tmp_style_test_res, parse_mode='html')

        elif callback.data == 'conversation1_stat':
            pass

        elif callback.data == 'leave':
            if self.case == 'case3':
                self.edit_message(callback.message.message_id, 'Мне очень жаль, что Вы решили покинуть переговоры. '
                                                               'Но это еще не конец. На следующей неделе будут '
                                                               'опубликованы рейтинги эффективности и социальной '
                                                               'активности участников')
            else:
                self.edit_message(callback.message.message_id, 'Мне очень жаль, что Вы решили покинуть переговоры. '
                                                                'Следующие переговоры начнутся в понедельник и я'
                                                               ' надеюсь, что у вас получится договориться с визави ;)',
                                  None)
            self.remove_social_score(50)
            self.change_state('MAIN_MENU')
            self.terminate_nego()

        elif callback.data == 'v_accept':
            self.edit_message(callback.message.message_id, callback.message.text, None)
            print(callback.message.text)
            vizavi = self.subscribers[0].users()[self.vizavi[0]]
            self.conv_score = 0
            if self.case == 'case1':
                self.goals = vizavi.goals
                print(self.goals)
                print(self.case_role[0])
                tmp = {'rus': ((10, 20, 30, 40), (40, 40, 50, 60)),
                       'china': ((40, 30, 20, 10), (30, 30, 40, 50))}
                low = 20
                self.conv_score += self.get_first_case_score(self.goals, self.case_role[0], tmp, low)
                print(self.conv_score)
                if len(vizavi.goals) != 4:
                    vizavi.goals = self.goals
                    vizavi.conv_score += self.get_first_case_score(self.goals, vizavi.case_role[0], tmp, low)
            elif self.case == 'case2':
                self.goals.clear()
                res12 = vizavi.goals
                self.goals = res12
                print(self.goals)
                if self.case_role[0] == 'atom':
                    name_score = 0
                    if len(re.findall(r'Atom', res12[3])) > 0 and self.case_role[0] == 'atom':
                        name_score += 5
                    self.conv_score = int(50 * (41.75 - float(res12[0])) / 12) + self.get_precent_scores(
                        self.case_role[0], int(res12[2])) + name_score + self.get_pos_scores(self.case_role[0],
                                                                                                     res12[1])
                    if len(vizavi.goals) != 4:
                        vizavi.goals = self.goals
                        vizavi.conv_score += int(round(70 * ((float(res12[0]) - 31.75) / 12))) + self.get_precent_scores(
                        self.case_role[0], int(res12[2])) + self.get_pos_scores(self.case_role[0], res12[1])
                elif self.case_role[0] == 'star':
                    self.conv_score += int(round(70 * ((float(res12[0]) - 31.75) / 12))) + self.get_precent_scores(
                        self.case_role[0], int(res12[2])) + self.get_pos_scores(self.case_role[0], res12[1])

                    if len(vizavi.goals) != 4:
                        vizavi.goals = self.goals
                        vizavi.conv_score = int(round(70 * ((float(res12[0]) - 31.75) / 12))) + self.get_precent_scores(
                        self.case_role[0], int(res12[2])) + self.get_pos_scores(self.case_role[0], res12[1])
                    print(self.conv_score)

            elif self.case == 'case3':
                self.goals.clear()
                res = vizavi.goals
                self.goals = res
                print(res)
                tmp = self.case_role[0]
                self.conv_score += self.get_place_scores_case3(tmp,
                                                               res[0]) + self.get_time_scores_case3(tmp,
                                                                                                    res[1])
                print(self.conv_score)
                self.conv_score += self.get_precent_scores_case3(tmp,
                                                                 int(res[2])) + self.get_days_scores_case3(tmp, int(res[3]))
                print(self.conv_score)
            print('{0} score = {1}'.format(self.id, self.conv_score))
            print('here 3')
            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(*[types.InlineKeyboardButton(i, callback_data=j) for i, j in
                         zip(('Да', 'Нет'), ('r_v_accept', 'v_decline'))])
            self.send_message('Вы действительно согласны на эти условия?',
                              markup)

        elif callback.data == 'r_v_accept':
            self.edit_message(callback.message.message_id, 'Вы приняли данные условия!', None)
            self.subscribers[0].end_nego((self.id, self.vizavi[0]), self.group_code(), self.case)

        elif callback.data == 'v_decline':
            self.subscribers[0].users()[self.vizavi[0]].change_state(f'IN_CONVERSATION_{self.case.upper()}')
            self.edit_message(callback.message.message_id, '<b>Вы не приняли данные условия.</b>', None,
                              parse_mode='html')
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add('Договорились👍', 'Покинуть переговоры!❌')
            self.send_message('Когда Вы обсудите разногласия с визави, нажмите кнопку "Договорились", которая появится '
                              'в нижнем меню и введите новое соглашение.', markup=markup)
            self.bot.send_message(self.vizavi[0], 'Визави не согласен с введенными Вами договоренностями.\n'
                                                  'Вы можете продолжить переговоры в чате')

        elif callback.data == 'change_final_goals':
            self.conv_score = 0
            self.edit_message(callback.message.message_id, 'Вы решили изменить договоренности')
            self.goals.clear()
            self.set_final_goals()

        elif callback.data == 'compare':
            start_date = self.ctrl.query_any_rows('{0}_side'.format(self.case_role[0]), self.id,
                                                  'conversation{}'.format(self.case[4]), ','.join(('begin_date', 'id')))
            print(self.case_role[0])
            tmp = self.ctrl.query_any_rows(table_name=f'conversation{self.case[4]}_goals_{self.case_role[0]}',
                                           col_name='goals', cond_value=start_date[0][1], cond='conversation_id')
            print(start_date)
            print(tmp)
            print(tmp[0][0].split(','))
            if int(self.case[4]) == 1:
                tmp1 = tmp[0][0].split(',')
                tmp = tmp1
                text = f'<b>Сравнение ЦЕЛЬ/ФАКТ</b>\nСлева поставленные цели по ЦОД в %, а справа фактическая ' \
                       f'договоренность:\n\nЦОД1: {tmp[0]}/{self.goals[0]}\nЦОД2: {tmp[1]}/{self.goals[1]}\n' \
                       f'ЦОД3: {tmp[2]}/{self.goals[2]}\nЦОД4: {tmp[3]}/{self.goals[3]}\n\nПредлагаю оценить Вашу ' \
                       f'удовлетворенность проведенными переговорами по 10-балльной шкале.'
            elif int(self.case[4]) == 2:
                tmp = tmp[0][0].split(',')
                text = f'<b>Сравнение ЦЕЛЬ/ФАКТ</b>\n\n<b>Ваша цель на переговоры:</b>\nЦена в млн.р: <b>{tmp[0]}\n</b>' \
                       f'Должность г-на Старче в компании и срок:\n<b>{tmp[1]}</b>\n' \
                       f'Сокращение персонала: <b>{tmp[2]}</b>\nНазвание компании: <b>{tmp[3]}</b>\n\n<b>Фактические ' \
                       f'договоренности:</b>\nЦена в млн.р: <b>{self.goals[0]}</b>\nДолжность г-на Старче в компании' \
                       f' и срок:\n<b>{self.goals[1]}</b>\nСокращение персонала: <b>{self.goals[2]}</b>\nНазвание' \
                       f' компании: <b>{self.goals[3]}</b>\n\n<b>Оцените насколько вы довольны проведенными переговорами' \
                       f' по 10-балльной шкале.</b> Где 10 баллов - результат переговоров выше ожиданий, 1 балл - вы не ' \
                       f'добились ничего из того, на что рассчитывали.'
            elif int(self.case[4]) == 3:
                tmp = tmp[0][0].split(',')
                text = f'<b>Сравнение ЦЕЛЬ/ФАКТ</b>\n\n<b>Ваша цель на переговоры:</b>\nМесто хранения: <b>{tmp[0]}\n</b>' \
                       f'Cроки переезда: <b>{tmp[1]}</b>\n' \
                       f'Процент повышения тарифов, % : <b>{tmp[2]}</b>\nОтсрочка платежа: <b>{tmp[3]}</b>\n\n<b>Фактические ' \
                       f'договоренности:</b>\nМесто хранения: <b>{self.goals[0]}</b>\nCроки переезда:' \
                       f' <b>{self.goals[1]}</b>\nПроцент повышения тарифов, % : <b>{self.goals[2]}</b>\nОтсрочка платежа:' \
                       f' <b>{self.goals[3]}</b>\n\n'
            self.edit_message(callback.message.message_id, callback.message.text, markup=None, parse_mode='html')
            self.send_message(text, markup=None, parse_mode='html')
            self.personal_assesment()

        elif callback.data in [str(i) for i in range(1, 11)]:
            self.change_state('END_NEGO')
            txt = f'\nВаша оценка: {callback.data}\nСпасибо что оценили обратную связь!\n'
            self.edit_message(callback.message.message_id, callback.message.text + txt, None, parse_mode='html')
            self.ctrl.custom_query(f'UPDATE feedback_conversation SET scores = {int(callback.data)} WHERE'
                                   f' user_id = {self.id} AND vizavi_id = {self.vizavi[0]}')
            self.send_message(
                'Ниже показаны баллы, полученные в прошедших переговорах. Общие рейтинговые баллы Вы найдёте в '
                'личном кабинете участника,который становится доступен после выполнения всех заданий этой недели.\n\n'
                '<b>Итоги переговоров:</b>\n<i>Рейтинг эффективности переговорщика:</i> <b>{0}</b>\n<i>Рейтинг социальной активности:</i>'
                ' <b>{1}</b>\n\n<b>Вы сможете начать новые переговоры в понедельник</b>'.format(
                    int(self.__score),
                    int(self.social_score)), parse_mode='html')
            self.prepare_to_next_case()
            self.send_message('Получить дополнительные материалы по\nлюбому из шагов переговорного процесса:',
                              self.create_inline_markup(['Якорю', 'Убеждаю', 'Структурирую', 'Изучаю', 'Предлагаю',
                                                         'Торгуюсь', 'Закрываю', 'Материалы по всем шагам',
                                                         'Материалы не нужны'],
                                                        ['ref1', 'ref2', 'ref3', 'ref4', 'ref5', 'ref6', 'ref7', 'ref8',
                                                         'skip_ref']))
            if self.case == 'case2':
                try:
                    times = self.container[0] - datetime.datetime.now()
                    text = f'Вот и завершились первые переговоры!\n\nТеперь Вы можете <b>пройти опросник на определение Вашего' \
                           f' переговорного стиля</b> и почитать на досуге полезные материалы, которые мы для Вас подготовили.' \
                           f'\n\n<b>Следующие переговоры будут доступны в понедельник, через {times.days} дней' \
                           f' {times.seconds // 3600} часов {times.seconds % 3600 // 60} минут</b>'
                    if self.done_test_style:
                        markup = self.create_inline_markup(['Личный кабинет'], ['profile'])
                    else:
                        markup = self.create_inline_markup(['Опросник "Переговорные стили"', 'Личный кабинет'],
                                                           ['start_nego_test_style', 'profile'])
                except IndexError:
                    text = f'Вот и завершились первые переговоры!\n\nТеперь Вы можете пройти опросник на определение Вашего' \
                           f' переговорного стиля и почитать на досуге полезные материалы, которые мы для Вас подготовили.'
                    markup = self.create_inline_markup(['Опросник "Переговорные стили"', 'Личный кабинет'],
                                                       ['start_nego_test_style', 'profile'])

                self.welcome_message(markup, external_text=text)

            elif self.case == 'case3':
                if self.done_test_style:
                    markup = self.create_inline_markup(['Личный кабинет'], ['profile'])
                else:
                    markup = self.create_inline_markup(['Опросник "Переговорные стили"',
                                                        'Личный кабинет'],
                                                       ['start_nego_test_style', 'profile'])
                try:
                    times = self.container[0] - datetime.datetime.now()
                    print(self.container)
                    print(times)
                    text = f'Вот и завершились вторые переговоры!\n\nТеперь Вы снова можете пройти опросник на определение Вашего' \
                           f' переговорного стиля, если еще этого не сделали и почитать на досуге полезные материалы, которые мы для Вас подготовили.' \
                           f'\n\n<b>Следующие переговоры будут доступны в понедельник, через {times.days} дней' \
                           f' {times.seconds // 3600} часов {times.seconds % 3600 // 60} минут</b>'
                    self.welcome_message(markup, external_text=text)
                except IndexError:
                    text = f'Вот и завершились вторые переговоры!\n\nТеперь Вы можете пройти опросник на определение Вашего' \
                           f' переговорного стиля и почитать на досуге полезные материалы, которые мы для Вас подготовили.'
                    self.welcome_message(markup, external_text=text)

            elif self.case == 'case4':
                if self.done_test_style:
                    markup = self.create_inline_markup(['Личный кабинет'], ['profile'])
                else:
                    markup = self.create_inline_markup(['Опросник "Переговорные стили"', 'Личный кабинет'],
                                                       ['start_nego_test_style', 'profile'])
                msg = f'<b>Приятно снова Вас видеть, {self.name()}!\n\n</b>\nВы завершили последние переговоры, а это значит, что' \
                      f' на следующей неделе мы опубликуем рейтинги эффективности переговорщика и рейтинг социальной' \
                      f' активности.\n\nПрактикуйте все полученные навыки и в реальной жизни и никогда не ' \
                      f'останавливайтесь на достигнутом!\nДо встречи :)'
                self.welcome_message(markup, external_text=msg, greetings_on=False)


        elif callback.data in ['ref1', 'ref2', 'ref3', 'ref4', 'ref5', 'ref6', 'ref7', 'ref8']:
            references = {'ref1': 'https://teletype.in/@sellwell/_dNI5s_V',
                          'ref2': 'https://teletype.in/@sellwell/xVlal4EJ',
                          'ref3': 'https://teletype.in/@sellwell/jf5gzyHA',
                          'ref4': 'https://teletype.in/@sellwell/3BPELuDq',
                          'ref5': 'https://teletype.in/@sellwell/w1etIKEw',
                          'ref6': 'https://teletype.in/@sellwell/3CCbDcJr',
                          'ref7': 'https://teletype.in/@sellwell/LYIDXw5x',
                          'ref8': 'https://teletype.in/@sellwell/VQxQHQFo'}
            labels = ['Якорю', 'Убеждаю', 'Структурирую', 'Изучаю', 'Предлагаю', 'Торгуюсь', 'Закрываю',
                      'Материалы по всем шагам', 'Материалы не нужны']
            text = 'Вы выбрали шаг "{0}. {1}"'.format(callback.data[3], labels[int(callback.data[3]) - 1])
            labels[int(callback.data[3]) - 1] = '✅' + labels[int(callback.data[3]) - 1]
            self.edit_message(callback.message.message_id, text,
                              self.create_inline_markup(labels, ['ref1', 'ref2', 'ref3', 'ref4', 'ref5', 'ref6', 'ref7',
                                                                 'ref8', 'skip_ref']))
            self.send_message(references[callback.data])

        elif callback.data == 'skip_ref':
            references = {'ref1': 'https://teletype.in/@sellwell/_dNI5s_V',
                          'ref2': 'https://teletype.in/@sellwell/xVlal4EJ',
                          'ref3': 'https://teletype.in/@sellwell/jf5gzyHA',
                          'ref4': 'https://teletype.in/@sellwell/3BPELuDq',
                          'ref5': 'https://teletype.in/@sellwell/w1etIKEw',
                          'ref6': 'https://teletype.in/@sellwell/3CCbDcJr',
                          'ref7': 'https://teletype.in/@sellwell/LYIDXw5x',
                          'ref8': 'https://teletype.in/@sellwell/VQxQHQFo'}
            labels = ['Якорю', 'Убеждаю', 'Структурирую', 'Изучаю', 'Предлагаю', 'Торгуюсь', 'Закрываю',
                      'Материалы по всем шагам', 'Материалы не нужны']
            text = 'Вы решили что материалы не нужны'
            labels[8] = '✅' + labels[8]
            self.edit_message(callback.message.message_id, text,
                              self.create_inline_markup(labels, ['ref1', 'ref2', 'ref3', 'ref4', 'ref5', 'ref6', 'ref7',
                                                                 'ref8', 'skip_ref']))


        elif callback.data in ['pa_{0}'.format(j) for j in range(1, 11)]:
            self.edit_message(callback.message.message_id, 'Вы поставили оценку {}'
                                                           ''.format(callback.data[3::]), None)
            self.metadata.append(int(callback.data[3::]))
            self.send_message('Напишите ответ на вопрос (в одном сообщении):\n<b>Что сработало из запланированного во '
                              'время подготовки?</b>\n\nНапример:\n<i>Я вовремя выяснил у визави его диапазоны и '
                              'истинные приоритеты. Мне это очень помогло на шаге "ТОРГУЮСЬ". Также у меня получилось'
                              ' использовать эмоциональный аргумент "все так делают", и понизить НАОС визави.</i>'
                              '', markup=types.ReplyKeyboardRemove(), parse_mode='html')
            self.bot.register_next_step_handler(callback.message, self.pa_func_one)

        elif callback.data in ['25%', '24%', '20%', '15%', '0%']:
            tmp1 = ['25%', '21-24%', '16-20%', '1-15%', '0%']
            tmp2 = ['25%', '24%', '20%', '15%', '0%']
            self.edit_message(callback.message.message_id, f'Вы выбрали {tmp1[tmp2.index(callback.data)]}', None)
            self.goals.append(int(callback.data[:-1:]))
            self.conv_score += self.get_precent_scores(self.case_role[0], int(callback.data[:-1:]))
            self.send_message('Название компании после покупки:', self.create_inline_markup(['"Atom-Kuznets" с '
                                                                                             'первого же дня',
                                                                                             'Другое название'],
                                                                                            ['Atom', 'another']))

        elif callback.data in ['kick', 'without_rights', '1_year', '3_years', '5_years']:
            tmp = {'kick': 'Немедленный уход (без должности)', 'without_rights': 'Президент на 3 года (без права '
                                                                                 'принятия решений',
                   '1_year': 'Генеральный директор на 1 год',
                   '3_years': 'Генеральный директор на 3 года',
                   '5_years': 'Генеральный директор на 5 лет'}
            self.conv_score += self.get_pos_scores(self.case_role[0], tmp[callback.data])
            print(self.conv_score)
            self.goals.append(tmp[callback.data])
            self.edit_message(callback.message.message_id, 'Вы выбрали {0}'.format(tmp[callback.data]), None)
            self.send_message('<b>Договоренность с профсоюзами о сокращении персонала, %</b>',
                              markup=self.create_inline_markup(['25%', '21-24%', '16-20%', '1-15%', '0%'],
                                                               ['25%', '24%', '20%', '15%', '0%']),
                              parse_mode='html')

        elif callback.data in ['Atom', 'another']:
            tmp = {'Atom': 'Atom-Kuznets', 'another': 'Другое название'}
            if callback.data == 'Atom' and self.case_role[0] == 'atom':
                self.conv_score += 5
            print(self.conv_score)
            self.goals.append(tmp[callback.data])
            self.edit_message(callback.message.message_id, 'Вы выбрали {0}'.format(tmp[callback.data]), None)
            print(self.state())
            if self.state() == 'WAITING_4_ACCEPT':
                self.send_goals_to_vizavi()
            else:
                self.validate_goals()

        elif callback.data in ['step_{0}'.format(i) for i in range(1, 8)]:
            tmp = {'step_1': 'Якорю', 'step_2': 'Убеждаю', 'step_3': 'Структурирую',
                   'step_4': 'Изучаю', 'step_5': 'Предлагаю', 'step_6': 'Торгуюсь', 'step_7': 'Закрываю'}
            self.edit_message(callback.message.message_id,
                              'Спасибо. Вы выбрали шаг {0}. {1}'.format(callback.data[5], tmp[callback.data]), None)
            self.goals.append(callback.data)
            self.send_message('<b>Что конкретно вы будете делать?</b>\n\nОпишите действия, которые Вы собираетесь '
                              'предпринять для достижения результатов.\n\nНапример:\n<i>В этот раз я больше внимания '
                              'буду уделять техничному завершению переговоров, а именно,  резюмированию и назначению '
                              'цены за согласие.</i>', parse_mode='html')
            self.bot.register_next_step_handler(callback.message, self.set_final_goals_case2)

        elif callback.data in ['vnuk', 'obn']:
            tmp = {'vnuk': 'Внуково', 'obn': 'Обнинск'}
            print(self.case_role[0])
            self.conv_score += self.get_place_scores_case3(self.case_role[0], tmp[callback.data])
            print(self.conv_score)
            self.goals.append(tmp[callback.data])
            self.edit_message(callback.message.message_id, 'Вы выбрали {0}'.format(tmp[callback.data]), None)
            self.send_message('Срок переезда', self.create_inline_markup(['23-31 марта', '1-30 апреля',
                                                                          '1-9 мая'], ['date1', 'date2', 'date3']))

        elif callback.data in ['date1', 'date2', 'date3']:
            tmp = {'date1': '23-31 марта', 'date2': '1-30 апреля', 'date3': '1-9 мая'}
            self.conv_score += self.get_time_scores_case3(self.case_role[0], tmp[callback.data])
            print(self.conv_score)
            self.goals.append(tmp[callback.data])
            self.edit_message(callback.message.message_id, 'Вы выбрали {0}'.format(tmp[callback.data]), None)
            self.send_message('<b>Процент повышения тарифов, %</b>',
                              markup=self.create_inline_markup(['9-12%', '5-8%', '1-4%', '0%'],
                                                               ['c312', 'c38', 'c34', 'c30']),
                              parse_mode='html')

        elif callback.data in ['c312', 'c38', 'c34', 'c30']:
            tmp = ['9-12%', '5-8%', '1-4%', '0%']
            tmp1 = ['c312', 'c38', 'c34', 'c30']
            self.edit_message(callback.message.message_id, f'Вы выбрали {tmp[tmp1.index(callback.data)]}', None)
            self.conv_score += self.get_precent_scores_case3(self.case_role[0], int(callback.data[2::]))
            self.goals.append(callback.data[2::])
            self.send_message('Отсрочка платежа', self.create_inline_markup(['30 дней', '60 дней', '90 дней',
                                                                             '120 дней'],
                                                                            ['30_days', '60_days', '90_days',
                                                                             '120_days']))

        elif callback.data in ['30_days', '60_days', '90_days', '120_days']:
            self.conv_score += self.get_days_scores_case3(self.case_role[0], int(callback.data[0:-5:]))
            print(self.conv_score)
            self.edit_message(callback.message.message_id, 'Вы выбрали {0} дней'.format(int(callback.data[0:-5:])),
                              None)
            self.goals.append(int(int(callback.data[0:-5:])))
            if self.state() == 'WAITING_4_ACCEPT':
                self.send_goals_to_vizavi()
            else:
                self.validate_goals()

        elif callback.data in [f'NPS_{i}' for i in range(11)]:
            score = int(callback.data.split('_')[1])
            self.edit_message(callback.message.message_id, f'Вы поставили {score} баллов', None)
            self.ctrl.update_data(table_name='NPS_data', cond='user_id', cond_value=self.id,
                                  col_name=f'{self.case}_score', new_value=score)
            self.p2p_assesment()

    def set_final_goals_case2(self, message):
        tmp = self.ctrl.query_any_rows(table_name='conversation{0}'.format(self.case[4]), col_name='id',
                                       cond='{0}_side'.format(self.case_role[0]),
                                       cond_value=self.id)[0]
        self.ctrl.add_record(table_name='conversation{0}_goals_{1}'.format(self.case[4], self.case_role[0]),
                             col_names=('conversation_id', 'goals', 'step', 'action'), col_values=(tmp[0],
                                                                                                   ','.join(tuple(map(
                                                                                                       lambda i: str(i),
                                                                                                       self.goals[
                                                                                                       0:4]))),
                                                                                                   self.goals[4],
                                                                                                   message.text))
        self.goals.clear()
        self.send_message('Отличная работа! Этап подготовки к переговорам завершен.\n\n'
                          'Как только Ваш визави завершит подготовку и будет готов начать переговоры\nВы оба получите '
                          'уведомление в чате')
        self.change_state('READY_TO_CONV'.format(self.case.upper()))
        self.start_nego_alert()

    @staticmethod
    def get_first_case_score(goals, side, side_map, low):
        if side == 'rus':
            return int(sum(
                [side_map[side][0][i] * (goals[i] - low) / (side_map[side][1][i] - low) for i in range(0, len(goals))]))
        elif side == 'china':
            return int(sum(
                [side_map[side][0][i] * (side_map[side][1][i] - goals[i]) / (side_map[side][1][i] - low) for i in
                 range(0, len(goals))]))

    @staticmethod
    def get_precent_scores(side, temp):
        data = {'star': (10, 5, 3, 0, 0),
                'atom': (0, 10, 20, 30, 35)}
        return {
            temp == 0: data[side][0],
            1 <= temp <= 15: data[side][1],
            15 <= temp <= 20: data[side][2],
            21 <= temp <= 24: data[side][3],
            25 == temp: data[side][4]
        }[True]

    @staticmethod
    def get_pos_scores(side, temp):
        data = {'star': (0, 3, 10, 18, 20),
                'atom': (10, 8, 5, 0, 0)}
        print(temp)
        return {
            temp == 'Немедленный уход (без должности)': data[side][0],
            temp == 'Президент на 3 года (без права принятия решений': data[side][1],
            temp == 'Генеральный директор на 1 год': data[side][2],
            temp == 'Генеральный директор на 3 года': data[side][3],
            temp == 'Генеральный директор на 5 лет': data[side][4]
        }[True]

    @staticmethod
    def get_precent_scores_case3(side, temp):
        print(side)
        data = {'orion': (1, 5, 25, 50),
                'dental_star': (15, 10, 3, 1)}
        return {
            temp <= 0: data[side][0],
            1 <= temp <= 4: data[side][1],
            5 <= temp <= 8: data[side][2],
            9 <= temp <= 12: data[side][3],
        }[True]

    @staticmethod
    def get_days_scores_case3(side, temp):
        data = {'orion': (25, 10, 5, 1),
                'dental_star': (1, 4, 6, 10)}
        return {
            temp == 30: data[side][0],
            temp == 60: data[side][1],
            temp == 90: data[side][2],
            temp == 120: data[side][3],
        }[True]

    @staticmethod
    def get_time_scores_case3(side, temp):
        data = {'orion': (10, 5, 1),
                'dental_star': (1, 15, 50)}
        print(temp)
        return {
            temp == '23-31 марта': data[side][0],
            temp == '1-30 апреля': data[side][1],
            temp == '1-9 мая': data[side][2]
        }[True]

    @staticmethod
    def get_place_scores_case3(side, temp):
        data = {'orion': (1, 15),
                'dental_star': (25, 5)}
        print(temp)
        return {
            temp == 'Внуково': data[side][0],
            temp == 'Обнинск': data[side][1],
        }[True]

    def set_third_goals_case2(self, message):
        try:
            res = int(message.text)
            if 0 <= res <= 25:
                self.goals.append(res)
                self.conv_score += self.get_precent_scores(self.case_role[0], int(message.text))
                print(self.conv_score)
                self.send_message('Название компании после покупки:', self.create_inline_markup(['"Atom-Kuznets" с '
                                                                                                 'первого же дня',
                                                                                                 'Другое название'],
                                                                                                ['Atom', 'another']))
            else:
                self.send_message('Ваши договоренности должны быть в диапазоне 0-25%')
                self.bot.register_next_step_handler(message, self.set_third_goals_case2)
        except ValueError:
            self.send_message('Укажите Вашу цель по договоренности с профсоюзами в % <b>целым числом без пробелов</b> '
                              '<i>(знак % вводить не нужно</i>', parse_mode='html')
            self.bot.register_next_step_handler(message, self.set_third_goals_case2)

    def pa_func_one(self, message):
        self.metadata.append(message.text)
        self.send_message('Напишите ответ на вопрос (в одном сообщении):\n<b>Что не сработало и Вы будете делать '
                          'по-другому?</b>\n\nНапример:\n<i>На этапе подготовки я'
                          ' невнимательно прочитал кейс и из-за этого чуть не согласился на неприемлемые условия. Также'
                          ' я мог бы заякорить атмосферу на самых первых этапах. Это помогло бы настроиться на '
                          'позитивную волну и снять лишнее напряжение. Тогда мы бы договорились гораздо быстрее.</i>',
                          parse_mode='html')
        self.bot.register_next_step_handler(message, self.pa_func_two)

    def pa_func_two(self, message):
        self.metadata.append(message.text)
        self.ctrl.add_record(table_name='personal_assesment_conv1', col_names=('user_id','score', 'res', 'freq'),
                             col_values=(self.id, *self.metadata))
        self.add_social_score(10)
        self.p2p_assesment()

    def prepare_to_next_case(self):
        self.change_case(self.case[0:4] + (str(int(self.case[4]) + 1)))
        if int(self.case[4]) - self.trend[2] > 1:
            self.change_case(self.case[0:4] + (str(int(self.case[4]) - 1)))
        print('{0} case = {1}'.format(self.id, self.case))
        self.clear_data()
        print('All clear!')
        try:
            self.push_to_group_queue()
        except IndexError:
            print('Index')

    def clear_data(self):
        self.metadata.clear()
        self.message_counter = 0
        self.conv_score = 0
        self.goals = []
        print(self.vizavi)
        self.ex_vizavis.append(self.vizavi)
        print(self.ex_vizavis)
        self.vizavi = []

    def input_good_step(self, message):
        self.ctrl.add_record(table_name='good_step_in_conv', col_names=('user_id', 'steps'),
                             col_values=(self.id, message.text))
        self.p2p_assesment()

    def input_mistakes(self, message):
        self.ctrl.add_record(table_name='mistakes_in_conv', col_names=('user_id', 'mistakes'),
                             col_values=(self.id, message.text))
        self.p2p_assesment()

    def unready_to_negotiat(self):
        self.ready_to_nego = False

    def start_test_style(self):
        self.unready_to_negotiat()
        tmp = sum(tuple(map(lambda i: len(i), tuple(self.test_style.values()))))
        if tmp > 0:
            if tmp == 20:
                self.send_message('Отличный темп! Треть теста уже пройдена 🤓')
            elif tmp == 10:
                self.send_message('Осталось всего 10 вопросов, скоро вы узнаете результаты 👍🏻')
            question = self.query_question()
            self.send_message(question, self.create_inline_markup(['никогда', 'редко', 'часто', 'всегда'],
                                                                  ['never', 'rare', 'often', 'always']))
        else:
            self.metadata = []
            print()
            self.done_test_style = True
            self.send_message(
                '<b>Ваш результат:</b>\n\nЖесткий стиль: <b>{0}</b>\nМягкий стиль: <b>{1}</b>\nПартнерский стиль: '
                '<b>{2}</b>\n'
                'https://teletype.in/@sellwell/RYi-Fe80'.format(*tuple(self.res_test.values())),
                parse_mode='html')
            self.ctrl.add_record(table_name='style_test_result', col_values=(self.id, *tuple(self.res_test.values())),
                                 col_names=('user_id', 'hard', 'soft', 'partner'))
            txt = f'<b>{self.name()}</b>, поздравляю с завершением опросника!\n\nВыявив свой преобладающий ' \
                  f'переговорный стиль и ознакомившись со всеми остальными, вы сможете не только более эффективно ' \
                  f'выстраивать стратегию переговоров, но и с лёгкостью распознавать стиль поведения визави и ' \
                  f'корректировать свои действия в моменте.\n\n'
            try:
                times = self.container[0] - datetime.datetime.now()
                txt += f'\nПереговорные комнаты откроются через:\n<b>{times.days} дней {times.seconds // 3600} часов' \
                      f' {times.seconds % 3600 // 60} минут</b>'
            except IndexError:
                txt += ''
            self.welcome_message(self.create_inline_markup(['Личный кабинет'], ['profile']), external_text=txt).q
            self.ready_to_negotiat()
            self.unlocked_case()

    def query_question(self):
        print('IM` calling')
        styles = list(self.test_style.keys())
        case = styles[random.randint(0, (len(styles) - 1))]
        numbs = len(self.test_style[case])
        print(self.test_style[case])
        self.metadata.append(case)
        if numbs > 0:
            tmp = random.choice(self.test_style[case])
            self.test_style[case].pop(self.test_style[case].index(tmp))
            return tmp
        else:
            self.test_style.pop(case)
            return self.query_question()

    def terminate_nego(self):
        self.ctrl.update_data(table_name=f'conversation{self.case[4]}', col_name='is_finished', new_value=f'"{True}"',
                              cond=f'{self.case_role[0]}_side', cond_value=self.id)
        self.container.clear()
        self.bot.send_message(self.vizavi[0], 'Визави решил покинуть переговоры...')
        self.clear_data()
        self.change_case(self.case[0:4] + (str(int(self.case[4]) + 1)))
        print(self.case)
        self.subscribers[0].users()[self.ex_vizavis[int(self.case[4]) - 2][0]].clear_data()
        self.subscribers[0].users()[self.ex_vizavis[int(self.case[4]) - 2][0]].change_case(self.case)
        print(self.ex_vizavis[int(self.case[4]) - 2][0])
        self.subscribers[0].terminate_nego(self.group_code(), (self.ex_vizavis[int(self.case[4]) - 2][0], self.id),
                                           self.case)

    def send_voice(self, file_id):
        self.bot.send_voice(self.vizavi[0], file_id)

    def send_question(self, question_number):
        question = list(self.__test_ref.keys())[question_number]
        numbers = ['1', '2', '3', '4', '5', '6', '7', '8', '9']
        tmp = ''.join(['<b>{0}.</b> {1}\n'.format(i, j) for i, j in zip(numbers, self.__test_ref[question]['answers'])])
        msg = '<b>{0}.</b> {1}\n\n{2}'.format(question_number + 1, question, tmp)
        self.send_message(msg, parse_mode='html')

    def get_answer(self, message):
        self.save_last_message(message)
        try:
            answ = [int(i) for i in re.findall(r'\d+', message.text)]
            number = len(self.metadata)
            try:
                self.metadata.append(','.join([str(i) for i in answ]))
                tmp = normalize_test(self.__test_ref)
                iter_score = 0
                res = []
                if not answ:
                    raise ValueError
                for i in answ:
                    try:
                        if i > len(list(self.__test_ref.values())[number]['answers']):
                            raise ValueError
                        if i in tmp[number] and i not in res:
                            res.append(i)
                            iter_score += 1
                            print(f'res = {res}')
                        elif i in tmp[number - 1] and i in res:
                            iter_score += 0
                        else:
                            iter_score -= 1
                    except IndexError as e:
                        print(e)
                if iter_score < 0:
                    iter_score = 0
                self.test_score += iter_score
                if number < 14:
                    if number == 7:
                        self.send_message('Вот это да! Не успел я отвернуться, как вы уже прошли половину теста! '
                                          'Так держать ;)')
                    self.send_question(number + 1)
                    self.bot.register_next_step_handler(message, self.get_answer)
                else:
                    res = int(self.test_score / 46 * 100)
                    self.change_state('MAIN_MENU')
                    try:
                        self.test_timer.cancel()
                    except:
                        print('Errror')
                    self.send_message(
                        'Тестирование пройдено!\n<b>Результат: {1:d}%</b>\n(Вы набрали {0} баллов из 46)\n'
                        ''.format(self.test_score, res), parse_mode='html')
                    self.add_social_score(5 + int(res / 10))
                    self.add_score(int(res / 10))
                    self.ready_to_negotiat()
                    self.push_to_group_queue()
                    try:
                        times = self.container[0] - datetime.datetime.now()
                        self.welcome_message(external_text=f'Вы уже прошли тест на знания, повторили материал и теперь '
                                                           f'готовы сделать следующий шаг.\n\nПереговоры будут доступны '
                                                           f'через:\n{times.days} дней {times.seconds // 3600} '
                                                           f'часов {times.seconds % 3600 // 60}'
                                                           f' минут\n\nПожалуйста, включите уведомления чата, чтобы вовремя'
                                                           f' начать переговоры.')
                    except IndexError:
                        self.welcome_message(external_text='Вы уже прошли тест на знания, повторили материал и теперь '
                                                           'готовы сделать следующий шаг.\n\nПожалуйста, включите '
                                                           'уведомления чата, чтобы вовремя начать переговоры.')
                    self.ctrl.add_record(table_name='start_test_res',
                                         col_values=(self.id, self.test_score,
                                                     *tuple(map(lambda i: int(i),
                                                                tuple(map(lambda j: ''.join(j),
                                                                          tuple(map(lambda k: k.split(','),
                                                                                    self.metadata))))))),
                                         col_names=('user_id', 'results', *['answer' + str(i) for i in range(1, 16)]))
                    self.metadata.clear()
            except ValueError as e:
                self.send_message('Простите, я не могу понять Ваш ответ. Попробуйте ввести его еще раз.')
                self.metadata.pop(number)
                self.bot.register_next_step_handler(message, self.get_answer)
            except AttributeError as e:
                self.metadata.pop(number)
                self.send_message('Простите, я не могу понять Ваш ответ. Попробуйте ввести его еще раз.')
                self.bot.register_next_step_handler(message, self.get_answer)
        except TypeError as e:
            self.send_message('Простите, я не могу понять Ваш ответ. Попробуйте ввести его еще раз.')
            self.bot.register_next_step_handler(message, self.get_answer)

    def get_info(self):
        return self.__dict__

    def change_state(self, new_state):
        self.__state = new_state
        self.ctrl.update_data('users', 'state', "'" + self.state() + "'", 'chat_id', self.id)

    def get_code(self, message):
        self.__group_code = message.text
        try:
            self.add_user_to_db()
            self.add_social_score(1)
            self.start_test()
        except KeyError:
            self.send_message("Неизвестный промокод. Пожалуйста введите промокод\n"
                              "<i>заглавными буквами без пробелов в одну строку</i>", parse_mode='html')
            self.bot.register_next_step_handler(message, self.get_code)

    def name(self):
        return self.__name

    def surname(self):
        return self.__surname

    def add_score(self, score):
        self.__score += score
        self.update_col_in_db('score', self.__score)

    def add_social_score(self, score):
        self.social_score += score
        self.update_col_in_db('social_score', self.social_score)

    def remove_social_score(self, score):
        self.social_score -= score
        self.update_col_in_db('social_score', self.social_score)

    def state(self):
        return self.__state

    def remove_score(self, score):
        self.__score -= score
        self.update_col_in_db('score', self.__score)

    def company(self):
        return self.__company

    def case_alert(self):
        self.send_message('Через 24 часа первое упражнение по переговорам будет доступно')
        self.timer = Timer(86400, self.unlocked_case)
        self.timer.start()

    def alert_in_case(self):
        self.send_message(
            f'<b>Спешу напомнить, что переговоры автоматически завершатся через 24 часа.</b>\n\nУ Вас еще есть '
            f'время договориться с {self.vizavi[1]}!\n\nВаш визави тоже получил уведомление, но Вы также'
            f' можете напомнить о переговорах {self.vizavi[1]} самостоятельно, если знакомы лично.',
            parse_mode='html')
        self.timer = Timer(86400, self.timeless_terminate)
        self.timer.start()

    def unlocked_case(self):
        if self.state() == 'IN_NEGO_TEST':
            self.send_message('✅Переговорные комнаты уже открылись, так что постарайтесь как можно скорее пройти тест'
                              ' и приступить к переговорам :)')

        elif self.state() not in [f'IN_CONVERSATION_{self.case.upper()}', 'SET_CASE_GOALS', 'READY_TO_CONV',
                                  'WAITING_4_ACCEPT']:
            self.send_message('Вы можете приступить к переговорам!')
            self.start_conversation(self.msg)
        timer = self.deadlines - datetime.datetime.now()
        print(f'timers {timer.days} {timer.seconds // 3600} {timer.seconds % 3600 // 60}')
        if timer.days >= 1:
            self.timer = Timer((timer.days - 1) * 86400 + timer.seconds, self.alert_in_case)
            self.timer.start()
        elif timer.days < 0:
            self.change_state('MAIN_MENU')
            self.timeless_terminate()
        else:
            self.timer = Timer(timer.seconds, self.timeless_terminate)
            self.timer.start()

    def terminate(self):
        try:
            self.delete_logger()
        except IndexError:
            pass
        self.clear_data()
        self.send_message(
            'Ниже показаны баллы, полученные в прошедших переговорах. Общие рейтинговые баллы Вы найдёте в '
            'личном кабинете участника,который становится доступен после выполнения всех заданий этой недели.\n'
            '<b>Итоги переговоров:</b>\n<i>Рейтинг эффективности переговорщика:</i> <b>{0}</b>\n<i>Рейтинг социальной активности:</i>'
            ' <b>{1}</b>\nВы сможете начать новые переговоры в понедельник'.format(
                int(self.__score - self.trend[0]),
                int(self.social_score - self.trend[
                    1])), parse_mode='html')
        self.change_case(self.case[0:4] + (str(int(self.case[4]) + 1)))
        try:
            print(f'Ex_vizavi = {self.ex_vizavis}')
            self.subscribers[0].terminate_nego(self.group_code(),
                                               (self.ex_vizavis[int(self.case[4]) - 2][0], self.id),
                                               self.case)
        except IndexError as e:
            print(f'Error: {e}')
        print('--------------------------------------------------')

    def load_conversation_data(self, data, call, rules_ref, role, date=datetime.datetime.now()):
        print(f'Call {__name__}')
        self.case_role = (role, rules_ref)
        self.vizavi = (data['id'], data['_User__name'], data['_User__surname'], data['_User__company'])
        self.trend = (self.__score, self.social_score, int(self.case[4]))
        dates = date - datetime.datetime.now()
        delts = [datetime.timedelta(seconds=0), datetime.timedelta(0, 0, 0), datetime.timedelta(0, 0, 0)]
        self.deadlines = date + datetime.timedelta(5, 3600 * 6)
        dates = dates + delts[int(self.case[4]) - 1]
        print(dates)
        if dates.days < 0:
            dates = delts[int(self.case[4]) - 1]
            self.ready_to_negotiat()
        self.container.append(date + datetime.timedelta(7))
        if self.state() in [f'IN_CONVERSATION_{self.case.upper()}', 'READY_TO_CONV',
                            'WAITING_4_ACCEPT']:
            self.unlocked_case()
        elif self.state() == 'IN_PA':
            self.personal_assesment()
        elif self.state() == 'IN_P2P':
            self.bot.register_next_step_handler(self.msg, self.p2p_func_one)
        elif self.state() == 'SET_CASE_GOALS':
            self.unlocked_case()
            if self.case == 'case1':
                self.bot.register_next_step_handler(self.msg, self.input_goal)
            elif self.case == 'case2':
                self.bot.register_next_step_handler(self.msg, self.set_first_goal_case2)

        elif self.state() == 'FINISH_NEGO':
            print('HEY')
            try:
                start_date = self.ctrl.query_any_rows(table_name=f'conversation{self.case[4]}',
                                                      cond=f'{self.case_role[0]}_side', cond_value=self.id,
                                                      col_name='id')
                print(f'query one res = {start_date}')
            except Exception as e:
                try:
                    self.change_case(f'case{int(self.case[4]) - 1}')
                    start_date = self.ctrl.query_any_rows(table_name=f'conversation{self.case[4]}',
                                                          cond=f'{self.case_role[0]}_side', cond_value=self.id,
                                                          col_name='id')
                except Exception as e:
                    print(f'error: {e}')
            print(start_date[0][0])
            print(f'conversation{self.case[4]}_result')
            goals = self.ctrl.query_any_rows(table_name=f'conversation{self.case[4]}_result', cond='id',
                                             cond_value=start_date[0][0], col_name='result')
            print(goals)
            self.goals = re.findall(r'[2-6][0-9]', goals[0][0])
            print(self.goals)
            if len(goals) != 4:
                self.goals = goals[0][0].split(',')
                if self.case == 'case3':
                    self.goals = [self.goals[0][2:-1], self.goals[1][2:-1], self.goals[2][2:-1], self.goals[3][:-1]]
                else:
                    try:
                        self.goals = [float(self.goals[0][1::]), self.goals[1][2:-1], int(self.goals[2][1:]),
                                      self.goals[3][2:-2]]
                    except ValueError as e:
                        self.goals = [float(self.goals[0][2:-1:]), self.goals[1][2:-1], int(self.goals[2][2:-1]),
                                      self.goals[3][2:-2]]
                        print(self.goals)
            else:
                self.goals = [int(i) for i in goals]
            print('FINISH_NEGO1')

        elif self.state() == 'WAITING_4_FB':
            data = self.ctrl.query_any_rows(table_name='feedback_conversation', cond='user_id', cond_value=self.id,
                                            col_name=','.join(('good', 'bad')))
            print(data)
            data.reverse()
            msg = '{0} {1} дал вам обратную связь по итогам переговоров:\n\n<b>Ваши сильные ходы:</b>\n{2}\n\n<b>Ваши ' \
                  'слабые ходы:</b>\n{3}\n\nПожалуйста оцените полезность обратной связи по 10-балльной шкале:' \
                  ''.format(self.name(), self.surname(), data[0][0], data[0][1])
            self.subscribers[0].push_data_to_hub(self.group_code(), self.vizavi[0], msg)
        elif self.ready_to_nego:
            if dates.days > 0:
                timers = (dates.days - 1) * 86400 + dates.seconds
                self.timer = Timer(timers, self.case_alert)
            elif dates.days < 0:
                self.unlocked_case()
            else:
                timers = dates.seconds
                self.timer = Timer(timers, self.unlocked_case)
            self.timer.start()
        self.save_last_message(call.message)
        print('{0} case role: {1}, cur_case {2}'.format(self.id, self.case_role, self.case))

    def check_test(self):
        print(self.state())
        if self.state() == 'BEGIN_TEST':
            self.send_message('<b>До завершения теста осталось 30 минут</b>\n\nПожалуйста, поторопитесь с прохождением'
                              ' теста, иначе вы больше не сможете к нему вернуться.', parse_mode='html')

    def timeless_terminate(self):
        try:
            self.ctrl.update_data(table_name=f'conversation{self.case[4]}', col_name='is_finished', new_value=f'"{True}"',
                                  cond=f'{self.case_role[0]}_side', cond_value=self.id)
        except:
            print('DB_Error')
        self.send_message('К сожалению, Вы не успели договориться и <b>переговоры завершились автоматически.</b>\n\n'
                          '<b>Следующий кейс будет доступен в понедельник</b>', parse_mode='html')
        try:
            self.delete_logger()
        except IndexError:
            print('error')
        if self.message_counter == 0:
            self.remove_social_score(40)
        self.send_message(
            'Ниже показаны баллы, полученные в прошедших переговорах. Общие рейтинговые баллы Вы найдёте в '
            'личном кабинете участника,который становится доступен после выполнения всех заданий этой недели.\n'
            '<b>Итоги переговоров:</b>\n<i>Рейтинг эффективности переговорщика:</i> <b>{0}</b>\n<i>Рейтинг социальной активности:</i>'
            ' <b>{1}</b>\nВы сможете начать новые переговоры в понедельник'.format(int(self.__score - self.trend[0]),
                                                                                   int(self.social_score - self.trend[
                                                                                       1])), parse_mode='html')
        self.personal_assesment()

    def start_conversation(self, msg):
        if not self.vizavi:
            self.send_message('На данный момент нет свободных участников для переговоров.\n'
                              'Как только появится возможность мы назначим Вам пару')
            self.welcome_message()
        else:
            if self.social_score == 1:
                self.remove_social_score(5)
            self.change_state('SET_CASE_GOALS')
            self.send_message(
                '<b>Ваш визави {0} {1}</b>, {2}\n\nНа переговоры (включая этапы подготовки и подведения итогов) вам'
                ' дается 6 дней.\n\nЕсли до субботы 18.00 Вы не придете к соглашению, переговоры завершатся автоматически.'
                'В таком случае каждая из сторон получит 0 баллов в рейтинг эффективности переговорщика.\n\n'
                'Прочитайте Вашу роль в этих переговорах и пройдите этап подготовки, после чего Вы сможете вступить в'
                ' диалог.\n\n<b>Внимание:</b>\nчат с визави откроется только после прохождения этапа подготовки.\n\n{3}'
                ''.format(*self.vizavi[1:4], self.case_role[1]), parse_mode='html')
            self.send_message(f'{self.name()}, Вы уже ознакомились со своей ролью.\nПредлагаю теперь поставить цели '
                              f'(желаемый результат) на переговоры.\n\n')
            self.set_goals()

    def send_mail(self, host='mail.nic.ru', subject='Отсутствие промокода',
                  to_addr='bot@sellwell.ru', from_addr='bot@sellwell.ru', port=587):
        print('Sending!!')
        text = 'Здравствуйте, меня зовут {0} {1}. Я из компании {2}. Мне не выдали промокод для группы.' \
               'Буду благодарен за решение проблемы\n\n\n\nP.S Сообщение сгенерировано автоматически.' \
               ''.format(self.name(), self.surname(), self.company())
        msg = MIMEMultipart()
        password = os.getenv('MAIL_PASS')
        msg['From'] = from_addr
        msg['To'] = to_addr
        msg['Subject'] = subject
        msg.attach(MIMEText(text, 'plain'))
        server = smtplib.SMTP(host=host, port=port)
        server.starttls()
        server.login(msg['From'], password)
        server.sendmail(msg['From'], msg['To'], msg.as_string())
        server.quit()

    def input_deadlines(self, *dates):
        self.deadlines = tuple(dates)

    def set_goals(self, goals_number=4, questions=(
    '<b>Укажите какого результата Вы планируете добиться по ЦОД1,%</b> (целым числом без пробелов)\n\nНапример: <i>30</i>',
    '<b>Укажите какого результата Вы планируете добиться по ЦОД2,%</b> (целым числом без пробелов)\n\nНапример: <i>30</i>',
    '<b>Укажите какого результата Вы планируете добиться по ЦОД3,%</b> (целым числом без пробелов)\n\nНапример: <i>30</i>',
    '<b>Укажите какого результата Вы планируете добиться по ЦОД4,%</b> (целым числом без пробелов)\n\nНапример: <i>30</i>')):
        self.conv_score = 0
        if self.case == 'case2' and self.message_counter == 0:
            self.send_message('<b>Укажите какого результата Вы планируете добиться:</b>\nЦена в млн.р без пробелов\n'
                              '<i>Например 43.75</i>', parse_mode='html')
            self.bot.register_next_step_handler(self.msg, self.set_first_goal_case2)

        elif self.case == 'case2':
            self.send_message('<b>Укажите какого результата Вы планируете добиться:</b>\nЦена в млн.р без пробелов\n'
                              '<i>Например 43.75</i>', parse_mode='html')
            self.bot.register_next_step_handler(self.msg, self.set_first_goal_case2)

        elif self.case == 'case3' and self.message_counter == 0:
            self.send_message('<b>Укажите какого результата Вы планируете добиться:</b>\nМесто хранения продукции\n',
                              markup=self.create_inline_markup(['Внуково', 'Обнинск'], ['vnuk', 'obn']),
                              parse_mode='html')

        elif self.case == 'case3':
            self.send_message('<b>Укажите какого результата Вы планируете добиться:</b>\nМесто хранения продукции\n',
                              markup=self.create_inline_markup(['Внуково', 'Обнинск'], ['vnuk', 'obn']),
                              parse_mode='html')

        else:
            cur_value = len(self.goals)
            if cur_value < goals_number:
                self.send_message(questions[cur_value], parse_mode='html')
                self.bot.register_next_step_handler(self.msg, self.input_goal)
            else:
                self.validate_goals()

    def set_first_goal_case3(self, message):
        try:
            res = int(message.text)
            lines = (0, 12)
            if lines[0] <= res <= lines[1]:
                self.goals.append(res)
                self.conv_score += self.get_precent_scores_case3(self.case_role[0], res)
                print(self.conv_score)
                self.send_message('Отсрочка платежа', self.create_inline_markup(['30 дней', '60 дней', '90 дней',
                                                                                 '120 дней'],
                                                                                ['30_days', '60_days', '90_days',
                                                                                 '120_days']))
            else:
                self.send_message('Ваши договоренности должны быть в диапазоне {0} - {1}%'.format(*lines))
                self.bot.register_next_step_handler(message, self.set_first_goal_case3)
        except ValueError:
            self.send_message('Укажите Вашу цель по проценту повышения тарифов в % <b>целым числом без пробелов</b> '
                              '<i>знак % вводить не нужно</i>', parse_mode='html')
            self.bot.register_next_step_handler(message, self.set_first_goal_case3)

    def set_first_goal_case2(self, message):
        ranges = ()
        scores = None
        if self.state() in ['SET_CASE_GOALS', 'IN_CONVERSATION_CASE2', 'WAITING_4_ACCEPT']:
            try:
                if self.case_role[0] == 'atom':
                    ranges = (29.75, 41.75)
                    self.conv_score += int(round(50 * ((41.75 - float(message.text)) / 12)))
                else:
                    ranges = (31.75, 43.75)
                    self.conv_score += int(round(70 * ((float(message.text) - 31.75) / 12)))
                res = float(message.text)
                if ranges[0] <= res <= ranges[1]:
                    self.goals.append(res)
                    print(self.conv_score)
                    self.send_message('Должность г-на Старче в компании и срок:',
                                      self.create_inline_markup(
                                          ['Немедленный уход (без должности)', 'Президент на 3 года (без '
                                                                               'права принятия решений',
                                           'Генеральный директор на 1 год', 'Генеральный директор на 3 '
                                                                            'года', 'Генеральный директор на '
                                                                                    '5 лет'],
                                          ['kick', 'without_rights', '1_year', '3_years', '5_years']))
                else:
                    self.send_message('Введите число в диапазоне <i>(от {0} до {1})</i>'.format(*ranges), parse_mode='html')
                    self.bot.register_next_step_handler(self.msg, self.set_first_goal_case2)
            except ValueError:
                self.send_message('Укажите Вашу цель на переговоры (млн.р) числом без символов и пробелов:')
                self.bot.register_next_step_handler(self.msg, self.set_first_goal_case2)

    def input_goal(self, message):
        cur_value = len(self.goals)
        tmp = {'rus': ((10, 20, 30, 40), (40, 40, 50, 60)),
               'china': ((40, 30, 20, 10), (30, 30, 40, 50))}
        low = 20
        if message.text.isdigit():
            try:
                if int(message.text) in range(low, tmp[self.case_role[0]][1][cur_value] + 1):
                    self.goals.append(message.text)
                    if cur_value > 3:
                        print(self.get_first_case_score(self.goals, self.case_role[0], tmp, low))
                        self.conv_score += self.get_first_case_score(self.goals, self.case_role[0], tmp, low)
                        print(self.goals)
                        print(self.conv_score)
                else:
                    self.send_message('Пожалуйста, введите число, попадающее в заданный диапазон: {0} - {1}'
                                      ''.format(low, tmp[self.case_role[0]][1][cur_value]))
            except KeyError:
                print('KeyError')
        else:
            self.send_message('Пожалуйста введите договоренности по ЦОД в % целым числом без пробелов'
                              ' (знак % вводить не нужно)', parse_mode='html')
        self.set_goals()

    def get_goals(self):
        return self.goals

    def save_last_message(self, message):
        if message.chat.id == self.id:
            self.msg = message
            self.update_last_activity_time()

    def group_code(self):
        return self.__group_code

    def subscribe(self, storage_ref):
        self.subscribers.append(storage_ref)

    def validate_goals(self):
        print(self.goals)
        if self.case == 'case1':
            print()
            self.send_message(
                '<b>Подтвердите правильность ввода:</b>\n<i>ЦОД1:</i> <b>{0}%</b>\n<i>ЦОД2:</i> <b>{1}%</b>\n<i>ЦОД3:</i> <b>{2}%</b>\n<i>ЦОД4:</i> <b>{3}%</b>\n'
                ''.format(*self.goals), self.create_inline_markup(['Все верно!✅', 'Изменить❌'],
                                                                  ['accept_goals', 'change_goals']),
                parse_mode='html')
        elif self.case == 'case2':
            self.send_message('<b>Подтвердите правильность ввода:</b>\n<i>Цена (млн.р):</i> <b>{0}</b>\n'
                              '<i>Должность г-на Старче в компании и срок:</i>\n<b>{1}</b>\n'
                              '<i>Сокращение персонала:</i> <b>{2}%</b>\n'
                              '<i>Название компании:</i> <b>{3}</b>\n'
                              ''.format(*self.goals), self.create_inline_markup(['Все верно!✅', 'Изменить❌'],
                                                                                ['accept_goals', 'change_goals']),
                              parse_mode='html')

        elif self.case == 'case3':
            self.send_message('<b>Подтвердите правильность ввода:</b>\n<i>Место хранения продукции:</i> <b>{0}</b>\n'
                              '<i>Срок переезда:</i> <b>{1}</b>\n'
                              '<i>Процент повышения тарифов:</i> <b>{2}%</b>\n'
                              '<i>Отсрочка платежа:</i> <b>{3} дней</b>\n'
                              ''.format(*self.goals), self.create_inline_markup(['Все верно!✅', 'Изменить❌'],
                                                                                ['accept_goals', 'change_goals']),
                              parse_mode='html')

    def ready_to_negotiat(self):
        print(f'{self.id} ready to nego!!!')
        self.ready_to_nego = True

    def push_to_group_queue(self):
        sides = [('rus_side', 'china_side'), ('star_side', 'atom_side'), ('orion_side', 'dental_star_side')]
        i = int(self.case[4])
        try:
            print('before')
            info = self.ctrl.query_any_rows(col_name=', '.join((*sides[i - 1], 'is_finished', 'id')),
                                            table_name=f'conversation{i}', cond_value=self.id, cond=sides[i - 1][0])
            print('after')
            if len(info) == 0:
                info = self.ctrl.query_any_rows(col_name=', '.join((*sides[i - 1], 'is_finished', 'id')),
                                                table_name=f'conversation{i}', cond_value=self.id, cond=sides[i - 1][1])
            try:
                if len(info) == 0 or info is None:
                    print('Inject from db')
                    self.subscribers[0].already_nego(info, self.group_code(), self.case)
                else:
                    self.subscribers[0].dispatch(self.group_code(), self.case, self.id)
            except IndexError:                                                                                                                                                                                                                                                                                                                                                      
                print('Error')                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  
                self.subscribers[0].dispatch(self.group_code(), self.case, self.id)
        except KeyError:
            self.send_message("Неизвестный промокод. Пожалуйста введите промокод\n"
                              "<i>заглавными буквами без пробелов в одну строку</i>", parse_mode='html')
            self.bot.register_next_step_handler(self.msg, self.get_code)

    def update_col_in_db(self, col_name, value):
        self.ctrl.update_data(table_name='users', col_name=col_name, new_value=value,
                              cond='chat_id', cond_value=self.id)

    def update_cols_in_db(self, table_name, col_names, values):
        self.ctrl.update_any_data(table_name=table_name, col_name=col_names, new_value=values,
                                  cond_value=self.id, cond='chat_id')

    def set_case_goals(self, message):
        tmp = self.ctrl.query_any_rows(table_name='conversation{0}'.format(self.case[4]), col_name='id',
                                       cond='{0}_side'.format(self.case_role[0]),
                                       cond_value=self.id)[0]
        self.ctrl.add_record(table_name='conversation{0}_goals_{1}'.format(self.case[4], self.case_role[0]),
                             col_names=('conversation_id', 'goals', 'expectation'),
                             col_values=(tmp[0], ','.join(self.goals), message.text))
        self.goals.clear()
        self.send_message('Отличная работа! Этап подготовки к переговорам завершен.\n\n'
                          'Как только Ваш визави будет готов начать переговоры,\nВы оба получите уведомление в чате\n\n'
                          '<b>Внимание:</b>\nЕсли Вы долго не получаете уведомление о старте, значит {0} еще не '
                          'завершил приготовления к переговорам или остался на этапе входного теста. Вы можете '
                          'напомнить о переговорах {1} самостоятельно, если знакомы лично.'.format(self.vizavi[1],
                                                                                                   self.vizavi[1]),
                          parse_mode='html')
        self.add_social_score(20)
        self.change_state('READY_TO_CONV')
        self.start_nego_alert()

    def start_nego_alert(self):
        key = 'READY_TO_CONV'.format(self.case.upper())
        vizavi_state = self.subscribers[0].users()[self.vizavi[0]].state()
        if self.state() == key and vizavi_state == key:
            self.change_state('IN_CONVERSATION_{0}'.format(self.case.upper()))
            self.subscribers[0].users()[self.vizavi[0]].change_state('IN_CONVERSATION_{0}'.format(self.case.upper()))
            self.send_message('Ваш визави завершил все приготовления к переговорам, а это значит, что '
                              'пора поприветствовать друг друга в чате!')
            self.bot.send_message(self.vizavi[0],
                                  'Ваш визави завершил все приготовления к переговорам, а это значит, что '
                                  'пора поприветствовать друг друга в чате!')
        elif self.state() == key and vizavi_state not in [key, 'SET_CASE_GOALS', 'IN_NEGO_TEST']:
            self.bot.send_message(self.vizavi[0], '{} {} приглашает вас начать переговоры.\n'.format(self.name(),
                                                                                                     self.surname()))
        elif vizavi_state == 'SET_CASE_GOALS':
            self.bot.send_message(self.vizavi[0], '{} уже прошел этап подготовки и приглашает вас начать переговоры.'
                                                  '\n<b>Продолжайте ввод цели в поле ниже</b>'.format(self.name()),
                                  parse_mode='html')

    def start_nego_test_style(self):
        self.send_message('Тест состоит из 30 вопросов, ответы на них\n'
                          'обычно занимают 5-7 минут\n'
                          'Для повышения достоверности и полезности\n'
                          'теста, в спомните пожалуйста реальные\n'
                          'ситуации и прегеоворы\n'
                          'После ответа на вопросы, Вы узнаете\n'
                          'какой стиль чаще демонистрируете в\n'
                          'переговорах', markup=self.create_inline_markup(['Начать'], ['start_nego_test_style']))

    def set_final_goals(self, questions=('Введите Ваши договоренности:\nПо ЦОД1 (в % <b>целым числом без пробелов</b>)',
                                         'Введите Ваши договоренности:\nПо ЦОД2 (в % <b>целым числом без пробелов</b>)',
                                         'Введите Ваши договоренности:\nПо ЦОД3 (в % <b>целым числом без пробелов</b>)',
                                         'Введите Ваши договоренности:\nПо ЦОД4 (в % <b>целым числом без пробелов</b>)')):
        if self.case == 'case1':
            cur_value = len(self.goals)
            if cur_value < len(questions):
                self.send_message(questions[cur_value], parse_mode='html')
                self.bot.register_next_step_handler(self.msg, self.input_final_goal)
            else:
                tmp = {'rus': ((10, 20, 30, 40), (40, 40, 50, 60)),
                       'china': ((40, 30, 20, 10), (30, 30, 40, 50))}
                self.conv_score = self.get_first_case_score(self.goals, self.case_role[0], tmp, 20)
                self.send_goals_to_vizavi()

        elif self.case in ['case2', 'case3']:
            self.set_goals()

    def personal_assesment(self):
        self.change_state('IN_PA')
        self.send_message('Оцените свою удовлетворенность проведенными переговорами по 10-балльной шкале',
                          self.create_inline_markup([str(i) for i in range(1, 11)],
                                                    ['pa_{0}'.format(j) for j in range(1, 11)], width=5))

    def p2p_func_two(self, message):
        markup1 = types.InlineKeyboardMarkup(row_width=5)
        buttons = [types.InlineKeyboardButton(text=str(i), callback_data=str(i)) for i in range(1, 11)]
        print(buttons)
        markup1.add(*buttons)
        data = self.ctrl.query_any_rows(table_name='feedback_conversation', cond='user_id', cond_value=self.id,
                                        col_name='good')
        self.ctrl.custom_query(f'UPDATE feedback_conversation SET bad = "{message.text}" WHERE'
                               f' user_id = {self.id} AND vizavi_id = {self.vizavi[0]}')
        self.send_message('Благодарим за предоставление обратной связи! Вы получите уведомление когда Ваш визави даст'
                          ' Вам обратную связь')
        self.ctrl.update_data(table_name=f'conversation{self.case[4]}', col_name='is_finished',
                              new_value=f'"{True}"', cond=f'{self.case_role[0]}_side', cond_value=self.id)
        self.add_social_score(20)
        self.change_state('WAITING_4_FB')
        key = self.inject_data_from_hub()
        print(key)
        print(self.case)
        if key is not None:
            print('key_is_not_none')
            self.send_message(key, markup=markup1, parse_mode='html')

        msg = '{0} {1} дал вам обратную связь по итогам переговоров:\n\n<b>Ваши сильные ходы:</b>\n{2}\n\n<b>Ваши ' \
              'слабые ходы:</b>\n{3}\n\nПожалуйста оцените полезность обратной связи по 10-балльной шкале:' \
              ''.format(self.name(), self.surname(), data[-1][0], message.text)

        vizavi_state = self.subscribers[0].users()[self.vizavi[0]].state()
        if vizavi_state == 'WAITING_4_FB':
            self.bot.send_message(self.vizavi[0], msg, reply_markup=markup1, parse_mode='html')
        else:
            self.subscribers[0].push_data_to_hub(self.group_code(), self.vizavi[0], msg)

    def inject_data_from_hub(self):
        return self.subscribers[0].get_data_from_hub(self.group_code(), self.id)

    def p2p_func_one(self, message):
        self.ctrl.add_record(table_name='feedback_conversation', col_names=('user_id', 'good', 'vizavi_id'),
                             col_values=(self.id, message.text, self.vizavi[0]))
        self.send_message('Спасибо!\n<b>Теперь укажите Вашему визави на 3 зоны роста,'
                          ' проработав которые, он сможет усилить себя как переговорщик:</b>\n\nНапример:\n<i>'
                          'Евгений, ты бы мог не уступать мне те 5% в ЦОД2, это сыграло бы тебе в плюс. Еще ты слишком'
                          ' долго отвечал на мои сообщения и лишний раз дал мне время перечитать условия кейса и '
                          'внимательнее подумать. Изначально я ошибся в расчетах и ты бы мог договориться со мной на '
                          'более выгодные для себя условия. В остальном мне сказать нечего, ты крут!</i>'
                          '', parse_mode='html')
        self.bot.register_next_step_handler(self.msg, self.p2p_func_two)

    def p2p_assesment(self):
        self.change_state('IN_P2P')
        self.send_message('Отличная работа, {2}!\n\nА теперь еще раз вспомните переговоры и\n<b>опишите 3 сильных '
                          'качества {0} {1}</b>\n\nНапример:\n<i>Евгений, ты изначально имел очень проактивный настрой,'
                          ' что помогло тебе взять под контроль переговоры. Тяжело было перехватить инициативу и '
                          'отстоять свою позицию. Также ты умело оперировал фактами и цифрами, быстро считал и '
                          'отвергал некоторые мои требования. Экспертиза на высшем уровне :) Продолжай в том же духе!</i>\n'
                          '\nПропустив этот шаг, Вы потеряете 40 баллов в рейтинге социальной активности.\n'
                          'Следующий этап очень важен, поэтому прошу дать максимально полезную обратную связь Вашему '
                          'визави. '.format(*self.vizavi[1:3], self.name()), parse_mode='html')
        self.bot.register_next_step_handler(self.msg, self.p2p_func_one)

    def send_goals_to_vizavi(self):
        if self.case == 'case1':
            self.send_message('Подтвердите правильность ввода:\nЦОД1: {0}\nЦОД2: {1}\nЦОД3: {2}\nЦОД4: {3}\n'
                              ''.format(*self.goals), self.create_inline_markup(['Отправить✅', 'Изменить❌'],
                                                                                ['send_goals',
                                                                                 'change_final_goals']),
                              parse_mode='html')
        elif self.case == 'case2':
            self.send_message('Подтвердите правильность ввода:\nЦена (млн.р): {0}\n'
                              'Должность г-на Старче в компании и срок:\n{1}\n'
                              'Сокращение персонала: {2}%\n'
                              'Название компании: {3}\n'
                              ''.format(*self.goals), self.create_inline_markup(['Отправить✅', 'Изменить❌'],
                                                                                ['send_goals', 'change_final_goals']),
                              parse_mode='html')

        elif self.case == 'case3':
            self.send_message('Подтвердите правильность ввода:\nМесто хранения продукции: {0}\n'
                              'Срок переезда: {1}\n'
                              'Процент повышения тарифов: {2}%\n'
                              'Отсрочка платежа: {3} дней\n'
                              ''.format(*self.goals), self.create_inline_markup(['Отправить✅', 'Изменить❌'],
                                                                                ['send_goals', 'change_final_goals']),
                              parse_mode='html')

    def delete_logger(self):
        try:
            self.subscribers[1].close()
            self.subscribers.pop(1)
        except:
            print('failed')


    def end_conversation(self, vizavis_data):
        print()
        self.container.clear()
        self.timer.cancel()
        try:
            self.delete_logger()
        except:
            print('error')
        self.change_state('FINISH_NEGO')
        dist = ''
        max_sum = ''
        start_date = self.ctrl.query_any_rows('{0}_side'.format(self.case_role[0]), self.id,
                                              'conversation{}'.format(self.case[4]), ','.join(('begin_date', 'id')))
        CV = int(self.conv_score + vizavis_data[0])
        print(CV)
        conv_time = datetime.datetime.now() - parse_time_from_string(start_date[0][0])
        print(conv_time)
        if self.case == 'case1':
            dist = '"Интеллект СБ" 55 / 55 "China Block Data"'
            max_sum = '"Интеллект СБ" 50 / 70 "China Block Data"'

        elif self.case == 'case2':
            dist = '1) "Атом-Мир 56 / 56 "г-н Старче"\n2) "Атом-Мир 54 / 53 "г-н Старче"'
            max_sum = '"Атом-Мир 56 / 56 "г-н Старче"'

        elif self.case == 'case3':
            dist = '"Дентал Стар" 77 / 77 "Орион"'
            max_sum = '"Дентал Стар" 77 / 77 "Орион"'

        print(self.vizavi[1:3])
        print(int(vizavis_data[0]))
        print(int(self.conv_score))
        msg = 'Поздравляю! Давайте подведем итоги переговоров :)\n\n<b>{0} {1}</b>\nВаш результат в баллах: <b>{2}</b>' \
              '\n\n<b>{3} {4}</b>\nРезультат визави в баллах: <b>{5}</b>\n\n<b>Ваша созданная ценность:</b> {6}\n' \
              '<b>Лучшее соотношение win-win:</b>\n{7}\n<b>Максимум совокупной выгоды:</b>\n{8}\n\nПродолжительность переговоров: {9}' \
              '\nКол-во отправленных сообщений {0} {1}: {10}\nКол-во отправленных сообщений {3} {4}: {11}\n' \
              ''.format(self.name(), self.surname(), int(self.conv_score), *self.vizavi[1:3], int(vizavis_data[0]),
                        CV, dist, max_sum, str(conv_time)[0:10], self.message_counter, vizavis_data[1])
        self.send_message('Нажмите кнопку "Сравнить свои цели с результатами" для того чтобы двигаться дальше')
        self.add_social_score(10)
        self.send_message(msg, self.create_inline_markup(['Сравнить свои цели с результатами'], ['compare']),
                          parse_mode='html')
        try:
            print('conv inject')
            self.ctrl.add_record(table_name='conversation{0}_result'.format(self.case[4]),
                                 col_names=('id', 'SCV', 'duration', 'message_number1', 'message_number2', 'result'),
                                 col_values=(
                                     start_date[0][1], CV, str(conv_time), self.message_counter, vizavis_data[1],
                                     str(self.goals)))
        except :
            print('Решим этот вопрос позже')

    def input_final_goal(self, message):
        cur_value = len(self.goals)
        ranges = ()
        scores = ()
        if self.case_role[0] == 'china':
            ranges = ((20, 30), (20, 30), (20, 40), (20, 50))
            scores = (40, 30, 20, 10)
        elif self.case_role[0] == 'rus':
            ranges = ((20, 40), (20, 40), (20, 50), (20, 60))
            scores = (10, 20, 30, 40)
        if message.text.isdigit():
            if int(message.text) in range(ranges[cur_value][0], ranges[cur_value][1] + 1):
                self.goals.append(int(message.text))
                print(self.goals)
            else:
                self.send_message('Пожалуйста введите число попадающее'
                                  'в заданный диапазон: {0} - {1}'.format(*ranges[cur_value]))
        else:
            self.send_message('Пожалуйста введите число!')
        self.set_final_goals()

    def change_case(self, new_case):
        print(f'change case in {self.id}')
        print(self.trend[2])
        print(new_case)
        tmp = self.case
        self.case = new_case
        try:
            if int(new_case[4]) - int(tmp[4]) > 1:
                self.case = tmp
        except (IndexError, ValueError, AttributeError, TypeError):
            print('SKIP')
        self.update_col_in_db('cur_case', '"' + self.case + '"')
        print(f'case in {self.id} = {self.case}')

    def get_current_pos_in_rate(self):
        tmp = []
        res = self.ctrl.query_with_sort_modify(table_name='users', col_name=','.join(('chat_id', 'score')),
                                               order_name='score', cond='group_code',
                                               cond_value=f"'{self.group_code()}'")
        for i in res:
            tmp.append(i[0])
        return tmp.index(self.id) + 1

    def get_current_pos_in_social_rate(self):
        tmp = []
        res = self.ctrl.query_with_sort_modify(table_name='users', col_name=','.join(('chat_id', 'social_score')),
                                               order_name='social_score', cond='group_code',
                                               cond_value=f"'{self.group_code()}'")
        for i in res:
            tmp.append(i[0])
        return tmp.index(self.id) + 1

    def update_last_activity_time(self):
        self.update_col_in_db('last_activity', "'" + datetime.datetime.now().strftime("%Y-%m-%d-%H.%M.%S") + "'")
