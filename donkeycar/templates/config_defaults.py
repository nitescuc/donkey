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
DRIVE_LOOP_HZ = 20
MAX_LOOPS = 100000

#CAMERA
USE_WEB_CAMERA = False
CAMERA_RESOLUTION = (120, 160) #(height, width)
CAMERA_FRAMERATE = DRIVE_LOOP_HZ

#TX
USE_TX_AS_DEFAULT = False
TX_THROTTLE_MIN = 913
TX_THROTTLE_MAX = 2111
TX_STEERING_MIN = 960
TX_STEERING_MAX = 2060
TX_THROTTLE_TRESH = 1470
TX_VERBOSE  = False

#PI RF
USE_PI_RF_AS_DEFAULT = False
PI_RF_THROTTLE_MIN = 913
PI_RF_THROTTLE_MAX = 2111
PI_RF_STEERING_MIN = 960
PI_RF_STEERING_MAX = 2060
PI_RF_THROTTLE_TRESH = 1470
PI_RF_STEERING_PIN = 18
PI_RF_THROTTLE_PIN = 23
PI_RF_VERBOSE  = False

# Set the following to false to deactivate PCA9685 driver (usefull to run donkey on laptop)
USE_PWM_ACTUATOR = True

#STEERING
STEERING_CHANNEL = 1
# While collecting training dataset, If you are using rPI in the middle of the PWM chain, uncomment following three lines 
#STEERING_AMPLITUDE = 100
#STEERING_LEFT_PWM = 369+STEERING_AMPLITUDE
#STEERING_RIGHT_PWM = 369-STEERING_AMPLITUDE
# Else if you make a direct connection between Rx controller and Throttle/Steering actuators, uncomment the following two lines :
STEERING_LEFT_PWM = ((TX_STEERING_MAX)/(16666/4095))
STEERING_RIGHT_PWM =((TX_STEERING_MIN)/(16666/4095))

#THROTTLE
THROTTLE_CHANNEL = 0
THROTTLE_FORWARD_PWM = 420
THROTTLE_STOPPED_PWM = 370
THROTTLE_REVERSE_PWM = 300

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
