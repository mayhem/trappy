from abc import abstractmethod
from colorsys import hsv_to_rgb
from time import sleep, monotonic

from gradient import Gradient
from random import random
from effect import Effect
from color import hue_to_rgb


class EffectGradientChase(Effect):

    def __init__(self, driver):
        super().__init__(driver)
        self.hue = 0.0

    def point_generator_hue(self, offset, row_index):
        self.hue += .01
        if row_index % 2 == 0:
            color = hue_to_rgb(self.hue)
        else:
            color = hue_to_rgb(self.hue + .5)
        return (offset, color)

    def point_generator_stripes(self, offset, row_index):
        if row_index % 2 == 0:
            color = (255, 0, 0)
        else:
            color = (0, 0, 255)
        return (offset, color)

    def point_generator_stripes(self, offset, row_index):
        if row_index % 2 == 0:
            color = (255, 0, 0)
        else:
            color = (0, 0, 255)
        return (offset, color)

    def point_generator_rainbow(self, offset, row_index):
        self.hue += .2
        return (offset, hue_to_rgb(self.hue))

    def shift(self, palette, dist):

        if dist > 0:
            direction = 1
        else:
            direction = 0

        shifted = []
        for offset, color in palette:
            new_offset = offset + dist
            if direction == 1:
                if new_offset < 1.5: 
                    shifted.append((new_offset, color))
                else:
                    shifted.append((-.5, color))
            else:
                if new_offset + dist > -.5: 
                    shifted.append((new_offset, color))
                else:
                    shifted.append((1.5, color))

        return sorted(shifted, key=lambda a: a[0])

    def run(self, timeout, variant):

        row_index = 0
        offset = -.5
        spacing = .1
        shift_dist = .02
        palette = []
        while True:
            if variant == 0:
                palette.append(self.point_generator_rainbow(offset, row_index))
            if variant == 1:
                palette.append(self.point_generator_hue(offset, row_index))
            if variant == 2:
                palette.append(self.point_generator_stripes(offset, row_index))

            row_index += 1
            offset += spacing
            if palette[-1][0] > 1.5:
                break

        g = Gradient(palette)
        while True:
            if monotonic() > timeout:
                return

            buf = []
            for k in range(self.driver.strips):
                for j in range(self.driver.leds):
                    col = g.get_color(float(j) / self.driver.leds)
                    buf.append(col)

            self.driver.set(buf)
            g.palette = self.shift(g.palette, -shift_dist)
