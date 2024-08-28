#!/usr/bin/env python3

from threading import Thread, Lock
from queue import Queue
from random import seed
from time import sleep, monotonic

from scroller import EffectScroller
from gradient_scroller import EffectGradientScroller
from defs import NUM_LEDS, NUM_STRIPS
from led_driver import LEDDriver
from apc_mini_controller import APCMiniMk2Controller
from effect import EffectEvent, SpeedEvent, GammaEvent

class EventQueue:
    """ Similar to the Lock object, but previous duplicate events are dropped. """

    def __init__(self):
        self.queue = []
        self.lock = Lock()

    def put(self, item):
        self.lock.acquire()
        try:
            if type(self.queue[0]) == type(item):
                self.queue.pop(0)
        except IndexError:
            pass

        self.queue.append(item)
        self.lock.release()

    def get(self):
        self.lock.acquire()
        try:
            item = self.queue.pop(0)
        except IndexError:
            item = None
        self.lock.release()

        return item


class Trappy:

    def __init__(self):
        self.driver = LEDDriver(leds=NUM_LEDS, strips=NUM_STRIPS)
        for i in range(0):
            self.driver.fill((255, 0, 255))
            sleep(.1)
            self.driver.fill((255, 60, 0))
            sleep(.1)

        self.driver.clear()

        self.queue = EventQueue()
        self.apc = APCMiniMk2Controller(self.queue)
        self.apc.startup()
        self.apc.start()

        duration =  99999999
        seed(monotonic())

        self.effect_classes = []
        self.effect_classes.append(EffectGradientScroller)
        self.effect_classes.append(EffectScroller)

        self.current_effect = None

    def queue_event(self, event, avoid_duplicates=False):
        self.queue.put(event)

    def run(self):
        try:
            while True:
                event = self.queue.get()
                if not event:
                    continue

                if isinstance(event, EffectEvent):
                    if event.effect is None:
                        self.current_effect.accept_event(event)
                        continue

                    if event.effect >= 0 and event.effect < len(self.effect_classes):
                        if self.current_effect is not None:
                           self.current_effect.exit()
                           self.current_effect.join()
                           self.current_effect = None

                        self.current_effect = self.effect_classes[event.effect](self.driver, event, apc=self.apc)
                        self.current_effect.start()

                if isinstance(event, SpeedEvent):
                    if self.current_effect is not None:
                        self.current_effect.accept_event(event)

                if isinstance(event, GammaEvent):
                    self.driver.set_gamma_correction(event.gamma)

        except KeyboardInterrupt:
            self.apc.exit()
            self.driver.clear()
            self.apc.shutdown()


if __name__ == "__main__":
    t = Trappy()
    t.run()
