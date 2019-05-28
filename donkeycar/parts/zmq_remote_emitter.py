import sys
import zmq
import time

class ZmqRemoteEmitter():
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

    def run_threaded(self, angle, throttle):
        self.angle = angle
        self.throttle = throttle

    def update(self):
        while self.on:
            if self.angle != None and self.throttle != None:
                self.publisher.send("{} {} {}".format("remote", self.angle, self.throttle).encode())
                self.angle = None
                self.throttle = None
            time.sleep(0.1)
            

    def shutdown(self):
        # indicate that the thread should be stopped
        self.on = False
        print('stoping ZmqRemoteEmitter')
        self.publisher.close()
        self.context.term()
