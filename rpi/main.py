from time import sleep
from math import sin

import smi_leds
from random import randint
from gradient import Gradient

def rand_color():
    return (randint(128, 255), randint(128, 255), randint(128, 255))


class Trappy:

    def __init__(self):
        self.leds = 144
        self.strips = 8

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

    def set_led(self, leds: bytearray, strip: int, led: int, color: tuple):
        offset = (strip * self.leds + led) * 4
        leds[offset] = color[2]
        leds[offset + 1] = color[1]
        leds[offset + 2] = color[0]

    def fill(self, color):
        col = (color[2], color[1], color[0], 0)
        leds = bytearray(col * self.leds * self.strips)
        smi_leds.leds_set(leds)
        smi_leds.leds_send()

    def test_gradient(self):
        self.pixels.fill((0, 0, 0))
        g = [[0.0, [128, 0, 0]],
             [.5,  [0, 128, 0]],
             [1.0, [127, 128, 0]]]
        gr = Gradient(g, leds=self.leds)
        t = 0.0
        while True:
            for i in range(144):
                gr.palette[1][0] = .5 + sin(t) / 4
                color = gr.get_color(i)
                for j in range(8):
                    self.set_led(j, i, color)
            smi_leds.leds_send()
            t += .1

    def gradient_test(self):

        g = Gradient([[0.0, [255, 0, 0]], [.5, [255, 0, 255]], [1.0, [255, 80, 0]]])
        buf = bytearray((0,0,0,0) * self.leds * self.strips)
        for i in range(1000): 
            t = i / 10
            wiggle = (sin(t/8) / 8.0) + .5 + (sin(t*3) / 12);
            g.palette[1][0] = wiggle
            for j in range(self.leds):
                for k in range(self.strips):
                    # TODO: Make additive
                    color = g.get_color(float(j) / self.leds)
                    self.set_led(buf, k, j, color)

            smi_leds.leds_set(buf)
            smi_leds.leds_send()
   

if __name__ == "__main__":
    t = Trappy()
    try:
        t.gradient_test()
    except KeyboardInterrupt:
        t.clear()
        sleep(.1)
