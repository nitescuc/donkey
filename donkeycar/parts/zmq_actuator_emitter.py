import sys
import zmq
import time

class ZmqActuatorEmitter():
    def __init__(self, binding = "tcp://*:5555"):
        #  Socket to talk to server
        self.context = zmq.Context()

        self.publisher = self.context.socket(zmq.PUB)
        self.publisher.bind(binding)

        self.on = True

    def run(self, angle, throttle, mode):
        if angle == None:
            angle = 7
        if throttle == None:
            throttle = 7
        if mode == None:
            mode = 'user'
        remap_angle = angle * (2/14) - 1
        remap_throttle = throttle * (2/14) - 1
        self.publisher.send_multipart([b"actuator", str(remap_angle).encode(), str(remap_throttle).encode(), mode.encode()], zmq.NOBLOCK)

    def run_threaded(self, angle, throttle, mode):
        pass

    def update(self):
        pass

    def shutdown(self):
        # indicate that the thread should be stopped
        self.on = False
        print('stoping ZmqActuatorEmitter')
        self.publisher.close()
        self.context.term()
