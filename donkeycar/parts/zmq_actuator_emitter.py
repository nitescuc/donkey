import sys
import zmq
import numpy as np
import json

class ZmqActuatorEmitter():
    def __init__(self, binding = "tcp://*:5555"):
        #  Socket to talk to server
        self.context = zmq.Context()

        self.publisher = self.context.socket(zmq.PUB)
        self.publisher.bind(binding)

        self.angle = None
        self.throttle = None

        self.on = True

    def run(self):
        pass

    def run_threaded(self, angle, throttle, mode):
        self.angle = angle
        self.throttle = throttle

    def update(self):
        while self.on:
            if self.angle != None and self.throttle != None:
                self.publisher.send("angle_throttle %d %d" % (self.angle, self.throttle))
                self.angle = None
                self.throttle = None

    def shutdown(self):
        # indicate that the thread should be stopped
        self.on = False
        print('stoping ZmqActuatorEmitter')
        self.subscriber.close()
        self.context.term()
