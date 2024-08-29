from abc import abstractmethod
from colorsys import hsv_to_rgb
from time import sleep, monotonic
from threading import Lock

from gradient import Gradient
from random import random, randint
from effect import Effect, SpeedEvent, FaderEvent, DirectionEvent
from color import hue_to_rgb, random_color


class EffectGradientScroller(Effect):

    FADER_SPEED = 2
    FADER_SPACING = 3
    SPACING_RANGE_MIN = .025
    SPACING_RANGE_MAX = .5 - SPACING_RANGE_MIN

    def __init__(self, driver, event, apc = None, timeout=None):
        super().__init__(driver, event, apc, timeout)
        self.lock = Lock()
        self.hue = 0.0
        self._spacing = self._map_spacing_value(event.fader_values[self.FADER_SPACING])
        self.current_colors = []

    @property
    def spacing(self):
        self.lock.acquire()
        spacing = self._spacing    
        self.lock.release()
        return spacing    

    def _map_spacing_value(self, value):
        # scale to SPACING_RANGE_MIN and SPACING_RANGE_MAX
        return value * self.SPACING_RANGE_MAX + self.SPACING_RANGE_MIN

    def generate_palette(self, offset, spacing):
        if offset > 0.0:
            print("Offset must be negative! (is %.03f)" % offset)
            return

        pal = []
        for i, col in enumerate(self.current_colors):
            pal.append((offset, col))
            offset += spacing

        return pal

    def print_palette(self, palette):
        for pal in palette:
            print("%.2f: " % pal[0], pal[1])
        print()

    def accept_event(self, event):
        super().accept_event(event)

        if isinstance(event, FaderEvent):
            if event.fader == self.FADER_SPACING:
                self.lock.acquire()
                self._spacing = self._map_spacing_value(event.value)
                self.lock.release()
            return

    def run(self):

        shift_dist = .02
        offset = -self.spacing
        for i in range(int(1.0 / self.SPACING_RANGE_MIN) + 2):
            self.current_colors.append(self.colors[self.color_index][:3])
            self.color_index = (self.color_index + 1) % len(self.colors)

        g = Gradient(self.generate_palette(offset, self.spacing))
        while not self.stop:
            if self.timeout is not None and monotonic() > self.timeout:
                return

            speed = self.speed
            if speed == 0:
                sleep(.01)
                continue

            # Calculate the strip data once and save it
            strip_data = []
            for j in range(self.driver.leds):
                col = g.get_color(float(j) / self.driver.leds)
                strip_data.append(col)

            buf = []
            for k in range(self.driver.strips):
                buf.extend(strip_data)

            self.driver.set(buf)

            if self.direction == DirectionEvent.OUTWARD:
                offset += shift_dist
            else:
                offset -= shift_dist
            if offset > 0.0:
                offset -= self.spacing
                self.current_colors.insert(0, self.get_next_color())
                del self.current_colors[-1]

            if offset < -self.spacing:
                offset += self.spacing
                self.current_colors.append(self.get_next_color())
                del self.current_colors[0]

            g.palette = self.generate_palette(offset, self.spacing)

            max_delay = .1
            delay = (1.0 - speed) * max_delay
            sleep(delay)
