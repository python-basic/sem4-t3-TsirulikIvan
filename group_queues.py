import random
from user import User
import datetime
from telebot import types
from empty_msg import EmptyMsg, EmptyCallback
from something import get_current_month, get_next_week
from message_saver import NegoLogger


def call_counter(func):
    if not hasattr(call_counter, 'count'):
        call_counter.count = {}
    call_counter.count[func.__name__] = 0
    print(f'func name {func}')

    def wrapper(*args, **kwargs):
        call_counter.count[func.__name__] += 1
        if call_counter.count[func.__name__] == 2:
            call_counter.count[func.__name__] = 0
            raise IndexError
        print(f'Call counter = {call_counter.count[func.__name__]}')
        res = func(*args, **kwargs)
        return res
    return wrapper


def create_inline_markup(titles=('Личный кабинет☑'),
                         callbacks=None, width=1):
    if callbacks is None:
        callbacks = ('profile')
    markup = types.InlineKeyboardMarkup(row_width=width)
    buttons = [types.InlineKeyboardButton(text=title, callback_data=callback_data)
               for title, callback_data in zip(titles, callbacks)]
    markup.add(*buttons)
    return markup

def convert_to_deltatime(date):
    return datetime.datetime.fromordinal(get_next_week(get_current_month(),
                                                       date)[0].toordinal()) - datetime.datetime.now()

class GroupQueue:
    def __init__(self, ctrl, dispatcher):
        self.case1 = []
        self.case2 = []
        self.case3 = []
        self.nego = []
        self.dispatcher = dispatcher
        self.timers = []
        self.loggers = []
        self.nego_queue = []
        self.hub = {}
        self.ctrl = ctrl
        self.temporary = []

    def adding_cur_nego(self, case, group_code, nego_info):
        res = nego_info
        if res[0][:2] not in self.nego and res[0][0] not in self.nego_queue and res[0][2] not in self.nego_queue:
            if self.dispatcher.users()[res[0][0]].case != case:
                self.dispatcher.users()[res[0][0]].change_case(case)
            if self.dispatcher.users()[res[0][1]].case != case:
                self.dispatcher.users()[res[0][1]].change_case(case)
            self.add_nego(res[0][:2])
            self.check_nego(res[0][0], case, group_code, res[0][3])

    def backup_nego(self, obj_ref):
        print(obj_ref)
        print(f'nego queue = {self.nego_queue}')
        print(self.nego)
        if obj_ref.id not in self.nego_queue:
            sides = [('rus_side', 'china_side'), ('star_side', 'atom_side'), ('orion_side', 'dental_star_side')]
            i = int(obj_ref.case[4])
            print(f'i = {i}')
            try:
                res = self.ctrl.query_any_rows(col_name=', '.join((*sides[i - 1], 'is_finished', 'id')),
                                                   table_name=f'conversation{i}', cond_value=obj_ref.id, cond=sides[i - 1][0])
                print(f'res first inject = {res}')
                if len(res) == 0:
                    i = int(obj_ref.case[4])
                    res = self.ctrl.query_any_rows(col_name=', '.join((*sides[i - 1], 'is_finished', 'id')),
                                                   table_name=f'conversation{i}', cond_value=obj_ref.id, cond=sides[i - 1][1])
                    print(f'res second inject = {res}')
                case = obj_ref.case
                print(res[0][:2])
                print('IN_backup')
                print(obj_ref.vizavi)
                print(f'{res[0][:2]} and nego {self.nego}')
                if res[0][:2] not in self.nego and res[0][0] not in self.nego_queue and res[0][2] not in self.nego_queue:
                    if self.dispatcher.users()[res[0][0]].case != case:
                        self.dispatcher.users()[res[0][0]].change_case(case)
                    if self.dispatcher.users()[res[0][1]].case != case:
                        self.dispatcher.users()[res[0][1]].change_case(case)
                    self.add_nego(res[0][:2])
                    print(f'finish nego {self.nego}')
                    self.check_nego(res[0][0], obj_ref.case, obj_ref.group_code(), res[0][3])
                else:
                    print('alredy creATED')
            except IndexError:
                    print('Error')
                    self.adding_to_queue(obj_ref.case, obj_ref.id, obj_ref.group_code(),
                                         self.dispatcher.callbacks[obj_ref.id], None)


    def adding_to_queue(self, case, obj_id, gcode, call, nego_id):
        print(f'obj_id = {obj_id}')
        if case == 'case1':
            self.case1.append(obj_id)
            print('adding to {0} queue. queue = {1}'.format(case, self.case1))
            try:
                for i in self.shuffle(self.case1, self.return_users_vizavis(self.case1)):
                    self.add_nego(i)
                    print(self.nego)
                    self.check_nego(i[0], case, gcode, nego_id)
            except ValueError as e:
                print(e)

        elif case == 'case2':
            self.case2.append(obj_id)
            print('adding to {0} queue. queue = {1}'.format(case, self.case2))
            try:
                for i in self.shuffle(self.case2, self.return_users_vizavis(self.case2)):
                    self.add_nego(i)
                    self.check_nego(i[0], case, gcode, nego_id)
            except Exception as e:
                print(e)

        elif case == 'case3':
            self.case3.append(obj_id)
            print('adding to {0} queue. queue = {1}'.format(case, self.case3))
            try:
                for i in self.shuffle(self.case3, self.return_users_vizavis(self.case3)):
                    self.add_nego(i)
                    self.check_nego(i[0], case, gcode, nego_id)
            except Exception as e:
                print(e)
        print(self.case1)
        print(self.case2)
        print(self.case3)

    def add_nego(self, users):
        self.nego.append(tuple(users))

    def check_nego(self, user_id, case, gcode, nego_id=None):
        print('CALL CHECK_NEGO')
        map = {'case1': ['conversation1', {'side1': 'rus', 'side2': 'china'}],
               'case2': ['conversation2', {'side1': 'star', 'side2': 'atom'}],
               'case3': ['conversation3', {'side1': 'orion', 'side2': 'dental_star'}]}
        print(f'code = {gcode}\nnego_id = {nego_id}')
        time_line = []
        print(len(self.nego))
        if len(self.nego) == 0:
            self.dispatcher.users()[user_id].send_message('Идет поиск визави!')
        else:
            for i in self.nego:
                if len(i) < 2:
                    self.dispatcher.users()[user_id].send_message('Идет поиск визави!')
                else:
                    if user_id in i:
                        date_data = {'SWTEST': (datetime.datetime(2020, 5, 18, 12),
                                                datetime.datetime(2020, 5, 25, 12),
                                                datetime.datetime(2020, 6, 1, 12)),
                                     'RUSATOM': (datetime.datetime(2020, 5, 18, 12),
                                                 datetime.datetime(2020, 5, 25, 12),
                                                 datetime.datetime(2020, 6, 1, 12)),
                                     'YANDEX_BERU2': (datetime.datetime(2020, 6, 1, 12),
                                                      datetime.datetime(2020, 6, 8, 12),
                                                      datetime.datetime(2020, 6, 15, 12))
                                     }
                        time_line = date_data[gcode]
                        print(time_line)
                        data = []
                        print(list(map[case][1].values()))
                        print(f'i = {i}')
                        if nego_id is not None:
                            start_date = self.ctrl.query_any_rows(cond='id', cond_value=nego_id,
                                                                  table_name=map[case][0],
                                                                  col_name=','.join([f'{i}_side' for i in
                                                                                     list(map[case][1].values())]))
                            print(start_date)
                            try:
                                if i != start_date[0]:
                                    raise IndexError
                                data = start_date[0]
                                print('backup nego')
                            except IndexError:
                                print('error')
                                data = tuple(self.disturb_roles(i).values())
                                self.ctrl.add_record(table_name=map[case][0],
                                                     col_values=(
                                                         *data, datetime.datetime.now().strftime("%Y-%m-%d-%H.%M.%S")),
                                                     col_names=('{0}_side'.format(map[case][1]['side1']),
                                                                '{0}_side'.format(map[case][1]['side2']), 'begin_date'))
                        else:
                            print('random disturb')
                            data = tuple(self.disturb_roles(i).values())
                            self.ctrl.add_record(table_name=map[case][0],
                                                 col_values=(
                                                 *data, datetime.datetime.now().strftime("%Y-%m-%d-%H.%M.%S")),
                                                 col_names=('{0}_side'.format(map[case][1]['side1']),
                                                            '{0}_side'.format(map[case][1]['side2']), 'begin_date'))
                            print('adding_new_conv_record')
                        tmp = data
                        self.loggers.append(NegoLogger(case, *tmp, None, None, None))
                        for i in tmp:
                            self.dispatcher.users()[i].subscribe(self.loggers[-1::][0])
                            print(self.dispatcher.users()[i].subscribers)
                        print(f'{user_id} tmp = {tmp}')
                        self.nego_queue.extend(tmp)
                        print(f'check_nego = {self.nego_queue}')
                        if tmp not in self.temporary:
                            self.temporary.append(tmp)
                            if user_id == tmp[0]:
                                print('if')
                                self.dispatcher.users()[user_id].load_conversation_data(self.dispatcher.users()[tmp[1]].get_info(),
                                                                                        self.dispatcher.callbacks[user_id],
                                                                                        self.dispatcher.rules[case]['side1'],
                                                                                        map[case][1]['side1'],
                                                                                        time_line[int(case[4]) - 1])
                                self.dispatcher.users()[tmp[1]].load_conversation_data(
                                    self.dispatcher.users()[user_id].get_info(),
                                    self.dispatcher.callbacks[user_id],
                                    self.dispatcher.rules[case]['side2'],
                                    map[case][1]['side2'], time_line[int(case[4]) - 1])
                            else:
                                print('else')
                                self.dispatcher.users()[user_id].load_conversation_data(self.dispatcher.users()[tmp[0]].get_info(),
                                                                                        self.dispatcher.callbacks[user_id],
                                                                                        self.dispatcher.rules[case]['side2'],
                                                                                        map[case][1]['side2'],
                                                                                        time_line[int(case[4]) - 1])
                                self.dispatcher.users()[tmp[0]].load_conversation_data(
                                    self.dispatcher.users()[user_id].get_info(),
                                    self.dispatcher.callbacks[user_id],
                                    self.dispatcher.rules[case]['side1'],
                                    map[case][1]['side1'], time_line[int(case[4]) - 1])
                            print(self.dispatcher.users()[tmp[0]].get_info())
                            print(self.dispatcher.users()[tmp[1]].get_info())
                            print(self.dispatcher.dispatch_map[self.dispatcher.groups_code_map[gcode]].__dict__)

    def see_users(self):
        return self.__dict__

    def end_nego(self, nego_sides, cur_case):
        print('here')
        print(nego_sides)
        max_value = {'case1': 120, 'case2': 112, 'case3': 154}
        tmp = None
        if nego_sides in self.nego:
            self.loggers.pop(self.nego.index(nego_sides))
            tmp = self.nego.pop(self.nego.index(nego_sides))
        else:
            nego_sides = (nego_sides[1], nego_sides[0])
            self.loggers.pop(self.nego.index(nego_sides))
            tmp = self.nego.pop(self.nego.index(nego_sides))
        for i in tmp:
            try:
                print(i)
                print(self.nego_queue)
                self.nego_queue.pop(self.nego_queue.index(i))
            except IndexError:
                continue
        print(self.dispatcher.users())
        print('call conversation at {0}'.format(tmp[0]))
        self.dispatcher.users()[tmp[0]].add_score(self.dispatcher.users()[tmp[0]].conv_score / max_value[cur_case] * 100)
        self.dispatcher.users()[tmp[0]].end_conversation((self.dispatcher.users()[tmp[1]].conv_score,
                                                          self.dispatcher.users()[tmp[1]].message_counter))
        print('call conversation at {0}'.format(tmp[1]))
        self.dispatcher.users()[tmp[1]].add_score(self.dispatcher.users()[tmp[1]].conv_score / max_value[cur_case] * 100)
        self.dispatcher.users()[tmp[1]].end_conversation((self.dispatcher.users()[tmp[0]].conv_score,
                                                          self.dispatcher.users()[tmp[0]].message_counter))

    def terminate_nego(self, sides, case, gcode):
        print('HERRRRRRRRRRRRRRRRRRRRRRR')
        print(self.nego)
        try:
            tmp = None
            if sides in self.nego:
                self.loggers.pop(self.nego.index(sides))
                tmp = self.nego.pop(self.nego.index(sides))
            else:
                nego_sides = (sides[1], sides[0])
                self.loggers.pop(self.nego.index(nego_sides))
                tmp = self.nego.pop(self.nego.index(nego_sides))
            print(tmp)
            for i in tmp:
                try:
                    self.nego_queue.pop(self.nego_queue.index(i))
                except IndexError:
                    continue
            for i in tmp:
                markup = None
                if case in ['case2', 'case3']:
                    try:
                        self.backup_nego(self.dispatcher.users()[i])
                    except Exception as e:
                        print(e)
                        self.adding_to_queue(case, i, gcode, self.dispatcher.callbacks[i], None)
                    if self.dispatcher.users()[i].done_test_style:
                        markup = create_inline_markup(titles=['Личный кабинет'], callbacks=['profile'])
                    else:
                        markup = create_inline_markup(titles=['Тест переговорные стили', 'Личный кабинет'],
                                                      callbacks=['start_nego_test_style', 'profile'])
                self.dispatcher.users()[i].change_state('MAIN_MENU')
                self.dispatcher.users()[i].welcome_message(custom_markup=markup)
        except ValueError:
            print('Ошибка')

    @staticmethod
    def disturb_roles(args):
        case = random.randint(0, 1)
        if case == 0:
            return {'side1': args[0], 'side2': args[1]}
        else:
            return {'side1': args[1], 'side2': args[0]}

    @staticmethod
    def shuffle(seq, seq_map):
        print(seq)
        print(seq_map)
        res_queue = []
        try:
            for j in seq_map.keys():
                for i in seq:
                    if i != j and i not in seq_map[j]:
                        res_queue.append((seq.pop(seq.index(j)), seq.pop(seq.index(i))))
                        break
                continue
        except (ValueError, IndexError):
            print('Недостаточно участников!')
        return res_queue

    def return_users_vizavis(self, queue):
        print({i: list(map(lambda j: j[0], self.dispatcher.users()[i].ex_vizavis)) for i in queue})
        return {i: list(map(lambda j: j[0], self.dispatcher.users()[i].ex_vizavis)) for i in queue}

    def push_data_to_hub(self, user_id, data):
        self.hub.update([(user_id, data)])
        print(self.hub)

    def get_data_from_hub(self, user_id):
        return self.hub.pop(user_id, None)


class GroupDispatcher:
    def __init__(self, users_data, ctrl, test, bot):
        self.rules = {'case1': {'side1': 'https://teletype.in/@sellwell/H1NiudZhH',   #Интеллект СБ
                                'side2': 'https://teletype.in/@sellwell/HkLhHdb3H'},  #Китай
                      'case2': {'side1': 'https://teletype.in/@sellwell/rknI7fSTH',   #Г-н старче
                                'side2': 'https://teletype.in/@sellwell/HkbhLMS6S'},  #АТОМ-МИР
                      'case3': {'side1': 'https://teletype.in/@sellwell/TkCT12no',
                                'side2': 'https://teletype.in/@sellwell/6aILe-pb'}}
        self.timers = {'case1': [], 'case2': [], 'case3': []}
        self.groups_data = self.parse(ctrl=ctrl, data_array=users_data)
        self.groups_code_map = {i[0]: i[1] for i in ctrl.query_adm_data('groups', ','.join(('group_code',
                                                                                            'group_name')))}
        self.dispatch_map = {i: GroupQueue(ctrl, self) for i in self.groups_data.keys()}
        self.callbacks = {}
        self.__users = {}
        self.load_users_data(ctrl, bot, test)
        self.backup_nego_info()
        print('AFter backup nego')
        lambda i: print(i.__dict__), tuple(self.dispatch_map.values())
        print('AFter load_queue_data')
        self.load_queue_data()
        lambda i: print(i.__dict__), tuple(self.dispatch_map.values())

    def dispatch(self, group_code, case, obj, nego_id=None):
        try:
            call = self.callbacks[obj]
        except KeyError:
            call = None
        print(group_code, case, obj, nego_id)
        self.dispatch_map[self.groups_code_map[group_code]].adding_to_queue(call=call, case=case, obj_id=obj,
                                                                            gcode=group_code, nego_id=nego_id)

    def load_users_data(self, ctrl, bot, test):
        data = ctrl.query_adm_data('users', 'chat_id')
        for i in data:
            self.add_user(i[0], bot, ctrl, EmptyMsg(i[0]), test)
            self.callbacks.update([(i[0], EmptyCallback(i))])
        print(self.users())

    def backup_nego_info(self):
        data = list(self.users().values())
        print('In_backup_nego')
        for i in data:
            if i.state() in ['MAIN_MENU', 'IN_CONVERSATION_CASE1', 'IN_CONVERSATION_CASE2', 'IN_CONVERSATION_CASE3',
                             'SET_CASE_GOALS', 'READY_TO_CONV', 'WAITING_4_ACCEPT', 'WAITING_4_FB']:
                i.ready_to_negotiat()
            if i.id not in self.dispatch_map[self.groups_code_map[i.group_code()]].nego_queue and i.ready_to_nego:
                self.dispatch_map[self.groups_code_map[i.group_code()]].backup_nego(i)

    def load_queue_data(self):
        data = list(self.users().values())
        for i in data:
            print(self.dispatch_map[self.groups_code_map[i.group_code()]].nego_queue)
            if i.state() not in ['NO_REG', 'BEGIN_TEST'] and i.id not in self.dispatch_map[self.groups_code_map[i.group_code()]].nego_queue:
                print(f'LOAD_QUEUE_AT {i}')
                self.dispatch(i.group_code(), i.case, i.id, i.last_nego_id)
            else:
                continue
        for i in self.dispatch_map.values():
            print(i.see_users())

    def current_users(self):
        for i in self.dispatch_map.values():
            i.see_users()

    def add_user(self, user_id, bot, ctrl, msg, start_test):
        self.__users.update([(user_id, User(msg, bot, ctrl, start_test))])
        self.__users[user_id].subscribe(self)

    def users_list(self):
        return tuple(self.__users.keys())

    def check_nego(self, user_id, case):
        print('Call_check_nego')
        self.dispatch_map[self.groups_code_map[self.users()[user_id].group_code()]].check_nego(user_id,
                                                                                               case,
                                                                                               self.users()[user_id].group_code(),
                                                                                               self.users()[user_id].last_nego_id)

    def users(self):
        return self.__users

    def already_nego(self, nego_info, gcode, case):
        self.dispatch_map[self.groups_code_map[gcode]].adding_cur_nego(case, gcode, nego_info)

    def add_callback(self, callback):
        self.callbacks.update([(callback.message.chat.id, callback)])

    @staticmethod
    def parse(ctrl, data_array):
        keys = ctrl.query_adm_data('groups', 'group_name')
        res = {i[0]: [] for i in keys}
        for i in data_array:
            res[i[0]].append(i[1])
        return res

    def end_nego(self, nego_sides, group_code, case):
        self.dispatch_map[self.groups_code_map[group_code]].end_nego(nego_sides, case)

    def terminate_nego(self, group_code, sides, case):
        try:
            self.dispatch_map[self.groups_code_map[group_code]].terminate_nego(sides, case, group_code)
        except IndexError:
            print('Errror')

    def see_info(self):
        return self.__dict__

    def push_data_to_hub(self, group_code, user_id, data):
        self.dispatch_map[self.groups_code_map[group_code]].push_data_to_hub(user_id, data)

    def get_data_from_hub(self, group_code, user_id):
        return self.dispatch_map[self.groups_code_map[group_code]].get_data_from_hub(user_id)


