from abc import abstractmethod
from colorsys import hsv_to_rgb
from math import fmod
from random import random, randint, shuffle
from time import sleep, monotonic

from gradient import Gradient
from effect import Effect, SpeedEvent, FaderEvent, DirectionEvent
from color import hue_to_rgb, random_color


class EffectSweep(Effect):

    FADER_HUE = 3
    FADER_SPREAD = 4
    FADER_JITTER = 5
    FADE_CONSTANT = .85

    def __init__(self, driver, event, apc = None, timeout=None):
        super().__init__(driver, event, apc, timeout)
        self.hue = 0.0

    def map_fader_value(self, fader, value):
        if fader == self.FADER_HUE:
            return value / 20.0

        if fader == self.FADER_SPREAD:
            return value / 2.0

        if fader == self.FADER_JITTER:
            return value / 10.0

        return None

    def run(self):

        led_data = [ list([0,0,0]) for x in range(self.driver.strips * self.driver.leds) ]
        hue = 0.0
        while not self.stop:
            if self.timeout is not None and monotonic() > self.timeout:
                return

            speed = self.speed
            if speed == 0:
                sleep(.01)
                continue

            hue_inc = self.fader_value(self.FADER_HUE)
            spread = self.fader_value(self.FADER_SPREAD)
            jitter = self.fader_value(self.FADER_JITTER)

            for strip in range(self.driver.strips):
                h = fmod(hue + (strip * spread) + 1.0, 1.0)
                g = Gradient([(0.0, hue_to_rgb(h-jitter)), (1.0, hue_to_rgb(h+jitter))], self.driver.leds)
                for l in range(self.driver.leds):
                    led_data[(strip * self.driver.leds) + l] = g.get_color(l / self.driver.leds)

            self.driver.set(led_data)

            hue = fmod(hue + hue_inc, 1.0)
            max_delay = .1
            delay = (1.0 - speed) * max_delay
            sleep(delay)
