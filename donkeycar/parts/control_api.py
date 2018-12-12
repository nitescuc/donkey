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
        self.config = None

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
    
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
    def post(self):
        data = tornado.escape.json_decode(self.request.body)
        if 'drive_mode' in data:
            self.application.mode = data['drive_mode']
        if 'recording' in data:
            self.application.recording = data['recording']
    def options(self):
        # no body
        self.set_status(204)
        self.finish()

class ConfigAPI(tornado.web.RequestHandler):    

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
    def post(self):
        data = tornado.escape.json_decode(self.request.body)
        self.application.config = data
        if 'model_path' in data:
            if data['model_path'] != '':
                self.application.mode = 'local_angle'
            else:
                self.application.mode = 'user'
    def options(self):
        # no body
        self.set_status(204)
        self.finish()
