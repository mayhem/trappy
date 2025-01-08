from abc import abstractmethod
from colorsys import hsv_to_rgb
from time import monotonic

from gradient import Gradient
from random import random, randint
from effect import Effect, SpeedEvent, FaderEvent, DirectionEvent
from color import hue_to_rgb, random_color


class EffectGradientScroller(Effect):

    SLUG = "gradient-scroller"
    FADER_SPACING = 4
    SPACING_RANGE_MIN = .025
    SPACING_RANGE_MAX = .5 - SPACING_RANGE_MIN

    def __init__(self, driver, event, apc = None, timeout=None):
        super().__init__(driver, event, apc, timeout)
        self.hue = 0.0
        self.current_colors = []

    def get_active_faders(self):
        return [ self.FADER_SPACING ]

    def map_fader_value(self, fader, value):
        # scale to SPACING_RANGE_MIN and SPACING_RANGE_MAX
        if fader == self.FADER_SPACING:
            return value * self.SPACING_RANGE_MAX + self.SPACING_RANGE_MIN

        return None

    def generate_palette(self, offset, spacing):
        if offset > 0.0:
            raise ValueError("Offset must be negative! (is %.03f)" % offset)

        pal = []
        for i, col in enumerate(self.current_colors):
            pal.append((offset, col))
            offset += spacing

        return pal

    def print_palette(self, palette=None):
        for pal in palette:
            print("%.2f: " % pal[0], pal[1])
        print()

    def run(self):

        self.set_sleep_params(0.0, .2)

        shift_dist = .02
        spacing = self.fader_value(self.FADER_SPACING)
        offset = -spacing
        for i in range(int(1.0 / self.SPACING_RANGE_MIN) + 2):
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

            if self.direction == DirectionEvent.OUTWARD:
                offset += shift_dist
            else:
                offset -= shift_dist
            if offset > 0.0:
                offset -= spacing
                self.current_colors.insert(0, self.get_next_color())
                del self.current_colors[-1]

            if offset < -spacing:
                offset += spacing
                self.current_colors.append(self.get_next_color())
                del self.current_colors[0]

            g.palette = self.generate_palette(offset, spacing)

            self.sleep()

            spacing = self.fader_value(self.FADER_SPACING)
