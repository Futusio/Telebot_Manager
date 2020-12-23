from sqlalchemy import Table, Column, Integer, ForeignKey, create_engine, String
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from hashlib import sha256
from cipher import Cipher

engine = create_engine('sqlite:///main.db', echo=False)

engine = create_engine('postgresql://{name}:{password}@{host}:{port}/main')

Base = declarative_base()


class Users(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    login = Column(String)
    password = Column(String)
    email = Column(String)
    children = relationship("Groups")
    
    def __init__(self, login, password):
        self.login = login
        self.password = sha256(bytes(password, encoding='utf-8')).hexdigest()

class Groups(Base):
    __tablename__ = 'groups'
    id = Column(Integer, primary_key=True)
    u_id = Column(Integer, ForeignKey('users.id'))
    name = Column(String)
    children = relationship("Sites")
    
    def __init__(self, u_id, name):
        self.u_id = u_id
        self.name = name

class Sites(Base):
    __tablename__ = 'sites'
    id = Column(Integer, primary_key=True)
    u_id = Column(Integer, ForeignKey('users.id'))
    g_id = Column(Integer, ForeignKey('groups.id'))
    name = Column(String)
    url = Column(String)
    children = relationship("Accounts")

    def __init__(self, u_id, g_id, name):
        self.u_id = u_id
        self.g_id = g_id
        self.name = name

class Accounts(Base):
    __tablename__ = 'accounts'
    id = Column(Integer, primary_key=True)
    u_id = Column(Integer, ForeignKey('users.id'))
    g_id = Column(Integer, ForeignKey('groups.id'))
    s_id = Column(Integer, ForeignKey('sites.id'))
    name = Column(String)
    login = Column(String)
    password = Column(String)
    about = Column(String)

    def __init__(self, u_id, g_id, s_id, name, login, password, key): 
        self.u_id = u_id
        self.g_id = g_id
        self.s_id = s_id
        self.name = name
        self.login = Cipher.encrypt(login, key)
        self.password = Cipher.encrypt(password, key)