#!/usr/bin/env python
#  -*- coding: utf-8 -*-

import uuid
import time
from history import History
import logging
from user import User


class Room:
    rooms = []

    def __init__(self, users_name=None, room_id=None, dt=None, alias=None, resource=None, is_group=None, last_message=None):
        if not dt:
            self.start_time = time.time()
        else:
            self.dt = dt
        if not room_id:
            self.room_id = str(uuid.uuid4())
        else:
            self.room_id = room_id
        self.users_name = users_name
        self.history = History(self.room_id)
        self.alias = alias
        self.resource = resource
        self.last_message = last_message
        self.is_group = is_group

    @classmethod
    def open(cls, users, resource):
        temp_room = Room(users_name=users, resource=resource)
        cls.rooms.append(temp_room)
        #logging.info("number on rooms: %r", len(cls.rooms))
        return temp_room.room_id

    @classmethod
    def restore(cls, users_name, dt, room_id, alias, resource, is_group, last_message):
        r = cls.find_room_by_name(room_id)
        try:
            if r.room_id != room_id:
                temp_room = Room(users_name=users_name, room_id=room_id, dt=dt, alias=alias, resource=resource, is_group=is_group, last_message=last_message)
                cls.rooms.append(temp_room)
                return temp_room.room_id
            else:
                return users_name
        except Exception, e:
            temp_room = Room(users_name=users_name, room_id=room_id, dt=dt, alias=alias, resource=resource,is_group=is_group, last_message=last_message)
            cls.rooms.append(temp_room)
            return temp_room.room_id

    @classmethod
    def find_users_by_room(cls, room_name):
        users_found = None
        for r in cls.rooms:
            if r.room_id == room_name:
                users_found = cls.covert(r.users_name)
                break
        return users_found

    @classmethod
    def find_users_instance_by_room(cls, room_name, networkId):
        users_found = []
        for r in cls.rooms:
            if r.room_id == room_name:
                users_found = cls.covert(r.users_name)
                break

        ret = []

        for user_name in users_found:
            ret.append({'networkId': networkId, 'username': user_name})
        return ret

    @classmethod
    def find_room_by_alias(cls, alias):
        room = None
        for r in cls.rooms:
            if r.alias == alias:
                room = r
                break

        return room

    @classmethod
    def find_alias_by_room(cls, room_name):
        alias = None
        for r in cls.rooms:
            if r.room_id == room_name:
                alias = r.alias
                break

        return alias

    @classmethod
    def find_room_by_name(cls, room_id):
        r = None
        for r in cls.rooms:
            if r.room_id == room_id:
                break
        return r

    @classmethod
    def check_exist_room(cls, users, audience):

        try:
            for r in cls.rooms:
                if r.users_name:
                    users_list = cls.covert(r.users_name)
                    if r.resource == audience:
                        users_list.sort()
                        users.sort()
                        if (users_list == users) and (not r.is_group):
                            return r.room_id
        except Exception, e:
            print "Error:", e
        return None

    @classmethod
    def find_room_by_users(cls, users, audience):
        res = ''
        for r in cls.rooms:
            if r.users_name:
                if r.resource == audience:
                    users_list = cls.covert(r.users_name)
                    if len(users_list) == 2:
                        if ((users_list[0] == users[0]) and (users_list[1] == users[1])) \
                                or ((users_list[0] == users[1]) and (users_list[1] == users[0])):
                            res = r.room_id
                            break
        return res

    @classmethod
    def history_add(cls, sender, destination, message, alias, target, message_id, t):
        r = cls.find_room_by_name(destination)
        r.last_message = t
        r.history.add(sender, destination, message, alias, target, message_id, t)

    def history_read(self, since):
        r = self.history.read(since)
        return r

    @classmethod
    def covert(cls, d):
        return [i['username'] for i in d]
