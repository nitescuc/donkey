import os
import json
import time

import requests

import tornado.ioloop
import tornado.web
import tornado.gen

#from ... import utils

class APIController(tornado.web.Application):

    def __init__(self):
        ''' 
        Create and publish variables needed on many of 
        the web handlers.
        '''

        print('Starting API Controller...')

        self.mode = 'user'
        self.recording = False

        handlers = [
            (r"/drive", DriveAPI),
            (r"/config", ConfigAPI)
            ]

        settings = {'debug': False}

        super().__init__(handlers, **settings)
    
    def update(self, port=8887):
        ''' Start the tornado webserver. '''
        print(port)
        self.port = int(port)
        self.listen(self.port)
        tornado.ioloop.IOLoop.instance().start()


    def run_threaded(self):
        ret = self.config
        self.config = None
        return self.mode, self.recording, ret
        
    def run(self):
        ret = self.config
        self.config = None
        return self.mode, self.recording, ret


class DriveAPI(tornado.web.RequestHandler):
    
    def post(self):
        data = tornado.escape.json_decode(self.request.body)
        if 'drive_mode' in data:
            self.application.mode = data['drive_mode']
        if 'recording' in data:
            self.application.recording = data['recording']

class ConfigAPI(tornado.web.RequestHandler):    

    def post(self):
        data = tornado.escape.json_decode(self.request.body)
        self.application.config = data
