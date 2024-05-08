from time import sleep, monotonic
from random import seed
from math import sin

import smi_leds
from random import randint
from gradient import Gradient
from scroller import EffectChase
from defs import NUM_LEDS, NUM_STRIPS

def rand_color():
    return (randint(128, 255), randint(128, 255), randint(128, 255))


class Trappy:

    def __init__(self):
        self.strips = NUM_STRIPS
        self.leds = NUM_LEDS

        smi_leds.leds_init(self.leds, 20)
        smi_leds.leds_clear()

        for i in range(3):
            self.fill((255, 0, 255))
            sleep(.1)
            self.fill((255, 60, 0))
            sleep(.1)

        smi_leds.leds_clear()

    def clear(self):
        smi_leds.leds_clear()

    def set_led(self, leds: list, strip: int, led: int, color: tuple):
        leds[strip * NUM_LEDS + led] = color

    def fill(self, color):
        leds = bytearray(color * self.leds * self.strips)
        smi_leds.leds_set(leds)
        smi_leds.leds_send()

    def set(self, buf):
        ba = bytearray()
        for col in buf:
            ba += bytearray(col)

        smi_leds.leds_set(ba)
        smi_leds.leds_send()

    def effect_gradient(self, timeout):

        g = Gradient([[0.0, [255, 0, 0]], [.5, [255, 255, 0]], [1.0, [255, 80, 0]]])
        for i in range(1000): 
            if monotonic() > timeout:
                return

            t = i / 10
            wiggle = (sin(t/8) / 8.0) + .5 + (sin(t*3) / 12);
            g.palette[1][0] = wiggle
            buf = []
            for k in range(self.strips):
                for j in range(self.leds):
                    col = g.get_color(float(j) / self.leds)
                    buf.append(col)

            self.set(buf)

    def effect_chase(self):
        eff = EffectChase()
        eff.run()

    def effect_checkerboard(self, timeout):
        row = 0

        while monotonic() < timeout:
            buf = []
            for strip in range(self.strips):
                for led in range(self.leds):
                    if led // 4 % 2 == row % 2:
                        color = ( 255, 0, 0 )
                    else:
                        color = ( 0, 0, 255 )
                    buf.append(color)

            self.set(buf)
            row += 1

if __name__ == "__main__":

    duration = 10 

    seed(monotonic())
    t = Trappy()
    try:
        while True:
            t.effect_chase()
#            t.effect_gradient(monotonic() + duration)
#            t.effect_checkerboard(monotonic() + duration)
    except KeyboardInterrupt:
        print("shutting down")
        t.clear()
        sleep(.5)
