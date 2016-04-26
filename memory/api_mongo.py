    #!/usr/bin/env python
#  -*- coding: utf-8 -*-
__author__ = 'cleytonpedroza'


import tornado.escape
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.websocket
import os.path
from tornado.options import define, options
from tornado import gen
import motor
import pymongo
import time
import json
import requests
import logging
import constants
import base64


URL_API_MONGO = constants.URL_API_MONGO
PORT_API_MONGO = constants.PORT_API_MONGO
MONGO_HOSTNAME = constants.MONGO_HOSTNAME
MONGO_PORT = int(constants.MONGO_PORT)


def insert_chat_history(_sender, _room_id, _message, _alias, _target, _message_id, t):
    info = {
        "type": "chat",
        "payload": {
            "command": "history",
            "details": {
                "sender": _sender,
                "room_id": _room_id,
                "message": _message,
                "alias": _alias,
                "target": _target,
                "message_id": _message_id,
                "dt":t
            }
        }
    }
    payload = {'msg': json.dumps(info)}
    response = requests.post(URL_API_MONGO + ":" + str(PORT_API_MONGO) + "/insert", params=payload)
    return response


def read_chat_history(_room_id, page, since):
    info = {"room_id": _room_id, "page": page, "since": since}
    response = requests.get(URL_API_MONGO + ":" + str(PORT_API_MONGO) + "/history", params=info)
    return response.text


def read_room(_room_id):
    info = {"room_id": _room_id}
    response = requests.get(URL_API_MONGO + ":" + str(PORT_API_MONGO) + "/room_find", params=info)
    return response.text


def read_user(user, resource):
    info = {"user": user, "resource": resource}
    response = requests.get(URL_API_MONGO + ":" + str(PORT_API_MONGO) + "/user_find", params=info)
    return response.text


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

#  ---------


class MainHandler(tornado.web.RequestHandler):
    def data_received(self, chunk):
        pass

    @tornado.web.asynchronous
    @gen.coroutine
    def get(self):
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Methods', 'POST')
        self.set_header('Access-Control-Allow-Headers', 'Content-Type')

        self.write("ServerMongo<BR><BR><BR>")

        n = yield db.history.find().count()

        self.write(str(n) + " Mensagens gravadas")
        self.finish()


class Insert(tornado.web.RequestHandler):
    def data_received(self, chunk):
        pass

    @tornado.web.asynchronous
    @gen.coroutine
    def get(self):
        pass

    @tornado.gen.coroutine
    @tornado.web.asynchronous
    def post(self):
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Methods', 'POST')
        self.set_header('Access-Control-Allow-Headers', 'Content-Type')
        received_parsed = json.loads(self.get_argument('msg'))  # string to JSON
        details = received_parsed['payload']['details']
        details['datetime'] = received_parsed['payload']['details']['dt']

        info = {"type": "chat", "payload": {"command": "history_insert", "details": details}}
        room_id = details['room_id']
        db.history.insert(info)
        # insert last message in room
        db.room.update({"payload.details.room_id": str(room_id)},
                        {'$set': {"payload.details.last_message": details['datetime']}})

        res = json.dumps({"type": "chat", "payload": {"command": "history_insert", "details": "OK"}})  # JSON TO STRING
        self.write(res)
        self.finish()

class RoomAdd(tornado.web.RequestHandler):
    def data_received(self, chunk):
        pass

    @tornado.web.asynchronous
    @gen.coroutine
    def get(self):
        pass

    @tornado.gen.coroutine
    @tornado.web.asynchronous
    def post(self):
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Methods', 'POST')
        self.set_header('Access-Control-Allow-Headers', 'Content-Type')

        received_parsed = json.loads(self.get_argument('msg'))  # string to JSON

        details = received_parsed['payload']['details']
        details['datetime'] = time.time()

        info = {"type": "chat", "payload": {"command": "room_add", "details": details}}
        db.room.insert(info)

        res = json.dumps({"type": "chat", "payload": {"command": "room_add", "details": "OK"}})  # JSON TO STRING
        self.write(res)
        self.finish()


class UserAdd(tornado.web.RequestHandler):
    def data_received(self, chunk):
        pass

    @tornado.web.asynchronous
    @gen.coroutine
    def get(self):
        pass

    @tornado.gen.coroutine
    @tornado.web.asynchronous
    def post(self):
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Methods', 'POST')
        self.set_header('Access-Control-Allow-Headers', 'Content-Type')

        received_parsed = json.loads(self.get_argument('msg'))  # string to JSON
        user = received_parsed['payload']['user']
        resource = received_parsed['payload']['resource']

        found = yield db.user.find_one({"payload.user": str(user), "payload.resource": str(resource)})

        if not found:
            info = {"type": "chat", "payload": {"password": "1234", "user": user, "resource": resource, "status": 1}}
            db.user.insert(info)

        self.finish()


class EmbedAdd(tornado.web.RequestHandler):
    def data_received(self, chunk):
        pass

    @tornado.web.asynchronous
    @gen.coroutine
    def get(self):
        pass

    @tornado.gen.coroutine
    @tornado.web.asynchronous
    def post(self):
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Methods', 'POST')
        self.set_header('Access-Control-Allow-Headers', 'Content-Type')

        info = json.loads(self.get_argument('msg'))  # string to JSON
        db.embed.insert(info)

        self.finish()


class History(tornado.web.RequestHandler):
    def data_received(self, chunk):
        pass

    @tornado.gen.coroutine
    @tornado.web.asynchronous
    def get(self):
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Methods', 'POST')
        self.set_header('Access-Control-Allow-Headers', 'Content-Type')

        room = self.get_argument('room_id')
        page = int(self.get_argument('page'))

        try:
            since = float(self.get_argument('since'))

            cursor = db.history.find({"payload.details.room_id": str(room),
                                      "payload.details.datetime": {"$gt": since}})
        except Exception, e:
            cursor = db.history.find({"payload.details.room_id": str(room)})
        cursor.sort([('payload.details.datetime', pymongo.DESCENDING)]).limit(200).skip(page*10)

        details = []
        while (yield cursor.fetch_next):
            document = cursor.next_object()
            message = document['payload']['details']['message']
            room = document['payload']['details']['room_id']
            dt = float(document['payload']['details']['datetime'])
            sender = document['payload']['details']['sender']
            target = document['payload']['details']['target']
            message_id = ""
            if "message_id" in document['payload']['details']:
                message_id = document['payload']['details']['message_id']

            details.append({"message": message,
                            "room_id": room,
                            "dt": dt,
                            "sender": sender,
                            "target": target,
                            "message_id": message_id})

        res = json.dumps(details)

        if not details:
            res = "null"

        self.write(res)
        self.finish()


class RoomFind(tornado.web.RequestHandler):
    def data_received(self, chunk):
        pass

    @tornado.gen.coroutine
    @tornado.web.asynchronous
    def get(self):
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Methods', 'POST')
        self.set_header('Access-Control-Allow-Headers', 'Content-Type')

        room = self.get_argument('room_id')

        document = yield db.room.find_one({"payload.details.room_id": str(room)})
        res = 'no room found'

        if document:
            room = document['payload']['details']['room_id']
            dt = float(document['payload']['details']['datetime'])
            users_name = document['payload']['details']['users_name']
            alias = document['payload']['details']['alias']
            resource = document['payload']['details']['resource']
            last_message = document['payload']['details']['last_message']
            is_group = document['payload']['details']['is_group']

            dc = {"type": "chat",
                  "payload": {"command": "room_find",
                              "details": {"room": room,
                                          "dt": dt,
                                          "users_name": users_name,
                                          "alias": alias,
                                          "resource": resource,
                                          "last_message": last_message,
                                          "is_group": is_group}}}

            dc["payload"]["details"]["is_group"] = is_group
            res = json.dumps(dc)
        else:
            res = '{"type": "chat", "payload": {"command": "error", "details": "information not found"}}'

        self.write(res)
        self.finish()


class UserFind(tornado.web.RequestHandler):
    def data_received(self, chunk):
        pass

    @tornado.gen.coroutine
    @tornado.web.asynchronous
    def get(self):
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Methods', 'POST')
        self.set_header('Access-Control-Allow-Headers', 'Content-Type')

        user = self.get_argument('user')
        resource = self.get_argument('resource')

        document = yield db.user.find_one({"payload.user": str(user), "payload.resource": str(resource)})
        res = 'no room found'
        if document:
            user = document['payload']['user']
            status = document['payload']['status']

            res = json.dumps({"type": "chat",
                              "payload": {"command": "user_find",
                                          "details": {"user": user, "status": status}}})
        else:
            res = json.dumps({"type": "chat",
                              "payload": {"command": "error",
                                          "details": {"message": "information not found",
                                                      "status": 1}}})

        self.write(res)
        self.finish()


class EmbedFind(tornado.web.RequestHandler):
    def data_received(self, chunk):
        pass

    @tornado.gen.coroutine
    @tornado.web.asynchronous
    def get(self):
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Methods', 'POST')
        self.set_header('Access-Control-Allow-Headers', 'Content-Type')

        key = self.get_argument('key')
        key_decoded = base64.b64decode(key)

        value = self.get_argument('value')
        value_decoded = base64.b64decode(value)

        document = yield db.embed.find_one({key_decoded: str(value_decoded)})
        res = 'NO'
        if document:
            print "Doc: ", document, type(document)
            del document['_id']
            res = json.dumps(document)
            print "Res: ",res

        self.write(res)
        self.finish()


class RoomList(tornado.web.RequestHandler):
    def data_received(self, chunk):
        pass

    @tornado.gen.coroutine
    @tornado.web.asynchronous
    def get(self):

        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Methods', 'POST')
        self.set_header('Access-Control-Allow-Headers', 'Content-Type')

        cursor = db.room.find({})

        details = []
        while (yield cursor.fetch_next):
            document = cursor.next_object()
            room = document['payload']['details']['room_id']
            alias = document['payload']['details']['alias']
            details.append({"room": room, "alias": alias})

        res = json.dumps({"type": "chat", "payload": {"command": "room_list", "details": details}})
        if not details:
            res = '{"type": "chat", "payload": {"command": "error", "details": "information not found"}}'

        self.write(res)
        self.finish()


class UserList(tornado.web.RequestHandler):
    def data_received(self, chunk):
        pass

    @tornado.gen.coroutine
    @tornado.web.asynchronous
    def get(self):
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Methods', 'POST')
        self.set_header('Access-Control-Allow-Headers', 'Content-Type')

        cursor = db.user.find({})

        details = []
        while (yield cursor.fetch_next):
            document = cursor.next_object()
            user = document['payload']['user']
            status = document['payload']['status']
            details.append({"user": user, "status": status})

        res = json.dumps({"type": "chat", "payload": {"command": "user_list", "details": details}})
        if not details:
            res = '{"type": "chat", "payload": {"command": "error", "details": "information not found"}}'

        self.write(res)
        self.finish()


class RoomAliasRename(tornado.web.RequestHandler):
    def data_received(self, chunk):
        pass

    @tornado.gen.coroutine
    @tornado.web.asynchronous
    def post(self):
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Methods', 'POST')
        self.set_header('Access-Control-Allow-Headers', 'Content-Type')

        info = json.loads(self.get_argument('msg'))
        room = info['payload']['details']['room_id']
        alias = info['payload']['details']['alias']

        yield db.room.update({"payload.details.room_id": str(room)}, {'$set': {"payload.details.alias": alias}})

        self.finish()


class RemoveUserRoom(tornado.web.RequestHandler):
    def data_received(self, chunk):
        pass

    @tornado.gen.coroutine
    @tornado.web.asynchronous
    def post(self):
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Methods', 'POST')
        self.set_header('Access-Control-Allow-Headers', 'Content-Type')

        info = json.loads(self.get_argument('msg'))

        room = info['payload']['details']['room_id']
        user_remove = info['payload']['details']['user_name']

        document = yield db.room.find_one({"payload.details.room_id": str(room)})
        if document:
            #print 'doc:', document

            users_name = document['payload']['details']['users_name']

            #print("REMOVE USERS ", [i['username'] for i in users_name])
            users_name.remove({"username": user_remove, "seen": None, "received": None})

            print 'users_name:', users_name
            print 'user_remove:', user_remove

            yield db.room.update({"payload.details.room_id": str(room)},
                                 {'$set': {"payload.details.users_name": users_name}})
        self.finish()


class RoomUsersChange(tornado.web.RequestHandler):
    def data_received(self, chunk):
        pass

    @tornado.gen.coroutine
    @tornado.web.asynchronous
    def post(self):
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Methods', 'POST')
        self.set_header('Access-Control-Allow-Headers', 'Content-Type')

        info = json.loads(self.get_argument('msg'))
        room = info['payload']['details']['room_id']
        users_name = info['payload']['details']['users_name']

        yield db.room.update({"payload.details.room_id": str(room)},
                             {'$set': {"payload.details.users_name": users_name}})

        self.finish()


class UserStatusChange(tornado.web.RequestHandler):
    def data_received(self, chunk):
        pass

    @tornado.gen.coroutine
    @tornado.web.asynchronous
    def post(self):
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Methods', 'POST')
        self.set_header('Access-Control-Allow-Headers', 'Content-Type')

        info = json.loads(self.get_argument('msg'))
        username = info['payload']['details']['username']
        status = info['payload']['details']['status']

        yield db.user.update({"payload.user": username},
                             {'$set': {"payload.status": status}})

        self.finish()


class Monitor(tornado.web.RequestHandler):
    def get(self):
        self.write({"status": "success"})


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", MainHandler),
            (r"/insert", Insert),
            (r"/history", History),
            (r"/room_add", RoomAdd),
            (r"/room_find", RoomFind),
            (r"/user_find", UserFind),
            (r"/user_list", UserList),
            (r"/room_list", RoomList),
            (r"/user_add", UserAdd),
            (r"/embed_find", EmbedFind),
            (r"/embed_add", EmbedAdd),
            (r"/user_status_change", UserStatusChange),
            (r"/room_alias_rename", RoomAliasRename),
            (r"/room_users_change", RoomUsersChange),
            (r"/remove_user_room", RemoveUserRoom),
            (r"/monitor", Monitor),

        ]
        settings = dict(
            cookie_secret="__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            xsrf_cookies=False,
            autoreload=True,
            debug=True
        )

        tornado.web.Application.__init__(self, handlers, **settings)


def main():
    tornado.options.parse_command_line()
    logging.disable(logging.INFO)
    app = Application()
    app.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()




if __name__ == "__main__":
    define("port", default=8889, help="run on the given port", type=int)
    db = motor.MotorClient(host=MONGO_HOSTNAME, port=MONGO_PORT).sbhistory
    # db = motor.MotorClient().sbhistory
    print 'API Mongo started success!'
    main()
