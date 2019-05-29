import sys
import zmq
import time

class ZmqRemoteEmitter():
    def __init__(self, binding = "tcp://*:5555"):
        #  Socket to talk to server
        self.context = zmq.Context()

        self.publisher = self.context.socket(zmq.PUB)
        self.publisher.bind(binding)

        self.on = True

    def run(self, angle, throttle):
        self.publisher.send_multipart([b"remote", str(angle).encode(), str(throttle).encode()], zmq.NOBLOCK)

    def run_threaded(self, angle, throttle):
        pass

    def update(self):
        pass            

    def shutdown(self):
        # indicate that the thread should be stopped
        self.on = False
        print('stoping ZmqRemoteEmitter')
        self.publisher.close()
        self.context.term()
