""" 
CAR CONFIG 

This file is read by your car application's manage.py script to change the car
performance. 

EXMAPLE
-----------
import dk
cfg = dk.load_config(config_path='~/d2/config.py')
print(cfg.CAMERA_RESOLUTION)

"""


import os

#PATHS
CAR_PATH = PACKAGE_PATH = os.path.dirname(os.path.realpath(__file__))
DATA_PATH = os.path.join(CAR_PATH, 'data')
MODELS_PATH = os.path.join(CAR_PATH, 'models')

#VEHICLE
DRIVE_LOOP_HZ = 30
MAX_LOOPS = 100000

#CAMERA
CAMERA_RESOLUTION = (120, 160) #(height, width)
CAMERA_FRAMERATE = DRIVE_LOOP_HZ
CAMERA_BRIGHTNESS = -30

#TX
USE_TX_AS_DEFAULT = False
TX_THROTTLE_MIN = 913
TX_THROTTLE_MAX = 2111
TX_STEERING_MIN = 960
TX_STEERING_MAX = 2060
TX_THROTTLE_TRESH = 1470
TX_VERBOSE  = False

SERIAL_DEVICE = '/dev/ttyACM0'
SERIAL_BAUD = 921600
ACT_LIMIT = 0.600
#PI RF; Full pulse length : 18540 - 18680 = 53-54 Hz
USE_PI_RF_AS_DEFAULT = False
PI_RF_THROTTLE_MIN = 1070
PI_RF_THROTTLE_MAX = 2015
PI_RF_STEERING_MIN = 990
PI_RF_STEERING_MAX = 2010
PI_RF_THROTTLE_TRESH = 1500
PI_RF_STEERING_PIN = 12
PI_RF_THROTTLE_PIN = 13
PI_RF_MODE_PIN = 16
PI_RF_VERBOSE  = False

#SONAR
SON_TRIGGER_PIN = 25
SON_ECHO_PIN = 24
SON_SLOWDONW = 6000
SON_BREAK = 1000
SON_VERBOSE = False

#STEERING
STEERING_CHANNEL = 1
STEERING_AMPLITUDE = 105
STEERING_LEFT_PWM = 369-STEERING_AMPLITUDE
STEERING_RIGHT_PWM = 369+STEERING_AMPLITUDE
#STEERING_LEFT_PWM = 442
#STEERING_RIGHT_PWM = 222

#THROTTLE
THROTTLE_CHANNEL = 0
THROTTLE_FORWARD_PWM = 420 # max 492
THROTTLE_STOPPED_PWM = 369
THROTTLE_REVERSE_PWM = 310 # min 246 

#TRAINING
BATCH_SIZE = 128
TRAIN_TEST_SPLIT = 0.8

#JOYSTICK
USE_JOYSTICK_AS_DEFAULT = False
JOYSTICK_MAX_THROTTLE = 0.25
JOYSTICK_STEERING_SCALE = 1.0
AUTO_RECORD_ON_THROTTLE = True
JOYSTICK_THROTTLE_AXIS = 'rz'
JOYSTICK_STEERING_AXIS = 'x'
JOYSTICK_DRIVING_MODE_BUTTON = 'trigger'
JOYSTICK_RECORD_TOGGLE_BUTTON = 'circle'
JOYSTICK_INCREASE_MAX_THROTTLE_BUTTON = 'triangle'
JOYSTICK_DECREASE_MAX_THROTTLE_BUTTON = 'cross'
JOYSTICK_INCREASE_THROTTLE_SCALE_BUTTON = 'base'
JOYSTICK_DECREASE_THROTTLE_SCALE_BUTTON = 'top2'
JOYSTICK_INCREASE_STEERING_SCALE_BUTTON = 'base2'
JOYSTICK_DECREASE_STEERING_SCALE_BUTTON = 'pinkie'
JOYSTICK_TOGGLE_CONSTANT_THROTTLE_BUTTON = 'top'
JOYSTICK_VERBOSE = False
