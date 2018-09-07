# Copyright (C) 2018 SignalFx, Inc. All rights reserved.
import tornado.web


class MyApplication(tornado.web.Application):

    pass


class HelloHandler(tornado.web.RequestHandler):

    def get(self, username='', *args, **kwargs):
        return self.write('hello {}!'.format(username or 'anonymous'))

    head = post = delete = patch = put = options = get
