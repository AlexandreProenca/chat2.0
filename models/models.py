#!/usr/bin/env python
#  -*- coding: utf-8 -*-
import json

from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship


Base = declarative_base()


class User(Base):
    __tablename__ = 'chat_auth_user'
    id = Column(Integer, primary_key=True)
    username = Column(String(250), nullable=False)
    password = Column(String(250), nullable=False)
    token = Column(String(250), nullable=False)

    def __repr__(self):
        return json.dumps({
            "id": self.id,
            "username": self.username,
            "password": self.password,
            "token": self.token,
        })


class Group(Base):
    __tablename__ = 'chat_group'
    id = Column(Integer, primary_key=True)
    title = Column(String(250), nullable=False)
    avatar_link = Column(String(250), nullable=False)
    last_message = Column(Float, nullable=False)
    created = Column(Float, nullable=False)

    def __repr__(self):
        return json.dumps({
            "id": self.id,
            "last_message": self.last_message,
            "title": self.title,
            "avatar_link": self.avatar_link,
            "created": self.created
        })


class Member(Base):
    __tablename__ = 'chat_member'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('chat_auth_user.id'))
    user = relationship(User)
    group_id = Column(Integer, ForeignKey('chat_group.id'))
    group = relationship(Group)
    joined = Column(Float, nullable=True)
    status = Column(Integer)
    admin = Column(Boolean)
    resource = Column(String(250), nullable=False)
    seen = Column(Float, nullable=True)
    received = Column(Float, nullable=True)

    def __repr__(self):
        return json.dumps({
            "id": self.id,
            "user": self.user.username,
            "group": self.group.title,
            "joined": self.joined,
            "status": self.status,
            "admin": self.admin,
            "resource": self.resource,
            "seen": self.seen,
            "received": self.received
        })


class Message(Base):
    __tablename__ = 'chat_message'
    id = Column(Integer, primary_key=True)
    sender_id = Column(Integer, ForeignKey('chat_auth_user.id'))
    sender = relationship(User)
    to = Column(Integer) # vai ser o id de um grupo ou um usuario
    text = Column(String(250), nullable=False)
    is_group = Column(Boolean)
    attachment_type = Column(String(50), nullable=True)
    attachment_link = Column(String(250), nullable=True)

    def __repr__(self):
        return json.dumps({
            "id": self.id,
            "sender": self.sender.username,
            "to": self.to,
            "text": self.text,
            "is_group": self.is_group,
            "attachment_type": self.attachment_type,
            "attachment_link": self.attachment_link,
        })