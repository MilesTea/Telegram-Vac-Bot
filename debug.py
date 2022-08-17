import types
import sql
import os
import json
from pprint import pprint


def com(_db):
    for func in dir(_db):
        if func[0] != '_' and isinstance(getattr(_db, func), types.MethodType):
            arguments_count = getattr(_db, func).__code__.co_argcount
            arguments = []
            if arguments_count > 1:
                for i in range(1, arguments_count):
                    arguments.append(getattr(_db, func).__code__.co_varnames[i])

            print(func, f'| Аргументы: {arguments if arguments else "Нет"}')


if 'connection.json' in os.listdir(os.getcwd()):
    with open('connection.json', 'r', encoding='utf-8') as file:
        connection = json.load(file)
else:
    raise Exception('Невозможно подключиться к базе данных. Сначала запустите бота')
db, address = connection['db'], connection['address']
connection = sql.Connection(db, address)
users = sql.UsersDb(sql.Users, 'user_id', connection)
admins = sql.AdminsDb(sql.Admins, 'user_id', connection)
events = sql.EventsDb(sql.Events, 'event_id', connection)
questions = sql.QuestionsDb(sql.Questions, 'question_id', connection)
certificates = sql.CertificateDb(sql.Certificates, 'certificate_id', connection)
message = '''объекты:
users
admins
events
questions
certificates

для просмотра команд по ним используйте com(объект)
'''
print(message)
while True:
    try:
        result = eval(input())
        if result:
            pprint(result)
    except Exception as er:
        print(er)
