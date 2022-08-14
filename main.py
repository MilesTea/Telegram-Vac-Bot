#!/usr/bin/python3.3
import time
from telebot import asyncio_handler_backends
from telebot.async_telebot import types as tbat
import telebot.async_telebot as tba
import asyncio
import utils
import sql
import settings
import copy

# logger = tba.logger
# tba.logger.setLevel(logging.DEBUG)

token = 'token'

# кеш состояния пользователя (для реализации внутренних команд)
users_state = {}

# кеш данных пользователя, необходимых для внутренних команд
users_data = {}

# временные сообщения, необходимы для реализации списков
temporary_messages = {}

texts = settings.get_texts()


def kb(user_id):
    """
    Генерация клавиатуры в зависимости от информации о пользователе
    """
    keyboard = tbat.ReplyKeyboardMarkup(True)
    if user_id in users_state:
        keyboard.row(texts['cancel'])
    else:
        # Админ кнопки
        if admin_db.check(user_id):
            row = [texts['events']['new'], texts['events']['all']]
            keyboard.row(*row)
            keyboard.row(texts['questions']['all'])
            keyboard.row(texts['certificates']['all'])
        else:
            # Обычные кнопки
            keyboard.row(texts['questions']['ask_button'])
            keyboard.row(texts['certificates']['ask_button'])
        '''
        keyboard.row('Инфо')
        if user_db.is_subscribed(user_id):
            keyboard.row('Отписаться от рассылки')
        else:
            keyboard.row('Подписаться на рассылку')
        '''
    return keyboard


def in_kb(ar):
    """
    Составляет Inline клавиатуру.
    Получает на вход массив вида:
    [
        [
            ['Кнопка1, ряд 1', данные кнопки],
            ['Кнопка2, ряд 1', данные кнопки],
        ],
        [
            ['Кнопка3, ряд 2', данные кнопки]
        ]
    ]
    :param ar:
    :return:
    """
    if ar is None:
        return None
    inline_keyboard = tbat.InlineKeyboardMarkup()
    for i, row in enumerate(ar):
        buttons = []
        for button in row:
            buttons.append(tbat.InlineKeyboardButton(button[0], callback_data=button[1]))
        inline_keyboard.row(*buttons)
    return inline_keyboard


# Фильтры
class IsAdmin(tba.asyncio_filters.SimpleCustomFilter):
    """
    Проверка является ли пользователь администратором
    """
    key = 'is_admin'

    @staticmethod
    async def check(message: tba.types.Message):
        return admin_db.check(message.chat.id)


class InUserState(tba.asyncio_filters.SimpleCustomFilter):
    """
    Проверка находится ли пользователь во внутренней команде
    """
    key = 'in_user_state'

    @staticmethod
    async def check(message: tba.types.Message):
        if message.chat.id in users_state:
            return True
        else:
            return False


class UserState(tba.asyncio_filters.SimpleCustomFilter):
    """
    Проверка состояния пользователя
    """
    key = 'user_state'

    @staticmethod
    async def check(message: tba.types.Message):
        return users_state.get(message.chat.id)


# Прослойка, отрабатывающая перед передачей сообщения в обработчик
class Middleware(asyncio_handler_backends.BaseMiddleware):
    def __init__(self):
        super().__init__()
        self.update_types = ['message']

    async def pre_process(self, message, data):
        """
        Автоматически добавляет пользователя в базу данных, если его там ещё нет
        """
        # data['foo'] = 'Hello' # just for example
        # data['is_admin'] = admin_db.check(message.chat.id)
        # we edited the data. now, this data is passed to handler.
        # return SkipHandler() -> this will skip handler
        # return CancelUpdate() -> this will cancel update
        if not user_db.check(message.chat.id):
            username = '@' + message.chat.username
            user_db.add(message.chat.id, username)

    async def post_process(self, message, data, exception=None):
        text = '@' + str(message.chat.username) + ': '
        if message.content_type == 'text':
            text += message.text
        elif message.content_type == 'photo':
            if message.caption:
                text += message.caption
        print(text, flush=True)
        if exception:
            print('ОШИБКА:', exception, flush=True)


class CallbackMiddleware(asyncio_handler_backends.BaseMiddleware):
    def __init__(self):
        super().__init__()
        self.update_types = ['callback_query']

    async def pre_process(self, message, data):
        pass

    async def post_process(self, message, data, exception=None):
        text = f'Callback @{message.from_user.username}: {message.data}'
        print(text, flush=True)
        if exception:
            print('ОШИБКА:', exception, flush=True)


# Инициализация бота
bot = tba.AsyncTeleBot(token)
bot.add_custom_filter(IsAdmin())
bot.add_custom_filter(InUserState())
bot.add_custom_filter(UserState())
bot.setup_middleware(Middleware())
bot.setup_middleware(CallbackMiddleware())


# Удаление временных сообщений
async def cleanup(user_id):
    if user_id in temporary_messages:
        if temporary_messages[user_id]:
            for message in temporary_messages[user_id]:
                await bot.delete_message(user_id, message)
        temporary_messages[user_id].clear()
    else:
        temporary_messages[user_id] = []


async def notif(text):
    admins = admin_db.get_all()
    if utils.in_time_frame(current_settings.notifications_state, *current_settings.notifications_hours):
        for admin in admins:
            await bot.send_message(admin.user_id, text, reply_markup=kb(admin.user_id))


# Отмена
@bot.message_handler(content_types=['text', ], in_user_state=True,
                     func=lambda message: message.text == texts['cancel'])
async def cancel(message):
    """
    Отмена действия, обнуления состояния
    """
    users_state.pop(message.chat.id, None)
    users_data.pop(message.chat.id, None)
    await bot.send_message(message.chat.id, text=texts['main_menu'], reply_markup=kb(message.chat.id))


paginator_settings = {
        'q': {'entries': 'question_db', 'id_row': 'question_id', 'callback_code': 'q',
              'buttons': [[[texts['questions']['answer_button'], 'qa'],
                           [texts['questions']['delete_button'], 'qd']]],
              'rows': ['username', 'text']},
        'c': {'entries': 'certificate_db', 'id_row': 'certificate_id', 'callback_code': 'c',
              'buttons': [[[texts['certificates']['answer_button'], 'ca'],
                           [texts['certificates']['delete_button'], 'cd']]],
              'rows': ['username', 'text']},
        'e': {'entries': 'event_db', 'id_row': 'event_id', 'callback_code': 'e',
              'buttons': [[[texts['events']['delete_button'], f'ed']]],
              'rows': ['text']},
    }


async def paginator(current_page, user_id, mode='q'):
    current_paginator_settings = paginator_settings.get(mode)
    id_row, cb_code = current_paginator_settings['id_row'], current_paginator_settings['callback_code']
    entries = eval(f'{current_paginator_settings["entries"]}.get_all()')
    page_elements = 5
    all_pages, m = divmod(len(entries), page_elements)
    all_pages += 1 if m > 0 else 0
    entries_len = len(entries) - (current_page-1) * page_elements
    current_page_elements = page_elements if page_elements <= entries_len else entries_len
    await cleanup(user_id)
    temporary_messages[user_id].append((await bot.send_message(user_id, f'Страница {current_page}/{all_pages}')).id)
    for i in range(current_page_elements):
        entry = entries[i + (current_page-1) * page_elements]
        dt = utils.get_datetime(entry.ts)

        # Генерация кнопок
        buttons = copy.deepcopy(current_paginator_settings['buttons'])
        for row in buttons:
            for button in row:
                button[1] = button[1] + str(getattr(entry, id_row))
        buttons = in_kb(buttons)

        # Генерация текста сообщения
        text = []
        for a in current_paginator_settings['rows']:
            text.append(getattr(entry, a))
        text = '\n'.join(text)

        # Отправка сообщения
        if ('photo' in dir(entry)) and entry.photo:
            temporary_messages[user_id].append((await bot.send_photo(user_id, entry.photo,
                                                                     dt + '\n' + text,
                                                                     reply_markup=buttons)).id)
        else:
            temporary_messages[user_id].append((await bot.send_message(user_id,
                                                                       dt + '\n' + text,
                                                                       reply_markup=buttons)).id)
    # Генерация кнопок перехода на страницы
    if all_pages == 1:
        kb_ar = None
    elif current_page == 1:
        kb_ar = [[['Далее', f'{cb_code}p{current_page+1}']]]
    elif current_page == all_pages:
        kb_ar = [[['Назад', f'{cb_code}p{current_page-1}']]]
    else:
        kb_ar = [[['Назад', f'{cb_code}p{current_page - 1}'], ['Далее', f'{cb_code}p{current_page+1}']]]
    temporary_messages[user_id].append((await bot.send_message(user_id, f'Страница {current_page}/{all_pages}',
                                                               reply_markup=in_kb(kb_ar))).id)


@bot.callback_query_handler(func=lambda call: call.data[1] == 'p')
async def paginator_callback(call):
    await bot.answer_callback_query(call.id, '')
    await paginator(int(call.data[2:]), call.message.chat.id, call.data[0])


# Удаление по inline кнопке
@bot.callback_query_handler(func=lambda call: call.data[1] == 'd')
async def delete_callback(call):
    await bot.answer_callback_query(call.id, '')
    delete_settings = {
        'q': question_db,
        'c': certificate_db,
        'e': event_db,
    }
    delete_settings[call.data[0]].delete(call.data[2:])
    if call.message.content_type == 'text':
        await bot.edit_message_text('Успешно удалено', call.message.chat.id, call.message.id)
    elif call.message.content_type == 'photo':
        await bot.edit_message_caption('Успешно удалено', call.message.chat.id, call.message.id)


# Ответ на вопрос
@bot.callback_query_handler(func=lambda call: call.data[0:2] == 'qa')
async def question_callback(call):
    # print(call.data[2:])
    current_question = question_db.get(call.data[2:])
    await bot.answer_callback_query(call.id, '')  # Бот принимает сообщение
    if not current_question:
        await bot.send_message(call.message.chat.id, texts['questions']['not_found'],
                               reply_markup=kb(call.message.chat.id))
        users_state.pop(call.message.chat.id)
        users_data.pop(call.message.chat.id)
    else:
        users_data[call.message.chat.id] = {'user_id': call.data[2:], 'reply_id': call.message.id}
        users_state[call.message.chat.id] = 'question_answer'
        username = current_question.username
        await bot.send_message(call.message.chat.id, texts['questions']['answer'].format(username=username),
                               reply_markup=kb(call.message.chat.id))


@bot.message_handler(content_types=['text', 'photo', ], in_user_state=True, is_admin=True,
                     user_state='question_answer')
async def question_answer0(message):
    current_question = question_db.get(users_data[message.chat.id]['user_id'])
    if not current_question:
        await bot.send_message(message.chat.id, texts['questions']['not_found'],
                               reply_markup=kb(message.chat.id))
        users_state.pop(message.chat.id)
        users_data.pop(message.chat.id)
    else:
        users_state.pop(message.chat.id)
        users_data.pop(message.chat.id)
        question_db.delete(current_question.question_id)
        # print('Формирую отклик')
        answer_start = texts['questions']['answer_first_line']
        try:
            if message.content_type == 'text':
                await bot.send_message(current_question.user_id, answer_start+message.text,
                                       reply_markup=kb(current_question.user_id))
            elif message.content_type == 'photo':
                await bot.send_message(current_question.user_id, answer_start,
                                       reply_markup=kb(current_question.user_id))
                await bot.send_photo(current_question.user_id, caption=message.caption,
                                     photo=message.photo[-1].file_id,
                                     reply_markup=kb(current_question.user_id))
            await bot.send_message(message.chat.id, texts['questions']['answer_complete'],
                                   reply_markup=kb(message.chat.id))
        except Exception as error:
            print(error)
            await bot.send_message(message.chat.id, texts['questions']['answer_error'],
                                   reply_markup=kb(message.chat.id))


# Ответ на заявку
@bot.callback_query_handler(func=lambda call: call.data[0:2] == 'ca')
async def certificate_callback(call):
    current_certificate = certificate_db.get(call.data[2:])
    await bot.answer_callback_query(call.id, '')  # Бот принимает сообщение
    if not current_certificate:
        await bot.send_message(call.message.chat.id, texts['certificates']['not_found'],
                               reply_markup=kb(call.message.chat.id))
        users_state.pop(call.message.chat.id)
        users_data.pop(call.message.chat.id)
    else:
        users_data[call.message.chat.id] = call.data[2:]
        users_state[call.message.chat.id] = 'certificate_answer'
        username = current_certificate.username
        await bot.send_message(call.message.chat.id, texts['certificates']['answer'].format(username=username),
                               reply_markup=kb(call.message.chat.id))


@bot.message_handler(content_types=['text', 'photo', ], in_user_state=True, is_admin=True,
                     user_state='certificate_answer')
async def certificate_answer0(message):
    current_certificate = certificate_db.get(users_data[message.chat.id])
    if not current_certificate:
        await bot.send_message(message.chat.id, texts['certificates']['not_found'],
                               reply_markup=kb(message.chat.id))
    else:
        users_state.pop(message.chat.id)
        users_data.pop(message.chat.id)
        certificate_db.delete(current_certificate.certificate_id)
        answer_start = texts['certificates']['answer_first_line']
        try:
            if message.content_type == 'photo':
                await bot.send_message(current_certificate.user_id, answer_start,
                                       reply_markup=kb(current_certificate.certificate_id))
                await bot.send_photo(current_certificate.user_id, caption=message.caption,
                                     photo=message.photo[-1].file_id,
                                     reply_markup=kb(current_certificate.certificate_id))
            else:
                await bot.send_message(current_certificate.user_id, answer_start+message.text,
                                       reply_markup=kb(current_certificate.certificate_id))
            await bot.send_message(message.chat.id, texts['certificates']['answer_complete'],
                                   reply_markup=kb(message.chat.id))
        except Exception as error:
            print(error)
            await bot.send_message(message.chat.id, texts['certificates']['answer_error'],
                                   reply_markup=kb(message.chat.id))

'''
# Тестовая информация
@bot.message_handler(content_types=['text', ], in_user_state=False,
                     func=lambda message: message.text.lower() == 'тест')
async def info(message):
    await bot.send_message(message.chat.id, 'тест',
                           reply_markup=kb(message.chat.id))
    print('a')
    print('b')

# Отписка
@bot.message_handler(content_types=['text', ], in_user_state=False,
                     func=lambda message: message.text.lower() == 'отписаться от рассылки')
async def unsubscribe(message):
    """
    Отписка от рассылки
    """
    user_db.subscription(message.chat.id, False)
    await bot.send_message(message.chat.id, text='Вы были отписаны от рассылки', reply_markup=kb(message.chat.id))
'''
'''
# Подписка
@bot.message_handler(content_types=['text', ], in_user_state = False,
                     func=lambda message: message.text.lower() == 'подписаться на рассылку')
async def subscribe(message):
    """
    Подписка на рассылку
    """
    user_db.subscription(message.chat.id, True)
    await bot.send_message(message.chat.id, text='Вы были подписаны на рассылку', reply_markup=kb(message.chat.id))
'''
'''
# Инфо
@bot.message_handler(content_types=['text', ], in_user_state=False,
                     func=lambda message: message.text.lower() == 'инфо')
async def info(message):
    await bot.send_message(message.chat.id, 'Здесь будет находиться базовая информация',
                           reply_markup=kb(message.chat.id))
'''


# Задать вопрос
@bot.message_handler(content_types=['text', ], in_user_state=False,
                     func=lambda message: message.text == texts['questions']['ask_button'])
async def question(message):
    if not question_db.check(message.chat.id):
        users_state[message.chat.id] = 'question0'
        await bot.send_message(message.chat.id, texts['questions']['ask'],
                               reply_markup=kb(message.chat.id))
    else:
        await bot.send_message(message.chat.id, texts['questions']['ask_limit'],
                               reply_markup=kb(message.chat.id))


@bot.message_handler(content_types=['text', 'audio', 'document', 'photo', 'sticker', 'video', 'voice', 'location',
                                    'contact', ], in_user_state=True, user_state='question0')
async def question0(message):
    if message.content_type != 'text':
        await bot.send_message(message.chat.id, texts['questions']['ask_text_only'], reply_markup=kb(message.chat.id))
        return
    text = message.text if message.content_type == 'text' else message.caption
    if not utils.verify(text):
        await bot.send_message(message.chat.id, texts['questions']['ask_too_long'], reply_markup=kb(message.chat.id))
    else:
        username = '@' + message.chat.username
        question_db.add(message.chat.id, username, time.time(), text=text)
        users_state.pop(message.chat.id)
        await bot.send_message(message.chat.id, texts['questions']['ask_complete'],
                               reply_markup=kb(message.chat.id))
        await notif(texts['questions']['admin_notification'].format(username=username))


# Запрос справки
@bot.message_handler(content_types=['text', ], in_user_state=False,
                     func=lambda message: message.text == texts['certificates']['ask_button'])
async def certificate(message):
    if certificate_db.count_by_user(message.chat.id) < 2:
        users_state[message.chat.id] = 'certificate0'
        await bot.send_message(message.chat.id, texts['certificates']['ask'],
                               reply_markup=kb(message.chat.id))
    else:
        await bot.send_message(message.chat.id, texts['certificates']['ask_limit'],
                               reply_markup=kb(message.chat.id))


@bot.message_handler(content_types=['text', 'audio', 'document', 'photo', 'sticker', 'video', 'voice', 'location',
                                    'contact', ], in_user_state=True, user_state='certificate0')
async def certificate0(message):
    if message.content_type != 'text':
        await bot.send_message(message.chat.id, texts['certificates']['ask_text_only'],
                               reply_markup=kb(message.chat.id))
        return
    text = message.text
    if not utils.verify(text):
        await bot.send_message(message.chat.id, texts['certificates']['ask_too_long'], reply_markup=kb(message.chat.id))
    else:
        username = '@' + message.chat.username
        certificate_db.add(message.chat.id, username, time.time(), text=text)
        users_state.pop(message.chat.id)
        await bot.send_message(message.chat.id, texts['certificates']['ask_complete'],
                               reply_markup=kb(message.chat.id))
        await notif(texts['certificates']['admin_notification'])


# Стартовое сообщение
@bot.message_handler(content_types=['text', ], in_user_state=False,
                     func=lambda message: message.text.lower() == '/start')
async def start(message):
    await bot.send_message(message.chat.id, texts['/start'],
                           reply_markup=kb(message.chat.id))


# просмотр вопросов
@bot.message_handler(content_types=['text', ], in_user_state=False, is_admin=True,
                     func=lambda message: message.text == texts['questions']['all'])
async def all_questions(message):
    questions = question_db.check()
    # print(questions)
    if questions:
        await paginator(1, message.chat.id)
    else:
        await bot.send_message(message.chat.id, texts['questions']['empty'], reply_markup=kb(message.chat.id))


# просмотр заявок на справки
@bot.message_handler(content_types=['text', ], in_user_state=False, is_admin=True,
                     func=lambda message: message.text == texts['certificates']['all'])
async def all_certificates(message):
    certificates = certificate_db.check()
    if certificates:
        await paginator(1, message.chat.id, 'c')
    else:
        await bot.send_message(message.chat.id, texts['certificates']['empty'], reply_markup=kb(message.chat.id))


# просмотр событий
@bot.message_handler(content_types=['text', ], in_user_state=False, is_admin=True,
                     func=lambda message: message.text == texts['events']['all'])
async def all_events(message):
    events = event_db.get_all()
    # print(_events)
    if events:
        await paginator(1, message.chat.id, 'e')
    else:
        await bot.send_message(message.chat.id, texts['events']['empty'], reply_markup=kb(message.chat.id))


# Новое событие
@bot.message_handler(content_types=['text', ], in_user_state=False, is_admin=True,
                     func=lambda message: message.text == texts['events']['new'])
async def new_event(message):
    users_state[message.chat.id] = 'ev0'
    await bot.send_message(message.chat.id, texts['events']['new_datetime'],
                           reply_markup=kb(message.chat.id))


@bot.message_handler(content_types=['text', ], in_user_state=True, user_state='ev0', is_admin=True)
async def new_event_0(message):
    ts = utils.make_ts(message.text)
    if not ts:
        await bot.send_message(message.chat.id, texts['events']['new_datetime_error'],
                               reply_markup=kb(message.chat.id))
    else:
        _dict = {message.chat.id: dict()}
        users_data.update(_dict)
        users_data[message.chat.id]['date'] = ts
        users_state[message.chat.id] = 'ev1'
        await bot.send_message(message.chat.id, texts['events']['new_text'],
                               reply_markup=kb(message.chat.id))


@bot.message_handler(content_types=['text', 'photo', ], in_user_state=True, user_state='ev1', is_admin=True)
async def new_event_1(message):
    ts = users_data[message.chat.id]["date"]
    if message.content_type == 'text':
        event_db.add(ts, message.text)
        users_state.pop(message.chat.id)
        users_data.pop(message.chat.id, None)
        await bot.send_message(message.chat.id,
                               texts['events']['new_complete'].format(datetime=utils.get_datetime(ts)),
                               reply_markup=kb(message.chat.id))
    elif message.content_type == 'photo':
        event_db.add(ts, message.caption, photo=message.photo[-1].file_id)
        users_state.pop(message.chat.id)
        users_data.pop(message.chat.id, None)
        await bot.send_message(message.chat.id,
                               texts['events']['new_complete'].format(datetime=utils.get_datetime(ts)),
                               reply_markup=kb(message.chat.id))


async def make_settings(chat_id, message_id=None):
    kb_ar = []
    if current_settings.notifications_state:
        kb_ar.append([['Выключить', 'snf']])
    else:
        kb_ar.append([['Включить', 'snt']])
    kb_ar.append([['Установить часы', 'st']])
    text = f'Текущие настройки\n{current_settings}'
    if not message_id:
        await bot.send_message(chat_id, text, reply_markup=in_kb(kb_ar))
    else:
        await bot.edit_message_text(text, chat_id, message_id, reply_markup=in_kb(kb_ar))


@bot.message_handler(content_types=['text', ], in_user_state=False, is_admin=True,
                     func=lambda message: message.text.lower() == 'настройки')
async def bot_settings(message):
    await make_settings(message.chat.id)


@bot.callback_query_handler(func=lambda call: call.data[0] == 's')
async def settings_callback(call):
    await bot.answer_callback_query(call.id, '')
    if call.data[1] == 'n':
        current_settings.notifications_state = False if call.data[2] == 'f' else True
        await make_settings(call.message.chat.id, call.message.id)
    elif call.data[1] == 't':
        users_state[call.message.chat.id] = 'set0'
        await bot.send_message(call.message.chat.id, 'Введите удобный для вас промежуток времени в формате ЧЧ-ЧЧ',
                               reply_markup=kb(call.message.chat.id))
        users_data[call.message.chat.id] = call.message.id


@bot.message_handler(content_types=['text', 'photo', ], in_user_state=True, is_admin=True,
                     user_state='set0')
async def settings_hours(message):
    orig = users_data[message.chat.id]
    hours = message.text.split('-')
    if (len(hours) != 2) \
            or (not (hours[0].isdigit() and hours[1].isdigit())) \
            or ((int(hours[0]) > 24 or int(hours[0]) < 0) or (int(hours[1]) > 24 or int(hours[1]) < 0)):
        await bot.send_message(message.chat.id, 'Некорректный промежуток времени', reply_markup=kb(message.chat.id))
    elif current_settings.notifications_hours != hours:
        current_settings.notifications_hours = hours
        await bot.delete_message(message.chat.id, orig)
        users_data.pop(message.chat.id)
        users_state.pop(message.chat.id)
        await make_settings(message.chat.id)
    else:
        await bot.send_message(message.chat.id, 'Указанный промежуток уже установлен', reply_markup=kb(message.chat.id))


# Админские права
'''
@bot.message_handler(content_types=['text', ], in_user_state=False,
                     func=lambda message: message.text.split(' ')[0].lower() == 'админ')
async def give_admin_rights(message):
    if len(message.text.split(' ')) == 1:
        admin_db.add(message.chat.id)
        await bot.send_message(message.chat.id, 'Вы теперь админ!', reply_markup=kb(message.chat.id))
    elif len(message.text.split(' ')) == 2 and message.text.split(' ')[1].isdigit():
        try:
            username = (await bot.get_chat(message.text.split(' ')[1])).username
        except Exception as er:
            print(er)
            await bot.send_message(message.chat.id, 'Указан неверный id', reply_markup=kb(message.chat.id))
        else:
            admin_db.add(message.text.split(' ')[1])
            await bot.send_message(message.chat.id, f'@{username} теперь админ!', reply_markup=kb(message.chat.id))

@bot.message_handler(content_types=['text', ], in_user_state=False, is_admin=True,
                     func=lambda message: message.text.split(' ')[0].lower() == 'не_админ')
async def remove_admin_rights(message):
    if len(message.text.split(' ')) == 1:
        admin_db.delete(message.chat.id)
        await bot.send_message(message.chat.id, 'Вы больше не админ', reply_markup=kb(message.chat.id))
    elif len(message.text.split(' ')) == 2 and message.text.split(' ')[1].isdigit():
        try:
            username = (await bot.get_chat(message.text.split(' ')[1])).username
        except Exception as er:
            print(er)
            await bot.send_message(message.chat.id, 'Указан неверный id', reply_markup=kb(message.chat.id))
        else:
            admin_db.delete(message.text.split(' ')[1])
            await bot.send_message(message.chat.id, f'@{username} больше не админ!', reply_markup=kb(message.chat.id))
'''


@bot.message_handler(content_types=['text', ], in_user_state=False, is_admin=True,
                     func=lambda message: message.text.lower() == 'админы')
async def admin_list(message):
    admins = ''
    for admin in admin_db.get_all_detailed():
        admins += f'{admin.user_id}: {admin.username}\n'
    await bot.send_message(message.chat.id, 'Список админов:\n' + admins, reply_markup=kb(message.chat.id))


@bot.message_handler(content_types=['text', ], in_user_state=False, is_admin=True,
                     func=lambda message: message.text.lower() == 'пользователи')
async def user_list(message):
    users = ''
    users_from_db = user_db.get_all()
    await bot.send_message(message.chat.id, 'Список пользователей:', reply_markup=kb(message.chat.id))
    while users_from_db:
        for user in users_from_db[0:20]:
            subs = 'Подписан' if user.is_subscribed else 'Не подписан'
            users += f'{user.user_id}: {user.username} {subs}\n\n'
        await bot.send_message(message.chat.id, users, reply_markup=kb(message.chat.id))
        users_from_db = users_from_db[20:]
        await asyncio.sleep(0.1)


# Неизвестная команда
@bot.message_handler(content_types=['text', ], in_user_state=False)
async def unknown_command(message):
    await bot.get_chat(message.chat.id)
    await bot.send_message(message.chat.id, texts['unknown_command'], reply_markup=kb(message.chat.id))


async def sending_message(user, text, photo=False):
    # users = user_db.get_subscribed()
    if not photo:
        # for user in users:
        try:
            await bot.send_message(user.user_id, text, reply_markup=kb(user.user_id))
        except Exception as error:
            print(error)
            print(f'ОШИБКА ПРИ ОТПРАВЛЕНИИ УВЕДОМЛЕНИЯ ПОЛЬЗОВАТЕЛЮ {user.user_id}')
    else:
        # for user in users:
        try:
            await bot.send_photo(user.user_id, photo, text, reply_markup=kb(user.user_id))
        except Exception as error:
            print(error)
            print(f'ОШИБКА ПРИ ОТПРАВЛЕНИИ УВЕДОМЛЕНИЯ ПОЛЬЗОВАТЕЛЮ {user.user_id}')


async def timer():
    t = 0
    while True:
        # print('Скрипт таймера...')
        event = event_db.get_first()
        if utils.check_event(event):
            print(event)
            users = user_db.get_subscribed()
            while users:
                for user in users[0:15]:
                    asyncio.create_task(sending_message(user, event.text, event.photo))
                users = users[15:]
                await asyncio.sleep(1)
            event_db.delete(event.event_id)
        if t % 60 == 0:
            print(f'{t // 60} minutes elapsed', flush=True)

        t += 5
        # print('Скрипт таймера выполнен')
        await asyncio.sleep(5)


async def main():
    await asyncio.gather(bot.infinity_polling(), timer())


if __name__ == '__main__':
    print('Инициализация...', flush=True)
    current_settings = settings.Settings()
    while True:
        try:
            connection = sql.Connection('sqlite')
            user_db = sql.UsersDb(sql.Users, 'user_id', connection)
            admin_db = sql.AdminsDb(sql.Admins, 'user_id', connection)
            event_db = sql.EventsDb(sql.Events, 'event_id', connection)
            question_db = sql.QuestionsDb(sql.Questions, 'question_id', connection)
            certificate_db = sql.CertificateDb(sql.Certificates, 'certificate_id', connection)
            break
        except Exception as error:
            print(error)
            print('Ожидание базы данных', flush=True)
            time.sleep(5)
    print('Инициализация выполнена', flush=True)

    asyncio.run(main())
