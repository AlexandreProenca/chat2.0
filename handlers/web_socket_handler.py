#!/usr/bin/env python
#  -*- coding: utf-8 -*-
import json
import logging

import sys
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.websocket
import os
from memory import manager

# Log, formater and file
dir_log = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../logs/chat.log')
logging.basicConfig(format='[%(asctime)s] - %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p',
                    filename=dir_log,
                    level=logging.INFO)


class WebSocketHandler(tornado.websocket.WebSocketHandler):

    def check_origin(self, origin):
        # to avoid cross-domain
        return True

    def open(self):
        manager.open(self)
        print("WebSocket opened by %s" % self)

    def on_message(self, message):
        parsed = None
        try:
            parsed = json.loads(message)
            if 'type' in parsed:
                if parsed['type'] != 'bridge':
                    if 'type' in parsed['payload']:
                        logging.info("WebSocket %s::%s::%s to %s" %(
                            parsed['type'],
                            parsed['payload']['type'],
                            parsed['target'][0]['resource'],
                            parsed['target'][0]['user']
                        ))
                    else:
                        logging.info("message : %r", json.dumps(parsed))
            else:
                # logging.info("message : %r", parsed)
                pass

        except Exception, e:
            logging.info("Exception:", sys.exc_info()[0], e)
            logging.info('not parsed value:', message)

        if parsed:
            if parsed['type'] == 'system':
                manager.system_call(self, parsed['payload'])

            elif parsed['type'] == 'bridge':
                manager.Heartbeat.ping_broadcast()
                self.write_message('OK')

            elif parsed['type'] == 'authenticate':
                if parsed['payload']['token']:
                    manager.login(self,
                                  parsed['payload']['token'])
                                  # parsed['payload']['issue'],
                                  # parsed['payload']['audience'])
                else:
                    if parsed['payload']['logout']:
                        manager.logout(self)

            elif parsed['type'] == 'notification':
                for el in parsed['target']:
                    manager.notification(el['user'], el['audience'], message)

            elif parsed['type'] == 'signal':
                for el in parsed['target']:
                    if el['user'] != '*':
                        manager.notification(el['user'], el['audience'], message)
                    else:
                        manager.notification_broadcast(el['audience'], message)

            elif parsed['type'] == 'chat':

                if parsed['payload']['command'] == 'user_list':
                    manager.user_list(self)

                elif parsed['payload']['command'] == 'logout':
                    manager.logout(self)

                elif parsed['payload']['command'] == 'room_list':
                    manager.room_list(self)

                elif parsed['payload']['command'] == 'room_create':
                    manager.room_create(self, parsed['payload'])

                elif parsed['payload']['command'] == 'room_enter':
                    manager.room_enter(self, parsed['payload']['details'])

                elif parsed['payload']['command'] == 'room_reopen':
                    manager.room_reopen(self, parsed['payload']['details'])

                elif parsed['payload']['command'] == 'room_message':
                    manager.room_message(self, parsed['payload']['details'])

                elif parsed['payload']['command'] == 'room_user_add':
                    manager.room_user_add(self, parsed['payload'])

                elif parsed['payload']['command'] == 'user_status':
                    manager.user_status(self, parsed['payload']['details'])

                elif parsed['payload']['command'] == 'user_change_text':
                    manager.user_change_text(self, parsed['payload']['details'])

                elif parsed['payload']['command'] == 'user_list_by_room':
                    manager.user_list_by_room(self, parsed['payload']['details'])

                elif parsed['payload']['command'] == 'room_list_by_user':
                    manager.room_list_by_user(self, parsed['payload']['details'])

                elif parsed['payload']['command'] == 'room_history':
                    manager.room_history(self, parsed['payload']['details'])

                elif parsed['payload']['command'] == 'room_rename':
                    manager.room_rename(self, parsed['payload']['details'])

                elif parsed['payload']['command'] == 'user_remove':
                    manager.user_remove(self, parsed['payload']['details'])

                elif parsed['payload']['command'] == 'contacts_online':
                    manager.contacts_online(self)


    def on_close(self):
        manager.open(self)
        print("WebSocket closed by %s" % self)