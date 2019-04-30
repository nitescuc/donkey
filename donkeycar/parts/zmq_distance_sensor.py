import sys
import zmq
import numpy as np

class ZmqDistanceSensor():
    def __init__(self, remote):
        #  Socket to talk to server
        self.context = zmq.Context()

        self.subscriber = self.context.socket(zmq.SUB)
        self.subscriber.connect(remote)
        self.subscriber.setsockopt(zmq.SUBSCRIBE, b"distance")

        self.on = True

    def run(self):
        [address, distance1, distance2] = self.subscriber.recv_multipart()
        self.distance = min(float(distance1), float(distance2))
        return self.distance

    def run_threaded(self):
        return self.distance

    def update(self):
        while self.on:
            [address, distance1, distance2] = self.subscriber.recv_multipart()
            self.distance = min(float(distance1), float(distance2))

    def shutdown(self):
        # indicate that the thread should be stopped
        self.on = False
        print('stoping ZmqDistance')
        self.subscriber.close()
        self.context.term()
