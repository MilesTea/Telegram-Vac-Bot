import datetime



class Event:
    def __init__(self, text: str, dt: datetime.datetime = None, ts=None, photo=None):
        if ts:
            self.ts = ts
            self.dt = datetime.datetime.fromtimestamp(ts)
        elif dt:
            self.dt = dt
            self.ts = datetime.datetime.timestamp(dt)
        else:
            raise TypeError('No arguments given. Event must have either dt or ts.')
        self.text = text

    def __str__(self):
        return f'\n{self.dt}  -  ' \
               f'{self.text}'

    def __repr__(self):
        return self.__str__()

'''
def new_event_console():
    raw_dt = input('Введите дату и время в формате дд.мм.гг чч:мм:сс\n')
    _format = '%d.%m.%y %H:%M:%S'
    dt = datetime.datetime.strptime(raw_dt, _format)
    ts = datetime.datetime.timestamp(dt)
    text = input('Введите текст события\n')
    _event = Event(text, ts=ts)
    events.append(_event)
    print(events)
'''

def new_event(ts, text, db, photo=None):
    print('Добавление события...')
    _event = Event(text, ts=ts)
    print(_event)
    if photo:
        db.add(_event.ts, _event.text, photo=photo)
    else:
        db.add(_event.ts, _event.text)
    print('Добавление события завершено')
    return _event


# def register_event(event, sort=True, db):
#     # print('\n\n\n\n\n\n\n\n')
#     # print('планирование события')
#     # events.append(event)
#     # print('сортировка событий')
#     # if sort:
#     #     sort_events()
#     # print('сортировка окончена')
#     print('начало регистрации')
#     print(event.ts, event.text)
#
#     print('конец регистрации')


def remove_event(event_id, db=None):
    print('Удаление события...')
    # events.remove(event)
    # print('||||||||||||')
    # print(event)
    # print('||||||||||||')
    db.delete(event_id)
    print('Удаление события завершено')



def make_ts(raw_dt):
    print('Формирование ts...')
    raw_dt = raw_dt.replace('.', ' ').replace(':', ' ')
    strp_dt = raw_dt.split(' ')
    print('проверка')
    if len(strp_dt) != 6:
        return None
    _numbers = []
    for number in strp_dt:
        while len(number) < 2:
            number = '0' + number
        while len(number) > 2:
            number = number[1:-1]
        _numbers.append(number)
    formatted_dt = ' '.join(_numbers)
    _format = '%d %m %y %H %M %S'
    print('конвертирование')
    try:
        dt = datetime.datetime.strptime(formatted_dt, _format)
        ts = datetime.datetime.timestamp(dt)
    except ValueError:
        return None
    print('Формирование ts завершено')
    return ts


'''
def fish_event():
    def fish(number):
        fish_number = str(random.randrange(1, number))
        if len(fish_number) == 1:
            fish_number = '0' + fish_number
        return fish_number

    raw_dt = f'{fish(26)}' \
             f'.{fish(13)}' \
             f'.{fish(22)}' \
             f' {fish(23)}' \
             f':{fish(60)}' \
             f':{fish(60)}'
    _format = '%d.%m.%y %H:%M:%S'
    dt = datetime.datetime.strptime(raw_dt, _format)
    ts = datetime.datetime.timestamp(dt)
    text = str(random.randrange(1, int('1' + '0'*random.randrange(1, 10))))
    _event = Event(text, ts=ts)
    events.append(_event)
'''


def check(db):
    print('Проверка событий...')
    now = datetime.datetime.now()
    for event in db.get_all():
        print('now:  ', now)
        print('event:', datetime.datetime.fromtimestamp(int(float(event.ts))))
        if event.ts <= now.timestamp():
            print('событие!')
            return event
    print('Проверка событий завершена')
    '''
    for event in events:
        print('now:  ', now)
        print('event:', event.dt)
        if event.ts <= now.timestamp():
            print('событие!')
            return event
    '''

def sort_events(events):
    print('Сортировка событий...')
    s_events = sorted(events, key=lambda x: x.ts)
    print('Сортировка событий завершена')
    return s_events



# def m():
    # new_event_console()
    # while True:
    #     time.sleep(5)
    #     now = datetime.datetime.now()
    #     for event in events:
    #         print('now:  ', now)
    #         print('event:', event.dt)
    #         if event.ts <= now.timestamp():
    #             print('событие!')
    #     print('\n')


# if __name__ == '__main__':
    #
    # for _ in range(10):
    #     fish_event()
    #
    # print(events)





    # опционально можно подключить к SQLite3 сделав методы у класса Event для сохранение и чтения и событий.
