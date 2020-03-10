import os

from sqlalchemy import Integer, Column, String

from db.base import Base, session_factory
from enum import Enum


class State(Enum):
    S_START = 0
    S_ENTER_NAME = 1
    S_ENTER_CITY = 2
    S_ENTER_QUERY = 3
    S_UNDEFINED = 4


class DBWorker:

    def __init__(self):
        self.session = session_factory()

    def get_user_state(self, chat_id):
        #session = session_factory()
        user = self.session.query(User).filter_by(telegram_id=chat_id).first()
        self.session.close()
        if user is not None:
            return user.state
        else:
            return -1

    def set_user_state(self, chat_id, state):
        #session = session_factory()
        self.session.query(User).filter_by(telegram_id=chat_id).update({User.state: state})
        self.session.commit()
        self.session.close()

    def create_new_user(self, chat_id):
        new_user = User(telegram_id=chat_id, name='',city='', query='', state=State.S_START.value)
        self.session.add(new_user)
        self.session.commit()
        self.session.close()
        return new_user

    def get_user_by_id(self, chat_id):
        user = self.session.query(User).filter_by(telegram_id=chat_id).first()
        self.session.close()
        return user

    def update_user(self, **data):
        new_data = dict()

        fields_to_update = (User.telegram_id.name, User.name.name, User.city.name, User.query.name)

        for key, value in data.items():
            if key in fields_to_update:
                new_data.update({key: value});

        self.session.query(User).filter_by(telegram_id=new_data['telegram_id']).update(new_data)
        self.session.commit()
        self.session.close()

    def refresh_user(self, chat_id):
        refreshed_user = self.session.query(User).filter_by(telegram_id=chat_id).update({User.city: '', User.name: '', User.query: ''})
        self.session.commit()
        self.session.close()
        return refreshed_user

    def session_close(self):
        self.session.close()


class User(Base):
    __tablename__ = 'user'
    telegram_id = Column(Integer, primary_key=True)
    name = Column(String, default='')
    query = Column(String, default='')
    city = Column(String, default='')
    state = Column(Integer, default=State.S_START.value)

    def __init__(self, name, telegram_id, city, query, state ):
        self.name = name
        self.telegram_id = telegram_id
        self.city = city
        self.query = query
        self.state = state

    def __repr__(self):
        return "<User('%s', '%s', '%s')>" % (self.name, self.telegram_id, self.city, self.query)


