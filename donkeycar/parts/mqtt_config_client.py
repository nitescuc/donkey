import json
import paho.mqtt.subscribe as subscribe
import re


class MqttConfigClient():
    def __init__(self, host="localhost", port=1883):
        self.host = host
        self.port = port
        self.mode = 'user'
        self.config = None

        self.on = True

    def on_message(self, client, userdata, message):
        print("Config Received mqtt message %s %s" % (message.topic, message.payload.decode()))
        data = json.loads(message.payload.decode())
        if 'model_path' in data:
            model_path = data['model_path']
            if data['model_path'] != '':
                if model_path.find('-blur-') >= 0:
                    data['apply_blur'] = True
                else:
                    data['apply_blur'] = False
                if model_path.find('-clahe') >= 0:
                    data['apply_clahe'] = True
                else:
                    data['apply_clahe'] = False
                if model_path.find('-crop') >= 0:
                    try:
                        crop_data = re.search(r"-crop(\d*)-", model_path)
                        print(crop_data.groups())
                        crop_level = int(crop_data.groups()[0])
                        if crop_level > 60:
                            data['crop_bottom'] = crop_level
                        else:
                            data['crop_top'] = crop_level
                    except Exception as err:
                        print('Config regex error')
                        print(err)
                self.mode = 'local_angle'
            else:
                self.mode = 'user'
        self.config = data

    def run(self):
        pass

    def run_threaded(self):
        config = self.config
        self.config = None
        return config, self.mode

    def update(self):
        subscribe.callback(self.on_message, "config", hostname=self.host, port=self.port)
        pass

    def shutdown(self):
        # indicate that the thread should be stopped
        self.on = False
        print('stoping MqttConfig')
        self.subscriber.close()
        self.context.term()
