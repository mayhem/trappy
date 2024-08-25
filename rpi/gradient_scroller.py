from abc import abstractmethod
from colorsys import hsv_to_rgb
from time import sleep, monotonic

from gradient import Gradient
from random import random, randint
from effect import Effect, SpeedEvent
from color import hue_to_rgb, random_color


class EffectGradientScroller(Effect):

    def __init__(self, driver, event, apc = None, timeout=None):
        super().__init__(driver, event, apc, timeout)
        self.hue = 0.0
        self.colors = event.color_values
        self.color_index = 0
        self.speed = .5 

        self.current_colors = []

    def _get_next_color(self):
        new_color  = self.colors[self.color_index][:3]
        self.color_index = (self.color_index + 1) % len(self.colors)

        return new_color

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

    def accept_event(self, event):
        if isinstance(event, SpeedEvent):
            self.speed = event.speed

    def run(self):

        direction = self.speed > 0.0

        spacing = .2
        shift_dist = .02
        offset = -spacing
        for i in range(int(1.0 / spacing) + 2):
            self.current_colors.append(self.colors[self.color_index][:3])
            self.color_index = (self.color_index + 1) % len(self.colors)

        g = Gradient(self.generate_palette(offset, spacing))
        while not self.stop:
            if self.timeout is not None and monotonic() > self.timeout:
                return

            # Calculate the strip data once and save it
            strip_data = []
            for j in range(self.driver.leds):
                col = g.get_color(float(j) / self.driver.leds)
                strip_data.append(col)

            buf = []
            for k in range(self.driver.strips):
                buf.extend(strip_data)

            self.driver.set(buf)

            if direction:
                offset += shift_dist
            else:
                offset -= shift_dist
            if offset > 0.0:
                offset -= spacing
                self.current_colors.insert(0, self._get_next_color())
                del self.current_colors[-1]

            if offset < -spacing:
                offset += spacing
                self.current_colors.append(self._get_next_color())
                del self.current_colors[0]

            g.palette = self.generate_palette(offset, spacing)

            max_delay = .1
            speed = abs(self.speed)
            delay = (1.0 - speed) * max_delay
            direction = self.speed > 0.0
            sleep(delay)
