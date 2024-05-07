from abc import abstractmethod
from gradient import Gradient
from random import random

import smi_leds
from main import NUM_LEDS, NUM_STRIPS

rainbow = [
    (255, 0, 0),
    (255, 160, 0),
    (255, 255, 0),
    (0, 255, 63),
    (0, 255, 255),
    (0, 63, 255),
    (127, 0, 255),
    (255, 0, 191)
]

class Pattern:

    def __init__(self, row_gen):
        self.row_gen = row_gen

    @abstractmethod
    def get(row_index):
        """ returns color tuple """
        pass

class PatternEveryOther(Pattern):

    def get(row_index):
        if row_index % 2 == 0:
            return self.row_gen.get(row_index)
        else:
            return [0,0,0,0] * NUM_STRIPS

class PatternAll(Pattern):

    def get(row_index):
        return self.row_gen.get(row_index)

class RowGenerator:

    def __init__(self, palette):
        self.palette = palette

    @abstractmethod
    def get(row_index):
        """ returns self.strip color tuples """
        pass


class RowRainbow(RowGenerator):
    @abstractmethod
    def get(row_index):
        return rainbow

class RowRandom(RowGenerator):

    def get(row_index):
        row = bytearray()
        for i in range(NUM_STRIPS):
            col = self.palette.get_color(random())
            row += bytearray((col[0], col[1], col[2], 0))

        return row


class Effect:

    def __init__(self):
        pass

    def scroll(self, pattern, buf, row_index, num_rows):
        direction = 1 if num_rows > 0 else 0;
        for j in range(abs(num_rows)):
            row = pattern.get(row_index)
            self.shift(buf, row, direction)
            smi_leds.leds_set(buf)
            smi_leds.leds_send()
            row_index += 1

        return row_index

    def shift(buf, new_row, direction):
        for strip in range(NUM_STRIPS):
            offset = strip * NUM_LEDS * 4
            length = NUM_STRIPS * NUM_LEDS * 4
            row_length = NUM_STRIPS * 4
            if direction == INWARD:
                buf[offset:offset+length-1] = buf[offset + row_length:offset+length-1] + new_row
            else:
                buf[offset:offset+length-1] = new_row + buf[offset:offset+length-1-row_length] 

    @abstractmethod
    def run(self):
        pass

class EffectChase(Effect):

    def run(self):
        buf = bytearray((0,0,0,0) * NUM_LEDS * NUM_STRIPS)
        pattern = PatternEveryOther(RowRandom())
        palette = Gradient([[0.0, [255, 0, 0]], [.5, [255, 0, 255]], [1.0, [255, 80, 0]]])
      
        row_index = 0
        while True:
            row_index = self.scroll(pattern, buf, row_index, NUM_LEDS)
            row_index = self.scroll(pattern, buf, row_index, -NUM_LEDS)
