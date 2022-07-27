import sql
from pprint import pprint

user_db = sql.UsersDb(sql.Users, 'user_id')
admin_db = sql.AdminsDb(sql.Admins, 'user_id')
event_db = sql.EventsDb(sql.Events, 'event_id')
question_db = sql.QuestionsDb(sql.Questions, 'question_id')
certificate_db = sql.CertificateDb(sql.Certificates, 'certificate_id')
help = '''объекты:
user_db
admin_db
event_db
question_db
certificate_db

для просмотра команд по ним используйте dir(объект)
'''
print(help)
while True:
    result = eval(input())
    if result:
        print(result)
