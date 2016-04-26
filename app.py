#  -*- coding: utf-8 -*-

import tornado.escape
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.websocket
from tornado.options import define, options
import tornado.httpserver

from handlers.member_request_handler import MemberHandler, MembersHandler
from handlers.group_request_handler import GroupHandler, GroupsHandler
from handlers.web_socket_handler import WebSocketHandler
from datetime import datetime
from config.constants import PORT

define("port", default=PORT, help="run on the given port", type=int)


class Application(tornado.web.Application):

    def __init__(self):
        handlers = [
            (r"/ws", WebSocketHandler),
            #(r"/login", LoginHandler),
            (r"/group/([0-9]+)", GroupHandler),
            (r"/group/", GroupHandler),
            (r"/groups/", GroupsHandler),
            (r"/member/([0-9]+)", MemberHandler),
            (r"/member/", MemberHandler),
            (r"/members/", MembersHandler),

        ]
        settings = dict(
            cookie_secret="sjw4f8hfy*ikdmfjcyeb[sjn9",
            login_url="/login",
            xsrf_cookies=True,
            autoreload=True,
            debug=False
        )
        tornado.web.Application.__init__(self, handlers, **settings)


def server_time():
    today = datetime.now()
    return str(today.hour)+':'+str(today.minute)+':'+str(today.second)+'h'


def main():
    #start client udp
    #ClientUdp.start((constants.URL_MOBILE_BRIDGE, constants.PORT_MOBILE_BRIDGE))

    #Setup Tronado
    tornado.options.parse_command_line()
    app = Application()
    print '-'*90

    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(options.port)

    #Start Main application
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    print 'Starting Chat Server on port', PORT, ' at ', server_time()
    main()

