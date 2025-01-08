from abc import abstractmethod
from colorsys import hsv_to_rgb
from time import sleep, monotonic

from gradient import Gradient
from random import random, randint
from effect import Effect, InstantColorEvent
from color import hue_to_rgb, random_color


class EffectPOV(Effect):

    def __init__(self, driver, event, apc = None, timeout=None):
        super().__init__(driver, event, apc, timeout)

        # Only take the first two colors
        self.colors = event.color_values[:2]
        self.local_color_index = 0

    def accept_event(self, event):
        if isinstance(event, InstantColorEvent):
            self.lock.acquire()
            self.colors[self.local_color_index] = event.color
            self.lock.release()
            self.local_color_index = (self.local_color_index + 1) % 2
            return

    def run(self):
        i = 0
        while not self.stop:
            if self.timeout is not None and monotonic() > self.timeout:
                return

            leds = []
            for strip in range(self.driver.strips):
                for led in range(self.driver.leds):
                    if led // 4 % 2 == i % 2:
                        leds.append(self.colors[0])
                    else:
                        leds.append(self.colors[1])

            self.driver.set(leds, no_gamma=True)  
            i += 1
