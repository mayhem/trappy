from abc import abstractmethod
from colorsys import hsv_to_rgb, rgb_to_hsv
from math import fmod
from random import random, randint, shuffle
from time import sleep, monotonic

from effect import Effect, SpeedEvent, FaderEvent, DirectionEvent
from color import hue_to_rgb, random_color


class EffectSpiral(Effect):

    SLUG = "spiral"
    FADER_SEGMENTS = 2
    VARIANTS = 1

    def __init__(self, driver, event, apc = None, timeout=None):
        super().__init__(driver, event, apc, timeout)

    def get_active_faders(self):
        return [ self.FADER_SEGMENTS ]

    def map_fader_value(self, fader, value):
        return None

    def init(self):
        pass

    def run(self):

        led_data = [ list([0,0,0]) for x in range(self.driver.strips * self.driver.leds) ]
        color = self.get_next_color()
        step = 3

        segments = self.fader_value(self.FADER_SEGMENTS)
        strip = 0
        while not self.stop:
            if self.timeout is not None and monotonic() > self.timeout:
                return

            segments = self.fader_value(self.FADER_SEGMENTS)
            for circle in range(self.driver.leds):
                offset = circle * 2
                led_data[strip * self.driver.leds + offset] = self.get_next_color()
                #strip = (strip + step) % self.driver.strips
                strip

                self.driver.set(led_data)

#            self.sleep()
