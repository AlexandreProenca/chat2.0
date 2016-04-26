import time
import tornado.ioloop
import tornado.web
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import logging
from config.constants import DEBUG
from models.models import Base, Member, Message, User
from sqlalchemy.ext.declarative import DeclarativeMeta


engine = create_engine('mysql://nwpartner2:gmmaster765@179.188.16.42/nwpartner2')
Base.metadata.bind = engine
Base.metadata.create_all(engine)
DBSession = sessionmaker(bind=engine)


dir_log = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../logs/chat.log')

logging.basicConfig(format='[%(asctime)s] - %(message)s',
                        datefmt='%d/%m/%Y %I:%M:%S %p',
                        filename=dir_log,
                        level=logging.INFO)


db = DBSession()


def insert_chat_message(sender_id, to, text, is_group, attachment_type, attachment_link, datetime):
    message = Message(sender_id=sender_id, to=to, text=text, is_group=is_group, attachment_type=attachment_type, attachment_link=attachment_link,datetime=datetime)
    db.add(message).commit()
    return message


def read_chat_history(_room_id, page, since):
    queryset = db.query(Message).filter_by(to=_room_id, since=since)
    return queryset


def read_room(_room_id):
    queryset = db.query(Message).filter_by(to=_room_id)
    return queryset


def read_user(user_id):
    queryset = db.query(User).filter_by(id=user_id).first()
    return queryset


def room_users_change(_room_id, users_name):
    information = {"type": "chat", "payload": {"command": "room_alias_rename",
                                               "details": {"room_id": _room_id, "users_name": users_name}}}
    payload = {'msg': json.dumps(information)}
    response = requests.post(URL_API_MONGO + ":" + str(PORT_API_MONGO) + "/room_users_change", params=payload)
    print 'ret:', response
    return response.text


def user_list():
    info = {}
    response = requests.get(URL_API_MONGO + ":" + str(PORT_API_MONGO) + "/user_list", params=info)
    return response.text


def read_room_list():
    info = {}
    try:
        response = requests.get(URL_API_MONGO + ":" + str(PORT_API_MONGO) + "/room_list", params=info)
        return response.text
    except:
        return None


def user_status_change(_username, _status):
    information = {"type": "chat", "payload": {"command": "user_status_change",
                                               "details": {"username": _username, "status": _status}}}
    payload = {'msg': json.dumps(information)}
    response = requests.post(URL_API_MONGO + ":" + str(PORT_API_MONGO) + "/user_status_change", params=payload)

    return response


def insert_room(_users, _room_id, _alias, _resource, _is_group, last_message):
    information = {"type": "chat", "payload": {"command": "room_add",
                                               "details": {"users_name": _users,
                                                           "room_id": _room_id,
                                                           "alias": _alias,
                                                           "resource": _resource,
                                                           "last_message": last_message,
                                                           "is_group": _is_group}}}
    payload = {'msg': json.dumps(information)}
    response = requests.post(URL_API_MONGO + ":" + str(PORT_API_MONGO) + "/room_add", params=payload)

    return response


def insert_user(user_name, user_resource):
    information = {"type": "chat", "payload": {"user": user_name, "resource": user_resource, "status": 1}}
    payload = {'msg': json.dumps(information)}
    response = requests.post(URL_API_MONGO + ":" + str(PORT_API_MONGO) + "/user_add", params=payload)

    return response


def rename_room(_destination, _room_rename):
    information = {"type": "chat", "payload": {"command": "room_alias_rename",
                                               "details": {"room_id": _destination, "alias": _room_rename}}}
    payload = {'msg': json.dumps(information)}
    response = requests.post(URL_API_MONGO + ":" + str(PORT_API_MONGO) + "/room_alias_rename", params=payload)

    return response


def remove_user_room(_destination, _user_name):
    information = {"type": "chat", "payload": {"command": "remove_user_room",
                                               "details": {"room_id": _destination, "user_name": _user_name}}}
    payload = {'msg': json.dumps(information)}
    response = requests.post(URL_API_MONGO + ":" + str(PORT_API_MONGO) + "/remove_user_room", params=payload)

    return response


def insert_embed(information):

    payload = {'msg': json.dumps(information)}
    response = requests.post(URL_API_MONGO + ":" + str(PORT_API_MONGO) + "/embed_add", params=payload)

    return response


def read_embed(key, value):
    key_encoded = base64.b64encode(key)
    value_encoded = base64.b64encode(value)
    info = {"key": key_encoded, "value":value_encoded}
    response = requests.get(URL_API_MONGO + ":" + str(PORT_API_MONGO) + "/embed_find", params=info)

    return response.text