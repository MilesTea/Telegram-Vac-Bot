import os
import random
# import time
import sqlalchemy as sq
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, relationship

working_dir = os.getcwd()


connections = {
    'sqlite': f'sqlite:///{working_dir}/database.db',
    'postgresql': f'postgresql+psycopg2://login:password@postgres:5432/telebot'
}

Base = declarative_base()


class Connection:
    def __init__(self, connection_mode):
        self.engine = sq.create_engine(connections[connection_mode])


class BaseDb:
    def __init__(self, table, id_row, db_connection: Connection):
        self.engine = db_connection.engine

        Base.metadata.create_all(self.engine)
        self.table = table
        self.id_row = id_row

    def add(self, entry_id, **kwargs):
        with Session(self.engine) as self.session:
            try:
                new_entry = self.table(**{self.id_row: entry_id, **kwargs})
                self.session.add(new_entry)
                self.session.commit()
            except Exception as error:
                print('cant add' + str(self.__class__) + str(entry_id))
                print(error)

    def delete(self, entry_id):
        with Session(self.engine) as self.session:
            try:
                self.session.query(self.table).filter(getattr(self.table, self.id_row) == entry_id).delete()
                self.session.commit()
            except Exception as error:
                print('cant delete' + str(self.__class__) + str(entry_id))
                print(error)

    def delete_all(self):
        with Session(self.engine) as self.session:
            try:
                self.session.query(self.table).delete()
                self.session.commit()
            except Exception as error:
                print('cant delete' + str(self.__class__))
                print(error)

    def check(self, entry_id=None):
        with Session(self.engine) as self.session:
            try:
                if entry_id:
                    if self.session.get(self.table, entry_id):
                        return True
                    else:
                        return False
                else:
                    if self.session.query(self.table).first():
                        return True
                    else:
                        return False
            except Exception as error:
                print('cant check:' + str(self.__class__) + str(entry_id))
                print(error)

    def get(self, entry_id):
        with Session(self.engine) as self.session:
            try:
                result = self.session.get(self.table, entry_id)
                # print(result)
                return result
            except Exception as error:
                print('cant get:' + str(self.__class__) + str(entry_id))
                print(error)

    def get_all(self):
        with Session(self.engine) as self.session:
            try:
                result = self.session.query(self.table).all()
                # print(result)
                return result
            except Exception as error:
                print('cant get:' + str(self.__class__))
                print(error)

    def is_on(self):
        with Session(self.engine) as self.session:
            try:
                self.session.query(self.table).first()
                return True
            except Exception as error:
                print('database is off:' + str(self.__class__))
                print(error)
                return False


class UsersDb(BaseDb):
    def add(self, user_id, username, is_subscribed: bool = True):
        with Session(self.engine) as self.session:
            try:
                user1 = self.table(user_id=user_id, username=username, is_subscribed=is_subscribed)
                self.session.add(user1)
                self.session.commit()
            except Exception as error:
                print('cant add:' + str(self.__class__) + str(user_id))
                print(error)

    def get_subscribed(self):
        with Session(self.engine) as self.session:
            try:
                result = self.session.query(self.table).filter_by(is_subscribed=True).all()
                # print(result)
                return result
            except Exception as error:
                print('cant_get:' + str(self.__class__))
                print(error)

    def get_by_username(self, username):
        with Session(self.engine) as self.session:
            try:
                result = self.session.query(self.table).filter_by(username=username).one()
                # print(result)
                return result
            except Exception as error:
                print('cant_get_by_username:' + str(self.__class__))
                print(error)

    def is_subscribed(self, user_id):
        user = self.get(user_id)
        return user.is_subscribed

    def subscription(self, user_id, subscribe: bool = True):
        with Session(self.engine) as self.session:
            user = self.get(user_id)
            user.is_subscribed = subscribe
            try:
                self.session.add(user)
                self.session.commit()
            except Exception as error:
                print('cant change:' + str(self.__class__) + str(user_id))
                print(error)


class AdminsDb(BaseDb):
    def get_all_detailed(self):
        with Session(self.engine) as self.session:
            try:
                result = self.session.query(self.table).join(self.table.user).all()
                for x in range(len(result)):
                    result[x] = result[x].user
                return result
            except Exception as er:
                print('cant get:' + str(self.__class__))
                print(er)


class EventsDb(BaseDb):
    def add(self, ts, text, photo=None):
        with Session(self.engine) as self.session:
            try:
                if photo:
                    event = Events(ts=ts, text=text, photo=photo)
                else:
                    event = Events(ts=ts, text=text)
                self.session.add(event)
                self.session.commit()
            except Exception as error:
                print('cant add:' + str(self.__class__) + str(text))
                print(error)

    def get_all(self):
        with Session(self.engine) as self.session:
            try:
                result = self.session.query(self.table).order_by(self.table.ts).all()
                # print(result)
                return result
            except Exception as error:
                print('cant_get:' + str(self.__class__))
                print(error)

    def get_first(self):
        with Session(self.engine) as self.session:
            try:
                result = self.session.query(self.table).order_by(self.table.ts).first()
                # print(result)
                return result
            except Exception as error:
                print('cant_get:' + str(self.__class__))
                print(error)


class QuestionsDb(EventsDb):
    def add(self, user_id, username, ts, text, photo=None):
        with Session(self.engine) as self.session:
            try:
                if photo:
                    question = self.table(user_id=user_id, username=username, ts=ts, text=text, photo=photo)
                else:
                    question = self.table(user_id=user_id, username=username, ts=ts, text=text)
                self.session.add(question)
                self.session.commit()
            except Exception as error:
                print('cant add:' + str(self.__class__) + str(text))
                print(error)

    def count_by_user(self, user_id):
        with Session(self.engine) as self.session:
            try:
                result = self.session.query(self.table).filter_by(user_id=user_id).count()
                if not result:
                    result = 0
                # print(result)
                return result
            except Exception as error:
                print('cant get_by_user:' + str(self.__class__) + str(user_id))
                print(error)

    def check(self, user_id=None):
        with Session(self.engine) as self.session:
            try:
                if user_id:
                    if self.session.query(self.table).filter_by(user_id=user_id).first():
                        return True
                    else:
                        return False
                else:
                    if self.session.query(self.table).first():
                        return True
                    else:
                        return False
            except Exception as error:
                print('cant check:' + str(self.__class__) + str(user_id))
                print(error)


class CertificateDb(QuestionsDb):
    """
    def add(self, user_id, username, ts, text):
        with Session(self.engine) as self.session:
            try:
                question = self.table(user_id=user_id, username=username, ts=ts, text=text)
                self.session.add(question)
                self.session.commit()
            except Exception as er:
                print(er)
                print('cant add:' + str(self.__class__) + str(text))

    def count_by_user(self, user_id):
        with Session(self.engine) as self.session:
            try:
                result = self.session.query(self.table).filter_by(user_id=user_id).count()
                if not result:
                    result = 0
                print(result)
                return result
            except Exception as er:
                print(er)
                print('cant get_by_user:' + str(self.__class__) + str(user_id))
    """


class Users(Base):
    __tablename__ = 'users'
    user_id = sq.Column(sq.Integer, primary_key=True)
    username = sq.Column(sq.TEXT)
    is_subscribed = sq.Column(sq.Boolean)
    admin = relationship('Admins', back_populates='user', uselist=False)
    questions = relationship('Questions', back_populates='user')
    certificates = relationship('Certificates', back_populates='user')

    def __repr__(self):
        return f'{self.user_id} {self.username} | subscribed:{self.is_subscribed}'


class Admins(Base):
    __tablename__ = 'admins'
    user_id = sq.Column(sq.Integer, sq.ForeignKey('users.user_id'), primary_key=True)
    user = relationship('Users', back_populates='admin')

    def __repr__(self):
        return f'{self.user_id}'


class Events(Base):
    __tablename__ = 'events'
    event_id = sq.Column(sq.Integer, primary_key=True)
    ts = sq.Column(sq.Integer)
    text = sq.Column(sq.TEXT)
    photo = sq.Column(sq.TEXT)

    def __repr__(self):
        return f'{self.event_id}\n{self.ts}\n{self.text}\n'


class Questions(Base):
    __tablename__ = 'questions'
    question_id = sq.Column(sq.Integer, primary_key=True)
    user_id = sq.Column(sq.Integer, sq.ForeignKey('users.user_id'))
    username = sq.Column(sq.TEXT)
    ts = sq.Column(sq.Integer)
    text = sq.Column(sq.TEXT)
    photo = sq.Column(sq.TEXT)
    user = relationship('Users', back_populates='questions')

    def __repr__(self):
        return f'{self.question_id}\n{self.username}\n{self.ts}\n{self.text}\n'


class Certificates(Base):
    __tablename__ = 'certificates'
    certificate_id = sq.Column(sq.Integer, primary_key=True)
    user_id = sq.Column(sq.Integer, sq.ForeignKey('users.user_id'))
    username = sq.Column(sq.TEXT)
    ts = sq.Column(sq.Integer)
    text = sq.Column(sq.TEXT)
    photo = sq.Column(sq.TEXT)
    user = relationship('Users', back_populates='certificates')

    def __repr__(self):
        return f'{self.certificate_id}\n{self.username}\n{self.ts}\n{self.text}\n'


if __name__ == '__main__':
    connection = Connection('sqlite')
    user_db = UsersDb(Users, 'user_id', connection)
    admin_db = AdminsDb(Admins, 'user_id', connection)
    event_db = EventsDb(Events, 'event_id', connection)
    question_db = QuestionsDb(Questions, 'question_id', connection)
    certificate_db = CertificateDb(Certificates, 'certificate_id', connection)

    import time
    for i in range(16):
        user_db.add(i, f'test_user{i}')
    for i in range(13):
        question_db.add(i, f'@test_user_{i}', time.time(), f'тестовый вопрос {i}')
    for i in range(16):
        certificate_db.add(i, f'@test_user_{i}', time.time(), f'тестовая заявка {i}')
    for i in range(5):
        event_db.add(time.time()+i*50000 + random.randrange(1, 20000), f'тестовое событие {i}')
    event_db.add(time.time() + 70000, f'тестовое событие с картинкой',
                 'AgACAgIAAxkBAAIN3GLZaF8_ps40AaVl0loyepQBfAmpAALvwTEbl5LJSq6po3pNRiuAAQADAgADeAADKQQ')

    # certificate_db.count_by_user(466251731)
    # db = DbManager(user_db, admin_db)
    # event_db.add('123123123', 'text')
    # user_db.add(12345)
    # admin_db.add(12345)
    # admin_db.check(12345)
    # print(db.user_check(12345))
    # user_db.add(12345)
    # print(user_db.check(12345))
    # print(user_db.get_all())
    # print()
    # print(user_db.is_subscribed(12345))
    # user_db.subscription(12345, False)
    # print(user_db.is_subscribed(12345))
    # user_db.delete_all()
    # print(working_dir)
    # event_db.add('event ts', 'event text')
    # print(event_db.get_all())
    # user_db.get_subscribed()
    # user_db.is_subscribed(466251731)
    # admin_db.get_all()
    # user_db.get_all()
