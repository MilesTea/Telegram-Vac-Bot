import os
import sqlalchemy as sq
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship

working_dir = os.getcwd()


class BaseDb:
    def __init__(self, table, id_row):
        self.engine = sq.create_engine(f'sqlite:///{working_dir}/database.db')
        self.Session = sessionmaker(bind=self.engine)
        Base.metadata.create_all(self.engine)
        self.table = table
        self.id_row = id_row

    def add(self, entry_id, **kwargs):
        with Session(self.engine) as self.session:
            try:
                new_entry = self.table(**{self.id_row: entry_id, **kwargs})
                self.session.add(new_entry)
                self.session.commit()
            except:
                print('cant add' + str(self.__class__) + str(entry_id))

    def delete(self, entry_id):
        with Session(self.engine) as self.session:
            try:
                self.session.query(self.table).filter(getattr(self.table, self.id_row) == entry_id).delete()
                self.session.commit()
            except:
                print('cant delete' + str(self.__class__) + str(entry_id))

    def delete_all(self):
        with Session(self.engine) as self.session:
            try:
                self.session.query(self.table).delete()
                self.session.commit()
            except:
                print('cant delete' + str(self.__class__))

    def check(self, entry_id):
        with Session(self.engine) as self.session:
            try:
                if self.session.get(self.table, entry_id):
                    return True
                else:
                    return False
            except:
                print('cant check:' + str(self.__class__) + str(entry_id))

    def get(self, entry_id):
        with Session(self.engine) as self.session:
            try:
                result = self.session.get(self.table, entry_id)
                print(result)
                return result
            except:
                print('cant get:' + str(self.__class__) + str(entry_id))

    def get_all(self):
        with Session(self.engine) as self.session:
            try:
                result = self.session.query(self.table).all()
                print(result)
                return result
            except:
                print('cant get:' + str(self.__class__))

    def is_on(self):
        with Session(self.engine) as self.session:
            try:
                self.session.query(self.table).first()
                return True
            except:
                print('database is off:' + str(self.__class__))
                return False


class UsersDb(BaseDb):
    def add(self, user_id, is_subscribed: bool = True):
        with Session(self.engine) as self.session:
            try:
                user1 = self.table(user_id=user_id, is_subscribed=is_subscribed)
                self.session.add(user1)
                self.session.commit()
            except:
                print('cant add:' + str(self.__class__) + str(user_id))

    def get_subscribed(self):
        with Session(self.engine) as self.session:
            try:
                result = self.session.query(self.table).filter_by(is_subscribed=True).all()
                print(result)
                return result
            except:
                print('cant_get:' + str(self.__class__))

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
            except:
                print('cant change:' + str(self.__class__) + str(user_id))


class AdminsDb(BaseDb):
    pass


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
            except:
                print('cant add:' + str(self.__class__) + str(text))

    def get_all(self):
        with Session(self.engine) as self.session:
            try:
                result = self.session.query(self.table).order_by(self.table.ts).all()
                print(result)
                return result
            except:
                print('cant_get:' + str(self.__class__))


class QuestionsDb(EventsDb):
    def add(self, question_id, ts, text, photo=None):
        with Session(self.engine) as self.session:
            try:
                if photo:
                    question = self.table(question_id=question_id, ts=ts, text=text, photo=photo)
                else:
                    question = self.table(question_id=question_id, ts=ts, text=text)
                self.session.add(question)
                self.session.commit()
            except:
                print('cant add:' + str(self.__class__) + str(text))


class  CertificateDb(EventsDb):
    def add(self, certificate_id, ts, text):
        with Session(self.engine) as self.session:
            try:
                question = self.table(certificate_id=certificate_id, ts=ts, text=text)
                self.session.add(question)
                self.session.commit()
            except:
                print('cant add:' + str(self.__class__) + str(text))


Base = declarative_base()


class Users(Base):
    __tablename__ = 'users'
    user_id = sq.Column(sq.Integer, primary_key=True)
    is_subscribed = sq.Column(sq.Boolean)
    admins = relationship('Admins', back_populates='users', uselist=False)

    def __repr__(self):
        return f'{self.user_id} | subscribed:{self.is_subscribed}'


class Admins(Base):
    __tablename__ = 'admins'
    user_id = sq.Column(sq.Integer, sq.ForeignKey('users.user_id'), primary_key=True)
    users = relationship('Users', back_populates='admins')
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
    ts = sq.Column(sq.Integer)
    text = sq.Column(sq.TEXT)
    photo = sq.Column(sq.TEXT)


class Certificates(Base):
    __tablename__ = 'certificates'
    certificate_id = sq.Column(sq.Integer, primary_key=True)
    ts = sq.Column(sq.Integer)
    text = sq.Column(sq.TEXT)


if __name__ == '__main__':
    user_db = UsersDb(Users, 'user_id')
    admin_db = AdminsDb(Admins, 'user_id')
    event_db = EventsDb(Events, 'event_id')
    # db = DbManager(user_db, admin_db)
    # event_db.add('123123123', 'text')
    user_db.add(12345)
    admin_db.add(12345)
    admin_db.check(12345)
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