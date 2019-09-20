#!/usr/bin/env python3
"""
Scripts to drive a donkey 2 car and train a model for it. 

Usage:
    manage.py (drive)
    manage.py (calibrate)
    manage.py (record)

Options:
    -h --help        Show this screen.
    --tub TUBPATHS   List of paths to tubs. Comma separated. Use quotes to use wildcards. ie "~/tubs/*"
    --js             Use physical joystick.
"""
import os
import logging
# set up logging to file - see previous section for more details
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s.%(msecs)03d %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M:%S',
                    filename='data/donkey.log',
                    filemode='w')
# define a Handler which writes INFO messages or higher to the sys.stderr
console = logging.StreamHandler()
console.setLevel(logging.ERROR)
# set a format which is simpler for console use
formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
# tell the handler to use this format
console.setFormatter(formatter)
# add the handler to the root logger
logging.getLogger('').addHandler(console)

from docopt import docopt

import donkeycar as dk

# import parts
from donkeycar.parts.camera import JetsonCV2Webcam
from donkeycar.parts.camera_calibrate import ImageCalibrate
from donkeycar.parts.preprocess import ImageProcessor
from donkeycar.parts.transform import Lambda
from donkeycar.parts.keras import KerasCategorical
from donkeycar.parts.datastore import TubHandler, TubGroup
from donkeycar.parts.zmq_actuator_emitter import ZmqActuatorEmitter
from donkeycar.parts.zmq_config_client import ZmqConfigClient
from donkeycar.parts.zmq_remote_receiver import ZmqRemoteReceiver
from donkeycar.parts.control_api import APIController
from donkeycar.parts.web_fpv.web import FPVWebController
from donkeycar.parts.speed_controller import SpeedController
from donkeycar.parts.zmq_speed_sensor import ZmqSpeedSensor

from sys import platform

def drive(cfg):
    '''
    Start the drive loop
    Each part runs as a job in the Vehicle loop, calling either
    it's run or run_threaded method depending on the constructor flag `threaded`.
    All parts are updated one after another at the framerate given in
    cfg.DRIVE_LOOP_HZ assuming each part finishes processing in a timely manner.
    Parts may have named outputs and inputs. The framework handles passing named outputs
    to parts requesting the same named input.
    '''

    # Initialize car
    V = dk.vehicle.Vehicle()

    ctr = APIController()
    V.add(ctr, outputs=['user/mode', 'recording', 'config'], threaded=True)

    def apply_config(config):
        if config != None:
            V.apply_config(config)
    apply_config_part = Lambda(apply_config)
    V.add(apply_config_part, inputs=['config'])

    preprocess = ImageProcessor(resolution=cfg.CAMERA_RESOLUTION, applyClahe=True, applyBlur=True)
    cam = JetsonCV2Webcam(resolution=cfg.CAMERA_RESOLUTION, framerate=cfg.CAMERA_FRAMERATE, processor=preprocess)
    V.add(cam, outputs=['cam/image_array'], threaded=True, can_apply_config=True)

    def pilot_condition(mode):
        if mode == 'user':
            return False
        else:
            return True

    pilot_condition_part = Lambda(pilot_condition)
    V.add(pilot_condition_part, inputs=['user/mode'], outputs=['run_pilot'])

    kl = KerasCategorical()
    V.add(kl, inputs=['cam/image_array'],
        outputs=['pilot/angle', 'pilot/throttle'],
        run_condition='run_pilot', threaded=False, can_apply_config=True)

    crt = ZmqSpeedSensor(remote=cfg.ZMQ_SPEED)
    V.add(crt,
        inputs=[],
        outputs=['speed'],
        threaded=True)

    ctr = SpeedController(slow_throttle=cfg.SLOW_THROTTLE, medium_throttle=cfg.MEDIUM_THROTTLE, fast_throttle=cfg.FAST_THROTTLE, 
        break_sequence=cfg.BREAK_SEQUENCE)
    V.add(ctr,
        inputs=['pilot/throttle', 'user/mode', 'speed'],
        outputs=['pilot/throttle'],
        run_condition='run_pilot',
        threaded=False)

    ctr = ZmqActuatorEmitter(binding=cfg.ZMQ_ACTUATOR_EMITTER)
    V.add(ctr, 
        inputs=['pilot/angle', 'pilot/throttle', 'user/mode'],
        outputs=[],
        run_condition='run_pilot', threaded=False, can_apply_config=False)

    print("You can now go to <your pi ip address>:8887 to drive your car.")

    # run the vehicle for 20 seconds
    V.start(rate_hz=cfg.DRIVE_LOOP_HZ, max_loop_count=cfg.MAX_LOOPS)


def record(cfg):
    V = dk.vehicle.Vehicle()

    cam = JetsonCV2Webcam(resolution=cfg.CAMERA_RESOLUTION, framerate=cfg.CAMERA_FRAMERATE)
    V.add(cam, outputs=['cam/image_array'], threaded=True, can_apply_config=True)

    ctr = ZmqRemoteReceiver(remote=cfg.ZMQ_REMOTE)
    V.add(ctr, 
        inputs=[],
        outputs=['user/angle', 'user/throttle', 'recording'],
        threaded=True, can_apply_config=False)

    # add tub to save data
    inputs = ['cam/image_array', 'user/angle', 'user/throttle']
    types = ['image_array', 'float', 'float']

    th = TubHandler(path=cfg.DATA_PATH)
    tub = th.new_tub_writer(inputs=inputs, types=types)
    V.add(tub, inputs=inputs, run_condition='recording')

    V.start(rate_hz=30, max_loop_count=cfg.MAX_LOOPS)

    print("You can now go to <your pi ip address>:8887 to drive your car.")


def calibrate(cfg):
    # Initialize car
    V = dk.vehicle.Vehicle()

    cam = JetsonCV2Webcam(resolution=(480, 640), framerate=cfg.CAMERA_FRAMERATE)
    V.add(cam, outputs=['cam/image_array'], threaded=True)
    calibrate = ImageCalibrate((480,640))
    V.add(calibrate, inputs=['cam/image_array'], outputs=['cam/image_array'], threaded=False)

    fpv = FPVWebController()
    V.add(fpv,
            inputs=['cam/image_array'],
            threaded=True)        
    # run the vehicle for 20 seconds
    V.start(rate_hz=cfg.DRIVE_LOOP_HZ, max_loop_count=cfg.MAX_LOOPS)
    print("You can now go to <your pi ip address>:8887 to drive your car.")


if __name__ == '__main__':
    args = docopt(__doc__)
    cfg = dk.load_config()

    if args['drive']:
        drive(cfg)

    if args['record']:
        record(cfg)

    if args['calibrate']:
        calibrate(cfg)




