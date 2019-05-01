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
from donkeycar.parts.camera import Webcam
from donkeycar.parts.camera_calibrate import ImageCalibrate
from donkeycar.parts.preprocess import ImageProcessor
from donkeycar.parts.transform import Lambda
from donkeycar.parts.keras import KerasCategorical
from donkeycar.parts.datastore import TubHandler, TubGroup
from donkeycar.parts.nucleo_controller import NucleoController
from donkeycar.parts.control_api import APIController
from donkeycar.parts.web_fpv.web import FPVWebController
from donkeycar.parts.zmq_speed_sensor import ZmqSpeedSensor
from donkeycar.parts.zmq_distance_sensor import ZmqDistanceSensor
from donkeycar.parts.speed_controller import SpeedController

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

    cam = Webcam(resolution=cfg.CAMERA_RESOLUTION, framerate=cfg.CAMERA_FRAMERATE, brightness=cfg.CAMERA_BRIGHTNESS)
    V.add(cam, outputs=['cam/image_array'], threaded=True)
    preprocess = ImageProcessor(resolution=cfg.CAMERA_RESOLUTION, trimBottom=cfg.CAMERA_TRIM_BOTTOM)
    V.add(preprocess, inputs=['cam/image_array'], outputs=['cam/image_array'], threaded=False)

    #This web controller will create a web server that is capable
    #of managing steering, throttle, and modes, and more.
    ctr = APIController()
    V.add(ctr, outputs=['user/mode', 'recording', 'config'], threaded=True)

    def apply_config(config):
        if config != None:
            V.apply_config(config)
    apply_config_part = Lambda(apply_config)
    V.add(apply_config_part, inputs=['config'])

    # See if we should even run the pilot module.
    # This is only needed because the part run_condition only accepts boolean
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
        run_condition='run_pilot', can_apply_config=True)

    # Speed sensor
    speed_sensor = ZmqSpeedSensor(remote=cfg.ZMQ_SPEED)
    V.add(speed_sensor, inputs=[], outputs=['speed'], threaded=True);
    # Distance sensor
    dist_sensor = ZmqDistanceSensor(remote=cfg.ZMQ_DISTANCE)
    V.add(dist_sensor, inputs=[], outputs=['distance'], threaded=True);

    # Speed controller
    ctr = SpeedController(slow_throttle=cfg.SLOW_THROTTLE, medium_throttle=cfg.MEDIUM_THROTTLE, fast_throttle=cfg.FAST_THROTTLE, break_sequence=cfg.BREAK_SEQUENCE)
    V.add(ctr,
        inputs=['pilot/throttle', 'user/mode', 'speed', 'distance'],
        outputs=['pilot/throttle'],
        run_condition='run_pilot',
        threaded=False)

    ctr = NucleoController(cfg.SERIAL_DEVICE, cfg.SERIAL_BAUD)
    V.add(ctr, 
        inputs=['pilot/angle', 'pilot/throttle', 'user/mode', 'recording'],
        outputs=['user/angle', 'user/throttle', 'user/mode', 'recording'],
        threaded=False, can_apply_config=True)

    # Choose what inputs should change the car.
    def drive_mode(mode,
                   user_angle, user_throttle,
                   pilot_angle, pilot_throttle):
        if mode == 'user':
            return user_angle, user_throttle

        elif mode == 'local_angle':
            return pilot_angle, user_throttle

        else:
            return pilot_angle, pilot_throttle

    drive_mode_part = Lambda(drive_mode)
    V.add(drive_mode_part,
          inputs=['user/mode', 'user/angle', 'user/throttle',
                  'pilot/angle', 'pilot/throttle'],
          outputs=['angle', 'throttle'])
    
    # add tub to save data
    inputs = ['cam/image_array', 'user/angle', 'user/throttle', 'user/mode', 'pilot/angle', 'pilot/throttle']
    types = ['image_array', 'float', 'float', 'str', 'numpy.float32', 'numpy.float32']

    th = TubHandler(path=cfg.DATA_PATH)
    tub = th.new_tub_writer(inputs=inputs, types=types)
    V.add(tub, inputs=inputs, run_condition='recording')

    # run the vehicle for 20 seconds
    V.start(rate_hz=cfg.DRIVE_LOOP_HZ,
            max_loop_count=cfg.MAX_LOOPS)

    print("You can now go to <your pi ip address>:8887 to drive your car.")

def record(cfg):
    # Initialize car
    V = dk.vehicle.Vehicle()

    cam = Webcam(resolution=cfg.CAMERA_RESOLUTION, framerate=cfg.CAMERA_FRAMERATE, brightness=cfg.CAMERA_BRIGHTNESS)
    V.add(cam, outputs=['cam/image_array'], threaded=True)

    #This web controller will create a web server that is capable
    #of managing steering, throttle, and modes, and more.
    ctr = APIController()
    V.add(ctr, outputs=['user/mode', 'recording', 'config'], threaded=True)

    def apply_config(config):
        if config != None:
            V.apply_config(config)
    apply_config_part = Lambda(apply_config)
    V.add(apply_config_part, inputs=['config'])

    # See if we should even run the pilot module.
    # This is only needed because the part run_condition only accepts boolean
    def pilot_condition(mode):
        if mode == 'user':
            return False
        else:
            return True
    pilot_condition_part = Lambda(pilot_condition)
    V.add(pilot_condition_part, inputs=['user/mode'], outputs=['run_pilot'])

    # Speed sensor
    speed_sensor = ZmqSpeedSensor(remote=cfg.ZMQ_SPEED)
    V.add(speed_sensor, inputs=[], outputs=['speed'], threaded=True)
    # Distance sensor
    dist_sensor = ZmqDistanceSensor(remote=cfg.ZMQ_DISTANCE)
    V.add(dist_sensor, inputs=[], outputs=['distance'], threaded=True)
    # Speed controller

    ctr = NucleoController(cfg.SERIAL_DEVICE, cfg.SERIAL_BAUD)
    V.add(ctr, 
        inputs=['pilot/angle', 'pilot/throttle', 'user/mode', 'recording'],
        outputs=['user/angle', 'user/throttle', 'user/mode', 'recording'],
        threaded=False, can_apply_config=True)

    # Choose what inputs should change the car.
    def drive_mode(mode,
                   user_angle, user_throttle,
                   pilot_angle, pilot_throttle):
        if mode == 'user':
            return user_angle, user_throttle

        elif mode == 'local_angle':
            return pilot_angle, user_throttle

        else:
            return pilot_angle, pilot_throttle

    drive_mode_part = Lambda(drive_mode)
    V.add(drive_mode_part,
          inputs=['user/mode', 'user/angle', 'user/throttle',
                  'pilot/angle', 'pilot/throttle'],
          outputs=['angle', 'throttle'])
    
    # add tub to save data
    inputs = ['cam/image_array', 'user/angle', 'user/throttle', 'user/mode', 'pilot/angle', 'pilot/throttle', 'speed', 'distance']
    types = ['image_array', 'float', 'float', 'str', 'numpy.float32', 'numpy.float32', 'float', 'float']

    th = TubHandler(path=cfg.DATA_PATH)
    tub = th.new_tub_writer(inputs=inputs, types=types)
    V.add(tub, inputs=inputs, run_condition='recording')

    # run the vehicle for 20 seconds
    V.start(rate_hz=cfg.DRIVE_LOOP_HZ,
            max_loop_count=cfg.MAX_LOOPS)

    print("You can now go to <your pi ip address>:8887 to drive your car.")

def calibrate(cfg):
    # Initialize car
    V = dk.vehicle.Vehicle()

    cam = Webcam(resolution=(480,640), framerate=cfg.CAMERA_FRAMERATE, brightness=cfg.CAMERA_BRIGHTNESS)
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




