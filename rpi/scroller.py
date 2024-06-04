from abc import abstractmethod
from gradient import Gradient
from random import random, randint
from time import sleep, monotonic
from colorsys import hsv_to_rgb
from effect import Effect
from color import random_color

import smi_leds
from defs import NUM_LEDS, NUM_STRIPS

rainbow = [
    [255, 0, 0],
    [255, 160, 0],
    [255, 255, 0],
    [0, 255, 63],
    [0, 255, 255],
    [0, 63, 255],
    [127, 0, 255],
    [255, 0, 191]
]

class Pattern:

    def __init__(self, row_gen):
        self.row_gen = row_gen

    @abstractmethod
    def get(self, row_index):
        """ returns color tuple """
        pass

class PatternEveryOther(Pattern):

    def get(self, row_index):
        if row_index % 2 == 0:
            return self.row_gen.get(row_index)
        else:
            return [ [0,0,0] for i in range(NUM_STRIPS) ]

class PatternAll(Pattern):

    def get(self, row_index):
        return self.row_gen.get(row_index)

class RowGenerator:

    def __init__(self, palette):
        self.palette = palette

    @abstractmethod
    def get(self, row_index):
        """ returns self.strip color tuples """
        pass


class RowRainbow(RowGenerator):
    @abstractmethod
    def get(self, row_index):
        row = []
        for col in rainbow:
            row.append(col)
        return row

class RowRandom(RowGenerator):

    def get(self, row_index):
        row = []
        col = self.palette.get_color(random())
        for i in range(NUM_STRIPS):
            row.append(col)
        return row

class RowRandomRainbow(RowGenerator):

    def get(self, row_index):
        row = []
        for i in range(NUM_STRIPS):
            r,g,b = hsv_to_rgb(random(), 1.0, 1.0)
            col = [int(255 * r), int(255 *g), int(255 * b)]
            row.append(col)
        return row

class RowSingleDots(RowGenerator):

    def __init__(self, palette, variant):
        super().__init__(palette)
        self.col = random_color()
        self.variant = variant

    def get(self, row_index):
        row = []
        for i in range(NUM_STRIPS):
            index = randint(0, 6)
            if index == 0:
                if self.variant == 0:
                    row.append(rainbow[i])
                else:
                    row.append(self.col)

            else:
                row.append([0, 0, 0])
        return row

class RowWibble(RowGenerator):

    def __init__(self, palette, variant):
        super().__init__(palette)
        self.col = random_color()
        self.variant = variant

    def get(self, row_index):
        row = []
        for i in range(NUM_STRIPS):
            if self.variant == 0:
                if i == row_index % NUM_STRIPS:
                    row.append(self.col)
                else:
                    row.append([0, 0, 0])

        return row

class EffectChase(Effect):

    def run(self, timeout, variant):
        buf = [[0,0,0] for i in range(NUM_LEDS * NUM_STRIPS)]
        palette = Gradient([[0.0, [255, 0, 0]], [.5, [255, 80, 255]], [1.0, [0, 0, 255]]])

        if variant == 0:
            pattern = PatternAll(RowSingleDots(palette, randint(0, 1)))
        else:
            pattern = PatternAll(RowWibble(palette, (0)))

        row_index = 0
        while monotonic() < timeout:
            row_index = self.scroll(pattern, .01, buf, row_index, NUM_LEDS * 2)
            row_index = self.scroll(pattern, .01, buf, row_index, -NUM_LEDS * 2)
            row_index = self.scroll(pattern, .005, buf, row_index, NUM_LEDS)
            row_index = self.scroll(pattern, .005, buf, row_index, -NUM_LEDS)
            row_index = self.scroll(pattern, .01, buf, row_index, NUM_LEDS * 2)
            row_index = self.scroll(pattern, .01, buf, row_index, -NUM_LEDS * 2)
