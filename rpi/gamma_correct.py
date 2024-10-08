from abc import abstractmethod
from colorsys import hsv_to_rgb
from queue import Queue
from time import sleep, monotonic
from threading import Lock

from gradient import Gradient
from random import random, randint
from effect import Effect

def write_table(gamma):
    print("# Gamma value: %.3f" % gamma)
    print("GAMMA = [")
    for i in range(256):
        print("    %d," % (int(255 * (i / 256) ** (gamma))))
    print("]")

class GammaCorrector:

    def __init__(self):
        self.gamma = None
        self.cur_table = []
        self.lock = Lock()

    def set_gamma(self, gamma):
        if gamma == self.gamma:
            return

        table = []
        for i in range(256):
            table.append(int(255 * (i / 256) ** (3.5-gamma)))

        self.lock.acquire()
        self.gamma = gamma
        self.cur_table = table
        self.lock.release()

    def gamma_correct(self, color):

        if not self.cur_table:
            self.calculate()

        self.lock.acquire()
        col = (self.cur_table[color[0]],self.cur_table[color[1]], self.cur_table[color[2]])
        self.lock.release()

        return col


class EffectGammaCorrect(Effect):

    def __init__(self, driver, event, timeout = None):
        super().__init__(driver, event, timeout)
        self.queue = Queue()

    def accept_event(self, event):
        self.queue.put(event)

    def run(self):

        while not self.stop:
            event = self.queue.get()
            if not event:
                continue

            gamma = (event.floats[0] * 1.5) + 1.0
            print(gamma)

#            leds = []
#            for s in range(8):
#                for i in range(144):
#
#                    # strips 1.8
#
#                    red = (i/144) ** (gamma)
#                    color = (0, 0, int(red * 255))
#                    leds.append(color)
#
#            self.driver.set(leds)

            for pad in range(64):
                red = (pad/64) ** (gamma)
                color = (int(red * 255), 0, 0)
                self.apc.set_pad_color(pad, color)
    
            # clear all messages that arrived since we started
            while self.queue.qsize() > 0:
                self.queue.get()

        sleep(1000)



if __name__ == "__main__":
    write_table(1.8)
