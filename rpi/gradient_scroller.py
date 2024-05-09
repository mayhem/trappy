from abc import abstractmethod
from gradient import Gradient
from random import random
from time import sleep, monotonic
from colorsys import hsv_to_rgb
from effect import Effect


class EffectGradientChase(Effect):

    def point_generator(self, offset, row_index):
        if row_index % 2 == 0:
            color = (255, 60, 0)
        else:
            color = (255, 0, 255)
        return (offset, color)

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
            palette.append(self.point_generator(offset, row_index))
            row_index += 1
            offset += spacing
            if palette[-1][0] > 1.5:
                break

        g = Gradient(palette)
        for i in range(1000): 
            if monotonic() > timeout:
                return

            buf = []
            for k in range(self.driver.strips):
                for j in range(self.driver.leds):
                    col = g.get_color(float(j) / self.driver.leds)
                    buf.append(col)

            self.driver.set(buf)
            g.palette = self.shift(g.palette, shift_dist)
