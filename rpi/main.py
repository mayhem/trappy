#!/usr/bin/env python3

from threading import Thread
from queue import Queue
from random import seed
from time import sleep, monotonic

from scroller import EffectScroller
from gradient_scroller import EffectGradientScroller
from defs import NUM_LEDS, NUM_STRIPS
from led_driver import LEDDriver
from apc_mini_controller import APCMiniMk2Controller


class Trappy:

    def __init__(self):
        self.driver = LEDDriver(NUM_STRIPS, NUM_LEDS)
        for i in range(0):
            self.driver.fill((255, 0, 255))
            sleep(.1)
            self.driver.fill((255, 60, 0))
            sleep(.1)

        self.driver.clear()

        self.queue = Queue()
        self.apc = APCMiniMk2Controller(self.queue)
        self.apc.startup()
        self.apc.start()

        duration =  99999999
        seed(monotonic())

        self.effect_classes = []
        self.effect_classes.append(EffectGradientScroller)
        self.effect_classes.append(EffectScroller)

        self.current_effect = None

    def queue_event(self, event):
        self.queue.put(event)

    def run(self):
        try:
            while True:
                event = self.queue.get()
                if not event:
                    continue

                if event.effect >= 0 and event.effect < len(self.effect_classes):
                    if self.current_effect is not None:
                       self.current_effect.exit()
                       self.current_effect.join()
                       self.current_effect = None

                    self.current_effect = self.effect_classes[event.effect](self.driver)
                    self.current_effect.start()

        except KeyboardInterrupt:
            self.apc.exit()
            self.driver.clear()
            self.apc.shutdown()


if __name__ == "__main__":
    t = Trappy()
    t.run()
