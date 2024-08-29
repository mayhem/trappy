from abc import abstractmethod
from colorsys import hsv_to_rgb
from time import sleep, monotonic

from gradient import Gradient
from random import random, randint
from effect import Effect, SpeedEvent, FaderEvent, DirectionEvent
from color import hue_to_rgb, random_color


class EffectPOV(Effect):

    def __init__(self, driver, event, apc = None, timeout=None):
        super().__init__(driver, event, apc, timeout)

        # Only take the first two colors
        self.colors = event.color_values[:2]
        print(self.colors)

    def run(self):
        i = 0
        while not self.stop:
            if self.timeout is not None and monotonic() > self.timeout:
                return

            color0 = self.get_next_color()
            color1 = self.get_next_color()
#            print(color0, color1)
            print(self.colors)
            leds = []
            for strip in range(self.driver.strips):
                for led in range(self.driver.leds):
                    if led // 4 % 2 == i % 2:
                        leds.append(color0)
                    else:
                        leds.append(color1)

            self.driver.set(leds, no_gamma=True)  
            i += 1
