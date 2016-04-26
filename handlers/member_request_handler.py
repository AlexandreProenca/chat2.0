#!/usr/bin/env python
#  -*- coding: utf-8 -*-
import json
import time
import tornado.ioloop
import tornado.web
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import logging
from config.constants import DEBUG
from models.models import Base, Member
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


class MemberHandler(tornado.web.RequestHandler):

    def initialize(self):
        self.db = DBSession()
        self.set_header('Content-Type', 'application/json')

    def get(self, _id):
        self.write(str(self.db.query(Member).filter_by(id=int(_id)).first()))

    def post(self):
        timestamp = time.time()
        member = Member(
                status=1,
                group_id=self.get_argument('group'),
                user_id=self.get_argument('user'),
                seen=None,
                received=None,
                admin=False,
                resource=self.get_argument('resource'),
                joined=timestamp
            )

        self.db.add(member)
        self.db.commit()
        logging.info("MEMBRO CRIADO %s" % member) if DEBUG else ''
        location = "/member/" + str(member.id)
        self.set_header('Location', location)
        self.set_status(201)
        self.write(str(member))

    def put(self, _id):
        member = self.db.query(Member).filter_by(id=_id).first()
        member.status = int(self.get_argument('status'))
        # member.group_id = int(self.get_argument('group'))
        # member.user_id = int(self.get_argument('user'))
        member.admin = bool(self.get_argument('admin'))
        self.db.add(member)
        self.db.commit()
        logging.info("MEMBRO ATUALIZADO %s" % member) if DEBUG else ''
        self.write(str(member))

    def delete(self, _id):
        member = self.db.query(Member).filter_by(id=_id).first()
        self.db.delete(member)
        self.db.commit()
        logging.info("MEMBRO DELETADO %s" % member) if DEBUG else ''
        self.write(str(member))


class MembersHandler(tornado.web.RequestHandler):

    def initialize(self):
        self.db = DBSession()
        self.set_header('Content-Type', 'application/json')

    def get(self):
        members = self.db.query(Member).order_by(Member.joined)
        self.write(str([g for g in members]))

    def delete(self):
        row = self.db.query(Member).delete()
        self.db.commit()
        self.write({"row_deleted": row})


