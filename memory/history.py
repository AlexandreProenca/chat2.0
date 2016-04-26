#!/usr/bin/env python
#  -*- coding: utf-8 -*-

import api_mongo


class History:
    def __init__(self, room):
        self.text = []
        self.room = room

    def add(self, sender, destination, message, alias, target, message_id, t):

        info = {"sender": sender,
                "destination": destination,
                "message": message,
                "alias": alias,
                "target": target,
                "message_id": message_id}
        self.text.append(info)
        api_mongo.insert_chat_history(sender, destination, message, alias, target, message_id, t)

    def read(self, since):
        res = api_mongo.read_chat_history(self.room, 0, since)
        return res

if __name__ == '__main__':

    print 'history channel, where the past comes alive'



