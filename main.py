import pygame
import sys
import math
import threading
import time
from djitellopy import Tello
from enum import Enum

from telemetry_panel import TelemetryPanel
from gamepad_interface import GamepadInterface
from drone_controller import DroneController
from drone_interface import DroneInterface

from global_variables import *

# Initialize pygame
pygame.init()



def main():
    interface = DroneInterface()
    interface.run()

if __name__ == "__main__":
    main()
