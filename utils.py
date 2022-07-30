import datetime


def get_datetime(ts):
    dt = datetime.datetime.fromtimestamp(int(float(ts))).strftime('%d.%m.%Y %H:%M')
    return dt


def verify(text):
    return len(text) < 512


def make_ts(raw_dt):
    # print('Формирование ts...')
    raw_dt = raw_dt.replace('.', ' ').replace(':', ' ')
    strp_dt = raw_dt.split(' ')
    # print('проверка')
    if len(strp_dt) != 5:
        return None
    _numbers = []
    for number in strp_dt:
        while len(number) < 2:
            number = '0' + number
        while len(number) > 2:
            number = number[1:]
        _numbers.append(number)
    formatted_dt = ' '.join(_numbers)
    _format = '%d %m %y %H %M'
    # print('конвертирование')
    try:
        dt = datetime.datetime.strptime(formatted_dt, _format)
        ts = datetime.datetime.timestamp(dt)
    except ValueError:
        return None
    return ts


def check_event(event):
    if event:
        now = datetime.datetime.now()
        if event.ts <= now.timestamp():
            return True