import sys
import zmq
import numpy as np
import json

class ZmqConfigClient():
    def __init__(self, remote):
        #  Socket to talk to server
        self.context = zmq.Context()

        self.subscriber = self.context.socket(zmq.SUB)
        self.subscriber.connect(remote)
        self.subscriber.setsockopt(zmq.SUBSCRIBE, b"config")

        self.mode = 'user'

        self.on = True

    def run(self):
        pass

    def run_threaded(self):
        config = self.config
        self.config = None
        return config, self.mode

    def update(self):
        while self.on:
            [address, config_string] = self.subscriber.recv_multipart()
            data = json.loads(config_string)
            if 'model_path' in data:
                model_path = data['model_path']
                if data['model_path'] != '':
                    if model_path.find('-blur-') >= 0:
                        data['apply_blur'] = True
                    if model_path.find('-clahe-') >= 0:
                        data['apply_clahe'] = True
                    if model_path.find('-crop') >= 0:
                        crop_data = re.match(r"-crop(\d*)-", model_path)
                        print(crop_data.groups())
                        crop_level = int(crop_data.groups()[0])
                        if crop_level > 60:
                            data['crop_bottom'] = crop_level
                        else:
                            data['crop_top'] = crop_level
                    self.mode = 'local_angle'
                else:
                    self.mode = 'user'
            self.config = data

    def shutdown(self):
        # indicate that the thread should be stopped
        self.on = False
        print('stoping ZmqConfig')
        self.subscriber.close()
        self.context.term()
