import sys
import zmq
import numpy as np
import json

class ZmqRemoteEmitter():
    def __init__(self, binding = "tcp://*:5555"):
        #  Socket to talk to server
        self.context = zmq.Context()

        self.publisher = self.context.socket(zmq.PUB)
        self.publisher.bind(binding)

        self.angle = None
        self.throttle = None
        self.mode = None

        self.on = True

    def run(self):
        pass

    def run_threaded(self, angle, throttle, mode):
        self.angle = angle
        self.throttle = throttle
        # remote only allow to switch between automatic modes
        if mode != 'user':
            self.mode = mode

    def update(self):
        while self.on:
            if self.angle != None and self.throttle != None and self.mode != None:
                self.publisher.send("remote %d %d %s" % (self.angle, self.throttle, self.mode))
                self.angle = None
                self.throttle = None
                self.mode = None

    def shutdown(self):
        # indicate that the thread should be stopped
        self.on = False
        print('stoping ZmqRemoteEmitter')
        self.publisher.close()
        self.context.term()
