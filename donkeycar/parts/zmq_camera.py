import sys
import zmq
import numpy as np

class ZmqCamera():
    def __init__(self, remote):
        #  Socket to talk to server
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PULL)

        self.socket.connect(remote)

        # initialize the frame and the variable used to indicate
        # if the thread should be stopped
        self.frame = None
        self.on = True

    def run(self):
        self.frame = np.frombuffer(memoryview(self.socket.recv()), dtype='uint8').reshape(120,160)
        return self.frame

    def run_threaded(self):
        return np.copy(self.frame)

    def update(self):
        while self.on:
            self.frame = np.frombuffer(memoryview(self.socket.recv()), dtype='uint8').reshape(120,160)

    def shutdown(self):
        # indicate that the thread should be stopped
        self.on = False
        print('stoping ZmqCamera')
        self.socket.close()
