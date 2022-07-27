import datetime

def get_datetime(ts):
    dt = datetime.datetime.fromtimestamp(int(float(ts))).strftime('%d.%m.%Y %H:%M')
    return dt

def verify(text):
    return len(text) < 512
