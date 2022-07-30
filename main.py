#!/usr/bin/python3.3
import time
from telebot import asyncio_handler_backends
from telebot.async_telebot import types as tbat
import telebot.async_telebot as tba
import asyncio
import utils
import sql


# logger = tba.logger
# tba.logger.setLevel(logging.DEBUG)

token = 'token'

# кеш состояния пользователя (для реализации внутренних команд)
users_state = {}

# кеш данных пользователя, необходимых для внутренних команд
users_data = {}

# временные сообщения, необходимы для реализации списков
temporary_messages = {}

# Составление клавиатуры на основе данных о пользователе
def kb(user_id):
    # print('Клавиатура...')
    keyboard = tbat.ReplyKeyboardMarkup(True)
    if user_id in users_state:
        keyboard.row('Отмена')
    else:
        # Админ кнопки
        if admin_db.check(user_id):
            row = ['Новое событие', 'Все события']
            keyboard.row(*row)
            # keyboard.row('Вопросы','Заявки на справки')
            keyboard.row('Вопросы')
            keyboard.row('Заявки на справки')
        else:
        # Обычные кнопки
            keyboard.row('Задать вопрос врачу профилактики')
            keyboard.row('Заказать справку')
        '''
        keyboard.row('Инфо')
        if user_db.is_subscribed(user_id):
            keyboard.row('Отписаться от рассылки')
        else:
            keyboard.row('Подписаться на рассылку')
        '''
    # print('Клавиатура составлена')
    # print(keyboard)
    return keyboard


def in_kb(ar):
    """
    Получает на вход массив вида
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
    if ar == None:
        return None
    inline_keyboard = tbat.InlineKeyboardMarkup()
    for i, row in enumerate(ar):
        buttons = []
        for button in row:
            buttons.append(tbat.InlineKeyboardButton(button[0], callback_data=button[1]))
        inline_keyboard.row(*buttons)
    # for element in ar:
    #
    #         inline_keyboard.row(tbat.InlineKeyboardButton(element[0], callback_data=element[1]))
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
            nickname = '@' + message.chat.username
            user_db.add(message.chat.id, nickname)

    async def post_process(self, message, data, exception=None):
        text = '@' + str(message.chat.username) + ': '
        if message.content_type == 'text':
            text += message.text
        elif message.content_type == 'photo':
            if message.caption:
                text += message.caption
        print(text, flush=True)



# Инициализация бота
bot = tba.AsyncTeleBot(token)
bot.add_custom_filter(IsAdmin())
bot.add_custom_filter(InUserState())
bot.add_custom_filter(UserState())
bot.setup_middleware(Middleware())



# Удаление временных сообщений
async def cleanup(user_id):
    if user_id in temporary_messages:
        if temporary_messages[user_id]:
            for message in temporary_messages[user_id]:
                await bot.delete_message(user_id, message)
        temporary_messages[user_id].clear()
    else:
        temporary_messages[user_id] = []



# Отмена
@bot.message_handler(content_types=['text', ], in_user_state=True,
                     func=lambda message: message.text.lower() == 'отмена')
async def cancel(message):
    """
    Отмена действия, обнуления состояния
    """
    users_state.pop(message.chat.id, None)
    users_data.pop(message.chat.id, None)
    await bot.send_message(message.chat.id, text='Возврат в главное меню', reply_markup=kb(message.chat.id))




async def pag(current_page, user_id, mode='q'):
    settings = {
        'q': {'entries': question_db, 'id_row': 'question_id', 'callback_code': 'q'},
        'c': {'entries': certificate_db, 'id_row': 'certificate_id', 'callback_code': 'c'}
    }
    current_settings = settings.get(mode)
    id_row = current_settings['id_row']
    cb_code = current_settings['callback_code']
    entries = current_settings['entries'].get_all()
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
        # print('отправляю...')
        buttons = in_kb([[['Ответить', f'{cb_code}a{getattr(entry, id_row)}'], ['Удалить', f'{cb_code}d{getattr(entry, id_row)}']]])
        if ('photo' in dir(entry)) and (entry.photo):
            temporary_messages[user_id].append((await bot.send_photo(user_id, entry.photo,
                                                       f'{entry.nickname}\n{dt}\n{entry.text}',
                                                       reply_markup=buttons)).id)
        else:
            temporary_messages[user_id].append((await bot.send_message(user_id, f'{entry.nickname}\n{dt}\n{entry.text}',
                                                         reply_markup=buttons)).id)
        # print('отправил')
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
async def answer_callback(call):
    await bot.answer_callback_query(call.id, '')
    await pag(int(call.data[2:]), call.message.chat.id, call.data[0])


# Удаление по inline кнопке
@bot.callback_query_handler(func=lambda call: call.data[1] == 'd')
async def delete_callback(call):
    await bot.answer_callback_query(call.id, '')
    settings = {
        'q': question_db,
        'c': certificate_db,
        'e': event_db,
    }
    result = settings[call.data[0]].delete(call.data[2:])
    if call.message.content_type == 'text':
        await bot.edit_message_text('Успешно удалено', call.message.chat.id, call.message.id)
    elif call.message.content_type == 'photo':
        await bot.edit_message_caption('Успешно удалено', call.message.chat.id, call.message.id)




# Ответ на вопрос
@bot.callback_query_handler(func=lambda call: call.data[0:2] == 'qa')
async def question_callback(call):
    question = question_db.get(call.data[2:])
    await bot.answer_callback_query(call.id, '')  # Бот принимает сообщение
    if not question:
        await bot.send_message(call.message.chat.id, 'На этот вопрос уже дали ответ',
                               reply_markup=kb(call.message.chat.id))
        users_state.pop(call.message.chat.id)
        users_data.pop(call.message.chat.id)
    else:
        users_data[call.message.chat.id] = {'user_id': call.data[2:], 'reply_id': call.message.id}
        users_state[call.message.chat.id] = 'question_answer'
        await bot.send_message(call.message.chat.id, f'Введите ваш ответ на вопрос от {question.nickname}', reply_markup=kb(call.message.chat.id))
        # await bot.answer_callback_query(call.id, f'{call.data}\n{call.message.text}') # Принимает и отправляет ответ(сверху)


@bot.message_handler(content_types=['text', 'photo',], in_user_state=True, is_admin=True,
                     user_state='question_answer')
async def question_answer0(message):
    question = question_db.get(users_data[message.chat.id]['user_id'])
    if not question:
        await bot.send_message(message.chat.id, 'На этот вопрос уже дали ответ',
                               reply_markup=kb(message.chat.id))
        users_state.pop(message.chat.id)
        users_data.pop(message.chat.id)
    else:
        users_state.pop(message.chat.id)
        users_data.pop(message.chat.id)
        question_db.delete(question.question_id)
        # print('Формирую отклик')
        answer_start = 'Ответ врача на ваш вопрос:\n'
        try:
            if message.content_type == 'text':
                await bot.send_message(question.user_id, answer_start+message.text, reply_markup=kb(question.user_id))
            elif message.content_type == 'photo':
                await bot.send_photo(question.user_id, caption=answer_start+message.caption, photo=message.photo[-1].file_id,
                                     reply_markup=kb(question.user_id))
            await bot.send_message(message.chat.id, 'Ваш ответ отправлен пользователю',
                                   reply_markup=kb(message.chat.id))
        except:
            await bot.send_message(message.chat.id, 'Ошибка при отправке ответа пользователю',
                                   reply_markup=kb(message.chat.id))





# Ответ на заявку
@bot.callback_query_handler(func=lambda call: call.data[0:2] == 'ca')
async def certificate_callback(call):
    certificate = certificate_db.get(call.data[2:])
    await bot.answer_callback_query(call.id, '')  # Бот принимает сообщение
    if not certificate:
        await bot.send_message(call.message.chat.id, 'На эту заявку уже дали ответ',
                               reply_markup=kb(call.message.chat.id))
        users_state.pop(call.message.chat.id)
        users_data.pop(call.message.chat.id)
    else:
        users_data[call.message.chat.id] = call.data[2:]
        users_state[call.message.chat.id] = 'certificate_answer'
        await bot.send_message(call.message.chat.id, f'Введите ваш ответ на заявку от {certificate.nickname}', reply_markup=kb(call.message.chat.id))
        # await bot.answer_callback_query(call.id, f'{call.data}\n{call.message.text}') # Принимает и отправляет ответ(сверху)


@bot.message_handler(content_types=['text', 'photo',], in_user_state=True, is_admin=True,
                     user_state='certificate_answer')
async def certificate_answer0(message):
    certificate = certificate_db.get(users_data[message.chat.id])
    if not certificate:
        await bot.send_message(message.chat.id, 'На эту заявку уже дали ответ',
                               reply_markup=kb(message.chat.id))
    else:
        answer_start = 'Врач рассмотрел вашу заявку:\n'
        if message.content_type == 'photo':
            await bot.send_message(certificate.user_id, answer_start + message.caption,
                                   reply_markup=kb(certificate.certificate_id))
            await bot.send_photo(certificate.user_id, message.photo[-1].file_id,
                                 reply_markup=kb(certificate.certificate_id))
        else:
            await bot.send_message(certificate.user_id, answer_start+message.text, reply_markup=kb(certificate.certificate_id))
        users_state.pop(message.chat.id)
        users_data.pop(message.chat.id)
        certificate_db.delete(certificate.certificate_id)
        await bot.send_message(message.chat.id, 'Ваш ответ отправлен пользователю',
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
@bot.message_handler(content_types=['text',], in_user_state=False,
                     func=lambda message: message.text.lower() == 'задать вопрос врачу профилактики')
async def question(message):
    # if question_db.count_by_user(message.chat.id) < 1:
    if not question_db.check(message.chat.id):
        users_state[message.chat.id] = 'question0'
        await bot.send_message(message.chat.id, 'Введите свой вопрос в одном сообщении.',
                               reply_markup=kb(message.chat.id))
    else:
        await bot.send_message(message.chat.id, 'Ваш вопрос уже находится в обработке',
                               reply_markup=kb(message.chat.id))

@bot.message_handler(content_types=['text',], in_user_state=True, user_state='question0')
async def question0(message):
    text = message.text if message.content_type == 'text' else message.caption
    if not utils.verify(text):
        await bot.send_message(message.chat.id, 'Слишком длинное сообщение', reply_markup=kb(message.chat.id))
    else:
        username = '@' + message.chat.username
        if message.content_type == 'text':
            question_db.add(message.chat.id, username, time.time(), text=text)
        # elif message.content_type == 'photo':
        #     question_db.add(message.chat.id, username, time.time(), text=text, photo=message.photo[-1].file_id)
        users_state.pop(message.chat.id)
        await bot.send_message(message.chat.id, 'Ваш вопрос был отправлен',
                               reply_markup=kb(message.chat.id))



# Запрос справки
@bot.message_handler(content_types=['text',], in_user_state=False,
                     func=lambda message: message.text.lower() == 'заказать справку')
async def certificate(message):
    if certificate_db.count_by_user(message.chat.id) < 2:
    # if not certificate_db.check(message.chat.id):
        users_state[message.chat.id] = 'certificate0'
        await bot.send_message(message.chat.id, 'Введите ФИО, класс ребёнка, и название необходимой справки',
                               reply_markup=kb(message.chat.id))
    else:
        await bot.send_message(message.chat.id, 'Вы можете запросить только 2 справки за раз',
                               reply_markup=kb(message.chat.id))

@bot.message_handler(content_types=['text',], in_user_state=True, user_state='certificate0')
async def certificate0(message):
    text = message.text
    if not utils.verify(text):
        await bot.send_message(message.chat.id, 'Слишком длинное сообщение', reply_markup=kb(message.chat.id))
    else:
        username = '@' + message.chat.username
        if message.content_type == 'text':
            certificate_db.add(message.chat.id, username, time.time(), text=text)
        # elif message.content_type == 'photo':
        #     certificate_db.add(message.chat.id, username, time.time(), text=text, photo=message.photo[-1].file_id)
        users_state.pop(message.chat.id)
        await bot.send_message(message.chat.id, 'Ваше заявление на справку было отправлено',
                               reply_markup=kb(message.chat.id))



# Стартовое сообщение
@bot.message_handler(content_types=['text', ], in_user_state=False,
                     func=lambda message: message.text.lower() == '/start')
async def start(message):
    await bot.send_message(message.chat.id, 'Приветствие',
                           reply_markup=kb(message.chat.id))



# просмотр вопросов
@bot.message_handler(content_types=['text', ], in_user_state=False, is_admin=True,
                     func=lambda message: message.text.lower() == 'вопросы')
async def all_questions(message):
    questions = question_db.check()
    # print(questions)
    if questions:
        await pag(1, message.chat.id)
    else:
        await bot.send_message(message.chat.id, 'Нет активных вопросов', reply_markup=kb(message.chat.id))




# просмотр заявок на справки
@bot.message_handler(content_types=['text', ], in_user_state=False, is_admin=True,
                     func=lambda message: message.text.lower() == 'заявки на справки')
async def all_certificates(message):
    certificates = certificate_db.check()
    if certificates:
        await pag(1, message.chat.id, 'c')
    else:
        await bot.send_message(message.chat.id, 'Нет активных заявок', reply_markup=kb(message.chat.id))





# просмотр событий
@bot.message_handler(content_types=['text', ], in_user_state=False, is_admin=True,
                     func=lambda message: message.text.lower() == 'все события')
async def all_events(message):
    _events = event_db.get_all()
    # print(_events)
    if _events:
        for event in _events:
            # dt = datetime.datetime.fromtimestamp(int(float(event.ts)))
            dt = utils.get_datetime(event.ts)
            if event.photo:
                await bot.send_photo(message.chat.id, event.photo, f'{dt}\n{event.text}',
                                       reply_markup=in_kb([[['Удалить', f'ed{event.event_id}']]]))
            else:
                await bot.send_message(message.chat.id, f'{dt}\n{event.text}',
                                       reply_markup=in_kb([[['Удалить', f'ed{event.event_id}']]]))
            await asyncio.sleep(0.1)
    else:
        await bot.send_message(message.chat.id, 'Нет активных событий', reply_markup=kb(message.chat.id))



# Новое событие
@bot.message_handler(content_types=['text', ], in_user_state=False, is_admin=True,
                     func=lambda message: message.text.lower() == 'новое событие')
async def new_event(message):
    users_state[message.chat.id] = 'set0'
    await bot.send_message(message.chat.id, 'Введите дату и время в формате дд.мм.гг чч:мм',
                           reply_markup=kb(message.chat.id))

@bot.message_handler(content_types=['text', ], in_user_state=True , user_state='set0', is_admin=True)
async def new_event_0(message):
    ts = utils.make_ts(message.text)
    if not ts:
        await bot.send_message(message.chat.id, 'Введите корректную дату согласно образцу',
                               reply_markup=kb(message.chat.id))
        users_state[message.chat.id] = 'set0'
    else:
        _dict = {message.chat.id: dict()}
        users_data.update(_dict)
        users_data[message.chat.id]['date'] = ts
        users_state[message.chat.id] = 'set1'
        await bot.send_message(message.chat.id, 'Введите текст события. Также вы можете прикрепить картинку', reply_markup=kb(message.chat.id))

@bot.message_handler(content_types=['text', 'photo', ], in_user_state=True , user_state='set1', is_admin=True)
async def new_event_1(message):
    ts = users_data[message.chat.id]["date"]
    if message.content_type == 'text':
        event_db.add(ts, message.text)
        users_state.pop(message.chat.id)
        users_data.pop(message.chat.id, None)
        await bot.send_message(message.chat.id, f'Событие запланировано на {utils.get_datetime(ts)}',
                               reply_markup=kb(message.chat.id))
    elif message.content_type == 'photo':
        event_db.add(ts, message.caption, photo=message.photo[-1].file_id)
        users_state.pop(message.chat.id)
        users_data.pop(message.chat.id, None)
        await bot.send_message(message.chat.id, f'Событие запланировано на {utils.get_datetime(ts)}',
                               reply_markup=kb(message.chat.id))



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
    for admin in admin_db.get_all():
        try:
            nickname = user_db.get(admin.user_id).nickname
        except Exception as er:
            nickname = 'Ошибка при получении ника'
        admins += f'{admin.user_id}: {nickname}\n'
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
            users += f'{user.user_id}: {user.nickname} {subs}\n\n'
        await bot.send_message(message.chat.id, users, reply_markup=kb(message.chat.id))
        users_from_db = users_from_db[20:]
        await asyncio.sleep(0.1)





# Неизвестная команда
@bot.message_handler(content_types=['text', ], in_user_state=False)
async def unknown_command(message):
    a = await bot.get_chat(message.chat.id)
    await bot.send_message(message.chat.id, 'Команда не распознана', reply_markup=kb(message.chat.id))




async def sending_message(user, text, photo=False):
    # users = user_db.get_subscribed()
    if not photo:
        # for user in users:
            try:
                await bot.send_message(user.user_id, text, reply_markup=kb(user.user_id))
            except:
                print(f'ОШИБКА ПРИ ОТПРАВЛЕНИИ УВЕДОМЛЕНИЯ ПОЛЬЗОВАТЕЛЮ {user.user_id}')
    else:
        # for user in users:
            try:
                await bot.send_photo(user.user_id, photo, text, reply_markup=kb(user.user_id))
            except:
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






def initialise():
    print('Инициализация...', flush=True)
    global user_db
    global admin_db
    global event_db
    global question_db
    global certificate_db
    while True:
        try:
            user_db = sql.UsersDb(sql.Users, 'user_id')
            admin_db = sql.AdminsDb(sql.Admins, 'user_id')
            event_db = sql.EventsDb(sql.Events, 'event_id')
            question_db = sql.QuestionsDb(sql.Questions, 'question_id')
            certificate_db = sql.CertificateDb(sql.Certificates, 'certificate_id')
            break
        except:
            print('Ожидание базы данных', flush=True)
            time.sleep(5)
    print('Инициализация выполнена', flush=True)


async def main():
    await asyncio.gather(bot.infinity_polling(), timer())


if __name__ == '__main__':
    initialise()
    asyncio.run(main())
