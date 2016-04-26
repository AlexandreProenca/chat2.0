#!/usr/bin/env python
#  -*- coding: utf-8 -*-
import time
import tornado.ioloop
import tornado.web
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import logging
from config.constants import DEBUG
from models.models import Base, Group


engine = create_engine('mysql://nwpartner2:gmmaster765@179.188.16.42/nwpartner2')
Base.metadata.bind = engine
Base.metadata.create_all(engine)
DBSession = sessionmaker(bind=engine)


dir_log = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../logs/chat.log')

logging.basicConfig(format='[%(asctime)s] - %(message)s',
                        datefmt='%d/%m/%Y %I:%M:%S %p',
                        filename=dir_log,
                        level=logging.INFO)


class GroupHandler(tornado.web.RequestHandler):

    def initialize(self):
        self.db = DBSession()
        self.set_header('Content-Type', 'application/json')

    def get(self, _id):
        self.write(str(self.db.query(Group).filter_by(id=int(_id)).first()))

    def post(self):
        timestamp = time.time()
        group = Group(
            title=self.get_argument('title', ''),
            avatar_link=self.get_argument('avatar_link', ''),
            last_message=timestamp,
            created=timestamp
        )

        self.db.add(group)
        self.db.commit()
        self.db.close()
        logging.info("GRUPO CRIADO %s" % group) if DEBUG else ''
        location = "/group/" + str(group.id)
        self.set_header('Location', location)
        self.set_status(201)
        self.write(str(group))

    def put(self, _id):
        group = self.db.query(Group).filter_by(id=_id).first()
        group.title = self.get_argument('title', ''),
        group.avatar_link = self.get_argument('avatar_link', ''),
        group.last_message = time.time()
        self.db.add(group)
        self.db.commit()
        logging.info("GRUPO ATUALIZADO %s" % group) if DEBUG else ''
        self.write(str(group))

    def delete(self, _id):
        group = self.db.query(Group).filter_by(id=_id).first()
        self.db.delete(group)
        self.db.commit()
        logging.info("GRUPO DELETADO %s" % group) if DEBUG else ''
        self.write(str(group))


class GroupsHandler(tornado.web.RequestHandler):

    def initialize(self):
        self.db = DBSession()
        self.set_header('Content-Type', 'application/json')

    def get(self):
        groups = self.db.query(Group).order_by(Group.last_message)
        self.write(str([g for g in groups]))

    def delete(self):
        row = self.db.query(Group).delete()
        self.db.commit()
        self.write({"row_deleted": row})


