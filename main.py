import datetime
import time
from pprint import pprint
import telebot
from telebot import asyncio_handler_backends
from telebot.async_telebot import types as tbat
import telebot.async_telebot as tba
import asyncio
import events
import sql
import logging

logger = tba.logger
tba.logger.setLevel(logging.DEBUG)

token = 'token'

''' Кнопки
фио + класс => админу         (ссылка на тг) / (отдельный интерфейс, как с событиями + бд)

Заказать справку;             вопрос врачу
'''
'''Доп админ кнопки
Вопросы; Заявки на справку; Настройки(опционально; настройка уведомлений админу)
'''
'''Вопросы врачу в админ панели
список {
    имя дата
    вопрос
    {inline клавиатура: Ответить(возможно forced reply); Закрыть}
}
'''
'''Вопрос врачу со стороны пользователя
бот: Напишите вопрос, который вы хотели бы задать врачу
юзер: какой-то вопрос
бот: Ваш вопрос был направлен врачу, ожидайте ответа (внимание, врач отвечает на вопросы с понедельника...)
'''


# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# ИЗУЧИТЬ https://stackoverflow.com/questions/45405369/pytelegrambotapi-how-to-save-state-in-next-step-handler-solution
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!


# кеш состояния пользователя (для реализации внутренних команд)
users_state = {}

# кеш данных пользователя, необходимых для внутренних команд
users_data = {}




# Составление клавиатуры на основе данных о пользователе
def kb(user_id):
    print('Клавиатура...')
    keyboard = tbat.ReplyKeyboardMarkup(True)
    if user_id in users_state:
        keyboard.row('Отмена')
    else:
        # Админ кнопки
        if admin_db.check(user_id):
            row = ['Новое событие', 'Все события', 'Удалить событие']
            keyboard.row(*row)
            keyboard.row('Вопросы','Заявки на справки')

        # Обычные кнопки
        keyboard.row('Задать вопрос врачу')
        keyboard.row('Заказать справку')
        '''
        keyboard.row('Инфо')
        if user_db.is_subscribed(user_id):
            keyboard.row('Отписаться от рассылки')
        else:
            keyboard.row('Подписаться на рассылку')
        '''
    print('Клавиатура составлена')
    print(keyboard)
    return keyboard


def in_kb(text, data):
    inline_keyboard = tbat.InlineKeyboardMarkup()
    inline_keyboard.add(tbat.InlineKeyboardButton(text, callback_data=data))
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
            user_db.add(message.chat.id)

    async def post_process(self, message, data, exception=None):
        # print(data['foo'])
        # if exception: # check for exception
        #     print(exception)
        pass



# Инициализация бота
bot = tba.AsyncTeleBot(token)
bot.add_custom_filter(IsAdmin())
bot.add_custom_filter(InUserState())
bot.add_custom_filter(UserState())
bot.setup_middleware(Middleware())



@bot.callback_query_handler(func=lambda call: call.data[0] == 'q')
async def question_callback(call):
    # pprint(call)
    # question = question_db.get(call.data[1:])
    await bot.answer_callback_query(call.id, '') # Бот принимает сообщение
    # markup = tbat.ForceReply(selective=False)
    users_data[call.message.chat.id] = call.data[1:]
    users_state[call.message.chat.id] = 'question_answer'
    await bot.send_message(call.message.chat.id, 'Введите ваш ответ', reply_markup=kb(call.message.chat.id))
    # await bot.answer_callback_query(call.id, f'{call.data}\n{call.message.text}') # Принимает и отправляет ответ(сверху)


@bot.message_handler(content_types=['text', 'photo',], in_user_state=True, is_admin=True,
                     user_state='question_answer')
async def question_answer0(message):
    question = question_db.get(users_data[message.chat.id])
    answer_start = 'Ответ врача на ваш вопрос:\n'
    if message.content_type == 'text':
        await bot.send_message(question.question_id, answer_start+message.text, reply_markup=kb(question.question_id))
    elif message.content_type == 'photo':
        await bot.send_photo(question.question_id, caption=answer_start+message.caption, photo=message.photo[-1].file_id,
                             reply_markup=kb(question.question_id))
    users_state.pop(message.chat.id)
    users_data.pop(message.chat.id)
    question_db.delete(question.question_id)
    await bot.send_message(message.chat.id, 'Ваш ответ отправлен пользователю',
                           reply_markup=kb(message.chat.id))





@bot.callback_query_handler(func=lambda call: call.data[0] == 'c')
async def certificate_callback(call):
    await bot.answer_callback_query(call.id, '') # Бот принимает сообщение
    users_data[call.message.chat.id] = call.data[1:]
    users_state[call.message.chat.id] = 'certificate_answer'
    await bot.send_message(call.message.chat.id, 'Введите ваш ответ', reply_markup=kb(call.message.chat.id))
    # await bot.answer_callback_query(call.id, f'{call.data}\n{call.message.text}') # Принимает и отправляет ответ(сверху)


@bot.message_handler(content_types=['text', 'photo',], in_user_state=True, is_admin=True,
                     user_state='certificate_answer')
async def certificate_answer0(message):
    certificate = certificate_db.get(users_data[message.chat.id])
    answer_start = 'Врач рассмотрел вашу заявку:\n'
    await bot.send_message(certificate.certificate_id, answer_start+message.text, reply_markup=kb(certificate.certificate_id))
    users_state.pop(message.chat.id)
    users_data.pop(message.chat.id)
    certificate_db.delete(certificate.certificate_id)
    await bot.send_message(message.chat.id, 'Ваш ответ отправлен пользователю',
                           reply_markup=kb(message.chat.id))






# Тестовая информация
@bot.message_handler(content_types=['text', ], in_user_state=False,
                     func=lambda message: message.text.lower() == 'тест')
async def info(message):
    await bot.send_message(message.chat.id, 'тест',
                           reply_markup=kb(message.chat.id, True))


# Отписка
@bot.message_handler(content_types=['text', ], in_user_state=False,
                     func=lambda message: message.text.lower() == 'отписаться от рассылки')
async def unsubscribe(message):
    """
    Отписка от рассылки
    """
    user_db.subscription(message.chat.id, False)
    await bot.send_message(message.chat.id, text='Вы были отписаны от рассылки', reply_markup=kb(message.chat.id))


# Подписка
@bot.message_handler(content_types=['text', ], in_user_state = False,
                     func=lambda message: message.text.lower() == 'подписаться на рассылку')
async def subscribe(message):
    """
    Подписка на рассылку
    """
    user_db.subscription(message.chat.id, True)
    await bot.send_message(message.chat.id, text='Вы были подписаны на рассылку', reply_markup=kb(message.chat.id))



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



# Инфо
@bot.message_handler(content_types=['text', ], in_user_state=False,
                     func=lambda message: message.text.lower() == 'инфо')
async def info(message):
    await bot.send_message(message.chat.id, 'Здесь будет находиться базовая информация',
                           reply_markup=kb(message.chat.id))


# Задать вопрос
@bot.message_handler(content_types=['text',], in_user_state=False,
                     func=lambda message: message.text.lower() == 'задать вопрос врачу')
async def question(message):
    if not question_db.check(message.chat.id):
        users_state[message.chat.id] = 'question0'
        await bot.send_message(message.chat.id, 'Введите свой вопрос в одном сообщении. '
                                                'Вы также можете прикрепитьк вопросу изображение',
                               reply_markup=kb(message.chat.id))
    else:
        await bot.send_message(message.chat.id, 'Ваш вопрос уже находится в обработке',
                               reply_markup=kb(message.chat.id))

@bot.message_handler(content_types=['text', 'photo',], in_user_state=True, user_state='question0')
async def question0(message):
    if message.content_type == 'text':
        question_db.add(message.chat.id, time.time(), text=message.text)
    elif message.content_type == 'photo':
        question_db.add(message.chat.id, time.time(), text=message.caption, photo=message.photo[-1].file_id)
    users_state.pop(message.chat.id)
    await bot.send_message(message.chat.id, 'Ваш вопрос был отправлен',
                           reply_markup=kb(message.chat.id))



# Запрос справки
@bot.message_handler(content_types=['text',], in_user_state=False,
                     func=lambda message: message.text.lower() == 'заказать справку')
async def certificate(message):
    if not certificate_db.check(message.chat.id):
        users_state[message.chat.id] = 'certificate0'
        await bot.send_message(message.chat.id, 'Введите необходимые данные для справки',
                               reply_markup=kb(message.chat.id))
    else:
        await bot.send_message(message.chat.id, 'Временное ограничение на 1 справку за раз',
                               reply_markup=kb(message.chat.id))

@bot.message_handler(content_types=['text',], in_user_state=True, user_state='certificate0')
async def certificate0(message):
    if message.content_type == 'text':
        certificate_db.add(message.chat.id, time.time(), text=message.text)
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
    questions = question_db.get_all()
    print(questions)
    if questions:
        for question in questions:
            dt = datetime.datetime.fromtimestamp(int(float(question.ts)))
            if question.photo:
                await bot.send_photo(message.chat.id, question.photo, f'{question.question_id}\n{dt}\n{question.text}',
                                       reply_markup=in_kb('Ответить', f'q{question.question_id}'))
            else:
                await bot.send_message(message.chat.id, f'{question.question_id}\n{dt}\n{question.text}',
                                       reply_markup=in_kb('Ответить', f'q{question.question_id}'))
    else:
        await bot.send_message(message.chat.id, 'Нет активных вопросов', reply_markup=kb(message.chat.id))




# просмотр заявок на справки
@bot.message_handler(content_types=['text', ], in_user_state=False, is_admin=True,
                     func=lambda message: message.text.lower() == 'заявки на справки')
async def all_certificates(message):
    certificates = certificate_db.get_all()
    if certificates:
        for certificate in certificates:
            dt = datetime.datetime.fromtimestamp(int(float(certificate.ts)))
            await bot.send_message(message.chat.id, f'{certificate.certificate_id}\n{dt}\n{certificate.text}',
                                       reply_markup=in_kb('Ответить', f'c{certificate.certificate_id}'))
    else:
        await bot.send_message(message.chat.id, 'Нет активных заявок', reply_markup=kb(message.chat.id))





# просмотр событий
@bot.message_handler(content_types=['text', ], in_user_state=False, is_admin=True,
                     func=lambda message: message.text.lower() == 'все события')
async def all_events(message):
    _events = event_db.get_all()
    print(_events)
    if _events:
        for event in _events:
            dt = datetime.datetime.fromtimestamp(int(float(event.ts)))
            if event.photo:
                await bot.send_photo(message.chat.id, event.photo, f'{event.event_id}\n{dt}\n{event.text}',
                                       reply_markup=kb(message.chat.id))
            else:
                await bot.send_message(message.chat.id, 'подгрузка без картинки...', reply_markup=kb(message.chat.id))
                await bot.send_message(message.chat.id, f'{event.event_id}\n{dt}\n{event.text}',
                                       reply_markup=kb(message.chat.id))
    else:
        await bot.send_message(message.chat.id, 'Нет активных событий', reply_markup=kb(message.chat.id))



# Новое событие
@bot.message_handler(content_types=['text', ], in_user_state=False, is_admin=True,
                     func=lambda message: message.text.lower() == 'новое событие')
async def new_event(message):
    users_state[message.chat.id] = 'set0'
    await bot.send_message(message.chat.id, 'Введите дату и время в формате дд.мм.гг чч:мм:сс',
                           reply_markup=kb(message.chat.id))

@bot.message_handler(content_types=['text', ], in_user_state=True , user_state='set0', is_admin=True)
async def new_event_0(message):
    ts = events.make_ts(message.text)
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
    if message.content_type == 'text':
        event = events.new_event(users_data[message.chat.id]['date'], message.text, event_db)
        users_state.pop(message.chat.id)
        users_data.pop(message.chat.id, None)
        await bot.send_message(message.chat.id, f'Событие запланировано на {event.dt}',
                               reply_markup=kb(message.chat.id))
    elif message.content_type == 'photo':
        event = events.new_event(users_data[message.chat.id]['date'], message.caption, event_db, message.photo[-1].file_id)
        users_state.pop(message.chat.id)
        users_data.pop(message.chat.id, None)
        await bot.send_message(message.chat.id, f'Событие запланировано на {event.dt}',
                               reply_markup=kb(message.chat.id))



# Удалить событие
@bot.message_handler(content_types=['text', ], in_user_state=False, is_admin=True,
                     func=lambda message: message.text.lower() == 'удалить событие')
async def delete_event(message):
    users_state[message.chat.id] = 'del0'
    await bot.send_message(message.chat.id, 'Введите номер события для удаления',
                           reply_markup=kb(message.chat.id))

@bot.message_handler(content_types=['text', ], in_user_state=True , user_state='del0', is_admin=True)
async def delete_event_0(message):
    event_id = message.text
    if event_db.check(event_id):
        event_db.delete(event_id)
        users_state.pop(message.chat.id)
        await bot.send_message(message.chat.id, 'Событие было удалено', reply_markup=kb(message.chat.id))
    else:
        await bot.send_message(message.chat.id, 'Неправильный номер события',
                               reply_markup=kb(message.chat.id))



# Админские права
@bot.message_handler(content_types=['text', ], in_user_state=False,
                     func=lambda message: message.text.split(' ')[0].lower() == 'админ')
async def give_admin_rights(message):
    if len(message.text.split(' ')) == 1:
        admin_db.add(message.chat.id)
        await bot.send_message(message.chat.id, 'Вы теперь админ!', reply_markup=kb(message.chat.id))
    elif len(message.text.split(' ')) == 2 and message.text.split(' ')[1].isdigit():
        try:
            username  = (await bot.get_chat(message.text.split(' ')[1])).username
        except Exception as er:
            print(er)
            await bot.send_message(message.chat.id, 'Указан неверный id', reply_markup=kb(message.chat.id))
        else:
            admin_db.add(message.text.split(' ')[1])
            await bot.send_message(message.chat.id, f'@{username} теперь админ!', reply_markup=kb(message.chat.id))

@bot.message_handler(content_types=['text', ], in_user_state=False, is_admin=True,
                     func=lambda message: message.text.lower() == 'не админ')
async def remove_admin_rights(message):
    admin_db.delete(message.chat.id)
    await bot.send_message(message.chat.id, 'Вы больше не админ', reply_markup=kb(message.chat.id))

@bot.message_handler(content_types=['text', ], in_user_state=False, is_admin=True,
                     func=lambda message: message.text.lower() == 'админы')
async def admin_list(message):
    admins = ''
    for admin in admin_db.get_all():
        try:
            username =  '@' + (await bot.get_chat(admin.user_id)).username
        except Exception as er:
            username = 'Ошибка при получении ника'
        admins += f'{admin.user_id}: {username}\n'
    await bot.send_message(message.chat.id, 'Список админов:\n' + admins, reply_markup=kb(message.chat.id))

@bot.message_handler(content_types=['text', ], in_user_state=False, is_admin=True,
                     func=lambda message: message.text.lower() == 'пользователи')
async def user_list(message):
    users = ''
    for user in user_db.get_all():
        try:
            username =  '@' + (await bot.get_chat(user.user_id)).username
        except Exception as er:
            username = 'Ошибка при получении ника'
        users += f'{user.user_id}: {username}  {user.is_subscribed}\n\n'
    await bot.send_message(message.chat.id, 'Список пользователей:\n' + users, reply_markup=kb(message.chat.id))





# Неизвестная команда
@bot.message_handler(content_types=['text', ], in_user_state=False)
async def unknown_command(message):
    a = await bot.get_chat(message.chat.id)
    await bot.send_message(message.chat.id, 'Команда не распознана', reply_markup=kb(message.chat.id))




async def sending_messages(text, photo=False):
    if not photo:
        for user in user_db.get_subscribed():
            await bot.send_message(user.user_id, text, reply_markup=kb(user.user_id))
            await asyncio.sleep(0.2)
    else:
        for user in user_db.get_subscribed():
            await bot.send_photo(user.user_id, photo, text, reply_markup=kb(user.user_id))
            await asyncio.sleep(0.2)


async def timer():
    t = 0
    while True:
        print('Скрипт таймера...')
        event = events.check(event_db)
        if event:
            print(event)
            events.remove_event(event.event_id, db=event_db)
            if not event.photo:
                await sending_messages(event.text)
            else:
                await sending_messages(event.text, event.photo)

        text = f'{t} seconds elapsed'
        print(text)

        t += 5
        print('Скрипт таймера выполнен')
        await asyncio.sleep(5)


@bot.my_chat_member_handler()
async def bruh(b):
    print(b)


def initialise():
    print('Инициализация...')
    print('Инициализация выполнена')


async def main():
    await asyncio.gather(bot.infinity_polling(), timer())


if __name__ == '__main__':
    user_db = sql.UsersDb(sql.Users, 'user_id')
    admin_db = sql.AdminsDb(sql.Admins, 'user_id')
    event_db = sql.EventsDb(sql.Events, 'event_id')
    question_db = sql.QuestionsDb(sql.Questions, 'question_id')
    certificate_db = sql.CertificateDb(sql.Certificates, 'certificate_id')
    initialise()
    asyncio.run(main())
