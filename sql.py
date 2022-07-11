import os
import sqlalchemy as sq
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship

working_dir = os.getcwd()


class UsersDb:
    def __init__(self):
        self.engine = sq.create_engine(f'sqlite:///{working_dir}/database.db')
        self.Session = sessionmaker(bind=self.engine)
        # self.session = self.Session()
        Base.metadata.create_all(self.engine)

    def add(self, user_id, is_subscribed: bool = True):
        with Session(self.engine) as self.session:
            try:
                user1 = Users(user_id=user_id, is_subscribed=is_subscribed)
                self.session.add(user1)
                self.session.commit()
            except:
                print('cant add')

    def delete(self, user_id):
        with Session(self.engine) as self.session:
            try:
                self.session.query(Users).filter(Users.user_id == user_id).delete()
                self.session.commit()
            except:
                print('cant delete')

    def delete_all(self):
        with Session(self.engine) as self.session:
            try:
                self.session.query(Users).delete()
                self.session.commit()
            except:
                print('cant delete')

    def check(self, user_id=None):
        with Session(self.engine) as self.session:
            try:
                if user_id:
                    if self.session.query(Users).filter_by(user_id=user_id).first():
                        return True
                    else:
                        return False
                else:
                    if self.session.query(Users).first():
                        return True
                    else:
                        return False
            except:
                print('cant_check')

    def get(self, user_id):
        with Session(self.engine) as self.session:
            try:
                result = self.session.query(Users).get(user_id)
                print(result)
                return result
            except:
                print('cant_get')

    def get_all(self):
        with Session(self.engine) as self.session:
            try:
                result = self.session.query(Users).all()
                print(result)
                return result
            except:
                print('cant_get')

    def get_subscribed(self):
        with Session(self.engine) as self.session:
            try:
                result = self.session.query(Users).filter_by(is_subscribed=True).all()
                print(result)
                return result
            except:
                print('cant_get')

    def is_subscribed(self, user_id):
        user = self.get(user_id)
        return user.is_subscribed

    def subscription(self, user_id, subscribe: bool = True):
        user = self.get(user_id)
        user.is_subscribed = subscribe
        try:
            self.session.add(user)
            self.session.commit()
        except:
            print('cant_change')

    def is_on(self):
        with Session(self.engine) as self.session:
            try:
                self.check()
                return True
            except:
                return False




class AdminDb:
    def __init__(self):
        self.engine = sq.create_engine(f'sqlite:///{working_dir}/database.db')
        self.Session = sessionmaker(bind=self.engine)
        # self.session = self.Session()
        Base.metadata.create_all(self.engine)

    def add(self, user_id):
        with Session(self.engine) as self.session:
            try:
                admin = Admins(user_id=user_id)
                self.session.add(admin)
                self.session.commit()
            except:
                print('cant add')

    def delete(self, user_id):
        with Session(self.engine) as self.session:
            try:
                self.session.query(Admins).filter(Admins.user_id == user_id).delete()
                self.session.commit()
            except:
                print('cant delete')

    def delete_all(self):
        with Session(self.engine) as self.session:
            try:
                self.session.query(Admins).delete()
                self.session.commit()
            except:
                print('cant delete')

    def check(self, user_id=None):
        with Session(self.engine) as self.session:
            try:
                if user_id:
                    if self.session.query(Admins).filter_by(user_id=user_id).first():
                        return True
                    else:
                        return False
                else:
                    if self.session.query(Admins).first():
                        return True
                    else:
                        return False
            except:
                print('cant_check')

    def get(self, user_id):
        with Session(self.engine) as self.session:
            try:
                result = self.session.query(Admins.user_id).get(user_id)
                print(result)
                return result
            except:
                print('cant_get')


    def get_all(self):
        with Session(self.engine) as self.session:
            try:
                result = self.session.query(Admins).all()
                print(result)
                return result
            except:
                print('cant_get')


class EventsDb:
    def __init__(self):
        self.engine = sq.create_engine(f'sqlite:///{working_dir}/database.db')
        self.Session = sessionmaker(bind=self.engine)
        # self.session = self.Session()
        Base.metadata.create_all(self.engine)

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
                print('cant add')

    def delete(self, event_id):
        with Session(self.engine) as self.session:
            try:
                self.session.query(Events).filter(Events.event_id == event_id).delete()
                self.session.commit()
            except:
                print('cant delete')

    def delete_all(self):
        with Session(self.engine) as self.session:
            try:
                self.session.query(Events).delete()
                self.session.commit()
            except:
                print('cant delete')

    def check(self, event_id=None):
        with Session(self.engine) as self.session:
            try:
                if event_id:
                    if self.session.query(Events).filter_by(event_id=event_id).first():
                        return True
                    else:
                        return False
                else:
                    if self.session.query(Events).first():
                        return True
                    else:
                        return False
            except:
                print('cant_check')

    def get(self, event_id):
        with Session(self.engine) as self.session:
            try:
                result = self.session.query(Events.event_id).get(event_id)
                print(result)
                return result
            except:
                print('cant_get')

    def get_all(self):
        with Session(self.engine) as self.session:
            try:
                result = self.session.query(Events).order_by(Events.ts).all()
                print(result)
                return result
            except:
                print('cant_get')

class DbManager:
    def __init__(self, user_db_ex: UsersDb, admin_db_ex: AdminDb, event_db_ex: EventsDb):
        self.user_db = user_db_ex
        self.admin_db = admin_db_ex
        self.event_db = event_db_ex

    def admin_add(self, user_id):
        self.admin_db.add(user_id)

    def admin_remove(self, user_id):
        self.admin_db.delete(user_id)

    def admin_check(self, user_id):
        self.admin_db.check(user_id)

    def user_add(self, user_id):
        self.user_db.add(user_id)

    def user_remove(self, user_id):
        self.user_db.delete(user_id)

    def user_check(self, user_id):
        self.user_db.check(user_id)

    def user_is_subscribed(self, user_id):
        self.user_is_subscribed(user_id)


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


if __name__ == '__main__':
    user_db = UsersDb()
    admin_db = AdminDb()
    event_db = EventsDb()
    # db = DbManager(user_db, admin_db)
    # event_db.add('123123123', 'text')
    # db.user_add(12345)
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
    user_db.get_all()