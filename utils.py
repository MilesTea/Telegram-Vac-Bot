import datetime
import re


def get_datetime(ts):
    dt = datetime.datetime.fromtimestamp(int(float(ts))).strftime('%d.%m.%Y %H:%M')
    return dt


def verify(text):
    return len(text) < 512


ts_pattern = r"([0-9]{1,2})[\. ]+([0-9]{1,2})[\. ]+([0-9]{1,4}) +([0-9]{1,2})[: ]+([0-9]{1,2})"


def make_ts(raw_dt):
    match = re.search(ts_pattern, raw_dt)
    if not match:
        return None
    list_dt = list(match.groups())
    if len(list_dt[2]) < 4:
        list_dt[2] = '20' + list_dt[2]
    for i, val in enumerate(list_dt):
        list_dt[i] = int(val)
    dt = datetime.datetime(year=list_dt[2], month=list_dt[1], day=list_dt[0], hour=list_dt[3], minute=list_dt[4])
    return dt.timestamp()


def check_event(event):
    if event:
        now = datetime.datetime.now()
        if event.ts <= now.timestamp():
            return True


def in_time_frame(state, hour_from, hour_to):
    if not state:
        return False
    time_now = datetime.datetime.now().time()
    time_from = datetime.time(hour=int(hour_from))
    if hour_to == 24 or hour_to == '24':
        time_to = datetime.time(hour=23, minute=59, second=59)
    else:
        time_to = datetime.time(hour=int(hour_to))

    if time_from < time_to:
        if time_from < time_now < time_to:
            return True
        else:
            return False
    if time_from > time_to:
        if time_now > time_from or time_now < time_to:
            return True
        else:
            return False
