import sys
import zmq
import numpy as np
import time

class ZmqSpeedSensor():
    def __init__(self, remote):
        #  Socket to talk to server
        self.context = zmq.Context()

        self.subscriber = self.context.socket(zmq.SUB)
        self.subscriber.connect(remote)
        self.subscriber.setsockopt(zmq.SUBSCRIBE, b"speed")

        self.on = True

        self.last_time = time.time() + 5
        self.speed = 0

    def run(self):
        [address, speed] = self.subscriber.recv_multipart()
        self.speed = float(speed)/1000
        return self.speed

    def run_threaded(self):
        return self.speed

    def update(self):
        while self.on:
            [address, speed] = self.subscriber.recv_multipart()
            self.speed = float(speed)/1000
            tt = time.time()
            if self.last_time < tt:
                self.last_time = tt + 1
                print('Speed ' + str(self.speed))

    def shutdown(self):
        # indicate that the thread should be stopped
        self.on = False
        print('stoping ZmqSpeed')
        self.subscriber.close()
        self.context.term()
