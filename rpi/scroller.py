from abc import abstractmethod
from gradient import Gradient
from random import random
from time import sleep, monotonic
from colorsys import hsv_to_rgb

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

class Effect:

    def __init__(self, driver):
        self.driver = driver

    def scroll(self, pattern, buf, row_index, num_rows):
        direction = 1 if num_rows > 0 else 0;
        for j in range(abs(num_rows)):
            row = pattern.get(row_index)
            self.shift(buf, row, direction)
            self.driver.set(buf)
            row_index += 1

        return row_index

    def shift(self, buf, new_row, direction):
        for strip in range(NUM_STRIPS):
            begin = strip * NUM_LEDS
            end = (strip + 1) * NUM_LEDS;
            if direction == 1:
                temp = buf[begin:end-1]
                temp.insert(0, new_row[strip])
                buf[begin:end] = temp
            else:
                temp = buf[begin+1:end]
                temp.append(new_row[strip])
                buf[begin:end] = temp


    @abstractmethod
    def run(self):
        pass

class EffectChase(Effect):

    def run(self, timeout):
        buf = [[0,0,0] for i in range(NUM_LEDS * NUM_STRIPS)]
        palette = Gradient([[0.0, [255, 0, 0]], [.5, [255, 80, 255]], [1.0, [0, 0, 255]]])
        pattern = PatternEveryOther(RowRandomRainbow(palette))

        row_index = 0
        while monotonic() < timeout:
            row_index = self.scroll(pattern, buf, row_index, NUM_LEDS)
            row_index = self.scroll(pattern, buf, row_index, -NUM_LEDS)
