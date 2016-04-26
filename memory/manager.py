

import jwt
import logging
import sys
from user import User
from room import Room
import json
import time
import uuid
import api_mongo


class Heartbeat:
    time_heart = 0
    time_delta = 120.0

    def __init__(self):
        pass

    @classmethod
    def ping_broadcast(cls):
        if (time.time() - Heartbeat.time_heart) > Heartbeat.time_delta:
            info = {"type": "ping", "payload": {"command": "ping", "details": "ping"}}
            for waiter in User.users:
                if waiter:
                    try:
                        waiter.connection.write_message(info)
                    except Exception, e:
                        pass
            Heartbeat.time_heart = time.time()


def send_to_parse(parsed, _user):
    print '-'* 90
    if type(parsed) is dict:
        if 'payload' in parsed:
            if 'command' in parsed['payload']:
                if parsed['payload']['command'] == 'room_message':
                    print 'parsed room message:', parsed
                    print 'user network:', _user.networkId
                    _message = parsed['payload']['message']
                    _room_id = parsed['payload']['room_id']
                    _sender = parsed['payload']['sender']


def send_to_parse_multicast(parsed, user_list):
    print '=' * 90
    if type(parsed) is dict:
        if 'payload' in parsed:
            if 'command' in parsed['payload']:
                if parsed['payload']['command'] == 'room_message':
                    for u in user_list:
                        _message = parsed['payload']['message']
                        _room_id = parsed['payload']['room_id']


def server_prepare():
    logging.getLogger("requests").setLevel(logging.WARNING)
    t_start = time.time()

    try:
        if api_mongo.read_room_list():
            rooms_to_connect_dict = json.loads(api_mongo.read_room_list())['payload']['details']
            rooms_to_connect_type = json.loads(api_mongo.read_room_list())['payload']['command']  # trata lista vazia
            print ('\t API Mongo read rooms success!')

            if not (rooms_to_connect_type == 'error'):
                if len([r['room'] for r in rooms_to_connect_dict]) > 0:
                    [room_restore(room_to_connect) for room_to_connect in [r['room'] for r in rooms_to_connect_dict]]

                print '\tserver config end after (ms):', (time.time() - t_start) * 1000

            return True

        else:
            print 'ERROR - please turn on Mongo DB API '
            return False
    except Exception, e:
        print 'Error:', e
        print 'PLEASE - CHECK MONGO'
        return False


def room_restore(room_name):
    '''
    Metodo que restaura uma sala em memoria
    :param room_name:
    :return:
    '''
    rooms = json.loads(api_mongo.read_room(room_name))

    if rooms:
        data = rooms["payload"]["details"]
        users_name = data['users_name']
        dt = data['dt']
        room = data['room']
        alias = data['alias']
        resource = data['resource']
        is_group = data['is_group']
        last_message = data['last_message']

        Room.restore(users_name, dt, room, alias, resource, is_group, last_message)


def send(user, info):
    target_sent = []
    for u in User.users:
        if (u.username == user.username) and (u.resource == user.resource):
            if [u.connection] not in target_sent:
                target_sent.append([u.connection])
                u.connection.write_message(info)


def send_broadcast(list_to_send, info, audience):
    target_sent = []

    if list_to_send:
        if list_to_send:
            for el in list_to_send:
                for waiter in User.users:
                    if (waiter.username == el) and (waiter.resource == audience):
                        if [waiter.connection] not in target_sent:
                            target_sent.append([waiter.connection])
                            try:
                                if waiter:
                                    waiter.connection.write_message(info)

                            except Exception, e:
                                print("EXCEPTION ", e)
                                pass


def send_system_info(sock, destination, message, user_name):
    data = {'message': message,
            'destination': destination,
            'sender': 'system_info',
            'target': user_name}
    room_message(sock, data)


def notification(user_target, audience, info):
    for waiter in User.users:
        try:
            if waiter:
                if (waiter.username == user_target) and (waiter.resource == audience):
                    waiter.connection.write_message(info)
        except Exception, e:
            print "Exception:", sys.exc_info()[0], e
            logging.error("Error sending message", exc_info=True)


def notification_broadcast(audience, info):
    for waiter in User.users:
        try:
            if waiter:
                if waiter.resource == audience:
                    waiter.connection.write_message(info)
        except Exception, e:
            print "Exception:", sys.exc_info()[0], e
            logging.error("Error sending message", exc_info=True)


def login(sock, token):
    user_login = User.find_user_by_sock(sock)  # sock para user

    # Options to set JWT decode
    options = {
        'verify_signature': True,
        'verify_exp': True,
        'verify_nbf': False,
        'verify_iat': False,
        'verify_aud': False,
        'require_exp': False,
        'require_iat': False,
        'require_nbf': False
    }

    if float(jwt.__version__[:3]) < 1.3:
        print 'ERROR - JWT MUST BE >= 1.3'
        sys.exit(0)

    info = False
    try:
        info = jwt.decode(token, 'socialbase', options=options)
    except Exception, e:
        text = '{"type":"authenticate","payload":{"status":"EXPIRED_CREDENTIALS","message":"authentication error"}}'
        send(user_login, text)

    if info:
        user_login.iss = info['iss']
        user_login.network = info['network']['name']
        user_login.exp = info['exp']
        user_login.username = info['user']['username']
        user_login.resource = info['network']['resource']
        user_login.networkId = info['network']['key']

        user_db = json.loads(api_mongo.read_user(info['user']['username'], user_login.resource))
        user_login.status = int(user_db['payload']['details']['status'])

        text = '{"type":"authenticate","payload":{"status":"OK"}}'
        send(user_login, text)

        api_mongo.insert_user(info['user']['username'], user_login.resource)

        reconnect_rooms(sock, user_login.username)
        contacts_online(sock)
    else:
        print 'JWT PARSE NOT POSSIBLE'
        close(sock)


def reconnect_rooms(sock, user):
    li = room_list_by_user(sock=None, data={'sender': user}, call=False)
    for el in li:
        r = Room.find_room_by_name(el['room'])
        for u in adapter(r.users_name):
            if u == user:
                s = User.find_user_by_sock(sock)
                s.connection = sock


def user_list(sock):

    info = api_mongo.user_list()
    user_login = User.find_user_by_sock(sock)
    send(user_login, info)


def user_status(sock, data):
    user_login = User.find_user_by_sock(sock)

    if int(data['number']) != 0:
        user_login.status = int(data['number'])
        api_mongo.user_status_change(user_login.username, user_login.status)

    info = {"type": "chat", "payload": {"command": "user_status", "details": user_login.status}}

    li = []
    for el in User.users:
        if el.username == user_login.username:
            li.append(el.username)

    send_broadcast(li, info, user_login.resource)

    if int(data['number']) != 0:
        contacts_online(sock)


def user_change_text(sock, data):
    destination = data['destination']
    tp = data["type"]

    u = User.find_user_by_sock(sock)
    list_user = Room.find_users_by_room(destination)

    info = {"type": "chat",
            "payload": {"command": "user_change_text",
                        "room_id": destination,
                        "user": u.username,
                        "type": tp}}
    send_broadcast(list_user, info, u.resource)


def contacts_online(sock):
    network_obj = User.find_network_by_sock(sock)

    if network_obj:
        contacts_broadcast(network_obj)


def contacts_broadcast(resource):
    ulist = User.who_online_by_net(resource)
    info = {"type": "chat", "payload": {"command": "contacts_online", "details": [dict(t) for t in set([tuple(d.items()) for d in ulist])]}}
    if len(ulist) > 0:
        list_to_send = []
        for el in ulist:
            list_to_send.append(el['user_name'])
        send_broadcast(list_to_send, info, resource)


def room_list(sock):
    user_call = User.find_user_by_sock(sock)

    def make_list():
        dict_list = []

        for r in Room.rooms:
            if r.room_id != '':
                if user_call.resource == r.resource:
                    if user_call.username in [i['username'] for i in r.users_name]:
                        dict_list.append({'room_id': r.room_id, 'alias': r.alias, "last_message": r.last_message,
                                          'users': r.users_name, 'is_group': r.is_group})
        return dict_list

    info = {"type": "chat", "payload": {"command": "room_list", "details": make_list()}}
    send(user_call, info)


def room_list_by_user(sock=None, data=None, call=True):
    def make_list():
        dict_list = []
        for r in Room.rooms:
            if r.users_name:
                for el in adapter(r.users_name):
                    if el == data['sender']:
                        dict_list.append({'room': r.room_id, "last_message": r.last_message})
        return dict_list

    info = {"type": "chat", "payload": {"command": "room_list_by_user", "details": make_list()}}

    if call:
        user_login = User.find_user_by_sock(sock)
        send(user_login, info)

    return make_list()


def user_list_by_room(sock, data=None):  # friends
    u = User.find_user_by_sock(sock)

    def make_list():
        dict_list = []
        for r in Room.rooms:
            if r.room_id == data['destination']:
                if r.users_name:
                    for el in adapter(r.users_name):
                        if u.username != el:
                            dict_list.append(el)
                    break
        return dict_list

    if sock:
        alias = Room.find_alias_by_room(data['destination'])
        info = {"type": "chat",
                "payload": {"command": "user_list_by_room", "alias": alias, "room_id": data['destination'],
                            "details": make_list()}}

        user_login = User.find_user_by_sock(sock)
        send(user_login, info)
    return make_list()


def room_history(sock=None, data=None):
    r = Room.find_room_by_name(data['destination'])

    since = 0
    if 'since' in data:
        since = data['since']

    h = r.history_read(since)
    h2 = json.loads(h)

    if sock:
        info = {"type": "chat", "payload": {"command": "room_history", "details": h2}}
        user_login = User.find_user_by_sock(sock)
        send(user_login, json.dumps(info))


def room_rename(sock, data=None):
    u = User.find_user_by_sock(sock)
    r = Room.find_room_by_name(data['destination'])
    r.alias = data['room_rename']
    api_mongo.rename_room(data['destination'], data['room_rename'])
    list_user = Room.find_users_by_room(data['destination'])
    info = {"type": "chat",
            "payload": {"command": "room_rename",
                        "room_id": data['destination'],
                        "alias": data['room_rename']}}
    send_broadcast(list_user, info, u.resource)


def room_create(sock, data):
    user = User.find_user_by_sock(sock)
    target_name = data['details']['new_user']

    echo = None
    if "echo" in data:
        echo = data['echo']

    target_resource = user.resource
    target_online = User.find_user_by_name(target_name, user.resource)  # sock de outro usuario conectado
    target_offline = None
    if not target_online:
        api_mongo.insert_user(target_name, target_resource)
        target_offline = target_name

    if user == target_online:
        info = {"type": "chat", "payload": {"command": "error", "details": "choose_another_less_you"}}
        send(user, info)
    else:
        second_user = None
        if target_online:
            second_user = target_online.username
        if not second_user:
            second_user = target_offline

        if second_user:
            if not Room.check_exist_room([user.username, second_user], user.resource):  # se sala nao existe

                user_temp = []
                for username in [user.username, second_user]:
                    user_temp.append({"username": username, "seen": None, "received": None})

                room_name = Room.open(user_temp, target_resource)  # cria a sala e recebe nome unico a sala
                new_room = Room.find_room_by_name(room_name)  # sock para o nova sala criada
                new_room.users_name = user_temp  # insert two news name users
                new_room.alias = 'DEFAULT'  # insert alias
                alias = new_room.alias
                api_mongo.insert_room(user_temp, room_name, alias, target_resource, False, None)
                info = {"type": "chat", "payload": {"command": "room_id",
                                                    "alias": new_room.alias,
                                                    "room_id": room_name,
                                                    "users": user_temp,
                                                    "echo": echo,
                                                    "is_group": False}}
                send(user, info)
            else:  # se sala ja existe
                user_temp = []
                for username in [user.username, second_user]:
                    user_temp.append({"username": username, "seen": None, "received": None})

                room_to_append = Room.find_room_by_users([user.username, second_user], user.resource)
                room_restore(room_to_append)
                new_room = Room.find_room_by_name(room_to_append)  # sock para o nova sala criada
                info = {"type": "chat", "payload": {"command": "room_id",
                                                    "alias": new_room.alias,
                                                    "room_id": room_to_append,
                                                    "users": user_temp,
                                                    "is_group": new_room.is_group}}
                send(user, info)


def room_enter(sock, data):
    logging.info(' room_enter data{}: %r', data)
    user = User.find_user_by_sock(sock)
    alias = data['alias']
    room_sock = Room.find_room_by_alias(alias)  # objeto da sala com esse alias

    if room_sock:
        if user.username in adapter(room_sock.users_name):  # verifica se esse usuario esta nessa sala
            room_restore(room_sock.name)  # coloca na memoria a sala encontrada

            info = {"type": "chat", "payload": {"command": "room_id",
                                                "room_id": room_sock.name,
                                                "alias": room_sock.alias}}
            for el in adapter(room_sock.users_name):  # envia room_id para todos os users do room
                u = User.find_user_by_name(el, user.resource)
                if u:
                    send(u, info)


def room_reopen(sock, data):
    user = User.find_user_by_sock(sock)
    destination = data['room_id']
    room_sock = Room.find_room_by_name(destination)  # objeto da sala com esse alias

    if room_sock:
        if any(d['username'] == user.username for d in room_sock.users_name):
            if user.resource == room_sock.resource:

                room_restore(room_sock.room_id)  # coloca na memoria a sala encontrada

                info = {"type": "chat", "payload": {"command": "room_id",
                                                    "room_id": room_sock.room_id,
                                                    "alias": room_sock.alias,
                                                    "is_group": room_sock.is_group}}

                if 'origin' in data:  # para abrir a janela de chat de maneiras diferentes
                    info = {"type": "chat", "payload": {"command": "room_id",
                                                        "room_id": room_sock.room_id,
                                                        "alias": room_sock.alias,
                                                        "origin": data['origin'],
                                                        "is_group": room_sock.is_group}}

                send(user, info)


def room_message(sock, data):
    # logging.info(' room_message data{}: %r', data)
    sender = data['sender']
    destination = data['destination']
    t = time.time()
    u = User.find_user_by_sock(sock)

    if 'message' in data:
        message = data['message']
        alias = Room.find_alias_by_room(destination)
        r = Room.find_room_by_name(data['destination'])
        r.last_message = t
        target = data['target'] if 'target' in data else ''
        message_id = str(uuid.uuid4())
        Room.history_add(sender, destination, message, alias, target, message_id, t)

        info = {
            "type": "chat",
            "payload": {
                "command": "room_message",
                "dt": t,
                "message": message,
                "room_id": destination,
                "sender": sender,
                "alias": alias,
                "target": target,
                "message_id": message_id
            }
        }

        list_user = Room.find_users_by_room(destination)
        send_broadcast(list_user, info, u.resource)

        if not sender == "system_info":
            sub_list = Room.find_users_instance_by_room(destination, u.networkId)
            sub_list.remove({'networkId': u.networkId, 'username': sender})
            send_to_parse_multicast(info, sub_list)


def room_user_add(sock, data):
    u = User.find_user_by_sock(sock)
    new_users_name = data['details']['new_user']
    if type(new_users_name) is unicode:
        new_users_name = [data['new_user']]

    echo = None
    if "echo" in data:
        echo = data['echo']

    origin = data['details']['destination']
    room_users = Room.find_users_by_room(origin)  # Lista de usuarios em uma sala
    u_list = []

    for el in new_users_name:
        if not (el in room_users):
            u_list.append(el)

    if room_users:
        for el in room_users:
            u_list.append(el)

    destination = Room.check_exist_room(u_list, u.resource)

    if not destination:
        room_name = Room.open([], u.resource)  # cria a sala e recebe nome unico a sala
        new_room = Room.find_room_by_name(room_name)  # sock para o nova sala criada
        destination = new_room.room_id
        new_room.is_group = True
        new_room.last_message = time.time()
        new_room.alias = 'DEFAULT'  # todo - validar nome default

        # for unew in u_list:  # todo validar se os usuarios estao off-line
        #     if unew != User.find_user_by_name(unew, u.resource)['username']:
        #         api_mongo.insert_user(unew, u.resource)

        obj_users = [{"username": i, "seen": None, "received": None} for i in u_list]
        api_mongo.insert_room(obj_users, room_name, new_room.alias, u.resource, True, new_room.last_message)

    if destination:
        room_restore(destination)
        new_room = Room.find_room_by_name(destination)  # sock para o nova sala criada
        [send_system_info(sock, destination, 'USER ADD', el) for el in new_users_name]  # envia message para grupo da entrada do user
        new_room.users_name = []
        obj_users = [{"username": i, "seen": None, "received": None} for i in u_list]
        new_room.users_name = obj_users
        new_room.is_group = True
        new_room.last_message = time.time()

        info = {
            "type": "chat",
            "payload": {
                "command": "room_id",
                "alias": new_room.alias,
                "room_id": new_room.room_id,
                "is_group": True,
                "users": obj_users,
                "echo": echo,
                "last_message":  new_room.last_message
            }
        }

        send_broadcast(room_users, info, u.resource)


def user_remove(sock, data):
    # logging.info(' room_leave data{}:\n %r', data)

    users_to_remove = data['user_remove']
    if type(users_to_remove) is unicode:
        users_to_remove = [data['user_remove']]

    u = User.find_user_by_sock(sock)

    users_remove = data['user_remove']
    if type(users_remove) is unicode:
        users_remove = [data['user_remove']]

    print("USERS REMOVE ", users_remove)

    destination = data['destination']  # id de sala a ser alterada
    room_users = Room.find_users_by_room(destination)  # Lista de usuarios em uma sala

    print("ROOOMS USERS", room_users)

    for el in users_remove:  # envia mensagem dos novos nomes
        send_system_info(sock, destination, 'USER REMOVE', el)  # envia message para grupo da saida do user

    u_list = []  # lista final
    for el in room_users:
        if not (el in users_remove):
            u_list.append(el)

    new_room = Room.find_room_by_name(destination)  # sock para o nova sala alterada
    new_room.users_name = [{"username": _u, "seen": None, "received": None} for _u in u_list]

    current_user = User.find_user_by_sock(sock)

    for uremove in users_to_remove:
        api_mongo.remove_user_room(destination, uremove)
        u = User.find_user_by_name(uremove, u.resource)
        if u:
            info = {"type": "chat", "payload": {"command": "user_remove",
                                                "room_id": destination}}
            send(u, info)


def open(sock):
    User.open(sock)


def logout(sock):
    close(sock)


def close(sock):
    network_obj = User.find_network_by_sock(sock)

    if network_obj:
        User.close(sock)
        contacts_broadcast(network_obj)
    else:
        User.close(sock)


def system_call(sock, data):
    sock.connection.write_message(data)


def monitor(sock, data):


    u = User.find_user_by_sock(sock)
    print 'command from:', u.username
    command = data['command']
    room_name = data['destination']

    if command == 'users':
        li = []
        for el in User.users:
            if el.username:
                li.append([el.username, el.network])
        print 'Number users on:', len(li), '---', len(User.users)
        for el in li:
            print el
    if command == 'rooms':
        r = Room.find_room_by_name(room_name)
        try:
            print 'room alias:', r.alias
            print 'room users_name:', adapter(r.users_name)
        except:
            print 'no room'
    if command == 'message':
        u = User.find_user_by_name('sbsuporte@socialbase.com.br', 'dev-socialbase')

        info = {"type": "chat", "payload": {"command": "test_user",
                                            "details": str(u)}}

        u.connection.write_message(info)
        print 'B.sended to ', u.username, info




def adapter(d):
    return [i['username'] for i in d]
