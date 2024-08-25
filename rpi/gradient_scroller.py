from abc import abstractmethod
from colorsys import hsv_to_rgb
from time import sleep, monotonic

from gradient import Gradient
from random import random, randint
from effect import Effect
from color import hue_to_rgb, random_color


class EffectGradientScroller(Effect):

    MAX_COLORS = 5

    def __init__(self, driver, event, apc = None, timeout=None):
        super().__init__(driver, event, apc, timeout)
        self.hue = 0.0
        self.colors = event.color_values[:EffectGradientScroller.MAX_COLORS]
        self.color_index = 0

        self.current_colors = []

    def _get_next_color(self):
        new_color  = self.colors[self.color_index][:3]
        self.color_index = (self.color_index + 1) % len(self.colors)

        return new_color

    def shift(self, palette, dist):

        shifted = []
        for offset, color in palette:
            new_offset = offset + dist
            if new_offset >= 1.5: 
                shifted.insert(0, (-.5, self._get_next_color()))
            else:
                shifted.append((new_offset, color))

        return shifted   #sorted(shifted, key=lambda a: a[0])

    def generate_palette(self, offset, spacing):
        if offset > 0.0:
            print("Offset must be negative!")
            return

        pal = []
        for i, col in enumerate(self.current_colors):
            pal.append((offset, col))  #self._get_next_color()))
            offset += spacing

        return pal

    def print_palette(self, palette):
        for pal in palette:
            print("%.2f: " % pal[0], pal[1])
        print()

    def run(self):

        direction = 0 #randint(0, 1)

        spacing = .2
        shift_dist = .02
        offset = -spacing
        for i in range(int(1.0 / spacing) + 2):
            self.current_colors.append(self.colors[self.color_index][:3])
            self.color_index = (self.color_index + 1) % len(self.colors)

        for i in range(30):
            self.print_palette(self.generate_palette(offset, spacing))
            print()

            offset += shift_dist
            if offset > 0.0:
                offset -= spacing

        import sys
#        sys.exit(-1)

        g = Gradient(self.generate_palette(offset, spacing))
        while not self.stop:
            if self.timeout is not None and monotonic() > self.timeout:
                return

            buf = []
            for k in range(self.driver.strips):
                for j in range(self.driver.leds):
                    col = g.get_color(float(j) / self.driver.leds)
                    buf.append(col)

            self.driver.set(buf)

            offset += shift_dist
            if offset > 0.0:
                offset -= spacing
                self.current_colors.insert(0, self._get_next_color())
                del self.current_colors[-1]

            g.palette = self.generate_palette(offset, spacing)
            self.print_palette(g.palette)

            sleep(.05)
