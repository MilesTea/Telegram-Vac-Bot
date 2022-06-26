import datetime

import telebot as tb
from telebot.async_telebot import types as tbat
import curses
import telebot.async_telebot as tba
import asyncio
import events
import sql
import logging
logger = tba.logger
tba.logger.setLevel(logging.DEBUG) # Outputs debug messages to console.

token = 'TOKEN'

# users_admin = []    # под удаление
# users = []          # под удаление
users_state = {}
users_data = {}     # под удаление !!!!!!не забыть прописать удаление данных при отмена!!!!!!





# users = {'user_id': {'is_admin': True, 'is_subscribed': True, 'state': 'some_state'}}


# ДОПИСАТЬ
def kb(user_id):
    print('Клавиатура...')
    keyboard = tbat.ReplyKeyboardMarkup(True)
    if user_id in users_state:
        keyboard.row('Отмена')
    else:
        if admin_db.check(user_id):
            row = ['Новое событие', 'Все события', 'Удалить событие']
            keyboard.row(*row)
        keyboard.row('Инфо')
        if user_db.is_subscribed(user_id):
            keyboard.row('Отписаться от рассылки')
        else:
            keyboard.row('Подписаться на рассылку')
    print('Клавиатура составлена')
    return keyboard
# ДОПИСАТЬ


class IsAdmin(tba.asyncio_filters.SimpleCustomFilter):
    key = 'is_admin'

    @staticmethod
    async def check(message: tba.types.Message):
        return admin_db.check(message.chat.id)


bot = tba.AsyncTeleBot(token)

bot.add_custom_filter(IsAdmin())







def unsubscribe_conditions(message):
    if message.text.lower() == 'отписаться от рассылки':
        return True
    else:
        return False

@bot.message_handler(content_types=['text',], func=unsubscribe_conditions)
async def unsubscribe(message):
    # users.remove(message.chat.id)
    user_db.subscription(message.chat.id, False)
    await bot.send_message(message.chat.id, text='Вы были отписаны от рассылки', reply_markup=kb(message.chat.id))


def subscribe_conditions(message):
    if message.text.lower() == 'подписаться на рассылку':
        return True
    else:
        return False

@bot.message_handler(content_types=['text',], func=subscribe_conditions)
async def subscribe(message):
    # users.remove(message.chat.id)
    user_db.subscription(message.chat.id, True)
    await bot.send_message(message.chat.id, text='Вы были подписаны на рассылку', reply_markup=kb(message.chat.id))


def cancel_conditions(message):
    if message.text.lower() == 'отмена' and message.chat.id in users_state:
        return True
    else:
        return False

@bot.message_handler(content_types=['text',], func=cancel_conditions)
async def cancel(message):
    users_state.pop(message.chat.id, None)
    users_data.pop(message.chat.id, None)
    await bot.send_message(message.chat.id, text='Возврат в главное меню', reply_markup=kb(message.chat.id))


def set_event_conditions(message):
    user_state = users_state.get(message.chat.id)
    if user_state:
        if 'set' in users_state[message.chat.id]:
            return True
    return False

'''
@bot.message_handler(func=set_event_conditions, is_admin=True)
async def set_event(message):
    user_state = users_state.get(message.chat.id)
    new_state = None
    if user_state == 'set0':
        if message.text.lower() == 'отмена':
            return
        ts = events.make_ts(message.text)
        if not ts:
            await bot.send_message(message.chat.id, 'Введите корректную дату согласно образцу', reply_markup=kb(message.chat.id))
            new_state = 'set0'
        else:
            _dict = {message.chat.id: dict()}
            users_data.update(_dict)
            users_data[message.chat.id]['date'] = ts
            new_state = 'set1'
            await bot.send_message(message.chat.id, 'Введите текст события', reply_markup=kb(message.chat.id))
    elif user_state == 'set1':
        event = events.new_event(users_data[message.chat.id]['date'], message.text)
        events.register_event(event, db=event_db)
        print(events.events)
        users_state.pop(message.chat.id)
        users_data.pop(message.chat.id, None)
        await bot.send_message(message.chat.id, f'Событие запланировано на {event.dt}', reply_markup=kb(message.chat.id))

    if new_state:
        users_state[message.chat.id] = new_state
    else:
        if message.chat.id in users_state:
            users_state.pop(message.chat.id)
'''


'''
@bot.message_handler(is_admin=True)
async def admin_of_group(message): # прописать проверку в основной функции ответов, иначе 'недостаточно прав'
    user_state = users_state.get(message.chat.id)
    if not users_state:
        if message.text.lower() == 'запланируй':
            users_state[message.chat.id] = 'set0'
            await bot.send_message(message.chat.id, 'Введите дату и время в формате дд.мм.гг чч:мм:сс', reply_markup=kb(message.chat.id))
    elif user_state:
        new_state = None

        if new_state:
            users_state[message.chat.id] = new_state
        else:
            users_state.pop(message.chat.id)
'''

@bot.message_handler(content_types=['text',])
async def text_handler(message):
    user_state = users_state.get(message.chat.id)
    if not user_db.check(message.chat.id):
        user_db.add(message.chat.id)

    if not user_state:
        # Админские команды
        if admin_db.check(message.chat.id):
            if message.text.lower() == 'новое событие':
                users_state[message.chat.id] = 'set0'
                await bot.send_message(message.chat.id, 'Введите дату и время в формате дд.мм.гг чч:мм:сс',
                                       reply_markup=kb(message.chat.id))
                return
            elif message.text.lower() == 'не админ':
                admin_db.delete(message.chat.id)
                await bot.send_message(message.chat.id, 'Вы больше не админ', reply_markup=kb(message.chat.id))
                return
            elif message.text.lower() == 'все события':
                _events = event_db.get_all()
                print(_events)
                if _events:
                    for event in _events:
                        dt = datetime.datetime.fromtimestamp(int(float(event.ts)))
                        await bot.send_message(message.chat.id, f'{event.event_id}\n{dt}\n{event.text}', reply_markup=kb(message.chat.id))
                else:
                    await bot.send_message(message.chat.id, 'Нет активных событий', reply_markup=kb(message.chat.id))
                return
            elif message.text.lower() == 'удалить событие':
                users_state[message.chat.id] = 'del0'
                await bot.send_message(message.chat.id, 'Введите номер события для удаления', reply_markup=kb(message.chat.id))
                return

        # Обычные команды
        if message.text.lower() == '/start':
            if not user_db.check(message.chat.id):
                user_db.add(message.chat.id)
            await bot.send_message(message.chat.id, 'Приветствие', reply_markup=kb(message.chat.id))
        elif message.text.lower() == 'админ':
            # users_admin.append(message.chat.id)
            admin_db.add(message.chat.id)
            await bot.send_message(message.chat.id, 'Вы теперь админ!', reply_markup=kb(message.chat.id))
        elif message.text.lower() == 'инфо':
            await bot.send_message(message.chat.id, 'Здесь будет находиться базовая информация')
        else:
            await bot.send_message(message.chat.id, 'Команда не распознана', reply_markup=kb(message.chat.id))

    elif user_state:
        new_state = None
        if admin_db.check(message.chat.id):
            if user_state == 'set0':
                if message.text.lower() == 'отмена':
                    return
                ts = events.make_ts(message.text)
                if not ts:
                    await bot.send_message(message.chat.id, 'Введите корректную дату согласно образцу',
                                           reply_markup=kb(message.chat.id))
                    new_state = 'set0'
                else:
                    _dict = {message.chat.id: dict()}
                    users_data.update(_dict)
                    users_data[message.chat.id]['date'] = ts
                    new_state = 'set1'
                    await bot.send_message(message.chat.id, 'Введите текст события', reply_markup=kb(message.chat.id))
            elif user_state == 'set1':
                event = events.new_event(users_data[message.chat.id]['date'], message.text, event_db)
                users_state.pop(message.chat.id)
                users_data.pop(message.chat.id, None)
                await bot.send_message(message.chat.id, f'Событие запланировано на {event.dt}',
                                       reply_markup=kb(message.chat.id))
            elif user_state == 'del0':
                event_id = message.text
                if event_db.check(event_id):
                    event_db.delete(event_id)
                    users_state.pop(message.chat.id)
                    await bot.send_message(message.chat.id, 'Событие было удалено', reply_markup=kb(message.chat.id))
                else:
                    await bot.send_message(message.chat.id, 'Неправильный номер события', reply_markup=kb(message.chat.id))

        if new_state:
            users_state[message.chat.id] = new_state
        else:
            users_state.pop(message.chat.id)



async def timer():
    t=0
    while True:
        print('Скрипт таймера...')
        event = events.check(event_db)
        if event:
            print(event)
            events.remove_event(event.event_id, db=event_db)
            for user in user_db.get_subscribed():
                await bot.send_message(user.user_id, event.text, reply_markup=kb(user.user_id))
        text = f'{t} seconds elapsed'

        # stdscr = curses.initscr()
        # stdscr.erase()
        # stdscr.addstr(text)
        print(text)

        t += 5
        # if users:
        #     for user in users:
        #         await bot.send_message(chat_id=user, text=text)
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
    user_db = sql.UsersDb()
    admin_db = sql.AdminDb()
    event_db = sql.EventsDb()
    initialise()
    asyncio.run(main())