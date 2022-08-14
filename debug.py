import types
import sql
from pprint import pprint


def com(db):
    for func in dir(db):
        if func[0] != '_' and isinstance(getattr(db, func), types.MethodType):
            arguments_count = getattr(db, func).__code__.co_argcount
            arguments = []
            if arguments_count > 1:
                for i in range(1, arguments_count):
                    arguments.append(getattr(db, func).__code__.co_varnames[i])

            print(func, f'| Аргументы: {arguments if arguments else "Нет"}')


connection = sql.Connection('sqlite')
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
