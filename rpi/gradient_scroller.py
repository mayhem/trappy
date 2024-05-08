from abc import abstractmethod
from gradient import Gradient
from random import random
from time import sleep, monotonic
from colorsys import hsv_to_rgb
from effect import Effect


class EffectGradientChase(Effect):

    def point_generator(self, offset, row_index):
        if row_index % 2 == 0:
            color = (255, 0, 0)
        else:
            color = (0, 0, 255)
        return (offset, color)

    def shift(self, palette, dist):
        shifted = []
        dropped = 0
        for offset, color in palette:
            if offset + dist < 1.0: 
                shifted.append((offset + dist, color))
            else:
                dropped += 1

        for i in range(dropped):
            shifted.insert(0, self.point_generator(shifted[0][0] - dist, i))

        return shifted

    def run(self, timeout):

        palette = [ self.point_generator(o / 20, o) for o in range(22) ]
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

            g.palette = self.shift(g.palette, .05)
            print(g.palette)
