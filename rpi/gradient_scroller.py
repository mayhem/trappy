from abc import abstractmethod
from math import fmod
from colorsys import hsv_to_rgb
from time import sleep, monotonic

from gradient import Gradient
from random import random
from effect import Effect


def hue_to_rgb(hue):
    r,g,b = hsv_to_rgb(fmod(hue, 1.0), 1.0, 1.0)
    return (int(r * 255), int(g * 255), int(b * 255))


class EffectGradientChase(Effect):

    def __init__(self, driver):
        super().__init__(driver)
        self.hue = 0.0

    def point_generator_stripes(self, offset, row_index):
        self.hue += .01
        if row_index % 2 == 0:
            color = hue_to_rgb(self.hue)
        else:
            color = hue_to_rgb(self.hue + .5)
        return (offset, color)

    def point_generator_rainbow(self, offset, row_index):
        self.hue += .2
        return (offset, hue_to_rgb(self.hue))

    def shift(self, palette, dist):
        shifted = []
        dropped = 0
        for offset, color in palette:
            if offset + dist < 1.5: 
                shifted.append((offset + dist, color))
            else:
                shifted.insert(0, (-.5, color))

        return shifted

    def run(self, timeout):

        row_index = 0
        offset = -.5
        spacing = .1
        shift_dist = .02
        palette = []
        while True:
            palette.append(self.point_generator_stripes(offset, row_index))
            row_index += 1
            offset += spacing
            if palette[-1][0] > 1.5:
                break

        g = Gradient(palette)
        while True:
#            if monotonic() > timeout:
#                return

            buf = []
            for k in range(self.driver.strips):
                for j in range(self.driver.leds):
                    col = g.get_color(float(j) / self.driver.leds)
                    buf.append(col)

            self.driver.set(buf)
            g.palette = self.shift(g.palette, shift_dist)
