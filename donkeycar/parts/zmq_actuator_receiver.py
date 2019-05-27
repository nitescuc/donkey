import sys
import zmq

class ZmqActuatorReceiver():
    def __init__(self, remote):
        #  Socket to talk to server
        self.context = zmq.Context()

        self.subscriber = self.context.socket(zmq.SUB)
        self.subscriber.connect(remote)
        self.subscriber.setsockopt(zmq.SUBSCRIBE, b"angle_throttle")

        self.angle = None
        self.throttle = None

        self.on = True

        self.speed = 0

    def run(self):
        pass

    def run_threaded(self):
        return self.angle, self.throttle

    def update(self):
        while self.on:
            [address, angle, throttle] = self.subscriber.recv_multipart()
            self.angle = angle
            self.throttle = throttle

    def shutdown(self):
        # indicate that the thread should be stopped
        self.on = False
        print('stoping ZmqActuatorReceiver')
        self.subscriber.close()
        self.context.term()
