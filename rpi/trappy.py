from time import sleep, monotonic
from random import seed, randint, random
from color import hue_to_rgb
from math import sin

from random import randint
from gradient import Gradient
from scroller import EffectScroller
from gradient_scroller import EffectGradientChase
from defs import NUM_LEDS, NUM_STRIPS
from led_driver import LEDDriver


class TrappyOld:

    def __init__(self):
        self.strips = NUM_STRIPS
        self.leds = NUM_LEDS

        self.driver = LEDDriver(self.strips, self.leds)
        for i in range(0):
            self.driver.fill((255, 0, 255))
            sleep(.1)
            self.driver.fill((255, 60, 0))
            sleep(.1)

        self.driver.clear()

    def effect_gradient(self, timeout):
        g = Gradient([[0.0, [255, 0, 0]], [.5, [255, 0, 255]], [1.0, [255, 80, 0]]])
        for i in range(1000): 
            if monotonic() > timeout:
                return

            t = i / 10
            wiggle = (sin(t/8) / 6.0) + .5 + (sin(t*3) / 12);
            g.palette[1][0] = wiggle
            buf = []
            for k in range(self.strips):
                for j in range(self.leds):
                    col = g.get_color(float(j) / self.leds)
                    buf.append(col)

            self.driver.set(buf)

    def effect_chase(self, timeout):
        eff = EffectScroller(self.driver)
        eff.run(timeout, randint(0, 2))

    def effect_gradient_chase(self, timeout):
        eff = EffectGradientChase(self.driver)
        eff.run(timeout, randint(0, 3))

    def effect_checkerboard(self, timeout):
        row = 0

        hue = random()
        while monotonic() < timeout:
            buf = []
            for strip in range(self.strips):
                for led in range(self.leds):
                    if led // 8 % 2 == row % 2:
                        color = hue_to_rgb(hue)
                    else:
                        color = hue_to_rgb(hue + .35)
                    buf.append(color)

            self.driver.set(buf)
            row += 1

if __name__ == "__main__":

    duration = 12 

    seed(monotonic())
    t = Trappy()
    try:
        while True:
            t.effect_gradient_chase(monotonic() + duration)
            t.effect_chase(monotonic() + duration)
            t.effect_checkerboard(monotonic() + duration)
    except KeyboardInterrupt:
        print("shutting down")
        t.driver.clear()
        t.driver.clear()
        sleep(1)
